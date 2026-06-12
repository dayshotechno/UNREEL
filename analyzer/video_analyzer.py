"""
Video Analyzer für DJ-Performance Videos.
Erkennt Szenenwechsel, Bewegungsintensität und Lichteffekte.
"""

import cv2
import numpy as np
from scenedetect import detect, ContentDetector, AdaptiveDetector
import config
import subprocess
import os
import json
from analyzer import tracking_engine


def analyze_video(video_path, progress_callback=None):
    """
    Führt vollständige visuelle Analyse durch.
    
    Returns:
        dict mit:
        - scene_changes: Liste von Zeitpunkten (Szenenwechsel)
        - motion_intensity: Array von {time, intensity} Werten
        - light_effects: Liste von {time, intensity} Lichteffekt-Events
        - resolution: {width, height}
        - fps: Framerate
        - duration: Dauer in Sekunden
    """
    if progress_callback:
        progress_callback("video", 0, "Video-Info wird gelesen...")

    # Video-Info holen
    video_info = _get_video_info(video_path)

    if progress_callback:
        progress_callback("video", 10, "Szenenwechsel werden erkannt...")

    # Scene Detection
    scene_changes = _detect_scenes(video_path)

    if progress_callback:
        progress_callback("video", 40, "Bewegung wird analysiert...")

    # Motion Intensity + Light Effects (in einem Durchgang)
    motion_data, light_effects, transition_points = _analyze_motion_and_light(
        video_path, video_info, progress_callback
    )

    if progress_callback:
        progress_callback("video", 95, "Video-Analyse abgeschlossen")

    # Thumbnail generieren
    _generate_thumbnail(video_path)

    # YOLO Tracking
    if progress_callback:
        progress_callback("video", 96, "Starte Personen-Tracking (Auto-Framing)...")
    tracking_data = tracking_engine.analyze_tracking(video_path, fps=1.0, progress_callback=progress_callback)

    results = {
        "scene_changes": scene_changes,
        "motion_intensity": motion_data,
        "light_effects": light_effects,
        "transition_points": transition_points,
        "tracking_data": tracking_data,
        "resolution": {
            "width": video_info["width"],
            "height": video_info["height"]
        },
        "fps": video_info["fps"],
        "duration": video_info["duration"],
    }

    if progress_callback:
        progress_callback("video", 100, "Video-Analyse fertig")

    return results


def _get_video_info(video_path):
    """Liest Video-Metadaten via OpenCV."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Video kann nicht geöffnet werden: {video_path}")

    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration": 0,
    }
    if info["fps"] > 0:
        info["duration"] = info["frame_count"] / info["fps"]

    cap.release()
    return info


def _detect_scenes(video_path):
    """Erkennt Szenenwechsel mit PySceneDetect."""
    scene_changes = []

    try:
        # ContentDetector für harte Schnitte
        scene_list = detect(video_path, ContentDetector(threshold=config.SCENE_THRESHOLD))
        for scene in scene_list:
            scene_changes.append(scene[0].get_seconds())
    except Exception as e:
        print(f"Scene detection Fehler: {e}")

    return scene_changes


def _analyze_motion_and_light(video_path, video_info, progress_callback=None):
    """
    Analysiert Bewegungsintensität und Lichteffekte in einem Durchgang.
    Sampelt nur jeden N-ten Frame für Performance.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return [], [], []

    fps = video_info["fps"]
    total_frames = video_info["frame_count"]

    # Nur jeden 6. Frame analysieren (ca. 5 fps bei 30fps Video)
    sample_interval = max(1, int(fps / 5))

    motion_data = []
    light_effects = []
    transition_points = [] # Neu: Für Blackouts/Whiteouts

    prev_gray = None
    prev_brightness = None
    frame_idx = 0
    analyzed = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_interval == 0:
            # In Graustufen konvertieren
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Verkleinern für Performance
            small_gray = cv2.resize(gray, (320, 240))

            current_time = frame_idx / fps

            # --- Motion ---
            if prev_gray is not None:
                # Frame-Differenz
                diff = cv2.absdiff(small_gray, prev_gray)
                motion_value = float(np.mean(diff)) / 255.0  # Normalisiert 0-1
                motion_data.append({
                    "time": round(current_time, 2),
                    "intensity": round(motion_value, 4)
                })

            # --- Lichteffekte & Helligkeit ---
            brightness = float(np.mean(small_gray))
            
            # Blackout Erkennung (sehr dunkel)
            if brightness < 15:
                transition_points.append({
                    "time": round(current_time, 2),
                    "type": "blackout",
                    "intensity": round(1.0 - (brightness / 15.0), 4)
                })
            
            # Whiteout Erkennung (sehr hell)
            elif brightness > 230:
                transition_points.append({
                    "time": round(current_time, 2),
                    "type": "whiteout",
                    "intensity": round((brightness - 230.0) / 25.0, 4)
                })

            if prev_brightness is not None:
                brightness_change = abs(brightness - prev_brightness)
                if brightness_change > config.BRIGHTNESS_CHANGE_THRESHOLD:
                    light_effects.append({
                        "time": round(current_time, 2),
                        "intensity": round(min(brightness_change / 100.0, 1.0), 4)
                    })

            prev_gray = small_gray
            prev_brightness = brightness
            analyzed += 1

            # Progress Update alle 100 analysierten Frames
            if progress_callback and analyzed % 100 == 0:
                pct = 40 + int((frame_idx / max(total_frames, 1)) * 50)
                progress_callback("video", min(pct, 90),
                                  f"Frame {frame_idx}/{total_frames} analysiert...")

        frame_idx += 1

    cap.release()

    # Motion normalisieren (relativ zum Maximum)
    if motion_data:
        max_motion = max(m["intensity"] for m in motion_data) or 1.0
        for m in motion_data:
            m["intensity"] = round(m["intensity"] / max_motion, 4)

    return motion_data, light_effects, transition_points


def _generate_thumbnail(video_path):
    """Generiert ein Thumbnail-Bild vom Video."""
    basename = os.path.splitext(os.path.basename(video_path))[0]
    thumb_path = os.path.join(config.THUMBNAILS_DIR, f"{basename}.jpg")

    if os.path.exists(thumb_path):
        return thumb_path

    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", "00:00:05",  # 5 Sekunden rein
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-y",
            thumb_path
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=30)
    except Exception as e:
        print(f"Thumbnail-Generierung fehlgeschlagen für {video_path}: {e}")
        thumb_path = None

    return thumb_path
