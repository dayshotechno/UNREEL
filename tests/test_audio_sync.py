"""Offline tests for audio_sync.py – cross-correlation on synthetic signals."""
import unittest
import json
import tempfile
from pathlib import Path

import numpy as np

import audio_sync as asy


class TestRms(unittest.TestCase):
    def test_rms_of_constant(self):
        y = np.full(1000, 0.5, dtype=np.float32)
        self.assertAlmostEqual(asy._compute_rms(y), 0.5, places=5)

    def test_rms_of_silence(self):
        self.assertAlmostEqual(asy._compute_rms(np.zeros(1000)), 0.0, places=6)


class TestComputeOffset(unittest.TestCase):
    def test_detects_known_shift(self):
        sr = 8000
        rng = np.random.default_rng(42)
        base = rng.standard_normal(sr * 2).astype(np.float32)  # 2 seconds of noise

        shift = 400  # samples = 0.05 s
        ref = base
        # target is the reference delayed by `shift` samples (starts later)
        target = np.concatenate([np.zeros(shift, dtype=np.float32), base])[: len(base)]

        offset = asy.compute_offset(ref, target, sr=sr)
        # Magnitude of the detected lag must match the injected shift.
        self.assertAlmostEqual(abs(offset), shift / sr, places=2)

    def test_zero_offset_for_identical(self):
        sr = 8000
        rng = np.random.default_rng(7)
        y = rng.standard_normal(sr).astype(np.float32)
        self.assertAlmostEqual(asy.compute_offset(y, y, sr=sr), 0.0, places=3)


class TestSyncResult(unittest.TestCase):
    def test_to_dict_and_save_roundtrip(self):
        res = asy.SyncResult(
            reference_clip="a.mov",
            offsets={"a.mov": 0.0, "b.mov": 1.234},
            rms_values={"a.mov": 0.1234567, "b.mov": 0.05},
            sample_rate=44100,
        )
        d = res.to_dict()
        self.assertEqual(d["reference_clip"], "a.mov")
        self.assertEqual(d["offsets"]["b.mov"], 1.234)
        # rms values are rounded to 6 places in to_dict
        self.assertEqual(d["rms_values"]["a.mov"], 0.123457)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sub" / "sync.json"
            res.save(p)
            self.assertTrue(p.exists())
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["reference_clip"], "a.mov")


class TestSyncGuards(unittest.TestCase):
    def test_sync_all_clips_requires_two(self):
        with self.assertRaises(ValueError):
            asy.sync_all_clips(["only_one.mov"])


if __name__ == "__main__":
    unittest.main()
