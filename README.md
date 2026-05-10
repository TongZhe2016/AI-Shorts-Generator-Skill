# Interview Shorts Selector Skill

A pure AI skill for selecting short-video candidates from long interview subtitles.

This repository no longer downloads, transcribes, cuts, crops, or renders videos. It focuses on one job: given timestamped subtitles, recommend high-potential short-video clips with complete context, full text, risk checks, titles, and publishing captions.

## What it does

Use this skill when you already have interview subtitles in `.srt`, `.ass`, or timestamped `.txt` format and want to find clips suitable for Shorts, Reels, TikTok, 小红书, B站, or similar platforms.

The skill helps identify:

- Knowledge/opinion clips with concentrated ideas.
- Strong opening statements that can stop scrolling.
- Personal-story clips when the guest's experience is the strongest material.
- Multi-segment clips when a hook, explanation, and payoff appear in separate places.
- Context-safe cuts that avoid misleading the speaker's meaning.

## What it does not do

It does not:

- Download source videos.
- Transcribe audio.
- Cut or render video files.
- Auto-crop vertical clips.
- Burn subtitles.
- Require an OpenAI API key or standalone CLI.

## Skill location

```text
.claude/skills/interview-shorts-selector/
├── SKILL.md
└── references/
    ├── selection-framework.md
    └── output-schema.md
```

## How to use

Ask Codex or Claude to use the skill, then provide a subtitle file or paste timestamped subtitle text.

Example request:

```text
Use the interview-shorts-selector skill. Read this SRT file and recommend 8 short-video clips. Prefer knowledge/opinion clips, but use personal-story clips if they are stronger. Return JSON plus a short Chinese summary.
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
