"""Literal ASR corrections must work with and without word timestamps.

Run without third-party dependencies:
    python -B -m tests.tools.test_subtitle_corrections -v
Only the in-memory correction helper is exercised; no execute(), media,
provider, event writer, or subprocess is invoked.
"""

import copy
import unittest
from unittest.mock import patch

from tools.subtitle.subtitle_gen import SubtitleGen


class SubtitleCorrectionsTest(unittest.TestCase):
    def test_segment_replacements_are_literal(self):
        for replacement in (r"C:\Audio", r"\1", r"\g<name>", "line\\ntext"):
            with self.subTest(replacement=replacement):
                segments = [{"text": "Cloud, cloud! cloudless", "start": 0, "end": 2}]
                original = copy.deepcopy(segments)
                result = SubtitleGen._apply_corrections(segments, {"CLOUD": replacement})
                self.assertEqual(result[0]["text"], f"{replacement}, {replacement}! cloudless")
                self.assertEqual(segments, original)
                self.assertEqual((result[0]["start"], result[0]["end"]), (0, 2))

    def test_word_and_segment_replacements_agree(self):
        replacement = r"C:\Audio\1"
        segments = [
            {"text": "Cloud!", "start": 0, "end": 1},
            {"text": "Cloud!", "start": 1, "end": 2,
             "words": [{"word": "Cloud!", "start": 1, "end": 2}]},
        ]
        original = copy.deepcopy(segments)
        result = SubtitleGen._apply_corrections(segments, {"cloud": replacement})
        self.assertEqual(result[0]["text"], replacement + "!")
        self.assertEqual(result[1]["text"], result[0]["text"])
        self.assertEqual(result[1]["words"][0]["word"], replacement + "!")
        self.assertEqual(segments, original)

    def test_plain_corrections_preserve_case_insensitive_whole_word_matching(self):
        result = SubtitleGen._apply_corrections(
            [{"text": "Cloud cloudless CLOUD.", "words": []}], {"cloud": "Claude"}
        )
        self.assertEqual(result[0]["text"], "Claude cloudless Claude.")


if __name__ == "__main__":
    # Block all sockets (including loopback) and child processes during this
    # standalone run, in addition to never invoking the production entry point.
    with patch("socket.socket.connect", side_effect=AssertionError("network forbidden")), \
         patch("socket.socket.connect_ex", side_effect=AssertionError("network forbidden")), \
         patch("socket.create_connection", side_effect=AssertionError("network forbidden")), \
         patch("subprocess.Popen", side_effect=AssertionError("subprocess forbidden")):
        unittest.main()
