# Interview Shorts Selector Skill Design

Date: 2026-05-10
Repository: `AI-Shorts-Generator-Skill`
Target skill name: `interview-shorts-selector`

## 1. Background

The repository currently contains an end-to-end YouTube shorts generation workflow: download video, transcribe audio, rank highlights, and crop/render vertical clips. The user now wants a narrower and cleaner skill: given an existing interview transcript/subtitle file, select high-potential short-video segments and output structured recommendations. The skill must not download, transcribe, or edit video.

The expected source videos are long interviews, usually 30 minutes to 2 hours. The desired clips are roughly 30 seconds to 2 minutes. The best clips should either contain a concentrated idea, a strong opening statement, or a story/emotional turn, while preserving context and avoiding misleading out-of-context edits.

The main account positioning is knowledge/opinion content. If a particular interview is more naturally personal-story driven, the skill may shift toward story-based clip selection.

## 2. Goals

1. Rebuild the repository as a pure Codex/Claude skill repository for interview subtitle clip selection.
2. Accept `.srt`, `.ass`, or timestamped `.txt` subtitle content as input.
3. Output ranked clip recommendations, not rendered videos.
4. Default to 8 candidate clips, each 30-120 seconds.
5. Allow a clip to be composed of multiple non-contiguous subtitle segments when necessary for hook/context/payoff.
6. Include full subtitle text for each segment and each full clip.
7. Include hook, core claim, performance rationale, context integrity check, risk label, title, and caption.
8. Preserve context and explicitly guard against misleading edits.
9. Use references to keep `SKILL.md` concise while providing a detailed selection framework and output schema.

## 3. Non-goals

The skill will not:

- Download videos.
- Transcribe audio.
- Cut, crop, render, or subtitle videos.
- Call a standalone Python CLI or require an OpenAI API key.
- Invent unsupported claims not found in the subtitle text.
- Optimize thumbnails, music, visual layout, or upload metadata beyond simple title/caption suggestions.

## 4. Design Choice

Use a full pure-skill rebuild.

Final repository structure:

```text
AI-Shorts-Generator-Skill/
├── .claude/
│   └── skills/
│       └── interview-shorts-selector/
│           ├── SKILL.md
│           └── references/
│               ├── selection-framework.md
│               └── output-schema.md
├── examples/
│   ├── sample-input.srt
│   └── sample-output.json
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-10-interview-shorts-selector-design.md
└── README.md
```

Remove old end-to-end implementation files:

```text
main.py
requirements.txt
requirements-local.txt
.env.example
shorts_generator/
.claude/skills/youtube-shorts-generator/
```

Rationale: leaving old video-processing entry points would make the repository confusing. The selected approach makes the repo match the actual intended workflow: subtitle in, clip recommendations out.

## 5. Borrowed Ideas from Existing Repos

The new skill should borrow the useful parts of the existing related projects without preserving their old scope.

From the current `AI-Shorts-Generator-Skill` / `AI-Youtube-Shorts-Generator` workflow:

- Virality criteria: hook, emotional peak, opinion bomb, revelation, conflict, quotable line, story peak, practical value.
- Long-video handling: chunk long transcripts and dedupe overlapping candidates.
- Candidate ranking: ask for more candidates than needed, then sort and prune.

From `yt-short-clipper`:

- Strict production-oriented output format.
- Strong duration validation.
- Emphasis on exact clip count where possible.
- Separation between finding highlights and later processing selected highlights.
- Explicit hook text and viral rationale for each candidate.

User-specific additions:

- Knowledge/opinion clips are primary.
- Personal-story clips are allowed when the material naturally supports them.
- Multi-part clips are allowed but must protect context.
- Full transcript text for each proposed segment must be included in output.
- Context integrity and risk must be first-class fields, not afterthoughts.

## 6. Skill Trigger and Defaults

The skill should trigger when the user asks to:

- Choose short-video clips from an interview subtitle file.
- Find traffic-potential clips from a transcript.
- Produce timecodes, text, titles, and captions without editing video.
- Identify strong hooks while avoiding out-of-context clipping.
- Select one or more parts of a transcript to combine into a single short.

Defaults when the user does not specify otherwise:

- Candidate count: 8.
- Duration range: 30-120 seconds.
- Primary mode: knowledge/opinion.
- Fallback mode: personal story.
- Output language: Chinese.
- Output format: JSON plus a short Chinese summary.
- Multi-segment clips: allowed, but only when useful and not more than 3 segments by default.

## 7. Workflow

### Step 1: Parse and normalize subtitle input

Read the subtitle file or pasted text. Preserve timecodes. Normalize timestamps to `HH:MM:SS.mmm`.

Supported input types:

- `.srt`: index + time range + text blocks.
- `.ass`: dialogue lines with start/end timestamps.
- `.txt`: timestamped lines or transcript blocks. If timestamps are missing, explain that precise clip output requires timestamps.

### Step 2: Build a content map

Before picking clips, identify:

- Main topics.
- Dense knowledge/opinion zones.
- Personal-story arcs.
- High-emotion moments.
- Strong opening statements.
- Contrarian or surprising claims.
- Necessary context around sensitive statements.

For long transcripts, work in chunks by time/topic, then merge candidates globally.

### Step 3: Generate candidate pool

Generate more candidates than final output, usually 12-16 for an 8-clip target.

Candidate types:

1. Knowledge/opinion: clear claim, explanation, implication, takeaway.
2. Strong hook: opening line has curiosity, tension, or a sharp claim.
3. Personal story: setup, turning point, payoff.
4. Practical insight: concrete lesson or mental model.
5. Debate/risk segment: only if context is clear and risk can be controlled.

### Step 4: Segment construction

Prefer a single continuous segment.

Allow multiple non-contiguous segments only when:

- Segment 1 provides a strong hook and segment 2 provides the necessary explanation.
- Two moments are part of the same argument chain.
- A later segment supplies context needed to avoid misleading interpretation.
- The final combined clip still feels watchable and coherent.

Default maximum: 3 segments per clip.

Do not combine unrelated remarks just because each is individually strong.

### Step 5: Context integrity check

For every candidate, check:

- Is any key premise missing?
- Is a limitation or reversal omitted?
- Is a joke, hypothetical, or quote being framed as the speaker's own position?
- Does the title/caption exaggerate the original meaning?
- Would adding 5-10 seconds before/after reduce misinterpretation?
- Is the clip fair to the guest and interview context?

### Step 6: Score and rank

Each clip receives `score_100` using this weighting:

- `hook_strength` 20: the first seconds can stop scrolling.
- `core_claim_strength` 20: the idea is focused, fresh, and understandable.
- `context_integrity` 20: the clip is complete and not misleading.
- `retention_structure` 15: setup, escalation, turn, payoff, or conclusion.
- `shareability` 15: it can drive comments, saves, reposts, or discussion.
- `risk_control` 10: controversy and reputational risk are manageable.

Risk labels:

- `低`: clear context, low controversy, low chance of misreading.
- `中`: potentially sensitive or easily over-titled; needs careful title/caption.
- `高`: high risk of controversy, personal attack, legal/reputation issues, or misleading edits. Include only if the user explicitly wants risky cuts or if its value is exceptional and context is very clear.

### Step 7: Output

Output JSON with `source`, `selection_profile`, and `clips`. After JSON, include a short Chinese summary listing top 3 recommendations and any warnings. If the user explicitly requests JSON only, output JSON only.

## 8. Output Schema

Top-level object:

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

Clip object:

```json
{
  "id": "clip-01",
  "rank": 1,
  "score_100": 88,
  "start": "00:12:03.000",
  "end": "00:13:28.000",
  "duration_seconds": 85,
  "segments": [
    {
      "start": "00:12:03.000",
      "end": "00:13:28.000",
      "text": "这一段内所有字幕文字的拼接总和"
    }
  ],
  "full_text": "所有 segments 文本拼接总和",
  "hook_line": "真正让人破防的是这一句……",
  "core_claim": "这段的核心观点",
  "why_it_may_perform": "为什么适合短视频传播",
  "context_integrity_check": {
    "verdict": "pass",
    "is_out_of_context": false,
    "reason": "前后语义完整，没有省略关键限定条件。",
    "needed_context": "无",
    "title_risk_note": "标题不能暗示嘉宾攻击某个人。"
  },
  "risk": "低",
  "risk_reason": "观点表达明确，争议较低。",
  "suggested_title": "中文标题",
  "suggested_caption": "发布文案"
}
```

For multi-segment clips:

- `start` is the first segment start.
- `end` is the last segment end.
- `duration_seconds` is the sum of included segment durations, not the wall-clock gap.
- `segments` contains each selected range and its exact subtitle text.
- `full_text` concatenates segment texts in viewing order.
- `context_integrity_check.reason` explains why the non-contiguous combination is fair.

## 9. Reference Files

### `references/selection-framework.md`

Include detailed guidance for:

- Knowledge/opinion mode.
- Personal-story fallback mode.
- Hook types that are strong but not misleading.
- Multi-segment combination rules.
- Context integrity checklist.
- Candidate dedupe and ranking.
- Risk labeling.

### `references/output-schema.md`

Include:

- Required top-level fields.
- Required clip fields.
- Timestamp format.
- Duration rules.
- Multi-segment semantics.
- Example JSON.

## 10. README

README should describe:

- What the skill does.
- What it does not do.
- How to install/copy the skill.
- How to ask Codex/Claude to use it.
- Example input and output.
- The principle: "traffic potential without misleading context."

README should not document video download/transcription/cropping workflows.

## 11. Examples

`examples/sample-input.srt` should be short and fictional, enough to demonstrate parsing and clip selection.

`examples/sample-output.json` should be valid JSON following the schema. It should include at least:

- One continuous clip.
- One multi-segment clip.
- Context integrity check.
- Risk fields.
- Chinese title and caption.

## 12. Validation Plan

After implementation:

1. Run skill validation with the skill creator validation script if available.
2. Check that the old video-processing entry points have been removed.
3. Confirm `examples/sample-output.json` parses as JSON.
4. Inspect `SKILL.md` frontmatter for correct name and description.
5. Run a small manual trial using a short excerpt from `2605杨晓燕/杨晓燕.srt` or `.txt` to confirm the skill guides the agent toward the expected schema and context checks.
6. Check git diff for accidental deletion of the design spec.

## 13. Open Decisions Resolved

- Use pure skill workflow, not a Python CLI.
- Fully remove old end-to-end video code.
- Default to knowledge/opinion clips.
- Use personal-story mode only when the material naturally fits.
- Use top-level `clips` and per-clip `segments`.
- Allow multi-segment clips, default maximum 3 segments.
- Include full text inside every output clip.
- Prioritize context integrity alongside virality.
