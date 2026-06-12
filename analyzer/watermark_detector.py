"""
CapCut Watermark Detector
Erkennt CapCut-Wasserzeichen anhand von Helligkeitsmustern
im typischen Wasserzeichen-Bereich (unterer Bildbereich, Mitte).
"""

import cv2
import numpy as np

# Wasserzeichen-Region (relative Koordinaten)
_WM_REGION = {
    'portrait':  {'x': (0.18, 0.82), 'y': (0.80, 0.95)},  # 9:16
    'landscape': {'x': (0.25, 0.75), 'y': (0.83, 0.96)},  # 16:9
}

_SAMPLE_FPS    = 4      # Frames pro Sekunde für Sampling
_SCAN_WINDOW   = 6.0    # Sekunden vorne/hinten scannen
_REL_BRIGHTNESS = 28    # Region muss X heller als Frame-Durchschnitt sein
_BRIGHT_MIN    = 155    # Schwellwert für "hell" (0–255)
_BRIGHT_FRAC   = 0.30   # Mindestanteil heller Pixel in der Region
_MIN_DURATION  = 0.4    # Mindestdauer eines WM-Blocks (Sekunden)


def _score_frame(frame, region: dict) -> bool:
    """
    True wenn im WM-Bereich ein Wasserzeichen-typisches Muster erkannt wird.

    Robustheit gegen Strobe/Lichteffekte: Die Region muss RELATIV heller
    sein als der Frame-Durchschnitt. Globale Flashes triggern nicht.
    """
    h, w = frame.shape[:2]
    x1, x2 = int(w * region['x'][0]), int(w * region['x'][1])
    y1, y2 = int(h * region['y'][0]), int(h * region['y'][1])

    wm_roi    = frame[y1:y2, x1:x2]
    wm_gray   = cv2.cvtColor(wm_roi, cv2.COLOR_BGR2GRAY)
    full_gray = cv2.cvtColor(frame,  cv2.COLOR_BGR2GRAY)

    wm_mean    = float(np.mean(wm_gray))
    full_mean  = float(np.mean(full_gray))
    bright_frac = float(np.sum(wm_gray > _BRIGHT_MIN) / wm_gray.size)

    return (wm_mean - full_mean) > _REL_BRIGHTNESS and bright_frac > _BRIGHT_FRAC


def _find_block(scored: list, from_start: bool, total: float) -> float:
    """
    Findet die Länge eines zusammenhängenden WM-Blocks
    am Anfang (from_start=True) oder am Ende (from_start=False).
    """
    if not scored:
        return 0.0

    if from_start:
        if not scored[0][1]:
            return 0.0
        last_wm_ts = 0.0
        for ts, has_wm in scored:
            if has_wm:
                last_wm_ts = ts
            else:
                break
        return round(last_wm_ts + 1.0 / _SAMPLE_FPS, 2)
    else:
        if not scored[-1][1]:
            return 0.0
        first_wm_ts = scored[-1][0]
        for ts, has_wm in reversed(scored):
            if has_wm:
                first_wm_ts = ts
            else:
                break
        return round(total - first_wm_ts, 2)


def detect_capcut_watermark(video_path: str) -> dict:
    """
    Scannt Anfang und Ende des Videos auf CapCut-Wasserzeichen.

    Returns:
        {
            'detected':   bool,
            'trim_start': float,  # Sekunden am Anfang abschneiden
            'trim_end':   float,  # Sekunden am Ende abschneiden
            'duration':   float,  # Gesamtlänge in Sekunden
        }
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {'detected': False, 'trim_start': 0.0, 'trim_end': 0.0,
                'duration': 0.0, 'error': 'Cannot open video'}

    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration     = total_frames / fps
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    region = _WM_REGION['portrait' if height > width else 'landscape']
    step   = max(1, int(fps / _SAMPLE_FPS))
    scan_n = min(int(_SCAN_WINDOW * fps), total_frames // 3)

    def _scan(indices):
        results = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            results.append((idx / fps, _score_frame(frame, region)))
        return results

    start_scores = _scan(range(0, scan_n, step))
    end_scores   = _scan(range(total_frames - scan_n, total_frames, step))
    cap.release()

    trim_start = _find_block(start_scores, from_start=True,  total=duration)
    trim_end   = _find_block(end_scores,   from_start=False, total=duration)

    if trim_start < _MIN_DURATION:
        trim_start = 0.0
    if trim_end < _MIN_DURATION:
        trim_end = 0.0

    return {
        'detected':   trim_start > 0 or trim_end > 0,
        'trim_start': trim_start,
        'trim_end':   trim_end,
        'duration':   round(duration, 2),
    }
