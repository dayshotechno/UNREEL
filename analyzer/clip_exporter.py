"""
Clip Exporter – FFmpeg-basierter Export von Video-Clips.
Unterstützt Reel-Format (9:16) und Raw Clips (Original-Format).
"""

import subprocess
import threading
import os
import json
import config

# Moderater "Dark Techno" Look Filter für einen einheitlichen Vibe
# - eq: Kontrast stark erhöht (1.15), kaltes Blau-Tinting (gamma_b=1.05), entsättigt (0.8)
# - vignette: dunkle Ränder für den Club-Vibe
CINEMATIC_LOOK_FILTER = "eq=contrast=1.15:brightness=-0.05:saturation=0.8:gamma=0.9:gamma_g=0.95:gamma_r=0.95:gamma_b=1.05,vignette=PI/4"

# ── Cancellable FFmpeg Registry ──────────────────────────────────────────────
# Mappt thread_id → laufender Popen-Prozess.
# app.py liest dieses Dict um den Prozess von außen abzubrechen.
_active_procs: dict[int, subprocess.Popen] = {}
_active_procs_lock = threading.Lock()


def _run_ffmpeg(cmd: list, timeout: int = 300) -> tuple[int, str]:
    """
    Ersetzt subprocess.run() für alle FFmpeg-Aufrufe.
    Registriert den Prozess im _active_procs-Dict damit er von außen
    via cancel_export() abgebrochen werden kann.
    Gibt (returncode, stderr) zurück.
    """
    tid = threading.get_ident()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with _active_procs_lock:
        _active_procs[tid] = proc
    try:
        _, raw_err = proc.communicate(timeout=timeout)
        return proc.returncode, raw_err.decode(errors="replace")
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise RuntimeError(f"FFmpeg Timeout (>{timeout}s)")
    finally:
        with _active_procs_lock:
            _active_procs.pop(tid, None)


# ── Tempo-Stretch (BPM-Matching) ─────────────────────────────────────────────
def _speed_params(duration, speed):
    """
    Gibt (use_speed, out_duration) zurück.
    use_speed ist False bei speed≈1.0 → kein setpts/atempo nötig.
    out_duration ist die Länge des Clips NACH dem Stretch (= duration / speed),
    wird sowohl für das Output-`-t`-Limit als auch für Fade-Zeiten gebraucht.
    """
    use = bool(speed) and speed > 0 and abs(speed - 1.0) > 1e-3
    out_dur = (duration / speed) if use else duration
    return use, out_dur


def _atempo_chain(speed):
    """
    Zerlegt einen Tempo-Faktor in eine Kette von atempo-Filtern.
    atempo akzeptiert pro Instanz nur 0.5–2.0; größere Faktoren werden
    durch Verkettung erreicht (z.B. 2.5 → atempo=2.0,atempo=1.25).
    """
    factors = []
    s = float(speed)
    while s > 2.0:
        factors.append(2.0)
        s /= 2.0
    while s < 0.5:
        factors.append(0.5)
        s *= 2.0
    factors.append(round(s, 6))
    return [f"atempo={f}" for f in factors]


def export_clip(video_path, start_sec, end_sec, output_name,
                mode="reel", fade=True, progress_callback=None, output_dir=None,
                speed=1.0, crop_x=0.5):
    """
    Exportiert einen einzelnen Clip.
    
    Args:
        video_path: Pfad zum Quell-Video
        start_sec: Start-Zeitpunkt in Sekunden
        end_sec: End-Zeitpunkt in Sekunden
        output_name: Name der Ausgabedatei (ohne Extension)
        mode: "reel" (9:16) oder "raw" (Original)
        fade: Fade-In/Fade-Out hinzufügen
        progress_callback: Optional, Fortschritts-Callback
        output_dir: Zielordner. Falls None, wird config.SINGLE_DOWNLOADS_DIR verwendet.
        speed: Tempo-Faktor (>1 schneller, <1 langsamer). 1.0 = unverändert.
        crop_x: Normalized X coordinate for cropping (0.0 to 1.0)

    Returns:
        dict mit Output-Pfad und Metadaten
    """
    duration = end_sec - start_sec
    if duration <= 0:
        raise ValueError("Clip-Dauer muss positiv sein")

    if output_dir is None:
        output_dir = config.SINGLE_DOWNLOADS_DIR

    os.makedirs(output_dir, exist_ok=True)

    if mode == "reel":
        output_path = os.path.join(output_dir, f"{output_name}.mp4")
        result = _export_reel(video_path, start_sec, duration, output_path, fade, speed=speed, crop_x=crop_x)
    else:
        ext = os.path.splitext(video_path)[1].lower()
        output_path = os.path.join(output_dir, f"{output_name}{ext}")
        result = _export_raw(video_path, start_sec, duration, output_path, speed=speed)

    return result


def _build_overlay_vf(duration, fade=True, look_filter=None, speed=1.0, crop_x=0.5):
    """
    Gibt die vollständige vf-Filterkette für einen Reel-Export zurück.
    Enthält Scale/Crop, Cinematic Look, Fade, Chromatic Aberration,
    CRT-Scanlines und Film Grain — aber KEIN Logo-Overlay
    (das braucht filter_complex mit zweitem Input).

    speed != 1.0 → setpts-basierter Tempo-Stretch (BPM-Matching).
    Fade-Out wird auf die gestretchte Ausgabedauer ausgerichtet.
    """
    use_speed, out_dur = _speed_params(duration, speed)

    parts = []
    if use_speed:
        parts.append(f"setpts=PTS/{speed:.6f}")
    parts.append("scale=1080:1920:force_original_aspect_ratio=increase")
    parts.append(f"crop={config.REEL_WIDTH}:{config.REEL_HEIGHT}:'max(0, min(iw-{config.REEL_WIDTH}, iw*{crop_x}-{config.REEL_WIDTH}/2))':0,setsar=1")
    parts.append(look_filter if look_filter else CINEMATIC_LOOK_FILTER)

    if fade and config.FADE_DURATION_SEC > 0:
        fd = config.FADE_DURATION_SEC
        parts.append(f"fade=t=in:st=0:d={fd}")
        parts.append(f"fade=t=out:st={max(0.0, out_dur - fd)}:d={fd}")

    shift = getattr(config, "OVERLAY_CHROMA_SHIFT", 0)
    if shift > 0:
        parts.append(f"rgbashift=rh={shift}:rv=0:bh=-{shift}:bv=0")

    dark = getattr(config, "OVERLAY_SCANLINE_DARKNESS", 0)
    if dark > 0:
        light = round(1.0 - dark, 4)
        parts.append(
            f"geq=lum='lum(X,Y)*({light}+{dark:.4f}*gt(mod(Y,4),1))'"
            f":cb='cb(X,Y)':cr='cr(X,Y)'"
        )

    grain = getattr(config, "OVERLAY_GRAIN_STRENGTH", 0)
    if grain > 0:
        parts.append(f"noise=alls={grain}:allf=t+u")

    return parts


def _export_reel(video_path, start_sec, duration, output_path, fade=True, look_filter=None, speed=1.0, crop_x=0.5):
    """
    Exportiert im Reel-Format (9:16, 1080x1920) mit allen Overlays.
    Wenn LOGO_PATH gesetzt ist, wird das Logo via filter_complex eingebrannt.
    speed != 1.0 → Tempo-Stretch (Video via setpts, Audio via atempo).
    """
    use_speed, out_dur = _speed_params(duration, speed)
    vf_parts = _build_overlay_vf(duration, fade, look_filter, speed, crop_x)

    af_parts = []
    if use_speed:
        af_parts.extend(_atempo_chain(speed))
    if fade and config.FADE_DURATION_SEC > 0:
        fd = config.FADE_DURATION_SEC
        af_parts.append(f"afade=t=in:st=0:d={fd}")
        af_parts.append(f"afade=t=out:st={max(0.0, out_dur - fd)}:d={fd}")

    logo_path = getattr(config, "LOGO_PATH", None)
    has_logo  = bool(logo_path and os.path.exists(logo_path))

    if has_logo:
        logo_scale   = getattr(config, "OVERLAY_LOGO_SCALE", 160)
        logo_opacity = getattr(config, "OVERLAY_LOGO_OPACITY", 0.65)
        logo_margin  = getattr(config, "OVERLAY_LOGO_MARGIN", 48)

        main_chain = ",".join(vf_parts)
        # colorkey entfernt den weißen Hintergrund aus alt master.png (similarity 0.30
        # erfasst reines Weiß sicher ohne in Schwarz/Rot zu greifen, blend=0.10 weiche Kante).
        # format=rgba erhält den Alpha-Kanal für das nachfolgende overlay.
        filter_complex = (
            f"[0:v]{main_chain}[main];"
            f"[1:v]scale={logo_scale}:-2,"
            f"colorkey=color=white:similarity=0.30:blend=0.10,"
            f"format=rgba,"
            f"colorchannelmixer=aa={logo_opacity}[logo];"
            f"[main][logo]overlay=W-w-{logo_margin}:H-h-{logo_margin}[out]"
        )
        cmd = [
            "ffmpeg",
            "-ss", str(start_sec),
            "-i", video_path,
            "-loop", "1", "-i", logo_path,
            "-t", str(out_dur),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "0:a?",
            "-c:v", config.REEL_CODEC,
            "-b:v", config.REEL_VIDEO_BITRATE,
            "-preset", config.REEL_PRESET,
            "-r", str(config.REEL_FPS),
            "-c:a", config.REEL_AUDIO_CODEC,
            "-b:a", config.REEL_AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg",
            "-ss", str(start_sec),
            "-i", video_path,
            "-t", str(out_dur),
            "-vf", ",".join(vf_parts),
            "-c:v", config.REEL_CODEC,
            "-b:v", config.REEL_VIDEO_BITRATE,
            "-preset", config.REEL_PRESET,
            "-r", str(config.REEL_FPS),
            "-c:a", config.REEL_AUDIO_CODEC,
            "-b:a", config.REEL_AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

    if af_parts:
        cmd.insert(-2, "-af")
        cmd.insert(-2, ",".join(af_parts))

    rc, stderr = _run_ffmpeg(cmd)
    if rc != 0:
        return _export_reel_simple(video_path, start_sec, duration, output_path, fade, look_filter, speed, crop_x)

    return {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "duration": duration,
        "mode": "reel",
        "resolution": f"{config.REEL_WIDTH}x{config.REEL_HEIGHT}",
    }


def _export_reel_simple(video_path, start_sec, duration, output_path, fade=True, look_filter=None, speed=1.0, crop_x=0.5):
    """Fallback-Export mit einfacherem Scale-Filter + Overlays (ohne Logo)."""
    use_speed, out_dur = _speed_params(duration, speed)

    vf_parts = []
    if use_speed:
        vf_parts.append(f"setpts=PTS/{speed:.6f}")
    vf_parts += [
        "scale=1080:1920:force_original_aspect_ratio=increase",
        f"crop={config.REEL_WIDTH}:{config.REEL_HEIGHT}:'max(0, min(iw-{config.REEL_WIDTH}, iw*{crop_x}-{config.REEL_WIDTH}/2))':0,setsar=1",
        look_filter if look_filter else CINEMATIC_LOOK_FILTER,
    ]

    if fade and config.FADE_DURATION_SEC > 0:
        fd = config.FADE_DURATION_SEC
        vf_parts.append(f"fade=t=in:st=0:d={fd}")
        vf_parts.append(f"fade=t=out:st={max(0.0, out_dur - fd)}:d={fd}")

    shift = getattr(config, "OVERLAY_CHROMA_SHIFT", 0)
    if shift > 0:
        vf_parts.append(f"rgbashift=rh={shift}:rv=0:bh=-{shift}:bv=0")

    dark = getattr(config, "OVERLAY_SCANLINE_DARKNESS", 0)
    if dark > 0:
        light = round(1.0 - dark, 4)
        vf_parts.append(
            f"geq=lum='lum(X,Y)*({light}+{dark:.4f}*gt(mod(Y,4),1))'"
            f":cb='cb(X,Y)':cr='cr(X,Y)'"
        )

    grain = getattr(config, "OVERLAY_GRAIN_STRENGTH", 0)
    if grain > 0:
        vf_parts.append(f"noise=alls={grain}:allf=t+u")

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg",
        "-ss", str(start_sec),
        "-i", video_path,
        "-t", str(out_dur),
        "-vf", vf,
        "-c:v", config.REEL_CODEC,
        "-b:v", config.REEL_VIDEO_BITRATE,
        "-preset", config.REEL_PRESET,
        "-r", str(config.REEL_FPS),
        "-c:a", config.REEL_AUDIO_CODEC,
        "-b:a", config.REEL_AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-y",
        output_path
    ]

    if use_speed:
        cmd.insert(-2, "-af")
        cmd.insert(-2, ",".join(_atempo_chain(speed)))

    rc, stderr = _run_ffmpeg(cmd)
    if rc != 0:
        raise RuntimeError(f"FFmpeg Fehler: {stderr[:500]}")

    return {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "duration": duration,
        "mode": "reel",
        "resolution": f"{config.REEL_WIDTH}x{config.REEL_HEIGHT}",
    }


def _export_raw(video_path, start_sec, duration, output_path, look_filter=None, speed=1.0):
    """
    Exportiert im Original-Format (mit etwas Padding).
    Jetzt mit Cinematic Filter (erfordert Re-Encode).
    speed != 1.0 → Tempo-Stretch; Audio wird dann re-encodiert (atempo statt copy).
    """
    padded_start = max(0, start_sec - config.RAW_CLIP_PADDING_SEC)
    padded_duration = duration + 2 * config.RAW_CLIP_PADDING_SEC
    use_speed, out_dur = _speed_params(padded_duration, speed)

    vf = look_filter if look_filter else CINEMATIC_LOOK_FILTER
    if use_speed:
        vf = f"setpts=PTS/{speed:.6f}," + vf

    cmd = [
        "ffmpeg",
        "-ss", str(padded_start),
        "-i", video_path,
        "-t", str(out_dur),
        "-vf", vf,
        "-c:v", config.REEL_CODEC,
        "-b:v", config.REEL_VIDEO_BITRATE,
    ]
    if use_speed:
        # Stretch erfordert Audio-Re-Encode (copy würde den Ton entkoppeln)
        cmd += ["-af", ",".join(_atempo_chain(speed)),
                "-c:a", config.REEL_AUDIO_CODEC, "-b:a", config.REEL_AUDIO_BITRATE]
    else:
        cmd += ["-c:a", "copy"]  # Audio kann kopiert werden
    cmd += ["-movflags", "+faststart", "-y", output_path]

    rc, stderr = _run_ffmpeg(cmd)
    if rc != 0:
        raise RuntimeError(f"FFmpeg Fehler: {stderr[:500]}")

    return {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "duration": out_dur,
        "mode": "raw",
        "resolution": "original",
    }


def export_batch(video_path, clips, mode="reel", fade=True, progress_callback=None, output_dir=None):
    """
    Exportiert mehrere Clips auf einmal.
    """
    results = []
    total = len(clips)

    for i, clip in enumerate(clips):
        if progress_callback:
            progress_callback("export", int((i / total) * 100),
                              f"Exportiere Clip {i + 1}/{total}...")

        try:
            name = clip.get("name", f"clip_{i + 1:03d}")
            result = export_clip(
                video_path,
                clip["start"],
                clip["end"],
                name,
                mode=mode,
                fade=fade,
                output_dir=output_dir,
                speed=clip.get("speed", 1.0),
                crop_x=clip.get("crop_x", 0.5)
            )
            result["status"] = "success"
            results.append(result)
        except Exception as e:
            results.append({
                "name": clip.get("name", f"clip_{i + 1}"),
                "status": "error",
                "error": str(e)
            })

    if progress_callback:
        progress_callback("export", 100, f"{len(results)} Clips exportiert")

    return results


def export_montage(clips, output_name, mode="reel", fade=True, progress_callback=None,
                   output_dir=None, cancel_event=None):
    """
    Erstellt eine Montage aus mehreren Clips, die von VERSCHIEDENEN Videos stammen können.
    clips: Liste von {video_path, start, end}
    """
    if not clips:
        raise ValueError("Keine Clips für Montage angegeben")

    if output_dir is None:
        output_dir = config.BEST_OF_DIR
        
    os.makedirs(output_dir, exist_ok=True)
    
    ext = ".mp4" if mode == "reel" else ".mov" # Fallback extension
    output_path = os.path.join(output_dir, f"{output_name}.mp4")

    # Helligkeits-Normalisierung: Clips mit extremem Highlight-Anteil anpassen
    from analyzer.clip_normalizer import compute_montage_filters
    if progress_callback:
        progress_callback("montage", 2, "Helligkeit der Clips wird analysiert...")
    look_filters = compute_montage_filters(clips)

    # Temporäre Clips exportieren
    temp_files = []
    total = len(clips)
    concat_list_path = os.path.join(config.TEMP_DIR, f"concat_{output_name}.txt")

    try:
        for i, clip in enumerate(clips):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("__CANCELLED__")

            v_path = clip["video_path"]
            if progress_callback:
                progress_callback("montage", 5 + int((i / total) * 75),
                                  f"Verarbeite Teil {i + 1}/{total}...")

            temp_name = f"temp_montage_{i:03d}_{output_name}"
            temp_path = os.path.join(config.TEMP_DIR, f"{temp_name}.mp4")
            lf = look_filters.get(i)
            sp = clip.get("speed", 1.0)
            crop_x = clip.get("crop_x", 0.5)

            if mode == "reel":
                _export_reel(v_path, clip["start"], clip["end"] - clip["start"], temp_path, fade, lf, sp, crop_x)
            else:
                _export_raw(v_path, clip["start"], clip["end"] - clip["start"], temp_path, lf, sp)

            temp_files.append(temp_path)

        if progress_callback:
            progress_callback("montage", 85, "Clips werden zusammengefügt...")

        # Concat-Liste für FFmpeg erstellen
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for tf in temp_files:
                f.write(f"file '{tf.replace('\\', '/')}'\n")

        # Concat ausführen
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c:v", "copy",  # Einfaches Kopieren da alle identisch sind
            "-an",           # Originalton für Best-Of / Montage entfernen
            "-y",
            output_path
        ]

        if cancel_event and cancel_event.is_set():
            raise RuntimeError("__CANCELLED__")

        rc, stderr = _run_ffmpeg(cmd)
        if rc != 0:
            raise RuntimeError(f"FFmpeg Concat Fehler: {stderr[:500]}")

        if progress_callback:
            progress_callback("montage", 100, "Montage fertig!")

        return {
            "path": output_path,
            "filename": os.path.basename(output_path),
            "mode": mode,
            "clips_count": len(clips)
        }

    finally:
        # Temp-Dateien immer aufräumen (auch bei Fehler)
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        for tf in temp_files:
            if os.path.exists(tf):
                os.remove(tf)

def export_seamless_loop(video_path, start_sec, end_sec, output_name, mode="reel", progress_callback=None, output_dir=None, speed=1.0):
    """
    Erstellt einen perfekten Seamless Loop (Split & Swap Technik).
    Teilt den Clip in der Mitte, setzt Teil B vor Teil A und verbindet sie mit einem Crossfade.
    So sind Anfang und Ende des fertigen Clips das exakte selbe Frame.
    speed != 1.0 → beide Hälften werden gestretcht (BPM-Matching).
    """
    if output_dir is None:
        output_dir = config.BEST_OF_DIR
        
    os.makedirs(output_dir, exist_ok=True)
    ext = ".mp4" if mode == "reel" else ".mov"
    output_path = os.path.join(output_dir, f"{output_name}{ext}")

    duration = end_sec - start_sec
    if duration <= 2.0:
        raise ValueError("Clip für Loop muss länger als 2 Sekunden sein")

    mid_point = start_sec + (duration / 2.0)
    dur_A = mid_point - start_sec
    dur_B = end_sec - mid_point

    temp_A = os.path.join(config.TEMP_DIR, f"temp_loop_A_{output_name}.mp4")
    temp_B = os.path.join(config.TEMP_DIR, f"temp_loop_B_{output_name}.mp4")

    try:
        if progress_callback: progress_callback("loop", 10, "Exportiere Teil 1...")
        # Export A (ohne fade)
        if mode == "reel":
            _export_reel(video_path, start_sec, dur_A, temp_A, fade=False, speed=speed)
        else:
            _export_raw(video_path, start_sec, dur_A, temp_A, speed=speed)

        if progress_callback: progress_callback("loop", 40, "Exportiere Teil 2...")
        # Export B (ohne fade)
        if mode == "reel":
            _export_reel(video_path, mid_point, dur_B, temp_B, fade=False, speed=speed)
        else:
            _export_raw(video_path, mid_point, dur_B, temp_B, speed=speed)

        if progress_callback: progress_callback("loop", 70, "Verknüpfe zum Seamless Loop...")

        # Crossfade B into A (B is first, A is second)
        # offset bezieht sich auf die GESTRETCHTE Länge von Teil B
        fade_dur = 0.3
        _use_sp, eff_dur_B = _speed_params(dur_B, speed)
        offset = max(0.1, eff_dur_B - fade_dur)

        cmd = [
            "ffmpeg",
            "-i", temp_B,
            "-i", temp_A,
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={fade_dur}:offset={offset}[v];[0:a][1:a]acrossfade=d={fade_dur}[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", config.REEL_CODEC,
            "-b:v", config.REEL_VIDEO_BITRATE,
            "-c:a", config.REEL_AUDIO_CODEC,
            "-b:a", config.REEL_AUDIO_BITRATE,
            "-y",
            output_path
        ]

        rc, stderr = _run_ffmpeg(cmd)
        if rc != 0:
            raise RuntimeError(f"FFmpeg Loop Fehler: {stderr[:500]}")

        if progress_callback: progress_callback("loop", 100, "Seamless Loop fertig!")

        return {
            "path": output_path,
            "filename": os.path.basename(output_path),
            "mode": mode,
            "duration": dur_A + dur_B - fade_dur
        }

    finally:
        if os.path.exists(temp_A): os.remove(temp_A)
        if os.path.exists(temp_B): os.remove(temp_B)
