---
name: interview-shorts-selector
description: Select high-potential short-video clips from long interview subtitles or transcripts. Use when the user provides `.srt`, `.ass`, or timestamped `.txt` subtitles and asks to find viral, traffic-worthy, knowledge/opinion, or personal-story clips; output ranked clip recommendations with timecodes, full segment text, hook line, core claim, context-integrity checks, risk label, Chinese title, and publishing caption. This skill does not download, transcribe, cut, crop, render, or edit videos.
---

# Interview Shorts Selector

Select short-video candidates from timestamped interview subtitles. Optimize for traffic potential without misleading context.

## Scope

Do:
- Read `.srt`, `.ass`, or timestamped `.txt` subtitles supplied by the user.
- Recommend 30-120 second clips from 30 minute to 2 hour interviews.
- Prefer knowledge/opinion clips; switch to personal-story clips when the material naturally fits.
- Allow multi-segment clips when a hook, explanation, or context appears in separate places.
- Output complete JSON with timecodes, full text, rationale, context checks, risk, title, and caption.

Do not:
- Download videos, transcribe audio, cut clips, crop vertical video, burn subtitles, or call a separate API/CLI.
- Invent claims not supported by the transcript.
- Turn a joke, hypothetical, or quoted view into the guest's own position.
- Choose a clip only because it is explosive if it becomes misleading without surrounding context.

## Defaults

If the user does not specify otherwise:
- Return 8 ranked candidates.
- Target 30-120 seconds per clip.
- Use Chinese output.
- Use knowledge/opinion mode first and personal-story mode as fallback.
- Prefer one continuous segment; allow up to 3 segments only when needed.
- Return JSON plus a short Chinese summary. If the user asks for JSON only, return JSON only.

## Workflow

1. Parse the subtitle input and preserve timecodes. Normalize timestamps to `HH:MM:SS.mmm`.
2. Build a content map before selecting clips: topics, dense opinion zones, story arcs, emotional peaks, strong hooks, and sensitive context.
3. Generate 12-16 rough candidates for an 8-clip target.
4. Construct each candidate as a continuous segment unless a multi-segment structure is necessary for hook, explanation, payoff, or context integrity.
5. Check every candidate for context integrity and risk before ranking.
6. Dedupe overlapping or repetitive candidates; keep the one with stronger hook, clearer claim, and lower context risk.
7. Output the highest-ranked candidates using the required schema.

## When to read references

- Read `references/selection-framework.md` before analyzing real interview subtitles or when deciding between knowledge/opinion, personal-story, and risky/controversial candidates.
- Read `references/output-schema.md` before producing final output or when the user asks for machine-readable JSON.

## Critical rules

- Keep the clip fair to the original speaker and interview context.
- Include the complete subtitle text for every selected segment.
- For multi-segment clips, set `duration_seconds` to the sum of selected segment durations, not the wall-clock gap.
- Mark risky candidates as `中` or `高` and explain how titles/captions could mislead.
- If timestamps are absent, state that precise clip boundaries require timestamped subtitles and provide approximate text-based suggestions only.
- If fewer than 8 strong candidates exist, return fewer candidates and explain why rather than padding with weak clips.
