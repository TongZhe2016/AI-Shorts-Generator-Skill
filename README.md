# Interview Shorts Selector Skill

A subtitle-first skill for selecting short-video candidates from long interviews, with optional local draft-video rendering when you already have the matching source video and SRT subtitles.

The core job is still selection: given timestamped subtitles, recommend high-potential short-video clips with complete context, full text, risk checks, titles, and publishing captions. The optional renderer can then turn the saved JSON selections into review-grade MP4 drafts with original subtitles burned in.

## What it does

Use this skill when you already have interview subtitles in `.srt`, `.ass`, or timestamped `.txt` format and want to find clips suitable for Shorts, Reels, TikTok, 小红书, B站, or similar platforms.

The skill helps identify:

- Knowledge/opinion clips with concentrated ideas.
- Strong opening statements that can stop scrolling.
- Personal-story clips when the guest's experience is the strongest material.
- Multi-segment clips when a hook, explanation, and payoff appear in separate places.
- Context-safe cuts that avoid misleading the speaker's meaning.
- Optional review-grade draft MP4s when a local source video and matching SRT are available.

## What it does not do

It does not:

- Download source videos.
- Transcribe audio.
- Translate subtitles.
- Auto-crop vertical clips.
- Add music, thumbnails, transitions, or polished motion graphics.
- Require an OpenAI API key for the bundled renderer.

## Skill location

```text
.claude/skills/interview-shorts-selector/
├── SKILL.md
├── scripts/
│   └── render_draft_clips.py
└── references/
    ├── selection-framework.md
    └── output-schema.md
```

## How to use: selection only

Ask Codex or Claude to use the skill, then provide a subtitle file or paste timestamped subtitle text.

Example request:

```text
Use the interview-shorts-selector skill. Read this SRT file and recommend 8 short-video clips. Prefer knowledge/opinion clips, but use personal-story clips if they are stronger. Save JSON plus a short Chinese summary.
```

Default output includes:

- Ranked clip IDs.
- Start/end timecodes.
- One or more selected segments.
- Full subtitle text for each segment.
- Combined full text.
- Hook line.
- Core claim.
- Why it may perform.
- Context integrity check.
- Risk label and reason.
- Chinese title and caption.

## Optional draft video rendering

If you also have the original local video and matching SRT subtitles, the skill can render review-grade draft clips from the saved selection JSON.

```powershell
python .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py `
  --video source.mp4 `
  --subtitles source.srt `
  --selection source_shorts_selection.json `
  --output-dir drafts
```

The renderer outputs `clip-id.draft.mp4`, `clip-id.local.srt`, and `clip-id.metadata.json` per clip, plus a `draft-render-manifest.json`. Multi-segment clips are cut separately and concatenated; subtitle timestamps are rebased to the draft timeline.

This is not polished editing: it does not download, transcribe, translate, crop vertical video, add music, or create thumbnails. Burned subtitles currently require SRT.

### Prerequisites for rendering

The renderer uses FFmpeg. It first looks for system `ffmpeg` on `PATH`, then falls back to the Python package `imageio-ffmpeg`.

If FFmpeg is missing, install one of:

```powershell
python -m pip install --user imageio-ffmpeg
```

or install FFmpeg system-wide and make sure `ffmpeg` is on `PATH`.

## Output shape

```json
{
  "source": {
    "file": "example.srt",
    "language": "zh",
    "duration_estimate": "01:23:45",
    "input_type": "srt"
  },
  "selection_profile": {
    "primary_mode": "knowledge-opinion",
    "fallback_mode": "personal-story",
    "target_clip_count": 8,
    "duration_range_seconds": [30, 120],
    "multi_segment_allowed": true
  },
  "clips": []
}
```

See `examples/sample-output.json` for a complete example.

## Principle

The core principle is:

> Maximize traffic potential without breaking context integrity.

A clip should be strong enough to attract viewers, but not so aggressively packaged that it distorts the guest's meaning.
