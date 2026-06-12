"""
UNREEL V3 – Audio Cross-Correlation Sync
Synchronizes multiple DJ video clips by finding the clip with the best audio
quality (highest RMS) and computing FFT-based cross-correlation offsets.

Usage:
    from analyzer.audio_sync import sync_all_clips
    offsets = sync_all_clips(["clip1.mov", "clip2.mov", "clip3.mov"])
    # → {"clip1.mov": 0.0, "clip2.mov": 12.347, "clip3.mov": -3.210}
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import librosa
from scipy.signal import correlate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SyncResult:
    """Result of audio synchronization for a set of clips."""
    reference_clip: str
    offsets: dict[str, float]  # {clip_path: offset_seconds}
    rms_values: dict[str, float]  # {clip_path: rms_level}
    sample_rate: int = 44100

    def to_dict(self) -> dict:
        return {
            "reference_clip": self.reference_clip,
            "offsets": self.offsets,
            "rms_values": {k: round(v, 6) for k, v in self.rms_values.items()},
            "sample_rate": self.sample_rate,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Sync results saved to {path}")


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _load_audio(video_path: str | Path, sr: int = 44100) -> np.ndarray:
    """Load audio from a video file using librosa. Returns mono float32 array."""
    path = str(video_path)
    logger.debug(f"Loading audio: {path}")
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y


def _compute_rms(y: np.ndarray) -> float:
    """Compute RMS energy of an audio signal."""
    return float(np.sqrt(np.mean(y ** 2)))


def find_reference_clip(video_paths: list[str | Path], sr: int = 44100) -> tuple[str, np.ndarray, dict[str, float]]:
    """
    Find the reference clip. If a master audio file (.mp3, .wav, .flac, .aiff, .aif)
    is present, it is automatically chosen as the reference.
    Otherwise, find the video clip with the highest RMS audio energy.
    
    Returns:
        (reference_path, reference_audio, rms_dict)
    """
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}
    
    rms_values: dict[str, float] = {}
    best_path = None
    best_rms = -1.0
    best_audio = None
    
    # First, check for an explicit master audio file
    master_audio_path = None
    for vp in video_paths:
        vp_str = str(vp)
        if Path(vp_str).suffix.lower() in AUDIO_EXTENSIONS:
            master_audio_path = vp_str
            break
            
    if master_audio_path:
        logger.info(f"  Found master audio file: {Path(master_audio_path).name}")
        try:
            best_audio = _load_audio(master_audio_path, sr=sr)
            best_rms = _compute_rms(best_audio)
            rms_values[master_audio_path] = best_rms
            best_path = master_audio_path
            
            # Still compute RMS for other clips just to have the values, 
            # but don't change the reference
            for vp in video_paths:
                vp_str = str(vp)
                if vp_str != master_audio_path:
                    try:
                        audio = _load_audio(vp, sr=sr)
                        rms_values[vp_str] = _compute_rms(audio)
                    except Exception:
                        rms_values[vp_str] = 0.0
                        
            logger.info(f"  → Reference clip: {Path(best_path).name} (Master Audio)")
            return best_path, best_audio, rms_values
        except Exception as e:
            logger.error(f"  Failed to load master audio {master_audio_path}: {e}")
            # Fall back to RMS method if master fails
    
    for vp in video_paths:
        vp_str = str(vp)
        if vp_str == master_audio_path:
            continue  # Already failed above
            
        try:
            audio = _load_audio(vp, sr=sr)
            rms = _compute_rms(audio)
            rms_values[vp_str] = rms
            logger.info(f"  {Path(vp_str).name}: RMS={rms:.4f}")

            if rms > best_rms:
                best_rms = rms
                best_path = vp_str
                best_audio = audio
        except Exception as e:
            logger.warning(f"  Failed to load {vp_str}: {e}")
            rms_values[vp_str] = 0.0

    if best_path is None:
        raise ValueError("No valid audio tracks found in any clip")

    logger.info(f"  → Reference clip: {Path(best_path).name} (RMS={best_rms:.4f})")
    return best_path, best_audio, rms_values


def compute_offset(
    ref_audio: np.ndarray,
    target_audio: np.ndarray,
    sr: int = 44100,
) -> float:
    """
    Compute the time offset (in seconds) between two audio signals
    using FFT-based cross-correlation.
    
    Positive offset means the target starts LATER than the reference.
    Negative offset means the target starts EARLIER.
    
    Uses scipy.signal.correlate with FFT method for performance on CPU.
    """
    # Normalize both signals to unit energy for robust correlation
    ref_norm = ref_audio / (np.std(ref_audio) + 1e-10)
    target_norm = target_audio / (np.std(target_audio) + 1e-10)

    # Use FFT-based cross-correlation (much faster than direct for long signals)
    correlation = correlate(ref_norm, target_norm, mode="full", method="fft")

    # Find the peak of the correlation
    lag_samples = int(np.argmax(correlation))

    # Convert lag to offset in seconds
    # The zero-lag point is at len(target_norm) - 1
    zero_lag = len(target_norm) - 1
    offset_samples = lag_samples - zero_lag
    offset_seconds = offset_samples / sr

    peak_corr = float(np.max(correlation))
    logger.debug(f"  Cross-correlation peak: {peak_corr:.2f} at offset={offset_seconds:.3f}s")

    return float(offset_seconds)


def sync_all_clips(
    video_paths: list[str | Path],
    sr: int = 44100,
    output_path: Path | None = None,
) -> SyncResult:
    """
    Synchronize all clips to the best-audio reference clip.
    
    Args:
        video_paths: List of video file paths to sync.
        sr: Sample rate for audio extraction.
        output_path: Optional path to save results JSON.
    
    Returns:
        SyncResult with offsets relative to the reference clip.
        The reference clip always has offset 0.0.
    """
    if len(video_paths) < 2:
        raise ValueError("Need at least 2 clips for synchronization")

    logger.info(f"Audio sync: Analyzing {len(video_paths)} clips...")

    # Step 1: Find the reference clip (best audio)
    ref_path, ref_audio, rms_values = find_reference_clip(video_paths, sr=sr)

    # Step 2: Compute offsets for all other clips
    offsets: dict[str, float] = {ref_path: 0.0}
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}

    for vp in video_paths:
        vp_str = str(vp)
        if vp_str == ref_path:
            continue
            
        if Path(vp_str).suffix.lower() in AUDIO_EXTENSIONS:
            # Skip computing offsets for other audio-only files if they aren't the reference
            logger.info(f"  Skipping extra audio file {Path(vp_str).name}")
            continue

        logger.info(f"  Computing offset for {Path(vp_str).name}...")
        target_audio = _load_audio(vp_str, sr=sr)
        offset = compute_offset(ref_audio, target_audio, sr=sr)
        offsets[vp_str] = round(offset, 3)
        logger.info(f"    → Offset: {offset:.3f}s")

    result = SyncResult(
        reference_clip=ref_path,
        offsets=offsets,
        rms_values=rms_values,
        sample_rate=sr,
    )

    if output_path:
        result.save(output_path)

    logger.info(f"Audio sync complete. Reference: {Path(ref_path).name}")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import glob

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.audio_sync <video_dir_or_files...>")
        print("  Example: python -m analyzer.audio_sync input/*.mov")
        sys.exit(1)

    # Expand glob patterns
    paths = []
    for arg in sys.argv[1:]:
        expanded = glob.glob(arg)
        paths.extend(expanded)

    if len(paths) < 2:
        print(f"Error: Found {len(paths)} files. Need at least 2 for sync.")
        sys.exit(1)

    print(f"Found {len(paths)} clips for sync.\n")
    result = sync_all_clips(
        paths,
        output_path=Path("output/audio_sync.json"),
    )

    print("\nResults:")
    for clip, offset in sorted(result.offsets.items(), key=lambda x: x[1]):
        print(f"  {Path(clip).name:40s}  offset={offset:+.3f}s  RMS={result.rms_values[clip]:.4f}")
