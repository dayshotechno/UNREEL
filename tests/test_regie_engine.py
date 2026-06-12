"""Offline tests for regie_engine.py – parsing, verification, plan model, providers.

No network: only the JSON parser, verifier, dataclasses and provider availability
logic are exercised. The anthropic/google/openai SDKs are never imported because
their .call() methods are not invoked.
"""
import unittest
import json
import tempfile
from pathlib import Path
from unittest import mock

import regie_engine as re_eng


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
class TestEditClip(unittest.TestCase):
    def test_to_dict_computes_duration_and_rounds(self):
        clip = re_eng.EditClip(
            video="a.mov", start=12.34567, end=18.78912,
            transition="hard_cut_on_beat", reason="drop",
        )
        d = clip.to_dict()
        self.assertEqual(d["start"], 12.346)
        self.assertEqual(d["end"], 18.789)
        self.assertEqual(d["duration"], 6.443)
        self.assertEqual(d["crop"], "9:16")


class TestEditPlan(unittest.TestCase):
    def _plan(self):
        return re_eng.EditPlan(
            clips=[
                re_eng.EditClip("a.mov", 0.0, 4.0, "cut", "r1"),
                re_eng.EditClip("b.mov", 4.0, 9.0, "cut", "r2", slow_mo=True, slow_mo_factor=2.0),
            ],
            narrative="arc",
            total_duration=9.0,
        )

    def test_to_dict_clip_count(self):
        d = self._plan().to_dict()
        self.assertEqual(d["clip_count"], 2)
        self.assertEqual(len(d["clips"]), 2)

    def test_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plan.json"
            self._plan().save(p)
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["clip_count"], 2)

    def test_to_ffmpeg_commands(self):
        cmds = self._plan().to_ffmpeg_commands(output_dir=Path("output"))
        self.assertEqual(len(cmds), 2)
        # 9:16 crop + lut applied
        self.assertIn("crop=ih*9/16:ih,scale=1080:1920", cmds[0])
        self.assertIn("lut3d=luts/underground_dark.cube", cmds[0])
        # slow-mo clip gets setpts prepended
        self.assertIn("setpts=PTS*2.0", cmds[1])


# --------------------------------------------------------------------------- #
# JSON parsing (the core robustness feature)
# --------------------------------------------------------------------------- #
class TestParseEditPlan(unittest.TestCase):
    VALID = {
        "clips": [
            {"video": "a.mov", "start": 1.0, "end": 5.0,
             "transition": "cut", "reason": "intro"},
        ],
        "narrative": "story",
    }

    def test_plain_json(self):
        plan = re_eng._parse_edit_plan(json.dumps(self.VALID), "claude", "m")
        self.assertEqual(len(plan.clips), 1)
        self.assertEqual(plan.clips[0].video, "a.mov")
        self.assertEqual(plan.narrative, "story")
        self.assertEqual(plan.provider_used, "claude")

    def test_markdown_fenced(self):
        raw = "```json\n" + json.dumps(self.VALID) + "\n```"
        plan = re_eng._parse_edit_plan(raw, "gemini", "m")
        self.assertEqual(len(plan.clips), 1)

    def test_text_wrapped_json(self):
        raw = "Here is your plan:\n" + json.dumps(self.VALID) + "\nHope it helps!"
        plan = re_eng._parse_edit_plan(raw, "deepseek", "m")
        self.assertEqual(len(plan.clips), 1)

    def test_defaults_applied(self):
        minimal = {"clips": [{"video": "x.mov", "start": 0, "end": 3}], "narrative": ""}
        plan = re_eng._parse_edit_plan(json.dumps(minimal), "claude", "m")
        c = plan.clips[0]
        self.assertEqual(c.transition, "cut")
        self.assertEqual(c.crop, "9:16")
        self.assertEqual(c.lut, "underground_dark")

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            re_eng._parse_edit_plan("not json at all", "claude", "m")


# --------------------------------------------------------------------------- #
# Verification / self-healing
# --------------------------------------------------------------------------- #
class TestVerifyEditPlan(unittest.TestCase):
    def test_drops_zero_and_negative_duration(self):
        plan = re_eng.EditPlan(
            clips=[
                re_eng.EditClip("a.mov", 5.0, 5.0, "cut", "zero"),
                re_eng.EditClip("b.mov", 5.0, 3.0, "cut", "negative"),
                re_eng.EditClip("c.mov", 0.0, 4.0, "cut", "ok"),
            ],
            narrative="", total_duration=0.0,
        )
        fixed = re_eng.verify_edit_plan(plan, {}, target_duration=4.0)
        self.assertEqual(len(fixed.clips), 1)
        self.assertEqual(fixed.clips[0].video, "c.mov")
        self.assertAlmostEqual(fixed.total_duration, 4.0)

    def test_trims_overlong_clip(self):
        plan = re_eng.EditPlan(
            clips=[re_eng.EditClip("a.mov", 0.0, 30.0, "cut", "too long")],
            narrative="", total_duration=30.0,
        )
        fixed = re_eng.verify_edit_plan(plan, {}, target_duration=15.0)
        self.assertEqual(fixed.clips[0].duration, 15.0)

    def test_empty_plan_is_safe(self):
        plan = re_eng.EditPlan(clips=[], narrative="", total_duration=0.0)
        self.assertEqual(re_eng.verify_edit_plan(plan, {}).clips, [])


# --------------------------------------------------------------------------- #
# Seamless loop helper
# --------------------------------------------------------------------------- #
class TestSeamlessLoop(unittest.TestCase):
    def test_swaps_halves(self):
        plan = re_eng.create_seamless_loop_plan("v.mov", start=10.0, end=20.0)
        self.assertEqual(len(plan.clips), 2)
        # Second half plays first
        self.assertEqual((plan.clips[0].start, plan.clips[0].end), (15.0, 20.0))
        self.assertEqual((plan.clips[1].start, plan.clips[1].end), (10.0, 15.0))
        self.assertEqual(plan.style, "seamless_loop")


# --------------------------------------------------------------------------- #
# Provider resolution (no API keys involved)
# --------------------------------------------------------------------------- #
class TestProviders(unittest.TestCase):
    def test_get_provider_unknown_raises(self):
        with self.assertRaises(ValueError):
            re_eng.get_provider("does_not_exist")

    def test_get_provider_returns_right_class(self):
        self.assertIsInstance(re_eng.get_provider("claude"), re_eng.ClaudeProvider)
        self.assertIsInstance(re_eng.get_provider("gemini"), re_eng.GeminiProvider)
        self.assertIsInstance(re_eng.get_provider("deepseek"), re_eng.DeepSeekProvider)

    def test_availability_requires_key(self):
        self.assertFalse(re_eng.ClaudeProvider(api_key="").is_available())

    def test_availability_requires_sdk(self):
        # Key present but SDK not importable -> not available (graceful degradation).
        with mock.patch.object(re_eng, "_sdk_installed", return_value=False):
            self.assertFalse(re_eng.DeepSeekProvider(api_key="secret").is_available())
        with mock.patch.object(re_eng, "_sdk_installed", return_value=True):
            self.assertTrue(re_eng.DeepSeekProvider(api_key="secret").is_available())

    def test_resolve_named_provider_without_key_raises(self):
        with mock.patch.object(re_eng.ClaudeProvider, "is_available", return_value=False):
            with self.assertRaises(ValueError):
                re_eng.resolve_provider("claude")

    def test_resolve_auto_without_any_key_raises(self):
        with mock.patch.object(re_eng.ClaudeProvider, "is_available", return_value=False), \
             mock.patch.object(re_eng.GeminiProvider, "is_available", return_value=False), \
             mock.patch.object(re_eng.DeepSeekProvider, "is_available", return_value=False):
            with self.assertRaises(ValueError):
                re_eng.resolve_provider("auto")

    def test_list_available_providers_structure(self):
        providers = re_eng.list_available_providers()
        self.assertEqual({p["name"] for p in providers}, {"claude", "gemini", "deepseek", "local"})
        for p in providers:
            self.assertIn("model", p)
            self.assertIn("available", p)


# --------------------------------------------------------------------------- #
# POV story preset + anti-advice hook
# --------------------------------------------------------------------------- #
class TestPovStoryPreset(unittest.TestCase):
    def test_prompt_includes_pov_section_only_for_pov_story(self):
        pov = re_eng._build_system_prompt("pov_story", 45)
        self.assertIn("ANTI-ADVICE HOOK", pov)
        self.assertIn("hook_text", pov)
        for phase in ("before", "during", "after"):
            self.assertIn(phase, pov)
        # other presets must NOT get the POV story block
        hl = re_eng._build_system_prompt("highlight", 60)
        self.assertNotIn("ANTI-ADVICE HOOK", hl)

    def test_pov_story_is_a_valid_cli_preset(self):
        # the preset name appears in the preset definitions of every prompt
        self.assertIn("pov_story", re_eng._build_system_prompt("highlight", 60))

    def test_parse_reads_hook_text_and_phase(self):
        raw = {
            "clips": [
                {"video": "arrive.mov", "start": 0, "end": 4, "phase": "before"},
                {"video": "drop.mov", "start": 10, "end": 14, "phase": "during"},
                {"video": "pack.mov", "start": 20, "end": 24, "phase": "after"},
            ],
            "narrative": "a day in the life",
            "hook_text": "stop practicing your transitions.",
        }
        plan = re_eng._parse_edit_plan(json.dumps(raw), "claude", "m")
        self.assertEqual(plan.hook_text, "stop practicing your transitions.")
        self.assertEqual([c.phase for c in plan.clips], ["before", "during", "after"])
        # hook_text + phase survive serialization
        d = plan.to_dict()
        self.assertEqual(d["hook_text"], "stop practicing your transitions.")
        self.assertEqual(d["clips"][0]["phase"], "before")

    def test_hook_text_defaults_empty_for_non_pov(self):
        minimal = {"clips": [{"video": "x.mov", "start": 0, "end": 3}], "narrative": ""}
        plan = re_eng._parse_edit_plan(json.dumps(minimal), "claude", "m")
        self.assertEqual(plan.hook_text, "")
        self.assertEqual(plan.clips[0].phase, "")


if __name__ == "__main__":
    unittest.main()
