"""
Reel-Vids – Flask API Server
REST-API für Video-Analyse, Highlight-Erkennung und Clip-Export.
"""

import os
import json
import threading
import time
import zipfile
from flask import Flask, jsonify, request, send_from_directory, send_file, Response
from flask_cors import CORS
import config

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# --- In-Memory State ---
analysis_jobs = {}   # video_name -> {status, progress, stage, message, results}
analysis_cache = {}  # video_name -> full results
export_jobs = {}     # job_id -> {status, progress, message, results, filename}
global_usage_log = {} # video_name -> count (how often used in global best of)

# --- Cancel-Infrastruktur ---
_job_threads: dict   = {}   # job_id -> thread_id (int)
_cancel_events: dict = {}   # job_id -> threading.Event

# Begrenzt parallele Analysen (librosa + OpenCV sind GIL-frei → echte CPU-Parallelität)
_analysis_semaphore = threading.Semaphore(3)

# Persistenz für Usage Log

# Persistenz für Usage Log
USAGE_LOG_PATH = os.path.join(config.OUTPUT_DIR, "global_usage_log.json")
if os.path.exists(USAGE_LOG_PATH):
    try:
        with open(USAGE_LOG_PATH, "r") as f:
            global_usage_log = json.load(f)
    except: pass

def save_usage_log():
    with open(USAGE_LOG_PATH, "w") as f:
        json.dump(global_usage_log, f)


# ── Metadaten-Zeitstempel Cache ──────────────────────────────────
_creation_time_cache = {}   # v_path -> float (Unix timestamp)

def _get_video_creation_time(v_path):
    """
    Liest den echten Aufnahme-Zeitstempel aus den Video-Metadaten via ffprobe.
    Das ist der Zeitpunkt der Aufnahme, nicht das Dateisystem-Datum.
    Fallback: os.path.getmtime() falls keine Metadaten vorhanden.
    Ergebnis wird in-memory gecacht.
    """
    if v_path in _creation_time_cache:
        return _creation_time_cache[v_path]

    ts = None
    try:
        import subprocess as _sp
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "format_tags=creation_time",
            v_path
        ]
        result = _sp.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            ts_str = data.get("format", {}).get("tags", {}).get("creation_time")
            if ts_str:
                from datetime import datetime
                # "Z" → "+00:00" für Python < 3.11 Kompatibilität
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except Exception:
        pass

    if ts is None:
        ts = os.path.getmtime(v_path)   # Fallback: Filesystem-Zeit

    _creation_time_cache[v_path] = ts
    return ts


# ── BPM Tempo-Matching ───────────────────────────────────────────
# Stellt alle Clips eines Exports auf eine einheitliche Ziel-BPM (140–165),
# indem jeder Clip um den Faktor (target_bpm / source_bpm) zeit-gestretcht wird.
_source_bpm_cache = {}   # video_path -> float (erkannte BPM aus der Analyse)

TARGET_BPM_MIN = 140.0
TARGET_BPM_MAX = 165.0


def _get_source_bpm(video_path):
    """Liest die erkannte BPM (audio.tempo) aus dem _analysis.json eines Videos."""
    if video_path in _source_bpm_cache:
        return _source_bpm_cache[video_path]
    bpm = 0.0
    name = os.path.splitext(os.path.basename(video_path))[0]
    p = os.path.join(config.OUTPUT_DIR, f"{name}_analysis.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            bpm = float(json.load(f).get("audio", {}).get("tempo", 0) or 0)
    except Exception:
        bpm = 0.0
    _source_bpm_cache[video_path] = bpm
    return bpm


def _match_octave(bpm, target):
    """
    Bringt eine BPM in dieselbe "Oktave" wie target (Faktor in [1/√2, √2]).
    Korrigiert die typischen librosa-Fehler, bei denen Hard-Techno-Tracks
    halb (z.B. 75 statt 150) oder doppelt erkannt werden. So bleibt der
    resultierende Stretch-Faktor moderat (< ±41 %) statt katastrophaler 2×.
    """
    if bpm <= 0:
        return 0.0
    while bpm < target / 1.414:
        bpm *= 2.0
    while bpm > target * 1.414:
        bpm /= 2.0
    return bpm


def _parse_target_bpm(data):
    """
    Liest 'target_bpm' aus dem Request-Body.
    Gibt None zurück, wenn kein/ungültiger Wert (→ kein Stretch),
    sonst den auf [140, 165] begrenzten Float.
    """
    tb = (data or {}).get("target_bpm")
    if tb in (None, "", 0, "0", False):
        return None
    try:
        tb = float(tb)
    except (TypeError, ValueError):
        return None
    if tb <= 0:
        return None
    return max(TARGET_BPM_MIN, min(TARGET_BPM_MAX, tb))


def _single_video_speed(video_path, target_bpm):
    """Stretch-Faktor für ein einzelnes Video (für Einzel-/Batch-Export)."""
    if not target_bpm:
        return 1.0
    src = _match_octave(_get_source_bpm(video_path), target_bpm)
    if not src or src <= 0:
        return 1.0
    return round(max(0.5, min(2.0, target_bpm / src)), 6)


def _apply_target_bpm(clips, target_bpm):
    """
    Setzt clip['speed'] für jeden Clip einer (Multi-Video-)Montage.
    No-op wenn target_bpm None ist. Nutzt die pro Video erkannte BPM,
    oktav-normalisiert, sodass jeder Clip auf die Ziel-BPM kommt.
    """
    if not target_bpm:
        return
    for c in clips:
        c["speed"] = _single_video_speed(c.get("video_path", ""), target_bpm)


def _sanitize_video_filename(filename):
    """
    Schützt gegen Path-Traversal-Angriffe.
    Gibt den bereinigten Dateinamen zurück, oder None bei ungültigem Input.
    - Entfernt alle Verzeichnis-Komponenten (z.B. '../', '/')
    - Erlaubt nur Dateierweiterungen aus SUPPORTED_EXTENSIONS
    """
    safe = os.path.basename(filename)
    if not safe:
        return None
    ext = os.path.splitext(safe)[1].lower()
    if ext not in {e.lower() for e in config.SUPPORTED_EXTENSIONS}:
        return None
    return safe


# ========================
# STATIC / FRONTEND
# ========================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ========================
# VIDEO LISTING
# ========================

@app.route("/api/videos")
def list_videos():
    """Listet alle Videos im Quellordner."""
    videos = []
    for f in os.listdir(config.VIDEO_SOURCE_DIR):
        ext = os.path.splitext(f)[1].lower()
        if ext in {e.lower() for e in config.SUPPORTED_EXTENSIONS}:
            # Punkt-Dateien (._xxx) überspringen
            if f.startswith("._"):
                continue
            filepath = os.path.join(config.VIDEO_SOURCE_DIR, f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)

            # Thumbnail wird on-the-fly generiert
            has_thumb = True

            # Prüfe ob bereits analysiert
            is_analyzed = f in analysis_cache

            videos.append({
                "filename": f,
                "size_mb": round(size_mb, 1),
                "has_thumbnail": has_thumb,
                "is_analyzed": is_analyzed,
                "usage_count": global_usage_log.get(f, 0)
            })

    # Nach Größe sortieren (größte zuerst)
    videos.sort(key=lambda v: v["size_mb"], reverse=True)

    return jsonify({"videos": videos, "count": len(videos)})


# ========================
# THUMBNAILS & VIDEO STREAMING
# ========================

@app.route("/api/thumbnail/<filename>")
def get_thumbnail(filename):
    """Liefert das Thumbnail eines Videos. Generiert es via FFmpeg, falls nicht vorhanden."""
    filename = _sanitize_video_filename(filename)
    if not filename:
        return jsonify({"error": "Ungültiger Dateiname"}), 400
    basename = os.path.splitext(filename)[0]
    thumb_path = os.path.join(config.THUMBNAILS_DIR, f"{basename}.jpg")

    if not os.path.exists(thumb_path):
        from analyzer.video_analyzer import _generate_thumbnail
        filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
        if os.path.exists(filepath):
            _generate_thumbnail(filepath)

    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")
    return jsonify({"error": "Thumbnail nicht gefunden"}), 404


@app.route("/api/video/<filename>")
def stream_video(filename):
    """Streamt ein Video-File."""
    filename = _sanitize_video_filename(filename)
    if not filename:
        return jsonify({"error": "Ungültiger Dateiname"}), 400
    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    # Range-Request Support für Video-Streaming
    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("Range")

    if range_header:
        byte1, byte2 = 0, None
        match = range_header.replace("bytes=", "").split("-")
        byte1 = int(match[0])
        if match[1]:
            byte2 = int(match[1])
        else:
            byte2 = file_size - 1

        length = byte2 - byte1 + 1

        with open(filepath, "rb") as f:
            f.seek(byte1)
            data = f.read(length)

        resp = Response(data, 206, mimetype="video/mp4",
                        direct_passthrough=True)
        resp.headers.add("Content-Range", f"bytes {byte1}-{byte2}/{file_size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(length))
        return resp

    return send_file(filepath, mimetype="video/mp4")


@app.route("/api/output/<path:filepath>")
def serve_output(filepath):
    """Serviert exportierte Dateien aus dem Output-Ordner."""
    full_path = os.path.join(config.OUTPUT_DIR, filepath)
    if not os.path.exists(full_path):
        return jsonify({"error": "Datei nicht gefunden"}), 404
    return send_file(full_path)


# ========================
# ANALYSE
# ========================

@app.route("/api/analyze/<filename>", methods=["POST"])
def start_analysis(filename):
    """Startet die Analyse-Pipeline für ein Video."""
    filename = _sanitize_video_filename(filename)
    if not filename:
        return jsonify({"error": "Ungültiger Dateiname"}), 400
    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    # Bereits in Arbeit?
    if filename in analysis_jobs and analysis_jobs[filename]["status"] == "running":
        return jsonify({"status": "already_running", "progress": analysis_jobs[filename]})

    # Job starten
    analysis_jobs[filename] = {
        "status": "running",
        "progress": 0,
        "stage": "starting",
        "message": "Analyse wird gestartet...",
        "started_at": time.time(),
    }

    thread = threading.Thread(target=_run_analysis, args=(filename, filepath))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "filename": filename})

@app.route("/api/analyze/all", methods=["POST"])
def start_batch_analysis():
    """Startet die Analyse für alle noch nicht analysierten Videos."""
    started = []
    for f in os.listdir(config.VIDEO_SOURCE_DIR):
        ext = os.path.splitext(f)[1].lower()
        if ext in {e.lower() for e in config.SUPPORTED_EXTENSIONS}:
            if f.startswith("._"):
                continue
            
            # Nur wenn noch nicht analysiert und nicht gerade läuft
            is_analyzed = f in analysis_cache or os.path.exists(
                os.path.join(config.OUTPUT_DIR, f"{os.path.splitext(f)[0]}_analysis.json")
            )
            is_running = f in analysis_jobs and analysis_jobs[f]["status"] == "running"
            
            if not is_analyzed and not is_running:
                # Analyse starten
                filepath = os.path.join(config.VIDEO_SOURCE_DIR, f)
                analysis_jobs[f] = {
                    "status": "running",
                    "progress": 0,
                    "stage": "queued",
                    "message": "In Warteschlange...",
                    "started_at": time.time(),
                }
                thread = threading.Thread(target=_run_analysis, args=(f, filepath))
                thread.daemon = True
                thread.start()
                started.append(f)
                
    return jsonify({"status": "started", "count": len(started), "videos": started})


def _run_analysis(filename, filepath):
    """Führt die Analyse-Pipeline in einem Hintergrund-Thread aus."""
    # Lazy imports um Startup schnell zu halten
    from analyzer.audio_analyzer import analyze_audio
    from analyzer.video_analyzer import analyze_video
    from analyzer.highlight_engine import compute_highlights

    def progress_cb(stage, pct, message):
        # Gesamt-Fortschritt: Audio 0-40%, Video 40-80%, Highlights 80-100%
        if stage == "audio":
            overall = int(pct * 0.4)
        elif stage == "video":
            overall = 40 + int(pct * 0.4)
        else:
            overall = 80 + int(pct * 0.2)

        analysis_jobs[filename].update({
            "progress": overall,
            "stage": stage,
            "message": message,
        })

    # Auf freien Analyse-Slot warten (max. 3 parallele Analysen)
    # Weitere Threads werden erstellt, blockieren hier bis ein Slot frei wird.
    analysis_jobs[filename].update({"stage": "queued", "message": "Warte auf freien Slot..."})
    with _analysis_semaphore:
        analysis_jobs[filename].update({"stage": "starting", "message": "Analyse wird gestartet..."})

        try:
            # 1. Audio-Analyse
            audio_results = analyze_audio(filepath, progress_callback=progress_cb)

            # 2. Video-Analyse
            video_results = analyze_video(filepath, progress_callback=progress_cb)

            # 3. Highlight Scoring
            progress_cb("highlights", 0, "Highlights werden berechnet...")
            highlight_results = compute_highlights(audio_results, video_results)
            progress_cb("highlights", 100, "Fertig!")

            # Ergebnisse zusammenführen
            full_results = {
                "filename": filename,
                "audio": audio_results,
                "video": {
                    "scene_changes": video_results["scene_changes"],
                    "motion_summary": {
                        "total_points": len(video_results["motion_intensity"]),
                        "avg_motion": (
                            sum(m["intensity"] for m in video_results["motion_intensity"]) /
                            max(len(video_results["motion_intensity"]), 1)
                        ),
                    },
                    "light_effects_count": len(video_results["light_effects"]),
                    "resolution": video_results["resolution"],
                    "fps": video_results["fps"],
                    "duration": video_results["duration"],
                },
                "highlights": highlight_results["highlights"],
                "timeline": highlight_results["timeline"],
                "suggested_clips": highlight_results["suggested_clips"],
            }

            # Cache speichern
            analysis_cache[filename] = full_results

            # Auch als JSON auf Disk speichern
            results_path = os.path.join(
                config.OUTPUT_DIR,
                f"{os.path.splitext(filename)[0]}_analysis.json"
            )
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(full_results, f, indent=2, ensure_ascii=False)

            analysis_jobs[filename].update({
                "status": "completed",
                "progress": 100,
                "stage": "done",
                "message": "Analyse abgeschlossen!",
                "completed_at": time.time(),
            })

        except Exception as e:
            analysis_jobs[filename].update({
                "status": "error",
                "message": f"Fehler: {str(e)}",
                "stage": "error",
            })
            import traceback
            traceback.print_exc()


@app.route("/api/status/<filename>")
def get_status(filename):
    """Gibt den aktuellen Analyse-Status zurück."""
    if filename in analysis_jobs:
        return jsonify(analysis_jobs[filename])
    return jsonify({"status": "not_started"})


@app.route("/api/results/<filename>")
def get_results(filename):
    """Gibt die Analyse-Ergebnisse zurück."""
    if filename in analysis_cache:
        return jsonify(analysis_cache[filename])

    # Versuche von Disk zu laden
    results_path = os.path.join(
        config.OUTPUT_DIR,
        f"{os.path.splitext(filename)[0]}_analysis.json"
    )
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        analysis_cache[filename] = results
        return jsonify(results)

    return jsonify({"error": "Keine Ergebnisse gefunden"}), 404


# ========================
# EXPORT
# ========================

@app.route("/api/export", methods=["POST"])
def export_clips():
    """Startet den Export von ausgewählten Clips im Hintergrund."""
    from analyzer.clip_exporter import export_batch

    data = request.json
    filename = data.get("filename")
    clips = data.get("clips", [])
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    fade = data.get("fade", True)

    if not filename or not clips:
        return jsonify({"error": "filename und clips sind erforderlich"}), 400

    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    # Job-ID generieren
    job_id = f"export_{int(time.time())}_{filename}"
    
    # Clip-Namen generieren falls nicht vorhanden
    base = os.path.splitext(filename)[0]
    for i, clip in enumerate(clips):
        if "name" not in clip:
            clip["name"] = f"{base}_{mode}_{i + 1:03d}"

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    sp = _single_video_speed(filepath, target_bpm)
    if sp != 1.0:
        for clip in clips:
            clip["speed"] = sp

    # Job initialisieren
    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Export von {len(clips)} Clips gestartet...",
        "filename": filename,
        "count": len(clips),
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_export_batch, 
        args=(job_id, filepath, clips, mode, fade)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


def _run_export_batch(job_id, filepath, clips, mode, fade):
    """Hintergrund-Thread für Batch-Export."""
    from analyzer.clip_exporter import export_batch

    def progress_cb(stage, pct, message):
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "progress": pct,
                "message": message
            })

    try:
        results = export_batch(
            filepath, clips, mode=mode, fade=fade, 
            progress_callback=progress_cb
        )
        
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Export erfolgreich abgeschlossen!",
                "results": results,
                "completed_at": time.time(),
            })
    except Exception as e:
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "status": "error",
                "message": f"Export fehlgeschlagen: {str(e)}",
            })
        import traceback
        traceback.print_exc()


@app.route("/api/export/montage", methods=["POST"])
def export_montage_endpoint():
    """Startet die Erstellung einer Montage im Hintergrund."""
    data = request.json
    filename = data.get("filename")
    clips = data.get("clips", [])
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    fade = data.get("fade", True)

    if not filename or not clips:
        return jsonify({"error": "filename und clips sind erforderlich"}), 400

    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    # Job-ID generieren
    job_id = f"montage_{int(time.time())}_{filename}"
    
    # Montage-Name
    base = os.path.splitext(filename)[0]
    output_name = f"{base}_montage_{int(time.time())}"

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    sp = _single_video_speed(filepath, target_bpm)
    if sp != 1.0:
        for clip in clips:
            clip["speed"] = sp

    # Job initialisieren
    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Montage aus {len(clips)} Clips wird erstellt...",
        "filename": filename,
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_montage_task, 
        args=(job_id, filepath, clips, output_name, mode, fade)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


def _run_montage_task(job_id, filepath, clips, output_name, mode, fade):
    """Hintergrund-Thread für Montage-Erstellung."""
    from analyzer.clip_exporter import export_montage

    def progress_cb(stage, pct, message):
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "progress": pct,
                "message": message
            })

    try:
        # v_path zum Clip-Dict hinzufügen für den Exporter
        for c in clips:
            c["video_path"] = filepath

        result = export_montage(
            clips, output_name, mode=mode, fade=fade, 
            progress_callback=progress_cb
        )
        
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Montage erfolgreich erstellt!",
                "results": [result], # Als Liste für Kompatibilität mit UI
                "completed_at": time.time(),
            })
    except Exception as e:
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "status": "error",
                "message": f"Montage fehlgeschlagen: {str(e)}",
            })
        import traceback
        traceback.print_exc()


# ── SMART PICK: intelligente, variable Clip-Auswahl fürs Editor Set ──
def _score_tier(score):
    """S/A/B/C-Tier (gleiche Schwellen wie das Frontend)."""
    if score >= 0.90: return "S"
    if score >= 0.75: return "A"
    if score >= 0.50: return "B"
    return "C"


def _length_bucket(duration):
    """Grobe Längen-Kategorie für den Längen-Mix."""
    if duration <= 2.5: return "short"
    if duration <= 4.0: return "mid"
    return "long"


def _classify_clip(clip, res):
    """
    Bestimmt den Moment-Typ eines Clips aus den vorhandenen Analyse-Daten.
    Priorität: DROP > BUILDUP > CROWD > (STROBE / HYPE / CALM aus Timeline).
    """
    s, e = clip["start"], clip["end"]
    audio = res.get("audio", {})

    # 1. DROP – ein Bass-Drop liegt im Clip-Fenster
    for d in audio.get("bass_drops", []):
        if s <= d.get("time", -1) <= e:
            return "DROP"
    # 2. BUILDUP – Clip überlappt einen Buildup
    for bu in audio.get("buildups", []):
        if s < bu.get("end", 0) and e > bu.get("start", 0):
            return "BUILDUP"
    # 3. CROWD – Clip startet kurz nach einem Drop (Reaktion / Kamera-Schnitt)
    for d in audio.get("bass_drops", []):
        if 0.3 <= (s - d.get("time", 0)) <= 7.0:
            return "CROWD"
    # 4. Charakter aus gemittelten Timeline-Komponenten im Clip-Fenster
    comps = [t["components"] for t in res.get("timeline", [])
             if "components" in t and s <= t.get("time", -1) <= e]
    if comps:
        n = len(comps)
        lights = sum(c.get("lights", 0)       for c in comps) / n
        scenes = sum(c.get("scenes", 0)       for c in comps) / n
        motion = sum(c.get("motion", 0)       for c in comps) / n
        energy = sum(c.get("audio_energy", 0) for c in comps) / n
        if lights > 0.45 or scenes > 0.5:
            return "STROBE"
        if motion > 0.5 and energy > 0.5:
            return "HYPE"
        if motion < 0.3 and energy < 0.35:
            return "CALM"
        return "HYPE" if (motion + energy) >= 1.0 else "CALM"
    return "HYPE"


@app.route("/api/export/best_of_set", methods=["POST"])
def export_best_of_set():
    """
    Editor Set: Einzelclips aller Videos, ausgewählt per SMART PICK
    (Moment-Typ-Quoten, Quellen-Spread, Längen-Mix, visuelle Dedup,
    gewichtetes Sampling → frisches Set bei jedem Lauf).
    Auswahl + Dedup (FFmpeg) laufen im Hintergrund-Thread.
    """
    data = request.json
    count = data.get("count", 30)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    # Kandidaten sammeln + anreichern (schnell, kein FFmpeg)
    all_clips = []
    for f in os.listdir(config.OUTPUT_DIR):
        if not f.endswith("_analysis.json"):
            continue
        video_name = f.replace("_analysis.json", "")
        v_path = None
        for ext in config.SUPPORTED_EXTENSIONS:
            p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
            if os.path.exists(p):
                v_path = p
                break
        if not v_path:
            continue

        with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
            res = json.load(j)

        usage = global_usage_log.get(os.path.basename(v_path), 0)
        rot = 0.8 ** usage   # Rotations-Gewichtung
        for c in res.get("suggested_clips", []):
            c = dict(c)
            c["video_path"]    = v_path
            c["video_name"]    = video_name
            c["moment_type"]   = _classify_clip(c, res)
            c["tier"]          = _score_tier(c.get("score", 0))
            c["length_bucket"] = _length_bucket(c.get("duration", 0))
            c["base_weight"]   = max(c.get("score", 0) * rot, 1e-4)
            all_clips.append(c)

    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404

    job_id = f"set_{int(time.time())}"
    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"SMART PICK: {len(all_clips)} Kandidaten werden ausgewertet...",
        "filename": "MULTI_SET",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_set_export_task,
        args=(job_id, all_clips, count, mode, target_bpm)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


def _smart_pick(all_clips, count, progress=None):
    """
    Wählt bis zu `count` Clips per gewichtetem Sampling mit Diversitäts-Penalty.
    Gewicht je Clip = base_weight (Score×Rotation) × Penalty für bereits oft
    gewählten Moment-Typ / dieselbe Quelle / dieselbe Länge → das Set wird
    automatisch vielfältig, bleibt aber qualitativ hoch und ist jedes Mal frisch.
    Harte Constraints: max. Clips pro Video, keine Zeitüberlappung, visuelle
    Dedup (dHash). 1 s Handles werden hier auf start/end gesetzt.
    """
    import random
    from collections import defaultdict
    from analyzer.frame_hasher import dhash, hamming

    PADDING = 1.0
    num_videos = len({c["video_name"] for c in all_clips}) or 1
    max_per_video = max(2, -(-count // num_videos) + 1)   # ceil(count/videos) + Puffer

    type_count   = defaultdict(int)
    source_count = defaultdict(int)
    length_count = defaultdict(int)
    video_intervals = defaultdict(list)
    accepted_hashes = []
    selected = []

    pool = list(all_clips)
    while pool and len(selected) < count:
        weights = []
        for c in pool:
            w = c["base_weight"]
            w *= 0.5  ** type_count[c["moment_type"]]
            w *= 0.45 ** source_count[c["video_name"]]
            w *= 0.8  ** length_count[c["length_bucket"]]
            weights.append(max(w, 1e-9))

        pick = random.choices(pool, weights=weights, k=1)[0]
        pool.remove(pick)

        # Quellen-Obergrenze
        if source_count[pick["video_name"]] >= max_per_video:
            continue

        # Zeit-Überlappung im selben Video (inkl. Handles)
        v = pick["video_path"]
        s_h = max(0.0, pick["start"] - PADDING)
        e_h = pick["end"] + PADDING
        if any(s_h < ee and e_h > ss for ss, ee in video_intervals[v]):
            continue

        # Visuelle Dedup – ein Frame aus der Clip-Mitte gehasht
        h = dhash(pick["video_path"], (pick["start"] + pick["end"]) / 2.0)
        if h is not None and any(hamming(h, ah) <= 6 for ah in accepted_hashes):
            continue

        pick = dict(pick)
        pick["start"] = s_h
        pick["end"]   = e_h
        selected.append(pick)
        video_intervals[v].append((s_h, e_h))
        type_count[pick["moment_type"]]     += 1
        source_count[pick["video_name"]]    += 1
        length_count[pick["length_bucket"]] += 1
        if h is not None:
            accepted_hashes.append(h)
        if progress:
            progress(len(selected))

    return selected


def _run_set_export_task(job_id, all_clips, count, mode, target_bpm=None):
    """Hintergrund-Thread: SMART PICK + Export der Einzelclips."""
    from collections import Counter
    from analyzer.clip_exporter import export_clip

    set_folder_name = job_id.replace("set_", "Set_")
    set_output_dir = os.path.join(config.EDITOR_SETS_DIR, set_folder_name)
    os.makedirs(set_output_dir, exist_ok=True)

    try:
        def _pick_progress(n):
            if job_id in export_jobs:
                export_jobs[job_id].update({
                    "message": f"SMART PICK: {n}/{count} Clips ausgewählt..."
                })

        selected = _smart_pick(all_clips, count, progress=_pick_progress)

        if not selected:
            if job_id in export_jobs:
                export_jobs[job_id].update({
                    "status": "error",
                    "message": "SMART PICK fand keine passenden Clips.",
                })
            return

        # Bestes zuerst (bestimmt die Nummerierung der Dateinamen)
        selected.sort(key=lambda c: c.get("score", 0), reverse=True)

        # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
        _apply_target_bpm(selected, target_bpm)

        # Rotation-Log aktualisieren (greift auch fürs Editor Set)
        for vn in {os.path.basename(c["video_path"]) for c in selected}:
            global_usage_log[vn] = global_usage_log.get(vn, 0) + 1
        save_usage_log()

        total = len(selected)
        results = []
        for i, clip in enumerate(selected):
            if job_id not in export_jobs:
                break
            export_jobs[job_id].update({
                "progress": int((i / total) * 100),
                "message": f"Export {i+1}/{total}: {clip['moment_type']} · {clip['video_name']}...",
            })
            # Name: 01_DROP_S_150BPM_<quelle>_<start>s
            # → Typ, Tier und (falls Tempo-Match aktiv) die Ziel-BPM im Media-Browser sichtbar
            bpm_tag = f"_{int(target_bpm)}BPM" if target_bpm else ""
            out_name = f"{i+1:02d}_{clip['moment_type']}_{clip['tier']}{bpm_tag}_{clip['video_name']}_{int(clip['start'])}s"
            res = export_clip(
                clip["video_path"], clip["start"], clip["end"],
                out_name, mode=mode, fade=False,   # kein Fade für manuellen Schnitt
                output_dir=set_output_dir,
                speed=clip.get("speed", 1.0),
            )
            res["status"]      = "success"
            res["moment_type"] = clip["moment_type"]
            res["tier"]        = clip["tier"]
            results.append(res)

        if job_id in export_jobs:
            mix = " · ".join(f"{n}x{t}" for t, n in
                             Counter(c["moment_type"] for c in selected).most_common())
            export_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"Editor Set fertig: {len(results)} Clips - {mix}",
                "results": results,
                "completed_at": time.time(),
            })
    except Exception as e:
        if job_id in export_jobs:
            export_jobs[job_id].update({"status": "error", "message": str(e)})
        import traceback
        traceback.print_exc()


@app.route("/api/export/global_best_of", methods=["POST"])
def export_global_best_of():
    """Erstellt eine Montage aus den besten Clips ALLER analysierten Videos."""
    data = request.json
    target_duration = data.get("duration", 30)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    
    # Alle Analyse-Dateien finden
    all_clips = []
    analyzed_videos = {}
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            # Original-Video Pfad finden
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break

            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                analyzed_videos[v_path] = res
                for c in res.get("suggested_clips", []):
                    # Nur kurze Clips für Transition-Montage
                    if c["duration"] <= 3:
                        c["video_path"] = v_path
                        all_clips.append(c)
    
    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404
        
    # Gewichtung anpassen: Bereits verwendete Videos werden bestraft
    for c in all_clips:
        v_name = os.path.basename(c["video_path"])
        usage = global_usage_log.get(v_name, 0)
        # 20% Abzug pro Verwendung, um Rotation zu erzwingen
        penalty = 0.8 ** usage 
        c["weighted_score"] = c["score"] * penalty

    # Sortieren nach gewichtetem Score
    all_clips.sort(key=lambda x: x["weighted_score"], reverse=True)
    
    # Top-Clips auswählen (ohne Überlappung innerhalb des gleichen Videos)
    selected = []
    current_dur = 0
    video_usage = {} # video -> list of intervals
    used_video_names = set()
    
    for c in all_clips:
        if current_dur >= target_duration: break
        
        v = c["video_path"]
        v_name = os.path.basename(v)
        if v not in video_usage: video_usage[v] = []
        
        # Überlappung prüfen
        overlap = False
        for start, end in video_usage[v]:
            if c["start"] < end and c["end"] > start:
                overlap = True
                break
        
        if not overlap:
            selected.append(c)
            video_usage[v].append((c["start"], c["end"]))
            current_dur += c["duration"]
            used_video_names.add(v_name)

    # Money Shot Lock: Besten Clip an ~70 %-Position setzen
    selected = _apply_money_shot_lock(selected)

    # Burst-Pause: Buildup in Wellen restrukturieren (Burst → Pause → Burst → …)
    selected = _apply_burst_pause(selected)

    # Contrast Injection: Atemmoment direkt vor dem Money Shot
    n_inj    = max(1, target_duration // 15)
    selected = _inject_contrast(selected, analyzed_videos, max_injections=n_inj)

    # Re-Hook Loop: ersten Clip kurz am Ende wiederholen → nahtloser Social-Media-Loop
    selected = _apply_rehook_loop(selected)

    # Job starten
    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id = f"global_best_{int(time.time())}"
    output_name = f"GLOBAL_BEST_OF_{target_duration}s_{int(time.time())}"
    
    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Global Best-Of ({len(selected)} Clips) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode, used_video_names),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


def _run_global_montage_task(job_id, clips, output_name, mode, used_video_names=None, dedup=False):
    """Hintergrund-Thread für Global Montage."""
    from analyzer.clip_exporter import export_montage

    # Thread registrieren + Cancel-Event anlegen
    _job_threads[job_id] = threading.get_ident()
    cancel_event = threading.Event()
    _cancel_events[job_id] = cancel_event

    # Erwarteten Output-Pfad vormerken (für Datei-Löschung bei Cancel)
    expected_output = os.path.join(config.BEST_OF_DIR, f"{output_name}.mp4")
    if job_id in export_jobs:
        export_jobs[job_id]["output_path"] = expected_output

    def progress_cb(stage, pct, message):
        if job_id in export_jobs:
            export_jobs[job_id].update({"progress": pct, "message": message})

    try:
        # Duplicate-Frame-Detection: visuell ähnliche Clips herausfiltern.
        # Re-Hook-Clips (is_rehook=True) werden vom Dedup ausgenommen —
        # sie sind bewusste Wiederholungen des ersten Clips für den Loop-Effekt.
        if dedup and clips:
            if job_id in export_jobs:
                export_jobs[job_id].update({
                    "message": f"Duplikate werden geprüft ({len(clips)} Clips)..."
                })
            from analyzer.frame_hasher import filter_duplicates
            rehook_clips  = [c for c in clips if c.get("is_rehook")]
            normal_clips  = [c for c in clips if not c.get("is_rehook")]
            before        = len(normal_clips)
            normal_clips  = filter_duplicates(normal_clips)
            removed       = before - len(normal_clips)
            clips         = normal_clips + rehook_clips   # Re-Hook immer am Ende
            if job_id in export_jobs:
                export_jobs[job_id].update({
                    "message": f"{len(clips)} Clips ({removed} Duplikate entfernt) – Export startet..."
                })

        result = export_montage(
            clips, output_name, mode=mode, fade=True,
            progress_callback=progress_cb,
            cancel_event=cancel_event,
        )
        if cancel_event.is_set():
            return  # already handled by cancel_export()
        if job_id in export_jobs:
            export_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Global Best-Of fertig!",
                "results": [result],
                "completed_at": time.time(),
            })
        if used_video_names:
            for vn in used_video_names:
                global_usage_log[vn] = global_usage_log.get(vn, 0) + 1
            save_usage_log()
    except Exception as e:
        if cancel_event.is_set():
            return  # cancel_export() already set status to cancelled
        if job_id in export_jobs:
            export_jobs[job_id].update({"status": "error", "message": str(e)})
    finally:
        _job_threads.pop(job_id, None)
        _cancel_events.pop(job_id, None)


@app.route("/api/export/highlight_reel", methods=["POST"])
def export_highlight_reel():
    """Erstellt ein Highlight Arc Reel mit Energie-Aufbau."""
    data = request.json
    target_duration = data.get("duration", 15)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    # Alle Analyse-Dateien finden (nur sehr kurze Clips für schnelle Schnitte)
    all_clips = []
    analyzed_videos = {}
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break

            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                analyzed_videos[v_path] = res
                for c in res.get("suggested_clips", []):
                    if c["duration"] <= 3:
                        c["video_path"] = v_path
                        all_clips.append(c)

    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404

    # Pacing Parameter
    if target_duration <= 15:
        climax_dur = 6
    elif target_duration <= 30:
        climax_dur = 10
    else:
        climax_dur = 15
    buildup_dur = target_duration - climax_dur

    # Sortieren nach Score (Energie)
    all_clips.sort(key=lambda x: x["score"], reverse=True)

    video_usage = {}
    def check_overlap(c):
        v = c["video_path"]
        if v not in video_usage: return False
        for start, end in video_usage[v]:
            if c["start"] < end and c["end"] > start:
                return True
        return False

    def add_usage(c):
        v = c["video_path"]
        if v not in video_usage: video_usage[v] = []
        video_usage[v].append((c["start"], c["end"]))

    # 1. Climax-Clips füllen (Die absolut besten Momente)
    climax_clips = []
    current_climax = 0
    remaining_clips = []

    for c in all_clips:
        if current_climax < climax_dur:
            if not check_overlap(c):
                climax_clips.append(c)
                add_usage(c)
                current_climax += c["duration"]
        else:
            remaining_clips.append(c)

    # 2. Buildup-Clips füllen (Die nächstbesten Momente)
    buildup_clips = []
    current_buildup = 0
    for c in remaining_clips:
        if current_buildup < buildup_dur:
            if not check_overlap(c):
                buildup_clips.append(c)
                add_usage(c)
                current_buildup += c["duration"]

    # 3. Buildup aufsteigend sortieren (Spannungsaufbau)
    buildup_clips.sort(key=lambda x: x["score"], reverse=False)

    # 4. Sequenz zusammenfügen
    selected = buildup_clips + climax_clips

    # Money Shot Lock: Besten Clip an ~70 %-Position setzen
    selected = _apply_money_shot_lock(selected)

    # Burst-Pause: Buildup in Wellen restrukturieren (Burst → Pause → Burst → …)
    selected = _apply_burst_pause(selected)

    # Contrast Injection: Atemmoment direkt vor dem Money Shot
    n_inj    = max(1, target_duration // 15)
    selected = _inject_contrast(selected, analyzed_videos, max_injections=n_inj)

    # Re-Hook Loop: ersten Clip kurz am Ende wiederholen → nahtloser Social-Media-Loop
    selected = _apply_rehook_loop(selected)

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id = f"highlight_{target_duration}s_{int(time.time())}"
    output_name = f"HIGHLIGHT_ARC_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Highlight Arc ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


@app.route("/api/export/chronological_reel", methods=["POST"])
def export_chronological_reel():
    """Erstellt eine Montage in chronologischer Reihenfolge der Videos."""
    data = request.json
    target_duration = data.get("duration", 30)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    # ── Clips pro Video sammeln ─────────────────────────────────────────
    # key: v_path → {"creation_time": float, "clips": [...]}
    videos = {}
    for f in os.listdir(config.OUTPUT_DIR):
        if not f.endswith("_analysis.json"):
            continue
        video_name = f.replace("_analysis.json", "")
        v_path = None
        for ext in config.SUPPORTED_EXTENSIONS:
            p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
            if os.path.exists(p):
                v_path = p
                break
        if not v_path:
            continue

        creation_time = _get_video_creation_time(v_path)

        with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
            res = json.load(j)

        clips = [
            {**c, "video_path": v_path, "creation_time": creation_time}
            for c in res.get("suggested_clips", [])
            if c["duration"] <= 3
        ]
        if clips:
            videos[v_path] = {"creation_time": creation_time, "clips": clips}

    if not videos:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404

    # ── Videos chronologisch sortieren ─────────────────────────────────
    sorted_paths = sorted(videos, key=lambda v: videos[v]["creation_time"])

    def best_clip(v_path):
        """Bester Clip (höchster Score) eines Videos."""
        return max(videos[v_path]["clips"], key=lambda c: c["score"])

    # ── Anker: ältestes & neuestes Video ───────────────────────────────
    anchor_start = best_clip(sorted_paths[0])
    anchor_end   = best_clip(sorted_paths[-1])

    # ── Mittelclips: alle anderen Videos, sortiert nach höchstem Tier ──
    # Aus jedem Video nur den besten Clip nehmen, dann nach Score sortieren
    middle_candidates = []
    middle_paths = sorted_paths[1:-1] if len(sorted_paths) > 2 else []

    for v in middle_paths:
        middle_candidates.append(best_clip(v))

    # Highest Tier first (Score absteigend)
    middle_candidates.sort(key=lambda c: c["score"], reverse=True)

    # Budget = Zieldauer minus die beiden Anker
    budget = target_duration - anchor_start["duration"] - anchor_end["duration"]

    selected_middle = []
    used_dur = 0
    for c in middle_candidates:
        if used_dur >= budget:
            break
        selected_middle.append(c)
        used_dur += c["duration"]

    # ── Finale Sequenz: ältestes → Beste Mitte → Neuestes ──────────────
    selected = [anchor_start] + selected_middle + [anchor_end]

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id = f"chrono_{target_duration}s_{int(time.time())}"
    output_name = f"CHRONO_ARC_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": (
            f"Chrono Arc: {len(selected)} Clips "
            f"({len(selected_middle)} Mittelclips nach Tier sortiert)"
        ),
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "started",
        "job_id": job_id,
        "anchor_start": anchor_start["video_path"].split("\\")[-1],
        "anchor_end":   anchor_end["video_path"].split("\\")[-1],
        "middle_clips": len(selected_middle),
    })


@app.route("/api/export/random_reel", methods=["POST"])
def export_random_reel():
    """Erstellt eine Montage aus zufällig ausgewählten Clips."""
    import random
    data = request.json
    target_duration = data.get("duration", 15)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    all_clips = []
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break
            
            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                for c in res.get("suggested_clips", []):
                    # Für Random Reels nutzen wir auch eher kurze Clips (1-5s) für die Dynamik
                    if c["duration"] <= 5:
                        c["video_path"] = v_path
                        all_clips.append(c)

    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404

    # Zufällig durchmischen
    random.shuffle(all_clips)

    selected = []
    current_dur = 0
    video_usage = {}
    
    for c in all_clips:
        if current_dur >= target_duration: break
        
        v = c["video_path"]
        if v not in video_usage: video_usage[v] = []
        
        # Überlappung prüfen
        overlap = False
        for start, end in video_usage[v]:
            if c["start"] < end and c["end"] > start:
                overlap = True
                break
        
        if not overlap:
            selected.append(c)
            video_usage[v].append((c["start"], c["end"]))
            current_dur += c["duration"]

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id = f"random_{target_duration}s_{int(time.time())}"
    output_name = f"RANDOM_ARC_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Zufälliges Reel ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


@app.route("/api/export/strobe_montage", methods=["POST"])
def export_strobe_montage():
    """Erstellt eine sehr schnelle Montage (harte Schnitte synchron auf jeden 2. oder 4. Beat) für High-Energy Strobe-Effekte."""
    import random
    data = request.json
    target_duration = data.get("duration", 15)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    all_clips = []
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break
            
            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                beats = res.get("audio", {}).get("beat_times", [])
                if not beats: continue
                timeline = res.get("timeline", [])
                
                # Finde hoch-energetische Stellen (Lights > 0.2 oder Motion > 0.4)
                valid_times = [t["time"] for t in timeline if t.get("components", {}).get("lights", 0) > 0.2 or t.get("components", {}).get("motion", 0) > 0.4]
                
                # Erstelle 2-Beat oder 4-Beat Clips
                for i in range(len(beats) - 4):
                    start = beats[i]
                    end = beats[i+random.choice([2, 4])]
                    
                    # Prüfe ob dieser Abschnitt in einer energetischen Phase liegt
                    if any(abs(start - vt) < 2.0 for vt in valid_times):
                        all_clips.append({
                            "video_path": v_path,
                            "start": round(start, 3),
                            "end": round(end, 3),
                            "duration": round(end - start, 3),
                            "score": 1.0  # Equal chance for all strobe clips
                        })

    if not all_clips:
        return jsonify({"error": "Keine geeigneten Strobe/Beat-Clips gefunden"}), 404

    random.shuffle(all_clips)

    selected = []
    current_dur = 0
    video_usage = {}
    
    for c in all_clips:
        if current_dur >= target_duration: break
        v = c["video_path"]
        if v not in video_usage: video_usage[v] = []
        overlap = False
        for start, end in video_usage[v]:
            if c["start"] < end and c["end"] > start:
                overlap = True
                break
        if not overlap:
            selected.append(c)
            video_usage[v].append((c["start"], c["end"]))
            current_dur += c["duration"]

    _apply_target_bpm(selected, target_bpm)

    job_id = f"strobe_{target_duration}s_{int(time.time())}"
    output_name = f"STROBE_MONTAGE_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Strobe Montage ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


@app.route("/api/export/crowd_culture", methods=["POST"])
def export_crowd_culture():
    """Erstellt eine Montage, die Crowd-Reaktionen (Jubel, Motion kurz nach Drop) in den Fokus stellt."""
    import random
    data = request.json
    target_duration = data.get("duration", 15)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    all_clips = []
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break
            
            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                for c in res.get("suggested_clips", []):
                    # "CROWD" Definition (0.3s - 7.0s nach einem Bass Drop)
                    c_type = _classify_clip(c, res)
                    if c_type == "CROWD" or c.get("components", {}).get("motion", 0) > 0.6:
                        c_copy = dict(c)
                        c_copy["video_path"] = v_path
                        all_clips.append(c_copy)

    if not all_clips:
        return jsonify({"error": "Keine Crowd-Clips gefunden"}), 404

    # Sortieren nach Score
    all_clips.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    current_dur = 0
    video_usage = {}
    
    for c in all_clips:
        if current_dur >= target_duration: break
        v = c["video_path"]
        if v not in video_usage: video_usage[v] = []
        overlap = False
        for start, end in video_usage[v]:
            if c["start"] < end and c["end"] > start:
                overlap = True
                break
        if not overlap:
            selected.append(c)
            video_usage[v].append((c["start"], c["end"]))
            current_dur += c["duration"]

    _apply_target_bpm(selected, target_bpm)

    job_id = f"crowd_{target_duration}s_{int(time.time())}"
    output_name = f"CROWD_CULTURE_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Crowd & Culture ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


def _snap_to_nearest_beat(time_sec, beat_times):
    """Findet den nächsten Beat-Zeitpunkt in einer sortierten Liste."""
    if not beat_times:
        return time_sec
    import bisect
    idx = bisect.bisect_left(beat_times, time_sec)
    candidates = []
    if idx > 0:
        candidates.append(beat_times[idx - 1])
    if idx < len(beat_times):
        candidates.append(beat_times[idx])
    return min(candidates, key=lambda t: abs(t - time_sec))


def _find_breath_clip(res: dict, v_path: str) -> dict | None:
    """
    Sucht den energieärmsten 1-Bar-Moment im Video — das ideale "Atemmoment"
    vor einem Drop. Scannt die vollständige Timeline (nicht nur suggested_clips,
    die nur Highlight-Regionen abdecken), sucht das tiefste Energietal in den
    ersten 80 % des Videos und gibt einen beat-genauen 4-Beat-Clip zurück.
    """
    timeline   = res.get("timeline", [])
    beat_times = res.get("audio", {}).get("beat_times", [])
    bpm        = float(res.get("audio", {}).get("tempo", 120.0))
    vid_dur    = float(res.get("audio", {}).get("duration", 0) or
                       res.get("video", {}).get("duration", 0))

    if not timeline or vid_dur < 3:
        return None

    beat_interval = 60.0 / max(bpm, 60.0)
    search_end    = vid_dur * 0.80        # Outro ausschließen

    # Energieärmsten Zeitpunkt in den ersten 80 % des Videos finden
    candidates = [t for t in timeline if t["time"] <= search_end]
    if not candidates:
        return None
    valley = min(candidates, key=lambda t: t["score"])

    # 4 Beats ab dem Tal-Punkt, beide Enden auf Beat snappen
    snap_start = _snap_to_nearest_beat(valley["time"], beat_times)
    snap_end   = _snap_to_nearest_beat(snap_start + 4 * beat_interval, beat_times)

    if snap_end > vid_dur or snap_end - snap_start < beat_interval:
        return None

    return {
        "video_path":       v_path,
        "start":            round(snap_start, 3),
        "end":              round(snap_end, 3),
        "duration":         round(snap_end - snap_start, 3),
        "score":            round(valley["score"], 4),
        "preset":           "breath",
        "is_contrast_clip": True,
    }


def _inject_contrast(selected: list, analyzed_videos: dict,
                     threshold_high: float = 0.72,
                     max_injections: int = 2) -> list:
    """
    Injiziert kurze Low-Energy-Clips ("Atemmomente") direkt vor den
    energiereichsten Clips der Auswahl — erzeugt den "Stille-vor-dem-Drop"-Effekt.

    Reihenfolge: Erst dasselbe Video (Klang-Kontinuität), dann anderes Video.
    Kein Atem-Clip wird doppelt eingefügt.
    """
    if not selected or not analyzed_videos:
        return selected

    # Hochenergetische Clips identifizieren (nicht den allerersten Clip)
    high_clips = sorted(
        [(i, c) for i, c in enumerate(selected)
         if c.get("score", 0) >= threshold_high and i > 0],
        key=lambda x: x[1]["score"], reverse=True,
    )[:max_injections]

    if not high_clips:
        return selected

    injections: list[tuple[int, dict]] = []
    used: set[tuple[str, float]] = set()   # (v_path, snap_start)

    for insert_idx, high_clip in high_clips:
        breath = None
        v = high_clip["video_path"]

        # Priorität 1: Atemmoment aus demselben Video
        if v in analyzed_videos:
            cand = _find_breath_clip(analyzed_videos[v], v)
            if cand and (v, cand["start"]) not in used:
                breath = cand

        # Priorität 2: Atemmoment aus einem anderen Video
        if breath is None:
            for vp, res in analyzed_videos.items():
                if vp == v:
                    continue
                cand = _find_breath_clip(res, vp)
                if cand and (vp, cand["start"]) not in used:
                    breath = cand
                    break

        if breath:
            injections.append((insert_idx, breath))
            used.add((breath["video_path"], breath["start"]))

    if not injections:
        return selected

    # Von hinten nach vorne einfügen — Indizes bleiben korrekt
    result = list(selected)
    for idx, breath in sorted(injections, key=lambda x: x[0], reverse=True):
        result.insert(idx, breath)

    return result


def _apply_money_shot_lock(selected: list) -> list:
    """
    Verschiebt den absolut besten Clip (höchster Score) an die ~70%-Position
    der Gesamtdauer — die klassische Spannungskurve:

        Aufbau (0–70 %)  →  KLIMAX / Money Shot  →  Outro (70–100 %)

    Buildup-Clips werden aufsteigend nach Score sortiert (Energie steigt linear).
    Outro-Clips behalten ihre Reihenfolge.
    Muss VOR _inject_contrast aufgerufen werden (noch keine Breath-Clips in der Liste).
    """
    if len(selected) < 3:
        return selected

    # Besten Clip finden
    ms_idx, money_shot = max(enumerate(selected), key=lambda x: x[1].get("score", 0))

    # Alle anderen Clips
    others = [c for i, c in enumerate(selected) if i != ms_idx]

    # Splitpunkt bei ~70 % der kumulierten Dauer
    total  = sum(c.get("duration", 0) for c in others)
    target = total * 0.70
    cum    = 0.0
    split  = len(others)                  # Fallback: Money Shot ganz am Ende
    for i, c in enumerate(others):
        cum += c.get("duration", 0)
        if cum >= target:
            split = i + 1
            break

    # Buildup: aufsteigend nach Score → Energie baut sich sauber auf
    buildup = sorted(others[:split], key=lambda c: c.get("score", 0))
    outro   = others[split:]              # Outro unverändert

    return buildup + [money_shot] + outro


def _apply_burst_pause(selected: list, wave_size: int = 4) -> list:
    """
    Restrukturiert den Buildup-Abschnitt in Burst-Pause-Wellen.
    Muss NACH _apply_money_shot_lock laufen (Money Shot bereits positioniert).

    Prinzip pro Welle (wave_size = 4):
        [burst: 3 aufsteigende Clips] → [pause: 1 niederenergetischer Clip]
    Wellen werden von Welle zu Welle intensiver — Overall-Energie steigt,
    aber mit rhythmischen Einbrüchen statt monotoner Rampe.

    Beispiel (8 Buildup-Clips, scores 0.3–0.75):
        Welle 1: [0.40 → 0.50 → 0.55] → [0.30]   ← erste Burst, dann Luft
        Welle 2: [0.65 → 0.70 → 0.75] → [0.60]   ← zweite Burst, intensiver
        [BREATH] [MONEY SHOT]

    Outro-Clips (nach dem Money Shot) werden nicht verändert.
    """
    if len(selected) < wave_size + 1:
        return selected

    # Money Shot finden (höchster Score, kein Breath-Clip)
    ms_idx, best_score = None, -1.0
    for i, c in enumerate(selected):
        s = c.get("score", 0)
        if not c.get("is_contrast_clip") and s > best_score:
            best_score, ms_idx = s, i

    if ms_idx is None or ms_idx < wave_size:
        return selected

    buildup = selected[:ms_idx]
    tail    = selected[ms_idx:]       # Money Shot + Outro unverändert

    n = len(buildup)
    if n < wave_size:
        return selected

    # Buildup aufsteigend nach Score sortieren (Wellen werden von links nach rechts intensiver)
    clips = sorted(buildup, key=lambda c: c.get("score", 0))

    result = []
    i = 0
    while i < n:
        wave = clips[i : i + wave_size]
        if len(wave) < 2:
            result.extend(wave)
            break
        # Niedrigster Clip der Welle = Pause (wird ans Ende gestellt)
        pause = wave[0]
        burst = wave[1:]          # Rest = Burst, aufsteigend (Intensität steigt innerhalb)
        result.extend(burst)
        result.append(pause)
        i += wave_size

    return result + tail


def _apply_rehook_loop(selected: list) -> list:
    """
    Hängt am Ende eine kurze Wiederholung des ersten Clips an (Re-Hook).

    Auf Instagram/TikTok loopen Reels automatisch — wenn der letzte Frame
    visuell an den ersten anknüpft, wirkt das Reel endlos und professionell produziert.

    Implementierung: erster echter Clip (kein Breath-Clip) wird mit max. 1.5s
    Länge als letzter Clip eingefügt. Markierung `is_rehook=True` schützt
    den Clip vor dem Dedup-Filter im Export-Thread.
    """
    if len(selected) < 2:
        return selected

    first = next((c for c in selected if not c.get("is_contrast_clip")), None)
    if first is None:
        return selected

    rehook_dur = min(first.get("duration", 1.5), 1.5)
    rehook = {
        **first,
        "end":       first["start"] + rehook_dur,
        "duration":  rehook_dur,
        "is_rehook": True,
        "preset":    "rehook",
    }
    return selected + [rehook]


@app.route("/api/export/bpm_locked_reel", methods=["POST"])
def export_bpm_locked_reel():
    """
    BPM-Locked Cut Montage: Alle Schnittpunkte liegen exakt auf dem Beat.
    Clip-Längen werden auf Vielfache von 4 Beats (1 Bar) gerundet.
    Clips aus verschiedenen Videos behalten jeweils ihr eigenes Beat-Grid.
    """
    data = request.json
    target_duration = data.get("duration", 15)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    bar_size = 4  # 4/4-Takt (Standard für Techno)

    all_clips = []
    analyzed_videos = {}
    for f in os.listdir(config.OUTPUT_DIR):
        if not f.endswith("_analysis.json"):
            continue
        video_name = f.replace("_analysis.json", "")
        v_path = None
        for ext in config.SUPPORTED_EXTENSIONS:
            p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
            if os.path.exists(p):
                v_path = p
                break
        if not v_path:
            continue

        with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
            res = json.load(j)
        analyzed_videos[v_path] = res

        bpm = float(res.get("audio", {}).get("tempo", 0))
        beat_times = res.get("audio", {}).get("beat_times", [])
        video_duration = float(res.get("video", {}).get("duration", 0) or
                               res.get("audio", {}).get("duration", 0))

        if not beat_times or bpm < 60:
            continue

        beat_interval = 60.0 / bpm

        for c in res.get("suggested_clips", []):
            if c["duration"] > 8:
                continue

            snapped_start = _snap_to_nearest_beat(c["start"], beat_times)

            # Clip-Länge auf nächstes Bar-Vielfaches runden
            raw_beats = (c["end"] - snapped_start) / beat_interval
            locked_beats = round(raw_beats / bar_size) * bar_size
            locked_beats = max(bar_size, locked_beats)

            raw_end = snapped_start + locked_beats * beat_interval
            snapped_end = _snap_to_nearest_beat(raw_end, beat_times)

            if snapped_end > video_duration:
                snapped_end = video_duration
            if snapped_end - snapped_start < beat_interval:
                continue

            locked_dur = snapped_end - snapped_start
            bars = max(1, round(locked_dur / beat_interval / bar_size))

            all_clips.append({
                **c,
                "video_path": v_path,
                "start":    round(snapped_start, 3),
                "end":      round(snapped_end, 3),
                "duration": round(locked_dur, 3),
                "bpm":      round(bpm, 1),
                "bars":     bars,
            })

    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips mit Beat-Daten gefunden"}), 404

    all_clips.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    current_dur = 0.0
    video_usage = {}

    for c in all_clips:
        if current_dur >= target_duration:
            break
        v = c["video_path"]
        if v not in video_usage:
            video_usage[v] = []
        overlap = any(c["start"] < end and c["end"] > start
                      for start, end in video_usage[v])
        if not overlap:
            selected.append(c)
            video_usage[v].append((c["start"], c["end"]))
            current_dur += c["duration"]

    if not selected:
        return jsonify({"error": "Keine passenden Beat-Aligned Clips gefunden"}), 404

    # Money Shot Lock: Besten Clip an ~70 %-Position setzen
    selected = _apply_money_shot_lock(selected)

    # Burst-Pause: Buildup in Wellen restrukturieren (Burst → Pause → Burst → …)
    selected = _apply_burst_pause(selected)

    # Contrast Injection: Atemmoment direkt vor dem Money Shot
    n_inj    = max(1, target_duration // 15)
    selected = _inject_contrast(selected, analyzed_videos, max_injections=n_inj)

    # Re-Hook Loop: ersten Clip kurz am Ende wiederholen → nahtloser Social-Media-Loop
    selected = _apply_rehook_loop(selected)

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id = f"bpm_locked_{target_duration}s_{int(time.time())}"
    output_name = f"BPM_LOCKED_{target_duration}s_{int(time.time())}"
    total_bars = sum(c.get("bars", 1) for c in selected)

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"BPM-Locked: {len(selected)} Clips / {total_bars} Bars",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "started",
        "job_id": job_id,
        "clips": len(selected),
        "total_bars": total_bars,
        "actual_duration": round(current_dur, 2),
    })


@app.route("/api/export/story_arc", methods=["POST"])
def export_story_arc():
    """
    Erstellt einen strukturierten Story-Arc Reel mit 4 Segmenten:
      1. Hook + Build-Up  – Spannung aufbauen
      2. Drop             – Der Moment der Entladung
      3. Crowd Reaction   – Reaktion kurz nach dem Drop
      4. Outro            – Ausklang / letzter Eindruck
    """
    data = request.json
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    # Alle analysierten Videos laden
    candidates = []
    for f in os.listdir(config.OUTPUT_DIR):
        if not f.endswith("_analysis.json"):
            continue
        video_name = f.replace("_analysis.json", "")
        v_path = None
        for ext in config.SUPPORTED_EXTENSIONS:
            p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
            if os.path.exists(p):
                v_path = p
                break
        if not v_path:
            continue
        try:
            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                candidates.append({"video_path": v_path, "results": json.load(j)})
        except Exception:
            pass

    if not candidates:
        return jsonify({"error": "Keine analysierten Videos gefunden"}), 404

    segments = _build_story_arc(candidates)
    if len(segments) < 2:
        return jsonify({"error": "Zu wenig Material für einen Story Arc"}), 404

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(segments, target_bpm)

    job_id = f"story_arc_{int(time.time())}"
    output_name = f"STORY_ARC_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Story Arc ({len(segments)} Segmente) wird erstellt...",
        "filename": "STORY_ARC",
        "started_at": time.time(),
        "segments": [s.get("segment_label", "?") for s in segments],
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, segments, output_name, mode)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id,
                    "segments": [s.get("segment_label", "?") for s in segments]})


def _build_story_arc(candidates):
    """
    Wählt für jeden der 4 Segmente den besten Clip aus allen analysierten Videos:

    buildup  – Clip überlappt erkannten Buildup ODER liegt in den ersten 40 % des Videos
    drop     – Clip enthält den Bass-Drop mit höchster Intensität
    crowd    – Clip startet 0.3–7s nach dem Drop (Crowd-Reaktion / Kamera-Schnitt)
    outro    – Clip aus den letzten 25 % des Videos
    """
    from collections import defaultdict

    pools = {"buildup": [], "drop": [], "crowd": [], "outro": []}
    all_clips = []   # Fallback-Pool

    for cand in candidates:
        res = cand["results"]
        v_path = cand["video_path"]
        duration = res["audio"].get("duration", 0)
        if duration <= 0:
            continue

        audio      = res["audio"]
        bass_drops = audio.get("bass_drops", [])
        buildups   = audio.get("buildups",   [])

        best_drop = max(bass_drops, key=lambda d: d["intensity"]) if bass_drops else None
        drop_time = best_drop["time"] if best_drop else None

        for clip in res.get("suggested_clips", []):
            c = {**clip, "video_path": v_path}
            s, e = c["start"], c["end"]
            mid = (s + e) / 2
            rel = mid / duration   # 0 = Anfang, 1 = Ende

            all_clips.append(c)

            # ── Hook + Build-Up ──────────────────────────────────────────
            in_buildup = any(s < bu["end"] and e > bu["start"] for bu in buildups)
            before_drop = (drop_time is None) or (e <= drop_time + 1.0)

            if in_buildup:
                pools["buildup"].append({
                    **c,
                    "seg_score": c["score"] * 1.5,
                    "segment_label": "BUILDUP",
                })
            elif rel < 0.40 and before_drop:
                pools["buildup"].append({
                    **c,
                    "seg_score": c["score"],
                    "segment_label": "HOOK",
                })

            # ── Drop ─────────────────────────────────────────────────────
            if drop_time is not None and s <= drop_time <= e:
                pools["drop"].append({
                    **c,
                    "seg_score": c["score"] * (1.0 + best_drop["intensity"]),
                    "segment_label": "DROP",
                })

            # ── Crowd Reaction ───────────────────────────────────────────
            if drop_time is not None:
                delay = s - drop_time
                if 0.3 <= delay <= 7.0:
                    # je kürzer das Delay, desto unmittelbarer die Reaktion
                    pools["crowd"].append({
                        **c,
                        "seg_score": c["score"] * (2.0 / (delay + 0.5)),
                        "segment_label": "CROWD",
                    })

            # ── Outro ────────────────────────────────────────────────────
            if rel > 0.75:
                pools["outro"].append({
                    **c,
                    "seg_score": c["score"],
                    "segment_label": "OUTRO",
                })

    # Sortieren
    for k in pools:
        pools[k].sort(key=lambda x: x.get("seg_score", 0), reverse=True)
    all_clips.sort(key=lambda x: x["score"], reverse=True)

    # Besten Clip pro Segment wählen – mit Ziel-Dauer-Präferenz
    def pick(pool, fallback, target_dur):
        source = pool if pool else fallback
        if not source:
            return None
        # Unter den Top-15 denjenigen mit passender Dauer bevorzugen
        top = source[:15]
        close = [c for c in top if abs(c["duration"] - target_dur) <= target_dur * 0.7]
        return close[0] if close else top[0]

    buildup = pick(pools["buildup"], all_clips,  5.0)
    drop    = pick(pools["drop"],    all_clips,  2.0)
    crowd   = pick(pools["crowd"],   all_clips,  3.0)
    outro   = pick(pools["outro"],   all_clips,  5.0)

    # Segment-Labels für Job-Status setzen
    for seg, label in [(buildup,"HOOK+BUILDUP"), (drop,"DROP"),
                       (crowd,"CROWD REACTION"), (outro,"OUTRO")]:
        if seg:
            seg["segment_label"] = label

    return [s for s in [buildup, drop, crowd, outro] if s]


@app.route("/api/export/adaptive_reel", methods=["POST"])
def export_adaptive_reel():
    """
    Adaptive-Length Reel: Clip-Längen passen sich an den Energie-Score an.
      score ≥ 0.85  →  2 Beats  (~0.9s bei 140 BPM)   — Climax-Schnitte
      score ≥ 0.70  →  4 Beats  (~1.7s)                — High Energy
      score ≥ 0.50  →  8 Beats  (~3.4s)                — Medium
      score ≥ 0.30  → 16 Beats  (~6.9s)                — Low Energy
      score  < 0.30 → 24 Beats  (~10s)                 — Ruhiger Einstieg
    Montage-Reihenfolge: aufsteigend nach Score → natürlicher Calm-to-Climax-Arc.
    """
    data = request.json
    target_duration = data.get("duration", 30)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    bar_size = 4  # 4/4-Takt

    all_clips = []
    analyzed_videos = {}
    for f in os.listdir(config.OUTPUT_DIR):
        if not f.endswith("_analysis.json"):
            continue
        video_name = f.replace("_analysis.json", "")
        v_path = None
        for ext in config.SUPPORTED_EXTENSIONS:
            p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
            if os.path.exists(p):
                v_path = p
                break
        if not v_path:
            continue

        with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
            res = json.load(j)
        analyzed_videos[v_path] = res

        bpm        = float(res.get("audio", {}).get("tempo", 120.0))
        beat_times = res.get("audio", {}).get("beat_times", [])
        vid_dur    = float(
            res.get("video", {}).get("duration", 0) or
            res.get("audio", {}).get("duration", 0)
        )
        beat_interval = 60.0 / max(bpm, 60.0)

        for c in res.get("suggested_clips", []):
            score = c.get("score", 0.0)

            # Score → Beat-Anzahl (inverse: hoher Score = kurzer Clip)
            if score >= 0.85:   beats = bar_size // 2
            elif score >= 0.70: beats = bar_size
            elif score >= 0.50: beats = bar_size * 2
            elif score >= 0.30: beats = bar_size * 4
            else:               beats = bar_size * 6

            snap_start = _snap_to_nearest_beat(c["start"], beat_times) if beat_times else c["start"]
            raw_end    = snap_start + beats * beat_interval
            snap_end   = _snap_to_nearest_beat(raw_end, beat_times) if beat_times else raw_end

            if snap_end > vid_dur:
                snap_end = vid_dur
            if snap_end - snap_start < beat_interval:
                continue

            all_clips.append({
                **c,
                "video_path": v_path,
                "start":    round(snap_start, 3),
                "end":      round(snap_end, 3),
                "duration": round(snap_end - snap_start, 3),
                "bpm":      round(bpm, 1),
                "beats":    beats,
            })

    if not all_clips:
        return jsonify({"error": "Keine analysierten Clips gefunden"}), 404

    # Aufsteigend nach Score → Calm zuerst, Climax am Ende
    all_clips.sort(key=lambda x: x["score"])

    selected  = []
    curr_dur  = 0.0
    vid_usage = {}

    for c in all_clips:
        if curr_dur >= target_duration:
            break
        v = c["video_path"]
        if v not in vid_usage:
            vid_usage[v] = []
        if not any(c["start"] < e and c["end"] > s for s, e in vid_usage[v]):
            selected.append(c)
            vid_usage[v].append((c["start"], c["end"]))
            curr_dur += c["duration"]

    if not selected:
        return jsonify({"error": "Keine Clips für Adaptive Arc gefunden"}), 404

    # Money Shot Lock: Besten Clip an ~70 %-Position setzen
    selected = _apply_money_shot_lock(selected)

    # Burst-Pause: Buildup in Wellen restrukturieren (Burst → Pause → Burst → …)
    selected = _apply_burst_pause(selected)

    # Contrast Injection: Atemmoment direkt vor dem Money Shot
    n_inj    = max(1, target_duration // 15)
    selected = _inject_contrast(selected, analyzed_videos, max_injections=n_inj)

    # Re-Hook Loop: ersten Clip kurz am Ende wiederholen → nahtloser Social-Media-Loop
    selected = _apply_rehook_loop(selected)

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    _apply_target_bpm(selected, target_bpm)

    job_id      = f"adaptive_{target_duration}s_{int(time.time())}"
    output_name = f"ADAPTIVE_ARC_{target_duration}s_{int(time.time())}"

    # Beat-Statistik für Job-Message
    dur_map = {c["beats"]: c["duration"] for c in selected}
    min_b   = min(c["beats"] for c in selected)
    max_b   = max(c["beats"] for c in selected)

    export_jobs[job_id] = {
        "status":     "running",
        "progress":   0,
        "message":    f"Adaptive Arc: {len(selected)} Clips · {min_b}–{max_b} Beats · ~{curr_dur:.0f}s",
        "filename":   "ALL_VIDEOS",
        "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, selected, output_name, mode),
        kwargs={"dedup": True},
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "status":          "started",
        "job_id":          job_id,
        "clips":           len(selected),
        "actual_duration": round(curr_dur, 2),
        "beat_range":      [min_b, max_b],
    })


@app.route("/api/export/seamless_loop", methods=["POST"])
def export_seamless_loop_endpoint():
    """Erstellt einen Seamless Loop aus dem besten 10s Clip über alle Videos hinweg."""
    data = request.json
    target_duration = data.get("duration", 10)
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    best_clip = None
    best_score = -1
    best_fallback = None
    best_fallback_score = -1

    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            v_path = None
            for ext in config.SUPPORTED_EXTENSIONS:
                p = os.path.join(config.VIDEO_SOURCE_DIR, video_name + ext)
                if os.path.exists(p):
                    v_path = p
                    break

            if not v_path: continue

            with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                res = json.load(j)
                for c in res.get("suggested_clips", []):
                    # Proportionale Toleranz (50% der Zieldauer, mind. 2s Puffer)
                    # Verhindert leere Ergebnisse wenn Presets nicht exakt zur Zieldauer passen
                    if abs(c["duration"] - target_duration) <= max(target_duration * 0.5, 2.0):
                        if c["score"] > best_score:
                            best_score = c["score"]
                            best_clip = c.copy()
                            best_clip["video_path"] = v_path
                    # Fallback: bester Clip mit Mindestlänge für den Loop-Algorithmus (>2s)
                    if c["duration"] > 2.0 and c["score"] > best_fallback_score:
                        best_fallback_score = c["score"]
                        best_fallback = c.copy()
                        best_fallback["video_path"] = v_path

    # Fallback verwenden wenn kein Clip im Toleranz-Fenster liegt
    if not best_clip:
        if not best_fallback:
            return jsonify({"error": "Kein passender Clip gefunden"}), 404
        best_clip = best_fallback

    # Tempo-Stretch auf Ziel-BPM (nur wenn Regler aktiv)
    loop_speed = _single_video_speed(best_clip["video_path"], target_bpm)

    job_id = f"loop_{target_duration}s_{int(time.time())}"
    output_name = f"SEAMLESS_LOOP_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": f"Seamless Loop ({best_clip['duration']}s) wird erstellt...",
        "filename": "ALL_VIDEOS",
        "started_at": time.time(),
    }

    def run_loop_task():
        from analyzer.clip_exporter import export_seamless_loop
        def progress_cb(stage, pct, message):
            if job_id in export_jobs:
                export_jobs[job_id].update({"progress": pct, "message": message})
        try:
            result = export_seamless_loop(
                best_clip["video_path"], best_clip["start"], best_clip["end"],
                output_name, mode=mode, progress_callback=progress_cb,
                speed=loop_speed
            )
            if job_id in export_jobs:
                export_jobs[job_id].update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Seamless Loop fertig!",
                    "results": [result],
                    "completed_at": time.time(),
                })
        except Exception as e:
            if job_id in export_jobs:
                export_jobs[job_id].update({"status": "error", "message": str(e)})

    thread = threading.Thread(target=run_loop_task)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})

@app.route("/api/export/single_loop", methods=["POST"])
def export_single_loop_endpoint():
    """Exportiert einen einzelnen Clip als Seamless Loop (aus dem Studio)."""
    from analyzer.clip_exporter import export_seamless_loop
    
    data = request.json
    filename = data.get("filename")
    start = data.get("start")
    end = data.get("end")
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)

    if not filename or start is None or end is None:
        return jsonify({"error": "filename, start und end sind erforderlich"}), 400

    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    base = os.path.splitext(filename)[0]
    clip_name = f"{base}_LOOP_{mode}_{int(start)}s-{int(end)}s"
    speed = _single_video_speed(filepath, target_bpm)

    try:
        result = export_seamless_loop(filepath, start, end, clip_name, mode=mode, output_dir=config.SINGLE_DOWNLOADS_DIR, speed=speed)
        return jsonify({"status": "success", "export": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export/status/<job_id>")
def get_export_status(job_id):
    """Gibt den Status eines Export-Jobs zurück."""
    if job_id in export_jobs:
        return jsonify(export_jobs[job_id])
    return jsonify({"status": "not_found"}), 404


@app.route("/api/export/cancel/<job_id>", methods=["POST"])
def cancel_export(job_id):
    """
    Bricht einen laufenden Export sofort ab:
    1. Setzt das Cancel-Event → Export-Loop stoppt vor dem nächsten Clip
    2. Killt den aktiven FFmpeg-Prozess für diesen Thread
    3. Löscht die unfertige Output-Datei
    """
    from analyzer.clip_exporter import _active_procs, _active_procs_lock

    # 1. Cancel-Event setzen
    evt = _cancel_events.get(job_id)
    if evt:
        evt.set()

    # 2. Laufenden FFmpeg-Prozess killen
    tid = _job_threads.get(job_id)
    if tid:
        with _active_procs_lock:
            proc = _active_procs.get(tid)
            if proc and proc.poll() is None:   # Prozess noch aktiv?
                proc.kill()

    # 3. Unfertige Output-Datei löschen
    job = export_jobs.get(job_id, {})
    output_path = job.get("output_path")
    deleted_files = []

    if output_path and os.path.exists(output_path):
        try:
            os.remove(output_path)
            deleted_files.append(os.path.basename(output_path))
        except Exception:
            pass

    # Temp-Verzeichnis partieller Dateien bereinigen
    try:
        for f in os.listdir(config.TEMP_DIR):
            if f.endswith(".mp4") or f.endswith(".txt"):
                p = os.path.join(config.TEMP_DIR, f)
                try:
                    os.remove(p)
                    deleted_files.append(f)
                except Exception:
                    pass
    except Exception:
        pass

    # 4. Job-Status aktualisieren
    if job_id in export_jobs:
        export_jobs[job_id].update({
            "status": "cancelled",
            "progress": 0,
            "message": "Export abgebrochen.",
            "deleted_files": deleted_files,
        })

    # Registrierungen aufräumen
    _job_threads.pop(job_id, None)
    _cancel_events.pop(job_id, None)

    return jsonify({
        "status": "cancelled",
        "job_id": job_id,
        "file_deleted": bool(deleted_files),
        "deleted_files": deleted_files,
    })


@app.route("/api/export/single", methods=["POST"])
def export_single_clip():
    """Exportiert einen einzelnen Clip."""
    from analyzer.clip_exporter import export_clip

    data = request.json
    filename = data.get("filename")
    start = data.get("start")
    end = data.get("end")
    mode = data.get("mode", "reel")
    target_bpm = _parse_target_bpm(data)
    fade = data.get("fade", True)

    if not filename or start is None or end is None:
        return jsonify({"error": "filename, start und end sind erforderlich"}), 400

    filepath = os.path.join(config.VIDEO_SOURCE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Video nicht gefunden"}), 404

    base = os.path.splitext(filename)[0]
    clip_name = f"{base}_{mode}_{int(start)}s-{int(end)}s"
    speed = _single_video_speed(filepath, target_bpm)

    try:
        result = export_clip(filepath, start, end, clip_name, mode=mode, fade=fade, speed=speed)
        return jsonify({"status": "success", "export": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/exports")
def list_exports():
    """Listet alle exportierten Clips."""
    exports = {"single": [], "best_of": [], "sets": []}

    # Helper function to recursively find files and keep relative path
    def add_files_from_dir(folder, key):
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for f in files:
                    filepath = os.path.join(root, f)
                    if os.path.isfile(filepath):
                        # Create relative path from OUTPUT_DIR
                        rel_path = os.path.relpath(filepath, config.OUTPUT_DIR)
                        exports[key].append({
                            "filename": os.path.basename(f),
                            "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 1),
                            "path": rel_path.replace('\\', '/'),
                        })

    add_files_from_dir(config.SINGLE_DOWNLOADS_DIR, "single")
    add_files_from_dir(config.BEST_OF_DIR, "best_of")
    add_files_from_dir(config.EDITOR_SETS_DIR, "sets")

    return jsonify(exports)

@app.route("/api/export/delete", methods=["POST"])
def delete_export():
    """Löscht eine exportierte Datei."""
    data = request.json
    filepath = data.get("path")

    if not filepath:
        return jsonify({"error": "path ist erforderlich"}), 400

    # Pfad validieren (Sicherheit: nur innerhalb von output)
    full_path = os.path.normpath(os.path.join(config.OUTPUT_DIR, filepath))
    if not full_path.startswith(os.path.normpath(config.OUTPUT_DIR)):
        return jsonify({"error": "Ungültiger Pfad"}), 403

    if os.path.exists(full_path) and os.path.isfile(full_path):
        try:
            os.remove(full_path)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Datei nicht gefunden"}), 404

@app.route("/api/exports/download_all")
def download_all_exports():
    """Erstellt ein ZIP-Archiv mit allen exportierten Clips."""
    zip_path = os.path.join(config.TEMP_DIR, "all_exports.zip")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for folder in [config.SINGLE_DOWNLOADS_DIR, config.BEST_OF_DIR, config.EDITOR_SETS_DIR]:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for f in files:
                        filepath = os.path.join(root, f)
                        if os.path.isfile(filepath):
                            arcname = os.path.relpath(filepath, config.OUTPUT_DIR)
                            zipf.write(filepath, arcname)

    return send_file(zip_path, as_attachment=True, download_name="ReelVids_Exports.zip")


# ========================
# CONFIG
# ========================

@app.route("/api/reset_usage_log", methods=["POST"])
def reset_usage_log():
    """Setzt den Rotations-Algorithmus zurück (alle Videos gleichwertig)."""
    global global_usage_log
    global_usage_log = {}
    save_usage_log()
    return jsonify({"status": "success"})


@app.route("/api/config")
def get_config():
    """Gibt die aktuelle Konfiguration zurück."""
    return jsonify({
        "reel_presets": config.REEL_PRESETS,
        "reel_resolution": f"{config.REEL_WIDTH}x{config.REEL_HEIGHT}",
        "highlight_threshold": config.HIGHLIGHT_SCORE_THRESHOLD,
        "weights": {
            "audio_energy": config.WEIGHT_AUDIO_ENERGY,
            "bass_drops": config.WEIGHT_BASS_DROPS,
            "visual_motion": config.WEIGHT_VISUAL_MOTION,
            "scene_changes": config.WEIGHT_SCENE_CHANGES,
            "light_effects": config.WEIGHT_LIGHT_EFFECTS,
        },
    })


def _cleanup_old_jobs(max_age_sec=3600):
    """Entfernt abgeschlossene/fehlerhafte Jobs die älter als max_age_sec sind."""
    cutoff = time.time() - max_age_sec
    for jobs_dict in (analysis_jobs, export_jobs):
        to_delete = [
            k for k, v in jobs_dict.items()
            if v.get("status") in ("completed", "error")
            and v.get("completed_at", v.get("started_at", 0)) < cutoff
        ]
        for k in to_delete:
            del jobs_dict[k]


import hashlib
import subprocess
from datetime import datetime

_ingested_hashes = {}

def _ingest_file(filepath):
    """
    Phase 5 Ingestion:
    1. Duplikat-Erkennung via Dateigröße + 1MB Hash. Löscht Duplikate sofort.
    2. Smart Renaming: Liest creation_time (ffprobe/os.stat) und benennt um nach UNREEL_YYYYMMDD_HHMMSS.mp4.
    """
    filename = os.path.basename(filepath)
    if filename.startswith("._"):
        return None
        
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'rb') as f:
            chunk = f.read(1024 * 1024)
        f_hash = f"{size}_{hashlib.md5(chunk).hexdigest()}"
    except Exception:
        return None
        
    # Duplikat-Check
    if f_hash in _ingested_hashes:
        existing = _ingested_hashes[f_hash]
        if existing != filepath and os.path.exists(existing):
            print(f"// INGESTION: Deleting duplicate {filename} (same as {os.path.basename(existing)})")
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"// INGESTION ERROR: Could not delete {filename}: {e}")
            return None
            
    _ingested_hashes[f_hash] = filepath
    
    # Renaming
    if not filename.startswith("UNREEL_"):
        ctime_str = ""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-select_streams", "v:0",
                "-show_entries", "format_tags=creation_time",
                "-of", "default=noprint_wrappers=1:nokey=1", filepath
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
            if out:
                dt = datetime.strptime(out[:19], "%Y-%m-%dT%H:%M:%S")
                ctime_str = dt.strftime("%Y%m%d_%H%M%S")
        except Exception:
            pass
            
        if not ctime_str:
            try:
                mtime = os.path.getmtime(filepath)
                dt = datetime.fromtimestamp(mtime)
                ctime_str = dt.strftime("%Y%m%d_%H%M%S")
            except Exception:
                ctime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                
        ext = os.path.splitext(filename)[1].lower()
        new_name = f"UNREEL_{ctime_str}{ext}"
        new_filepath = os.path.join(os.path.dirname(filepath), new_name)
        
        counter = 1
        while os.path.exists(new_filepath) and new_filepath != filepath:
            new_name = f"UNREEL_{ctime_str}_{counter}{ext}"
            new_filepath = os.path.join(os.path.dirname(filepath), new_name)
            counter += 1
            
        if new_filepath != filepath:
            print(f"// INGESTION: Renaming {filename} -> {new_name}")
            try:
                os.rename(filepath, new_filepath)
                _ingested_hashes[f_hash] = new_filepath
                return new_filepath
            except Exception as e:
                print(f"// INGESTION ERROR: Could not rename {filename}: {e}")
                return filepath
                
    return filepath


def run_watchdog():
    """Hintergrund-Thread, der alle 30 Sekunden nach neuen Videos sucht."""
    while True:
        try:
            for f in os.listdir(config.VIDEO_SOURCE_DIR):
                ext = os.path.splitext(f)[1].lower()
                if ext in {e.lower() for e in config.SUPPORTED_EXTENSIONS}:
                    if f.startswith("._"): continue

                    filepath = os.path.join(config.VIDEO_SOURCE_DIR, f)
                    
                    # Phase 5: Ingestion (Deduplication & Renaming)
                    new_filepath = _ingest_file(filepath)
                    if not new_filepath:
                        continue # File was deleted or error
                        
                    new_f = os.path.basename(new_filepath)

                    results_path = os.path.join(
                        config.OUTPUT_DIR,
                        f"{os.path.splitext(new_f)[0]}_analysis.json"
                    )

                    # Wenn weder Analyse existiert noch ein Job läuft -> Starten
                    if not os.path.exists(results_path) and new_f not in analysis_jobs:
                        analysis_jobs[new_f] = {
                            "status": "running", "progress": 0, "stage": "queued",
                            "message": "Auto-Pilot...", "started_at": time.time(),
                        }
                        thread = threading.Thread(target=_run_analysis, args=(new_f, new_filepath))
                        thread.daemon = True
                        thread.start()
                        print(f"// WATCHDOG: ANALYZING {new_f}")

            # Abgeschlossene Jobs bereinigen um Memory Leak zu verhindern
            _cleanup_old_jobs()

        except Exception as e:
            print(f"// WATCHDOG ERROR: {e}")

        time.sleep(30)


def load_existing_results():
    """Lädt bereits vorhandene Analyse-Ergebnisse in den Cache."""
    if not os.path.exists(config.OUTPUT_DIR): return
    
    count = 0
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            video_name = f.replace("_analysis.json", "")
            # Suche das passende Video-File
            for ext in config.SUPPORTED_EXTENSIONS:
                full_name = video_name + ext
                if os.path.exists(os.path.join(config.VIDEO_SOURCE_DIR, full_name)):
                    try:
                        with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                            analysis_cache[full_name] = json.load(j)
                            count += 1
                        break
                    except: pass
    print(f"// BOOT: LOADED {count} EXISTING ANALYSES INTO CACHE.")


# ========================
# WATERMARK DETECTION & REMOVAL
# ========================

@app.route("/api/watermark/batch_clean", methods=["POST"])
def watermark_batch_clean():
    import uuid as _uuid
    import subprocess as _sp
    from analyzer.watermark_detector import detect_capcut_watermark

    scan_dirs = [
        os.path.join(config.OUTPUT_DIR, "single_downloads"),
        os.path.join(config.OUTPUT_DIR, "best_of"),
        os.path.join(config.OUTPUT_DIR, "editor_sets"),
    ]
    job_id = str(_uuid.uuid4())[:8]
    export_jobs[job_id] = {"status": "running", "progress": 0, "message": "COLLECTING FILES..."}

    def _run():
        files = []
        for d in scan_dirs:
            if os.path.exists(d):
                for f in sorted(os.listdir(d)):
                    if f.lower().endswith(".mp4") and not f.endswith("_nowm.mp4"):
                        files.append(os.path.join(d, f))

        total = len(files)
        if total == 0:
            export_jobs[job_id] = {"status": "completed", "progress": 100,
                                   "message": "NO EXPORTS FOUND",
                                   "results": {"cleaned": 0, "total": 0}}
            return

        cleaned = 0
        errors  = 0
        for i, fpath in enumerate(files):
            fname = os.path.basename(fpath)
            export_jobs[job_id]["progress"] = int(i / total * 95)
            export_jobs[job_id]["message"]  = f"SCANNING {i+1}/{total}: {fname}"
            temp_path = fpath + ".wm_tmp.mp4"
            try:
                result = detect_capcut_watermark(fpath)
                if not result.get("detected"):
                    continue
                trim_start = result["trim_start"]
                trim_end   = result["trim_end"]
                new_dur    = max(0.1, result["duration"] - trim_start - trim_end)
                cmd = ["ffmpeg", "-y", "-ss", str(trim_start), "-i", fpath,
                       "-t", str(new_dur), "-c", "copy", temp_path]
                _sp.run(cmd, check=True, capture_output=True)
                os.replace(temp_path, fpath)
                cleaned += 1
            except Exception:
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                errors += 1

        export_jobs[job_id] = {
            "status": "completed", "progress": 100,
            "message": f"DONE — {cleaned}/{total} CLEANED",
            "results": {"cleaned": cleaned, "errors": errors, "total": total},
        }

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    _job_threads[job_id] = t.ident
    return jsonify({"job_id": job_id})


@app.route("/api/watermark/detect/<path:filename>", methods=["POST"])
def watermark_detect(filename):
    import uuid as _uuid
    safe = _sanitize_video_filename(filename)
    if not safe:
        return jsonify({"error": "Invalid filename"}), 400
    video_path = os.path.join(config.VIDEO_SOURCE_DIR, safe)
    if not os.path.exists(video_path):
        return jsonify({"error": "Video not found"}), 404
    from analyzer.watermark_detector import detect_capcut_watermark
    result = detect_capcut_watermark(video_path)
    return jsonify(result)


@app.route("/api/watermark/remove/<path:filename>", methods=["POST"])
def watermark_remove(filename):
    import uuid as _uuid
    import subprocess as _sp
    safe = _sanitize_video_filename(filename)
    if not safe:
        return jsonify({"error": "Invalid filename"}), 400
    data       = request.json or {}
    trim_start = float(data.get("trim_start", 0))
    trim_end   = float(data.get("trim_end",   0))
    duration   = float(data.get("duration",   0))
    if trim_start <= 0 and trim_end <= 0:
        return jsonify({"error": "Nothing to trim"}), 400
    video_path = os.path.join(config.VIDEO_SOURCE_DIR, safe)
    if not os.path.exists(video_path):
        return jsonify({"error": "Video not found"}), 404
    base, ext = os.path.splitext(safe)
    out_name  = f"{base}_nowm{ext}"
    out_path  = os.path.join(config.OUTPUT_DIR, "single_downloads", out_name)
    job_id = str(_uuid.uuid4())[:8]
    export_jobs[job_id] = {"status": "running", "progress": 0, "message": "TRIMMING..."}

    def _run():
        try:
            new_dur = max(0.1, duration - trim_start - trim_end)
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(trim_start),
                "-i", video_path,
                "-t", str(new_dur),
                "-c", "copy",
                out_path,
            ]
            _sp.run(cmd, check=True, capture_output=True)
            export_jobs[job_id] = {
                "status": "success", "progress": 100, "message": "DONE",
                "results": {"filename": out_name, "output_path": out_path},
            }
        except Exception as e:
            export_jobs[job_id] = {"status": "error", "error": str(e)}

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    _job_threads[job_id] = t.ident
    return jsonify({"job_id": job_id})


# ========================
# NEUE DJ PRESETS (PHASE 4)
# ========================

@app.route("/api/export/drop_architecture", methods=["POST"])
def export_drop_architecture():
    data = request.json or {}
    target_duration = float(data.get("duration", 15.0))
    mode = data.get("mode", "reel")
    
    best_drop = None
    best_video = None
    best_tracking = []
    
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            v_path = _find_video_for_json(f)
            if not v_path: continue
            
            try:
                with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                    res = json.load(j)
                    audio_data = res.get("audio", res)
                    drops = audio_data.get("bass_drops", [])
                    if drops:
                        max_drop = max(drops, key=lambda x: x["intensity"])
                        if best_drop is None or max_drop["intensity"] > best_drop["intensity"]:
                            best_drop = max_drop
                            best_video = v_path
                            best_tracking = res.get("tracking_data", [])
            except Exception as e:
                print(f"Fehler: {e}")

    if not best_drop or not best_video:
        return jsonify({"error": "Keine Bass Drops gefunden"}), 404

    drop_time = best_drop["time"]
    start = max(0.0, drop_time - 3.0)
    end = start + target_duration
    
    crop_x = 0.5
    if best_tracking:
        xs = [pt["x_center"] for pt in best_tracking if start <= pt["time"] <= end]
        if xs: crop_x = sum(xs) / len(xs)

    clip = {
        "video_path": best_video,
        "start": round(start, 3),
        "end": round(end, 3),
        "duration": round(end - start, 3),
        "crop_x": round(crop_x, 4)
    }

    job_id = f"drop_arch_{target_duration}s_{int(time.time())}"
    output_name = f"DROP_ARCHITECTURE_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running", "progress": 0,
        "message": f"Drop Architecture ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS", "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, [clip], output_name, mode),
        kwargs={"dedup": False},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


@app.route("/api/export/transition_mastery", methods=["POST"])
def export_transition_mastery():
    data = request.json or {}
    target_duration = float(data.get("duration", 30.0))
    mode = data.get("mode", "reel")
    
    best_clip = None
    best_video = None
    best_tracking = []
    
    for f in os.listdir(config.OUTPUT_DIR):
        if f.endswith("_analysis.json"):
            v_path = _find_video_for_json(f)
            if not v_path: continue
            
            try:
                with open(os.path.join(config.OUTPUT_DIR, f), "r", encoding="utf-8") as j:
                    res = json.load(j)
                    timeline = res.get("timeline", [])
                    vid_dur = res.get("duration", 0)
                    if vid_dur == 0:
                        vid_dur = res.get("video", {}).get("duration", 0)
                        
                    if not timeline or vid_dur < target_duration:
                        continue
                        
                    time_steps = [t["time"] for t in timeline]
                    motion_scores = [t.get("components", {}).get("motion", 0) for t in timeline]
                    
                    if not motion_scores: continue
                    
                    min_motion = float("inf")
                    best_start_for_vid = 0
                    
                    window_size = int(target_duration / 0.5)
                    if window_size == 0 or len(motion_scores) < window_size:
                        continue
                        
                    for i in range(len(motion_scores) - window_size):
                        window = motion_scores[i:i+window_size]
                        avg_m = sum(window) / len(window)
                        # Suche nach minimaler Bewegung, aber nicht komplett 0 (Standbild/Schwarz)
                        if 0.05 < avg_m < min_motion:
                            min_motion = avg_m
                            best_start_for_vid = time_steps[i]
                            
                    if best_start_for_vid > 0:
                        if best_clip is None or min_motion < best_clip["score"]:
                            best_clip = {
                                "start": best_start_for_vid,
                                "end": best_start_for_vid + target_duration,
                                "score": min_motion
                            }
                            best_video = v_path
                            best_tracking = res.get("tracking_data", [])
            except Exception as e:
                print(f"Fehler: {e}")

    if not best_clip or not best_video:
        return jsonify({"error": "Keine Transition-Segmente gefunden"}), 404

    start = best_clip["start"]
    end = best_clip["end"]
    
    crop_x = 0.5
    if best_tracking:
        xs = [pt["x_center"] for pt in best_tracking if start <= pt["time"] <= end]
        if xs: crop_x = sum(xs) / len(xs)

    clip = {
        "video_path": best_video,
        "start": round(start, 3),
        "end": round(end, 3),
        "duration": round(end - start, 3),
        "crop_x": round(crop_x, 4)
    }

    job_id = f"transition_{target_duration}s_{int(time.time())}"
    output_name = f"TRANSITION_MASTERY_{target_duration}s_{int(time.time())}"

    export_jobs[job_id] = {
        "status": "running", "progress": 0,
        "message": f"Transition Mastery ({target_duration}s) wird erstellt...",
        "filename": "ALL_VIDEOS", "started_at": time.time(),
    }

    thread = threading.Thread(
        target=_run_global_montage_task,
        args=(job_id, [clip], output_name, mode),
        kwargs={"dedup": False},
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})

# ========================
# MAIN
# ========================

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Vorhandene Ergebnisse laden
    load_existing_results()

    print("\n" + "=" * 60)
    print("  UNREEL - DJ PRODUCTION UTILITY v2.0")
    print("=" * 60)
    print(f"  SOURCE_DIR: {config.VIDEO_SOURCE_DIR}")
    print(f"  OUTPUT_DIR: {config.OUTPUT_DIR}")
    print(f"  DASHBOARD:  http://localhost:5000")
    print("=" * 60 + "\n")

    # Watchdog im Hintergrund starten
    watchdog_thread = threading.Thread(target=run_watchdog)
    watchdog_thread.daemon = True
    watchdog_thread.start()

    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
