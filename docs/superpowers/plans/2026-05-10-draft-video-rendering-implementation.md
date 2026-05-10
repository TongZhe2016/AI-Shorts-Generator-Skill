# Draft Video Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional local draft-video rendering to `interview-shorts-selector`, producing one burned-subtitle draft MP4 per selected JSON clip.

**Architecture:** Add one deterministic Python CLI at `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`. The CLI owns timecode parsing, SRT parsing/windowing, FFmpeg cut/concat/burn orchestration, and per-clip metadata output; docs teach agents when and how to use it.

**Tech Stack:** Python 3 standard library, FFmpeg or `imageio-ffmpeg` fallback, existing skill Markdown docs, JSON/SRT fixtures.

---

## File Structure

- Create: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`
  - Responsibility: command-line draft renderer and all helper functions for timestamp parsing, SRT parsing, subtitle rebasing, FFmpeg discovery, segment cutting, concat, subtitle burn-in, and metadata writing.
- Create: `tests/test_render_draft_clips.py`
  - Responsibility: fast Python unit tests for timestamp parsing, SRT parsing, local SRT rebasing, and selection JSON validation. No FFmpeg dependency.
- Modify: `.claude/skills/interview-shorts-selector/SKILL.md`
  - Responsibility: document optional draft rendering workflow and limitations.
- Modify: `.claude/skills/interview-shorts-selector/references/output-schema.md`
  - Responsibility: document renderer-relevant schema fields and SRT-only draft subtitle support.
- Modify: `README.md`
  - Responsibility: user-facing selection-only and draft-rendering instructions.
- Modify: `.gitignore`
  - Responsibility: ignore generated draft media folders and Windows `desktop.ini` noise.

## Task 1: Add test scaffold for renderer helpers

**Files:**
- Create: `tests/test_render_draft_clips.py`
- Create later in Task 2: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`

- [ ] **Step 1: Create failing tests for timestamp parsing and formatting**

Create `tests/test_render_draft_clips.py` with this initial content:

```python
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "interview-shorts-selector" / "scripts" / "render_draft_clips.py"
spec = importlib.util.spec_from_file_location("render_draft_clips", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_parse_timecode_accepts_dot_and_comma_milliseconds():
    assert renderer.parse_timecode("00:01:02.345") == 62.345
    assert renderer.parse_timecode("00:01:02,345") == 62.345


def test_format_srt_time_rounds_to_milliseconds():
    assert renderer.format_srt_time(62.3454) == "00:01:02,345"
    assert renderer.format_srt_time(62.3456) == "00:01:02,346"
```

- [ ] **Step 2: Run test to verify it fails because the script does not exist**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: FAIL or collection error mentioning `render_draft_clips.py` is missing.

## Task 2: Implement timestamp helpers

**Files:**
- Create: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`
- Test: `tests/test_render_draft_clips.py`

- [ ] **Step 1: Add minimal timestamp helper implementation**

Create `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py` with:

```python
#!/usr/bin/env python3
"""Render draft interview-short clips from selection JSON, source video, and SRT subtitles."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

TIMECODE_RE = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?P<sep>[,.])(?P<ms>\d{1,3})$")


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run timestamp tests**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: PASS for 2 tests.

- [ ] **Step 3: Commit timestamp helper baseline**

Run:

```powershell
git add -- tests/test_render_draft_clips.py .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
git commit -m "test: add renderer timestamp helpers"
```

## Task 3: Add SRT parsing and local subtitle rebasing

**Files:**
- Modify: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`
- Modify: `tests/test_render_draft_clips.py`

- [ ] **Step 1: Add failing tests for SRT parsing and multi-segment rebasing**

Append to `tests/test_render_draft_clips.py`:

```python

def test_parse_srt_reads_cues_with_multiline_text():
    cues = renderer.parse_srt("""1\n00:00:10,000 --> 00:00:12,500\n第一行\n第二行\n\n2\n00:00:15.000 --> 00:00:16.000\n下一句\n""")

    assert len(cues) == 2
    assert cues[0].start == 10.0
    assert cues[0].end == 12.5
    assert cues[0].text == "第一行\n第二行"
    assert cues[1].start == 15.0


def test_build_local_srt_rebases_multiple_segments():
    cues = renderer.parse_srt("""1\n00:00:10,000 --> 00:00:12,000\nA\n\n2\n00:00:20,000 --> 00:00:22,000\nB\n""")
    segments = [renderer.Segment(10.0, 12.0, ""), renderer.Segment(20.0, 22.0, "")]

    local_srt = renderer.build_local_srt(cues, segments)

    assert "00:00:00,000 --> 00:00:02,000\nA" in local_srt
    assert "00:00:02,000 --> 00:00:04,000\nB" in local_srt
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: FAIL because `parse_srt`, `Segment`, and `build_local_srt` are not defined.

- [ ] **Step 3: Implement SRT parsing and rebasing**

Add these definitions after `format_srt_time` in `render_draft_clips.py`:

```python
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
        cues.append(Cue(parse_timecode(match.group("start")), parse_timecode(match.group("end")), "\n".join(text_lines).strip()))
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
            lines.extend([str(index), f"{format_srt_time(local_start)} --> {format_srt_time(local_end)}", cue.text, ""])
            index += 1
        local_offset += segment.duration
    return "\n".join(lines).strip() + ("\n" if lines else "")
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: PASS for 4 tests.

- [ ] **Step 5: Commit SRT helpers**

Run:

```powershell
git add -- tests/test_render_draft_clips.py .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
git commit -m "feat: add subtitle rebasing helpers"
```

## Task 4: Add selection loading and validation

**Files:**
- Modify: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`
- Modify: `tests/test_render_draft_clips.py`

- [ ] **Step 1: Add failing tests for selection JSON loading**

Append to `tests/test_render_draft_clips.py`:

```python

def test_load_selection_clips_validates_segments(tmp_path):
    selection = tmp_path / "selection.json"
    selection.write_text('{"clips":[{"id":"clip-01","segments":[{"start":"00:00:01.000","end":"00:00:03.000","text":"hello"}],"hook_line":"hook","suggested_title":"title"}]}', encoding="utf-8")

    clips = renderer.load_selection_clips(selection)

    assert clips[0].clip_id == "clip-01"
    assert clips[0].segments == [renderer.Segment(1.0, 3.0, "hello")]
    assert clips[0].hook_line == "hook"
    assert clips[0].suggested_title == "title"


def test_load_selection_clips_rejects_empty_segments(tmp_path):
    selection = tmp_path / "selection.json"
    selection.write_text('{"clips":[{"id":"clip-01","segments":[]}]}', encoding="utf-8")

    try:
        renderer.load_selection_clips(selection)
    except ValueError as exc:
        assert "clip-01" in str(exc)
        assert "segments" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: FAIL because `load_selection_clips` and `clip_id` model are missing.

- [ ] **Step 3: Implement selection loading**

Add this dataclass after `Cue` and this function after `build_local_srt`:

```python
@dataclass(frozen=True)
class ClipSelection:
    clip_id: str
    segments: list[Segment]
    hook_line: str = ""
    suggested_title: str = ""
    suggested_caption: str = ""
    raw: dict | None = None


def load_selection_clips(path: Path) -> list[ClipSelection]:
    data = json.loads(path.read_text(encoding="utf-8"))
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
            raise ValueError(f"{clip_id} must contain at least one segment with start and end")
        segments: list[Segment] = []
        for seg_position, raw_segment in enumerate(raw_segments, start=1):
            if not isinstance(raw_segment, dict):
                raise ValueError(f"{clip_id} segment #{seg_position} must be an object")
            start_value = raw_segment.get("start")
            end_value = raw_segment.get("end")
            if not start_value or not end_value:
                raise ValueError(f"{clip_id} segment #{seg_position} must include start and end")
            segment = Segment(parse_timecode(str(start_value)), parse_timecode(str(end_value)), str(raw_segment.get("text") or ""))
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
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: PASS for 6 tests.

- [ ] **Step 5: Commit selection loading**

Run:

```powershell
git add -- tests/test_render_draft_clips.py .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
git commit -m "feat: load clip selections for rendering"
```

## Task 5: Add FFmpeg rendering CLI

**Files:**
- Modify: `.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py`
- Modify: `tests/test_render_draft_clips.py`

- [ ] **Step 1: Add failing tests for FFmpeg path escaping and output metadata shape**

Append to `tests/test_render_draft_clips.py`:

```python

def test_escape_subtitles_filter_path_handles_windows_drive():
    escaped = renderer.escape_subtitles_filter_path(Path(r"C:\Users\me\字幕 file.srt"))
    assert "\\:" in escaped
    assert "字幕 file.srt" in escaped


def test_build_metadata_contains_hook_and_paths(tmp_path):
    clip = renderer.ClipSelection(
        clip_id="clip-01",
        segments=[renderer.Segment(1.0, 3.0, "hello")],
        hook_line="hook",
        suggested_title="title",
        suggested_caption="caption",
        raw={"id": "clip-01"},
    )
    metadata = renderer.build_metadata(clip, tmp_path / "clip-01.draft.mp4", tmp_path / "clip-01.local.srt")

    assert metadata["id"] == "clip-01"
    assert metadata["hook_line"] == "hook"
    assert metadata["suggested_title"] == "title"
    assert metadata["outputs"]["draft_video"].endswith("clip-01.draft.mp4")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: FAIL because `escape_subtitles_filter_path` and `build_metadata` are missing.

- [ ] **Step 3: Implement FFmpeg orchestration and CLI**

Extend `render_draft_clips.py` with these functions before `main`, and replace `main` with the CLI implementation:

```python
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
    raw = raw.replace(":", "\\:").replace("'", "\\'")
    return raw


def cut_segment(ffmpeg: str, video: Path, segment: Segment, output: Path, preset: str, crf: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_command([
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
    ])


def concat_segments(ffmpeg: str, parts: Sequence[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.with_suffix(".concat.txt")
    list_file.write_text("\n".join(f"file '{part.resolve().as_posix().replace("'", "'\\''")}'" for part in parts) + "\n", encoding="utf-8")
    try:
        run_command([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output)])
    finally:
        list_file.unlink(missing_ok=True)


def burn_subtitles(ffmpeg: str, video: Path, srt: Path, output: Path, preset: str, crf: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_arg = f"subtitles='{escape_subtitles_filter_path(srt)}'"
    run_command([
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
    ])


def build_metadata(clip: ClipSelection, draft_video: Path, local_srt: Path) -> dict:
    return {
        "id": clip.clip_id,
        "hook_line": clip.hook_line,
        "suggested_title": clip.suggested_title,
        "suggested_caption": clip.suggested_caption,
        "segments": [
            {"start_seconds": segment.start, "end_seconds": segment.end, "duration_seconds": segment.duration, "text": segment.text}
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
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata["outputs"]["metadata"] = str(metadata_path)
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

    manifest = {"source_video": str(args.video), "source_subtitles": str(args.subtitles), "selection": str(args.selection), "clips": exported}
    manifest_path = args.output_dir / "draft-render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    return 0
```

If the nested quote in `concat_segments` is error-prone, replace that function with a helper that escapes concat paths in a separate statement before building the list string.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
```

Expected: PASS for 8 tests.

- [ ] **Step 5: Run Python compile check**

Run:

```powershell
python -m py_compile .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit renderer CLI**

Run:

```powershell
git add -- tests/test_render_draft_clips.py .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
git commit -m "feat: render draft clips from selections"
```

## Task 6: Validate with generated dummy video

**Files:**
- Use generated files under ignored output directory only.

- [ ] **Step 1: Confirm FFmpeg availability**

Run:

```powershell
python - <<'PY'
from pathlib import Path
import importlib.util
script = Path('.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py').resolve()
spec = importlib.util.spec_from_file_location('render_draft_clips', script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.ffmpeg_exe())
PY
```

Expected: prints an FFmpeg executable path.

- [ ] **Step 2: Generate dummy validation video**

Run:

```powershell
$ffmpeg = python - <<'PY'
from pathlib import Path
import importlib.util
script = Path('.claude/skills/interview-shorts-selector/scripts/render_draft_clips.py').resolve()
spec = importlib.util.spec_from_file_location('render_draft_clips', script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.ffmpeg_exe())
PY
New-Item -ItemType Directory -Force -Path output/render-test | Out-Null
& $ffmpeg -y -f lavfi -i testsrc=size=640x360:rate=25 -f lavfi -i sine=frequency=1000:sample_rate=44100 -t 210 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac output/render-test/source.mp4
```

Expected: `output/render-test/source.mp4` exists.

- [ ] **Step 3: Render fixture clips**

Run:

```powershell
python .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py --video output/render-test/source.mp4 --subtitles examples/sample-input.srt --selection examples/sample-output.json --output-dir output/render-test/drafts --preset ultrafast --crf 28
```

Expected: prints `Rendered clip-01`, `Rendered clip-02`, and manifest path.

- [ ] **Step 4: Verify output files and rebased subtitles**

Run:

```powershell
Test-Path output/render-test/drafts/clip-01/clip-01.draft.mp4
Test-Path output/render-test/drafts/clip-01/clip-01.local.srt
Test-Path output/render-test/drafts/clip-02/clip-02.draft.mp4
Test-Path output/render-test/drafts/clip-02/clip-02.local.srt
Get-Content output/render-test/drafts/clip-02/clip-02.local.srt -TotalCount 12
```

Expected: all `Test-Path` commands print `True`; clip-02 local SRT starts at `00:00:00,000` and second segment appears after the first segment duration, not at the original wall-clock timestamp.

## Task 7: Update skill docs and repository ignore rules

**Files:**
- Modify: `.claude/skills/interview-shorts-selector/SKILL.md`
- Modify: `.claude/skills/interview-shorts-selector/references/output-schema.md`
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Update `.gitignore`**

Append these lines if they are not already present:

```gitignore
# Generated local draft-render outputs
output/
drafts/
*.mp4
*.mov
*.mkv
*.srt.tmp

# Windows / cloud-drive metadata
desktop.ini
```

- [ ] **Step 2: Update `SKILL.md` scope and workflow**

Edit `.claude/skills/interview-shorts-selector/SKILL.md` so:

- `description` mentions optional local draft video rendering when source video and SRT are provided.
- `Do:` includes rendering draft MP4s from existing selection JSON.
- `Do not:` keeps no download/transcription/translation/polished editing.
- Workflow adds a final optional draft-rendering step with the exact command.
- Critical rules state SRT is required for burned draft subtitles.

- [ ] **Step 3: Update `output-schema.md`**

Add a short section named `Draft rendering compatibility` explaining:

```markdown
## Draft rendering compatibility

The optional draft renderer reads `clips[].segments[].start` and `clips[].segments[].end` as the source-video cut boundaries. `hook_line`, `suggested_title`, and `suggested_caption` are copied into per-clip metadata for future hook-card/title-card workflows. Burned subtitles currently require a source `.srt`; timestamped `.txt` can be selected but cannot be burned by the renderer without conversion.
```

- [ ] **Step 4: Update `README.md`**

Add sections:

```markdown
## Optional draft video rendering

If you also have the original local video and matching SRT subtitles, the skill can render review-grade draft clips from the saved selection JSON.

```powershell
python .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py `
  --video source.mp4 `
  --subtitles source.srt `
  --selection source_shorts_selection.json `
  --output-dir drafts
```

The renderer outputs `clip-id.draft.mp4`, `clip-id.local.srt`, and `clip-id.metadata.json` per clip. Multi-segment clips are cut separately and concatenated; subtitle timestamps are rebased to the draft timeline.

This is not polished editing: it does not download, transcribe, translate, crop vertical video, add music, or create thumbnails. Burned subtitles currently require SRT.
```

- [ ] **Step 5: Run documentation sanity checks**

Run:

```powershell
Select-String -Path .claude/skills/interview-shorts-selector/SKILL.md,README.md -Pattern "render_draft_clips.py"
python -m json.tool examples/sample-output.json > $null
```

Expected: command references are found; JSON parses.

- [ ] **Step 6: Commit docs and ignore rules**

Run:

```powershell
git add -- .gitignore .claude/skills/interview-shorts-selector/SKILL.md .claude/skills/interview-shorts-selector/references/output-schema.md README.md
git commit -m "docs: document draft video rendering workflow"
```

## Task 8: Final verification and push

**Files:**
- No new source files beyond previous tasks.

- [ ] **Step 1: Run full local verification**

Run:

```powershell
python -m pytest tests/test_render_draft_clips.py -q
python -m py_compile .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py
python -m json.tool examples/sample-output.json > $null
git status --short --branch
```

Expected: tests pass, compile succeeds, JSON parses, git status has no tracked-file changes. Ignored `output/` and `desktop.ini` must not be staged.

- [ ] **Step 2: Inspect recent commits**

Run:

```powershell
git log --oneline --decorate -6
```

Expected: implementation commits appear above `docs: add draft video rendering design`.

- [ ] **Step 3: Push to GitHub**

Run:

```powershell
git push origin main
```

Expected: push succeeds.
