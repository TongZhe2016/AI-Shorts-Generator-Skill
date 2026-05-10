# Draft Video Rendering Design for Interview Shorts Selector

Date: 2026-05-10
Repository: `AI-Shorts-Generator-Skill`
Target skill name: `interview-shorts-selector`

## 1. Background

The current `interview-shorts-selector` skill selects high-potential clips from timestamped interview subtitles and writes a structured JSON file. It deliberately does not download, transcribe, cut, crop, or render video.

The new requirement is to keep subtitle-first selection as the core workflow while adding an optional draft-video export step. When the user has the original video and subtitle file, the skill should be able to produce reviewable draft clips for the selected JSON candidates. The first implementation should support video cutting plus burning the original subtitles. It should not attempt translation, vertical reframing, thumbnail design, or polished social-platform packaging.

The user also described a future short-video structure with a first 2-3 second hook/title moment followed by one or more body segments. This design reserves room for that hook-card workflow, but the first implementation does not need to generate a separate title-card sequence by default.

## 2. Goals

1. Add optional draft-video rendering to the existing subtitle-selection skill.
2. Read the existing selection JSON produced by the skill.
3. Accept a local source video path and a local source subtitle path.
4. Export one reviewable draft video per selected clip.
5. Support continuous clips and multi-segment clips.
6. Burn original SRT subtitles into each draft video.
7. Rebase subtitle timestamps so multi-segment drafts have correct local timing.
8. Preserve hook/title metadata for future hook-card rendering.
9. Provide deterministic helper scripts so agents do not need to hand-write fragile FFmpeg commands.
10. Keep the workflow local: no video download, no transcription, no translation, no external APIs.

## 3. Non-goals

This change will not:

- Download source videos.
- Transcribe audio.
- Translate subtitles.
- Automatically crop or reframe to 9:16 vertical video.
- Create polished motion graphics, thumbnails, music, or platform-specific exports.
- Guarantee frame-perfect professional edits.
- Burn subtitles for timestamped `.txt` transcripts.
- Make `.ass` subtitle windowing a required first-pass feature.

## 4. Chosen Approach

Use a single primary rendering script with small internal helpers:

```text
.claude/skills/interview-shorts-selector/
  scripts/
    render_draft_clips.py
```

The script will read the selected clips JSON and handle the complete draft export pipeline:

1. Parse clip timecodes from JSON.
2. Parse source SRT cues.
3. Cut each selected segment from the source video.
4. Concatenate multiple segments when needed.
5. Build a local SRT file whose timestamps match the final draft clip timeline.
6. Burn the local SRT into the draft video.
7. Write per-clip metadata.

Rationale: a single user-facing command is easier and safer than asking the agent to manually orchestrate several FFmpeg commands, especially on Windows paths with spaces or Chinese characters.

## 5. User-Facing Workflow

After the skill creates a selection file such as:

```text
interview_shorts_selection.json
```

The user can ask for draft videos. The agent runs:

```powershell
python .claude/skills/interview-shorts-selector/scripts/render_draft_clips.py `
  --video path/to/source.mp4 `
  --subtitles path/to/source.srt `
  --selection path/to/interview_shorts_selection.json `
  --output-dir path/to/drafts
```

Expected output:

```text
drafts/
  clip-01/
    clip-01.draft.mp4
    clip-01.local.srt
    clip-01.metadata.json
  clip-02/
    clip-02.draft.mp4
    clip-02.local.srt
    clip-02.metadata.json
```

The chat response should report the output directory, exported clip count, any skipped clips, and concrete blockers if rendering failed.

## 6. JSON Input Contract

The renderer consumes the current output schema:

```json
{
  "clips": [
    {
      "id": "clip-01",
      "segments": [
        {"start": "00:00:10.000", "end": "00:01:22.000", "text": "..."}
      ],
      "hook_line": "...",
      "suggested_title": "..."
    }
  ]
}
```

For rendering, each clip must have at least one segment with `start` and `end`. Segment text is useful for metadata but not required for video cutting if timestamps are valid.

## 7. Video Rendering Rules

### Continuous clip

If a clip has one segment, cut from `start` to `end`, create a local subtitle window from the source SRT, and burn that local subtitle file into the output draft.

### Multi-segment clip

If a clip has multiple segments:

1. Cut each segment independently.
2. Concatenate the segment files in listed order.
3. Build one local SRT where each source cue is shifted onto the new concatenated timeline.
4. Burn the local SRT into the concatenated video.

For example, if segment A is 12 seconds and segment B starts later in the source video, B's subtitle cues start at 12 seconds in the local SRT, not at their original source timestamp.

### Duration calculation

The rendered duration is the sum of segment durations. This matches the existing schema rule for multi-segment clips.

## 8. Subtitle Handling

First-pass subtitle support is SRT.

The script should:

- Parse `HH:MM:SS,mmm` and `HH:MM:SS.mmm` forms.
- Select cues overlapping each segment.
- Clip cue boundaries to segment boundaries.
- Shift cue timestamps to the draft video's local timeline.
- Write `clip-id.local.srt` in UTF-8.
- Burn that local SRT into the draft video with FFmpeg's `subtitles` filter.

For `.ass`, the skill may explain that draft rendering currently expects SRT and recommend converting to SRT first. For timestamped `.txt`, the skill may still select clips but should not promise burned subtitles.

## 9. FFmpeg Strategy

The script should find FFmpeg in this order:

1. System `ffmpeg` on `PATH`.
2. `imageio-ffmpeg` Python package fallback.
3. If neither exists, fail with a clear installation message.

Encoding defaults:

- Video codec: `libx264`.
- Audio codec: `aac`.
- Preset: `medium` or `veryfast` for drafts.
- CRF: around `18` to `23`; draft default can prioritize speed.
- Add `-movflags +faststart`.

Path handling must be robust on Windows, including spaces and Chinese characters.

## 10. Hook Card Extension Point

The renderer should preserve hook metadata in `clip-id.metadata.json`:

- `hook_line`
- `suggested_title`
- `suggested_caption`
- original segment list
- rendered output paths

The CLI can reserve an optional flag name such as `--hook-title-mode`, but the default first implementation should not generate title-card video. Future work can add:

- a 2-3 second first-frame title overlay,
- a generated solid-color title card,
- a drawtext overlay on the first seconds of the first segment,
- or separate hook/body rendering modes.

## 11. Skill Documentation Changes

Update `SKILL.md` so its scope becomes:

- Select clips from subtitles.
- Optionally render draft clips when the user provides source video and source SRT.
- Clearly distinguish draft rendering from polished editing.

Update the old prohibition from "does not cut or render video" to "does not download/transcribe/polish video; draft rendering is available only when local source video and supported subtitles are provided."

Update `README.md` with:

- Basic selection-only usage.
- Draft-video usage.
- Required local prerequisites.
- Output folder shape.
- Limitations.

Update `references/output-schema.md` only if needed to mention that `segments[].start/end` drive draft rendering and `hook_line`/`suggested_title` are reused as metadata.

## 12. Validation Plan

1. Confirm `ffmpeg` is available or `imageio-ffmpeg` can provide it.
2. Generate a short dummy test video from FFmpeg test sources.
3. Use `examples/sample-input.srt` and `examples/sample-output.json` or a purpose-built fixture.
4. Render at least one continuous clip.
5. Render at least one multi-segment clip.
6. Verify expected files exist:
   - `clip-id.draft.mp4`
   - `clip-id.local.srt`
   - `clip-id.metadata.json`
7. Verify the local SRT starts near `00:00:00,000` and multi-segment timing is rebased.
8. Run Python syntax checks for scripts.
9. Confirm JSON examples still parse.
10. Review git diff to avoid committing generated videos, temporary files, or `desktop.ini` noise.

## 13. Risks and Mitigations

- **Windows/Chinese paths break FFmpeg filters.** Mitigate by passing normal file arguments as subprocess list entries and carefully escaping only filter paths.
- **Subtitle burn-in fails due missing libass support.** Report the exact FFmpeg error and keep the non-subtitled intermediate if useful.
- **Multi-segment edits feel abrupt.** This is acceptable for draft review; future polishing can add transitions.
- **`.ass` and `.txt` expectations become unclear.** Document that first-pass burned subtitles require SRT.
- **Generated files bloat the repository.** Add or maintain gitignore rules for draft output folders and media artifacts if needed.

## 14. Acceptance Criteria

The change is complete when:

1. The skill can still perform selection-only output.
2. A new renderer script can export draft videos from a local video, SRT, and selection JSON.
3. Continuous and multi-segment clips both work in a local validation run.
4. Burned subtitle timing matches the rendered draft timeline.
5. Documentation explains prerequisites, command usage, output files, and limitations.
6. The repository commit contains source/docs changes only, not generated draft media.
