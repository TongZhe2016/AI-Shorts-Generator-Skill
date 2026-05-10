---
name: interview-shorts-selector
description: Select high-potential short-video clips from long interview subtitles or transcripts, and optionally render local draft MP4 clips when the user provides the matching source video and SRT subtitles. Use when the user provides `.srt`, `.ass`, or timestamped `.txt` subtitles and asks to find viral, traffic-worthy, knowledge/opinion, or personal-story clips; write ranked clip recommendations to a local output file with timecodes, full segment text, hook line, core claim, context-integrity checks, risk label, Chinese title, and publishing caption. Draft rendering does not download, transcribe, translate, crop, or polish videos.
---

# Interview Shorts Selector

Select short-video candidates from timestamped interview subtitles. Optimize for traffic potential without misleading context. Optionally render review-grade draft MP4 clips from a local source video, a matching SRT file, and the saved selection JSON.

## Scope

Do:
- Read `.srt`, `.ass`, or timestamped `.txt` subtitles supplied by the user.
- Recommend 30-120 second clips from 30 minute to 2 hour interviews.
- Prefer knowledge/opinion clips; switch to personal-story clips when the material naturally fits.
- Allow multi-segment clips when a hook, explanation, or context appears in separate places.
- Write complete JSON with timecodes, full text, rationale, context checks, risk, title, and caption to a local output file.
- When the user provides a local source video, matching source SRT, and selection JSON, render draft MP4 clips with original subtitles burned in by running `scripts/render_draft_clips.py`.

Do not:
- Download videos, transcribe audio, translate subtitles, crop vertical video, add music, create thumbnails, or produce polished final edits.
- Invent claims not supported by the transcript.
- Turn a joke, hypothetical, or quoted view into the guest's own position.
- Choose a clip only because it is explosive if it becomes misleading without surrounding context.
- Promise burned-subtitle draft rendering for `.ass` or timestamped `.txt` inputs unless they have been converted to SRT first.

## Defaults

If the user does not specify otherwise:
- Return 8 ranked candidates.
- Target 30-120 seconds per clip.
- Use Chinese output.
- Use knowledge/opinion mode first and personal-story mode as fallback.
- Prefer one continuous segment; allow up to 3 segments only when needed.
- Write the full JSON result to a local `.json` file by default, and reply only with the saved file path plus a short Chinese summary. If the user explicitly asks to print JSON in chat, print it in chat after saving the file unless they request chat-only output.
- Draft rendering is opt-in and only runs when the user asks for draft videos and provides local video plus SRT paths.

## Workflow

1. Parse the subtitle input and preserve timecodes. Normalize timestamps to `HH:MM:SS.mmm`.
2. Build a content map before selecting clips: topics, dense opinion zones, story arcs, emotional peaks, strong hooks, and sensitive context.
3. Generate 12-16 rough candidates for an 8-clip target.
4. Construct each candidate as a continuous segment unless a multi-segment structure is necessary for hook, explanation, payoff, or context integrity.
5. Check every candidate for context integrity and risk before ranking.
6. Dedupe overlapping or repetitive candidates; keep the one with stronger hook, clearer claim, and lower context risk.
7. Output the highest-ranked candidates using the required schema.
8. Save the complete result to a local JSON file before replying. Use the source subtitle directory by default, with filename `<subtitle_stem>_shorts_selection.json`; if that path is not writable, use the current working directory. If the user specifies an output path or format, follow it.
9. In the chat response, do not paste the full JSON by default. Report the output file path, clip count, and a brief Chinese summary of the top recommendations and risks.
10. Optional draft rendering: if the user asks for draft videos and provides a local source video plus matching `.srt`, run:

```powershell
python .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py `
  --video source.mp4 `
  --subtitles source.srt `
  --selection source_shorts_selection.json `
  --output-dir drafts
```

Report the output directory, exported clip count, skipped clips if any, and exact blockers if rendering fails.

## Draft rendering output

The renderer creates:

```text
drafts/
  clip-01/
    clip-01.draft.mp4
    clip-01.local.srt
    clip-01.metadata.json
  draft-render-manifest.json
```

Multi-segment clips are cut segment-by-segment, concatenated in JSON order, and given a rebased local SRT timeline before subtitle burn-in. `hook_line`, `suggested_title`, and `suggested_caption` are copied into per-clip metadata for future hook-card/title-card workflows.

## When to read references

- Read `references/selection-framework.md` before analyzing real interview subtitles or when deciding between knowledge/opinion, personal-story, and risky/controversial candidates.
- Read `references/output-schema.md` before producing final output, when the user asks for machine-readable JSON, or before draft rendering from a saved selection file.

## Critical rules

- Keep the clip fair to the original speaker and interview context.
- Include the complete subtitle text for every selected segment.
- For multi-segment clips, set `duration_seconds` to the sum of selected segment durations, not the wall-clock gap.
- Mark risky candidates as `中` or `高` and explain how titles/captions could mislead.
- If timestamps are absent, state that precise clip boundaries require timestamped subtitles and provide approximate text-based suggestions only.
- If fewer than 8 strong candidates exist, write fewer candidates and explain why rather than padding with weak clips.
- Save the complete JSON artifact to disk before claiming the selection is done; never rely on chat-only output unless the user explicitly asks for chat-only output.
- Burned-subtitle draft rendering currently requires a source `.srt`; for `.ass` or timestamped `.txt`, ask the user to convert to SRT or render without promising burned subtitles.
- Draft videos are review aids, not final polished social-platform edits.
