"""
Frame Hasher – Difference Hash (dHash) zur Erkennung visuell ähnlicher Clips.
Nutzt FFmpeg für Frame-Extraktion und numpy für die Hash-Berechnung.
Keine zusätzlichen Dependencies nötig.
"""

import subprocess
import numpy as np


def dhash(video_path: str, time_sec: float, hash_size: int = 8) -> int | None:
    """
    Berechnet den Difference-Hash eines Frames bei time_sec.

    dHash vergleicht jedes Pixel mit dem rechten Nachbarn (8×8 = 64 Bits).
    Gibt None zurück wenn der Frame nicht extrahierbar ist.
    """
    w, h = hash_size + 1, hash_size  # 9×8 Pixel → 64 horizontale Differenzen

    cmd = [
        "ffmpeg",
        "-ss", str(max(0.0, time_sec)),
        "-i", video_path,
        "-frames:v", "1",
        "-f", "rawvideo",
        "-pix_fmt", "gray",
        "-vf", f"scale={w}:{h}",
        "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=8)
        if result.returncode != 0 or len(result.stdout) < w * h:
            return None
        pixels = np.frombuffer(result.stdout[: w * h], dtype=np.uint8).reshape(h, w)
        diff = pixels[:, :-1] > pixels[:, 1:]
        return int.from_bytes(np.packbits(diff.flatten()).tobytes(), byteorder="big")
    except Exception:
        return None


def hamming(h1: int, h2: int) -> int:
    """Anzahl unterschiedlicher Bits zwischen zwei Hashes."""
    return bin(h1 ^ h2).count("1")


def filter_duplicates(clips: list, threshold: int = 6) -> list:
    """
    Entfernt visuell ähnliche Clips aus einer nach Score sortierten Liste.

    Für jeden Clip wird der Frame bei der Mitte des Zeitfensters gehasht und
    mit allen bereits akzeptierten Clips verglichen.
    Hamming-Distanz ≤ threshold → Duplikat → überspringen.

    threshold=6 ≈ 90% Bildähnlichkeit — fängt echte Duplikate ohne false positives
    bei typischen DJ-Performance-Videos (schnelle Lichtwechsel, hohe Dynamik).
    """
    if not clips:
        return clips

    accepted = []
    hashes: list[int | None] = []

    for clip in clips:
        mid = (clip["start"] + clip["end"]) / 2
        h = dhash(clip["video_path"], mid)

        if h is None:
            # Frame nicht extrahierbar → Clip trotzdem aufnehmen
            accepted.append(clip)
            hashes.append(None)
            continue

        is_dup = any(
            eh is not None and hamming(h, eh) <= threshold
            for eh in hashes
        )
        if not is_dup:
            accepted.append(clip)
            hashes.append(h)

    return accepted
