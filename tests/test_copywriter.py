"""Offline tests for copywriter.py – sanitizing + graceful degradation (Ollama mocked)."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest import mock

import analyzer.copywriter as cw


class TestCleanFilename(unittest.TestCase):
    def test_spaces_and_case(self):
        self.assertEqual(cw._clean_filename("Dark Bassline Crowd"), "dark_bassline_crowd")

    def test_strips_special_chars(self):
        self.assertEqual(cw._clean_filename('"Dark!! Drop@2am"'), "dark_drop2am")

    def test_truncates_to_40(self):
        out = cw._clean_filename("a" * 80)
        self.assertLessEqual(len(out), 40)

    def test_empty_falls_back(self):
        self.assertEqual(cw._clean_filename("!!!"), "unnamed_clip")

    def test_strips_trailing_underscores(self):
        self.assertEqual(cw._clean_filename("__hello__"), "hello")


class TestGenerateFilename(unittest.TestCase):
    def test_uses_model_output(self):
        with mock.patch.object(cw, "_query_llm", return_value="Dark Bassline Crowd"):
            self.assertEqual(cw.generate_filename({"bpm": 140, "tags": ["techno"]}),
                             "dark_bassline_crowd")

    def test_fallback_when_offline(self):
        # Ollama unavailable -> empty response -> metadata-based fallback.
        with mock.patch.object(cw, "_query_llm", return_value=""):
            name = cw.generate_filename({"bpm": 145, "tags": ["CROWD_ENERGY"]})
            self.assertEqual(name, "techno_crowd_energy_145bpm")


class TestGenerateCaption(unittest.TestCase):
    def test_uses_model_output(self):
        with mock.patch.object(cw, "_query_llm", return_value="raw techno energy #techno"):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertEqual(cap, "raw techno energy #techno")

    def test_fallback_when_offline(self):
        with mock.patch.object(cw, "_query_llm", return_value=""):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertIn("#techno", cap)

    def test_truncates_overlong(self):
        long = "x" * 3000
        with mock.patch.object(cw, "_query_llm", return_value=long):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertLessEqual(len(cap), 2200)


class TestBatchAndSave(unittest.TestCase):
    def test_batch_and_save(self):
        clips = [{"bpm": 140, "tags": ["techno"]}, {"bpm": 150, "tags": ["house"]}]
        with mock.patch.object(cw, "_query_llm", return_value=""):
            results = cw.batch_process(clips)
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], cw.CopyResult)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "caps.json"
            cw.save_captions(results, p)
            loaded = json.loads(p.read_text())
            self.assertEqual(len(loaded), 2)
            self.assertIn("filename", loaded[0])
            self.assertIn("caption", loaded[0])


if __name__ == "__main__":
    unittest.main()
