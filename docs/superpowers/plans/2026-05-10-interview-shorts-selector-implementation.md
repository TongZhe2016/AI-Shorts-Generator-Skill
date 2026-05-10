# Interview Shorts Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild this repository into a pure skill for selecting high-potential interview short-video clips from timestamped subtitles.

**Architecture:** Remove the old end-to-end video-processing code and replace it with a concise skill plus two reference documents and examples. `SKILL.md` contains the core workflow and navigation; `references/selection-framework.md` holds detailed selection heuristics; `references/output-schema.md` holds the JSON contract. README becomes the repository usage entry point.

**Tech Stack:** Markdown skill files, JSON examples, Git. No Python runtime or external API is required for the final skill.

---

## File Structure

Create/modify/remove these files:

- Create: `.claude/skills/interview-shorts-selector/SKILL.md` — skill metadata and core workflow.
- Create: `.claude/skills/interview-shorts-selector/references/selection-framework.md` — detailed clip selection and risk framework.
- Create: `.claude/skills/interview-shorts-selector/references/output-schema.md` — JSON output contract and example.
- Create: `examples/sample-input.srt` — short fictional subtitle input.
- Create: `examples/sample-output.json` — valid JSON demonstrating continuous and multi-segment clip output.
- Modify: `README.md` — repository overview and usage for the pure skill.
- Remove: `.claude/skills/youtube-shorts-generator/` — old video-generation skill.
- Remove: `main.py`, `requirements.txt`, `requirements-local.txt`, `.env.example`, `shorts_generator/` — old CLI and video-processing code.
- Keep: `docs/superpowers/specs/2026-05-10-interview-shorts-selector-design.md`.
- Keep: this implementation plan under `docs/superpowers/plans/`.

---

### Task 1: Confirm Safety and Baseline

**Files:**
- Read: repository git state

- [ ] **Step 1: Check branch, status, and recent commits**

Run:

```powershell
git branch --show-current
git status --short
git log --oneline -3
```

Expected:

- Current branch is `main`.
- Only the implementation plan may be untracked/modified before code changes.
- Recent log includes `docs: add interview shorts selector design`.

- [ ] **Step 2: Confirm old repository layout exists before removal**

Run:

```powershell
Test-Path .claude\skills\youtube-shorts-generator
Test-Path shorts_generator
Test-Path main.py
```

Expected output contains three `True` values before removal.

---

### Task 2: Create the New Skill Files

**Files:**
- Create: `.claude/skills/interview-shorts-selector/SKILL.md`
- Create: `.claude/skills/interview-shorts-selector/references/selection-framework.md`
- Create: `.claude/skills/interview-shorts-selector/references/output-schema.md`

- [ ] **Step 1: Create skill directories**

Run:

```powershell
New-Item -ItemType Directory -Force -Path .claude\skills\interview-shorts-selector\references | Out-Null
```

Expected: command succeeds with no output.

- [ ] **Step 2: Write `SKILL.md`**

Write this exact file:

```markdown
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
```

- [ ] **Step 3: Write `selection-framework.md`**

Write this exact file:

```markdown
# Selection Framework

Use this framework to choose short-video candidates from interview subtitles. The priority is traffic potential with context integrity.

## Selection modes

### Knowledge/opinion mode, primary

Prioritize clips where the speaker delivers a focused idea that can stand alone:

- A clear claim, judgment, or mental model.
- A counterintuitive explanation or reframing.
- A practical lesson viewers may save or share.
- A strong cause-and-effect chain.
- A concise answer to a question many viewers have.

A strong knowledge/opinion clip usually has:

1. Hook: a sentence that creates curiosity or tension.
2. Development: explanation, evidence, example, or contrast.
3. Payoff: conclusion, implication, advice, or memorable line.

Reject clips that are only topic labels, vague agreement, long setup without payoff, or generic information with no point of view.

### Personal-story mode, fallback

Use this mode when the transcript is more naturally driven by lived experience than abstract ideas.

Prioritize:

- Personal turning points.
- Vulnerability, regret, surprise, or relief.
- A story with setup, obstacle, choice, and consequence.
- A moment that changes how viewers perceive the person.

Reject story clips that lack a payoff or require too much outside context to understand.

### Risky/controversial mode, limited

Controversy can create reach, but never at the cost of fairness. Use only when:

- The speaker's actual meaning is clear.
- The clip includes enough context to prevent a false accusation.
- The suggested title does not exaggerate the target, certainty, or hostility.

Mark risk `中` or `高` when a clip involves personal criticism, institutional accusations, medical/legal/financial claims, identity groups, politics, or reputational harm.

## Virality signals

Rank candidates by these signals:

1. Strong hook: the opening line creates curiosity, surprise, disagreement, or emotional pull.
2. Core claim: the clip has one main point, not several loose topics.
3. Cognitive gap: viewers learn a frame they did not expect.
4. Emotional texture: the speaker shows conviction, vulnerability, humor, anger, or surprise.
5. Retention shape: setup, escalation, turn, and payoff are visible.
6. Shareability: the idea can spark comments, saves, reposts, or debate.
7. Quotability: one sentence can become a title, cover line, or caption opener.
8. Practical value: the viewer can apply or remember the idea.

## Duration rules

Default duration range: 30-120 seconds.

- 30-45 seconds: use for tight claims, punchy reframes, or concise Q&A.
- 45-90 seconds: ideal for most knowledge/opinion clips.
- 90-120 seconds: use for stories or arguments that need setup and payoff.
- Over 120 seconds: avoid unless the user explicitly asks for longer clips.

Do not cut mid-sentence or mid-thought. Add a few seconds before or after when needed to preserve grammar and meaning.

## Multi-segment rules

Prefer continuous clips. Use multiple segments only when the final short becomes more coherent or fair.

Valid multi-segment patterns:

- Hook + explanation: an early sharp line becomes clear only with a later explanation.
- Claim + evidence: two separated parts form one argument chain.
- Setup + payoff: a story's premise and conclusion are separated by filler.
- Context repair: a later line prevents the hook from becoming misleading.

Invalid multi-segment patterns:

- Combining unrelated viral lines.
- Joining contradictory statements without explaining the shift.
- Removing the speaker's caveat to make a stronger claim.
- Creating a conclusion the speaker never made.

Default maximum: 3 segments. If more than 3 segments are needed, the candidate is probably not a good short.

## Context integrity checklist

For each candidate, answer these checks before final output:

- Are the speaker's premise and conclusion both present?
- Is an important caveat, reversal, or limitation missing?
- Is the speaker quoting or describing someone else's view?
- Is the statement a joke, hypothetical, or exaggeration?
- Would the title/caption make the claim sound more absolute than it is?
- Would 5-10 seconds of adjacent context materially reduce misunderstanding?
- Is the clip fair to the guest, interviewer, and named third parties?

Use `context_integrity_check.verdict`:

- `pass`: safe and complete.
- `needs_context`: usable only if the listed context is included.
- `reject`: too misleading or incomplete to recommend.

Do not include `reject` candidates in the final `clips` array unless the user explicitly asks to see rejected candidates.

## Scoring

Assign `score_100` using this weighting:

- `hook_strength` 20 points.
- `core_claim_strength` 20 points.
- `context_integrity` 20 points.
- `retention_structure` 15 points.
- `shareability` 15 points.
- `risk_control` 10 points.

Interpretation:

- 90-100: exceptional; likely top clip if context is safe.
- 80-89: strong candidate; should usually be included.
- 70-79: usable; include if it adds topic diversity.
- 60-69: borderline; include only if few strong clips exist.
- Below 60: do not include by default.

## Dedupe rules

When candidates overlap or repeat the same idea:

1. Keep the candidate with clearer opening hook.
2. Prefer the candidate with a complete claim and payoff.
3. Prefer lower context risk when scores are similar.
4. Avoid multiple clips with the same title angle unless the user wants many clips from one topic.

## Title and caption rules

Titles should be Chinese, specific, and faithful.

Good titles:

- Emphasize the question, tension, or insight.
- Avoid naming a target unless the transcript clearly supports it.
- Avoid absolute claims if the speaker used caveats.

Captions should:

- Open with the hook or viewer-facing question.
- Summarize the idea without adding unsupported claims.
- Invite discussion when appropriate.
```

- [ ] **Step 4: Write `output-schema.md`**

Write this exact file:

```markdown
# Output Schema

Return a JSON object with `source`, `selection_profile`, and `clips`. Use Chinese for explanatory fields unless the user requests another language.

## Timestamp format

Use `HH:MM:SS.mmm`, for example `00:12:03.000`.

For `.srt` timestamps like `00:12:03,000`, convert the comma to a period.

## Top-level object

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

## Clip object

Every clip must include exactly these fields:

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
  "hook_line": "真正让人停住的是这一句……",
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

## Required field semantics

- `id`: Stable ID in `clip-01` format.
- `rank`: Ranking after scoring and dedupe.
- `score_100`: Integer from 0 to 100.
- `start`: First selected segment start.
- `end`: Last selected segment end.
- `duration_seconds`: Sum of selected segment durations.
- `segments`: One or more selected subtitle ranges with full text.
- `full_text`: Concatenate all segment text in viewing order.
- `hook_line`: The best opening line or title-card hook, faithful to the transcript.
- `core_claim`: One-sentence summary of the clip's main point.
- `why_it_may_perform`: Specific short-video performance rationale.
- `context_integrity_check`: Object explaining whether the clip is fair and complete.
- `risk`: One of `低`, `中`, `高`.
- `risk_reason`: Why that risk label was assigned.
- `suggested_title`: Chinese title, not misleading.
- `suggested_caption`: Chinese publishing caption.

## Multi-segment clips

For multi-segment clips:

- Keep `segments` in playback order.
- Calculate `duration_seconds` from included segment lengths only.
- Explain in `context_integrity_check.reason` why the combination is fair.
- Use `needed_context` to state any extra context that must be kept in editing.

## JSON-only mode

If the user asks for JSON only, return only the JSON object. Do not wrap it in markdown fences.

If the user allows explanation, return the JSON first, then a short Chinese summary with:

- Top 3 recommended clips.
- Any medium/high risk warnings.
- Any note about missing timestamps or uncertain boundaries.
```

- [ ] **Step 5: Verify new files exist**

Run:

```powershell
Test-Path .claude\skills\interview-shorts-selector\SKILL.md
Test-Path .claude\skills\interview-shorts-selector\references\selection-framework.md
Test-Path .claude\skills\interview-shorts-selector\references\output-schema.md
```

Expected output contains three `True` values.

---

### Task 3: Create Examples

**Files:**
- Create: `examples/sample-input.srt`
- Create: `examples/sample-output.json`

- [ ] **Step 1: Create examples directory**

Run:

```powershell
New-Item -ItemType Directory -Force -Path examples | Out-Null
```

Expected: command succeeds with no output.

- [ ] **Step 2: Write `examples/sample-input.srt`**

Write this exact file:

```text
1
00:00:10,000 --> 00:00:18,000
主持人：你觉得年轻人最容易误解职业选择的地方是什么？

2
00:00:18,000 --> 00:00:31,000
嘉宾：很多人以为选择行业是在选择风口，其实是在选择自己愿意长期承受哪一种痛苦。

3
00:00:31,000 --> 00:00:46,000
嘉宾：风口会变，薪资会变，甚至你喜欢的工作内容也会变，但是那种日复一日要面对的问题，才真正决定你能不能留下来。

4
00:00:46,000 --> 00:01:05,000
主持人：所以不是问我喜欢什么，而是问我能忍受什么？

5
00:01:05,000 --> 00:01:22,000
嘉宾：对，而且不是消极地忍受，是你知道这个代价存在，但你仍然觉得它值得。

6
00:02:10,000 --> 00:02:25,000
主持人：你自己有过这种判断失误吗？

7
00:02:25,000 --> 00:02:44,000
嘉宾：有。我第一次创业的时候，最兴奋的是产品发布那一天，但真正让我崩溃的是发布之后每天都要处理用户投诉。

8
00:02:44,000 --> 00:03:03,000
嘉宾：后来我才明白，创业不是喜欢创造就够了，你还要喜欢解决那些没人愿意碰的麻烦。

9
00:03:03,000 --> 00:03:18,000
嘉宾：如果你只喜欢高光，不喜欢高光背后的脏活，那这个选择很快就会反噬你。
```

- [ ] **Step 3: Write `examples/sample-output.json`**

Write this exact valid JSON:

```json
{
  "source": {
    "file": "examples/sample-input.srt",
    "language": "zh",
    "duration_estimate": "00:03:18",
    "input_type": "srt"
  },
  "selection_profile": {
    "primary_mode": "knowledge-opinion",
    "fallback_mode": "personal-story",
    "target_clip_count": 2,
    "duration_range_seconds": [30, 120],
    "multi_segment_allowed": true
  },
  "clips": [
    {
      "id": "clip-01",
      "rank": 1,
      "score_100": 88,
      "start": "00:00:10.000",
      "end": "00:01:22.000",
      "duration_seconds": 72,
      "segments": [
        {
          "start": "00:00:10.000",
          "end": "00:01:22.000",
          "text": "主持人：你觉得年轻人最容易误解职业选择的地方是什么？ 嘉宾：很多人以为选择行业是在选择风口，其实是在选择自己愿意长期承受哪一种痛苦。 嘉宾：风口会变，薪资会变，甚至你喜欢的工作内容也会变，但是那种日复一日要面对的问题，才真正决定你能不能留下来。 主持人：所以不是问我喜欢什么，而是问我能忍受什么？ 嘉宾：对，而且不是消极地忍受，是你知道这个代价存在，但你仍然觉得它值得。"
        }
      ],
      "full_text": "主持人：你觉得年轻人最容易误解职业选择的地方是什么？ 嘉宾：很多人以为选择行业是在选择风口，其实是在选择自己愿意长期承受哪一种痛苦。 嘉宾：风口会变，薪资会变，甚至你喜欢的工作内容也会变，但是那种日复一日要面对的问题，才真正决定你能不能留下来。 主持人：所以不是问我喜欢什么，而是问我能忍受什么？ 嘉宾：对，而且不是消极地忍受，是你知道这个代价存在，但你仍然觉得它值得。",
      "hook_line": "选行业，其实是在选你愿意承受哪种痛苦",
      "core_claim": "职业选择不只是追风口或兴趣，而是判断自己是否愿意长期承担某种代价。",
      "why_it_may_perform": "这段用反常识表达重构了职业选择问题，开头有强观点，中间有解释，结尾有可记忆的判断标准。",
      "context_integrity_check": {
        "verdict": "pass",
        "is_out_of_context": false,
        "reason": "问题、核心判断、解释和限定条件都被保留，没有把消极忍受误读成盲目吃苦。",
        "needed_context": "保留主持人关于“喜欢什么/忍受什么”的追问。",
        "title_risk_note": "标题应避免写成“年轻人别选风口”，因为原意不是否定风口。"
      },
      "risk": "低",
      "risk_reason": "观点是职业建议，不涉及具体个人或敏感指控。",
      "suggested_title": "选行业前，先问自己能承受什么",
      "suggested_caption": "很多人以为职业选择是在追风口，其实更关键的是：你愿不愿意长期承受这份工作的代价？"
    },
    {
      "id": "clip-02",
      "rank": 2,
      "score_100": 84,
      "start": "00:00:18.000",
      "end": "00:03:18.000",
      "duration_seconds": 72,
      "segments": [
        {
          "start": "00:00:18.000",
          "end": "00:00:31.000",
          "text": "嘉宾：很多人以为选择行业是在选择风口，其实是在选择自己愿意长期承受哪一种痛苦。"
        },
        {
          "start": "00:02:25.000",
          "end": "00:03:18.000",
          "text": "嘉宾：有。我第一次创业的时候，最兴奋的是产品发布那一天，但真正让我崩溃的是发布之后每天都要处理用户投诉。 嘉宾：后来我才明白，创业不是喜欢创造就够了，你还要喜欢解决那些没人愿意碰的麻烦。 嘉宾：如果你只喜欢高光，不喜欢高光背后的脏活，那这个选择很快就会反噬你。"
        }
      ],
      "full_text": "嘉宾：很多人以为选择行业是在选择风口，其实是在选择自己愿意长期承受哪一种痛苦。 嘉宾：有。我第一次创业的时候，最兴奋的是产品发布那一天，但真正让我崩溃的是发布之后每天都要处理用户投诉。 嘉宾：后来我才明白，创业不是喜欢创造就够了，你还要喜欢解决那些没人愿意碰的麻烦。 嘉宾：如果你只喜欢高光，不喜欢高光背后的脏活，那这个选择很快就会反噬你。",
      "hook_line": "你喜欢的可能是高光，不是这份工作本身",
      "core_claim": "真正的职业或创业选择，要看自己是否愿意面对高光背后的长期麻烦。",
      "why_it_may_perform": "前段给出强观点，后段用创业投诉的个人经历补足证据和情绪，适合做观点加故事的短视频。",
      "context_integrity_check": {
        "verdict": "pass",
        "is_out_of_context": false,
        "reason": "两个片段属于同一观点链：先提出选择痛苦，再用创业经历解释高光背后的代价。",
        "needed_context": "剪辑时需要用转场或字幕提示“他后来用创业经历解释这个判断”。",
        "title_risk_note": "标题不要暗示创业一定会失败，原意是提醒识别代价。"
      },
      "risk": "低",
      "risk_reason": "多段组合没有改变原意，且不涉及第三方评价。",
      "suggested_title": "别只爱高光，要看见背后的脏活",
      "suggested_caption": "如果你只喜欢一个选择最闪亮的瞬间，却不愿意处理它背后的麻烦，它很快就会反噬你。"
    }
  ]
}
```

- [ ] **Step 4: Validate example JSON**

Run:

```powershell
python -m json.tool examples\sample-output.json > $null
```

Expected: exit code 0 and no output.

---

### Task 4: Rewrite README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README content**

Write this exact file:

```markdown
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
```

- [ ] **Step 2: Confirm README no longer mentions old video pipeline as current scope**

Run:

```powershell
Select-String -Path README.md -Pattern 'download|transcribe|crop|render|MuAPI|ffmpeg|yt-dlp|Whisper'
```

Expected: matches only appear in the "does not do" section, or no matches for old implementation-specific terms such as `MuAPI`, `ffmpeg`, `yt-dlp`, `Whisper`.

---

### Task 5: Remove Old End-to-End Implementation

**Files:**
- Remove: `.claude/skills/youtube-shorts-generator/`
- Remove: `main.py`
- Remove: `requirements.txt`
- Remove: `requirements-local.txt`
- Remove: `.env.example`
- Remove: `shorts_generator/`

- [ ] **Step 1: Remove old files and directories using PowerShell**

Run:

```powershell
$repo = (Get-Location).Path
$targets = @(
  '.claude\skills\youtube-shorts-generator',
  'shorts_generator',
  'main.py',
  'requirements.txt',
  'requirements-local.txt',
  '.env.example'
)
foreach ($target in $targets) {
  $full = Join-Path $repo $target
  $resolved = [System.IO.Path]::GetFullPath($full)
  if (-not $resolved.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove outside repo: $resolved"
  }
  if (Test-Path -LiteralPath $resolved) {
    Remove-Item -LiteralPath $resolved -Recurse -Force
  }
}
```

Expected: command succeeds with no output.

- [ ] **Step 2: Verify old entry points are gone**

Run:

```powershell
Test-Path .claude\skills\youtube-shorts-generator
Test-Path shorts_generator
Test-Path main.py
Test-Path requirements.txt
Test-Path requirements-local.txt
Test-Path .env.example
```

Expected output contains six `False` values.

---

### Task 6: Validate Skill Structure and Content

**Files:**
- Validate: `.claude/skills/interview-shorts-selector/SKILL.md`
- Validate: references and examples

- [ ] **Step 1: Validate skill frontmatter manually**

Run:

```powershell
Get-Content .claude\skills\interview-shorts-selector\SKILL.md -TotalCount 6
```

Expected:

```text
---
name: interview-shorts-selector
description: Select high-potential short-video clips from long interview subtitles or transcripts. Use when the user provides `.srt`, `.ass`, or timestamped `.txt` subtitles and asks to find viral, traffic-worthy, knowledge/opinion, or personal-story clips; output ranked clip recommendations with timecodes, full segment text, hook line, core claim, context-integrity checks, risk label, Chinese title, and publishing caption. This skill does not download, transcribe, cut, crop, render, or edit videos.
---
```

- [ ] **Step 2: Run quick skill validation if available**

Run:

```powershell
$validator = 'C:\Users\14126\.codex\skills\.system\skill-creator\scripts\quick_validate.py'
if (Test-Path $validator) {
  python $validator .claude\skills\interview-shorts-selector
} else {
  Write-Host 'quick_validate.py not found; manual validation already performed'
}
```

Expected: validation passes, or the fallback message appears.

- [ ] **Step 3: Search for stale old-scope wording**

Run:

```powershell
rg -n "MuAPI|yt-dlp|ffmpeg|auto-crop|crop_highlights|generate_shorts|openai-whisper|YouTube URL|download_youtube" . --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**' --glob '!.git/**'
```

Expected: no matches in active skill, README, or examples.

- [ ] **Step 4: Validate JSON again**

Run:

```powershell
python -m json.tool examples\sample-output.json > $null
```

Expected: exit code 0 and no output.

---

### Task 7: Review Diff and Commit

**Files:**
- All changed files

- [ ] **Step 1: Review status**

Run:

```powershell
git status --short
```

Expected: shows new skill, examples, README modification, old files deleted, and the implementation plan.

- [ ] **Step 2: Review diff summary**

Run:

```powershell
git diff --stat
```

Expected: old Python implementation deleted; new skill/reference/example/docs files added.

- [ ] **Step 3: Commit implementation**

Run:

```powershell
git add -A
git commit -m "feat: rebuild as interview shorts selector skill"
```

Expected: commit succeeds.

---

### Task 8: Final Verification

**Files:**
- Repository state

- [ ] **Step 1: Confirm clean working tree**

Run:

```powershell
git status --short
```

Expected: no output.

- [ ] **Step 2: Confirm final structure**

Run:

```powershell
Get-ChildItem -Recurse -File .claude\skills\interview-shorts-selector, examples | Select-Object FullName
```

Expected: lists `SKILL.md`, both reference files, `sample-input.srt`, and `sample-output.json`.

- [ ] **Step 3: Confirm latest commits**

Run:

```powershell
git log --oneline -3
```

Expected: latest commit is `feat: rebuild as interview shorts selector skill`, followed by the design commit.
```
