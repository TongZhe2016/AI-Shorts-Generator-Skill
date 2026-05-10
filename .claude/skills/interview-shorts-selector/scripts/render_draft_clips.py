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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
