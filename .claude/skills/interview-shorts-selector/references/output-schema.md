# Output Schema

Create a JSON object with `source`, `selection_profile`, and `clips`, then save it to disk. Use Chinese for explanatory fields unless the user requests another language.

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

## File output mode

Default behavior: save the complete JSON object to a `.json` file and do not paste the full object into chat.

Output path rules:

- If the user provides an output path, use it.
- Otherwise save next to the source subtitle as `<subtitle_stem>_shorts_selection.json`.
- If the source directory is not writable, save in the current working directory.
- Use UTF-8 encoding and preserve Chinese text.
- Before replying, verify the file exists and the JSON parses successfully.

Chat response after saving:

- Provide the saved file path.
- Report clip count.
- Give a short Chinese summary: top 3 recommended clips, medium/high risk warnings, and uncertain-boundary notes.

## JSON-only / chat output exceptions

If the user explicitly asks for JSON only, save the JSON file first, then print only the JSON object in chat. Do not wrap it in markdown fences.

If the user explicitly asks for chat-only output, print the JSON in chat and state that no file was written.


## Draft rendering compatibility

The optional draft renderer reads `clips[].segments[].start` and `clips[].segments[].end` as the source-video cut boundaries. For multi-segment clips, the renderer cuts each segment, concatenates them in order, and rebases subtitles to the new draft timeline.

`hook_line`, `suggested_title`, and `suggested_caption` are copied into per-clip metadata for future hook-card/title-card workflows.

Burned subtitles currently require a source `.srt`; timestamped `.txt` can be selected but cannot be burned by the renderer without conversion. `.ass` inputs should be converted to SRT before using the bundled draft renderer.
