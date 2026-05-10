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


if __name__ == "__main__":
    unittest.main()
