"""Offline tests for config.py – paths and constants (no secrets required)."""
import unittest
from pathlib import Path

import config


class TestConfigPaths(unittest.TestCase):
    def test_base_dir_is_repo_root(self):
        # config.py lives at the repo root, so BASE_DIR must be that root.
        self.assertEqual(config.BASE_DIR, Path(config.__file__).resolve().parent)

    def test_derived_dirs_under_base(self):
        for d in (config.INPUT_DIR, config.OUTPUT_DIR, config.LUT_DIR):
            self.assertEqual(d.parent, config.BASE_DIR)

    def test_lut_dir_created(self):
        # config.py mkdir's the LUT dir on import.
        self.assertTrue(config.LUT_DIR.exists())


class TestConfigConstants(unittest.TestCase):
    def test_available_luts(self):
        self.assertEqual(
            set(config.AVAILABLE_LUTS),
            {"underground_dark", "vhs_analog", "neon_nights"},
        )

    def test_tag_bonus_scores(self):
        self.assertAlmostEqual(config.TAG_BONUS_SCORES["CROWD_ENERGY"], 0.8)
        self.assertAlmostEqual(config.TAG_BONUS_SCORES["UNUSABLE"], -1.0)

    def test_fallback_order(self):
        # DeepSeek is the primary provider in the auto-hierarchy.
        self.assertEqual(
            config.REGIE_PROVIDER_FALLBACK_ORDER,
            ["deepseek", "claude", "gemini"],
        )

    def test_reel_dimensions_are_vertical(self):
        self.assertEqual((config.REEL_WIDTH, config.REEL_HEIGHT), (1080, 1920))


if __name__ == "__main__":
    unittest.main()
