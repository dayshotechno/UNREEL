# UNREEL V3 – Modul- & Funktionsreferenz

Vollständige Referenz aller Skripte und ihrer öffentlichen Funktionen, gruppiert nach
Pipeline-Phase und Verwendungszweck. Ergänzt die High-Level-Übersicht in der
[README.md](README.md).

**Pipeline-Fluss:**

```
 0 Ingest/Setup → 1 Sync → 2 Vision → 3 Regie → 4 Copy → 5 Export
 (Dedup/LUTs)     (Audio)   (Tags)     (KI-Plan)  (Text)   (Schnitt + Reel)
```

> **Hinweis zur Struktur:** Die V3-Kernmodule liegen im **Repo-Root**
> (`ingest.py`, `audio_sync.py`, `kick_snare_detector.py`, `lut_generator.py`,
> `regie_engine.py`, `config.py`). Die `analyzer/`-Module sind ergänzende
> Analyse-/Export-Werkzeuge (teils aus V2). Der Orchestrator ist `src/main.py`,
> aufgerufen über den dünnen Wrapper `main.py`.

---

## Inhaltsverzeichnis

1. [Orchestrierung](#1-orchestrierung)
2. [Phase 0 – Ingestion & Setup](#2-phase-0--ingestion--setup)
3. [Phase 1 – Audio-Analyse](#3-phase-1--audio-analyse)
4. [Phase 2 – Vision / Szenen-Tagging](#4-phase-2--vision--szenen-tagging)
5. [Phase 3 – KI-Regie (Edit-Plan)](#5-phase-3--ki-regie-edit-plan)
6. [Phase 4 – Copywriting](#6-phase-4--copywriting)
7. [Phase 5 – Export & Schnitt](#7-phase-5--export--schnitt)
8. [Analyse-Werkzeuge (V2 / optional)](#8-analyse-werkzeuge-v2--optional)
9. [Backends & Infrastruktur](#9-backends--infrastruktur)
10. [CLI-Schnellreferenz](#10-cli-schnellreferenz)

---

## 1. Orchestrierung

### `main.py` (Root-Wrapper)
Dünner Einstiegspunkt. Fügt das Projekt-Root zum Pfad hinzu und ruft `src.main.main()`.
**Use Case:** Der eine Befehl, den der Nutzer aufruft – `python main.py -i ./input -p pov_story -d 90`.

### `src/main.py` (Pipeline-Orchestrator)
Definiert alle Phasen-Funktionen, den `run_pipeline`-Treiber und den CLI-Parser.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `phase_ingest(input_dir)` | Ruft Phase-0-Ingestion auf, liefert die finale Clip-Liste. |
| `phase_0_setup()` | Generiert fehlende `.cube`-LUT-Dateien. |
| `phase_1_sync(video_paths)` | Audio-Sync + Kick/Snare-Detection für alle Clips. **Preset-unabhängig → gecacht.** |
| `phase_2_analyze(video_paths, existing, save_cb)` | Vision-Tagging pro Clip. **Resumebar:** überspringt bereits getaggte Clips (`existing`), speichert nach jedem Clip via `save_cb`. |
| `phase_3_regie(analysis, preset, duration, provider, multi)` | Schickt Analyse an die KI, erhält Edit-Plan. **Preset-/Dauer-abhängig.** |
| `phase_4_copywriting(clips_metadata, style)` | Generiert Dateinamen + Instagram-Captions. |
| `phase_5_assembly(edit_plan, sync_data, music_path, vision_data)` | FFmpeg-Export jedes Clips (Crop 9:16, LUT, Slow-Mo, VFX), dann Concat zum finalen Reel. Lädt `edit_plan.json` als Fallback. Optional: Musikteppich via `music_path`. |
| `_apply_music_bed(reel, music, clips, vision_data)` | Legt einen frei gewählten Track über das fertige Reel (ersetzt Originalton). Richtet den **Song-Drop auf den Reel-Energie-Peak** aus, 1,5 s Fade-out. |
| `_find_music_drop(music_path)` | Selbstständige Drop-Erkennung (librosa+numpy): steilster Anstieg der Bass-Energie <200 Hz. |
| `_reel_peak_time(clips, vision_data)` / `_score_clip_energy(...)` | Bestimmt den energiereichsten Reel-Moment aus Vision-Tags (Fallback: „drop"-Reason, dann 62 %). |
| `_concat_snippets(snippets, style)` | Fügt exportierte Snippets in Plan-Reihenfolge zum Reel zusammen (Re-Encode für einheitliche fps). |
| `run_pipeline(...)` | Treiber: führt angeforderte Phasen aus, **lädt vorhandene Ergebnisse immer** und überspringt fertige Analyse (Resume). |
| `main()` | argparse-CLI: `--input/-i`, `--preset/-p`, `--duration/-d`, `--style/-s`, `--provider`, `--multi`, `--phase`, `--luts`, `--verbose/-v`. |

**Resume-Verhalten (wichtig):** Ein Voll-Lauf (ohne `--phase`) lädt `output/pipeline_results.json`,
übernimmt gecachten Audio-Sync und resumed das Vision-Tagging. Nur Regie/Copy/Export laufen neu.
→ Varianten erzeugst du günstig mit `--phase regie export`.

---

## 2. Phase 0 – Ingestion & Setup

### `ingest.py`
Dedup, Timestamp-Extraktion und Umbenennung roher Clips zu `UNREEL_YYYYMMDD_HHMMSS.<ext>`.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `ingest_directory(source_dir)` | **Hauptfunktion.** Entfernt Duplikate (Größe + MD5 der ersten 1 MB), liest Aufnahmezeit (ffprobe `creation_time`, Fallback mtime), benennt um. Liefert `IngestResult`. |
| `IngestResult` (Dataclass) | `renamed`, `duplicates_removed`, `skipped`, `errors`, `final_files` + `.to_dict()`, `.save()`. |
| `_quick_hash`, `_read_creation_time`, `_target_name`, `_is_supported` | Interne Helfer (Hash, Zeitstempel, Kollisions-Counter, Format-Check). |

**Standalone-CLI:** `python ingest.py` → räumt den Input-Ordner auf.
**Use Case:** Footage von verschiedenen Geräten/Apps landet chaotisch benannt im `input/` – ein Lauf normalisiert Namen und wirft Doppel raus.

### `lut_generator.py`
Programmatische Erzeugung von 3D-LUT `.cube`-Dateien (rein numpy, kein Foto-Asset nötig).

| Funktion | Zweck / Use Case |
|----------|------------------|
| `generate_all_luts(output_dir)` | Erzeugt alle drei LUTs, falls fehlend. Liefert `{name: Path}`. |
| `get_lut_path(lut_name, lut_dir)` | Pfad zu einer LUT (für FFmpeg `lut3d=`). |
| `_transform_underground_dark/_vhs_analog/_neon_nights` | Farbtransformationen pro Look (crushed blacks, Milky/Faded, Neon-Sättigung). |
| `_generate_cube_file`, `_srgb_to_linear`, `_linear_to_srgb`, `_clamp` | LUT-Sampling und sRGB↔linear-Mathematik. |

**Standalone-CLI:** `python lut_generator.py` → schreibt LUTs nach `luts/`.
**Looks:** `underground_dark` (Default), `vhs_analog`, `neon_nights`.
**Use Case:** Einheitliches cineastisches Color-Grading ohne externe LUT-Dateien.

---

## 3. Phase 1 – Audio-Analyse

### `audio_sync.py`
Synchronisiert mehrere Clips über FFT-Kreuzkorrelation auf eine gemeinsame Zeitachse.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `sync_all_clips(video_paths)` | **Hauptfunktion.** Wählt Referenz-Clip (höchstes RMS) und berechnet Offsets aller anderen. Liefert `SyncResult`. |
| `find_reference_clip(video_paths)` | Bestimmt den Clip mit der besten Audioqualität als Anker. |
| `compute_offset(ref, other)` | Kreuzkorrelation `scipy.signal.correlate(method='fft')` → Versatz in Sekunden. |
| `SyncResult` (Dataclass) | `reference_clip`, `offsets`, `rms_values` + `.to_dict()`, `.save()`. |

**Standalone-CLI:** `python audio_sync.py input/*.mov`
**Use Case:** Mehrere Handys filmen denselben Set – alle Clips werden auf eine Master-Audiospur ausgerichtet.

### `kick_snare_detector.py`
Percussion-Erkennung via Mel-Spektrogramm + Onset-Detection.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `detect_kicks_snares(video_path)` | **Hauptfunktion.** Liefert `PercussionMap` mit Kicks (<200 Hz), Snares (2–8 kHz), BPM. |
| `get_beat_grid(video_path, ...)` | Beat-Raster für taktgenaues Schneiden. |
| `_detect_kicks`, `_detect_snares`, `_get_bpm` | Band-gefilterte Onset-Detection und Tempo-Schätzung. |
| `PercussionMap`, `PercussiveHit` (Dataclasses) | Treffer mit Zeit/Stärke + `.to_dict()`, `.save()`. |

**Standalone-CLI:** `python kick_snare_detector.py input/clip.mov`
**Use Case:** Liefert „Cut-on-Beat"-Punkte und Drops für die KI-Regie und beat-reaktive VFX.

### `analyzer/audio_analyzer.py`
Höherstufige Audio-Analyse (für Highlight-Engine / V2-Pfad).

| Funktion | Zweck / Use Case |
|----------|------------------|
| `analyze_audio(video_path, progress_callback)` | BPM, Beats, Energie-Hüllkurve, Drops, Build-ups/Breakdowns. |
| `extract_audio(video_path, output_path)` | Audiospur als WAV extrahieren (FFmpeg). |
| `_detect_bass_drops`, `_detect_buildups_breakdowns`, `_find_peaks` | Energie-/Onset-basierte Event-Erkennung. |

**Use Case:** Speist die `highlight_engine`-Scores; alternativer Analysepfad zum schlanken `kick_snare_detector`.

---

## 4. Phase 2 – Vision / Szenen-Tagging

### `analyzer/vision_engine.py`
Multimodales Szenen-Tagging über das gewählte Vision-Backend.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `tag_video_frames(video_path)` | **Hauptfunktion.** Sampelt Frames, lässt sie taggen, liefert `list[FrameTag]`. |
| `extract_sample_frames(video_path, ...)` | Repräsentative Frames per OpenCV ziehen. |
| `filter_unusable(tags, min_confidence)` | Wirft `UNUSABLE`/zu unsichere Tags raus. |
| `get_tag_scores(tags)` | Aggregiert Tags zu Highlight-Bonus-Scores. |
| `FrameTag` (Dataclass) | `time`, `tag`, `confidence`, `description` + `.to_dict()`. |

**Standalone-CLI:** `python -m analyzer.vision_engine input/clip.mov`
**Tag-Taxonomie:** `CROWD_ENERGY`, `DJ_SETUP`, `LIGHT_SHOW`, `TRANSITION`, `BREAKDOWN`, `BACKSTAGE`, `ARRIVAL`, `PACKDOWN`, `UNUSABLE`.
**Use Case:** Versteht den Inhalt jedes Clips, damit die Regie sinnvolle Szenen wählt (z. B. Crowd-Peaks, Story-Phasen für `pov_story`).

---

## 5. Phase 3 – KI-Regie (Edit-Plan)

### `regie_engine.py`
Multi-Provider-KI-Regisseur. Schickt die Analyse-JSON an ein LLM und erhält einen millisekundengenauen Schnittplan.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `generate_edit_plan(analysis, preset, duration, provider, output_path)` | **Hauptfunktion.** Erzeugt + validiert einen `EditPlan`, speichert `edit_plan.json`. |
| `generate_multi_plan(...)` | Ruft alle verfügbaren Provider auf (A/B-Vergleich), `edit_plan_<name>.json`. |
| `verify_edit_plan(plan, ...)` | Plausibilitätsprüfung/Auto-Fix des Plans. |
| `create_seamless_loop_plan(...)` | Algorithmischer Loop-Plan (ohne KI) für `seamless_loop`. |
| `resolve_provider(name)` / `get_provider(name)` | Provider-Auflösung inkl. `auto`-Fallback (Claude → Gemini → DeepSeek). |
| `list_available_providers()` | Status aller Provider (Key vorhanden?). |
| `_parse_edit_plan(raw, ...)` | JSON-Parsing inkl. Markdown-Fence-Stripping **und `json_repair`-Fallback** bei fehlerhaftem JSON. |
| `_build_system_prompt(preset, duration, target_bpm)` | Baut den Regie-System-Prompt je Preset. |
| `_trim_analysis_for_prompt(data)` | Kürzt große Arrays vor dem Senden ans LLM. |
| `EditPlan` / `EditClip` (Dataclasses) | Plan-Schema + `.to_ffmpeg_commands()`, `.save()`, `.to_dict()`. |

**Provider-Klassen** (alle erfüllen das `RegieProvider`-Protocol – `name`, `model_id`, `is_available()`, `call()`):

| Klasse | Modell (Default) | Besonderheit |
|--------|------------------|--------------|
| `ClaudeProvider` | `claude-fable-5` | Liest nur Text-Blöcke (ignoriert ThinkingBlocks); Retry ohne `temperature` (Fable lehnt den Param ab). |
| `GeminiProvider` | `gemini-2.5-flash`* | `response_mime_type="application/json"`. |
| `DeepSeekProvider` | `deepseek-v4-pro` | OpenAI-kompatibel, `response_format={"type":"json_object"}`. |
| `LocalMLXProvider` (in `analyzer/`) | `qwen3.5:9b` / MLX | Schema-erzwungenes JSON, offline. Siehe unten. |

\* Default in `config.py` ist `gemini-3.1-pro-preview`; Free-Tier-Keys haben darauf jedoch Quota 0 → `.env` auf `gemini-2.5-flash` gesetzt.

**Standalone-CLI:** `python -m analyzer.regie_engine output/pipeline_results.json --provider deepseek`
**Use Case:** Das kreative Herz – verwandelt nüchterne Analyse-Daten in eine erzählerische Schnittfolge.

### `analyzer/local_regie_provider.py`
Vierter, lokaler Regie-Provider (Cloud bleibt Default).

| Element | Zweck / Use Case |
|---------|------------------|
| `LocalMLXProvider` | Provider mit zwei Backends (per `LOCAL_REGIE_ENGINE`): **ollama** (XGrammar `format=<schema>`) oder **mlx** (`outlines` constrained decoding). Beide erzwingen schema-konformes JSON. |
| `_default_model(engine)` | Default-Modell je Engine. |
| `.unload()` | Gibt Modellspeicher frei. |

**Standalone-CLI:** `python -m analyzer.local_regie_provider`
**Use Case:** Komplett offline/kostenlos Regie fahren, wenn kein Cloud-Key gewünscht ist.

---

## 6. Phase 4 – Copywriting

### `analyzer/copywriter.py`
Generiert Dateinamen und Instagram-Captions via Text-Backend (Llama 3.2 / MLX).

| Funktion | Zweck / Use Case |
|----------|------------------|
| `generate_filename(...)` | Sprechender Dateiname aus Clip-Metadaten. |
| `generate_caption(...)` | Instagram-Caption (Hook, Hashtags). |
| `batch_process(clips_metadata, style)` | Beide Schritte für viele Clips. |
| `save_captions(results, output_path)` | Schreibt `captions.json`. |
| `CopyResult` (Dataclass) | `.to_dict()`. |
| `_clean_filename`, `_query_llm`, `_get_text_backend` | Sanitizing, LLM-Call, Backend-Wahl. |

**Standalone-CLI:** `python -m analyzer.copywriter demo`
**Use Case:** Fertige Posting-Texte/Dateinamen, damit das Reel direkt veröffentlicht werden kann.

---

## 7. Phase 5 – Export & Schnitt

> Der Standardpfad nutzt den FFmpeg-Export direkt in `src/main.py:phase_5_assembly`
> (Crop 9:16 mit JIT-Auto-Framing, LUT, Slow-Mo, beat-reaktive VFX). Die folgenden
> `analyzer/`-Module sind die wiederverwendbare Export-Toolbox (V2-Pfad).

### `analyzer/clip_exporter.py`
FFmpeg-basierter Export einzelner Clips, Montagen und Loops.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `export_clip(video, start, end, output_name, ...)` | Einzelclip exportieren (Reel oder Raw). |
| `export_batch(video, clips, mode, ...)` | Mehrere Schnitte aus einem Video. |
| `export_montage(clips, output_name, ...)` | Mehrere Clips zu einer Montage zusammensetzen. |
| `export_seamless_loop(video, start, end, ...)` | Algorithmischer Swap-Loop mit Crossfade. |
| `CINEMATIC_LOOK_FILTER` (Konstante) | Vordefinierter „Dark Techno"-eq+vignette-Look. |
| `_run_ffmpeg`, `_speed_params`, `_atempo_chain`, `_build_overlay_vf` | Prozess-Handling, Slow-Mo, Audio-Tempo, Filterketten. Abbrechbar via `_active_procs`. |

**Use Case:** Standalone-Export und der V2-Montagepfad; liefert die LUT/Look-Filter-Bausteine.

### `analyzer/clip_normalizer.py`
Helligkeits-Angleich zwischen Clips einer Montage.

| Funktion | Zweck / Use Case |
|----------|------------------|
| `compute_montage_filters(clips)` | Berechnet pro Clip einen `eq`-Filter, damit alle visuell zusammenpassen. |
| `sample_clip_brightness(video, start, end)` | Misst mittlere Helligkeit. |
| `build_look_filter(clip_brightness, target)` | Adaptiver Korrektur-Filter. |

**Use Case:** Verhindert, dass ein zu helles Handyvideo in der Montage „heraussticht".

---

## 8. Analyse-Werkzeuge (V2 / optional)

### `analyzer/video_analyzer.py`
| Funktion | Zweck / Use Case |
|----------|------------------|
| `analyze_video(video_path, progress_callback)` | Szenenwechsel (PySceneDetect), Bewegungsintensität, Lichteffekte. |
| `_get_video_info`, `_detect_scenes`, `_analyze_motion_and_light`, `_generate_thumbnail` | Metadaten, Cut-Erkennung, Motion/Light, Thumbnail. |

**Use Case:** Liefert Motion-/Scene-Signale für die Highlight-Scores.

### `analyzer/highlight_engine.py`
| Funktion | Zweck / Use Case |
|----------|------------------|
| `compute_highlights(audio_results, video_results)` | Kombiniert Audio+Video zu einem Highlight-Score und schlägt Cut-Punkte vor. |
| `_compute_energy_score/_event_score/_motion_score` | Teil-Scores. |
| `_extract_highlight_regions`, `_generate_clip_suggestions`, `_snap_to_beat`, `_remove_overlapping_clips` | Regionen finden, Clips vorschlagen, auf Beat snappen, Überlappungen entfernen. |

**Use Case:** Algorithmische (KI-freie) Alternative zur Clip-Auswahl; beat-genaue Schnittvorschläge.

### `analyzer/tracking_engine.py`
| Funktion | Zweck / Use Case |
|----------|------------------|
| `analyze_tracking(video, fps, start_time, end_time, ...)` | YOLO11-Personen-Tracking → `[{"time", "x_center"}]` für dynamisches 9:16-Auto-Framing. |
| `get_yolo_model()` | Lazy-Load von `yolo11n.pt` (Auto-Download). |

**Use Case:** „JIT Auto-Framing" – hält die Person beim 16:9→9:16-Crop im Bild, statt stumpf mittig zu schneiden.

### `analyzer/watermark_detector.py`
| Funktion | Zweck / Use Case |
|----------|------------------|
| `detect_capcut_watermark(video_path)` | Erkennt CapCut-Wasserzeichen über Helligkeitsmuster im typischen Bereich; liefert Zeitfenster. |
| `_score_frame`, `_find_block`, `_scan` | Region-Scoring und Block-Suche. |

**Use Case:** Wasserzeichen-behaftete Clips erkennen/wegtrimmen, bevor sie ins Reel kommen.

### `analyzer/frame_hasher.py`
| Funktion | Zweck / Use Case |
|----------|------------------|
| `dhash(video, time_sec, hash_size)` | Difference-Hash eines Frames (nur FFmpeg + numpy). |
| `hamming(h1, h2)` | Distanz zweier Hashes. |
| `filter_duplicates(clips, threshold)` | Visuell (fast) identische Clips aussortieren. |

**Use Case:** Near-Duplicate-Clips entfernen, die `ingest.py` (byte-genauer Hash) nicht erwischt.

---

## 9. Backends & Infrastruktur

### `config.py`
Zentrale Konfiguration; lädt aus `.env` (`python-dotenv`). Enthält API-Keys, Modell-IDs
(`CLAUDE_MODEL`, `GEMINI_MODEL`, `DEEPSEEK_MODEL`, lokale Modelle), Pfade (`BASE_DIR`,
`INPUT_DIR`, `OUTPUT_DIR`, `LUT_DIR`), `DEFAULT_LUT` und Provider-/Backend-Schalter.
**Use Case:** Eine Stelle für alle Schalter – keine hartkodierten Secrets oder Pfade.

### `analyzer/vision_backends.py`
| Element | Zweck / Use Case |
|---------|------------------|
| `get_vision_backend()` | Liefert je Plattform/ENV das passende Vision-Backend. |
| `OllamaVisionBackend` | Gemma 4 E2B via Ollama (Windows/Linux, CPU). |
| `MLXVisionBackend` | GPU-beschleunigt auf macOS (Apple Silicon). |
| `VisionBackend` (ABC) | `is_available()`, `describe_frames()`, `unload()`. |

### `analyzer/text_backends.py`
| Element | Zweck / Use Case |
|---------|------------------|
| `get_text_backend()` | Liefert das passende Text-Backend (Copywriting). |
| `OllamaTextBackend` / `MLXTextBackend` | Llama 3.2 via Ollama bzw. MLX. |
| `TextBackend` (ABC) | `is_available()`, `complete()`, `unload()`. |

**Use Case:** Hybride Plattform-Unterstützung – derselbe Code läuft per Ollama (CPU) oder MLX (Apple GPU), ohne dass die Phasen-Logik das wissen muss.

---

## 10. CLI-Schnellreferenz

```powershell
# ── Voller Lauf (Analyse einmalig, dann Reel) ───────────────────────────
python main.py -i ./input -p pov_story -d 90

# ── Varianten (günstig: nutzt gecachte Analyse) ─────────────────────────
python main.py -i ./input -p highlight -d 60 --phase regie export
python main.py -i ./input -p moody     -d 45 --phase regie export

# ── Mit Musikteppich (ersetzt Originalton, Drop trifft Reel-Peak) ───────
python main.py -i ./input -p highlight -d 60 --music ./mysong.mp3
python main.py -i ./input -p highlight -d 60 --music ./mysong.mp3 --phase export

# ── Tarantino-Edit: non-linear, Tech-Noir-Flashback, J-Cut/Lowpass ──────
# (--jcut ist bei -p tarantino automatisch an: Musik dumpf bis zum Drop)
python main.py -i ./input -p tarantino -d 30 --music ./hardtechno.mp3
python main.py -i ./input -p highlight  -d 60 --music ./song.mp3 --jcut

# ── Einzelne Phasen ─────────────────────────────────────────────────────
python main.py --phase sync            # nur Audio-Sync
python main.py --phase vision          # nur Vision-Tagging (resumebar)
python main.py --phase export          # nur Schnitt aus edit_plan.json
python main.py --luts                  # nur LUTs erzeugen

# ── Provider wählen / vergleichen ───────────────────────────────────────
python main.py --provider gemini --phase regie
python main.py --multi --phase regie   # alle Provider (A/B)

# ── Module standalone ───────────────────────────────────────────────────
python ingest.py                                   # Input aufräumen
python audio_sync.py input/*.mov                   # Sync-Offsets
python kick_snare_detector.py input/clip.mov       # Percussion/BPM
python -m analyzer.vision_engine input/clip.mov    # Szenen-Tags
python -m analyzer.copywriter demo                 # Caption-Demo
python -m analyzer.regie_engine output/pipeline_results.json --provider deepseek
python lut_generator.py                            # LUTs erzeugen
```

### Presets

| Preset | Beschreibung |
|--------|--------------|
| `highlight` | Beste Momente, schnelle Cuts, 60–90 s |
| `drop_focus` | Build-up → Drop → Aftermath |
| `seamless_loop` | 15–30 s, algorithmischer Swap-Loop |
| `moody` | Atmosphärisch, langsamere Cuts (BREAKDOWN + LIGHT_SHOW) |
| `pov_story` | „A Day in the Life": `before → during → after`, Anti-Advice-Hook in den ersten ~3 s |

### Wichtige Ausgabedateien (`output/`)

| Datei | Inhalt |
|-------|--------|
| `pipeline_results.json` | Akkumulierte Ergebnisse aller Phasen (Resume-Quelle). |
| `edit_plan.json` | Aktiver Schnittplan (Fallback-Input für den Export). |
| `edit_plan_<provider>.json` | Pläne je Provider bei `--multi`. |
| `captions.json` | Generierte Captions/Dateinamen. |
| `reel_<preset>.mp4` | **Das fertige Reel.** |
