import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "interview-shorts-selector" / "scripts" / "render_draft_clips.py"
spec = importlib.util.spec_from_file_location("render_draft_clips", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = renderer
spec.loader.exec_module(renderer)


class RenderDraftClipsTests(unittest.TestCase):
    def test_parse_timecode_accepts_dot_and_comma_milliseconds(self):
        self.assertEqual(renderer.parse_timecode("00:01:02.345"), 62.345)
        self.assertEqual(renderer.parse_timecode("00:01:02,345"), 62.345)

    def test_format_srt_time_rounds_to_milliseconds(self):
        self.assertEqual(renderer.format_srt_time(62.3454), "00:01:02,345")
        self.assertEqual(renderer.format_srt_time(62.3456), "00:01:02,346")

    def test_parse_srt_reads_cues_with_multiline_text(self):
        cues = renderer.parse_srt("""1
00:00:10,000 --> 00:00:12,500
Line one
Line two

2
00:00:15.000 --> 00:00:16.000
Next line
""")

        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start, 10.0)
        self.assertEqual(cues[0].end, 12.5)
        self.assertEqual(cues[0].text, "Line one\nLine two")
        self.assertEqual(cues[1].start, 15.0)

    def test_build_local_srt_rebases_multiple_segments(self):
        cues = renderer.parse_srt("""1
00:00:10,000 --> 00:00:12,000
A

2
00:00:20,000 --> 00:00:22,000
B
""")
        segments = [renderer.Segment(10.0, 12.0, ""), renderer.Segment(20.0, 22.0, "")]

        local_srt = renderer.build_local_srt(cues, segments)

        self.assertIn("00:00:00,000 --> 00:00:02,000\nA", local_srt)
        self.assertIn("00:00:02,000 --> 00:00:04,000\nB", local_srt)


    def test_load_selection_clips_validates_segments(self):
        with self.subTest("valid selection"):
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                selection = Path(tmp) / "selection.json"
                selection.write_text('{"clips":[{"id":"clip-01","segments":[{"start":"00:00:01.000","end":"00:00:03.000","text":"hello"}],"hook_line":"hook","suggested_title":"title"}]}', encoding="utf-8")

                clips = renderer.load_selection_clips(selection)

                self.assertEqual(clips[0].clip_id, "clip-01")
                self.assertEqual(clips[0].segments, [renderer.Segment(1.0, 3.0, "hello")])
                self.assertEqual(clips[0].hook_line, "hook")
                self.assertEqual(clips[0].suggested_title, "title")

    def test_load_selection_clips_rejects_empty_segments(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            selection = Path(tmp) / "selection.json"
            selection.write_text('{"clips":[{"id":"clip-01","segments":[]}]}', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "clip-01.*segments"):
                renderer.load_selection_clips(selection)


if __name__ == "__main__":
    unittest.main()
