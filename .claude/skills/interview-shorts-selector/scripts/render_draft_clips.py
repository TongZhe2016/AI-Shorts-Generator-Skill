#!/usr/bin/env python3
"""Render draft interview-short clips from selection JSON, source video, and SRT subtitles."""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

TIMECODE_RE = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?P<sep>[,.])(?P<ms>\d{1,3})$")
SRT_TIME_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s+-->\s+"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str = ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class ClipSelection:
    clip_id: str
    segments: list[Segment]
    hook_line: str = ""
    suggested_title: str = ""
    suggested_caption: str = ""
    raw: dict | None = None


def parse_timecode(value: str) -> float:
    match = TIMECODE_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid timecode: {value!r}; expected HH:MM:SS.mmm")
    ms = match.group("ms").ljust(3, "0")[:3]
    return int(match.group("h")) * 3600 + int(match.group("m")) * 60 + int(match.group("s")) + int(ms) / 1000


def format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(math.floor(seconds * 1000 + 0.5))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(text: str) -> list[Cue]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    blocks = re.split(r"\n\s*\n", normalized)
    cues: list[Cue] = []
    for block in blocks:
        lines = [line.rstrip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        time_line_index = next((i for i, line in enumerate(lines) if "-->" in line), -1)
        if time_line_index < 0:
            continue
        match = SRT_TIME_RE.search(lines[time_line_index])
        if not match:
            continue
        text_lines = lines[time_line_index + 1 :]
        cues.append(
            Cue(
                parse_timecode(match.group("start")),
                parse_timecode(match.group("end")),
                "\n".join(text_lines).strip(),
            )
        )
    return cues


def build_local_srt(cues: Sequence[Cue], segments: Sequence[Segment]) -> str:
    lines: list[str] = []
    local_offset = 0.0
    index = 1
    for segment in segments:
        for cue in cues:
            if cue.end <= segment.start or cue.start >= segment.end:
                continue
            local_start = local_offset + max(cue.start, segment.start) - segment.start
            local_end = local_offset + min(cue.end, segment.end) - segment.start
            if local_end <= local_start:
                continue
            lines.extend(
                [
                    str(index),
                    f"{format_srt_time(local_start)} --> {format_srt_time(local_end)}",
                    cue.text,
                    "",
                ]
            )
            index += 1
        local_offset += segment.duration
    return "\n".join(lines).strip() + ("\n" if lines else "")


def load_selection_clips(path: Path) -> list[ClipSelection]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_clips = data.get("clips")
    if not isinstance(raw_clips, list):
        raise ValueError(f"Selection JSON must contain a clips array: {path}")
    clips: list[ClipSelection] = []
    for position, raw_clip in enumerate(raw_clips, start=1):
        if not isinstance(raw_clip, dict):
            raise ValueError(f"Clip #{position} must be an object")
        clip_id = str(raw_clip.get("id") or f"clip-{position:02d}")
        raw_segments = raw_clip.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            raise ValueError(f"{clip_id} must contain at least one segments entry with start and end")
        segments: list[Segment] = []
        for seg_position, raw_segment in enumerate(raw_segments, start=1):
            if not isinstance(raw_segment, dict):
                raise ValueError(f"{clip_id} segment #{seg_position} must be an object")
            start_value = raw_segment.get("start")
            end_value = raw_segment.get("end")
            if not start_value or not end_value:
                raise ValueError(f"{clip_id} segment #{seg_position} must include start and end")
            segment = Segment(
                parse_timecode(str(start_value)),
                parse_timecode(str(end_value)),
                str(raw_segment.get("text") or ""),
            )
            if segment.end <= segment.start:
                raise ValueError(f"{clip_id} segment #{seg_position} end must be after start")
            segments.append(segment)
        clips.append(
            ClipSelection(
                clip_id=clip_id,
                segments=segments,
                hook_line=str(raw_clip.get("hook_line") or ""),
                suggested_title=str(raw_clip.get("suggested_title") or ""),
                suggested_caption=str(raw_clip.get("suggested_caption") or ""),
                raw=raw_clip,
            )
        )
    return clips


def ffmpeg_exe() -> str:
    direct = shutil.which("ffmpeg")
    if direct:
        return direct
    try:
        out = subprocess.check_output(
            [sys.executable, "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
            text=True,
        ).strip()
    except Exception as exc:
        raise RuntimeError("ffmpeg not available; install system ffmpeg or `pip install imageio-ffmpeg`") from exc
    if not out or not Path(out).exists():
        raise RuntimeError("ffmpeg executable path not found")
    return out


def run_command(cmd: Sequence[str]) -> None:
    completed = subprocess.run(cmd)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}")


def escape_subtitles_filter_path(path: Path) -> str:
    raw = str(path.resolve()).replace("\\", "/")
    return raw.replace(":", "\\:").replace("'", "\\'")


def cut_segment(ffmpeg: str, video: Path, segment: Segment, output: Path, preset: str, crf: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            ffmpeg,
            "-y",
            "-ss",
            f"{segment.start:.3f}",
            "-i",
            str(video),
            "-t",
            f"{segment.duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            crf,
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def escape_concat_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")


def concat_segments(ffmpeg: str, parts: Sequence[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.with_suffix(".concat.txt")
    list_file.write_text("\n".join(f"file '{escape_concat_path(part)}'" for part in parts) + "\n", encoding="utf-8")
    try:
        run_command([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output)])
    finally:
        list_file.unlink(missing_ok=True)


def burn_subtitles(ffmpeg: str, video: Path, srt: Path, output: Path, preset: str, crf: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_arg = f"subtitles='{escape_subtitles_filter_path(srt)}'"
    run_command(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video),
            "-vf",
            filter_arg,
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            crf,
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def build_metadata(clip: ClipSelection, draft_video: Path, local_srt: Path) -> dict:
    return {
        "id": clip.clip_id,
        "hook_line": clip.hook_line,
        "suggested_title": clip.suggested_title,
        "suggested_caption": clip.suggested_caption,
        "segments": [
            {
                "start_seconds": segment.start,
                "end_seconds": segment.end,
                "duration_seconds": segment.duration,
                "text": segment.text,
            }
            for segment in clip.segments
        ],
        "outputs": {"draft_video": str(draft_video), "local_srt": str(local_srt)},
        "raw_clip": clip.raw,
    }


def render_clip(ffmpeg: str, video: Path, cues: Sequence[Cue], clip: ClipSelection, output_dir: Path, preset: str, crf: str) -> dict:
    clip_dir = output_dir / clip.clip_id
    clip_dir.mkdir(parents=True, exist_ok=True)
    local_srt = clip_dir / f"{clip.clip_id}.local.srt"
    local_srt.write_text(build_local_srt(cues, clip.segments), encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix=f"{clip.clip_id}-", dir=str(clip_dir)) as tmp_name:
        tmp_dir = Path(tmp_name)
        parts: list[Path] = []
        for index, segment in enumerate(clip.segments, start=1):
            part = tmp_dir / f"part-{index:02d}.mp4"
            cut_segment(ffmpeg, video, segment, part, preset, crf)
            parts.append(part)
        concat_input = parts[0]
        if len(parts) > 1:
            concat_input = tmp_dir / f"{clip.clip_id}.concat.mp4"
            concat_segments(ffmpeg, parts, concat_input)
        draft_video = clip_dir / f"{clip.clip_id}.draft.mp4"
        burn_subtitles(ffmpeg, concat_input, local_srt, draft_video, preset, crf)

    metadata_path = clip_dir / f"{clip.clip_id}.metadata.json"
    metadata = build_metadata(clip, draft_video, local_srt)
    metadata["outputs"]["metadata"] = str(metadata_path)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def existing_file(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"File does not exist: {value}")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=existing_file, help="Source video file")
    parser.add_argument("--subtitles", required=True, type=existing_file, help="Source SRT subtitle file")
    parser.add_argument("--selection", required=True, type=existing_file, help="Selection JSON produced by the skill")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for rendered draft clips")
    parser.add_argument("--preset", default="veryfast", help="libx264 preset for draft rendering")
    parser.add_argument("--crf", default="23", help="libx264 CRF for draft rendering")
    args = parser.parse_args(argv)

    if args.subtitles.suffix.lower() != ".srt":
        raise SystemExit("Draft subtitle burning currently requires an .srt subtitle file")

    ffmpeg = ffmpeg_exe()
    cues = parse_srt(args.subtitles.read_text(encoding="utf-8", errors="ignore"))
    if not cues:
        raise SystemExit(f"No SRT cues found in {args.subtitles}")
    clips = load_selection_clips(args.selection)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    exported = []
    for clip in clips:
        exported.append(render_clip(ffmpeg, args.video, cues, clip, args.output_dir, args.preset, args.crf))
        print(f"Rendered {clip.clip_id}")

    manifest = {
        "source_video": str(args.video),
        "source_subtitles": str(args.subtitles),
        "selection": str(args.selection),
        "clips": exported,
    }
    manifest_path = args.output_dir / "draft-render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


