"""
Highlight Scoring Engine.
Kombiniert Audio- und Video-Analyse-Ergebnisse zu einem Highlight-Score
und generiert optimale Cut-Punkte für Social Media Reels.
"""

import numpy as np
import config


def compute_highlights(audio_results, video_results):
    """
    Kombiniert Audio- und Video-Scores zu einem Highlight-Score pro Zeitfenster.
    """
    duration = max(audio_results.get("duration", 0), video_results.get("duration", 0))
    if duration <= 0:
        return {"timeline": [], "highlights": [], "suggested_clips": []}

    # Timeline in 0.5-Sekunden-Schritten
    time_step = 0.5
    timeline_points = np.arange(0, duration, time_step)

    # --- Score-Kanäle berechnen ---
    audio_energy_score = _compute_energy_score(
        audio_results.get("energy_envelope", []),
        audio_results.get("energy_times", []),
        timeline_points
    )

    bass_drop_score = _compute_event_score(
        [d["time"] for d in audio_results.get("bass_drops", [])],
        [d["intensity"] for d in audio_results.get("bass_drops", [])],
        timeline_points,
        spread_sec=3.0
    )

    motion_score = _compute_motion_score(
        video_results.get("motion_intensity", []),
        timeline_points
    )

    scene_score = _compute_event_score(
        video_results.get("scene_changes", []),
        None,
        timeline_points,
        spread_sec=1.0
    )

    light_score = _compute_event_score(
        [l["time"] for l in video_results.get("light_effects", [])],
        [l["intensity"] for l in video_results.get("light_effects", [])],
        timeline_points,
        spread_sec=1.5
    )

    # --- Buildup-Bonus ---
    buildup_bonus = np.zeros(len(timeline_points))
    for bu in audio_results.get("buildups", []):
        end_time = bu["end"]
        for i, t in enumerate(timeline_points):
            if end_time <= t <= end_time + 4.0:
                buildup_bonus[i] = max(buildup_bonus[i], bu.get("intensity", 0.5))

    # --- Gewichteter Gesamt-Score ---
    combined_score = (
        config.WEIGHT_AUDIO_ENERGY * audio_energy_score +
        config.WEIGHT_BASS_DROPS * (bass_drop_score + buildup_bonus * 0.5) +
        config.WEIGHT_VISUAL_MOTION * motion_score +
        config.WEIGHT_SCENE_CHANGES * scene_score +
        config.WEIGHT_LIGHT_EFFECTS * light_score
    )

    # Sync-Bonus: Audio + Video Energie gleichzeitig (Golden Moments)
    sync_mask = (audio_energy_score > 0.6) & (motion_score > 0.6)
    combined_score[sync_mask] *= 1.2 # 20% Boost für synchronisierte Highlights

    # Transition Bonus: Momente kurz vor/nach Blackouts/Whiteouts
    transition_bonus = _compute_event_score(
        [t["time"] for t in video_results.get("transition_points", [])],
        [t["intensity"] for t in video_results.get("transition_points", [])],
        timeline_points,
        spread_sec=1.0
    )
    combined_score += transition_bonus * 0.2

    # Normalisieren
    max_score = combined_score.max() if combined_score.max() > 0 else 1.0
    combined_score = combined_score / max_score

    # --- Timeline erstellen ---
    timeline = []
    for i, t in enumerate(timeline_points):
        timeline.append({
            "time": round(float(t), 2),
            "score": round(float(combined_score[i]), 4),
            "components": {
                "audio_energy": round(float(audio_energy_score[i]), 4),
                "bass_drops": round(float(bass_drop_score[i]), 4),
                "motion": round(float(motion_score[i]), 4),
                "scenes": round(float(scene_score[i]), 4),
                "lights": round(float(light_score[i]), 4),
            }
        })

    # --- Highlights extrahieren ---
    highlights = _extract_highlight_regions(timeline_points, combined_score)

    # --- Clip-Vorschläge generieren ---
    suggested_clips = _generate_clip_suggestions(
        highlights, timeline_points, combined_score,
        audio_results.get("beat_times", []), duration,
        video_results.get("tracking_data", [])
    )

    return {
        "timeline": timeline,
        "highlights": highlights,
        "suggested_clips": suggested_clips,
        "transition_points": video_results.get("transition_points", []),
    }


def _compute_energy_score(energy_envelope, energy_times, timeline_points):
    """Interpoliert die Audio-Energie auf die Timeline."""
    score = np.zeros(len(timeline_points))
    if not energy_envelope or not energy_times:
        return score

    energy = np.array(energy_envelope)
    times = np.array(energy_times)

    score = np.interp(timeline_points, times, energy)
    return score


def _compute_event_score(event_times, event_intensities, timeline_points, spread_sec=2.0):
    """Erstellt einen Score-Kanal aus diskreten Events mit Gauss-Spread."""
    score = np.zeros(len(timeline_points))
    if not event_times:
        return score

    for i, t in enumerate(event_times):
        intensity = event_intensities[i] if event_intensities and i < len(event_intensities) else 1.0
        # Gauss-artige Verteilung um den Event
        distances = np.abs(timeline_points - t)
        contribution = intensity * np.exp(-(distances ** 2) / (2 * (spread_sec / 2) ** 2))
        score += contribution

    # Normalisieren
    if score.max() > 0:
        score = score / score.max()

    return score


def _compute_motion_score(motion_data, timeline_points):
    """Interpoliert Motion-Intensität auf die Timeline."""
    score = np.zeros(len(timeline_points))
    if not motion_data:
        return score

    times = np.array([m["time"] for m in motion_data])
    intensities = np.array([m["intensity"] for m in motion_data])

    if len(times) > 0:
        score = np.interp(timeline_points, times, intensities)

    return score


def _extract_highlight_regions(timeline_points, combined_score):
    """Findet zusammenhängende Highlight-Regionen über dem Schwellenwert."""
    highlights = []
    threshold = config.HIGHLIGHT_SCORE_THRESHOLD

    in_highlight = False
    start_idx = 0

    for i in range(len(combined_score)):
        if combined_score[i] >= threshold and not in_highlight:
            in_highlight = True
            start_idx = i
        elif (combined_score[i] < threshold or i == len(combined_score) - 1) and in_highlight:
            in_highlight = False
            region_scores = combined_score[start_idx:i + 1]
            peak_idx = start_idx + np.argmax(region_scores)
            highlights.append({
                "start": round(float(timeline_points[start_idx]), 2),
                "end": round(float(timeline_points[min(i, len(timeline_points) - 1)]), 2),
                "peak_time": round(float(timeline_points[peak_idx]), 2),
                "peak_score": round(float(combined_score[peak_idx]), 4),
                "avg_score": round(float(np.mean(region_scores)), 4),
            })

    # Nach Score sortieren
    highlights.sort(key=lambda h: h["peak_score"], reverse=True)

    # Mindestabstand zwischen Highlights erzwingen
    filtered = []
    for h in highlights:
        too_close = False
        for existing in filtered:
            if abs(h["peak_time"] - existing["peak_time"]) < config.HIGHLIGHT_MIN_GAP_SEC:
                too_close = True
                break
        if not too_close:
            filtered.append(h)

    return filtered


def _generate_clip_suggestions(highlights, timeline_points, combined_score, beat_times, duration, tracking_data=None):
    """
    Generiert Clip-Vorschläge basierend auf Highlights und Reel-Presets.
    Richtet Start/Ende auf Beat-Grenzen aus.
    """
    if tracking_data is None:
        tracking_data = []

    suggestions = []
    beat_times = np.array(beat_times) if beat_times else np.array([])

    for preset_key, preset in config.REEL_PRESETS.items():
        clip_duration = preset["duration"]

        for highlight in highlights[:40]:  # Max 40 Highlights pro Preset
            peak_time = highlight["peak_time"]

            # Clip um den Peak zentrieren
            raw_start = peak_time - clip_duration * 0.4  # Peak etwas nach links
            raw_end = raw_start + clip_duration

            # Grenzen prüfen
            if raw_start < 0:
                raw_start = 0
                raw_end = clip_duration
            if raw_end > duration:
                raw_end = duration
                raw_start = max(0, duration - clip_duration)

            # Auf Beat-Grenzen ausrichten
            start = _snap_to_beat(raw_start, beat_times)
            end = _snap_to_beat(raw_end, beat_times)

            # Sicherstellen, dass der Clip nicht zu kurz ist
            if end - start < clip_duration * 0.8:
                end = start + clip_duration

            if end > duration:
                end = duration

            # Durchschnittlichen Score im Clip berechnen
            clip_mask = (timeline_points >= start) & (timeline_points <= end)
            if np.any(clip_mask):
                avg_score = float(np.mean(combined_score[clip_mask]))
            else:
                avg_score = highlight["avg_score"]

            # Tracking/Auto-Framing: X-Koordinate für den Crop berechnen
            crop_x = 0.5
            if tracking_data:
                xs = [pt["x_center"] for pt in tracking_data if start <= pt["time"] <= end]
                if xs:
                    crop_x = sum(xs) / len(xs)

            suggestions.append({
                "start": round(float(start), 2),
                "end": round(float(end), 2),
                "duration": round(float(end - start), 2),
                "preset": preset_key,
                "preset_label": preset["label"],
                "score": round(avg_score, 4),
                "peak_time": highlight["peak_time"],
                "highlight_score": highlight["peak_score"],
                "crop_x": round(crop_x, 4)
            })

    # Nach Score sortieren und Überlappungen entfernen
    suggestions.sort(key=lambda s: s["score"], reverse=True)
    suggestions = _remove_overlapping_clips(suggestions)

    return suggestions


def _snap_to_beat(time_sec, beat_times):
    """Richtet einen Zeitpunkt am nächsten Beat aus."""
    if len(beat_times) == 0:
        return time_sec

    # Nächsten Beat finden
    diffs = np.abs(beat_times - time_sec)
    nearest_idx = np.argmin(diffs)

    # Nur snappen wenn der Beat nah genug ist (< 0.5s)
    if diffs[nearest_idx] < 0.5:
        return float(beat_times[nearest_idx])

    return time_sec


def _remove_overlapping_clips(clips):
    """Entfernt überlappende Clips (behält den mit höherem Score)."""
    if not clips:
        return clips

    filtered = [clips[0]]
    for clip in clips[1:]:
        overlaps = False
        for existing in filtered:
            # Prüfe Überlappung
            if clip["start"] < existing["end"] and clip["end"] > existing["start"]:
                # Gleicher Preset? Dann überspringen
                if clip["preset"] == existing["preset"]:
                    overlaps = True
                    break
        if not overlaps:
            filtered.append(clip)

    return filtered
