"""
UNREEL V3 – Kick/Snare Detection Module
Extends the existing librosa-based audio analysis with percussive element detection.
Identifies kicks (bass < 200Hz) and snares (mid/high 2kHz-8kHz) for precise beat-cutting.

Usage:
    from analyzer.kick_snare_detector import detect_kicks_snares
    result = detect_kicks_snares("input/clip.mov")
    # → {"kicks": [{"time": 1.23, "intensity": 0.85}], "snares": [...]}
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import librosa

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PercussiveHit:
    time: float        # Time in seconds
    intensity: float   # 0.0 to 1.0

    def to_dict(self) -> dict:
        return {"time": round(self.time, 3), "intensity": round(self.intensity, 3)}


@dataclass
class PercussionMap:
    kicks: list[PercussiveHit]
    snares: list[PercussiveHit]
    bpm: float = 0.0
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "kicks": [k.to_dict() for k in self.kicks],
            "snares": [s.to_dict() for s in self.snares],
            "kick_count": len(self.kicks),
            "snare_count": len(self.snares),
            "bpm": round(self.bpm, 1),
            "duration": round(self.duration, 2),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Percussion map saved to {path}")


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def _detect_kicks(y: np.ndarray, sr: int = 44100) -> list[PercussiveHit]:
    """
    Detect kick drums by analyzing the bass frequency band (< 200 Hz).
    Uses onset detection on the low-frequency Mel-spectrogram.
    """
    # Isolate bass frequencies
    S_bass = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=64, fmin=20, fmax=200,
        hop_length=512,
    )
    S_bass_db = librosa.power_to_db(S_bass, ref=np.max)

    # Onset detection on bass
    onset_env = librosa.onset.onset_strength(
        S=S_bass_db, sr=sr, hop_length=512,
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr,
        hop_length=512, backtrack=True,
    )

    # Convert frames to times and compute intensities
    times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)

    kicks = []
    for i, frame in enumerate(onset_frames):
        # Intensity from the onset envelope
        intensity = float(np.clip(onset_env[frame] / (np.max(onset_env) + 1e-10), 0, 1))
        if intensity > 0.15:  # Filter weak detections
            kicks.append(PercussiveHit(time=float(times[i]), intensity=intensity))

    logger.info(f"  Detected {len(kicks)} kicks")
    return kicks


def _detect_snares(y: np.ndarray, sr: int = 44100) -> list[PercussiveHit]:
    """
    Detect snares/claps by analyzing the mid/high frequency band (2kHz - 8kHz).
    Uses onset detection on the high-frequency Mel-spectrogram.
    """
    # Isolate mid/high frequencies
    S_high = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=64, fmin=2000, fmax=8000,
        hop_length=512,
    )
    S_high_db = librosa.power_to_db(S_high, ref=np.max)

    # Onset detection on highs
    onset_env = librosa.onset.onset_strength(
        S=S_high_db, sr=sr, hop_length=512,
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr,
        hop_length=512, backtrack=True,
    )

    times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)

    snares = []
    for i, frame in enumerate(onset_frames):
        intensity = float(np.clip(onset_env[frame] / (np.max(onset_env) + 1e-10), 0, 1))
        if intensity > 0.2:  # Slightly higher threshold for snares
            snares.append(PercussiveHit(time=float(times[i]), intensity=intensity))

    logger.info(f"  Detected {len(snares)} snares")
    return snares


def _get_bpm(y: np.ndarray, sr: int = 44100) -> float:
    """Get BPM from audio using librosa's beat tracker."""
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    return float(tempo)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_kicks_snares(
    video_or_audio_path: str | Path,
    sr: int = 44100,
) -> PercussionMap:
    """
    Detect kicks and snares in an audio file or video file.
    
    Args:
        video_or_audio_path: Path to video or audio file
        sr: Sample rate
    
    Returns:
        PercussionMap with kick and snare timestamps + intensities
    """
    path = str(video_or_audio_path)
    logger.info(f"Detecting percussion in {Path(path).name}...")

    # Load audio (librosa handles video containers too)
    y, _ = librosa.load(path, sr=sr, mono=True)
    duration = float(len(y) / sr)

    # BPM
    bpm = _get_bpm(y, sr)
    logger.info(f"  BPM: {bpm:.1f}, Duration: {duration:.1f}s")

    # Detect kicks and snares
    kicks = _detect_kicks(y, sr)
    snares = _detect_snares(y, sr)

    return PercussionMap(
        kicks=kicks,
        snares=snares,
        bpm=bpm,
        duration=duration,
    )


def get_beat_grid(
    percussion_map: PercussionMap,
    bpm: float | None = None,
) -> list[dict]:
    """
    Combine kicks and snares into a unified beat grid for edit decisions.
    Returns sorted list of {"time": float, "type": "kick"|"snare", "intensity": float}
    """
    bpm = bpm or percussion_map.bpm
    beats = []

    for k in percussion_map.kicks:
        beats.append({"time": k.time, "type": "kick", "intensity": k.intensity})
    for s in percussion_map.snares:
        beats.append({"time": s.time, "type": "snare", "intensity": s.intensity})

    beats.sort(key=lambda x: x["time"])
    return beats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.kick_snare_detector <audio_or_video_path>")
        sys.exit(1)

    path = sys.argv[1]
    result = detect_kicks_snares(path)

    print(f"\nPercussion Map: {result.bpm:.1f} BPM, {result.duration:.1f}s")
    print(f"  Kicks:  {result.kicks.__len__()}")
    print(f"  Snares: {result.snares.__len__()}")

    print("\nFirst 10 kicks:")
    for k in result.kicks[:10]:
        print(f"    t={k.time:7.3f}s  intensity={k.intensity:.3f}")

    print("\nFirst 10 snares:")
    for s in result.snares[:10]:
        print(f"    t={s.time:7.3f}s  intensity={s.intensity:.3f}")
