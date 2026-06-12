"""Offline tests for vision_engine.py – taxonomy, scoring, graceful degradation.

No Ollama and no real video decoding: the model call is faked by injecting a
stub `ollama` module, and availability is monkeypatched.
"""
import sys
import json
import unittest
from unittest import mock

import analyzer.vision_engine as ve


class TestTaxonomy(unittest.TestCase):
    def test_new_story_tags_present(self):
        self.assertIn("ARRIVAL", ve.VALID_TAGS)
        self.assertIn("PACKDOWN", ve.VALID_TAGS)

    def test_every_valid_tag_has_a_score(self):
        for tag in ve.VALID_TAGS:
            self.assertIn(tag, ve.TAG_BONUS_SCORES, f"missing score for {tag}")

    def test_story_tags_have_zero_bonus(self):
        self.assertEqual(ve.TAG_BONUS_SCORES["ARRIVAL"], 0.0)
        self.assertEqual(ve.TAG_BONUS_SCORES["PACKDOWN"], 0.0)

    def test_system_prompt_documents_new_tags(self):
        self.assertIn("ARRIVAL", ve.SYSTEM_PROMPT)
        self.assertIn("PACKDOWN", ve.SYSTEM_PROMPT)


class TestFilteringAndScoring(unittest.TestCase):
    def _tags(self):
        return [
            ve.FrameTag(0.0, "ARRIVAL", 0.9, "load-in"),
            ve.FrameTag(5.0, "CROWD_ENERGY", 0.8, "drop"),
            ve.FrameTag(9.0, "PACKDOWN", 0.7, "empty floor"),
            ve.FrameTag(12.0, "UNUSABLE", 0.9, "blurry"),
            ve.FrameTag(15.0, "DJ_SETUP", 0.1, "low conf"),
        ]

    def test_filter_keeps_story_tags_drops_unusable_and_lowconf(self):
        kept = {t.tag for t in ve.filter_unusable(self._tags(), min_confidence=0.3)}
        self.assertEqual(kept, {"ARRIVAL", "CROWD_ENERGY", "PACKDOWN"})

    def test_get_tag_scores(self):
        scores = ve.get_tag_scores(self._tags())
        # story tags contribute nothing; crowd energy contributes 0.8 * 0.8
        self.assertAlmostEqual(scores["0.0"], 0.0)
        self.assertAlmostEqual(scores["9.0"], 0.0)
        self.assertAlmostEqual(scores["5.0"], 0.64)


class TestGracefulDegradation(unittest.TestCase):
    def test_returns_empty_when_backend_down(self):
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.is_available.return_value = False
            self.assertEqual(ve.tag_video_frames("whatever.mov"), [])


class TestBatchTagValidation(unittest.TestCase):
    def test_new_tag_kept_unknown_coerced(self):
        response = [
            {"time": 0.0, "tag": "ARRIVAL", "confidence": 0.9, "description": "load-in"},
            {"time": 5.0, "tag": "ROBOT_DANCE", "confidence": 0.9, "description": "bogus tag"},
        ]
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.describe_frames.return_value = json.dumps(response)
            tags = ve._analyze_frames_batch([(0.0, b"x"), (5.0, b"y")])

        self.assertEqual(tags[0].tag, "ARRIVAL")        # new valid tag preserved
        self.assertEqual(tags[1].tag, "UNUSABLE")        # unknown tag coerced

    def test_concatenated_arrays_are_merged(self):
        # gemma4:e2b often returns one JSON array per image, concatenated.
        raw = (
            '[{"time": 0.0, "tag": "DJ_SETUP", "confidence": 0.95, "description": "a"}]\n'
            '[{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "b"}]'
        )
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.describe_frames.return_value = raw
            tags = ve._analyze_frames_batch([(0.0, b"x"), (5.0, b"y")])
        self.assertEqual([t.tag for t in tags], ["DJ_SETUP", "CROWD_ENERGY"])
        self.assertEqual([t.time for t in tags], [0.0, 5.0])


if __name__ == "__main__":
    unittest.main()
