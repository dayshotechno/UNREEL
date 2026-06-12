"""
Clip Brightness Normalizer
Analysiert Clips auf extreme Helligkeit und berechnet adaptive
eq-Filter damit alle Clips einer Montage visuell zusammenpassen.
"""

import cv2
import numpy as np

# Wie viel heller ein Clip sein darf, bevor er korrigiert wird
_BRIGHT_THRESHOLD = 1.30   # >30% über Median → Korrektur einsetzen
_SAMPLES = 6                # Frames pro Clip für Helligkeits-Messung


def sample_clip_brightness(video_path: str, start: float, end: float) -> float:
    """
    Misst die mittlere Luminanz eines Clip-Abschnitts (0–255).
    Sampelt SAMPLES Frames gleichmäßig über die Clip-Dauer.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 100.0  # Fallback

    fps      = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = max(0.1, end - start)
    values   = []

    for i in range(_SAMPLES):
        t = start + duration * (i + 0.5) / _SAMPLES
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        values.append(float(np.mean(gray)))

    cap.release()
    return float(np.mean(values)) if values else 100.0


def build_look_filter(clip_brightness: float, target_brightness: float) -> str:
    """
    Gibt einen FFmpeg eq-Filter-String zurück, der für diesen Clip passend ist.

    Zu helle Clips werden per gamma + brightness-Anpassung an den Median angenähert.
    Der Standard-Cinematic-Look wird dabei als Basis beibehalten.

    clip_brightness : gemessene mittlere Luminanz des Clips (0–255)
    target_brightness: Ziel-Luminanz (Median aller Montage-Clips)
    """
    ratio = clip_brightness / max(target_brightness, 20)

    if ratio <= _BRIGHT_THRESHOLD:
        # Normaler Bereich: Standard-Cinematic-Look
        return "eq=contrast=1.05:brightness=-0.02:saturation=0.9"

    # Intensität der Korrektur: 0.0 (bei threshold) bis 1.0 (ab 2× Median)
    intensity = min((ratio - _BRIGHT_THRESHOLD) / (2.0 - _BRIGHT_THRESHOLD), 1.0)

    # Gamma < 1 dunkelt Lichter stärker als Schatten ab → natürlichere Wirkung
    gamma      = round(1.0  - intensity * 0.25,  2)   # 1.0  → 0.75
    brightness = round(-0.02 - intensity * 0.18, 3)   # -0.02 → -0.20
    contrast   = round(1.05  + intensity * 0.10,  2)   # 1.05  → 1.15
    saturation = round(0.90  - intensity * 0.08,  2)   # 0.90  → 0.82

    return (
        f"eq=contrast={contrast}:brightness={brightness}"
        f":saturation={saturation}:gamma={gamma}"
    )


def compute_montage_filters(clips: list) -> dict:
    """
    Analysiert alle Clips einer Montage und gibt ein Dict
    { clip_index: eq_filter_string } zurück.

    clips: Liste von {'video_path': str, 'start': float, 'end': float}
    """
    brightnesses = []
    for clip in clips:
        b = sample_clip_brightness(clip["video_path"], clip["start"], clip["end"])
        brightnesses.append(b)

    if not brightnesses:
        return {}

    median = float(np.median(brightnesses))

    filters = {}
    for i, (clip, brightness) in enumerate(zip(clips, brightnesses)):
        filters[i] = build_look_filter(brightness, median)

    return filters
