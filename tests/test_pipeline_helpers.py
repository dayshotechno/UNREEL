"""
Tests für die Pipeline-Helfer aus src/main.py und regie_engine.py:
- Twin-Detektor (Vision-Duplikat-Vorfilter)
- Reel-Peak-Berechnung (Musik-Overlay)
- Quelldauer-Clamping im Edit-Plan-Verifier
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import (  # noqa: E402
    _clip_reel_duration,
    _find_visual_twin,
    _reel_peak_time,
)
from regie_engine import EditClip, EditPlan, verify_edit_plan  # noqa: E402


# ---------------------------------------------------------------------------
# Twin-Detektor (_find_visual_twin)
# ---------------------------------------------------------------------------

# Hashes mit definierter Bit-Distanz: BASE hat 12 gesetzte Bits (informativ).
BASE = 0b111111111111
def _flip(h: int, n: int) -> int:
    """Kippt die n höchsten Bits eines 64-bit-Werts (verändert Distanz, nicht popcount-kritisch)."""
    for i in range(n):
        h ^= 1 << (63 - i)
    return h


class TestFindVisualTwin:
    def test_identical_signature_is_twin(self):
        sig = [BASE, BASE, BASE, BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": list(sig)}) == "a.mp4"

    def test_small_distance_is_twin(self):
        # Re-Encodes weichen real um <=7 Bits ab; Threshold ist 10
        sig = [BASE, BASE, BASE, BASE, BASE]
        other = [_flip(BASE, 7), BASE, _flip(BASE, 3), BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": other}) == "a.mp4"

    def test_large_distance_is_no_twin(self):
        # Verschiedene Szenen liegen real bei >=16 Bits
        sig = [BASE] * 5
        other = [_flip(BASE, 16)] * 5
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_one_bad_position_rejects(self):
        # ALLE vergleichbaren Positionen müssen passen (konservativ)
        sig = [BASE] * 5
        other = [BASE, BASE, BASE, BASE, _flip(BASE, 16)]
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_uniform_frames_not_comparable(self):
        # Hash 0 / popcount<4 = schwarzes Bild → zählt nicht; <2 vergleichbar → kein Twin
        sig = [0, 0b1, BASE, 0, 0b11]
        other = [0, 0b1, BASE, 0, 0b11]
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_none_positions_skipped(self):
        sig = [None, BASE, BASE, None, None]
        other = [BASE, BASE, BASE, BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": other}) == "a.mp4"


# ---------------------------------------------------------------------------
# Reel-Peak (_reel_peak_time / _clip_reel_duration)
# ---------------------------------------------------------------------------

class TestReelPeak:
    def test_slow_mo_stretches_reel_duration(self):
        clip = {"start": 0.0, "end": 4.0, "slow_mo": True, "slow_mo_factor": 2.0}
        assert _clip_reel_duration(clip) == 8.0

    def test_peak_at_highest_energy_clip(self):
        clips = [
            {"video": "a.mp4", "start": 0, "end": 5},
            {"video": "b.mp4", "start": 0, "end": 4},
            {"video": "c.mp4", "start": 0, "end": 6},
        ]
        vision = {"b.mp4": {"vision_tags_filtered": [
            {"tag": "CROWD_ENERGY"}, {"tag": "LIGHT_SHOW"}]}}
        peak, total = _reel_peak_time(clips, vision)
        assert total == 15.0
        assert peak == 7.0  # Mitte von b: 5 + 4/2

    def test_fallback_to_drop_reason(self):
        clips = [
            {"video": "a.mp4", "start": 0, "end": 5},
            {"video": "b.mp4", "start": 0, "end": 5, "reason": "the DROP hits"},
        ]
        peak, _ = _reel_peak_time(clips, None)
        assert peak == 7.5  # Mitte von b

    def test_fallback_to_62_percent(self):
        clips = [{"video": "a.mp4", "start": 0, "end": 10}]
        peak, total = _reel_peak_time(clips, None)
        assert total == 10.0
        assert peak == pytest.approx(6.2)

    def test_empty_plan(self):
        assert _reel_peak_time([], None) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Quelldauer-Clamping (verify_edit_plan)
# ---------------------------------------------------------------------------

def _plan(clips: list[EditClip]) -> EditPlan:
    return EditPlan(
        clips=clips,
        narrative="test",
        total_duration=sum(c.duration for c in clips),
        provider_used="test",
        model_used="test",
    )


class TestVerifyEditPlanClamping:
    def test_end_clamped_to_source_duration(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 4.6)
        plan = _plan([EditClip("a.mov", 0.0, 5.0, "hard_cut", "x")])
        out = verify_edit_plan(plan, {}, target_duration=4.6)
        assert out.clips[0].end == 4.6

    def test_clip_starting_past_source_is_dropped(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 3.0)
        plan = _plan([
            EditClip("a.mov", 5.0, 8.0, "hard_cut", "x"),   # start hinter Quellende
            EditClip("a.mov", 0.0, 2.0, "hard_cut", "x"),
        ])
        out = verify_edit_plan(plan, {}, target_duration=2.0)
        assert len(out.clips) == 1
        assert out.clips[0].start == 0.0

    def test_shortfall_recovered_from_headroom(self, monkeypatch):
        import regie_engine
        # Quelle ist 20s lang – Clip endet bei 5s, hat also Headroom
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 20.0)
        plan = _plan([
            EditClip("a.mov", 0.0, 5.0, "hard_cut", "x"),
            EditClip("b.mov", 0.0, 5.0, "hard_cut", "x"),
        ])
        out = verify_edit_plan(plan, {}, target_duration=13.0)
        # +2s max pro Clip → 10 + 2 + 1 = 13 erreichbar
        assert out.total_duration == pytest.approx(13.0, abs=0.1)
        # Startzeiten (beat-aligned) bleiben unangetastet
        assert all(c.start == 0.0 for c in out.clips)

    def test_unknown_duration_skips_clamping(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 0.0)
        plan = _plan([EditClip("a.mov", 0.0, 5.0, "hard_cut", "x")])
        out = verify_edit_plan(plan, {}, target_duration=5.0)
        assert out.clips[0].end == 5.0
