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
