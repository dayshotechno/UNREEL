"""Offline tests for kick_snare_detector.py – dataclasses and beat grid logic."""
import unittest
import json
import tempfile
from pathlib import Path

import kick_snare_detector as ksd


class TestDataclasses(unittest.TestCase):
    def test_hit_to_dict_rounds(self):
        hit = ksd.PercussiveHit(time=1.23456, intensity=0.987654)
        self.assertEqual(hit.to_dict(), {"time": 1.235, "intensity": 0.988})

    def test_map_to_dict_counts(self):
        pm = ksd.PercussionMap(
            kicks=[ksd.PercussiveHit(0.5, 0.9), ksd.PercussiveHit(1.0, 0.8)],
            snares=[ksd.PercussiveHit(0.75, 0.7)],
            bpm=140.04,
            duration=12.345,
        )
        d = pm.to_dict()
        self.assertEqual(d["kick_count"], 2)
        self.assertEqual(d["snare_count"], 1)
        self.assertEqual(d["bpm"], 140.0)
        self.assertEqual(d["duration"], 12.35)

    def test_map_save_roundtrip(self):
        pm = ksd.PercussionMap(kicks=[ksd.PercussiveHit(0.5, 0.9)], snares=[], bpm=128.0, duration=4.0)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "perc.json"
            pm.save(p)
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["kick_count"], 1)


class TestBeatGrid(unittest.TestCase):
    def test_merges_and_sorts(self):
        pm = ksd.PercussionMap(
            kicks=[ksd.PercussiveHit(2.0, 0.9), ksd.PercussiveHit(0.0, 0.8)],
            snares=[ksd.PercussiveHit(1.0, 0.7)],
            bpm=140.0,
            duration=3.0,
        )
        grid = ksd.get_beat_grid(pm)
        times = [b["time"] for b in grid]
        self.assertEqual(times, [0.0, 1.0, 2.0])
        types = [b["type"] for b in grid]
        self.assertEqual(types, ["kick", "snare", "kick"])

    def test_empty_grid(self):
        pm = ksd.PercussionMap(kicks=[], snares=[], bpm=0.0, duration=0.0)
        self.assertEqual(ksd.get_beat_grid(pm), [])


if __name__ == "__main__":
    unittest.main()
