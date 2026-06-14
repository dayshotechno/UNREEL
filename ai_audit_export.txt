UNREEL V3 – AI Audit Export

> Kontext-Bündel. Ausgeschlossen: .env, Binär-/Media-Dateien, luts/*.cube, input/, output/, LOGO/, .agents/, .claude/

1. Verzeichnisstruktur
\\	ext
UNREEL/
├── analyzer/
│   ├── __pycache__/   [14 Dateien ausgelassen]
│   ├── __init__.py
│   ├── audio_analyzer.py
│   ├── clip_exporter.py
│   ├── clip_normalizer.py
│   ├── copywriter.py
│   ├── frame_hasher.py
│   ├── highlight_engine.py
│   ├── local_regie_provider.py
│   ├── text_backends.py
│   ├── tracking_engine.py
│   ├── video_analyzer.py
│   ├── vision_backends.py
│   ├── vision_engine.py
│   └── watermark_detector.py
├── src/
│   ├── __pycache__/   [1 Dateien ausgelassen]
│   └── main.py
├── tests/
│   ├── __pycache__/   [17 Dateien ausgelassen]
│   ├── __init__.py
│   ├── test_audio_sync.py
│   ├── test_config.py
│   ├── test_copywriter.py
│   ├── test_ingest.py
│   ├── test_kick_snare_detector.py
│   ├── test_lut_generator.py
│   ├── test_pipeline_helpers.py
│   ├── test_regie_engine.py
│   └── test_vision_engine.py
├── .agents/   [39 Dateien ausgelassen]
├── .aider-desk/   [4 Dateien ausgelassen]
├── .aider.tags.cache.v4/   [3 Dateien ausgelassen]
├── .claude/   [33 Dateien ausgelassen]
├── .git/   [278 Dateien ausgelassen]
├── .pytest_cache/   [5 Dateien ausgelassen]
├── __pycache__/   [11 Dateien ausgelassen]
├── input/   [85 Dateien ausgelassen]
├── input_pov/   [32 Dateien ausgelassen]
├── LOGO/   [5 Dateien ausgelassen]
├── luts/   [4 Dateien ausgelassen]
├── output/   [842 Dateien ausgelassen]
├── .gitignore
├── audio_sync.py
├── CLAUDE.md
├── CLAUDE_MASTER.md
├── CLAUDE_TASK.md
├── COMMANDS.md
├── config.py
├── env.example
├── GEMINI.md
├── ingest.py
├── kick_snare_detector.py
├── lut_generator.py
├── main.py
├── MLX_SETUP.md
├── MODULES.md
├── PREP_windows.md
├── README.md
├── REEL_recherche.md
├── REGIE_BENCHMARK.md
├── regie_engine.py
├── requirements.txt
├── rollout_plan.md
├── skills-lock.json
├── test_ingest.py
└── TODO.md
\\n
2. Konfiguration & Architektur-Doku

### \requirements.txt\n
\\text
# UNREEL V3 – Python Dependencies
# Install: pip install -r requirements.txt

# --- Audio Analysis ---
librosa>=0.10.0
scipy>=1.11.0
numpy>=1.24.0

# --- Video Processing ---
opencv-python-headless>=4.8.0
moviepy>=1.0.3
ultralytics>=8.0.0
scenedetect>=0.6.0

# --- Local AI Models (via Ollama) ---
ollama>=0.4.0

# --- Regie Engine: Multi-Provider AI ---
anthropic>=0.30.0
google-generativeai>=0.8.0
openai>=1.30.0

# --- Configuration ---
python-dotenv>=1.0.0

# --- Optional: Testing ---
pytest>=7.4.0

# --- Apple Silicon (MLX) ---
mlx>=0.16.0; sys_platform == 'darwin'
mlx-lm>=0.16.0; sys_platform == 'darwin'
mlx-vlm>=0.0.12; sys_platform == 'darwin'
outlines[mlxlm]>=0.0.44; sys_platform == 'darwin'
json-repair>=0.30.0   # Repair malformed LLM JSON output

\\n
### \env.example\n
\\ini
# UNREEL V3 – Environment Configuration
# Copy to .env and fill in your values. NEVER commit this file with real keys.

# --- Regie Engine: Active Provider ---
# Options: "claude", "gemini", "deepseek", "auto"
# "auto" tries providers in fallback order: claude → gemini → deepseek
REGIE_PROVIDER=auto

# --- Anthropic (Claude Fable 5) ---
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-fable-5

# --- Google Gemini 3.1 Pro ---
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-pro-preview

# --- DeepSeek V4 Pro ---
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# --- Ollama (Local Models) ---
OLLAMA_HOST=http://localhost:11434
GEMMA_MODEL=gemma4:e2b
COPYWRITER_MODEL=llama3.2

# --- KI-Backend-Auswahl ---
# VISION_BACKEND: ollama | mlx | gemini | claude
#   gemini = Cloud (gemini-2.5-flash), stärker & schneller, batch-fähig.
#   claude = Cloud-Fallback. DeepSeek kann KEIN Vision (text-only Endpoint).
#   Cloud-Frames verlassen den Rechner – bewusst opt-in.
VISION_BACKEND=ollama
TEXT_BACKEND=ollama

# Cloud-Vision Feintuning (nur bei VISION_BACKEND=gemini|claude):
GEMINI_VISION_MODEL=gemini-2.5-flash
# CLAUDE_VISION_MODEL=claude-fable-5
# Frames pro Modell-Aufruf. Lokal klein lassen (4); Cloud verträgt einen
# ganzen Clip auf einmal → 12 spart Calls & schont Free-Tier-RPM-Limits.
VISION_BATCH_SIZE=4

# --- MLX-Modelle (Apple Silicon) ---
MLX_VISION_MODEL=mlx-community/Qwen2.5-VL-7B-Instruct-4bit
MLX_TEXT_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit
MLX_VISION_FRAMES_PER_CALL=1

# --- Lokaler Regie-Provider (Opt-in; wird in Phase E benutzt) ---
# Bei MLX stattdessen einen Repo-Namen setzen, z.B. mlx-community/Qwen2.5-7B-Instruct-4bit
LOCAL_REGIE_ENGINE=ollama
LOCAL_REGIE_MODEL=qwen3.5:9b

# --- LUT Color Grading ---
# Options: underground_dark, vhs_analog, neon_nights, none
DEFAULT_LUT=underground_dark

\\n
### \.gitignore\n
\\text
.aider*
.env

# Footage & Render-Ausgaben (groß, persönlich)
input/
input_pov/
output/

# Generierte Artefakte
luts/
*.pt
__pycache__/
.pytest_cache/
test2.jpg
test_thumb.jpg

# macOS AppleDouble-Metadaten
._*
.DS_Store

# Lokale Tool-Konfiguration
.claude/
.agents/
skills-lock.json

\\n
### \CLAUDE.md\n
\\markdown
# CLAUDE.md – UNREEL V3 Project Context

## Project Overview

UNREEL V3 is a Python CLI tool that transforms raw, low-quality DJ gig footage (16:9) into polished, synced Instagram Reels (9:16). The pipeline analyzes audio, tags video content with local AI, generates AI-directed edit plans via cloud APIs, and exports with cinematic 3D-LUT color grading. **Everything runs on CPU – no GPU required.**

## Architecture

```
UNREEL/                          # V3 core modules live at the REPO ROOT
├── main.py                      # Thin CLI wrapper → src.main
├── config.py                    # Central config (loads from .env)
├── ingest.py                    # Phase 0: dedup + rename to UNREEL_<timestamp>
├── audio_sync.py                # Cross-correlation multi-clip sync (scipy)
├── kick_snare_detector.py       # Percussion detection (librosa)
├── regie_engine.py              # Multi-provider AI director (Claude/Gemini/DeepSeek)
├── lut_generator.py             # Programmatic .cube LUT generation (numpy)
├── analyzer/                    # Vision/copy backends + V2 analysis tools
│   ├── vision_engine.py         # Scene tagging via Gemma 4 E2B (Ollama)
│   ├── vision_backends.py       # Ollama (CPU) / MLX (Apple) vision backends
│   ├── copywriter.py            # Filenames + Instagram captions (Llama 3.2)
│   ├── text_backends.py         # Ollama / MLX text backends
│   ├── tracking_engine.py       # YOLO11 auto-framing (sample_x_center)
│   ├── local_regie_provider.py  # Optional local regie provider (Ollama/MLX)
│   └── …                        # V2 tools: audio/video_analyzer, highlight_engine,
│                                #   clip_exporter, frame_hasher, watermark_detector
├── src/
│   └── main.py                  # Pipeline orchestrator (all phase_* functions)
├── luts/                        # Generated 3D-LUT files (.cube, regenerated by Phase 0)
├── tests/                       # pytest suite
├── requirements.txt
├── env.example
├── input/                       # User places raw footage here
└── output/                      # All exports land here (incl. caches)
```

See **MODULES.md** for the full per-function reference.

## Pipeline Phases

| Phase | Module | What it does |
|-------|--------|--------------|
| 0 | `lut_generator` | Generates `.cube` LUT files if missing |
| 1 | `audio_sync` + `kick_snare_detector` | Syncs multiple clips via FFT cross-correlation, detects kicks/snares |
| 2 | `vision_engine` | Samples frames → Gemma 4 E2B tags scenes (CROWD_ENERGY, DJ_SETUP, etc.) |
| 3 | `regie_engine` | Sends analysis JSON to cloud AI → gets millisecond-accurate edit plan |
| 4 | `copywriter` | Generates filenames + Instagram captions via local Llama 3.2 |
| 5 | `main.py` (assembly) | FFmpeg exports with 3D-LUT, 9:16 crop, slow-mo |

## AI Provider Setup (Regie Engine)

Three cloud providers for the regie phase, with automatic fallback:

| Provider | Model | SDK | Env Key |
|----------|-------|-----|---------|
| Anthropic | Claude Fable 5 (`claude-fable-5`) | `anthropic` | `ANTHROPIC_API_KEY` |
| Google | `gemini-2.5-flash` (free tier; `gemini-3.1-pro-preview` needs billing) | `google-generativeai` | `GEMINI_API_KEY` |
| DeepSeek | V4 Pro (`deepseek-v4-pro`) | `openai` (compatible endpoint) | `DEEPSEEK_API_KEY` |

Provider quirks (handled in `regie_engine.py` – keep when refactoring):
- Claude Fable 5 may return a thinking block first (read only `type == "text"` blocks) and rejects the `temperature` param (retry without it).
- Gemini model ids must exist for the key's tier – `models.list` is the source of truth.
- All providers: JSON responses are repaired via `json_repair` on parse failure.

`REGIE_PROVIDER=auto` tries Claude → Gemini → DeepSeek. Set at least one key.

Local models via Ollama:
- **Gemma 4 E2B** (`gemma4:e2b`) – scene tagging
- **Llama 3.2** (`llama3.2`) – copywriting

## Key Commands

```bash
# Full pipeline
python main.py --input ./input --preset highlight --duration 60

# Specific provider
python main.py --provider gemini --phase regie

# All providers (A/B comparison)
python main.py --multi --phase regie

# Individual phases
python main.py --phase sync       # Audio sync only
python main.py --phase vision     # Vision tagging only
python main.py --luts             # Generate LUTs only

# Module-level CLI (V3 modules live at the repo root)
python audio_sync.py input/*.mov
python kick_snare_detector.py input/clip.mov
python -m analyzer.vision_engine input/clip.mov
python -m analyzer.copywriter demo
python regie_engine.py output/pipeline_results.json --provider deepseek
python lut_generator.py
python ingest.py                      # dedup + rename input folder
```

## Development Rules

### Critical Constraints
- **CPU-only.** NEVER assume CUDA, GPU, or `torch.cuda`. All ML inference runs on CPU via Ollama or cloud APIs.
- **No hardcoded secrets.** All API keys load from `.env` via `python-dotenv`. Use `os.environ.get()`.
- **Relative paths only.** Use `pathlib.Path` relative to `BASE_DIR`. No absolute paths.
- **Graceful degradation.** If Ollama is not running, vision/copywriting phases return empty results and the pipeline continues. If no API key is set, the regie phase skips with a clear warning.

### Python Conventions
- **snake_case** for functions and variables.
- **kebab-case** for file names (Python modules use snake_case per convention).
- All modules have a `if __name__ == "__main__"` CLI block for standalone testing.
- All modules return typed dataclasses with `.to_dict()` and optional `.save(path)` methods.
- Use `logging` module (never `print()` in library code). CLI entry points may print.
- Handle FFmpeg tasks with `subprocess.run()`, not async (simplicity over complexity).

### Audio & Video
- Audio sync uses `scipy.signal.correlate(mode='full', method='fft')` for CPU performance.
- Kick detection: librosa Mel-spectrogram filtered to <200Hz + onset detection.
- Snare detection: same approach, 2kHz–8kHz band.
- Video cropping to 9:16: `crop=ih*9/16:ih,scale=1080:1920` in FFmpeg.
- Color grading via `lut3d=` FFmpeg filter with generated `.cube` files.
- Slow-motion for high-motion clips: `setpts=PTS*2.0` (50% speed).
- Seamless loops: split clip in half, swap halves, crossfade at junction.

### Data Flow
- All analysis results are plain Python `dict` / `dataclass` → serialized to JSON.
- The pipeline accumulates results in `all_results` dict and saves to `output/pipeline_results.json`.
- The regie engine receives the full analysis dict, trims large arrays, and sends to the AI as JSON.
- AI responses are parsed as JSON (markdown-fence-stripped), validated, and auto-fixed.

### Edit Plan Schema
```json
{
  "clips": [
    {
      "video": "filename.mov",
      "start": 12.345,
      "end": 18.789,
      "transition": "hard_cut_on_beat",
      "reason": "Drop starts here",
      "crop": "9:16",
      "lut": "underground_dark",
      "slow_mo": false,
      "slow_mo_factor": 1.0
    }
  ],
  "narrative": "...",
  "total_duration": 60.0,
  "provider_used": "claude",
  "model_used": "claude-fable-5"
}
```

### Provider Architecture
- Each provider implements the `RegieProvider` protocol: `name`, `model_id`, `is_available()`, `call()`.
- `resolve_provider("auto")` iterates fallback order and returns the first with an API key.
- `generate_multi_plan()` calls all available providers and returns a dict of plans.
- Gemini uses `response_mime_type="application/json"` to force structured output.
- DeepSeek uses `response_format={"type": "json_object"}` via OpenAI-compatible API.
- Claude uses standard Anthropic Messages API.

### Vision Tag Taxonomy
`CROWD_ENERGY`, `DJ_SETUP`, `LIGHT_SHOW`, `TRANSITION`, `BREAKDOWN`, `BACKSTAGE`, `ARRIVAL`, `PACKDOWN`, `UNUSABLE`

`ARRIVAL` (load-in / getting ready before the set) and `PACKDOWN` (packing up / empty floor after the set) are story tags that drive the `pov_story` preset's `before`/`after` phases. They carry no highlight bonus (`0.0`, like `BACKSTAGE`), so they don't affect energy-based presets.

Tag bonus scores for highlight engine: `CROWD_ENERGY=+0.8`, `LIGHT_SHOW=+0.5`, `DJ_SETUP=+0.3`, `BREAKDOWN=+0.2`, `TRANSITION=+0.1`, `BACKSTAGE/ARRIVAL/PACKDOWN=0.0`, `UNUSABLE=-1.0`

### Presets
- `highlight` – Best moments, fast cuts, 60-90s
- `drop_focus` – Build-up → drop → aftermath
- `seamless_loop` – 15-30s, algorithmic swap-loop
- `moody` – Atmospheric, slower cuts, BREAKDOWN + LIGHT_SHOW
- `pov_story` – POV / "A Day in the Life": story-driven vlog reel ordered `before → during → after` a gig (uses BACKSTAGE clips), with an **anti-advice hook** (contrarian text line) in the first ~3s. Adds plan field `hook_text` and per-clip `phase` (`before`/`during`/`after`). Hook is metadata only — not burned into the video.

## Existing Analysis Modules

The `analyzer/` folder contains specific analysis and utility modules:
- `audio_analyzer.py` (BPM, beats, drops, buildups)
- `video_analyzer.py` (motion, scenes, light)
- `highlight_engine.py` (scoring)
- `tracking_engine.py` (YOLO auto-framing)
- `clip_exporter.py` (FFmpeg export with eq-filter)

## Dependencies

```
librosa>=0.10.0        # Audio analysis
scipy>=1.11.0          # Cross-correlation
numpy>=1.24.0          # LUT generation math
opencv-python-headless  # Frame extraction
moviepy>=1.0.3         # Video processing
ollama>=0.4.0          # Local AI (Gemma, Llama)
anthropic>=0.30.0      # Claude API
google-generativeai>=0.8.0  # Gemini API
openai>=1.30.0         # DeepSeek API (OpenAI-compatible)
python-dotenv>=1.0.0   # .env loading
```

\\n
### \CLAUDE_MASTER.md\n
\\markdown
# MASTER-TASK für Claude Code: Lokale KI auf MLX umstellen (Apple Silicon)

> Eine zusammenhängende Arbeitsanweisung. Erledige die Phasen **in Reihenfolge**.
> Nach jedem **Gate** die Verifikationsbefehle ausführen und die Ausgabe zeigen.
> Bei rotem Gate oder Unklarheit: **STOPP und fragen, nicht raten.**

## Status / Scope
- ✅ ERLEDIGT (nicht erneut anfassen): Web-App gelöscht, Ingestion als Phase 0.
- 🔲 DIESE TASK: lokale KI (Vision-Tagging + Copywriter) von HARDCODIERTEM
  Ollama auf eine **Backend-Abstraktion** umstellen, die per ENV zwischen
  **Ollama** (CPU/alte Maschine) und **MLX** (Apple Silicon) umschaltet.
  Ziel-Hardware: MacBook Pro M1 Pro, 16 GB.

## Mitgelieferte, FERTIGE Dateien (unverändert übernehmen)
| Quelle | Zielort im Repo |
|---|---|
| `vision_backends.py`      | `analyzer/vision_backends.py` |
| `text_backends.py`        | `analyzer/text_backends.py` |
| `local_regie_provider.py` | `analyzer/local_regie_provider.py` |
| `requirements.txt`        | Repo-Root (ersetzt die alte) |

## Globale Constraints
- NUR die LLM-/VLM-Aufruf-Stellen ersetzen. Prompts, JSON-Parsing, Cleaning,
  Fallbacks, Dataclasses, CLIs → UNVERÄNDERT.
- Keine neuen Hardcodes. Werte kommen aus ENV via die mitgelieferten Factories.
- CPU/Ollama-Pfad muss erhalten bleiben (Default-Verhalten).
- 16 GB RAM: Vision- und Textmodell NIE gleichzeitig geladen halten.

---

## PHASE A — Backend-Dateien + Dependencies

### A1. Dateien einsetzen
- `analyzer/vision_backends.py` und `analyzer/text_backends.py` ablegen (unverändert).
- alte `requirements.txt` durch die mitgelieferte ersetzen.

### A2. config.py: ALLE neuen ENV-Keys EINMAL anlegen
> Wichtig: diese Keys werden von BEIDEN folgenden Phasen gebraucht. Hier zentral
> einmal hinzufügen, damit sie später nicht doppelt entstehen.
```python
# --- Lokale KI: Backend-Auswahl (ollama | mlx) ---
VISION_BACKEND = os.environ.get("VISION_BACKEND", "ollama")
TEXT_BACKEND   = os.environ.get("TEXT_BACKEND", "ollama")

# --- MLX-Modelle (Apple Silicon) ---
MLX_VISION_MODEL = os.environ.get(
    "MLX_VISION_MODEL", "mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
MLX_TEXT_MODEL   = os.environ.get(
    "MLX_TEXT_MODEL",   "mlx-community/Qwen2.5-7B-Instruct-4bit")
# Optional: Frames pro VLM-Aufruf (nur für multi-image-fähige Modelle > 1 setzen)
MLX_VISION_FRAMES_PER_CALL = int(
    os.environ.get("MLX_VISION_FRAMES_PER_CALL", "1") or 1)

# --- Lokaler Regie-Provider (Opt-in; wird in Phase E benutzt) ---
LOCAL_REGIE_ENGINE = os.environ.get("LOCAL_REGIE_ENGINE", "ollama")  # ollama | mlx
LOCAL_REGIE_MODEL  = os.environ.get("LOCAL_REGIE_MODEL", "qwen3.5:9b")
```
`env.example` um dieselben Keys + Kurzkommentare erweitern.
> Hinweis `LOCAL_REGIE_MODEL`: bei `LOCAL_REGIE_ENGINE=mlx` stattdessen einen
> MLX-Repo-Namen setzen, z.B. `mlx-community/Qwen2.5-7B-Instruct-4bit`.

### A3. Gate A
```bash
python -c "import analyzer.vision_backends, analyzer.text_backends; print('backends import ok')"
python -c "import config; print(config.VISION_BACKEND, config.TEXT_BACKEND, config.MLX_VISION_MODEL)"
```
Erwartung: `backends import ok`, dann `ollama ollama mlx-community/Qwen2.5-VL-7B-Instruct-4bit`.

---

## PHASE B — Vision-Tagging auf Backend umstellen

Datei: `analyzer/vision_engine.py`. Finde `_analyze_frames_batch()`,
`_ollama_available()` und die hardcodierten `OLLAMA_HOST`/`GEMMA_MODEL`.

### B1. Umstellen
1. Import: `from vision_backends import get_vision_backend`
2. Backend lazy beziehen (Modul-Singleton):
   ```python
   _vision_backend = None
   def _get_vision_backend():
       global _vision_backend
       if _vision_backend is None:
           _vision_backend = get_vision_backend()
       return _vision_backend
   ```
3. In `_analyze_frames_batch`: den `import ollama … ollama.chat(...)`-Block
   ersetzen durch:
   ```python
   raw = _get_vision_backend().describe_frames(user_text, frames)
   ```
   Der `user_text`-Aufbau davor und das JSON-Parsing danach bleiben UNVERÄNDERT.
4. In `tag_video_frames`: `_ollama_available()` → `_get_vision_backend().is_available()`.
   **Nach** der Batch-Schleife (alle Frames getaggt): `_get_vision_backend().unload()`
   aufrufen (gibt RAM für die Copywriting-Phase frei – kritisch auf 16 GB).
5. Tote Hardcodes `OLLAMA_HOST`/`GEMMA_MODEL` entfernen (sofern nicht woanders
   importiert). `SYSTEM_PROMPT`, `VALID_TAGS`, `extract_sample_frames`,
   Parsing → unangetastet.

### B2. Gate B (Struktur, ohne echtes Modell)
```bash
python -c "import analyzer.vision_engine; print('vision_engine import ok')"
```
Kein ImportError/NameError. Echtes Tagging wird in Phase D auf der HW getestet.

---

## PHASE C — Copywriter auf Backend umstellen

Datei: `analyzer/copywriter.py`. Finde `_query_ollama()` und die hardcodierten
`OLLAMA_HOST`/`COPYWRITER_MODEL`.

### C1. Umstellen
1. Import: `from text_backends import get_text_backend`
2. Backend lazy beziehen:
   ```python
   _text_backend = None
   def _get_text_backend():
       global _text_backend
       if _text_backend is None:
           _text_backend = get_text_backend()
       return _text_backend
   ```
3. `_query_ollama(prompt, model=..., temperature=...)` durch eine dünne Hülle
   ersetzen (gleiche Aufrufer behalten):
   ```python
   def _query_llm(prompt: str, temperature: float = 0.7) -> str:
       return _get_text_backend().complete(prompt, temperature=temperature)
   ```
   An den 2 Aufrufstellen `_query_ollama(...)` → `_query_llm(...)`, `model=` weg.
4. Hardcodes `OLLAMA_HOST`/`COPYWRITER_MODEL` entfernen.
5. Öffentliche Signaturen (`generate_filename`/`generate_caption`/`batch_process`)
   NICHT brechen: ein evtl. vorhandenes `model=`-Argument belassen + ignorieren.
   `FILENAME_PROMPT`, `CAPTION_PROMPT`, `_clean_filename`, Fallbacks,
   `CopyResult`, `save_captions` → UNVERÄNDERT.

### C2. RAM-Reihenfolge prüfen (16 GB)
Falls `src/main.py` Vision UND Copywriting in einem Lauf macht: sicherstellen,
dass die Vision-Phase (mit ihrem `unload()`) komplett VOR der Copywriting-Phase
läuft. Kein gleichzeitiges Laden beider Modelle. Optional am Ende der
Copywriting-Phase `_get_text_backend().unload()`.

### C3. Gate C
```bash
python -c "import analyzer.copywriter; print('copywriter import ok')"
grep -n "OLLAMA_HOST\|COPYWRITER_MODEL\|GEMMA_MODEL" analyzer/vision_engine.py analyzer/copywriter.py || echo "keine Hardcodes mehr"
```

---

## PHASE D — Doku + Verifikation

### D1. Doku
- `requirements.txt` ist bereits ersetzt (Phase A). Prüfen, dass `ultralytics`
  drin ist (tracking_engine nutzt YOLO).
- `CLAUDE.md`/`README.md`: kurzen Abschnitt „Apple Silicon / MLX" ergänzen
  (ENV-Schalter `VISION_BACKEND`/`TEXT_BACKEND` + Modell-Keys).

### D2. Gate D1 — plattformübergreifend (kein MLX nötig)
```bash
pip install -r requirements.txt          # bricht auf Nicht-Apple NICHT (Marker)
python -c "import analyzer.vision_engine, analyzer.copywriter, config; print('all import ok')"
pytest -q                                # bestehende Suite bleibt grün
```

### D3. Gate D2 — NUR auf dem M1 Pro (echte Modelle)
```bash
# .env: VISION_BACKEND=mlx, TEXT_BACKEND=mlx
python -m analyzer.vision_engine input/<kurzer_clip>.mp4   # taggt via MLX
python -m analyzer.copywriter demo                          # Caption via MLX
```
Manuell prüfen: Tags/Captions plausibel? Activity Monitor → Memory Pressure
grün/gelb? Wenn rot → kleineres Modell (`Qwen2.5-VL-3B` / `Qwen2.5-3B`).

---

## PHASE E — Lokaler Regie-Provider (Opt-in, Cloud bleibt Default)

Ein vierter Regie-Provider `local`. Cloud bleibt Default; lokal wird NUR bewusst
gewählt (`--provider local`). Fallback-Order (auto) wird NICHT geändert.

Der mitgelieferte `LocalMLXProvider` hat ZWEI Backends (ENV `LOCAL_REGIE_ENGINE`):
- `ollama` (Default): nutzt Ollamas `format=<schema>` (braucht Ollama-Dienst+Modell)
- `mlx`: reines mlx-lm via `outlines` (kein Ollama; Schema-Constraint via outlines)
Beide erzwingen schema-konformes JSON (sonst liefern kleine Modelle unsauberes JSON).

### E1. Datei einsetzen
- `analyzer/local_regie_provider.py` ablegen (unverändert; ENV-Keys aus Phase A2 reichen).

### E2. In `regie_engine.py` registrieren (genau 3 Stellen)
1. Import bei den anderen Provider-Klassen:
   ```python
   from local_regie_provider import LocalMLXProvider
   ```
2. `get_provider()` → `providers`-Dict um `"local": LocalMLXProvider` erweitern.
3. `list_available_providers()` → Liste um `("local", LocalMLXProvider)` erweitern.
> NICHT ändern: `REGIE_PROVIDER_FALLBACK_ORDER` und `resolve_provider`
> (auto soll `local` nicht automatisch wählen).

### E3. CLI/Doku
- Falls `src/main.py` `--provider`-choices auflistet: `local` ergänzen.
- README/CLAUDE.md: Hinweis „lokaler Regisseur (Opt-in): `--provider local`;
  Engine via `LOCAL_REGIE_ENGINE=ollama|mlx`".

### E4. Gate E (Struktur)
```bash
python -c "import analyzer.local_regie_provider; print('local provider import ok')"
python -c "import analyzer.regie_engine as r; print([p['name'] for p in r.list_available_providers()])"
```
Erwartung: zweite Zeile enthält `'local'`.

### E5. NUR mit Modell: echter Test (eine der beiden Engines)
```bash
# Engine A (ollama):
ollama pull qwen3.5:9b
LOCAL_REGIE_ENGINE=ollama python -m analyzer.regie_engine output/pipeline_results.json --provider local

# Engine B (reines MLX, kein Ollama):
pip install "outlines[mlxlm]"
LOCAL_REGIE_ENGINE=mlx LOCAL_REGIE_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit \
  python -m analyzer.regie_engine output/pipeline_results.json --provider local
```
Erwartung: gültiger EditPlan; Cuts plausibel. (Benchmark-Details: REGIE_BENCHMARK.md)

---

## Reihenfolge & Commits
1. `feat: vision/text backends + updated requirements` (Phase A)
2. `refactor: vision_engine uses vision backend` (Phase B)
3. `refactor: copywriter uses text backend` (Phase C)
4. `docs: MLX/Apple Silicon section` (Phase D)
5. `feat: local regie provider (opt-in, ollama|mlx)` (Phase E)

## Definition of Done
- [ ] Gate A–D1 grün; (auf M1 Pro) Gate D2 grün; Gate E grün
- [ ] `VISION_BACKEND`/`TEXT_BACKEND=ollama` → altes Verhalten; `=mlx` → MLX
- [ ] Keine hardcodierten OLLAMA_HOST/GEMMA_MODEL/COPYWRITER_MODEL mehr
- [ ] Vision unload() vor Copywriting; kein Doppel-Laden auf 16 GB
- [ ] `pip install -r requirements.txt` bricht auf keiner Plattform
- [ ] Doku enthält den MLX-Abschnitt
- [ ] `local`-Provider registriert; auto/Fallback unverändert; `--provider local` funktioniert

---

## Begleit-Dokumente (Referenz, nicht ausführen)
- `MLX_SETUP.md` — Hardware-Realität, Modellwahl, Benchmark-Befehle
- `INSTALL_macbook.md` — Schritt-für-Schritt-Installation auf nacktem Mac
> Hinweis Multi-Image: `MLX_VISION_FRAMES_PER_CALL>1` nur mit offiziell
> multi-image-fähigen VLMs (Qwen2-VL, Pixtral, llava-interleaved). Qwen2.5-VL
> ist NICHT gelistet → dort bei 1 bleiben.
```

\\n
### \README.md\n
\\markdown
# UNREEL V3

**Automatisierte DJ-Video-Pipeline.** Verwandelt rohes Gig-Footage in ein fertiges, hochkant
geschnittenes Instagram-Reel (1080×1920) – mit Audio-Analyse, lokalem KI-Szenen-Tagging,
KI-gesteuertem Schnittplan und 3D-LUT-Color-Grading. 
Unterstützt hybride Plattform-Modi: **Windows/Linux** (lokal auf CPU via Ollama) und **macOS** (GPU-beschleunigt via MLX).

```
 0 Setup  →  1 Sync  →  2 Vision  →  3 Regie  →  4 Copy  →  5 Export
 (LUTs)      (Audio)     (Tags)       (KI-Plan)   (Captions)  (Schnitt + Reel)
```

Ein Befehl → ein fertiges Reel:

```powershell
python main.py -i ./input -p pov_story -d 45
# Ergebnis: output/reel_pov_story.mp4
```

---

## Quickstart

```powershell
# 1) Abhängigkeiten
python -m pip install -r requirements.txt
python -m pip install anthropic openai google-generativeai ollama

# 2) Keys eintragen (mind. einer reicht)
Copy-Item env.example .env ; notepad .env

# 3) Lokale Modelle (für Vision + Captions)
ollama pull gemma4:e2b
ollama pull llama3.2:3b

# 4) Clips nach ./input legen und starten
python main.py -i ./input -p pov_story -d 45
```

> Detaillierte Schritt-für-Schritt-Anleitung, alle Optionen und Troubleshooting:
> **→ [COMMANDS.md](COMMANDS.md)**
>
> Vollständige Referenz aller Skripte und Funktionen mit Use-Cases:
> **→ [MODULES.md](MODULES.md)**

---

## Presets

| Preset | Beschreibung |
|--------|--------------|
| `highlight` | Beste Momente, hohe Energie, schnelle Cuts |
| `drop_focus` | Aufbau → Drop → Aftermath |
| `seamless_loop` | Kurz, Ende fließt in den Anfang (ohne API-Call) |
| `moody` | Atmosphärisch, langsamere Cuts |
| `pov_story` | POV / „A Day in the Life" mit Anti-Advice-Hook |

## AI-Provider (Regie-Phase)

`REGIE_PROVIDER=auto` wählt automatisch in der Reihenfolge **DeepSeek → Claude → Gemini**
(erster mit Key + installiertem SDK). Lokale Modelle laufen über das System-Backend 
(Ollama auf Windows/Linux, natives MLX auf Apple Silicon).

## Wichtigste Ausgaben (`output/`)

- **`reel_<preset>.mp4`** – das fertige Reel
- `snippet_*.mp4` – die einzelnen Schnitt-Clips
- `edit_plan.json` – der KI-Schnittplan (bei `pov_story` inkl. `hook_text`)
- `captions.json` – Instagram-Captions

---

## Projekt-Struktur

```
UNREEL/
├── src/main.py          # Pipeline-Orchestrator (Phasen 0–5)
├── main.py              # Einstieg (delegiert an src/main.py)
├── config.py            # Zentrale Konfiguration (lädt aus .env)
├── audio_sync.py        # Audio-Cross-Correlation-Sync
├── kick_snare_detector.py
├── regie_engine.py      # Multi-Provider KI-Regie (Schnittplan)
├── lut_generator.py     # .cube-LUTs
├── analyzer/            # Spezifische Analyse-Module
│   ├── vision_engine.py # Szenen-Tagging (Ollama / MLX)
│   └── copywriter.py    # Dateinamen + Captions (Ollama / MLX)
├── luts/                # Generierte Farb-LUTs
├── tests/               # Offline-Unit-Tests
├── input/               # Rohes Footage hier ablegen
└── output/              # Alle Ergebnisse
```

## Tests

```powershell
python -m unittest discover -s tests -t .
```

---

**Dokumentation:** [COMMANDS.md](COMMANDS.md) (Anleitung & Befehle) · [CLAUDE.md](CLAUDE.md) (Architektur & Entwicklungsregeln)

\\n
### \COMMANDS.md\n
\\markdown
# UNREEL V3 – Endnutzer-Referenz

**UNREEL V3** verwandelt rohes DJ-Gig-Material automatisch in ein fertiges, hochkant geschnittenes Instagram-Reel (1080×1920).  
Die Pipeline durchläuft 6 Stufen: **Setup** (LUTs) → **Sync** (Audio) → **Vision** (Tags) → **Regie** (KI-Plan) → **Copy** (Captions) → **Export** (Schnitt + Reel).

> **Ausführen:** Immer aus dem Projekt-Root `C:\Users\DAY SHO\Desktop\UNREEL`  
> `python main.py …` (kurz) oder `python -m src.main …`

---

## 1. Einmaliges Setup

```powershell
python -m pip install -r requirements.txt
python -m pip install anthropic openai google-generativeai ollama
Copy-Item env.example .env
notepad .env
```

In der `.env` mindestens **einen** API-Key eintragen. Empfohlen: `REGIE_PROVIDER=auto`.  
**Ollama starten und Modelle holen** (für Vision & Copywriting):

```powershell
ollama serve
ollama pull gemma4:e2b
ollama pull llama3.2:3b
```

---

## 2. Schnellstart – Ein Befehl, ein Reel

```powershell
python main.py -i ./input -p highlight -d 60
```

Ergebnis in `output/`:
- **`reel_<preset>.mp4`** – das fertige Reel
- `snippet_001…00N.mp4` – Einzelclips
- `edit_plan.json` – Schnittplan
- `captions.json` – Caption-Vorschläge

---

## 3. Alle CLI-Optionen

| Flag | Werte | Bedeutung |
|------|-------|-----------|
| `-i, --input` | Pfad | Ordner mit Quell-Clips (Default `./input`) |
| `-o, --output` | Pfad | Ausgabe-Ordner (Default `./output`) |
| `-p, --preset` | siehe unten | Schnitt-Stil |
| `-d, --duration` | Sekunden | Ziel-Länge des Reels (Default `60`) |
| `-s, --style` | `techno`, `house`, `minimal` | Caption-Stil für Phase 4 |
| `--provider` | `deepseek`, `claude`, `gemini`, `auto` | Erzwingt einen KI-Provider |
| `--multi` | – | Pläne von **allen** verfügbaren Providern |
| `--music` | Pfad | Musik-Track als Hintergrundaudio (ersetzt Original) |
| `--jcut` | – | J-Cut + Lowpass: Musik dumpf bis zum Drop, dann voll |
| `--endcard` | – | Brutalistisches Logo-Endcard anhängen |
| `--sfx` | – | Unsichtbares Sounddesign: Noise-Riser in den Drop + Sub-Impact (braucht `--music`) |
| `--phase` | `setup`, `sync`, `vision`, `regie`, `copy`, `export`, `analyze` | Nur bestimmte Phasen ausführen |
| `--luts` | – | Nur LUTs erzeugen und beenden |
| `-v, --verbose` | – | Ausführliche Debug-Ausgaben |

**Hinweis zu `--phase`**: `analyze` = `sync` + `vision` in einem. Mehrere Phasen möglich: `--phase regie export`.

---

## 4. Presets im Detail

| Preset | Beschreibung | Typische Länge |
|--------|--------------|----------------|
| `highlight` | Beste Momente, hohe Energie, schnelle Cuts | 60–90 s |
| `drop_focus` | Aufbau → Drop → Aftermath, Drops zentriert | 60 s |
| `seamless_loop` | Kurz, Ende fließt in Anfang (kein API-Call) | 15–30 s |
| `moody` | Atmosphärisch, langsame Cuts, `BREAKDOWN`+`LIGHT_SHOW` | 60 s |
| `pov_story` | **„A Day in the Life"**: before → during → after + Anti-Advice-Hook | 30–60 s |
| `tarantino` | **Retention-Pipeline**: 30s Reel mit 4 Phasen (hook/flashback/buildup/escalation), setzt `--jcut` + `--endcard` automatisch | 30 s (fest) |
| `artist_narrative` | **Story-Waffe** (Reichweite): sarkastischer POV-Hook, entsättigter „Grind" (journey) → Explosion in den Club beim Drop. Auto `--jcut` + `--endcard` | 15–45 s |
| `booking` | **Promoter-Schaufenster**: pure Professionalität, Mixer-Technik + volle Crowd, keine privaten Szenen, kompromisslose Eskalation. Auto `--endcard` | 15–45 s |
| `community` | **Behind-the-Scenes** (Fans): chronologisch, lockerer, Crew/Candid, Kontrast „privater Patrick vs. Maschine DAY SHØ" | 15–45 s |

**Retention-Presets** (`tarantino`, `artist_narrative`, `booking`, `community`) zielen auf 15–45 s; ohne `-d` werden 30 s genutzt. Der Drop deiner `--music` wird automatisch auf den Energie-Peak des Reels gelegt. `tarantino` ist fest 30 s.

---

## 5. Phasenweises Arbeiten & Resume

```powershell
python main.py -i ./input --phase setup            # Nur LUTs
python main.py -i ./input --phase sync             # Nur Audio-Sync
python main.py -i ./input --phase vision           # Nur Vision-Tagging (Ollama)
python main.py -i ./input --phase regie            # Nur Schnittplan (braucht vorh. Vision)
python main.py -i ./input --phase copy             # Nur Captions
python main.py -i ./input --phase export           # Nur Schnitt + Reel
python main.py -i ./input --phase regie export     # Plan neu + Reel bauen
```

**Resume-Mechanismus**:  
- Phasen laden vorhandene `output/pipeline_results.json` und überspringen fertige Schritte.  
- Vision speichert **nach jedem Clip** – ein abgebrochener Lauf kann einfach neu gestartet werden.

**Empfohlener Workflow für pov_story / tarantino:**  
```powershell
python main.py -i ./input --phase vision          # Einmal Vision laufen lassen (dauert)
python main.py -i ./input -p tarantino -d 30 --music track.mp3 --phase regie export
```

---

## 6. Kurz-Referenz

```powershell
# Volles Reel (alle Phasen)
python main.py -i ./input -p highlight -d 60

# tarantino mit Musik und J-Cut
python main.py -i ./input -p tarantino --music track.mp3

# pov_story
python main.py -i ./input_pov -p pov_story -d 45

# Nur Vision taggen, dann Regie+Export mit verschiedenen Presets
python main.py -i ./input --phase vision
python main.py -i ./input -p highlight --phase regie export
python main.py -i ./input -p moody --phase regie export

# Multi-Provider Vergleich
python main.py -i ./input -p highlight --multi

# Provider-Status
python -c "import regie_engine as r; [print(p['name'], p['model'], p['available']) for p in r.list_available_providers()]"

# Nur LUTs
python main.py --luts

# Modul einzeln testen
python audio_sync.py input/*.mov
python vision_engine.py input/clip.mov
python regie_engine.py output/pipeline_results.json -p pov_story --provider gemini
```

---

## 7. Troubleshooting (Kurzfassung)

| Symptom | Lösung |
|---------|--------|
| Vision liefert 0 Tags | Unkritisch; Clip erneut taggen (Resume) |
| Vision bricht ab | Ruhezustand deaktivieren; `--phase vision` erneut starten |
| Regie: leeres JSON | Anderen Provider testen (`--provider claude`) |
| Export: FFmpeg-Fehler bei `lut3d` | Aus dem Projekt-Root starten |
| Reel kürzer als `-d` | Normal – Quellclip-Länge begrenzt |
| „No edit plan available" | API-Key prüfen; `--provider` setzen |

---

## 8. Output-Dateien

| Pfad | Inhalt |
|------|--------|
| `output/pipeline_results.json` | Gesammelte Analyse aller Phasen |
| `output/edit_plan.json` | Schnittplan |
| `output/snippet_001…00N.mp4` | Einzelne geschnittene Clips |
| `output/reel_<preset>.mp4` | **Fertiges Reel** |
| `output/captions.json` | Dateinamen + Instagram-Captions |
| `output/tracking_cache.json` | Gecachte Auto-Framing-Daten |
| `output/percussion_map.json` | Kick/Snare/BPM des Tracks |
| `luts/*.cube` | Farb-LUTs |

\\n
### \GEMINI.md\n
\\markdown
# GEMINI.md — Projektregeln & Aufgabe für Antigravity (Gemini 3.1)

Diese Datei ist der verbindliche Kontext für jeden Agenten in diesem Repo.
Halte dich an die Regeln UND arbeite die unten verlinkte Master-Aufgabe ab.

## Arbeitsweise in Antigravity (verbindlich)
1. **Erst Plan-Artifact, dann Code.** Erzeuge für JEDE Phase zuerst einen
   Implementation-Plan als Artifact und WARTE auf meine Genehmigung/Annotation,
   bevor du Dateien änderst. Keine autonome Mehrdatei-Umsetzung ohne Freigabe.
2. **Eine Phase pro Lauf.** Vermische Phasen NICHT. Nach jeder Phase: das
   zugehörige **Gate** als Terminal-Artifact ausführen und die Ausgabe zeigen.
3. **Bei rotem Gate oder Unklarheit: STOPP und frag per Kommentar.** Nicht raten,
   nicht „weiterprobieren".

## KRITISCHE Wissens-Constraints (sonst halluzinierst du falschen Code)
> Diese Bibliotheken sind speziell und vermutlich nicht 1:1 in deinem Training.
> Verlasse dich auf die MITGELIEFERTEN, FERTIGEN Dateien — erfinde KEINE eigene
> Implementierung und keine „Standard"-Alternative.

- `mlx`, `mlx-vlm`, `mlx-lm`, `outlines` laufen NUR auf Apple Silicon. NICHT auf
  Windows installieren/testen. Auf Nicht-Apple werden sie via Plattform-Marker
  in `requirements.txt` übersprungen — das ist GEWOLLT.
- Die fertigen Dateien `vision_backends.py`, `text_backends.py`,
  `local_regie_provider.py` sind GETESTET. **Übernimm sie unverändert.** Ändere
  NICHT ihre Aufruf-Signaturen oder die MLX-/outlines-API-Aufrufe.
- Ersetze in `vision_engine.py`/`copywriter.py` NUR die LLM/VLM-Aufrufstelle.
  Prompts, JSON-Parsing, Cleaning, Fallbacks, Dataclasses, CLIs → UNVERÄNDERT.
- Keine neuen Hardcodes (kein hardcodiertes OLLAMA_HOST/Modell). Werte kommen aus
  ENV/config über die mitgelieferten Factory-Funktionen.

## Die Aufgabe
Arbeite **`CLAUDE_MASTER.md`** ab (gilt modell-unabhängig: Phasen A–E + die
bereits erledigte Phase 0). Es ist die maßgebliche Schritt-für-Schritt-Spezifikation
inkl. exakter Code-Snippets, der drei Registrierungsstellen für den lokalen
Provider und aller Gates. Diese GEMINI.md ergänzt nur die Antigravity-spezifische
Arbeitsweise; bei Konflikten gewinnt der konkrete Schritt aus CLAUDE_MASTER.md.

## Plattform-Kontext für DIESEN Lauf
- Falls auf **Windows** (Vorbereitung): Ziel sind alle Gates AUSSER D2.
  MLX nicht installieren; Logik über das **Ollama-Backend** verifizieren
  (siehe `PREP_windows.md`). `VISION_BACKEND=ollama`, `TEXT_BACKEND=ollama`,
  `LOCAL_REGIE_ENGINE=ollama`.
- Falls auf **macOS (Apple Silicon)**: zusätzlich Gate D2 + MLX-Pfade.

## Pro-Phase: Plan-Artifact-Vorlage (so will ich es)
Für jede Phase liefere im Plan-Artifact:
- **Betroffene Dateien** (exakte Pfade) + ob neu/geändert.
- **Genaue Änderung** (welche Funktion/Zeile, welcher Ersatz) — bei
  vision_engine/copywriter NUR die eine Aufrufstelle.
- **Gate-Befehle**, die du danach ausführst, + erwartete Ausgabe.
- **Risiken/Annahmen** (z.B. „config-Key X fehlt evtl." → dann anhalten).

## Phasen-Kurzüberblick (Details in CLAUDE_MASTER.md)
- Phase 0 — ✅ erledigt (Web-App raus, Ingestion). NICHT anfassen.
- Phase A — Backend-Dateien einsetzen + ALLE neuen config-Keys einmal anlegen.
- Phase B — vision_engine auf `vision_backends` umstellen (+ `unload()` nach Tagging).
- Phase C — copywriter auf `text_backends` umstellen.
- Phase D — Doku + plattformweite Verifikation (D1 überall, D2 nur Mac).
- Phase E — lokalen Regie-Provider registrieren (3 Stellen; auto/Fallback NICHT ändern).

## Definition of Done (gesamt)
- Alle Plan-Artifacts genehmigt, jede Phase einzeln umgesetzt.
- Gate A–D1 + E grün (Windows); D2 grün (Mac).
- `pip install -r requirements.txt` bricht auf keiner Plattform.
- `ollama`-Default-Verhalten erhalten; `mlx`-Schalter funktioniert auf dem Mac.
- Keine veränderten Signaturen/APIs in den mitgelieferten Dateien.

\\n
### \MODULES.md\n
\\markdown
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
# (-p tarantino aktiviert --jcut UND --endcard automatisch)
python main.py -i ./input -p tarantino -d 30 --music ./hardtechno.mp3
python main.py -i ./input -p highlight  -d 60 --music ./song.mp3 --jcut --endcard

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

\\n
### \TODO.md\n
\\markdown
# TODO – Stand vom 12.06.2026 auf das MacBook übertragen

Alle Code-Änderungen von heute sind auf GitHub (`main`, Commits `f4458f4` →
`941f078` → `c48d0f0`). **Der Code kommt also per `git pull` – manuell
nachziehen musst du nur, was Git nicht überträgt** (.env, Dependencies,
lokale Caches in `output/`).

---

## 1. Code holen

- [ ] `git pull origin main`
- [ ] Prüfen, dass nichts Lokales kollidiert (`git status` vorher)

## 2. Dependencies nachinstallieren (neu seit heute)

- [ ] `pip install json-repair` (Repair-Fallback für kaputtes LLM-JSON)
- [ ] `pip install scenedetect` (war in requirements.txt vergessen)
- [ ] oder einfach: `pip install -r requirements.txt`
      (zieht auf macOS automatisch auch die MLX-Pakete)

## 3. `.env` anpassen (gitignored – überträgt sich NICHT!)

- [ ] `GEMINI_MODEL=gemini-2.5-flash`
      (war `gemini-3.1-pro` → existiert nicht; `gemini-3.1-pro-preview`
      braucht Billing, Free-Tier hat darauf Quota 0)
- [ ] Optional: `EXPORT_WORKERS=3` (Parallel-Export; Default ist 3,
      auf einem starken MacBook ggf. 4)

## 4. Lokale Caches (gitignored, in `output/`)

Diese Dateien entstehen auf dem Mac neu – nichts zu tun, nur wissen:

- [ ] `output/pipeline_results.json` – Vision-Tags werden auf dem Mac
      **einmal neu getaggt** (oder die Datei vom Windows-Rechner rüberkopieren,
      dann wird resumed – Pfad-Keys sind absolut, müssen aber nur als
      `input/`-Dateinamen matchen → bei identischem Input-Ordner-Inhalt
      funktioniert Kopieren NICHT direkt wegen absoluter Pfade. Neu taggen
      ist sauberer.)
- [ ] `output/tracking_cache.json` – baut sich beim ersten Export selbst auf
- [ ] `luts/*.cube` – werden von Phase 0 automatisch generiert

---

## Was sich heute geändert hat (Kontext zum Nachlesen)

### Bugfixes
| Problem | Fix | Datei |
|---|---|---|
| Gemini 404 `gemini-3.1-pro is not found` | korrekte Modell-ID, Free-Tier-Default `gemini-2.5-flash` | `config.py`, `.env`, `env.example` |
| Claude crash `'ThinkingBlock' has no attribute 'text'` | nur `type=="text"`-Blöcke lesen | `regie_engine.py` |
| Claude 400 `temperature is deprecated` (Fable 5) | Retry ohne `temperature` | `regie_engine.py` |
| DeepSeek: kaputtes JSON (fehlendes Komma) | `json_repair`-Fallback beim Parsen | `regie_engine.py` |
| FFmpeg: fast alle Snippets schlugen fehl | Kommata in Crop-Expression escapen (`\,`) | `src/main.py` |
| `pump`-VFX crashte (zoompan kann kein `enable`) | zeitbasierter Zoom-Punch via `scale=eval=frame` | `src/main.py` |
| `flash`-VFX = 0,2s pures Weiß (`brightness=1.5`) | auf `0.4` reduziert | `src/main.py` |
| Voll-Lauf wipte Vision-Tags | Resume lädt `pipeline_results.json` IMMER | `src/main.py` |
| Concat-Timeout (10 min zu kurz) | obsolet durch Stream-Copy, Fallback 60 min | `src/main.py` |
| Reel kürzer als geplant (KI überplant Quellenden) | Clamping + Headroom-Rückgewinnung + `clip_durations` im Prompt | `regie_engine.py`, `src/main.py` |
| Copywriter bekam Fake-Metadaten | echte Vision-Tags, Plan-Narrativ + Hook, echte Dauern | `src/main.py` |

### Performance (Export: ~35 min → ~1:30 min)
- **Stream-Copy-Concat**: Snippets einheitlich encodiert (fps/pix_fmt/Audio),
  Concat kopiert nur noch Streams (2s statt 12–15 min, keine 2. Encode-Generation)
- **Tracking**: `sample_x_center()` seekt 10 Frames statt alle zu dekodieren
  (~10×), Ergebnisse gecacht in `output/tracking_cache.json`
- **Parallel-Export**: 3 Worker (`EXPORT_WORKERS`), YOLO hinter Lock
- **Vision-Vorfilter**: 5-Frame-dHash erkennt Duplikat-Clips → erben Tags,
  Gemma wird übersprungen (kalibriert: Duplikate ≤7 Bit, Szenen ≥16, Threshold 10)

### Neue Features
- **`--music <pfad>`**: Track über das fertige Reel legen (ersetzt Originalton);
  Song-Drop wird automatisch auf den Reel-Energie-Peak ausgerichtet, 1,5s Fade-out
- **`MODULES.md`**: vollständige Modul-/Funktionsreferenz
- **15 neue Tests** (`tests/test_pipeline_helpers.py`), Suite gesamt 89 grün

### macOS-spezifische Hinweise
- Vision/Copywriting laufen auf dem Mac über **MLX** statt Ollama
  (automatische Backend-Wahl via `analyzer/vision_backends.py` /
  `text_backends.py`) – die heutigen Änderungen betreffen die Backends nicht.
- `yolo11n.pt` lädt ultralytics beim ersten Tracking automatisch herunter.
- Offen/geparkt: Migration `google-generativeai` → `google-genai`
  (altes SDK ist deprecated, läuft aber noch).

## Verifikation auf dem Mac

- [ ] `python -m pytest tests/ -q` → 89 passed
- [ ] `python main.py -i ./input -p pov_story -d 90` (erster Lauf taggt neu)
- [ ] Zweiter Varianten-Lauf ist dann billig:
      `python main.py -i ./input -p highlight -d 60 --phase regie export`

\\n
3. Quellcode (Python)

### \audio_sync.py\n
\\python
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

\\n
### \config.py\n
\\python
"""
UNREEL V3 – Configuration
All settings loaded from environment variables or .env file.
NEVER hardcode secrets or API keys.
"""

import os
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LUT_DIR = BASE_DIR / "luts"
LUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Ingestion (Phase 0)
# ---------------------------------------------------------------------------
# Source folder ingestion scans (= the pipeline input dir by default).
VIDEO_SOURCE_DIR = INPUT_DIR
# Video and Audio extensions ingestion/the pipeline accept (matched case-insensitively).
SUPPORTED_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mp3", ".wav", ".flac", ".aiff", ".aif"]

# ---------------------------------------------------------------------------
# Audio Analysis
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100
# V2 analysis modules (audio_analyzer, highlight_engine) reference these names.
AUDIO_SAMPLE_RATE = SAMPLE_RATE  # alias kept for the V2 analyzer modules
HOP_LENGTH = 512                 # librosa STFT/onset hop (≈11.6 ms @ 44.1 kHz)
ENERGY_THRESHOLD_PERCENTILE = 75  # energy-peak gate used by analyze_audio
BASS_FREQ_MAX = 200              # Hz – upper bound of the bass/kick band
BUILDUP_WINDOW_SEC = 4.0         # window for buildup/drop energy ramp detection
MIN_DROP_ENERGY_RATIO = 1.8      # bass energy jump factor that counts as a drop
TEMP_DIR = OUTPUT_DIR            # scratch dir for extracted per-clip audio (.wav)
AUDIO_SYNC_OUTPUT = OUTPUT_DIR / "audio_sync.json"
PERCUSSION_OUTPUT = OUTPUT_DIR / "percussion_map.json"

# ---------------------------------------------------------------------------
# LUT Color Grading
# ---------------------------------------------------------------------------

DEFAULT_LUT = os.environ.get("DEFAULT_LUT", "underground_dark")
AVAILABLE_LUTS = ["underground_dark", "vhs_analog", "neon_nights"]

# ---------------------------------------------------------------------------
# Ollama (Local AI Models)
# ---------------------------------------------------------------------------

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
COPYWRITER_MODEL = os.environ.get("COPYWRITER_MODEL", "llama3.2")

# --- Lokale KI: Backend-Auswahl (ollama | mlx) ---
VISION_BACKEND = os.environ.get("VISION_BACKEND", "ollama")
TEXT_BACKEND   = os.environ.get("TEXT_BACKEND", "ollama")

# --- MLX-Modelle (Apple Silicon) ---
MLX_VISION_MODEL = os.environ.get(
    "MLX_VISION_MODEL", "mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
MLX_TEXT_MODEL   = os.environ.get(
    "MLX_TEXT_MODEL",   "mlx-community/Qwen2.5-7B-Instruct-4bit")
# Optional: Frames pro VLM-Aufruf (nur für multi-image-fähige Modelle > 1 setzen)
MLX_VISION_FRAMES_PER_CALL = int(
    os.environ.get("MLX_VISION_FRAMES_PER_CALL", "1") or 1)

# --- Lokaler Regie-Provider (Opt-in; wird in Phase E benutzt) ---
LOCAL_REGIE_ENGINE = os.environ.get("LOCAL_REGIE_ENGINE", "ollama")  # ollama | mlx
LOCAL_REGIE_MODEL  = os.environ.get("LOCAL_REGIE_MODEL", "qwen3.5:9b")

# ---------------------------------------------------------------------------
# Regie Engine – Multi-Provider AI Configuration
# ---------------------------------------------------------------------------
# Active provider: "claude", "gemini", "deepseek", or "auto"
# "auto" tries providers in order: claude → gemini → deepseek

REGIE_PROVIDER = os.environ.get("REGIE_PROVIDER", "auto")

# --- Anthropic (Claude Fable 5) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-fable-5")

# --- Google Gemini 3.1 Pro ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

# --- DeepSeek V4 Pro ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# Provider priority order for "auto" mode
REGIE_PROVIDER_FALLBACK_ORDER = ["deepseek", "claude", "gemini"]

# ---------------------------------------------------------------------------
# Highlight Scoring Weights (adjusted to include vision)
# ---------------------------------------------------------------------------

WEIGHT_MOTION = 0.25
WEIGHT_AUDIO = 0.25
WEIGHT_SCENE = 0.20
WEIGHT_LIGHT = 0.15
WEIGHT_VISION_TAGS = 0.15

# Vision tag bonus scores
TAG_BONUS_SCORES = {
    "CROWD_ENERGY": 0.8,
    "LIGHT_SHOW": 0.5,
    "DJ_SETUP": 0.3,
    "TRANSITION": 0.1,
    "BREAKDOWN": 0.2,
    "BACKSTAGE": 0.0,
    "ARRIVAL": 0.0,    # Story-only (pov_story "before"); no highlight bonus
    "PACKDOWN": 0.0,   # Story-only (pov_story "after"); no highlight bonus
    "UNUSABLE": -1.0,
}

# ---------------------------------------------------------------------------
# Export Settings
# ---------------------------------------------------------------------------

REEL_WIDTH = 1080
REEL_HEIGHT = 1920
REEL_FPS = 30
REEL_BITRATE = "4M"
H264_PRESET = "fast"
H264_CRF = 23

# Slow-Mo threshold
SLOW_MO_MOTION_THRESHOLD = 0.8
SLOW_MO_FACTOR = 2.0

# ---------------------------------------------------------------------------
# Vision Engine
# ---------------------------------------------------------------------------

VISION_SAMPLE_INTERVAL = 5  # seconds between frame samples
VISION_BATCH_SIZE = 4
VISION_CONFIDENCE_THRESHOLD = 0.3

\\n
### \ingest.py\n
\\python
"""
UNREEL – Ingestion & Renaming (Phase 0)

Gerettet aus der (gelöschten) Flask-Web-App `app.py` (_ingest_file / run_watchdog).

Verantwortung:
    1. Dedup    – Duplikate via (Dateigröße + MD5 der ersten 1 MB) erkennen
                  und entfernen. Exakt, deterministisch, offline. Kein KI.
    2. Timestamp – echten Aufnahme-Zeitpunkt aus den Metadaten lesen
                  (ffprobe creation_time), Fallback: Datei-mtime.
    3. Rename   – nach UNREEL_YYYYMMDD_HHMMSS<ext>, mit Kollisions-Counter.

Unterschied zur Web-Version:
    - Kein Dauer-Watchdog (30-s-Polling). Stattdessen einmaliger Lauf über
      den Input-Ordner, gedacht als Pipeline-Phase 0 oder Standalone-CLI.
    - `logging` statt `print`.
    - Dedup-Hash wird pro Lauf frisch aufgebaut (kein modul-globaler Zustand,
      der über Läufe hinweg "leakt").
    - Typisierte Dataclass-Ergebnisse mit `.to_dict()` (Stil-konsistent).
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_HASH_CHUNK_BYTES = 1024 * 1024  # erste 1 MB – schnell & in der Praxis kollisionsarm
_FILENAME_PREFIX = "UNREEL_"
_TS_FORMAT = "%Y%m%d_%H%M%S"
# Audio-only extensions are music tracks, not clips → include in file list but never rename.
_AUDIO_ONLY_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}



@dataclass
class IngestResult:
    """Ergebnis eines Ingestion-Laufs über einen Ordner."""
    renamed: list[tuple[str, str]] = field(default_factory=list)  # (alt, neu)
    duplicates_removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)   # (datei, grund)
    final_files: list[str] = field(default_factory=list)          # Pfade nach dem Lauf

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


def _is_supported(path: Path) -> bool:
    if path.name.startswith("._"):
        return False
    exts = {e.lower() for e in config.SUPPORTED_EXTENSIONS}
    return path.suffix.lower() in exts


def _quick_hash(path: Path) -> str | None:
    """Dedup-Signatur: '<groesse>_<md5(erste 1MB)>'. None bei Lesefehler."""
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            chunk = f.read(_HASH_CHUNK_BYTES)
        return f"{size}_{hashlib.md5(chunk).hexdigest()}"
    except OSError as e:
        logger.warning("Hash fehlgeschlagen für %s: %s", path.name, e)
        return None


def _read_creation_time(path: Path) -> datetime:
    """
    Echter Aufnahme-Zeitstempel aus den Metadaten (ffprobe creation_time).
    Fallback-Reihenfolge: ffprobe -> Datei-mtime -> jetzt.
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "format_tags=creation_time",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ]
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=10
        ).strip()
        if out:
            # "2025-06-12T14:30:00.000000Z" -> erste 19 Zeichen reichen
            return datetime.strptime(out[:19], "%Y-%m-%dT%H:%M:%S")
    except (subprocess.SubprocessError, ValueError, OSError) as e:
        logger.debug("ffprobe creation_time nicht lesbar für %s: %s", path.name, e)

    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return datetime.now()


def _target_name(path: Path, seen_targets: set[str]) -> Path:
    """
    Liefert den Ziel-Pfad UNREEL_YYYYMMDD_HHMMSS<ext>, kollisionsfrei.
    `seen_targets` verhindert Kollisionen auch innerhalb desselben Laufs.
    """
    ts = _read_creation_time(path).strftime(_TS_FORMAT)
    ext = path.suffix.lower()
    base = f"{_FILENAME_PREFIX}{ts}"
    candidate = path.with_name(f"{base}{ext}")

    counter = 1
    while (candidate.exists() and candidate != path) or str(candidate) in seen_targets:
        candidate = path.with_name(f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def ingest_directory(source_dir: str | Path | None = None) -> IngestResult:
    """
    Verarbeitet alle unterstützten Videos in `source_dir`:
      1. Duplikate löschen, 2. nach UNREEL_<timestamp> umbenennen.

    Bereits korrekt benannte Dateien (Prefix UNREEL_) werden nicht erneut
    umbenannt, aber weiterhin auf Duplikate geprüft.

    Returns:
        IngestResult mit Umbenennungen, gelöschten Duplikaten, Fehlern und
        der finalen Dateiliste (Pfade), die die Pipeline weiterverarbeitet.
    """
    source_dir = Path(source_dir or config.VIDEO_SOURCE_DIR)
    result = IngestResult()

    if not source_dir.exists():
        logger.warning("Input-Ordner existiert nicht: %s", source_dir)
        return result

    seen_hashes: dict[str, Path] = {}   # signatur -> behaltener Pfad
    seen_targets: set[str] = set()      # bereits vergebene Ziel-Pfade (dieser Lauf)

    for path in sorted(source_dir.iterdir()):
        if not path.is_file() or not _is_supported(path):
            result.skipped.append(str(path))
            continue

        # 1) Dedup
        sig = _quick_hash(path)
        if sig is None:
            result.errors.append((str(path), "hash failed"))
            continue
        if sig in seen_hashes:
            try:
                path.unlink()
                result.duplicates_removed.append(str(path))
                logger.info("Duplikat entfernt: %s (== %s)",
                            path.name, seen_hashes[sig].name)
            except OSError as e:
                result.errors.append((str(path), f"delete failed: {e}"))
            continue
        seen_hashes[sig] = path

        # 2) Rename (nur wenn nötig)
        if path.name.startswith(_FILENAME_PREFIX):
            result.final_files.append(str(path))
            seen_targets.add(str(path))
            continue

        # Audio-only files are music tracks – keep original name, don't rename.
        if path.suffix.lower() in _AUDIO_ONLY_EXTENSIONS:
            result.final_files.append(str(path))
            seen_targets.add(str(path))
            logger.info("Audio-Track beibehalten (kein Rename): %s", path.name)
            continue


        target = _target_name(path, seen_targets)
        try:
            path.rename(target)
            result.renamed.append((str(path), str(target)))
            seen_hashes[sig] = target
            seen_targets.add(str(target))
            result.final_files.append(str(target))
            logger.info("Umbenannt: %s -> %s", path.name, target.name)
        except OSError as e:
            result.errors.append((str(path), f"rename failed: {e}"))
            result.final_files.append(str(path))  # trotzdem weiterverarbeiten

    logger.info(
        "Ingestion fertig: %d umbenannt, %d Duplikate entfernt, %d Fehler",
        len(result.renamed), len(result.duplicates_removed), len(result.errors),
    )
    return result


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="UNREEL Ingestion & Renaming (Phase 0)")
    parser.add_argument("source", nargs="?", default=None,
                        help="Input-Ordner (Default: config.VIDEO_SOURCE_DIR)")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    args = parser.parse_args()

    res = ingest_directory(args.source)
    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"  Umbenannt:          {len(res.renamed)}")
        print(f"  Duplikate entfernt: {len(res.duplicates_removed)}")
        print(f"  Fehler:             {len(res.errors)}")
        print(f"  Dateien bereit:     {len(res.final_files)}")

\\n
### \kick_snare_detector.py\n
\\python
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

\\n
### \lut_generator.py\n
\\python
"""
UNREEL V3 – LUT Generator
Programmatically generates .cube LUT files for underground techno color grading.
Replaces the previous eq-filter approach with professional 3D-LUT color grading.

Usage:
    python -m analyzer.lut_generator
    → Generates all .cube files into luts/
"""

import os
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# LUT configuration
# ---------------------------------------------------------------------------
LUT_DIR = Path(__file__).resolve().parent / "luts"
LUT_SIZE = 33  # 33x33x33 cube – standard for most NLEs and FFmpeg

# ---------------------------------------------------------------------------
# Color math helpers
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: float) -> float:
    """Convert sRGB [0,1] to linear [0,1]."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    """Convert linear [0,1] to sRGB [0,1]."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# LUT transform functions (input: R,G,B in [0,1] → output: R,G,B in [0,1])
# ---------------------------------------------------------------------------

def _transform_underground_dark(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Underground Dark Techno Look:
    - Crushed blacks (lift shadows into near-black)
    - Cyan/teal shadow tint
    - Desaturated midtones
    - Slightly warm highlights
    - Overall contrast boost
    """
    # Convert to linear for processing
    rl, gl, bl = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)

    # Step 1: Crush blacks – apply a power curve to push shadows down
    crush_power = 1.4
    rl = rl ** crush_power
    gl = gl ** crush_power
    bl = bl ** crush_power

    # Step 2: Desaturate (mix towards luminance)
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    desat_amount = 0.35
    rl = rl * (1 - desat_amount) + lum * desat_amount
    gl = gl * (1 - desat_amount) + lum * desat_amount
    bl = bl * (1 - desat_amount) + lum * desat_amount

    # Step 3: Cyan tint in shadows (add blue-green to low values)
    cyan_strength = 0.08
    shadow_mask = max(0.0, 1.0 - lum * 3.0)  # fades out in midtones
    bl += cyan_strength * shadow_mask
    gl += cyan_strength * 0.3 * shadow_mask

    # Step 4: Warm tint in highlights
    highlight_mask = max(0.0, (lum - 0.5) * 2.0)
    rl += 0.03 * highlight_mask

    # Step 5: Contrast S-curve (in linear)
    contrast = 1.15
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_vhs_analog(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    VHS Analog Look:
    - Color bleed (red channel shifted)
    - Raised blacks (milky shadows)
    - Reduced contrast
    - Slight green color cast
    - Faded highlights
    """
    rl, gl, bl = r, g, b  # Work in sRGB for this one

    # Step 1: Raise blacks
    black_lift = 0.06
    rl = rl * 0.92 + black_lift
    gl = gl * 0.92 + black_lift
    bl = bl * 0.92 + black_lift

    # Step 2: Color bleed – shift red channel slightly (simulate chroma shift)
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    rl = rl * 0.9 + lum * 0.1  # Red bleeds towards luminance

    # Step 3: Green/warm cast
    gl += 0.02
    bl -= 0.01

    # Step 4: Reduce contrast
    contrast = 0.85
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    # Step 5: Desaturate slightly
    desat = 0.15
    rl = rl * (1 - desat) + lum * desat
    gl = gl * (1 - desat) + lum * desat
    bl = bl * (1 - desat) + lum * desat

    # Step 6: Clip highlights (faded look)
    rl = min(rl, 0.95)
    gl = min(gl, 0.95)
    bl = min(bl, 0.95)

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_neon_nights(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Neon Nights Look:
    - Crushed blacks
    - Highly saturated colors
    - Magenta/blue highlight tint
    - Electric feel for light show clips
    """
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)

    # Step 1: Crush blacks hard
    rl = max(0, (rl - 0.05)) ** 1.3
    gl = max(0, (gl - 0.05)) ** 1.3
    bl = max(0, (bl - 0.05)) ** 1.3

    # Step 2: Boost saturation significantly
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    sat_boost = 1.5
    rl = lum + (rl - lum) * sat_boost
    gl = lum + (gl - lum) * sat_boost
    bl = lum + (bl - lum) * sat_boost

    # Step 3: Magenta/blue tint in highlights
    highlight_mask = max(0.0, (lum - 0.3) * 1.5)
    rl += 0.04 * highlight_mask
    bl += 0.06 * highlight_mask

    # Step 4: Strong contrast
    contrast = 1.25
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_tech_noir(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Tech-Noir Look (tarantino preset flashback):
    - Near-monochrome (heavy desaturation), cold industrial tint
    - Very high contrast with crushed blacks and clipped highlights
    - For the daytime/outdoor flashback: cold, mechanical, almost B&W

    Works in sRGB space directly (no linear round-trip) so the contrast
    curve reads as a hard, photographic S-curve.
    """
    # Step 1: luminance (Rec.709)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Step 2: heavy desaturation toward luma (0.15 = near-monochrome)
    sat = 0.15
    r = lum + (r - lum) * sat
    g = lum + (g - lum) * sat
    b = lum + (b - lum) * sat

    # Step 3: cold industrial tint (lift blue, drop red slightly)
    r *= 0.96
    b *= 1.08

    # Step 4: hard S-curve – crush shadows, then expand contrast around 0.5
    contrast = 1.6

    def _scurve(c: float) -> float:
        c = max(0.0, c - 0.04)            # crush shadows
        return 0.5 + (c - 0.5) * contrast  # expand contrast

    return _clamp(_scurve(r)), _clamp(_scurve(g)), _clamp(_scurve(b))


# ---------------------------------------------------------------------------
# .cube file writer
# ---------------------------------------------------------------------------

def _generate_cube_file(
    transform_fn,
    output_path: Path,
    lut_name: str,
    size: int = LUT_SIZE,
) -> None:
    """Generate an Adobe .cube LUT file from a transform function."""
    total_entries = size ** 3
    print(f"Generating '{lut_name}' ({size}^3 = {total_entries} entries)...")

    with open(output_path, "w") as f:
        # Header
        f.write(f'TITLE "{lut_name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write("\n")

        # Generate LUT entries
        # .cube format iterates: R changes fastest, then G, then B
        for b_idx in range(size):
            for g_idx in range(size):
                for r_idx in range(size):
                    r_in = r_idx / (size - 1)
                    g_in = g_idx / (size - 1)
                    b_in = b_idx / (size - 1)

                    r_out, g_out, b_out = transform_fn(r_in, g_in, b_in)

                    # Convert linear back to sRGB for underground/neon transforms
                    if transform_fn in (_transform_underground_dark, _transform_neon_nights):
                        r_out = _linear_to_srgb(r_out)
                        g_out = _linear_to_srgb(g_out)
                        b_out = _linear_to_srgb(b_out)

                    f.write(f"{r_out:.6f} {g_out:.6f} {b_out:.6f}\n")

    size_kb = output_path.stat().st_size / 1024
    print(f"  Written to {output_path} ({size_kb:.0f} KB)")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_luts(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate all LUT files. Returns dict of {name: path}."""
    out = output_dir or LUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    luts = {
        "underground_dark": (_transform_underground_dark, out / "underground_dark.cube"),
        "vhs_analog": (_transform_vhs_analog, out / "vhs_analog.cube"),
        "neon_nights": (_transform_neon_nights, out / "neon_nights.cube"),
        "tech_noir": (_transform_tech_noir, out / "tech_noir.cube"),
    }

    for name, (fn, path) in luts.items():
        _generate_cube_file(fn, path, name)

    return {name: path for name, (_, path) in luts.items()}


def get_lut_path(lut_name: str, lut_dir: Path | None = None) -> Path:
    """Resolve a LUT name to its .cube file path."""
    d = lut_dir or LUT_DIR
    path = d / f"{lut_name}.cube"
    if not path.exists():
        raise FileNotFoundError(f"LUT file not found: {path}. Run lut_generator first.")
    return path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("UNREEL V3 – LUT Generator")
    print("=" * 40)
    paths = generate_all_luts()
    print(f"\nDone. Generated {len(paths)} LUT files in {LUT_DIR}/")

\\n
### \main.py\n
\\python
import sys
import subprocess
from pathlib import Path

# Simply delegate to the src.main module
if __name__ == "__main__":
    # Ensure project root is in path
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    
    from src.main import main
    main()

\\n
### \regie_engine.py\n
\\python
"""
UNREEL V3 – Regie Engine (Multi-Provider)
Uses Claude Fable 5, Gemini 3.1 Pro, or DeepSeek V4 Pro as the creative director
to plan millisecond-precise edits based on audio/video analysis metadata.
Generates structured edit plans (Schnittlisten) with automatic provider fallback.

Usage:
    from analyzer.regie_engine import generate_edit_plan, verify_edit_plan
    plan = generate_edit_plan(analysis_data, preset="highlight", duration=60)

    # Explicit provider:
    plan = generate_edit_plan(data, provider="gemini")
    plan = generate_edit_plan(data, provider="deepseek")
    plan = generate_edit_plan(data, provider="claude")

CLI:
    python -m analyzer.regie_engine analysis.json --provider gemini --preset highlight
"""

import importlib.util
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Protocol

from analyzer.local_regie_provider import LocalMLXProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (loaded from config module / .env)
# ---------------------------------------------------------------------------

from config import (
    REGIE_PROVIDER,
    REGIE_PROVIDER_FALLBACK_ORDER,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_BASE_URL,
)

# ---------------------------------------------------------------------------
# SDK availability helper
# ---------------------------------------------------------------------------

def _sdk_installed(module_name: str) -> bool:
    """True if the given SDK module can be imported (without importing it)."""
    return importlib.util.find_spec(module_name) is not None


# ---------------------------------------------------------------------------
# Data classes (shared across all providers)
# ---------------------------------------------------------------------------

@dataclass
class EditClip:
    """A single clip in the edit plan."""
    video: str
    start: float
    end: float
    transition: str
    reason: str
    crop: str = "9:16"
    lut: str = "underground_dark"
    vfx: str = "none"
    slow_mo: bool = False
    slow_mo_factor: float = 1.0
    phase: str = ""  # Story phase for pov_story preset: "before" | "during" | "after"

    def to_dict(self) -> dict:
        return {
            "video": self.video,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.end - self.start, 3),
            "transition": self.transition,
            "reason": self.reason,
            "crop": self.crop,
            "lut": self.lut,
            "vfx": self.vfx,
            "slow_mo": self.slow_mo,
            "slow_mo_factor": self.slow_mo_factor,
            "phase": self.phase,
        }

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class EditPlan:
    """Complete edit plan generated by AI."""
    clips: list[EditClip]
    narrative: str
    total_duration: float
    target_bpm: float = 0.0
    style: str = "highlight"
    hook_text: str = ""           # Anti-advice hook line (pov_story preset, first ~3s)
    provider_used: str = ""       # Which AI generated this plan
    model_used: str = ""          # Exact model identifier
    generation_time_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "clips": [c.to_dict() for c in self.clips],
            "narrative": self.narrative,
            "hook_text": self.hook_text,
            "total_duration": round(self.total_duration, 3),
            "target_bpm": self.target_bpm,
            "style": self.style,
            "clip_count": len(self.clips),
            "provider_used": self.provider_used,
            "model_used": self.model_used,
            "generation_time_s": round(self.generation_time_s, 2),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Edit plan saved to {path}")

    def to_ffmpeg_commands(self, output_dir: Path = Path("output")) -> list[str]:
        """Convert the edit plan to FFmpeg command strings for execution."""
        commands = []
        for i, clip in enumerate(self.clips):
            vf_parts = []

            if clip.crop == "9:16":
                vf_parts.append("crop=ih*9/16:ih,scale=1080:1920")
            elif clip.crop == "16:9":
                vf_parts.append("scale=1920:1080")

            if clip.lut and clip.lut != "none":
                vf_parts.append(f"lut3d=luts/{clip.lut}.cube")

            if clip.slow_mo and clip.slow_mo_factor > 1.0:
                vf_parts.insert(0, f"setpts=PTS*{clip.slow_mo_factor}")

            # Beat-reactive VFX (applied at start of clip)
            if clip.vfx == "flash":
                vf_parts.append("eq=brightness=1.5:enable='between(t,0,0.2)'")
            elif clip.vfx == "pump":
                vf_parts.append("zoompan=z='min(max(zoom,pzoom)+0.03,1.05)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:enable='between(t,0,0.3)'")

            vf = ",".join(vf_parts) if vf_parts else None

            output_name = f"snippet_{i + 1:03d}_{Path(clip.video).stem}.mp4"
            output_path = output_dir / output_name

            cmd_parts = [
                "ffmpeg", "-y",
                "-ss", f"{clip.start:.3f}",
                "-to", f"{clip.end:.3f}",
                "-i", clip.video,
            ]
            if vf:
                cmd_parts.extend(["-vf", vf])
            cmd_parts.extend([
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                str(output_path),
            ])
            commands.append(" ".join(cmd_parts))

        return commands


# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------

class RegieProvider(Protocol):
    """Interface that all AI providers must implement."""

    @property
    def name(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def is_available(self) -> bool: ...

    def call(
        self,
        system_prompt: str,
        user_data: str,
        temperature: float = 0.4,
        max_tokens: int = 8192,
    ) -> str: ...


# ---------------------------------------------------------------------------
# Provider: Claude Fable 5 (Anthropic)
# ---------------------------------------------------------------------------

class ClaudeProvider:
    """Anthropic Claude provider – Claude Fable 5."""

    def __init__(
        self,
        api_key: str = ANTHROPIC_API_KEY,
        model: str = CLAUDE_MODEL,
    ):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "claude"

    @property
    def model_id(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return bool(self._api_key) and _sdk_installed("anthropic")

    def call(
        self,
        system_prompt: str,
        user_data: str,
        temperature: float = 0.4,
        max_tokens: int = 8192,
    ) -> str:
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic not installed. Run: pip install anthropic")

        client = anthropic.Anthropic(api_key=self._api_key)

        logger.info(f"  → Calling {self._model} (Anthropic)...")

        params = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_data}],
            temperature=temperature,
        )
        try:
            response = client.messages.create(**params)
        except anthropic.BadRequestError as exc:
            # Newer models (e.g. Fable 5) reject `temperature`; retry without it.
            if "temperature" in str(exc).lower():
                params.pop("temperature", None)
                response = client.messages.create(**params)
            else:
                raise

        # Fable 5 (and any model with extended thinking) returns thinking
        # blocks before the answer, so pick text blocks only — never content[0].
        text = "".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        )
        return text


# ---------------------------------------------------------------------------
# Provider: Gemini 3.1 Pro (Google)
# ---------------------------------------------------------------------------

class GeminiProvider:
    """Google Gemini provider – Gemini 3.1 Pro."""

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
    ):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_id(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return bool(self._api_key) and _sdk_installed("google.generativeai")

    def call(
        self,
        system_prompt: str,
        user_data: str,
        temperature: float = 0.4,
        max_tokens: int = 8192,
    ) -> str:
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY not set")

        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

        genai.configure(api_key=self._api_key)

        model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",  # Force JSON output
            ),
        )

        logger.info(f"  → Calling {self._model} (Google Gemini)...")

        response = model.generate_content(user_data)

        return response.text


# ---------------------------------------------------------------------------
# Provider: DeepSeek V4 Pro
# ---------------------------------------------------------------------------

class DeepSeekProvider:
    """DeepSeek provider – V4 Pro via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str = DEEPSEEK_API_KEY,
        model: str = DEEPSEEK_MODEL,
        base_url: str = DEEPSEEK_BASE_URL,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def model_id(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return bool(self._api_key) and _sdk_installed("openai")

    def call(
        self,
        system_prompt: str,
        user_data: str,
        temperature: float = 0.4,
        max_tokens: int = 8192,
    ) -> str:
        if not self._api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")

        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

        logger.info(f"  → Calling {self._model} (DeepSeek)...")

        response = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},  # Force JSON
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data},
            ],
        )

        return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Provider Registry & Resolution
# ---------------------------------------------------------------------------

def get_provider(provider_name: str = "") -> RegieProvider:
    """
    Instantiate a provider by name. Empty string uses REGIE_PROVIDER from config.
    Raises ValueError if the provider is not available (missing API key).
    """
    name = provider_name or REGIE_PROVIDER
    name = name.lower().strip()

    providers: dict[str, type] = {
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
        "local": LocalMLXProvider,
    }

    if name not in providers:
        raise ValueError(f"Unknown provider '{name}'. Choose from: {', '.join(providers)}")

    return providers[name]()


def resolve_provider(provider_name: str = "") -> RegieProvider:
    """
    Resolve the active provider. Handles "auto" mode by trying each provider
    in fallback order until one with a configured API key is found.
    """
    name = (provider_name or REGIE_PROVIDER).lower().strip()

    if name != "auto":
        provider = get_provider(name)
        if not provider.is_available():
            raise ValueError(
                f"Provider '{name}' is not available – "
                f"the required API key is not set in .env or environment."
            )
        return provider

    # Auto mode: try each provider in fallback order
    logger.info(f"Auto-selecting provider (fallback order: {' → '.join(REGIE_PROVIDER_FALLBACK_ORDER)})...")

    for candidate_name in REGIE_PROVIDER_FALLBACK_ORDER:
        try:
            provider = get_provider(candidate_name)
            if provider.is_available():
                logger.info(f"  ✓ Selected: {provider.name} ({provider.model_id})")
                return provider
            else:
                logger.debug(f"  ✗ {candidate_name}: API key not set")
        except Exception as e:
            logger.debug(f"  ✗ {candidate_name}: {e}")

    raise ValueError(
        "No AI provider available. Set at least one API key in .env:\n"
        "  ANTHROPIC_API_KEY=...  (Claude Fable 5)\n"
        "  GEMINI_API_KEY=...     (Gemini 3.1 Pro)\n"
        "  DEEPSEEK_API_KEY=...   (DeepSeek V4 Pro)\n"
        "Or set REGIE_PROVIDER=local to use the local model."
    )


def list_available_providers() -> list[dict]:
    """List all providers and their availability status."""
    result = []
    for name, cls in [("claude", ClaudeProvider), ("gemini", GeminiProvider), ("deepseek", DeepSeekProvider), ("local", LocalMLXProvider)]:
        provider = cls()
        result.append({
            "name": name,
            "model": provider.model_id,
            "available": provider.is_available(),
        })
    return result


# ---------------------------------------------------------------------------
# System prompt builder (shared across all providers)
# ---------------------------------------------------------------------------

_POV_STORY_SECTION = """
POV / "A DAY IN THE LIFE" STORY MODE (preset = pov_story) — this OVERRIDES the generic editing rules above.
This is a story-driven, POV vlog-style reel, NOT a beat-cut highlight montage. Build a mini narrative across
three phases of a gig:
  - "before": arriving, getting ready, soundcheck, backstage, nerves, walking to the booth (ARRIVAL / BACKSTAGE / DJ_SETUP)
  - "during": the actual set — mixing, the drop, the crowd reacting (CROWD_ENERGY / LIGHT_SHOW / DJ_SETUP)
  - "after": the comedown — last track, packing up, crowd leaving, the quiet after (PACKDOWN / BACKSTAGE / BREAKDOWN)

POV STORY RULES:
1. DO use ARRIVAL, PACKDOWN and BACKSTAGE clips here — they carry the "before" and "after" story. The generic "avoid BACKSTAGE" rule does NOT apply. ARRIVAL strongly signals "before"; PACKDOWN strongly signals "after".
2. Order clips chronologically as a narrative: before -> during -> after. Set each clip's "phase" field accordingly.
3. Cuts may be motivated by story beats, not only kicks/snares. Pacing: slower (before) -> peak (during) -> settle (after).
4. Establishing clips in "before"/"after" may run a bit longer (up to ~6s); keep the "during" phase punchy.
5. The FIRST clip is the HOOK (first ~3 seconds) and MUST stop the scroll.

ANTI-ADVICE HOOK (REQUIRED — put it in the top-level "hook_text" field):
Write ONE short, punchy on-screen text line for the first 3 seconds. It is "anti-advice": deliberately
contrarian / counterintuitive / provocative — the OPPOSITE of a polite tip. Bait the viewer by challenging
conventional DJ wisdom or undercutting expectations. Under ~60 characters, no hashtags, no emojis.
Match this energy (do NOT copy verbatim):
  - "stop practicing your transitions."
  - "nobody cares about your warm-up set."
  - "POV: ignored every DJ tip and still packed the floor"
  - "the crowd doesn't want your 'journey'."
Make the hook thematically connect to what actually happens in the chosen clips.
"""


_TARANTINO_SECTION = """
TARANTINO / PERSONALISED RETENTION-PIPELINE MODE (preset = tarantino) — this OVERRIDES the generic editing rules above.
This is a precision‑timed reel based on the four‑phase "Retention‑Pipeline" dramaturgy.
The reel is exactly 30 seconds long. The analysis data includes "music_analysis" with "drop_times",
where each entry is an object {"time": seconds, "intensity": 0..1}.
If a drop exists, the final drop time = drop_times[0].time (the "time" field of the FIRST entry) and
phase 4 (escalation) MUST start exactly at that time.
If no music_analysis is present, the default final drop time is 12.0s.

ABSOLUTE TIMELINE (each clip's "phase" field must be set accordingly):

1. "hook" (0.0s – 3.0s) — PATTERN INTERRUPT (BEAT-SYNC, 1/4 NOTES)
   START IN MEDIA RES. No intro, no warning – fire the most intense club shot instantly.
   EVERY kick drum = ONE cut. That is fast enough to show energy, but still readable.
   Content: deep red light, strobes, you at the decks, crowd going off (CROWD_ENERGY / LIGHT_SHOW).
   Clip duration: multiples of a 1/4 note at the track BPM (use subdivision_grid). 
   LUT: "underground_dark" or "neon_nights". VFX: "flash" on the hardest hit.

2. "flashback" (3.0s – 8.0s) — DOPAMIN RESET (HALF-TIME, 1/2 NOTES TO WHOLE BARS)
   HARD CONTRAST to the hook. Drop visual energy drastically. Use long, stoic, almost monochrome shots
   (train, walking, field, outdoor). Let clips breathe for 2 beats (1/2 note) or even 4 beats (one bar).
   The quiet images feel oppressive because the muffled bass (J‑cut lowpass) rumbles underneath.
   Content: ARRIVAL / BACKSTAGE / outdoor. Chronological backstory.
   Clip duration: "1/2_half" or "1/1_bar" values from subdivision_grid. NO fast cutting here.
   LUT: "tech_noir" (cold, monochrome, high-contrast). VFX: "none".

3. "buildup" (8.0s – 12.0s) — SNARE‑ROLL ACCELERATION (1/4 → 1/8 NOTES)
   The track rolls toward the drop. Mirror the tension with accelerating cut frequency.
   START with 1/4‑note cuts, and in the LAST TWO BARS before the drop switch to double‑time (1/8 notes).
   This is the visual "snare roll" – the rhythm tightens exactly as the music does.
   Content: branding shots – artist unapproachable: hands on mixer, adjusting glasses, looking into
   camera, back shots (DJ_SETUP). Cut them rhythmically, getting faster.
   LUT: "tech_noir". The LAST clip that transitions into Phase 4 → VFX: "glitch" (black‑frame stutter).

4. "escalation" (12.0s – 30.0s) — DOUBLE‑TIME MASSACRE (1/8 BASE + 1/16 GLITCHES)
   THE DROP. Bass hits, filter opens. Full 1/8‑note cutting as baseline.
   For absolute peaks (drops, strobes) insert ultra‑short 1/16‑note micro‑cuts (≈0.1s) – percussive
   visual glitches, not meant to be fully readable, just felt.
   Content: hands on XONE mixer, sweating crowd, strobes, chaos (CROWD_ENERGY / LIGHT_SHOW / DJ_SETUP).
   LUT: "underground_dark" / "neon_nights". VFX: "pump" on driving kicks, "flash" on hardest drops.

MUSIC DROP ALIGNMENT:
If music_analysis.drop_times is available, the "final drop" time = drop_times[0].time
(each drop_times entry is {"time": seconds, "intensity": 0..1}).
Phase 3 (buildup) ends at the later of 12.0s or (drop_time – 2.0s) – this ensures at least
two bars of buildup before the drop. Phase 4 (escalation) starts at drop_time and stretches
to 30.0s. If no drop_time, default drop = 12.0s.

DURATION MATH:
The reel is exactly 30.0s. The four phases occupy:
  hook:        0.0 –  3.0 = 3.0s  (fixed)
  flashback:   3.0 –  8.0 = 5.0s  (fixed)
  buildup:     8.0 – drop_time   = variable (minimum 4.0s)
  escalation:  drop_time – 30.0  = variable (at least 4.0s)
If drop_time < 8.0, clamp buildup start to 8.0 (so phase 2 stays intact) and let escalation
absorb the remaining time.

MATCH CUTS (Bewegungsschnitt):
The analysis data field "clip_scenes" maps each clip filename to {"tags", "scenes"} where "scenes"
are short per-frame descriptions. USE these descriptions to find pairs of clips with similar motion.
Find SIMILAR MOVEMENTS across different scenes and cut IN THE MIDDLE OF THE MOTION:
- Adjusting glasses/hat outdoors → hand reaching for the XONE mixer or CDJs in the club
- Walking forward on the street → leaning forward over the decks
- Arm gesture in daylight → arm raised in the crowd
- Turning head outdoors → turning to look at the crowd
Use 1–3 match cuts per reel, preferably at phase boundaries (flashback→buildup, buildup→escalation).
Set "transition": "match_cut" and describe the movement connection in "reason".

COLOR RULES:
- "flashback" + "buildup" clips → LUT: "tech_noir" (cold, industrial, near‑monochrome).
- "hook" + "escalation" clips (club) → LUT: "underground_dark" or "neon_nights".
HARD CUTS ONLY. No crossfades. The aesthetic is brutalist and abrupt.
"""



_ARTIST_NARRATIVE_SECTION = """
ARTIST-NARRATIVE / STORY-WEAPON MODE (preset = artist_narrative) — OVERRIDES the generic rules.
Goal: REACH. Turn the gig's backstory (train ride, walking, crew moments) into a story with a sharp,
often sarcastic or "deep" take on DJ life. The viewer should feel they are on a MISSION with you.
Retention pipeline: bait in 3s → make them feel the grind → pay it off with the drop.

ANTI-ADVICE / "POV" HOOK (REQUIRED — put it in the top-level "hook_text" field):
ONE punchy on-screen line for the first 3s, sarcastic/deep, contrasting the grind with the reward.
Under ~70 chars, no hashtags/emojis. Match this energy (do NOT copy verbatim):
  - "POV: 6h Zugfahrt für ein 90-Minuten-Set im roten Bereich."
  - "niemand sieht die 8 Stunden vorher. nur die 8 Sekunden danach."
  - "the train was late. the drop wasn't."

PHASES (set each clip's "phase"):
1. "hook" (0–3s): the text hook over a grabbing image — can be a quiet/tense travel shot OR a flash of
   the club to come. Establish the contrast immediately.
2. "journey" (3s → drop): the grind, CHRONOLOGICAL — train, walking, van, soundcheck, crew (ARRIVAL /
   BACKSTAGE / outdoor). DESATURATED, mechanical, cold. LUT: "tech_noir". Cuts on the beat but the
   muffled bass (J-cut) rumbles underneath. Energy deliberately suppressed.
3. "escalation" (drop → end): EXPLODE into the club exactly at music drop_times[0].time. Strobes, crowd,
   decks, full energy (CROWD_ENERGY / LIGHT_SHOW). LUT: "underground_dark" / "neon_nights".
The LAST "journey" clip before the club → VFX: "glitch". VFX: "flash" on the hardest club hit.
HARD CUTS. The contrast quiet→explosion is the whole point.
"""

_BOOKING_SECTION = """
BOOKING / PROMOTER-SHOWCASE MODE (preset = booking) — OVERRIDES the generic rules.
This is a DIGITAL BUSINESS CARD for club owners / promoters. In 10 seconds they must see: this artist is
professional, the floor is PACKED, the energy fits. NO private moments, NO funny train scenes, NO journey.
Pure, uncompromising professionalism and escalation.

RULES:
- Content ONLY: technique at the mixer (hands on XONE / Pioneer / CDJs, DJ_SETUP) intercut with WIDE shots
  of the packed, celebrating crowd (CROWD_ENERGY / LIGHT_SHOW). EXCLUDE ARRIVAL / BACKSTAGE / outdoor /
  travel / goofing-around clips entirely.
- FRONT-LOAD the single most impressive crowd/energy moment in the first 3s (retention) — no slow intro.
- Fast, precise, confident cuts on kicks/snares. Tight, never sloppy. Keep energy HIGH the whole time,
  no comedown. If music_analysis exists, peak the cut frequency around drop_times[0].time.
- LUT: "underground_dark" or "neon_nights" (club look only — NEVER "tech_noir", there is no journey).
- VFX: "flash" / "pump" on hits. No "glitch" (that signals a scene change; here it's all one world).
- "hook_text" stays "" — this sells through pure visual professionalism, not a text gimmick.
Set each clip's "phase": "opener" | "showcase" | "peak".
"""

_COMMUNITY_SECTION = """
COMMUNITY / BEHIND-THE-SCENES MODE (preset = community) — OVERRIDES the generic rules.
For the existing fanbase: the jokes on the train, messing around with the crew, the unfiltered reality
before and after the gig. Build a real, approachable bond. Show the contrast between "private Patrick"
and the "unapproachable machine DAY SHØ" behind the decks.

RULES:
- USE the human clips: ARRIVAL, BACKSTAGE, PACKDOWN, crew moments, candid/outdoor. The generic
  "avoid BACKSTAGE" rule does NOT apply — these ARE the content.
- CHRONOLOGICAL and looser pacing — NOT a brutalist beat-massacre. Clips may breathe (up to ~6s).
  Cuts can follow story beats, not only kicks.
- The KEY beat: at least one HARD contrast cut from a candid/goofy private moment straight into a
  focused, intense behind-the-decks shot (the "Patrick → DAY SHØ" flip). Consider VFX "glitch" there.
- Warmer, natural look: LUT "vhs_analog" for the candid/BTS moments, "underground_dark" for the booth.
- Retention: still open with the most charming/funny 3s so the fan stops scrolling.
- "hook_text" optional — a light, personal line (e.g. "die jungs vs. das set."). "" is fine.
Set each clip's "phase": "before" | "during" | "after" (chronological).
"""


def _build_system_prompt(preset: str, duration: float, target_bpm: float = 0) -> str:
    """Build the system prompt for the regie AI task."""
    sections = {
        "pov_story": _POV_STORY_SECTION,
        "tarantino": _TARANTINO_SECTION,
        "artist_narrative": _ARTIST_NARRATIVE_SECTION,
        "booking": _BOOKING_SECTION,
        "community": _COMMUNITY_SECTION,
    }
    preset_section = sections.get(preset, "")

    return f"""You are an expert video editor and creative director specializing in techno/electronic music content for Instagram Reels.

Your task: Create a precise, millisecond-accurate edit plan for a DJ video reel.

EDIT SPECIFICATIONS:
- Target duration: {duration} seconds
- Preset style: {preset}
- Target BPM: {target_bpm or "auto-detect"}
- Output format: 9:16 (1080x1920) for Instagram Reels
- Color grading: 3D-LUT underground techno look

EDITING RULES:
1. Every cut MUST land on a beat, kick, snare, or drop timestamp
2. Build dramatic tension: start calm → build up → peak at drops → cool down
3. Prioritize CROWD_ENERGY and LIGHT_SHOW tags for peak moments
4. Avoid UNUSABLE and BACKSTAGE segments
5. Use hard cuts on kicks/snares for energy, crossfades for transitions
6. Keep individual clips between 2-8 seconds (reels need fast pacing)
7. If a clip has high motion (>0.8), consider slow-motion (setpts=PTS*2.0)
8. VFX rules: Use "vfx": "flash" on the hardest drops. Use "vfx": "pump" on driving kicks. Use "vfx": "glitch" on a clip that marks a hard scene change (e.g. the cut from daytime/outdoor footage into the dark club) for a machine-like black-frame stutter. Otherwise "none".
9. The last clip should create a seamless loop feel if possible
10. The analysis JSON includes "clip_durations" (real length of each source file in seconds). NEVER set a clip's "end" beyond its source duration.
11. **Per‑clip audio analysis**: Each video in phase_2 may contain an "audio_analysis" dict with: tempo, beat_times, bass_drops, buildups, breakdowns, energy_envelope, energy_times. Use these to align cuts to that specific video's kicks/beats. If a video lacks audio_analysis, fall back to the global beat grid.
12. **Music track analysis** (optional): If present in music_analysis, it contains: bpm, kick_times, drop_times, beat_times. You may align cuts to the music track for a tighter sync between the reel and the background audio. If both per‑clip and music track data exist, prefer per‑clip data for the video's own cuts, but use music track data for the overall pacing and drop alignment.

PRESET DEFINITIONS:
- "highlight": Best moments, high energy, fast cuts, 60-90s
- "drop_focus": Centered around drops, build-up → drop → aftermath
- "seamless_loop": Short (15-30s), end flows back to start
- "moody": Slower cuts, atmospheric, BREAKDOWN + LIGHT_SHOW heavy
- "pov_story": POV / "A Day in the Life" — story-driven vlog reel (before → during → after a gig) with an anti-advice text hook in the first 3s
- "tarantino": Non-linear, brutalist techno edit — climax first (in media res), then chronological flashback (tech-noir, hard beat-cuts), buildup, escalation
- "artist_narrative": Story-weapon for reach — sarcastic/deep POV hook, desaturated grind (journey), then explode into the club at the drop
- "booking": Promoter showcase / business card — pure professionalism, mixer technique + packed crowd, no private scenes, relentless escalation
- "community": Behind-the-scenes for fans — chronological, looser, crew/candid moments, the "private Patrick vs machine DAY SHØ" contrast
{preset_section}
You MUST respond with ONLY valid JSON in this exact format (no markdown fences, no commentary):
{{
  "clips": [
    {{
      "video": "filename.mov",
      "start": 12.345,
      "end": 18.789,
      "transition": "hard_cut_on_beat",
      "reason": "Drop starts here, crowd erupts",
      "crop": "9:16",
      "lut": "underground_dark",
      "vfx": "flash",
      "slow_mo": false,
      "slow_mo_factor": 1.0,
      "phase": ""
    }}
  ],
  "narrative": "Description of the edit's story arc",
  "hook_text": ""
}}

SCHEMA NOTES:
- "phase": pov_story / community → "before" | "during" | "after"; tarantino → "hook" | "flashback" | "buildup" | "escalation"; artist_narrative → "hook" | "journey" | "escalation"; booking → "opener" | "showcase" | "peak"; "" for all other presets.
- "hook_text": REQUIRED (non-empty) for pov_story and artist_narrative; optional for community; "" otherwise."""


# ---------------------------------------------------------------------------
# JSON Response Parser (shared across all providers)
# ---------------------------------------------------------------------------

def _parse_edit_plan(raw: str, provider_name: str = "", model_id: str = "") -> EditPlan:
    """Parse AI JSON response into an EditPlan. Handles markdown fences and extra text."""
    # Strip markdown fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```)
        cleaned = "\n".join(lines[1:])
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try to find JSON object in the response (some providers add text before/after)
    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        cleaned = cleaned[json_start:json_end]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # LLMs occasionally emit slightly malformed JSON (missing/trailing
        # commas). Try to repair it before giving up.
        logger.warning(f"{provider_name} JSON invalid ({e}); attempting repair...")
        try:
            from json_repair import repair_json
            parsed = repair_json(cleaned, return_objects=True)
            if not isinstance(parsed, dict):
                raise ValueError("repaired JSON is not an object")
            logger.info(f"  Repaired malformed JSON from {provider_name}")
        except Exception as repair_err:
            logger.error(f"Failed to parse {provider_name} response as JSON: {e}")
            logger.debug(f"Raw response: {raw[:500]}")
            raise ValueError(f"Invalid JSON from {provider_name}: {e}") from repair_err

    clips = []
    for c in parsed.get("clips", []):
        clips.append(EditClip(
            video=c["video"],
            start=float(c["start"]),
            end=float(c["end"]),
            transition=c.get("transition", "cut"),
            reason=c.get("reason", ""),
            crop=c.get("crop", "9:16"),
            lut=c.get("lut", "underground_dark"),
            vfx=c.get("vfx", "none"),
            slow_mo=c.get("slow_mo", False),
            slow_mo_factor=c.get("slow_mo_factor", 1.0),
            phase=c.get("phase", ""),
        ))

    total = sum(c.duration for c in clips) if clips else 0

    return EditPlan(
        clips=clips,
        narrative=parsed.get("narrative", ""),
        hook_text=parsed.get("hook_text", ""),
        total_duration=total,
        style="highlight",
        provider_used=provider_name,
        model_used=model_id,
    )


# ---------------------------------------------------------------------------
# Data trimming for context limits
# ---------------------------------------------------------------------------

# Per-frame envelopes / internal arrays the LLM cannot use but which blow the
# context window (energy_envelope alone was ~10 MB across 83 clips). Dropped
# recursively before sending. Curated equivalents (clip_scenes, subdivision_grid,
# the music_summary, bass_drops/buildups) carry the usable information instead.
_HEAVY_KEYS = {
    "energy_envelope", "energy_times", "onset_env",
    "beat_times", "subbass_energy", "bass_energy",
    "dhash_sig", "vision_tags", "vision_tags_filtered",
}


def _trim_analysis_for_prompt(data, max_list: int = 80):
    """Recursively trim analysis data so it fits the API context window.

    Drops known-heavy per-frame arrays (`_HEAVY_KEYS`) at any depth and
    truncates any remaining long list to head+tail. Nested dicts (e.g. the
    per-clip phase_2 entries) are now traversed — the old version kept them
    whole, which let the per-clip audio envelopes overflow the context.
    """
    if isinstance(data, dict):
        out = {}
        for key, value in data.items():
            if key in _HEAVY_KEYS:
                continue
            out[key] = _trim_analysis_for_prompt(value, max_list)
        return out
    if isinstance(data, list):
        if len(data) > max_list:
            head = max_list * 3 // 4
            tail = max_list // 4
            kept = data[:head] + [f"...({len(data) - max_list} more)"] + data[-tail:]
            return [_trim_analysis_for_prompt(x, max_list) for x in kept]
        return [_trim_analysis_for_prompt(x, max_list) for x in data]
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_edit_plan(
    analysis_data: dict,
    preset: str = "highlight",
    duration: float = 60.0,
    target_bpm: float = 0.0,
    provider: str = "",
    output_path: Path | None = None,
    temperature: float = 0.4,
    max_tokens: int = 8192,  # headroom for reasoning models (e.g. deepseek) whose
                             # chain-of-thought counts against the token budget
) -> EditPlan:
    """
    Generate an AI-directed edit plan.

    Args:
        analysis_data: Complete analysis dict containing:
            - audio: {bpm, beats, drops, kicks, snares, buildups}
            - video: {scenes, motion_scores, light_changes}
            - vision_tags: [{time, tag, confidence, description}]
            - highlights: [{start, end, score}]
            - sync_offsets: {filename: offset_seconds}
        preset: Edit style preset ("highlight", "drop_focus", "seamless_loop", "moody")
        duration: Target reel duration in seconds
        target_bpm: Override BPM (0 = auto-detect)
        provider: AI provider to use ("claude", "gemini", "deepseek", "" = auto)
        output_path: Optional path to save the plan JSON
        temperature: Generation temperature (0.0-1.0)
        max_tokens: Max tokens in response

    Returns:
        EditPlan with precise clip selections
    """
    # Resolve provider
    ai = resolve_provider(provider)

    logger.info(f"Generating edit plan: preset={preset}, duration={duration}s")
    logger.info(f"  Provider: {ai.name} ({ai.model_id})")

    # Build prompts
    system_prompt = _build_system_prompt(preset, duration, target_bpm)

    # Musikdaten als zusätzlichen Abschnitt im System-Prompt einfügen (für alle Presets)
    music_analysis = analysis_data.get("music_analysis")
    if music_analysis and "error" not in music_analysis:
        music_summary = "\n\nMUSIC TRACK ANALYSIS (use for timing cuts, drops, and overall pacing):\n"
        if music_analysis.get("bpm"):
            music_summary += f"- BPM: {music_analysis['bpm']:.1f}\n"
        if music_analysis.get("beat_times"):
            beats = music_analysis["beat_times"]
            music_summary += f"- {len(beats)} beat_times: first 8 = {beats[:8]}\n"
        if music_analysis.get("kick_times"):
            kicks = music_analysis["kick_times"]
            music_summary += f"- {len(kicks)} kick_times: first 10 = {kicks[:10]}\n"
        if music_analysis.get("drop_times"):
            drops = music_analysis["drop_times"]
            music_summary += f"- {len(drops)} drop_times: {drops[:5]}\n"
        if music_analysis.get("subbass_energy"):
            # Nur zeigen, dass es existiert
            music_summary += f"- subbass_energy curve available ({len(music_analysis['subbass_energy'])} values)\n"
        system_prompt += music_summary

    trimmed = _trim_analysis_for_prompt(analysis_data)
    user_data = f"ANALYSIS DATA:\n```json\n{json.dumps(trimmed, indent=2, ensure_ascii=False, default=str)}\n```"

    # Call AI provider
    t0 = time.time()
    raw_response = ai.call(
        system_prompt=system_prompt,
        user_data=user_data,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.time() - t0

    logger.info(f"  Response received in {elapsed:.1f}s")

    # Parse response
    plan = _parse_edit_plan(raw_response, provider_name=ai.name, model_id=ai.model_id)
    plan.generation_time_s = elapsed
    plan.style = preset  # reflect the requested preset (parser defaults to "highlight")

    # Verify and fix
    plan = verify_edit_plan(plan, analysis_data, target_duration=duration)

    if output_path:
        plan.save(output_path)

    logger.info(f"Edit plan generated: {len(plan.clips)} clips, {plan.total_duration:.1f}s total "
                f"[{ai.name}/{ai.model_id}, {elapsed:.1f}s]")
    return plan


def generate_multi_plan(
    analysis_data: dict,
    preset: str = "highlight",
    duration: float = 60.0,
    target_bpm: float = 0.0,
    providers: list[str] | None = None,
) -> dict[str, EditPlan]:
    """
    Generate edit plans from MULTIPLE providers for comparison/A/B testing.
    Each provider with a configured API key generates its own plan.

    Returns:
        Dict of {provider_name: EditPlan}
    """
    if providers is None:
        providers = REGIE_PROVIDER_FALLBACK_ORDER

    results: dict[str, EditPlan] = {}

    for provider_name in providers:
        try:
            provider = get_provider(provider_name)
            if not provider.is_available():
                logger.info(f"Skipping {provider_name}: API key not set")
                continue

            logger.info(f"\n{'=' * 40}")
            logger.info(f"Generating plan with {provider_name}...")

            plan = generate_edit_plan(
                analysis_data,
                preset=preset,
                duration=duration,
                target_bpm=target_bpm,
                provider=provider_name,
            )
            results[provider_name] = plan

        except Exception as e:
            logger.error(f"  {provider_name} failed: {e}")
            continue

    if not results:
        raise RuntimeError("All providers failed to generate edit plans")

    return results


# ---------------------------------------------------------------------------
# Verification & Self-Healing
# ---------------------------------------------------------------------------

def _source_duration(video_path: str, _cache: dict = {}) -> float:
    """Source media duration via ffprobe, cached per path. 0.0 if unknown."""
    if video_path in _cache:
        return _cache[video_path]
    import subprocess
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=30,
        )
        dur = float(out.stdout.strip()) if out.returncode == 0 else 0.0
    except Exception:
        dur = 0.0
    _cache[video_path] = dur
    return dur


def verify_edit_plan(
    plan: EditPlan,
    analysis_data: dict,
    target_duration: float = 60.0,
) -> EditPlan:
    """
    Verify an edit plan and fix common issues:
    - Clips with zero/negative duration
    - Overly long clips (>15s)
    - End times beyond the real source duration (AI overshoot) – clamped,
      then the lost time is recovered by extending clips that have headroom
    - Duration mismatch warnings
    """
    if not plan.clips:
        logger.warning("Empty edit plan - nothing to verify")
        return plan

    fixed_clips = []
    for clip in plan.clips:
        if clip.end <= clip.start:
            logger.warning(f"Skipping zero/negative duration clip: {clip.video} [{clip.start}-{clip.end}]")
            continue

        # Clamp against the REAL source duration – the AI only sees analysis
        # data and routinely plans end times past the end of short clips.
        # If ffprobe returns 0.0 (path unavailable, timeout, etc.) we skip
        # the source-clamp entirely – never drop a clip purely because ffprobe
        # couldn't probe it (the path may still be valid at render time).
        src_dur = _source_duration(clip.video)
        if src_dur > 0:
            if clip.start >= src_dur:
                logger.warning(
                    f"Skipping clip starting past source end: {clip.video} "
                    f"[start={clip.start:.1f}s, source={src_dur:.1f}s]"
                )
                continue
            if clip.end > src_dur:
                logger.warning(
                    f"Clamping clip end to source duration: {clip.video} "
                    f"[{clip.end:.1f}s → {src_dur:.1f}s]"
                )
                clip.end = src_dur
        else:
            logger.debug(
                f"ffprobe returned 0 for {clip.video} – source clamp skipped "
                f"(file may be valid; will be checked at render time)"
            )

        clip_duration = clip.duration
        if clip_duration > 15.0:
            logger.warning(f"Trimming long clip ({clip_duration:.1f}s): {clip.video}")
            clip.end = clip.start + 15.0

        fixed_clips.append(clip)

    plan.clips = fixed_clips
    plan.total_duration = sum(c.duration for c in plan.clips)

    # Recover clamped time: extend clips whose SOURCE has headroom past their
    # planned end. Start times stay untouched (they are beat-aligned cut-ins);
    # shots just breathe a little longer. Max +2 s per clip, 15 s clip cap.
    shortfall = target_duration - plan.total_duration
    if shortfall > 1.0:
        for clip in plan.clips:
            if shortfall <= 0:
                break
            src_dur = _source_duration(clip.video)
            if src_dur <= 0:
                continue
            headroom = min(src_dur - clip.end, 2.0, 15.0 - clip.duration)
            if headroom > 0.1:
                extend = min(headroom, shortfall)
                clip.end = round(clip.end + extend, 3)
                shortfall -= extend
        recovered = sum(c.duration for c in plan.clips) - plan.total_duration
        if recovered > 0.05:
            logger.info(f"Recovered {recovered:.1f}s by extending clips with source headroom")
        plan.total_duration = sum(c.duration for c in plan.clips)

    duration_diff = abs(plan.total_duration - target_duration)
    if duration_diff > 5.0:
        logger.warning(
            f"Duration mismatch: plan={plan.total_duration:.1f}s vs target={target_duration:.1f}s "
            f"(diff={duration_diff:.1f}s)"
        )

    logger.info(
        f"Verification: {len(plan.clips)} clips, "
        f"total={plan.total_duration:.1f}s, "
        f"target={target_duration:.1f}s"
    )

    return plan


# ---------------------------------------------------------------------------
# Seamless Loop Helper
# ---------------------------------------------------------------------------

def create_seamless_loop_plan(
    video_path: str,
    start: float,
    end: float,
    crossfade_duration: float = 0.5,
) -> EditPlan:
    """
    Create a seamless loop edit plan by splitting a clip and swapping halves.
    End-clip goes first, Start-clip goes last, with crossfade at the junction.
    Exploits Instagram's loop behavior for higher view counts.
    """
    midpoint = (start + end) / 2

    return EditPlan(
        clips=[
            EditClip(
                video=video_path,
                start=midpoint,
                end=end,
                transition="crossfade",
                reason="Second half of original (plays first for seamless loop)",
            ),
            EditClip(
                video=video_path,
                start=start,
                end=midpoint,
                transition="crossfade",
                reason="First half of original (plays second for seamless loop)",
            ),
        ],
        narrative="Seamless loop: end flows back to start for infinite replay",
        total_duration=end - start,
        style="seamless_loop",
        provider_used="algorithmic",
        model_used="seamless_loop_v1",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="UNREEL V3 – Regie Engine (Multi-Provider AI)",
    )
    parser.add_argument("analysis_json", help="Path to analysis JSON file")
    parser.add_argument("--preset", "-p", default="highlight",
                        choices=["highlight", "drop_focus", "seamless_loop", "moody", "pov_story", "tarantino", "artist_narrative", "booking", "community"])
    parser.add_argument("--duration", "-d", type=float, default=60.0)
    parser.add_argument("--provider", choices=["claude", "gemini", "deepseek", "auto"],
                        default="auto", help="AI provider (default: auto)")
    parser.add_argument("--multi", action="store_true",
                        help="Generate plans from ALL available providers for comparison")
    parser.add_argument("--output", "-o", type=Path, default=Path("output/edit_plan.json"))
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    with open(args.analysis_json) as f:
        analysis = json.load(f)

    # Show provider status
    print("\n📡 Provider Status:")
    for p in list_available_providers():
        status = "✅ available" if p["available"] else "❌ no API key"
        print(f"  {p['name']:10s}  {p['model']:25s}  {status}")
    print()

    if args.multi:
        # Multi-provider comparison
        results = generate_multi_plan(analysis, preset=args.preset, duration=args.duration)

        print(f"\n{'=' * 60}")
        print(f"MULTI-PROVIDER COMPARISON ({len(results)} plans)")
        print(f"{'=' * 60}")

        for name, plan in results.items():
            print(f"\n  [{name.upper()}] {plan.model_used}")
            print(f"  Clips: {len(plan.clips)}, Duration: {plan.total_duration:.1f}s, "
                  f"Time: {plan.generation_time_s:.1f}s")
            print(f"  Narrative: {plan.narrative}")
            plan.save(args.output.parent / f"edit_plan_{name}.json")

    else:
        # Single provider
        plan = generate_edit_plan(
            analysis,
            preset=args.preset,
            duration=args.duration,
            provider=args.provider,
            output_path=args.output,
        )

        print(f"\nEdit Plan by {plan.provider_used} ({plan.model_used})")
        print(f"  {len(plan.clips)} clips, {plan.total_duration:.1f}s, generated in {plan.generation_time_s:.1f}s")
        print(f"  Narrative: {plan.narrative}\n")

        for i, clip in enumerate(plan.clips):
            print(f"  [{i + 1:02d}] {Path(clip.video).name:30s}  "
                  f"{clip.start:7.3f}s → {clip.end:7.3f}s  "
                  f"({clip.duration:.1f}s)  {clip.transition}")

        print(f"\nSaved to {args.output}")

\\n
### \test_ingest.py\n
\\python
"""
Tests für analyzer/ingest.py – Ingestion & Renaming (Phase 0).

Stil-konsistent zu den übrigen tests/: keine echten Videos, ffprobe wird
über den mtime-Fallback umgangen (für Dummy-Dateien hat ffprobe keine
creation_time, also greift automatisch os.path.getmtime).
"""

import os
import time

import pytest

import ingest


@pytest.fixture
def src(tmp_path, monkeypatch):
    """Isolierter Input-Ordner + gemocktes config.SUPPORTED_EXTENSIONS."""
    monkeypatch.setattr(ingest.config, "VIDEO_SOURCE_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4", ".mov"], raising=False)
    return tmp_path


def _make(path, content: bytes, ts: float | None = None):
    path.write_bytes(content)
    if ts is not None:
        os.utime(path, (ts, ts))
    return path


def _ts(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def test_renames_to_timestamp(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "raw_clip.mp4", b"A" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250612_143000.mp4").exists()
    assert not (src / "raw_clip.mp4").exists()
    assert len(result.renamed) == 1


def test_removes_duplicates(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "a.mp4", b"SAME" * 1000, base)
    _make(src / "b.mp4", b"SAME" * 1000, base + 10)  # identischer Inhalt

    result = ingest.ingest_directory(src)

    remaining = [f for f in os.listdir(src) if f.endswith(".mp4")]
    assert len(remaining) == 1
    assert len(result.duplicates_removed) == 1


def test_skips_hidden_and_unsupported(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "._hidden.mp4", b"x", base)
    _make(src / "notes.txt", b"hello", base)

    result = ingest.ingest_directory(src)

    assert result.renamed == []
    assert result.duplicates_removed == []
    assert (src / "._hidden.mp4").exists()
    assert (src / "notes.txt").exists()


def test_keeps_already_named_files(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "UNREEL_20250101_000000.mp4", b"C" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250101_000000.mp4").exists()
    assert result.renamed == []
    assert str(src / "UNREEL_20250101_000000.mp4") in result.final_files


def test_timestamp_collision_gets_counter(src):
    base = _ts("2025-06-12 14:30:00")
    # Zwei unterschiedliche Inhalte, gleiche Endung, gleicher Timestamp.
    _make(src / "first.mp4", b"FIRST" * 1000, base)
    _make(src / "second.mp4", b"SECND" * 1000, base)

    ingest.ingest_directory(src)

    names = sorted(f for f in os.listdir(src) if f.startswith("UNREEL_"))
    assert "UNREEL_20250612_143000.mp4" in names
    assert "UNREEL_20250612_143000_1.mp4" in names


def test_final_files_feeds_pipeline(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "x.mp4", b"X" * 4000, base)
    _make(src / "UNREEL_20250101_000000.mov", b"Y" * 4000, base)

    result = ingest.ingest_directory(src)

    # final_files enthält genau die Dateien, die danach existieren & verarbeitbar sind.
    for p in result.final_files:
        assert os.path.exists(p)
    assert len(result.final_files) == 2


def test_missing_source_dir_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4"], raising=False)
    result = ingest.ingest_directory(tmp_path / "does_not_exist")
    assert result.final_files == []
    assert result.errors == []

\\n
### \src/main.py\n
\\python
"""
UNREEL V3 – Main CLI Entry Point (Orchestrator)
Orchestrates the full DJ video pipeline: ingest → sync → analyze → regie → export.
Supports multi-provider AI regie (Claude, Gemini, DeepSeek).

Usage:
    python -m src.main --input ./input --preset highlight --duration 60
    python -m src.main --input ./input --preset seamless_loop --duration 30
    python -m src.main --input ./input --provider gemini --phase regie
    python -m src.main --input ./input --provider deepseek --multi
    python -m src.main --input ./input --phase sync        # Run only Phase 1
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path for imports (V3 modules live at the repo root)
# src/main.py is in src/, so root is parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    INPUT_DIR, OUTPUT_DIR, LUT_DIR, DEFAULT_LUT,
    SAMPLE_RATE, COPYWRITER_MODEL, GEMMA_MODEL,
    REGIE_PROVIDER, REEL_FPS,
)
from lut_generator import generate_all_luts, get_lut_path
from audio_sync import sync_all_clips
from kick_snare_detector import detect_kicks_snares, get_beat_grid
from analyzer.vision_engine import tag_video_frames, filter_unusable
from analyzer.copywriter import generate_caption, generate_filename, batch_process, save_captions
from regie_engine import (
    generate_edit_plan,
    generate_multi_plan,
    create_seamless_loop_plan,
    list_available_providers,
)
from ingest import ingest_directory

logger = logging.getLogger("unreel")

# Retention-focused presets default to a 15–45s reel (30s when -d is left at
# the 60s default). Music behaviour is auto-tuned per preset:
#   J-cut (muffled bass → drop) fits the build→explode narratives.
#   Endcard (logo) fits the branded/promo presets, not the casual community one.
_RETENTION_PRESETS = {"artist_narrative", "booking", "community"}
_AUTO_JCUT_PRESETS = {"tarantino", "artist_narrative"}
_AUTO_ENDCARD_PRESETS = {"tarantino", "booking", "artist_narrative"}
# Invisible sound design (riser → drop + sub-impact) fits the presets with a
# clear drop payoff. Needs --music to have something to mix over.
_AUTO_SFX_PRESETS = {"tarantino", "artist_narrative"}


# ---------------------------------------------------------------------------
# Pipeline Phases
# ---------------------------------------------------------------------------

def phase_ingest(input_dir):
    """Phase 0: Duplikate entfernen + nach UNREEL_<timestamp> umbenennen."""
    logger.info("Phase 0: Ingestion & Renaming")
    result = ingest_directory(input_dir)
    return [Path(p) for p in result.final_files]


def phase_0_setup():
    """Phase 0: Generate LUTs if they don't exist."""
    logger.info("=" * 60)
    logger.info("PHASE 0: Setup – Generating LUTs")
    logger.info("=" * 60)

    luts = generate_all_luts()
    for name, path in luts.items():
        logger.info(f"  ✓ {name}: {path}")
    return luts


_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}


def phase_1_sync(video_paths: list[Path], music_path: Path | None = None) -> dict:
    """Phase 1: Audio Cross-Correlation Sync + Kick/Snare Detection.

    If `music_path` is given (--music), or an audio-only file is found in
    `video_paths`, that file is used for BPM/kick/snare detection instead of
    the camera scratch audio. Video sync offsets still run on video clips only.
    """
    logger.info("=" * 60)
    logger.info("PHASE 1: Audio Sync & Percussion Detection")
    logger.info("=" * 60)

    result = {}

    # Separate video clips from audio-only files in the input list
    videos_only = [p for p in video_paths if p.suffix.lower() not in _AUDIO_EXTENSIONS]
    audio_files = [p for p in video_paths if p.suffix.lower() in _AUDIO_EXTENSIONS]

    # Audio sync (only if multiple VIDEO clips)
    if len(videos_only) >= 2:
        sync_result = sync_all_clips(
            [str(p) for p in videos_only],
            sr=SAMPLE_RATE,
            output_path=OUTPUT_DIR / "audio_sync.json",
        )
        result["sync"] = sync_result.to_dict()
        ref_path = sync_result.reference_clip
    elif videos_only:
        ref_path = str(videos_only[0])
        result["sync"] = {"reference_clip": ref_path, "offsets": {ref_path: 0.0}}
    else:
        ref_path = str(video_paths[0]) if video_paths else ""
        result["sync"] = {"reference_clip": ref_path, "offsets": {}}

    # Determine the best audio source for percussion analysis:
    # Priority: --music track > audio files in input > reference video clip
    percussion_source = ref_path
    percussion_label = "reference video (camera audio)"

    if music_path and Path(music_path).exists():
        percussion_source = str(music_path)
        percussion_label = f"music track: {Path(music_path).name}"
    elif audio_files:
        percussion_source = str(audio_files[0])
        percussion_label = f"input audio: {audio_files[0].name}"

    # Kick/Snare/BPM detection on the best audio source
    logger.info(f"\nPercussion analysis source: {percussion_label}")
    percussion = detect_kicks_snares(percussion_source, sr=SAMPLE_RATE)
    percussion.save(OUTPUT_DIR / "percussion_map.json")
    result["percussion"] = percussion.to_dict()
    result["beat_grid"] = get_beat_grid(percussion)

    logger.info(f"\n  Source: {Path(percussion_source).name}")
    logger.info(f"  BPM: {percussion.bpm:.1f}")
    logger.info(f"  Kicks: {len(percussion.kicks)}")
    logger.info(f"  Snares: {len(percussion.snares)}")

    return result



def _video_signature(video_path: str) -> list[int | None] | None:
    """
    Cheap visual signature: dHash of five frames spread across the clip.
    Used to detect near-duplicate clips before the expensive vision tagging.
    Five positions (not three) so that mostly-dark club footage still yields
    enough informative (non-uniform) frames for a confident comparison.
    None if the duration can't be probed.
    """
    from analyzer.frame_hasher import dhash
    duration = _probe_duration(Path(video_path))
    if duration <= 0:
        return None
    return [dhash(video_path, duration * f) for f in (0.15, 0.35, 0.5, 0.65, 0.85)]


def _find_visual_twin(sig: list, known_sigs: dict[str, list]) -> str | None:
    """
    Return the path of an already-tagged clip that is visually near-identical
    to `sig`, or None. Conservative: ALL comparable frame positions must be
    within the hamming threshold, and at least two must be comparable —
    false positives would propagate wrong tags into the edit plan.

    Calibrated on real footage: re-encoded duplicates differ by <=7 bits,
    different scenes by >=16, so threshold 10 sits safely in the gap.
    Near-uniform frames (e.g. black strobe-off moments, popcount < 4) carry
    no information and would match across unrelated night clips, so they
    don't count as comparable.
    """
    from analyzer.frame_hasher import hamming
    threshold = 10

    def informative(h: int | None) -> bool:
        return h is not None and bin(h).count("1") >= 4

    for path, other in known_sigs.items():
        comparable = 0
        match = True
        for a, b in zip(sig, other):
            if not informative(a) or not informative(b):
                continue
            comparable += 1
            if hamming(a, b) > threshold:
                match = False
                break
        if match and comparable >= 2:
            return path
    return None


def phase_2_analyze(video_paths: list[Path], existing: dict | None = None, save_cb=None,
                    music_path: Path | None = None) -> dict:
    """Phase 2: Video Analysis + Vision Tagging.

    Resumable: clips already present in `existing` are skipped, and `save_cb(result)`
    is invoked after each clip so an interruption (sleep/kill) never loses progress.
    Near-duplicate clips (3-frame dHash signature) inherit the tags of their
    visual twin instead of going through Gemma again.
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: Video Analysis & Vision Tagging")
    logger.info("=" * 60)

    result = dict(existing) if existing else {}
    total = len(video_paths)

    # Signatures of already-tagged clips (for the duplicate pre-filter)
    known_sigs: dict[str, list] = {
        p: e["dhash_sig"] for p, e in result.items()
        if isinstance(e, dict) and e.get("dhash_sig")
    }

    for i, vp in enumerate(video_paths, 1):
        vp_str = str(vp)
        if vp_str in result and "vision_tags" in result[vp_str]:
            # Backfill signature for entries from before the pre-filter existed
            if vp_str not in known_sigs:
                sig = _video_signature(vp_str)
                if sig:
                    result[vp_str]["dhash_sig"] = sig
                    known_sigs[vp_str] = sig
            logger.info(f"\n[{i}/{total}] Skipping {vp.name} (already tagged)")
            continue

        # Pre-filter: visually near-identical to an already-tagged clip?
        sig = _video_signature(vp_str)
        twin = _find_visual_twin(sig, known_sigs) if sig else None
        if twin is not None:
            twin_entry = result[twin]
            result[vp_str] = {
                "vision_tags": twin_entry.get("vision_tags", []),
                "vision_tags_filtered": twin_entry.get("vision_tags_filtered", []),
                "tag_count": twin_entry.get("tag_count", 0),
                "usable_count": twin_entry.get("usable_count", 0),
                "duplicate_of": twin,
                "dhash_sig": sig,
            }
            logger.info(f"\n[{i}/{total}] {vp.name}: visual duplicate of "
                        f"{Path(twin).name} – inheriting tags (Gemma skipped)")
            if save_cb is not None:
                save_cb(result)
            continue

        logger.info(f"\n[{i}/{total}] Analyzing {vp.name}...")

        # Vision tagging via Gemma 4. A single unreadable/corrupt clip must
        # NOT kill the whole run – mark it empty and carry on.
        logger.info("  Running vision tagging (Gemma 4 E2B)...")
        try:
            tags = tag_video_frames(vp_str)
        except Exception as e:
            logger.error(f"  ✗ Tagging failed for {vp.name} ({e}) – skipping clip")
            result[vp_str] = {
                "vision_tags": [],
                "vision_tags_filtered": [],
                "tag_count": 0,
                "usable_count": 0,
                "error": str(e),
                "dhash_sig": sig,
            }
            if save_cb is not None:
                save_cb(result)
            continue

        filtered = filter_unusable(tags)

        result[vp_str] = {
            "vision_tags": [t.to_dict() for t in tags],
            "vision_tags_filtered": [t.to_dict() for t in filtered],
            "tag_count": len(tags),
            "usable_count": len(filtered),
            "dhash_sig": sig,
        }
        if sig:
            known_sigs[vp_str] = sig

        logger.info(f"  Tags: {len(tags)} total, {len(filtered)} usable")
        for t in filtered[:5]:
            logger.info(f"    t={t.time:.1f}s  {t.tag}  ({t.confidence:.2f})")

        # Audio-Analyse für dieses Video (BPM, Beats, Energy, Bass Drops, Buildups)
        logger.info(f"  Analyzing audio for {vp.name}...")
        try:
            from analyzer.audio_analyzer import analyze_audio
            audio_result = analyze_audio(vp_str)
            result[vp_str]["audio_analysis"] = audio_result
            logger.info(f"    BPM: {audio_result['tempo']:.1f}, Beats: {len(audio_result['beat_times'])}, "
                        f"Drops: {len(audio_result['bass_drops'])}, Buildups: {len(audio_result['buildups'])}")
        except Exception as e:
            logger.warning(f"    Audio analysis failed: {e}")
            result[vp_str]["audio_analysis"] = {"error": str(e)}

        # Persist after every clip so progress survives interruptions
        if save_cb is not None:
            save_cb(result)

    # Musikdatei analysieren (Bass, Subbass, Kicks, Transienten, Drops)
    if music_path and music_path.exists() and music_path.suffix.lower() in _AUDIO_EXTENSIONS:
        logger.info(f"\nMusic file for analysis: {music_path.name}")
        try:
            from analyzer.audio_analyzer import analyze_music_file
            music_analysis = analyze_music_file(str(music_path))
            result["music_analysis"] = music_analysis
            logger.info(f"  Music analysis complete: BPM={music_analysis.get('bpm', '?')}, "
                        f"{len(music_analysis.get('kick_times', []))} kicks, "
                        f"{len(music_analysis.get('transient_times', []))} transients, "
                        f"{len(music_analysis.get('drop_times', []))} drops")
        except Exception as e:
            logger.warning(f"Music analysis failed: {e}")
            result["music_analysis"] = {"error": str(e)}
    elif music_path:
        logger.warning(f"Music file {music_path} not found or unsupported – skipping music analysis")
    else:
        result["music_analysis"] = None  # kein Music-Track angegeben

    return result


def _build_subdivision_grid(bpm: float, duration: float) -> dict:
    """Berechnet Zeitpunkte für Notenwerte basierend auf BPM.

    Gibt der AI exakte Sekunden-Dauern für 1/4, 1/2, 1/8, 1/16 Noten
    und ganze Takte, plus quantisierte Schnittpunkte auf 1/4 und 1/8.
    """
    if bpm <= 0:
        return {}
    beat_sec = 60.0 / bpm  # 1/4-Note in Sekunden
    return {
        "bpm": round(bpm, 1),
        "note_durations": {
            "1/1_bar":  round(beat_sec * 4, 3),
            "1/2_half": round(beat_sec * 2, 3),
            "1/4_beat": round(beat_sec, 3),
            "1/8_eighth": round(beat_sec / 2, 3),
            "1/16_sixteenth": round(beat_sec / 4, 3),
        },
        "cut_points_1_4": [round(i * beat_sec, 3)
                           for i in range(int(duration / beat_sec) + 1)],
        "cut_points_1_8": [round(i * beat_sec / 2, 3)
                           for i in range(int(duration / (beat_sec / 2)) + 1)],
    }


def phase_3_regie(
    analysis_data: dict,
    preset: str,
    duration: float,
    provider: str = "",
    multi: bool = False,
) -> dict:
    """
    Phase 3: AI Regie – Multi-provider edit plan generation.
    Supports Claude Fable 5, Gemini 3.1 Pro, and DeepSeek V4 Pro.
    """
    logger.info("=" * 60)
    logger.info("PHASE 3: AI Regie – Generating Edit Plan")
    logger.info("=" * 60)

    # Show provider status
    providers = list_available_providers()
    available = [p for p in providers if p["available"]]
    logger.info(f"  Available providers: {', '.join(p['name'] for p in available) or 'none'}")

    if not available:
        logger.warning("No AI provider available – skipping Regie phase")
        logger.warning(
            "Set at least one API key in .env:\n"
            "  ANTHROPIC_API_KEY=...  (Claude Fable 5)\n"
            "  GEMINI_API_KEY=...     (Gemini 3.1 Pro)\n"
            "  DEEPSEEK_API_KEY=...   (DeepSeek V4 Pro)"
        )
        return {"edit_plan": None, "skipped": True, "reason": "no_api_key"}

    # Real source durations → the planner stops scheduling cuts past a clip's
    # end (the verifier additionally clamps, but informed plans cut better).
    p2 = analysis_data.get("phase_2") or {}
    durations = {}
    for vp_str, entry in p2.items():
        if isinstance(entry, dict):
            d = _probe_duration(Path(vp_str))
            if d > 0:
                durations[Path(vp_str).name] = round(d, 2)
    if durations:
        analysis_data = {**analysis_data, "clip_durations": durations}

    # Notenbasiertes Beat-Grid für den AI-Provider (Pacing per Phase)
    perc = analysis_data.get("phase_1", {}).get("percussion", {})
    bpm = perc.get("bpm", 0)
    if bpm > 0:
        grid = _build_subdivision_grid(bpm, duration)
        analysis_data = {**analysis_data, "subdivision_grid": grid}
        logger.info(f"  Beat-Grid: {bpm:.0f} BPM → 1/4={grid['note_durations']['1/4_beat']}s, "
                    f"1/8={grid['note_durations']['1/8_eighth']}s, "
                    f"1/16={grid['note_durations']['1/16_sixteenth']}s")

    # Kompakte Szenen-Beschreibungen pro Clip für Match-Cut-Erkennung
    clip_scenes = {}
    for vp_str, entry in p2.items():
        if not isinstance(entry, dict):
            continue
        tags = entry.get("vision_tags_filtered") or entry.get("vision_tags") or []
        descriptions = [t.get("description", "") for t in tags if t.get("description")]
        if descriptions:
            clip_scenes[Path(vp_str).name] = {
                "tags": list({t.get("tag") for t in tags if t.get("tag")}),
                "scenes": descriptions[:5],
            }
    if clip_scenes:
        analysis_data = {**analysis_data, "clip_scenes": clip_scenes}
        logger.info(f"  Clip-Scenes: {len(clip_scenes)} clips with descriptions for match-cut analysis")

    # Seamless loop (algorithmic, no AI needed)
    if preset == "seamless_loop":
        videos = list(analysis_data.get("sync", {}).get("offsets", {}).keys())
        if videos:
            plan = create_seamless_loop_plan(videos[0], 5.0, 5.0 + duration)
            plan.save(OUTPUT_DIR / "edit_plan.json")
            result = plan.to_dict()
            logger.info(f"\n  Seamless Loop Plan: {len(plan.clips)} clips, {plan.total_duration:.1f}s")
            return {"edit_plan": result}
        else:
            logger.error("No videos available for seamless loop")
            return {"edit_plan": None}

    # Multi-provider mode: generate from all available providers
    if multi:
        logger.info("  Mode: MULTI-PROVIDER (generating plans from all available AIs)")
        try:
            plans = generate_multi_plan(
                analysis_data,
                preset=preset,
                duration=duration,
            )
        except RuntimeError as e:
            logger.error(f"Multi-provider generation failed: {e}")
            return {"edit_plan": None, "skipped": True, "reason": str(e)}

        # Save all plans
        all_plans = {}
        for name, plan in plans.items():
            plan.save(OUTPUT_DIR / f"edit_plan_{name}.json")
            all_plans[name] = plan.to_dict()
            logger.info(f"\n  [{name.upper()}] {plan.model_used}")
            logger.info(f"    {len(plan.clips)} clips, {plan.total_duration:.1f}s, "
                        f"generated in {plan.generation_time_s:.1f}s")
            logger.info(f"    Narrative: {plan.narrative}")

        # Use the first provider's plan as the default
        primary = list(plans.values())[0]
        primary.save(OUTPUT_DIR / "edit_plan.json")

        return {"edit_plan": primary.to_dict(), "all_plans": all_plans}

    # Single provider mode
    try:
        plan = generate_edit_plan(
            analysis_data,
            preset=preset,
            duration=duration,
            provider=provider,
            output_path=OUTPUT_DIR / "edit_plan.json",
        )
    except ValueError as e:
        logger.error(f"Provider error: {e}")
        return {"edit_plan": None, "skipped": True, "reason": str(e)}

    result = plan.to_dict()

    logger.info(f"\n  Edit Plan by {plan.provider_used} ({plan.model_used})")
    logger.info(f"  {len(plan.clips)} clips, {plan.total_duration:.1f}s, "
                f"generated in {plan.generation_time_s:.1f}s")
    logger.info(f"  Narrative: {plan.narrative}")
    if plan.hook_text:
        logger.info(f'  Anti-advice hook (first ~3s): "{plan.hook_text}"')

    for i, clip in enumerate(plan.clips):
        phase = f"  [{clip.phase}]" if clip.phase else ""
        logger.info(f"    [{i + 1:02d}] {Path(clip.video).name}  "
                     f"{clip.start:.3f}s → {clip.end:.3f}s  ({clip.duration:.1f}s)  {clip.transition}{phase}")

    return {"edit_plan": result}


def phase_4_copywriting(clips_metadata: list[dict], style: str = "techno") -> dict:
    """Phase 4: Llama 3.2 Copywriting – filenames and captions."""
    logger.info("=" * 60)
    logger.info("PHASE 4: Copywriting – Filenames & Captions")
    logger.info("=" * 60)

    results = batch_process(clips_metadata, style=style, model=COPYWRITER_MODEL)
    save_captions(results, OUTPUT_DIR / "captions.json")

    for r in results:
        logger.info(f"  {r.filename}.mp4")
        logger.info(f"    → {r.caption[:80]}...")

    return {
        "captions": [r.to_dict() for r in results],
        "count": len(results),
    }


# Serializes YOLO inference (the shared model instance is not thread-safe)
# and the tracking-cache file when snippets are exported in parallel.
_TRACKING_LOCK = threading.Lock()


def _tracked_x_center(video: str, start: float, end: float) -> float | None:
    """
    Cached JIT auto-framing: average x-position of the main person in the
    clip window. Results are persisted in output/tracking_cache.json so
    variant runs and re-exports skip YOLO entirely for known windows.
    """
    cache_path = OUTPUT_DIR / "tracking_cache.json"
    key = f"{Path(video).name}|{start:.3f}|{end:.3f}"

    with _TRACKING_LOCK:
        cache: dict = {}
        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        if key in cache:
            logger.info("       → (cached)")
            return cache[key]  # may be None (= no subject found)

        from analyzer.tracking_engine import sample_x_center
        avg_x = sample_x_center(video, start_time=start, end_time=end, samples=10, imgsz=640)

        cache[key] = avg_x
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except OSError as e:
            logger.warning(f"Could not write tracking cache: {e}")
        return avg_x


def _build_endcard(duration: float = 2.6) -> Path | None:
    """
    Brutalist tech-noir logo endcard (output/_endcard.mp4).

    The DAY SHØ wordmark stutters in with a chromatic RGB-split glitch over the
    first ~0.45 s, then snaps clean and holds on black – hard and machine-like,
    no soft tweens. Encoded with the same params as the snippets so it
    stream-copy concatenates onto the reel.
    """
    logo = LUT_DIR.parent / "LOGO" / "alt master.png"
    if not logo.exists():
        logger.warning(f"Endcard logo not found: {logo} – skipping endcard")
        return None

    out = OUTPUT_DIR / "_endcard.mp4"
    filter_complex = (
        "[1:v]scale=760:-1[lg];"
        "[0:v][lg]overlay=(W-w)/2:(H-h)/2[comp];"
        "[comp]rgbashift=rh=7:bh=-7:enable='lt(t,0.45)',"
        "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:"
        "enable='between(t,0,0.05)+between(t,0.12,0.15)+between(t,0.24,0.26)+between(t,0.34,0.36)',"
        f"fps={REEL_FPS}[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r={REEL_FPS}:d={duration}",
        "-loop", "1", "-i", str(logo),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{duration}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            logger.info(f"  ✓ Endcard built ({duration:.1f}s)")
            return out
        logger.error(f"  ✗ Endcard failed: {result.stderr.strip()[-300:]}")
    except Exception as e:
        logger.error(f"  ✗ Endcard error: {e}")
    return None


def phase_5_assembly(
    edit_plan: dict | None,
    sync_data: dict | None = None,
    music_path: Path | None = None,
    vision_data: dict | None = None,
    jcut: bool = False,
    endcard: bool = False,
    sfx: bool = False,
    input_dir: Path | None = None,
) -> None:
    """Phase 5: FFmpeg Assembly – Export with 3D-LUT, VFX, and optional master audio.

    If `music_path` is given, a chosen music track is laid over the finished
    reel (original audio replaced), with the track's drop aligned to the reel's
    energy peak (derived from `vision_data`).
    """
    logger.info("=" * 60)
    logger.info("PHASE 5: FFmpeg Assembly & Color Grading")
    logger.info("=" * 60)

    # Fallback: Edit-Plan aus Datei laden, falls nicht übergeben
    if edit_plan is None:
        edit_plan_path = OUTPUT_DIR / "edit_plan.json"
        if edit_plan_path.exists():
            try:
                with open(edit_plan_path, encoding="utf-8") as f:
                    edit_plan = json.load(f)
                logger.info(f"Loaded edit plan from {edit_plan_path}")
            except Exception as e:
                logger.error(f"Could not load edit plan: {e}")
                return
        else:
            logger.warning("No edit plan available – skipping assembly")
            logger.info("Tip: Set an AI provider API key to generate edit plans")
            return

    clips = edit_plan.get("clips", [])
    if not clips:
        logger.warning("Empty edit plan – nothing to assemble")
        return

    logger.info(f"Assembling {len(clips)} clips...")

    # Export snippets in parallel: encodes are independent FFmpeg processes,
    # so a small worker pool overlaps tracking + encoding. Results keep plan
    # order via their index. Worker count via EXPORT_WORKERS (default 3).
    workers = max(1, int(os.environ.get("EXPORT_WORKERS", "3")))
    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_export_one_snippet, i, clip, sync_data, input_dir): i
            for i, clip in enumerate(clips)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                path = fut.result()
                if path is not None:
                    results[idx] = path
            except Exception as e:
                logger.error(f"  [{idx + 1:02d}] ✗ Export worker error: {e}")

    exported_snippets = [results[i] for i in sorted(results)]  # plan order

    # Optional: brutalist logo endcard, appended as the last snippet so the
    # music bed (applied after concat) flows over it.
    if endcard and exported_snippets:
        card = _build_endcard()
        if card is not None:
            exported_snippets.append(card)

    # Final step: stitch the snippets into ONE reel, in plan order
    final_reel: Path | None = None
    if len(exported_snippets) >= 2:
        final_reel = _concat_snippets(exported_snippets, style=edit_plan.get("style", "reel"))
    elif len(exported_snippets) == 1:
        final_reel = exported_snippets[0]
        logger.info("Only one snippet exported – skipping concat (snippet IS the reel)")
    else:
        logger.warning("No snippets exported – nothing to concatenate")

    # Optional: lay a chosen music track over the finished reel
    if music_path is not None and final_reel is not None:
        _apply_music_bed(Path(final_reel), Path(music_path), clips, vision_data, jcut=jcut, sfx=sfx)


def _export_one_snippet(i: int, clip: dict, sync_data: dict | None, input_dir: Path | None = None) -> Path | None:
    """Export a single edit-plan clip to output/snippet_<idx>_<stem>.mp4.

    Thread-safe: YOLO tracking and its cache are serialized via _TRACKING_LOCK
    inside _tracked_x_center; the FFmpeg encode runs fully parallel.
    Returns the snippet path, or None on failure.
    """
    video = clip.get("video", "")
    start = clip.get("start", 0)
    end = clip.get("end", 0)
    lut = clip.get("lut", DEFAULT_LUT)
    vfx = clip.get("vfx", "none")
    slow_mo = clip.get("slow_mo", False)
    slow_mo_factor = clip.get("slow_mo_factor", 1.0)
    crop = clip.get("crop", "9:16")

    video_path = Path(video)
    if not video_path.exists():
        # Fallback to input_dir or INPUT_DIR
        if input_dir and (input_dir / video_path.name).exists():
            video_path = input_dir / video_path.name
        elif (INPUT_DIR / video_path.name).exists():
            video_path = INPUT_DIR / video_path.name

    if not video_path.exists():
        logger.warning(f"  Source not found: {video}")
        return None
        
    video = str(video_path)

    # Master Audio Sync Logic
    master_audio = None
    offset = 0.0
    if sync_data:
        ref_clip = sync_data.get("reference_clip", "")
        AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}
        if Path(ref_clip).suffix.lower() in AUDIO_EXTENSIONS:
            master_audio = ref_clip
            offset = sync_data.get("offsets", {}).get(video, 0.0)

    # Build FFmpeg filter chain
    vf_parts = []

    # Slow motion (applied first in chain)
    if slow_mo and slow_mo_factor > 1.0:
        vf_parts.append(f"setpts=PTS*{slow_mo_factor}")

    # Beat-reactive VFX: flash (brightness pop on the cut)
    # eq brightness range is [-1, 1]; 1.5 blew the frame out to pure white.
    if vfx == "flash":
        vf_parts.append("eq=brightness=0.4:enable='between(t,0,0.2)'")

    # Crop for 9:16 (mit JIT Auto-Framing, gecacht)
    if crop == "9:16":
        crop_x_expr = "(iw-ih*9/16)/2"  # Standard Center-Crop
        try:
            logger.info(f"  [{i + 1:02d}] JIT Auto-Framing: Tracking {Path(video).name} ({start:.1f}s - {end:.1f}s)...")
            avg_x = _tracked_x_center(video, start, end)
            if avg_x is not None:
                crop_x_expr = f"max(0,min(iw-ih*9/16,iw*{avg_x:.3f}-(ih*9/16)/2))"
                logger.info(f"       → Subject tracked at x_center={avg_x:.2f}. Dynamic crop applied.")
            else:
                logger.info(f"       → No subject found. Using center crop.")
        except Exception as e:
            logger.warning(f"       → JIT Auto-Framing failed: {e}. Using center crop.")

        # Escape commas: in an FFmpeg filtergraph a bare comma separates
        # filters, so min()/max() args would otherwise be torn apart.
        crop_x_expr = crop_x_expr.replace(",", "\\,")
        vf_parts.append(f"crop=ih*9/16:ih:{crop_x_expr}:0")
        vf_parts.append("scale=1080:1920")

        # Beat-reactive VFX: pump (zoom punch decaying over 0.3 s).
        # zoompan does not support the `enable` timeline option, so this
        # uses a per-frame scale + centered crop back to 1080x1920 instead.
        # Placed after the 9:16 crop so the frame size is known and the
        # image is not distorted.
        if vfx == "pump":
            zoom = "(1+0.05*max(0\\,1-t/0.3))"
            vf_parts.append(
                f"scale=w='trunc(1080*{zoom}/2)*2':h='trunc(1920*{zoom}/2)*2':eval=frame"
            )
            vf_parts.append("crop=1080:1920")

    # 3D-LUT color grading – relativer Pfad mit Forward-Slashes für FFmpeg
    lut_path = LUT_DIR / f"{lut}.cube"
    if lut_path.exists():
        rel_path = os.path.relpath(lut_path).replace("\\", "/")
        vf_parts.append(f"lut3d={rel_path}")
    else:
        logger.warning(f"  LUT not found: {lut_path}, using default")
        default_path = LUT_DIR / f"{DEFAULT_LUT}.cube"
        if default_path.exists():
            rel_path = os.path.relpath(default_path).replace("\\", "/")
            vf_parts.append(f"lut3d={rel_path}")

    # Beat-reactive VFX: glitch (machine-like black-frame stutter at the cut).
    # Three ~2-frame black bursts in the first 0.24s – the "single-digit frame
    # dropout" look for day→night transitions. Single quotes protect the commas
    # in the enable expression (same as flash). Placed last so the black frames
    # override the graded image.
    if vfx == "glitch":
        vf_parts.append(
            "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:"
            "enable='between(t,0,0.04)+between(t,0.1,0.14)+between(t,0.2,0.24)'"
        )

    # Normalize fps as the LAST filter so every snippet shares identical
    # video parameters (fps/pix_fmt/resolution) – this lets the final
    # concat stream-copy instead of re-encoding the whole reel.
    vf_parts.append(f"fps={REEL_FPS}")
    vf = ",".join(vf_parts)

    output_name = f"snippet_{i + 1:03d}_{Path(video).stem}.mp4"
    output_path = OUTPUT_DIR / output_name

    # Uniform encode params (audio too: mixed sample rates/channel counts
    # would break audio stream-copy concat).
    encode_params = [
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
    ]

    # Build FFmpeg command
    if master_audio and Path(master_audio).exists():
        # Extract video from video clip, audio from master audio (synchronized)
        master_start = max(0.0, start + offset)
        master_end = max(0.0, end + offset)
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(video),
            "-ss", f"{master_start:.3f}", "-to", f"{master_end:.3f}", "-i", str(master_audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            *encode_params,
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-to", f"{end:.3f}",
            "-i", str(video),
            "-vf", vf,
            *encode_params,
            "-movflags", "+faststart",
            str(output_path),
        ]

    logger.info(f"  [{i + 1:02d}] {Path(video).name} → {output_name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            size_kb = output_path.stat().st_size / 1024
            logger.info(f"  [{i + 1:02d}] ✓ Exported ({size_kb:.0f} KB)")
            return output_path
        logger.error(f"  [{i + 1:02d}] ✗ FFmpeg error: {result.stderr.strip()[-400:]}")
    except subprocess.TimeoutExpired:
        logger.error(f"  [{i + 1:02d}] ✗ Timeout exporting clip")
    except Exception as e:
        logger.error(f"  [{i + 1:02d}] ✗ Error: {e}")
    return None


def _concat_snippets(snippets: list[Path], style: str = "reel") -> Path | None:
    """
    Concatenate exported snippets into the final reel (output/reel_<style>.mp4).

    Re-encodes at a uniform frame rate: source clips recorded in slow-mo (e.g.
    120 fps phone footage) produce snippets with mixed fps, which breaks
    stream-copy concat timing.
    """
    output_path = OUTPUT_DIR / f"reel_{style}.mp4"
    list_path = OUTPUT_DIR / "concat_list.txt"

    # concat demuxer list; single quotes in paths escaped per FFmpeg syntax
    lines = [f"file '{str(p.resolve()).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"
             for p in snippets]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    logger.info(f"Concatenating {len(snippets)} snippets → {output_path.name}")

    # Fast path: snippets are exported with uniform fps/pix_fmt/resolution,
    # so the concat demuxer can stream-copy (seconds instead of minutes, and
    # no second encode generation degrading quality). Verify uniformity first
    # because mismatched streams would silently produce a broken file.
    if _snippets_uniform(snippets):
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"  ✓ Final reel (stream copy): {output_path} ({size_mb:.1f} MB)")
                return output_path
            logger.warning(f"  Stream-copy concat failed, falling back to re-encode: {result.stderr[-200:]}")
        except Exception as e:
            logger.warning(f"  Stream-copy concat error ({e}), falling back to re-encode")
    else:
        logger.info("  Snippets not uniform (mixed fps/resolution) – re-encoding concat")

    # Fallback: re-encode (slow on CPU – a full 90 s reel needs >10 min)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-vf", f"fps={REEL_FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ Final reel: {output_path} ({size_mb:.1f} MB)")
            return output_path
        logger.error(f"  ✗ Concat failed: {result.stderr[-300:]}")
    except subprocess.TimeoutExpired:
        logger.error("  ✗ Timeout concatenating reel")
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
    return None


def _snippets_uniform(snippets: list[Path]) -> bool:
    """True if all snippets share codec, resolution, fps and audio params."""
    signatures = set()
    for p in snippets:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
                 "-of", "csv=p=0", str(p)],
                capture_output=True, text=True, timeout=30,
            )
            if out.returncode != 0:
                return False
            signatures.add(out.stdout.strip())
        except Exception:
            return False
    return len(signatures) == 1


# ---------------------------------------------------------------------------
# Music overlay (energy-aligned background track)
# ---------------------------------------------------------------------------

# Tag → energy bonus (mirrors the highlight taxonomy in CLAUDE.md).
_TAG_ENERGY = {
    "CROWD_ENERGY": 0.8, "LIGHT_SHOW": 0.5, "DJ_SETUP": 0.3,
    "BREAKDOWN": 0.2, "TRANSITION": 0.1,
    "BACKSTAGE": 0.0, "ARRIVAL": 0.0, "PACKDOWN": 0.0, "UNUSABLE": -1.0,
}


def _clip_reel_duration(clip: dict) -> float:
    """Duration this clip occupies in the final reel (slow-mo stretches it)."""
    dur = float(clip.get("end", 0)) - float(clip.get("start", 0))
    if clip.get("slow_mo") and float(clip.get("slow_mo_factor", 1.0)) > 1.0:
        dur *= float(clip["slow_mo_factor"])
    return max(0.0, dur)


def _score_clip_energy(clip: dict, vision_data: dict | None) -> float:
    """Energy proxy for a clip from its source's vision tags."""
    if not vision_data:
        return 0.0
    entry = vision_data.get(clip.get("video", "")) or {}
    tags = entry.get("vision_tags_filtered") or entry.get("vision_tags") or []
    return sum(_TAG_ENERGY.get(t.get("tag", ""), 0.0) for t in tags)


def _reel_peak_time(clips: list[dict], vision_data: dict | None) -> tuple[float, float]:
    """
    (peak_time, total_duration) on the FINAL reel timeline.

    Peak = midpoint of the highest-energy clip. Falls back to a clip whose
    reason/transition mentions a drop/peak, then to 62 % of the reel.
    """
    if not clips:
        return 0.0, 0.0

    starts, durs, scores = [], [], []
    t = 0.0
    for c in clips:
        d = _clip_reel_duration(c)
        starts.append(t)
        durs.append(d)
        scores.append(_score_clip_energy(c, vision_data))
        t += d
    total = t

    best = max(range(len(clips)), key=lambda i: scores[i])
    if scores[best] > 0:
        return starts[best] + durs[best] / 2, total

    for i, c in enumerate(clips):
        text = f"{c.get('reason', '')} {c.get('transition', '')}".lower()
        if "drop" in text or "peak" in text:
            return starts[i] + durs[i] / 2, total

    return 0.62 * total, total


def _find_music_drop(music_path: Path, sr: int = 22050) -> float:
    """
    Self-contained drop detection: time of the steepest sustained rise in
    sub-200 Hz (bass) energy. Uses only librosa + numpy (no V2 config).
    """
    import numpy as np
    import librosa

    y, _ = librosa.load(str(music_path), sr=sr, mono=True)
    n_fft, hop = 2048, 512
    spec = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    bass = spec[freqs < 200].mean(axis=0)
    if bass.size < 4:
        return 0.0

    win = max(1, int(0.5 * sr / hop))  # ~0.5 s smoothing
    bass_s = np.convolve(bass, np.ones(win) / win, mode="same")
    deriv = np.diff(bass_s)
    times = librosa.frames_to_time(np.arange(len(deriv)), sr=sr, hop_length=hop)

    lo, hi = int(0.05 * len(deriv)), int(0.95 * len(deriv))  # trim edges
    if hi <= lo:
        return 0.0
    idx = lo + int(np.argmax(deriv[lo:hi]))
    return float(times[idx])


def _probe_duration(path: Path) -> float:
    """Media duration in seconds via ffprobe (0.0 on failure)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def _apply_music_bed(
    reel_path: Path, music_path: Path,
    clips: list[dict], vision_data: dict | None,
    jcut: bool = False, sfx: bool = False,
) -> None:
    """
    Replace the reel's audio with `music_path`, aligning the track's drop to
    the reel's energy peak. Adds a 1.5 s fade-out. Edits `reel_path` in place.

    When `jcut` is set (J-cut + lowpass), the music plays heavily lowpassed
    ("through the club door") until the drop lands on the reel peak, then the
    filter is removed and the full track slams in – building tension across
    the flashback before the visual arrival in the club.

    When `sfx` is set, synthetic "invisible" sound design is mixed in: a noise
    riser crescendoing into the drop and a sub-bass impact ON the drop. Both
    are generated in FFmpeg (no assets), positioned via the reel peak time.
    """
    if not music_path.exists():
        logger.warning(f"Music file not found: {music_path} – keeping original audio")
        return

    reel_dur = _probe_duration(reel_path)
    if reel_dur <= 0:
        logger.error("Could not probe reel duration – skipping music overlay")
        return

    peak_t, _ = _reel_peak_time(clips, vision_data)
    try:
        drop_t = _find_music_drop(music_path)
    except Exception as e:
        logger.warning(f"Drop detection failed ({e}); starting music at 0:00")
        drop_t = 0.0
    music_start = max(0.0, drop_t - peak_t)

    music_dur = _probe_duration(music_path)
    if music_dur and (music_dur - music_start) < reel_dur:
        logger.warning(
            f"Music ({music_dur:.0f}s, from {music_start:.1f}s) is shorter than the "
            f"reel ({reel_dur:.0f}s) – the tail will be silent/cut."
        )

    logger.info(
        f"🎵 Music overlay: drop@{drop_t:.1f}s → reel peak@{peak_t:.1f}s  "
        f"(track starts at {music_start:.1f}s)"
    )

    fade_start = max(0.0, reel_dur - 1.5)
    fade = f"afade=t=out:st={fade_start:.3f}:d=1.5"
    use_jcut = jcut and peak_t > 0.5
    use_sfx = sfx and peak_t > 0.5

    # Music processing graph from [1:a] → [mus].
    # J-cut as a SMOOTH filter sweep (not a binary switch): split into a
    # constant lowpassed base (kick/bass) + a highpass band whose volume
    # ramps 0→1 over ~1.5s ending on the drop. The highs "bloom" in, so the
    # filter opens gradually instead of snapping. FFmpeg can't time-automate a
    # lowpass cutoff directly, hence the split/fade-in trick.
    if use_jcut:
        sweep = 1.5
        sstart = max(0.0, peak_t - sweep)
        env = f"min(1,max(0,(t-{sstart:.3f})/{sweep:.3f}))"
        mus_graph = (
            f"[1:a]asplit=2[lo][hi];"
            f"[lo]lowpass=f=380[lo2];"
            f"[hi]highpass=f=380,volume='{env}':eval=frame[hi2];"
            f"[lo2][hi2]amix=inputs=2:normalize=0[mj];"
            f"[mj]{fade},aformat=channel_layouts=stereo[mus]"
        )
        logger.info(f"  🚪 J-cut: filter sweeps open over {sweep:.1f}s into the drop @ {peak_t:.1f}s")
    else:
        mus_graph = f"[1:a]{fade},aformat=channel_layouts=stereo[mus]"

    tmp_path = reel_path.with_name(reel_path.stem + "_music.mp4")
    base = ["ffmpeg", "-y", "-i", str(reel_path), "-ss", f"{music_start:.3f}", "-i", str(music_path)]
    tail = ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(tmp_path)]

    if use_sfx:
        # Synthetic SFX positioned by the reel peak: a noise riser ending ON
        # the drop + a sub-bass impact ON the drop, mixed over the music.
        # Levels modest (felt, not heard); amix normalize=0 = additive.
        riser_start_ms = int(max(0.0, peak_t - 2.5) * 1000)
        peak_ms = int(peak_t * 1000)
        filter_complex = (
            f"{mus_graph};"
            f"[2:a]highpass=f=300,volume='pow(t/2.5,2.5)':eval=frame,volume=0.30,"
            f"adelay={riser_start_ms}:all=1,aformat=channel_layouts=stereo[r];"
            f"[3:a]volume='exp(-t*6)':eval=frame,volume=3.0,"
            f"adelay={peak_ms}:all=1,aformat=channel_layouts=stereo[i];"
            f"[mus][r][i]amix=inputs=3:normalize=0:duration=first[a]"
        )
        cmd = base + [
            "-f", "lavfi", "-i", "anoisesrc=c=pink:d=2.5:a=0.7",
            "-f", "lavfi", "-i", "aevalsrc='0.5*sin(2*PI*48*t)+0.5*sin(2*PI*80*t)':d=0.8",
            "-filter_complex", filter_complex,
            "-map", "0:v:0", "-map", "[a]",
        ] + tail
        logger.info(f"  🔊 SFX: riser → drop @ {peak_t:.1f}s + sub-impact")
    elif use_jcut:
        cmd = base + ["-filter_complex", mus_graph, "-map", "0:v:0", "-map", "[mus]"] + tail
    else:
        cmd = base + ["-map", "0:v:0", "-map", "1:a:0", "-af", fade] + tail
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            tmp_path.replace(reel_path)
            logger.info(f"  ✓ Music applied → {reel_path.name}")
        else:
            logger.error(f"  ✗ Music overlay failed: {result.stderr.strip()[-400:]}")
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"  ✗ Music overlay error: {e}")
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    input_dir: Path = INPUT_DIR,
    preset: str = "highlight",
    duration: float = 60.0,
    phases: list[str] | None = None,
    style: str = "techno",
    provider: str = "",
    multi: bool = False,
    music: Path | None = None,
    jcut: bool = False,
    endcard: bool = False,
    sfx: bool = False,
):
    """Run the complete UNREEL V3 pipeline."""
    # Ensure directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Resolve --music path: try as-is, then input_dir, then INPUT_DIR
    if music is not None and not Path(music).exists():
        for candidate_dir in [input_dir, INPUT_DIR]:
            candidate = candidate_dir / Path(music).name
            if candidate.exists():
                logger.info(f"Music track found at {candidate}")
                music = candidate
                break
        if not Path(music).exists():
            logger.warning(f"Music file not found: {music}")


    # Phase 0: Ingestion & Renaming (Dedup + UNREEL_<timestamp>) yields the clip list
    video_paths = phase_ingest(input_dir)

    if not video_paths:
        logger.error(f"No video files found in {input_dir}")
        logger.info("Place your DJ footage in the 'input/' directory and re-run.")
        return

    logger.info(f"UNREEL V3 – Found {len(video_paths)} video(s)")
    for vp in video_paths:
        logger.info(f"  {vp.name}")

    # Show provider status at start
    providers = list_available_providers()
    logger.info("\n📡 AI Providers:")
    for p in providers:
        status = "✅" if p["available"] else "❌"
        logger.info(f"  {status} {p['name']:10s}  {p['model']}")

    all_results = {}
    results_path = OUTPUT_DIR / "pipeline_results.json"

    def _save_progress():
        """Persist results after each phase so a later crash never loses work."""
        serializable = json.loads(json.dumps(all_results, default=str))
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

    # Resume: ALWAYS seed from the last saved run when present. The expensive,
    # preset-independent analysis (audio sync, vision tagging) is then reused
    # across runs — only the preset-dependent phases (regie/copy/export) re-run.
    # A full run no longer wipes prior vision tags by starting from scratch.
    if results_path.exists():
        try:
            with open(results_path, encoding="utf-8") as f:
                all_results = json.load(f)
            logger.info(f"Resumed prior results from {results_path}")
        except Exception as e:
            logger.warning(f"Could not load prior results ({e}); starting fresh")

    # Phase 0: Setup (always run)
    if phases is None or "setup" in phases:
        all_results["luts"] = phase_0_setup()

    # Phase 1: Audio Sync + Kick/Snare (preset-independent → reuse cache).
    # Explicitly requesting --phase sync/analyze forces a recompute; a full
    # run reuses cached results if present.
    # Fix C: wenn --music übergeben aber music_analysis noch nicht im Cache,
    # Phase 1 + 2 erzwingen damit die neue Audiodatei analysiert wird.
    cached_p2 = all_results.get("phase_2") if isinstance(all_results.get("phase_2"), dict) else {}
    music_not_analyzed = (
        music is not None
        and Path(music).exists()
        and not cached_p2.get("music_analysis")
    )
    if music_not_analyzed:
        logger.info(
            f"New music file detected ({Path(music).name}) – forcing Phase 1+2 re-analysis"
        )

    sync_requested = phases is not None and ("sync" in phases or "analyze" in phases)
    if sync_requested or music_not_analyzed or (phases is None and not all_results.get("phase_1")):
        all_results["phase_1"] = phase_1_sync(video_paths, music_path=music)
        _save_progress()
    elif all_results.get("phase_1"):
        logger.info("✓ Reusing cached audio sync (phase_1)")

    # Phase 2: Video Analysis + Vision (resumable, saves after each clip)
    analyze_requested = phases is None or "vision" in phases or "analyze" in phases
    if analyze_requested or music_not_analyzed:
        prior_p2 = all_results.get("phase_2") if isinstance(all_results.get("phase_2"), dict) else None

        def _save_phase2(partial):
            all_results["phase_2"] = partial
            _save_progress()

        # music_path aus dem CLI-Argument übergeben
        phase2_music = music if music and Path(music).exists() else None
        all_results["phase_2"] = phase_2_analyze(video_paths, existing=prior_p2, save_cb=_save_phase2,
                                                  music_path=phase2_music)
        _save_progress()

    # Phase 3: AI Regie (multi-provider)
    if phases is None or "regie" in phases:
        # Tarantino preset: the prompt's phase timeline is hardcoded to 30s, so
        # the reel is ALWAYS 30s regardless of -d (matches COMMANDS.md). Without
        # this, e.g. -d 45 would feed the LLM contradictory durations.
        if preset == "tarantino" and duration != 30.0:
            logger.info(f"Tarantino preset: forcing reel duration 30.0s (was {duration:.0f}s)")
            duration = 30.0
        # Retention presets target 15–45s; if -d was left at the 60s default,
        # use a sensible 30s. An explicit -d in range is respected.
        elif preset in _RETENTION_PRESETS and duration == 60.0:
            logger.info(f"{preset} preset: defaulting reel duration to 30.0s (pass -d 15..45 to override)")
            duration = 30.0

        # Füge Musik-Analyse + pro-Video Audio-Analyse zum Context hinzu
        p2 = all_results.get("phase_2") or {}
        music_analysis = p2.get("music_analysis") if isinstance(p2, dict) else None
        if music_analysis and "error" not in music_analysis:
            # The LLM only needs the timing data, NOT the per-frame energy
            # envelopes (subbass_/bass_energy are thousands of points each →
            # would blow the prompt's token budget). Send a slimmed copy.
            slim = {k: v for k, v in music_analysis.items()
                    if k not in ("subbass_energy", "bass_energy")}
            all_results = {**all_results, "music_analysis": slim}
            logger.info(f"  Music analysis available: BPM={music_analysis.get('bpm', '?')}, "
                        f"{len(music_analysis.get('drop_times', []))} drops, "
                        f"{len(music_analysis.get('kick_times', []))} kicks")
        # Prüfe, ob pro-Video Audio-Analysen vorhanden sind
        audio_count = sum(1 for vp_str, entry in p2.items()
                          if isinstance(entry, dict) and "audio_analysis" in entry)
        if audio_count > 0:
            logger.info(f"  Per‑clip audio analysis available for {audio_count}/{len(p2)} videos")
        all_results["phase_3"] = phase_3_regie(
            all_results, preset, duration,
            provider=provider,
            multi=multi,
        )
        _save_progress()

    # Phase 4: Copywriting – fed with REAL analysis data: vision tags from
    # phase 2, narrative/hook from the edit plan, true clip durations.
    # Only the videos actually used in the plan are processed (not all input).
    if phases is None or "copy" in phases:
        bpm = all_results.get("phase_1", {}).get("percussion", {}).get("bpm", 140)
        p2 = all_results.get("phase_2") or {}
        plan = (all_results.get("phase_3") or {}).get("edit_plan") or {}
        plan_clips = plan.get("clips", [])
        narrative = plan.get("narrative", "")
        hook = plan.get("hook_text", "")
        scene = narrative or "DJ performance"
        if hook:
            scene = f"{scene} | Hook: {hook}"

        # Unique source videos in plan order; fall back to all inputs if no plan
        videos = list(dict.fromkeys(c.get("video", "") for c in plan_clips)) \
            if plan_clips else [str(vp) for vp in video_paths]

        clips_meta = []
        for v in videos:
            entry = p2.get(v) if isinstance(p2, dict) else None
            tag_names = [t.get("tag", "") for t in (entry or {}).get("vision_tags_filtered", [])]
            top_tags = [t for t, _ in Counter(tag_names).most_common(3) if t] or ["techno"]
            plan_dur = sum(
                c.get("duration", c.get("end", 0) - c.get("start", 0))
                for c in plan_clips if c.get("video") == v
            )
            peaks = [c.get("reason", "") for c in plan_clips
                     if c.get("video") == v and "drop" in c.get("reason", "").lower()]
            clips_meta.append({
                "bpm": bpm,
                "tags": top_tags,
                "duration": round(plan_dur) or 30,
                "scene": scene,
                "peak": peaks[0] if peaks else "bass drop",
            })
        all_results["phase_4"] = phase_4_copywriting(clips_meta, style=style)
        _save_progress()

    # Phase 5: Assembly
    if phases is None or "export" in phases:
        # Fix B: Wenn kein regie-Lauf in dieser Session stattfand, NICHT den
        # gecachten phase_3-Plan nehmen – stattdessen None übergeben, damit
        # phase_5_assembly() direkt output/edit_plan.json liest (das ist immer
        # der zuletzt von regie geschriebene, aktuelle Plan).
        regie_ran_this_session = phases is None or "regie" in (phases or [])
        if regie_ran_this_session:
            edit_plan = all_results.get("phase_3", {}).get("edit_plan")
        else:
            edit_plan = None  # phase_5_assembly liest output/edit_plan.json
            logger.info("Export: loading edit_plan.json directly (regie not in this session)")
        sync_data = all_results.get("phase_1", {}).get("sync")
        # J-cut/lowpass is the tarantino aesthetic by default; --jcut forces it
        # on for any preset.
        phase_5_assembly(
            edit_plan,
            sync_data=sync_data,
            music_path=music,
            vision_data=all_results.get("phase_2"),
            jcut=jcut or preset in _AUTO_JCUT_PRESETS,
            endcard=endcard or preset in _AUTO_ENDCARD_PRESETS,
            sfx=sfx or preset in _AUTO_SFX_PRESETS,
            input_dir=input_dir,
        )

    # Final save
    _save_progress()

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Results: {results_path}")
    logger.info(f"Output:  {OUTPUT_DIR}/")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UNREEL V3 – Automated DJ Video Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --input ./input --preset highlight --duration 60
  python -m src.main --input ./input --preset seamless_loop --duration 30
  python -m src.main --input ./input --provider gemini --phase regie
  python -m src.main --input ./input --provider deepseek --multi
  python -m src.main --input ./input --phase sync
  python -m src.main --luts
""",
    )

    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=INPUT_DIR,
        help="Input directory with video files (default: ./input)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--preset", "-p",
        choices=["highlight", "drop_focus", "seamless_loop", "moody", "pov_story", "tarantino", "artist_narrative", "booking", "community"],
        default="highlight",
        help="Edit preset style (default: highlight)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=60.0,
        help="Target reel duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--style", "-s",
        choices=["techno", "house", "minimal"],
        default="techno",
        help="Music style for captions (default: techno)",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "gemini", "deepseek", "auto"],
        default="",
        help="AI provider for regie phase (default: auto-detect from .env)",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Generate edit plans from ALL available AI providers for comparison",
    )
    parser.add_argument(
        "--music",
        type=Path,
        default=None,
        help="Lay a music track over the final reel (replaces original audio). "
             "The track's drop is auto-aligned to the reel's energy peak.",
    )
    parser.add_argument(
        "--jcut",
        action="store_true",
        help="J-cut + lowpass: music plays muffled ('through the club door') "
             "until the drop, then slams in. Auto-on for the tarantino preset.",
    )
    parser.add_argument(
        "--endcard",
        action="store_true",
        help="Append a brutalist animated logo endcard (LOGO/alt master.png). "
             "Auto-on for the tarantino preset.",
    )
    parser.add_argument(
        "--sfx",
        action="store_true",
        help="Mix synthetic invisible sound design (noise riser into the drop "
             "+ sub-bass impact). Needs --music. Auto-on for tarantino/artist_narrative.",
    )
    parser.add_argument(
        "--phase",
        nargs="*",
        choices=["setup", "sync", "vision", "regie", "copy", "export", "analyze"],
        help="Run specific phases only (analyze = sync+vision)",
    )
    parser.add_argument(
        "--luts",
        action="store_true",
        help="Generate LUT files only and exit",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Logging setup
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Generate LUTs only
    if args.luts:
        phase_0_setup()
        return

    # Run pipeline with CLI-provided paths
    run_pipeline(
        input_dir=args.input,
        preset=args.preset,
        duration=args.duration,
        phases=args.phase,
        style=args.style,
        provider=args.provider,
        multi=args.multi,
        music=args.music,
        jcut=args.jcut,
        endcard=args.endcard,
        sfx=args.sfx,
    )


if __name__ == "__main__":
    main()

\\n
### \analyzer/__init__.py\n
\\python
# analyzer package

\\n
### \analyzer/audio_analyzer.py\n
\\python
"""
Audio Analyzer für DJ-Performance Videos.
Erkennt Beat Drops, Buildups, Energie-Spitzen und Transitions.
"""

import numpy as np
import librosa
import subprocess
import os
import tempfile
import config


def extract_audio(video_path, output_path=None):
    """Extrahiert Audio aus einem Video als WAV-Datei."""
    if output_path is None:
        output_path = os.path.join(
            config.TEMP_DIR,
            os.path.splitext(os.path.basename(video_path))[0] + ".wav"
        )

    if os.path.exists(output_path):
        return output_path

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",  # kein Video
        "-acodec", "pcm_s16le",
        "-ar", str(config.AUDIO_SAMPLE_RATE),
        "-ac", "1",  # Mono
        "-y",  # Überschreiben
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
    except subprocess.TimeoutExpired:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(f"FFmpeg Timeout bei Audio-Extraktion (>120s): {video_path}")
    except subprocess.CalledProcessError as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(
            f"FFmpeg Fehler bei Audio-Extraktion: "
            f"{e.stderr.decode(errors='replace')[:300]}"
        )
    return output_path


def analyze_audio(video_path, progress_callback=None):
    """
    Führt vollständige Audio-Analyse durch.
    
    Returns:
        dict mit:
        - tempo: BPM
        - beat_times: Array von Beat-Zeitpunkten in Sekunden
        - energy_envelope: Onset-Strength über Zeit
        - energy_times: Zeitstempel für energy_envelope
        - energy_peaks: Zeitpunkte von Energie-Spitzen
        - bass_drops: Liste von {time, intensity} Bass-Drop-Events
        - buildups: Liste von {start, end, intensity} Buildup-Bereiche
        - breakdowns: Liste von {start, end} Breakdown-Bereiche
        - duration: Gesamtdauer in Sekunden
    """
    if progress_callback:
        progress_callback("audio", 0, "Audio wird extrahiert...")

    # Audio extrahieren
    audio_path = extract_audio(video_path)

    if progress_callback:
        progress_callback("audio", 15, "Audio wird geladen...")

    # Audio laden
    y, sr = librosa.load(audio_path, sr=config.AUDIO_SAMPLE_RATE)
    duration = librosa.get_duration(y=y, sr=sr)

    if progress_callback:
        progress_callback("audio", 25, "Beats werden erkannt...")

    # --- Beat Detection ---
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    # tempo kann ein Array sein in neueren librosa-Versionen
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=config.HOP_LENGTH)

    if progress_callback:
        progress_callback("audio", 40, "Energie wird analysiert...")

    # --- Energy/Onset Strength ---
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    energy_times = librosa.times_like(onset_env, sr=sr, hop_length=config.HOP_LENGTH)

    # Normalisieren
    if onset_env.max() > 0:
        onset_env_norm = onset_env / onset_env.max()
    else:
        onset_env_norm = onset_env

    # Energie-Peaks finden
    threshold = np.percentile(onset_env_norm, config.ENERGY_THRESHOLD_PERCENTILE)
    peak_indices = _find_peaks(onset_env_norm, threshold, min_distance_frames=int(sr / config.HOP_LENGTH * 0.5))
    energy_peaks = energy_times[peak_indices] if len(peak_indices) > 0 else np.array([])

    if progress_callback:
        progress_callback("audio", 55, "Bass Drops werden erkannt...")

    # --- Bass Drop Detection ---
    bass_drops = _detect_bass_drops(y, sr, energy_times)

    if progress_callback:
        progress_callback("audio", 70, "Buildups werden erkannt...")

    # --- Buildup / Breakdown Detection ---
    buildups, breakdowns = _detect_buildups_breakdowns(onset_env_norm, energy_times)

    if progress_callback:
        progress_callback("audio", 90, "Audio-Analyse abgeschlossen")

    results = {
        "tempo": tempo,
        "beat_times": beat_times.tolist(),
        "energy_envelope": onset_env_norm.tolist(),
        "energy_times": energy_times.tolist(),
        "energy_peaks": energy_peaks.tolist(),
        "bass_drops": bass_drops,
        "buildups": buildups,
        "breakdowns": breakdowns,
        "duration": duration,
    }

    if progress_callback:
        progress_callback("audio", 100, "Audio-Analyse fertig")

    # WAV-Datei nach erfolgreicher Analyse löschen (kein Nutzen als Cache,
    # da Ergebnisse in _analysis.json persistiert werden)
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except OSError:
        pass  # Nicht-kritisch – nächster Lauf extrahiert neu

    return results


def _find_peaks(signal, threshold, min_distance_frames=10):
    """Findet Peaks in einem Signal über einem Schwellenwert."""
    peaks = []
    i = 1
    while i < len(signal) - 1:
        if signal[i] > threshold and signal[i] > signal[i - 1] and signal[i] >= signal[i + 1]:
            peaks.append(i)
            i += min_distance_frames  # Mindestabstand
        else:
            i += 1
    return np.array(peaks)


def _detect_bass_drops(y, sr, energy_times):
    """Erkennt Bass Drops durch Analyse der tiefen Frequenzen."""
    bass_drops = []

    # Mel-Spektrogramm berechnen
    S = librosa.feature.melspectrogram(
        y=y, sr=sr,
        hop_length=config.HOP_LENGTH,
        n_mels=128,
        fmax=sr // 2
    )

    # Nur Bass-Frequenzen (untere Mel-Bänder, ca. < 200Hz)
    mel_freqs = librosa.mel_frequencies(n_mels=128, fmax=sr // 2)
    bass_mask = mel_freqs < config.BASS_FREQ_MAX
    bass_energy = np.sum(S[bass_mask], axis=0)

    # Normalisieren
    if bass_energy.max() > 0:
        bass_norm = bass_energy / bass_energy.max()
    else:
        return bass_drops

    # Zeitachse
    times = librosa.times_like(bass_norm, sr=sr, hop_length=config.HOP_LENGTH)

    # Bass Drops finden: plötzlicher Anstieg der Bass-Energie
    window_frames = int(config.BUILDUP_WINDOW_SEC * sr / config.HOP_LENGTH)

    for i in range(window_frames, len(bass_norm) - 1):
        # Vergleiche aktuelle Bass-Energie mit dem Durchschnitt der letzten Sekunden
        preceding_mean = np.mean(bass_norm[max(0, i - window_frames):i])
        if preceding_mean > 0:
            ratio = bass_norm[i] / preceding_mean
            if ratio >= config.MIN_DROP_ENERGY_RATIO and bass_norm[i] > 0.5:
                # Prüfe ob nicht zu nah am letzten Drop
                if len(bass_drops) == 0 or (times[i] - bass_drops[-1]["time"]) > 4.0:
                    bass_drops.append({
                        "time": float(times[i]),
                        "intensity": float(min(ratio / 4.0, 1.0))  # Normalisiert 0-1
                    })

    return bass_drops


def analyze_music_file(music_path: str) -> dict:
    """
    Analysiert eine eigenständige Audiodatei (mp3/wav/flac/aif/aiff)
    auf Bass, Subbass, Kicks, Transienten und Drops.
    
    Returns:
        dict with:
        - subbass_energy: Liste von (time, energy) für 20-60 Hz
        - bass_energy: Liste von (time, energy) für 60-250 Hz
        - kick_times: Liste von Zeitpunkten in Sekunden (Kick-Onsets)
        - transient_times: Liste von Zeitpunkten in Sekunden (Transienten)
        - drop_times: Liste von {time, intensity} für Bass-Drops
        - duration: Dauer in Sekunden
        - sample_rate: verwendete Abtastrate
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(music_path, sr=config.AUDIO_SAMPLE_RATE)
    duration = librosa.get_duration(y=y, sr=sr)

    # BPM & Beat-Times
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=config.HOP_LENGTH)

    # Mel-Spektrogramm für Frequenzbänder
    S = librosa.feature.melspectrogram(
        y=y, sr=sr,
        hop_length=config.HOP_LENGTH,
        n_mels=128,
        fmax=sr // 2
    )
    times = librosa.times_like(S, sr=sr, hop_length=config.HOP_LENGTH)

    # Frequenzbänder in Mel-Skala
    mel_freqs = librosa.mel_frequencies(n_mels=128, fmax=sr // 2)

    # Subbass: 20-60 Hz
    subbass_mask = (mel_freqs >= 20) & (mel_freqs < 60)
    subbass_energy = np.sum(S[subbass_mask], axis=0) if np.any(subbass_mask) else np.zeros(S.shape[1])
    subbass_norm = subbass_energy / (subbass_energy.max() + 1e-6)

    # Bass: 60-250 Hz
    bass_mask = (mel_freqs >= 60) & (mel_freqs < 250)
    bass_energy = np.sum(S[bass_mask], axis=0) if np.any(bass_mask) else np.zeros(S.shape[1])
    bass_norm = bass_energy / (bass_energy.max() + 1e-6)

    # Kick-Detektion: tiefe Frequenz (Subbass+Bass) + onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    onset_env_norm = onset_env / (onset_env.max() + 1e-6)

    # Kombinierte Kick-Energie (Subbass + onset)
    kick_energy = 0.6 * subbass_norm + 0.4 * onset_env_norm
    kick_threshold = np.percentile(kick_energy, 85)
    kick_peaks = _find_peaks2(kick_energy, kick_threshold, min_distance_frames=int(0.1 * sr / config.HOP_LENGTH))
    kick_times = times[kick_peaks].tolist() if len(kick_peaks) > 0 else []

    # Transienten: schnelle Anstiege im onset envelope (high-frequency content)
    transient_threshold = np.percentile(onset_env_norm, 90)
    trans_peaks = _find_peaks2(onset_env_norm, transient_threshold, min_distance_frames=int(0.05 * sr / config.HOP_LENGTH))
    transient_times = times[trans_peaks].tolist() if len(trans_peaks) > 0 else []

    # Drop-Detektion: steiler Anstieg der Bass-Energie (ähnlich _detect_bass_drops)
    drops = _detect_drops(bass_norm, times, sr)

    # Energie-Kurven als Listen von (time, value)
    subbass_list = [(float(times[i]), float(subbass_norm[i])) for i in range(len(times))]
    bass_list = [(float(times[i]), float(bass_norm[i])) for i in range(len(times))]

    return {
        "bpm": tempo,
        "beat_times": beat_times.tolist(),
        "subbass_energy": subbass_list,
        "bass_energy": bass_list,
        "kick_times": kick_times,
        "transient_times": transient_times,
        "drop_times": drops,
        "duration": duration,
        "sample_rate": sr,
    }


def _find_peaks2(signal: np.ndarray, threshold: float, min_distance_frames: int = 10) -> np.ndarray:
    """Findet Peaks in einem 1D-Signal (einfach, kein scipy)."""
    peaks = []
    i = 1
    while i < len(signal) - 1:
        if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] >= signal[i+1]:
            peaks.append(i)
            i += min_distance_frames
        else:
            i += 1
    return np.array(peaks)


def _detect_drops(bass_energy: np.ndarray, times: np.ndarray, sr: int) -> list:
    """
    Erkennt Drops als plötzlichen Anstieg der Bass-Energie.
    Gibt Liste von {time, intensity} zurück.
    """
    drops = []
    window_frames = int(1.0 * sr / config.HOP_LENGTH)  # 1 Sekunde Vergangenheit
    for i in range(window_frames, len(bass_energy) - 1):
        preceding_mean = np.mean(bass_energy[max(0, i - window_frames):i])
        if preceding_mean > 0 and bass_energy[i] > 0.5:
            ratio = bass_energy[i] / preceding_mean
            if ratio >= 2.0:  # Faktor 2 Anstieg
                # Abstand zu letztem Drop > 4 sec
                if len(drops) == 0 or (times[i] - drops[-1]["time"]) > 4.0:
                    drops.append({
                        "time": float(times[i]),
                        "intensity": float(min(ratio / 4.0, 1.0))
                    })
    return drops


def _detect_buildups_breakdowns(onset_env_norm, energy_times):
    """
    Erkennt Buildups (steigende Energie) und Breakdowns (fallende Energie).
    """
    buildups = []
    breakdowns = []

    # Glätten der Energie-Kurve
    window_size = 50  # Frames
    if len(onset_env_norm) < window_size * 2:
        return buildups, breakdowns

    smoothed = np.convolve(onset_env_norm, np.ones(window_size) / window_size, mode='same')

    # Gradient berechnen
    gradient = np.gradient(smoothed)

    # Positive Gradienten-Regionen = Buildups
    buildup_threshold = np.percentile(gradient[gradient > 0], 70) if np.any(gradient > 0) else 0.001
    breakdown_threshold = np.percentile(gradient[gradient < 0], 30) if np.any(gradient < 0) else -0.001

    # Zusammenhängende Regionen finden
    in_buildup = False
    buildup_start = 0

    for i in range(len(gradient)):
        if gradient[i] > buildup_threshold and not in_buildup:
            in_buildup = True
            buildup_start = i
        elif gradient[i] <= buildup_threshold * 0.5 and in_buildup:
            in_buildup = False
            start_time = float(energy_times[buildup_start])
            end_time = float(energy_times[min(i, len(energy_times) - 1)])
            duration = end_time - start_time
            if duration >= 2.0:  # Mindestens 2 Sekunden
                intensity = float(np.mean(gradient[buildup_start:i]) / max(buildup_threshold, 0.001))
                buildups.append({
                    "start": start_time,
                    "end": end_time,
                    "intensity": min(intensity, 1.0)
                })

    # Breakdowns: plötzlicher Energieabfall
    in_breakdown = False
    breakdown_start = 0

    for i in range(len(gradient)):
        if gradient[i] < breakdown_threshold and not in_breakdown:
            in_breakdown = True
            breakdown_start = i
        elif gradient[i] >= breakdown_threshold * 0.5 and in_breakdown:
            in_breakdown = False
            start_time = float(energy_times[breakdown_start])
            end_time = float(energy_times[min(i, len(energy_times) - 1)])
            duration = end_time - start_time
            if duration >= 1.0:
                breakdowns.append({
                    "start": start_time,
                    "end": end_time,
                })

    return buildups, breakdowns

\\n
### \analyzer/clip_exporter.py\n
\\python
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

\\n
### \analyzer/clip_normalizer.py\n
\\python
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

\\n
### \analyzer/copywriter.py\n
\\python
"""
UNREEL V3 – Copywriter Engine (Llama 3.2 / Qwen 3 via Ollama)
Generates filenames and Instagram captions for DJ video clips using a local
lightweight LLM. Runs entirely on CPU with 30+ tokens/sec.

Usage:
    from analyzer.copywriter import generate_caption, generate_filename, batch_process
"""

import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from analyzer.text_backends import get_text_backend

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_text_backend = None

def _get_text_backend():
    global _text_backend
    if _text_backend is None:
        _text_backend = get_text_backend()
    return _text_backend

FILENAME_PROMPT = """Generate a short, descriptive filename for a DJ video clip.
Rules:
- Max 40 characters
- lowercase with underscores only
- Format: adjective_scene_detail
- No special chars, no spaces, no numbers at start

Clip info:
- BPM: {bpm}
- Tags: {tags}
- Peak moment: {peak}
- Duration: {duration}s

Respond with ONLY the filename, nothing else. Example: dark_bassline_crowd_eruption"""

CAPTION_PROMPT = """Write an Instagram caption for a techno DJ video.
Rules:
- Max 200 characters
- Style: Hard Techno / Schranz / Underground
- Include 5-8 relevant hashtags
- Authentic, not cheesy
- Can use emojis sparingly

Clip info:
- BPM: {bpm}
- Tags: {tags}
- Scene: {scene}
- Vibe: {vibe}

Respond with ONLY the caption text, nothing else."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CopyResult:
    filename: str
    caption: str

    def to_dict(self) -> dict:
        return {"filename": self.filename, "caption": self.caption}


# ---------------------------------------------------------------------------
# Backend interaction
# ---------------------------------------------------------------------------

def _query_llm(prompt: str, temperature: float = 0.7) -> str:
    """Send a prompt to the local text backend and return the response text."""
    try:
        return _get_text_backend().complete(prompt, temperature=temperature)
    except Exception as e:
        logger.warning(f"Text backend copywriting error: {e}")
        return ""


def _clean_filename(raw: str) -> str:
    """Sanitize a generated filename."""
    # Remove quotes, extra whitespace
    cleaned = raw.strip().strip('"\'`')
    # Replace spaces/hyphens with underscores
    cleaned = re.sub(r"[\s\-]+", "_", cleaned)
    # Remove anything that's not alphanumeric or underscore
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned.lower())
    # Truncate
    cleaned = cleaned[:40]
    # Remove trailing underscores
    cleaned = cleaned.strip("_")
    return cleaned or "unnamed_clip"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_filename(
    clip_metadata: dict,
    model: str = "",
) -> str:
    """
    Generate a descriptive filename for a DJ clip.
    
    Args:
        clip_metadata: Dict with keys like 'bpm', 'tags', 'peak', 'duration'
    
    Returns:
        Clean filename string (e.g., 'dark_bassline_crowd_eruption')
    """
    prompt = FILENAME_PROMPT.format(
        bpm=clip_metadata.get("bpm", "unknown"),
        tags=", ".join(clip_metadata.get("tags", ["techno"])),
        peak=clip_metadata.get("peak", "bass drop"),
        duration=clip_metadata.get("duration", 30),
    )

    raw = _query_llm(prompt, temperature=0.5)
    filename = _clean_filename(raw)

    if not filename or filename == "unnamed_clip":
        # Fallback: build from metadata
        bpm = clip_metadata.get("bpm", 140)
        tag = clip_metadata.get("tags", ["techno"])[0].lower()
        filename = f"techno_{tag}_{bpm}bpm"

    logger.info(f"Generated filename: {filename}")
    return filename


def generate_caption(
    clip_metadata: dict,
    style: str = "techno",
    model: str = "",
) -> str:
    """
    Generate an Instagram caption for a DJ video clip.
    
    Args:
        clip_metadata: Dict with keys like 'bpm', 'tags', 'scene', 'vibe'
        style: Style preset ('techno', 'house', 'minimal')
    
    Returns:
        Caption string with hashtags
    """
    vibe_map = {
        "techno": "dark, underground, raw energy",
        "house": "groovy, uplifting, soulful",
        "minimal": "deep, hypnotic, subtle",
    }

    prompt = CAPTION_PROMPT.format(
        bpm=clip_metadata.get("bpm", "unknown"),
        tags=", ".join(clip_metadata.get("tags", ["techno"])),
        scene=clip_metadata.get("scene", "DJ performance"),
        vibe=vibe_map.get(style, vibe_map["techno"]),
    )

    caption = _query_llm(prompt, temperature=0.8)

    if not caption:
        # Fallback caption
        caption = (
            "When the bass hits different at 2am 🔊⚡ "
            f"#techno #hardtechno #schranz #djlife #raveCulture #underground"
        )

    # Ensure it's not too long for Instagram
    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    logger.info(f"Generated caption ({len(caption)} chars)")
    return caption


def batch_process(
    clips: list[dict],
    style: str = "techno",
    model: str = "",
) -> list[CopyResult]:
    """
    Process multiple clips and generate filenames + captions.
    
    Args:
        clips: List of clip metadata dicts
        style: Caption style preset
    
    Returns:
        List of CopyResult objects
    """
    results = []

    for i, clip_meta in enumerate(clips):
        logger.info(f"Copywriting clip {i + 1}/{len(clips)}...")
        filename = generate_filename(clip_meta, model=model)
        caption = generate_caption(clip_meta, style=style, model=model)
        results.append(CopyResult(filename=filename, caption=caption))

    return results


def save_captions(results: list[CopyResult], output_path: Path) -> None:
    """Save caption results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [{"filename": r.filename, "caption": r.caption} for r in results]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} captions to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.copywriter <command> [args]")
        print("  Commands: filename <bpm> <tags> | caption <bpm> <tags> | demo")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "demo":
        demo_meta = {"bpm": 145, "tags": ["CROWD_ENERGY", "DROP"], "peak": "bass drop", "duration": 30}
        print("Demo copywriting:\n")
        fn = generate_filename(demo_meta)
        cap = generate_caption(demo_meta)
        print(f"Filename: {fn}")
        print(f"Caption:  {cap}")
    elif cmd == "filename" and len(sys.argv) >= 4:
        meta = {"bpm": sys.argv[2], "tags": sys.argv[3:], "peak": "drop"}
        print(generate_filename(meta))
    elif cmd == "caption" and len(sys.argv) >= 4:
        meta = {"bpm": sys.argv[2], "tags": sys.argv[3:], "scene": "DJ set"}
        print(generate_caption(meta))
    else:
        print("Unknown command or missing args")

\\n
### \analyzer/frame_hasher.py\n
\\python
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

\\n
### \analyzer/highlight_engine.py\n
\\python
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

\\n
### \analyzer/local_regie_provider.py\n
\\python
"""
UNREEL – Lokaler Regie-Provider (zusätzliche Option, Cloud bleibt Default)

Fügt der regie_engine einen vierten Provider `local` hinzu, der dem
bestehenden RegieProvider-Protocol entspricht
(name, model_id, is_available(), call(...)).

ZWEI BACKENDS, per ENV wählbar (LOCAL_REGIE_ENGINE):

  "ollama" (Default) – nutzt Ollamas eingebautes `format=<json-schema>`
                       (XGrammar). Braucht laufenden Ollama-Dienst + Modell.

  "mlx"             – reines mlx-lm via `outlines` (from_mlxlm + output_type).
                      KEIN Ollama nötig. Outlines erzwingt schema-konformes JSON
                      durch constrained decoding (Schema→Regex→Token-Masking).

Hintergrund: Die Regie ist die anspruchsvollste KI-Aufgabe (langer JSON-Input +
Reasoning + striktes JSON-Output). Kleine lokale Modelle liefern OHNE
Schema-Constraint unzuverlässiges JSON. Beide Backends erzwingen daher gültiges
JSON – das lokale Äquivalent zum `response_format={"type":"json_object"}` des
DeepSeek-Providers.

ENV/config:
    LOCAL_REGIE_ENGINE  = "ollama" | "mlx"   (default: "ollama")
    LOCAL_REGIE_MODEL   = je nach Engine:
                            ollama: "qwen3.5:9b"
                            mlx:    "mlx-community/Qwen2.5-7B-Instruct-4bit"
    OLLAMA_HOST         (nur für ollama-Engine; bereits vorhanden)
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

# --- EditPlan-Schema (JSON-Schema-Dict, für die Ollama-Engine) --------------
# Felder matchen EditClip/EditPlan der regie_engine exakt.
EDIT_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "video": {"type": "string"},
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "transition": {"type": "string"},
                    "reason": {"type": "string"},
                    "crop": {"type": "string"},
                    "lut": {"type": "string"},
                    "vfx": {"type": "string"},
                    "slow_mo": {"type": "boolean"},
                    "slow_mo_factor": {"type": "number"},
                    "phase": {"type": "string"},
                },
                "required": ["video", "start", "end"],
            },
        },
        "narrative": {"type": "string"},
        "hook_text": {"type": "string"},
        "total_duration": {"type": "number"},
    },
    "required": ["clips"],
}


def _default_model(engine: str) -> str:
    if engine == "mlx":
        return os.environ.get(
            "LOCAL_REGIE_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit"
        )
    return os.environ.get("LOCAL_REGIE_MODEL", "qwen3.5:9b")


class LocalMLXProvider:
    """
    Lokaler Regie-Provider. Backend (ollama|mlx) per ENV LOCAL_REGIE_ENGINE.
    Erfüllt dasselbe Protocol wie ClaudeProvider/DeepSeekProvider.
    """

    def __init__(self, model: str | None = None, engine: str | None = None,
                 host: str | None = None):
        self._engine = (engine or os.environ.get("LOCAL_REGIE_ENGINE", "ollama")).lower()
        self._model = model or _default_model(self._engine)
        self._host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self._mlx_model = None      # lazy (nur mlx-Engine)
        self._mlx_tokenizer = None

    @property
    def name(self) -> str:
        return "local"

    @property
    def model_id(self) -> str:
        return self._model

    # ---- Verfügbarkeit -----------------------------------------------------
    def is_available(self) -> bool:
        if self._engine == "mlx":
            return self._mlx_available()
        return self._ollama_available()

    def _ollama_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status != 200:
                    return False
                tags = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return False
        names = [m.get("name", "") for m in tags.get("models", [])]
        base = self._model.split(":")[0]
        return any(n == self._model or n.startswith(base) for n in names)

    def _mlx_available(self) -> bool:
        try:
            import importlib.util
            return (importlib.util.find_spec("mlx_lm") is not None
                    and importlib.util.find_spec("outlines") is not None)
        except Exception:
            return False

    # ---- Aufruf ------------------------------------------------------------
    def call(self, system_prompt: str, user_data: str,
             temperature: float = 0.4, max_tokens: int = 8192) -> str:
        if self._engine == "mlx":
            return self._call_mlx(system_prompt, user_data, temperature, max_tokens)
        return self._call_ollama(system_prompt, user_data, temperature, max_tokens)

    def _call_ollama(self, system_prompt, user_data, temperature, max_tokens) -> str:
        try:
            import ollama
        except ImportError:
            raise ImportError("ollama not installed. Run: pip install ollama")

        logger.info("  → Calling %s (local/ollama, schema-constrained)…", self._model)
        client = ollama.Client(host=self._host)
        response = client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data},
            ],
            format=EDIT_PLAN_SCHEMA,
            options={"temperature": temperature, "num_predict": max_tokens,
                     "num_ctx": 8192},
        )
        return response["message"]["content"]

    def _call_mlx(self, system_prompt, user_data, temperature, max_tokens) -> str:
        """
        Reines mlx-lm via outlines. Erzwingt EditPlan-konformes JSON ohne Ollama.
        Outlines nimmt ein Pydantic-Modell als output_type; wir bauen es einmal.
        """
        try:
            import mlx_lm
            import outlines
        except ImportError:
            raise ImportError(
                "mlx engine needs: pip install \"outlines[mlxlm]\" mlx-lm"
            )

        logger.info("  → Calling %s (local/mlx via outlines, schema-constrained)…",
                    self._model)

        if self._mlx_model is None:
            self._mlx_model = outlines.from_mlxlm(*mlx_lm.load(self._model))

        # Pydantic-Schema für outlines (entspricht EDIT_PLAN_SCHEMA).
        from pydantic import BaseModel, Field

        class _EditClip(BaseModel):
            video: str
            start: float
            end: float
            transition: str = "cut"
            reason: str = ""
            crop: str = "9:16"
            lut: str = "underground_dark"
            vfx: str = "none"
            slow_mo: bool = False
            slow_mo_factor: float = 1.0
            phase: str = ""

        class _EditPlan(BaseModel):
            clips: list[_EditClip]
            narrative: str = ""
            hook_text: str = ""
            total_duration: float = 0.0

        # Chat-artiger Prompt: System + Daten in einen String (mlx-lm Tokenizer
        # mit Chat-Template wäre schöner, aber outlines nimmt hier den Prompt).
        prompt = f"{system_prompt}\n\n{user_data}\n\nReturn ONLY the JSON edit plan."
        result = self._mlx_model(prompt, output_type=_EditPlan,
                                 max_tokens=max_tokens)
        # outlines liefert bereits einen JSON-String (schema-konform).
        return result if isinstance(result, str) else json.dumps(result)

    def unload(self) -> None:
        self._mlx_model = None
        self._mlx_tokenizer = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    p = LocalMLXProvider()
    print(f"name={p.name} engine={p._engine} model={p.model_id}")
    print(f"available={p.is_available()}")
    print(f"schema keys={list(EDIT_PLAN_SCHEMA['properties'])}")

\\n
### \analyzer/text_backends.py\n
\\python
"""
UNREEL – Text-Backend-Abstraktion (Copywriter)

Selbes Muster wie vision_backends.py, aber für reine TEXT-Modelle
(Dateinamen + Instagram-Captions). Zwei austauschbare Implementierungen:

    - OllamaTextBackend → läuft überall, wo Ollama läuft (alter CPU-Rechner)
    - MLXTextBackend    → Apple Silicon, schnell, via mlx-lm

Umgeschaltet per ENV (TEXT_BACKEND="mlx" | "ollama").

Schnittstelle bewusst minimal: complete(prompt, temperature) -> str.
Das ersetzt das hardcodierte _query_ollama() in copywriter.py.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TextBackend(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        """Schickt `prompt` ans Modell, gibt den (gestrippten) Antworttext zurück."""

    def unload(self) -> None:
        """Optional: Modell aus dem RAM entladen (wichtig auf 16 GB)."""


# ---------------------------------------------------------------------------
# Backend 1: Ollama (Bestand)
# ---------------------------------------------------------------------------

class OllamaTextBackend(TextBackend):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self._host = host
        self._model = model

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        try:
            import ollama
        except ImportError:
            logger.warning("ollama package not installed. pip install ollama")
            return ""
        try:
            response = ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.warning("Ollama text error: %s", e)
            return ""


# ---------------------------------------------------------------------------
# Backend 2: MLX-LM (Apple Silicon)
# ---------------------------------------------------------------------------

class MLXTextBackend(TextBackend):
    """
    Text-Generierung via mlx-lm. Modell lazy geladen, unload() gibt RAM frei.

    API-Hinweis (recherchiert): neuere mlx-lm-Versionen nehmen `temperature`
    NICHT mehr direkt in generate(), sondern erwarten einen `sampler`
    (mlx_lm.sample_utils.make_sampler). Wir bauen den Sampler und probieren
    versionsrobust beide Aufruf-Varianten.
    """
    name = "mlx"

    def __init__(self, model: str, max_tokens: int = 256):
        self._model_id = model
        self._max_tokens = max_tokens
        self._model = None
        self._tokenizer = None

    def is_available(self) -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("mlx_lm") is not None
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from mlx_lm import load
        logger.info("Lade MLX-LM Textmodell: %s (einmalig)…", self._model_id)
        self._model, self._tokenizer = load(self._model_id)

    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        from mlx_lm import generate
        self._ensure_loaded()

        # Chat-Template anwenden (alle Instruct-Modelle erwarten das).
        messages = [{"role": "user", "content": prompt}]
        try:
            formatted = self._tokenizer.apply_chat_template(
                messages, add_generation_prompt=True
            )
        except Exception:
            formatted = prompt  # Fallback für Tokenizer ohne Chat-Template

        # Sampler bauen (neuere API). Fällt auf direkten temperature-Call zurück.
        try:
            from mlx_lm.sample_utils import make_sampler
            sampler = make_sampler(temp=temperature)
            try:
                out = generate(self._model, self._tokenizer, prompt=formatted,
                               max_tokens=self._max_tokens, sampler=sampler,
                               verbose=False)
            except TypeError:
                # noch neuere/ältere Signatur ohne 'sampler'-kw
                out = generate(self._model, self._tokenizer, formatted,
                               max_tokens=self._max_tokens, verbose=False)
        except ImportError:
            # sehr alte mlx-lm: temperature direkt
            out = generate(self._model, self._tokenizer, prompt=formatted,
                           max_tokens=self._max_tokens, temp=temperature,
                           verbose=False)

        text = out if isinstance(out, str) else getattr(out, "text", str(out))
        return text.strip()

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()
            logger.info("MLX-LM Textmodell entladen, Speicher freigegeben.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_text_backend() -> TextBackend:
    """
    ENV-Keys (Defaults):
        TEXT_BACKEND    = "ollama" | "mlx"                   (default: "ollama")
        MLX_TEXT_MODEL  = "mlx-community/Qwen2.5-7B-Instruct-4bit"
        OLLAMA_HOST, COPYWRITER_MODEL  (für das Ollama-Backend)
    """
    backend = os.environ.get("TEXT_BACKEND", "ollama").lower()

    if backend == "mlx":
        model = os.environ.get(
            "MLX_TEXT_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit"
        )
        return MLXTextBackend(model=model)

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("COPYWRITER_MODEL", "llama3.2")
    return OllamaTextBackend(host=host, model=model)

\\n
### \analyzer/tracking_engine.py\n
\\python
import cv2
import math
from ultralytics import YOLO

# Globale YOLO Modell-Instanz (wird lazy geladen, um Startzeit zu minimieren)
_model = None

def get_yolo_model():
    global _model
    if _model is None:
        # yolo11n.pt wird automatisch heruntergeladen, falls nicht lokal vorhanden
        _model = YOLO("yolo11n.pt")
    return _model

def sample_x_center(video_path, start_time=0.0, end_time=None, samples=10, imgsz=640):
    """
    Schneller JIT-Pfad für das Auto-Framing: Da der Export ohnehin nur den
    DURCHSCHNITT der x-Positionen nutzt (statischer Crop), reichen wenige
    direkt angesprungene Frames. Im Gegensatz zu analyze_tracking() wird
    nicht jeder Frame dekodiert (bei 120-fps-Material hunderte Reads),
    sondern pro Sample gezielt geseekt.

    Returns:
        Durchschnittliche normalisierte x-Position der größten Person
        (0.0–1.0) oder None, wenn keine Person gefunden wurde.
    """
    try:
        model = get_yolo_model()
    except Exception as e:
        print(f"YOLO konnte nicht geladen werden: {e}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    if end_time is None:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        end_time = (total / video_fps) if total > 0 else start_time + 1.0

    span = max(0.0, end_time - start_time)
    # Samples gleichmäßig im Fenster verteilen (Mittelpunkte der Teilstücke)
    times = [start_time + span * (i + 0.5) / samples for i in range(samples)]

    positions = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ret, frame = cap.read()
        if not ret:
            continue
        results = model.predict(frame, classes=[0], verbose=False, imgsz=imgsz)
        best, max_area = None, 0
        if len(results) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    best = float(((x1 + x2) / 2.0) / frame.shape[1])
        if best is not None:
            positions.append(best)

    cap.release()
    if not positions:
        return None
    return sum(positions) / len(positions)


def analyze_tracking(video_path, fps=1.0, start_time=0.0, end_time=None, progress_callback=None):
    """
    Führt YOLO-basiertes Tracking von Personen (Klasse 0) im Video durch.
    
    Args:
        video_path: Pfad zum Video
        fps: Wie viele Frames pro Sekunde für Tracking analysiert werden sollen (z.B. 1 oder 2)
        start_time: Startzeit in Sekunden (für Just-In-Time Tracking)
        end_time: Endzeit in Sekunden (für Just-In-Time Tracking)
        progress_callback: Callback für Fortschritt
        
    Returns:
        Liste von Dicts: [{"time": 0.0, "x_center": 0.5}, ...]
    """
    try:
        model = get_yolo_model()
    except Exception as e:
        print(f"YOLO konnte nicht geladen werden: {e}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30.0
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(video_fps / fps))
    
    tracking_data = []
    
    frame_idx = 0
    if start_time > 0.0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000.0)
        frame_idx = int(start_time * video_fps)
        
    analyzed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = frame_idx / video_fps
        if end_time is not None and current_time > end_time:
            break
            
        if frame_idx % frame_interval == 0:
            # Verkleinern für schnellere Inferenz (640px ist Standard für YOLOn)
            # YOLO skaliert intern sowieso, aber OpenCV resize spart Speicher/Zeit beim Übergeben
            results = model.predict(frame, classes=[0], verbose=False, imgsz=640)
            
            best_person = None
            max_area = 0
            
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    # box.xyxy: [x1, y1, x2, y2]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    if area > max_area:
                        max_area = area
                        # Mitte berechnen und normalisieren
                        x_center = (x1 + x2) / 2.0
                        norm_x = float(x_center / frame.shape[1])
                        best_person = norm_x
                        
            # Wenn Person gefunden, X-Koordinate speichern (sonst 0.5 als Fallback in der späteren Verarbeitung)
            if best_person is not None:
                tracking_data.append({
                    "time": round(current_time, 2),
                    "x_center": round(best_person, 4)
                })
                
            analyzed += 1
            if progress_callback and analyzed % 10 == 0:
                pct = int((frame_idx / max(total_frames, 1)) * 100)
                progress_callback("tracking", pct, f"Tracking: Frame {frame_idx}/{total_frames} (Auto-Framing)")

        frame_idx += 1
        
    cap.release()
    return tracking_data

\\n
### \analyzer/video_analyzer.py\n
\\python
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

\\n
### \analyzer/vision_backends.py\n
\\python
"""
UNREEL – Vision-Backend-Abstraktion

Problem (aus dem Audit): vision_engine.py spricht Ollama HARDCODIERT an.
Lösung: eine dünne Backend-Schicht. Dieselbe `tag_frames()`-Schnittstelle,
zwei austauschbare Implementierungen:

    - OllamaVisionBackend  → läuft überall, wo Ollama läuft (alter CPU-Rechner)
    - MLXVisionBackend     → Apple Silicon, schnell, via mlx-vlm

Umgeschaltet wird per config/ENV (VISION_BACKEND="mlx" | "ollama").
So läuft DASSELBE Repo auf beiden Maschinen ohne Fork.

Das Backend bekommt rohe Frames (timestamp, jpeg_bytes) + einen Prompt und
liefert den ROHEN Text der Modellantwort zurück. Das JSON-Parsing/Validieren
bleibt in vision_engine.py (eine Stelle, backend-unabhängig).
"""

from __future__ import annotations

import base64
import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VisionBackend(ABC):
    """Gemeinsame Schnittstelle für alle Vision-Backends."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """True, wenn das Backend einsatzbereit ist (Modell/Dienst vorhanden)."""

    @abstractmethod
    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        """
        Schickt `frames` (Liste aus (timestamp, jpeg_bytes)) zusammen mit
        `prompt` ans Modell und gibt den ROHEN Antworttext zurück.
        """

    def unload(self) -> None:
        """Optional: Modell aus dem RAM entladen (wichtig auf 16 GB)."""


# ---------------------------------------------------------------------------
# Backend 1: Ollama (Bestand – CPU/alte Maschine)
# ---------------------------------------------------------------------------

class OllamaVisionBackend(VisionBackend):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self._host = host
        self._model = model

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import ollama
        images = [base64.b64encode(b).decode("utf-8") for _, b in frames]
        response = ollama.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt, "images": images}],
            options={"temperature": 0.3},
        )
        return response["message"]["content"]


# ---------------------------------------------------------------------------
# Backend 2: MLX-VLM (Apple Silicon)
# ---------------------------------------------------------------------------

class MLXVisionBackend(VisionBackend):
    """
    Vision-Tagging via mlx-vlm (Apple Silicon).
    Modell wird LAZY geladen (erst beim ersten Aufruf) und kann via unload()
    wieder freigegeben werden – entscheidend auf 16 GB unified memory, damit
    danach das Text-/Caption-Modell Platz hat.

    MULTI-IMAGE:
    `frames_per_call` steuert, wie viele Frames pro Modellaufruf gebündelt
    werden. mlx-vlm unterstützt Multi-Image offiziell für Qwen2-VL, Pixtral
    und llava-interleaved. Bei Qwen2.5-VL ist Multi-Image NICHT offiziell
    gelistet – dort lieber bei frames_per_call=1 bleiben oder vorsichtig testen.
    Default 1 = robust für jedes Modell.
    """
    name = "mlx"

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
        frames_per_call: int = 1,
    ):
        self._model_id = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._frames_per_call = max(1, int(frames_per_call))
        self._model = None
        self._processor = None
        self._config = None

    def is_available(self) -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("mlx_vlm") is not None
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from mlx_vlm import load
        from mlx_vlm.utils import load_config
        logger.info("Lade MLX-VLM Modell: %s (einmalig)…", self._model_id)
        self._model, self._processor = load(self._model_id)
        # config liegt je nach Version am Modell oder via load_config vor.
        self._config = getattr(self._model, "config", None) or load_config(self._model_id)

    def _generate(self, formatted_prompt: str, image_paths: list[str]) -> str:
        """
        Versionsrobuster generate()-Aufruf.

        ACHTUNG: die Argument-Reihenfolge von mlx_vlm.generate() hat sich
        zwischen Versionen geändert:
            ältere:  generate(model, processor, images, prompt, ...)
            neuere:  generate(model, processor, prompt, images, ...)
        Außerdem nehmen neuere Versionen `temperature` NICHT mehr direkt,
        sondern erwarten den Default oder einen sampler. Wir versuchen die
        gängigen Signaturen der Reihe nach.
        """
        from mlx_vlm import generate

        attempts = [
            # neuere Signatur, mit temperature
            lambda: generate(self._model, self._processor, formatted_prompt,
                             image_paths, max_tokens=self._max_tokens,
                             temperature=self._temperature, verbose=False),
            # neuere Signatur, ohne temperature
            lambda: generate(self._model, self._processor, formatted_prompt,
                             image_paths, max_tokens=self._max_tokens, verbose=False),
            # ältere Signatur (images vor prompt)
            lambda: generate(self._model, self._processor, image_paths,
                             formatted_prompt, max_tokens=self._max_tokens, verbose=False),
        ]
        last_err = None
        for call in attempts:
            try:
                out = call()
                # neuere Versionen geben evtl. ein Result-Objekt statt str zurück
                return out if isinstance(out, str) else getattr(out, "text", str(out))
            except TypeError as e:
                last_err = e
                continue
        raise RuntimeError(f"mlx_vlm.generate() Signatur nicht erkannt: {last_err}")

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        """
        Bündelt Frames zu Gruppen der Größe `frames_per_call`, ruft das Modell
        je Gruppe auf und konkateniert die Roh-Antworten. vision_engine.py
        parst danach jede Teil-Antwort (Parsing ist robust gegen mehrere
        JSON-Blöcke).
        """
        import os
        import tempfile
        from mlx_vlm.prompt_utils import apply_chat_template

        self._ensure_loaded()
        out_parts: list[str] = []
        step = self._frames_per_call

        for i in range(0, len(frames), step):
            group = frames[i:i + step]
            tmp_paths: list[str] = []
            try:
                for _, jpeg in group:
                    fd, path = tempfile.mkstemp(suffix=".jpg")
                    with os.fdopen(fd, "wb") as fh:
                        fh.write(jpeg)
                    tmp_paths.append(path)

                index_hint = "\n".join(
                    f"- Image {j + 1}: frame at t={ts:.1f}s"
                    for j, (ts, _) in enumerate(group)
                )
                group_prompt = (
                    f"{prompt}\n\nThe images are provided in this order; "
                    f"use the matching timestamp as the 'time' value:\n{index_hint}"
                )
                formatted = apply_chat_template(
                    self._processor, self._config, group_prompt,
                    num_images=len(tmp_paths),
                )
                out_parts.append(self._generate(formatted, tmp_paths))
            finally:
                for p in tmp_paths:
                    try:
                        os.remove(p)
                    except OSError:
                        pass

        return "\n".join(out_parts)

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()  # gibt MLX-GPU-Speicher frei
            logger.info("MLX-VLM Modell entladen, Speicher freigegeben.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Backend 3: Gemini (Cloud – stark & schnell, batch-fähig)
# ---------------------------------------------------------------------------

class GeminiVisionBackend(VisionBackend):
    """
    Vision-Tagging über die Google-Gemini-Cloud (default gemini-2.5-flash).

    Gemini ist nativ multimodal und nimmt mehrere Bilder pro Aufruf entgegen –
    eine ganze Frame-Gruppe geht in EINEM Request raus. Stärker als die lokalen
    Modelle (weniger Fehl-Tags) und auf Cloud-GPUs deutlich schneller als
    CPU/MLX. `response_mime_type=application/json` erzwingt sauberes JSON.

    Privatsphäre-Hinweis: die Frames verlassen den Rechner. Bewusst per
    VISION_BACKEND=gemini opt-in, Default bleibt lokal.
    """
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import importlib.util
            return importlib.util.find_spec("google.generativeai") is not None
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(
            model_name=self._model,
            generation_config=genai.types.GenerationConfig(
                temperature=self._temperature,
                response_mime_type="application/json",
            ),
        )
        # One request: prompt text followed by all frames as inline JPEG blobs.
        parts: list = [prompt]
        for _, jpeg in frames:
            parts.append({"mime_type": "image/jpeg", "data": jpeg})

        response = model.generate_content(parts)
        return response.text


# ---------------------------------------------------------------------------
# Backend 4: Claude (Cloud – Fallback, ebenfalls multimodal)
# ---------------------------------------------------------------------------

class ClaudeVisionBackend(VisionBackend):
    """
    Vision-Tagging über Anthropic Claude. Fallback/Alternative zu Gemini.
    Das Modell muss Bild-Input unterstützen (Claude-Vision-fähige Modelle).
    Fable 5 may emit a thinking block first, so only text blocks are read.
    """
    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-fable-5",
                 temperature: float = 0.3, max_tokens: int = 2048):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import importlib.util
            return importlib.util.find_spec("anthropic") is not None
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        content: list = []
        for _, jpeg in frames:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.b64encode(jpeg).decode("utf-8"),
                },
            })
        content.append({"type": "text", "text": prompt})

        params = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": content}],
            temperature=self._temperature,
        )
        try:
            response = client.messages.create(**params)
        except anthropic.BadRequestError as exc:
            if "temperature" in str(exc).lower():
                params.pop("temperature", None)
                response = client.messages.create(**params)
            else:
                raise
        return "".join(
            b.text for b in response.content
            if getattr(b, "type", None) == "text"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_vision_backend() -> VisionBackend:
    """
    Wählt das Backend nach config/ENV.

    Erwartete config/ENV-Keys (mit Defaults):
        VISION_BACKEND   = "ollama" | "mlx" | "gemini" | "claude"  (default: "ollama")
        MLX_VISION_MODEL = z.B. "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"
        OLLAMA_HOST, GEMMA_MODEL          (für das Ollama-Backend)
        GEMINI_API_KEY, GEMINI_VISION_MODEL  (default: gemini-2.5-flash)
        ANTHROPIC_API_KEY, CLAUDE_VISION_MODEL
    """
    backend = os.environ.get("VISION_BACKEND", "ollama").lower()

    if backend == "gemini":
        key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("GEMINI_VISION_MODEL", "gemini-2.5-flash")
        return GeminiVisionBackend(api_key=key, model=model)

    if backend == "claude":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        model = os.environ.get("CLAUDE_VISION_MODEL", "claude-fable-5")
        return ClaudeVisionBackend(api_key=key, model=model)

    if backend == "mlx":
        model = os.environ.get(
            "MLX_VISION_MODEL",
            "mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
        )
        # frames_per_call=1 ist der sichere Default. Für offiziell multi-image-
        # fähige Modelle (Qwen2-VL, Pixtral, llava-interleaved) kann man via
        # MLX_VISION_FRAMES_PER_CALL z.B. 4 setzen → weniger Aufrufe, schneller.
        fpc = int(os.environ.get("MLX_VISION_FRAMES_PER_CALL", "1") or 1)
        return MLXVisionBackend(model=model, frames_per_call=fpc)

    # Default: Ollama
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
    return OllamaVisionBackend(host=host, model=model)

\\n
### \analyzer/vision_engine.py\n
\\python
"""
UNREEL V3 – Vision Engine (Gemma 4 E2B Scene Tagging)
Uses a local multimodal model via Ollama to analyze video frames and assign
semantic tags for DJ event footage.

Usage:
    from analyzer.vision_engine import tag_video_frames
    tags = tag_video_frames("input/clip1.mov")
    # → [{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "..."}]
"""

import json
import logging
import base64
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import cv2
from analyzer.vision_backends import get_vision_backend

logger = logging.getLogger(__name__)

_vision_backend = None

def _get_vision_backend():
    global _vision_backend
    if _vision_backend is None:
        _vision_backend = get_vision_backend()
    return _vision_backend

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

import os

SAMPLE_INTERVAL_SEC = 5  # Sample a frame every N seconds
# Frames per model call. Local models (small VRAM/context) want few; cloud
# models (Gemini/Claude) handle a whole clip at once → set VISION_BATCH_SIZE
# higher (e.g. 12) to cut calls and stay under free-tier RPM limits.
BATCH_SIZE = int(os.environ.get("VISION_BATCH_SIZE", "4") or 4)
CONFIDENCE_THRESHOLD = 0.3

VALID_TAGS = [
    "CROWD_ENERGY",
    "DJ_SETUP",
    "LIGHT_SHOW",
    "TRANSITION",
    "BREAKDOWN",
    "BACKSTAGE",
    "ARRIVAL",
    "PACKDOWN",
    "UNUSABLE",
]

TAG_BONUS_SCORES = {
    "CROWD_ENERGY": 0.8,
    "LIGHT_SHOW": 0.5,
    "DJ_SETUP": 0.3,
    "TRANSITION": 0.1,
    "BREAKDOWN": 0.2,
    "BACKSTAGE": 0.0,
    "ARRIVAL": 0.0,    # Story-only (pov_story "before"); no highlight bonus
    "PACKDOWN": 0.0,   # Story-only (pov_story "after"); no highlight bonus
    "UNUSABLE": -1.0,
}

SYSTEM_PROMPT = """You are a professional video analyst specializing in electronic music events.
Analyze the provided DJ event frames and classify each one.

For EACH frame, provide:
- "time": the timestamp in seconds (float)
- "tag": exactly one of: CROWD_ENERGY, DJ_SETUP, LIGHT_SHOW, TRANSITION, BREAKDOWN, BACKSTAGE, ARRIVAL, PACKDOWN, UNUSABLE
- "confidence": your confidence level from 0.0 to 1.0
- "description": a brief German description (max 20 words)

Guidelines:
- CROWD_ENERGY: Audience dancing, hands up, crowd visible and active
- DJ_SETUP: Focus on DJ equipment, decks, mixer, laptop
- LIGHT_SHOW: Dominant light effects, lasers, strobes, visuals
- TRANSITION: DJ switching tracks, calm between sections
- BREAKDOWN: Musical breakdown, calmer moment, less movement
- BACKSTAGE: Behind the scenes, non-performance areas (generic, not clearly arrival/packdown)
- ARRIVAL: BEFORE the set — arriving at the venue, loading in gear, getting ready, soundcheck, empty room filling up, walking to the booth
- PACKDOWN: AFTER the set — last track ending, packing up gear, crowd leaving, empty floor, lights on, the quiet afterwards
- UNUSABLE: Blurry, too dark, pointless footage

Respond ONLY with valid JSON. No markdown fences. Format:
[{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "Crowd geht ab bei Drop"}]
"""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FrameTag:
    time: float
    tag: str
    confidence: float
    description: str

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "tag": self.tag,
            "confidence": self.confidence,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_sample_frames(
    video_path: str | Path,
    interval_sec: float = SAMPLE_INTERVAL_SEC,
) -> list[tuple[float, bytes]]:
    """
    Extract frames from a video at regular intervals.
    Returns list of (timestamp_seconds, jpeg_bytes).

    Primary path uses OpenCV. OpenCV ships its own FFmpeg build that
    occasionally fails to open perfectly valid h264 clips ("Could not open
    codec h264"); when that happens we fall back to the system ffmpeg, which
    decodes far more reliably.
    """
    path = str(video_path)
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        logger.warning(f"OpenCV cannot open {Path(path).name} – trying system ffmpeg")
        return _extract_frames_ffmpeg(path, interval_sec)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    interval_frames = int(fps * interval_sec)
    samples: list[tuple[float, bytes]] = []

    logger.info(f"Extracting frames from {Path(path).name} "
                f"({duration:.1f}s, every {interval_sec}s ≈ {int(duration / interval_sec)} frames)")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if interval_frames > 0 and frame_idx % interval_frames == 0:
            timestamp = frame_idx / fps
            # Encode as JPEG for smaller payload
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            samples.append((timestamp, jpeg.tobytes()))

        frame_idx += 1

    cap.release()

    # OpenCV opened the file but produced no frames (codec init failed
    # mid-stream) – fall back to system ffmpeg before giving up.
    if not samples:
        logger.warning(f"OpenCV extracted 0 frames from {Path(path).name} – trying system ffmpeg")
        return _extract_frames_ffmpeg(path, interval_sec)

    logger.info(f"  Extracted {len(samples)} sample frames")
    return samples


def _extract_frames_ffmpeg(
    path: str,
    interval_sec: float = SAMPLE_INTERVAL_SEC,
) -> list[tuple[float, bytes]]:
    """
    Fallback frame extraction via the system ffmpeg binary (subprocess).
    Decodes one JPEG every `interval_sec` using `-vf fps=1/interval` and
    splits the concatenated MJPEG stream on JPEG SOI/EOI markers.
    """
    import subprocess

    cmd = [
        "ffmpeg", "-v", "error",
        "-i", path,
        "-vf", f"fps=1/{interval_sec},scale=-2:480",
        "-q:v", "5",
        "-f", "image2pipe", "-c:v", "mjpeg", "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=300)
    except Exception as e:
        raise IOError(f"Cannot open video (ffmpeg fallback failed): {path} ({e})")

    data = proc.stdout
    if proc.returncode != 0 or not data:
        tail = proc.stderr.decode(errors="replace")[-200:]
        raise IOError(f"Cannot open video (ffmpeg fallback): {path} – {tail}")

    # Split concatenated JPEGs on SOI (FFD8) … EOI (FFD9) markers.
    samples: list[tuple[float, bytes]] = []
    start = data.find(b"\xff\xd8")
    idx = 0
    while start != -1:
        end = data.find(b"\xff\xd9", start)
        if end == -1:
            break
        jpeg = data[start:end + 2]
        samples.append((idx * interval_sec, jpeg))
        idx += 1
        start = data.find(b"\xff\xd8", end + 2)

    if not samples:
        raise IOError(f"Cannot open video: {path} (no frames via ffmpeg)")

    logger.info(f"  Extracted {len(samples)} sample frames (ffmpeg fallback)")
    return samples


# ---------------------------------------------------------------------------
# API interaction
# ---------------------------------------------------------------------------

def _analyze_frames_batch(
    frames: list[tuple[float, bytes]],
    model: str = "",
) -> list[FrameTag]:
    """
    Send a batch of frames to the Ollama multimodal model for analysis.
    Uses the ollama Python library (pip install ollama).
    """
    # Build the message format
    frame_index = "\n".join(
        f"- Image {i + 1}: frame at t={timestamp:.1f}s"
        for i, (timestamp, _) in enumerate(frames)
    )
    user_text = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Analyze these {len(frames)} frames. The images are provided in this order, "
        f"use the matching timestamp as the 'time' value:\n"
        f"{frame_index}"
    )

    try:
        raw = _get_vision_backend().describe_frames(user_text, frames)
    except Exception as e:
        logger.warning(f"Vision backend API error: {e}")
        return []

    # Parse JSON from response
    try:
        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # The model may emit one JSON array per image (concatenated), a single
        # array, or a bare object. Decode every top-level JSON value and flatten.
        parsed = []
        decoder = json.JSONDecoder()
        idx, n = 0, len(cleaned)
        while idx < n:
            while idx < n and cleaned[idx] in " \t\r\n,":
                idx += 1
            if idx >= n:
                break
            try:
                value, end = decoder.raw_decode(cleaned, idx)
            except json.JSONDecodeError:
                break
            if isinstance(value, list):
                parsed.extend(value)
            elif isinstance(value, dict):
                parsed.append(value)
            idx = end

        if not parsed:
            logger.warning(f"No JSON parsed from vision response.\nRaw: {raw[:200]}")
            return []

        tags = []
        for entry in parsed:
            tag = entry.get("tag", "UNUSABLE")
            if tag not in VALID_TAGS:
                tag = "UNUSABLE"
            tags.append(FrameTag(
                time=float(entry.get("time", 0)),
                tag=tag,
                confidence=float(entry.get("confidence", 0.5)),
                description=entry.get("description", ""),
            ))
        return tags

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse vision response: {e}\nRaw: {raw[:200]}")
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tag_video_frames(
    video_path: str | Path,
    sample_interval_sec: float = SAMPLE_INTERVAL_SEC,
    model: str = "",
) -> list[FrameTag]:
    """
    Analyze a video file and return semantic tags for sampled frames.
    
    Falls back gracefully if backend is not available (returns empty list).
    """
    if not _get_vision_backend().is_available():
        logger.warning("Vision backend not available. Skipping vision tagging.")
        return []

    # Extract sample frames
    frames = extract_sample_frames(video_path, interval_sec=sample_interval_sec)
    if not frames:
        return []

    # Process in batches
    all_tags: list[FrameTag] = []
    for i in range(0, len(frames), BATCH_SIZE):
        batch = frames[i : i + BATCH_SIZE]
        logger.info(f"  Analyzing batch {i // BATCH_SIZE + 1}/{(len(frames) + BATCH_SIZE - 1) // BATCH_SIZE}...")
        tags = _analyze_frames_batch(batch, model=model)
        all_tags.extend(tags)

    _get_vision_backend().unload()
    logger.info(f"  Got {len(all_tags)} tags from vision model")
    return all_tags


def filter_unusable(tags: list[FrameTag], min_confidence: float = CONFIDENCE_THRESHOLD) -> list[FrameTag]:
    """Remove UNUSABLE tags and low-confidence entries."""
    return [t for t in tags if t.tag != "UNUSABLE" and t.confidence >= min_confidence]


def get_tag_scores(tags: list[FrameTag]) -> dict[str, float]:
    """
    Convert tags to a score dictionary for the highlight engine.
    Returns {timestamp_range_key: bonus_score}.
    """
    scores = {}
    for tag in tags:
        key = f"{tag.time:.1f}"
        scores[key] = scores.get(key, 0.0) + TAG_BONUS_SCORES.get(tag.tag, 0.0) * tag.confidence
    return scores


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.vision_engine <video_path>")
        sys.exit(1)

    video = sys.argv[1]
    print(f"Analyzing {video}...")

    tags = tag_video_frames(video)
    for t in tags:
        print(f"  t={t.time:6.1f}s  {t.tag:15s}  conf={t.confidence:.2f}  {t.description}")

    print(f"\nFiltered (unusable removed):")
    filtered = filter_unusable(tags)
    for t in filtered:
        print(f"  t={t.time:6.1f}s  {t.tag:15s}  conf={t.confidence:.2f}")

\\n
### \analyzer/watermark_detector.py\n
\\python
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

\\n
### \tests/__init__.py\n
\\python

\\n
### \tests/test_audio_sync.py\n
\\python
"""Offline tests for audio_sync.py – cross-correlation on synthetic signals."""
import unittest
import json
import tempfile
from pathlib import Path

import numpy as np

import audio_sync as asy


class TestRms(unittest.TestCase):
    def test_rms_of_constant(self):
        y = np.full(1000, 0.5, dtype=np.float32)
        self.assertAlmostEqual(asy._compute_rms(y), 0.5, places=5)

    def test_rms_of_silence(self):
        self.assertAlmostEqual(asy._compute_rms(np.zeros(1000)), 0.0, places=6)


class TestComputeOffset(unittest.TestCase):
    def test_detects_known_shift(self):
        sr = 8000
        rng = np.random.default_rng(42)
        base = rng.standard_normal(sr * 2).astype(np.float32)  # 2 seconds of noise

        shift = 400  # samples = 0.05 s
        ref = base
        # target is the reference delayed by `shift` samples (starts later)
        target = np.concatenate([np.zeros(shift, dtype=np.float32), base])[: len(base)]

        offset = asy.compute_offset(ref, target, sr=sr)
        # Magnitude of the detected lag must match the injected shift.
        self.assertAlmostEqual(abs(offset), shift / sr, places=2)

    def test_zero_offset_for_identical(self):
        sr = 8000
        rng = np.random.default_rng(7)
        y = rng.standard_normal(sr).astype(np.float32)
        self.assertAlmostEqual(asy.compute_offset(y, y, sr=sr), 0.0, places=3)


class TestSyncResult(unittest.TestCase):
    def test_to_dict_and_save_roundtrip(self):
        res = asy.SyncResult(
            reference_clip="a.mov",
            offsets={"a.mov": 0.0, "b.mov": 1.234},
            rms_values={"a.mov": 0.1234567, "b.mov": 0.05},
            sample_rate=44100,
        )
        d = res.to_dict()
        self.assertEqual(d["reference_clip"], "a.mov")
        self.assertEqual(d["offsets"]["b.mov"], 1.234)
        # rms values are rounded to 6 places in to_dict
        self.assertEqual(d["rms_values"]["a.mov"], 0.123457)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sub" / "sync.json"
            res.save(p)
            self.assertTrue(p.exists())
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["reference_clip"], "a.mov")


class TestSyncGuards(unittest.TestCase):
    def test_sync_all_clips_requires_two(self):
        with self.assertRaises(ValueError):
            asy.sync_all_clips(["only_one.mov"])


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_config.py\n
\\python
"""Offline tests for config.py – paths and constants (no secrets required)."""
import unittest
from pathlib import Path

import config


class TestConfigPaths(unittest.TestCase):
    def test_base_dir_is_repo_root(self):
        # config.py lives at the repo root, so BASE_DIR must be that root.
        self.assertEqual(config.BASE_DIR, Path(config.__file__).resolve().parent)

    def test_derived_dirs_under_base(self):
        for d in (config.INPUT_DIR, config.OUTPUT_DIR, config.LUT_DIR):
            self.assertEqual(d.parent, config.BASE_DIR)

    def test_lut_dir_created(self):
        # config.py mkdir's the LUT dir on import.
        self.assertTrue(config.LUT_DIR.exists())


class TestConfigConstants(unittest.TestCase):
    def test_available_luts(self):
        self.assertEqual(
            set(config.AVAILABLE_LUTS),
            {"underground_dark", "vhs_analog", "neon_nights"},
        )

    def test_tag_bonus_scores(self):
        self.assertAlmostEqual(config.TAG_BONUS_SCORES["CROWD_ENERGY"], 0.8)
        self.assertAlmostEqual(config.TAG_BONUS_SCORES["UNUSABLE"], -1.0)

    def test_fallback_order(self):
        # DeepSeek is the primary provider in the auto-hierarchy.
        self.assertEqual(
            config.REGIE_PROVIDER_FALLBACK_ORDER,
            ["deepseek", "claude", "gemini"],
        )

    def test_reel_dimensions_are_vertical(self):
        self.assertEqual((config.REEL_WIDTH, config.REEL_HEIGHT), (1080, 1920))


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_copywriter.py\n
\\python
"""Offline tests for copywriter.py – sanitizing + graceful degradation (Ollama mocked)."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest import mock

import analyzer.copywriter as cw


class TestCleanFilename(unittest.TestCase):
    def test_spaces_and_case(self):
        self.assertEqual(cw._clean_filename("Dark Bassline Crowd"), "dark_bassline_crowd")

    def test_strips_special_chars(self):
        self.assertEqual(cw._clean_filename('"Dark!! Drop@2am"'), "dark_drop2am")

    def test_truncates_to_40(self):
        out = cw._clean_filename("a" * 80)
        self.assertLessEqual(len(out), 40)

    def test_empty_falls_back(self):
        self.assertEqual(cw._clean_filename("!!!"), "unnamed_clip")

    def test_strips_trailing_underscores(self):
        self.assertEqual(cw._clean_filename("__hello__"), "hello")


class TestGenerateFilename(unittest.TestCase):
    def test_uses_model_output(self):
        with mock.patch.object(cw, "_query_llm", return_value="Dark Bassline Crowd"):
            self.assertEqual(cw.generate_filename({"bpm": 140, "tags": ["techno"]}),
                             "dark_bassline_crowd")

    def test_fallback_when_offline(self):
        # Ollama unavailable -> empty response -> metadata-based fallback.
        with mock.patch.object(cw, "_query_llm", return_value=""):
            name = cw.generate_filename({"bpm": 145, "tags": ["CROWD_ENERGY"]})
            self.assertEqual(name, "techno_crowd_energy_145bpm")


class TestGenerateCaption(unittest.TestCase):
    def test_uses_model_output(self):
        with mock.patch.object(cw, "_query_llm", return_value="raw techno energy #techno"):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertEqual(cap, "raw techno energy #techno")

    def test_fallback_when_offline(self):
        with mock.patch.object(cw, "_query_llm", return_value=""):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertIn("#techno", cap)

    def test_truncates_overlong(self):
        long = "x" * 3000
        with mock.patch.object(cw, "_query_llm", return_value=long):
            cap = cw.generate_caption({"bpm": 140, "tags": ["techno"]})
            self.assertLessEqual(len(cap), 2200)


class TestBatchAndSave(unittest.TestCase):
    def test_batch_and_save(self):
        clips = [{"bpm": 140, "tags": ["techno"]}, {"bpm": 150, "tags": ["house"]}]
        with mock.patch.object(cw, "_query_llm", return_value=""):
            results = cw.batch_process(clips)
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], cw.CopyResult)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "caps.json"
            cw.save_captions(results, p)
            loaded = json.loads(p.read_text())
            self.assertEqual(len(loaded), 2)
            self.assertIn("filename", loaded[0])
            self.assertIn("caption", loaded[0])


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_ingest.py\n
\\python
"""
Tests für analyzer/ingest.py – Ingestion & Renaming (Phase 0).

Stil-konsistent zu den übrigen tests/: keine echten Videos, ffprobe wird
über den mtime-Fallback umgangen (für Dummy-Dateien hat ffprobe keine
creation_time, also greift automatisch os.path.getmtime).
"""

import os
import time

import pytest

import ingest


@pytest.fixture
def src(tmp_path, monkeypatch):
    """Isolierter Input-Ordner + gemocktes config.SUPPORTED_EXTENSIONS."""
    monkeypatch.setattr(ingest.config, "VIDEO_SOURCE_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4", ".mov"], raising=False)
    return tmp_path


def _make(path, content: bytes, ts: float | None = None):
    path.write_bytes(content)
    if ts is not None:
        os.utime(path, (ts, ts))
    return path


def _ts(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def test_renames_to_timestamp(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "raw_clip.mp4", b"A" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250612_143000.mp4").exists()
    assert not (src / "raw_clip.mp4").exists()
    assert len(result.renamed) == 1


def test_removes_duplicates(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "a.mp4", b"SAME" * 1000, base)
    _make(src / "b.mp4", b"SAME" * 1000, base + 10)  # identischer Inhalt

    result = ingest.ingest_directory(src)

    remaining = [f for f in os.listdir(src) if f.endswith(".mp4")]
    assert len(remaining) == 1
    assert len(result.duplicates_removed) == 1


def test_skips_hidden_and_unsupported(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "._hidden.mp4", b"x", base)
    _make(src / "notes.txt", b"hello", base)

    result = ingest.ingest_directory(src)

    assert result.renamed == []
    assert result.duplicates_removed == []
    assert (src / "._hidden.mp4").exists()
    assert (src / "notes.txt").exists()


def test_keeps_already_named_files(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "UNREEL_20250101_000000.mp4", b"C" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250101_000000.mp4").exists()
    assert result.renamed == []
    assert str(src / "UNREEL_20250101_000000.mp4") in result.final_files


def test_timestamp_collision_gets_counter(src):
    base = _ts("2025-06-12 14:30:00")
    # Zwei unterschiedliche Inhalte, gleiche Endung, gleicher Timestamp.
    _make(src / "first.mp4", b"FIRST" * 1000, base)
    _make(src / "second.mp4", b"SECND" * 1000, base)

    ingest.ingest_directory(src)

    names = sorted(f for f in os.listdir(src) if f.startswith("UNREEL_"))
    assert "UNREEL_20250612_143000.mp4" in names
    assert "UNREEL_20250612_143000_1.mp4" in names


def test_final_files_feeds_pipeline(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "x.mp4", b"X" * 4000, base)
    _make(src / "UNREEL_20250101_000000.mov", b"Y" * 4000, base)

    result = ingest.ingest_directory(src)

    # final_files enthält genau die Dateien, die danach existieren & verarbeitbar sind.
    for p in result.final_files:
        assert os.path.exists(p)
    assert len(result.final_files) == 2


def test_missing_source_dir_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4"], raising=False)
    result = ingest.ingest_directory(tmp_path / "does_not_exist")
    assert result.final_files == []
    assert result.errors == []

\\n
### \tests/test_kick_snare_detector.py\n
\\python
"""Offline tests for kick_snare_detector.py – dataclasses and beat grid logic."""
import unittest
import json
import tempfile
from pathlib import Path

import kick_snare_detector as ksd


class TestDataclasses(unittest.TestCase):
    def test_hit_to_dict_rounds(self):
        hit = ksd.PercussiveHit(time=1.23456, intensity=0.987654)
        self.assertEqual(hit.to_dict(), {"time": 1.235, "intensity": 0.988})

    def test_map_to_dict_counts(self):
        pm = ksd.PercussionMap(
            kicks=[ksd.PercussiveHit(0.5, 0.9), ksd.PercussiveHit(1.0, 0.8)],
            snares=[ksd.PercussiveHit(0.75, 0.7)],
            bpm=140.04,
            duration=12.345,
        )
        d = pm.to_dict()
        self.assertEqual(d["kick_count"], 2)
        self.assertEqual(d["snare_count"], 1)
        self.assertEqual(d["bpm"], 140.0)
        self.assertEqual(d["duration"], 12.35)

    def test_map_save_roundtrip(self):
        pm = ksd.PercussionMap(kicks=[ksd.PercussiveHit(0.5, 0.9)], snares=[], bpm=128.0, duration=4.0)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "perc.json"
            pm.save(p)
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["kick_count"], 1)


class TestBeatGrid(unittest.TestCase):
    def test_merges_and_sorts(self):
        pm = ksd.PercussionMap(
            kicks=[ksd.PercussiveHit(2.0, 0.9), ksd.PercussiveHit(0.0, 0.8)],
            snares=[ksd.PercussiveHit(1.0, 0.7)],
            bpm=140.0,
            duration=3.0,
        )
        grid = ksd.get_beat_grid(pm)
        times = [b["time"] for b in grid]
        self.assertEqual(times, [0.0, 1.0, 2.0])
        types = [b["type"] for b in grid]
        self.assertEqual(types, ["kick", "snare", "kick"])

    def test_empty_grid(self):
        pm = ksd.PercussionMap(kicks=[], snares=[], bpm=0.0, duration=0.0)
        self.assertEqual(ksd.get_beat_grid(pm), [])


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_lut_generator.py\n
\\python
"""Offline tests for lut_generator.py – color math and .cube file structure."""
import unittest
import tempfile
from pathlib import Path

import lut_generator as lg


class TestColorMath(unittest.TestCase):
    def test_clamp_bounds(self):
        self.assertEqual(lg._clamp(-0.5), 0.0)
        self.assertEqual(lg._clamp(1.5), 1.0)
        self.assertEqual(lg._clamp(0.42), 0.42)

    def test_srgb_linear_roundtrip(self):
        for c in (0.0, 0.04, 0.2, 0.5, 0.8, 1.0):
            back = lg._linear_to_srgb(lg._srgb_to_linear(c))
            self.assertAlmostEqual(back, c, places=5)

    def test_transforms_return_valid_rgb(self):
        transforms = (
            lg._transform_underground_dark,
            lg._transform_vhs_analog,
            lg._transform_neon_nights,
        )
        for fn in transforms:
            for rgb in [(0.0, 0.0, 0.0), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (0.2, 0.6, 0.9)]:
                out = fn(*rgb)
                self.assertEqual(len(out), 3)
                for v in out:
                    self.assertGreaterEqual(v, 0.0)
                    self.assertLessEqual(v, 1.0)


class TestCubeFile(unittest.TestCase):
    def test_generate_cube_file_structure(self):
        # Use a tiny size for speed; structure must still be valid.
        size = 3
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "test.cube"
            lg._generate_cube_file(lg._transform_vhs_analog, out, "test", size=size)
            self.assertTrue(out.exists())

            lines = out.read_text().splitlines()
            self.assertIn(f"LUT_3D_SIZE {size}", lines)
            self.assertIn('TITLE "test"', lines)

            data_lines = [
                ln for ln in lines
                if ln and ln[0].isdigit() and len(ln.split()) == 3
            ]
            self.assertEqual(len(data_lines), size ** 3)

            # Every data triple must be parseable floats in [0,1].
            r, g, b = (float(x) for x in data_lines[0].split())
            for v in (r, g, b):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_get_lut_path_resolves_and_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "underground_dark.cube").write_text("TITLE \"x\"\n")
            self.assertEqual(
                lg.get_lut_path("underground_dark", lut_dir=d),
                d / "underground_dark.cube",
            )
            with self.assertRaises(FileNotFoundError):
                lg.get_lut_path("does_not_exist", lut_dir=d)


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_pipeline_helpers.py\n
\\python
"""
Tests für die Pipeline-Helfer aus src/main.py und regie_engine.py:
- Twin-Detektor (Vision-Duplikat-Vorfilter)
- Reel-Peak-Berechnung (Musik-Overlay)
- Quelldauer-Clamping im Edit-Plan-Verifier
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import (  # noqa: E402
    _clip_reel_duration,
    _find_visual_twin,
    _reel_peak_time,
)
from regie_engine import EditClip, EditPlan, verify_edit_plan  # noqa: E402


# ---------------------------------------------------------------------------
# Twin-Detektor (_find_visual_twin)
# ---------------------------------------------------------------------------

# Hashes mit definierter Bit-Distanz: BASE hat 12 gesetzte Bits (informativ).
BASE = 0b111111111111
def _flip(h: int, n: int) -> int:
    """Kippt die n höchsten Bits eines 64-bit-Werts (verändert Distanz, nicht popcount-kritisch)."""
    for i in range(n):
        h ^= 1 << (63 - i)
    return h


class TestFindVisualTwin:
    def test_identical_signature_is_twin(self):
        sig = [BASE, BASE, BASE, BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": list(sig)}) == "a.mp4"

    def test_small_distance_is_twin(self):
        # Re-Encodes weichen real um <=7 Bits ab; Threshold ist 10
        sig = [BASE, BASE, BASE, BASE, BASE]
        other = [_flip(BASE, 7), BASE, _flip(BASE, 3), BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": other}) == "a.mp4"

    def test_large_distance_is_no_twin(self):
        # Verschiedene Szenen liegen real bei >=16 Bits
        sig = [BASE] * 5
        other = [_flip(BASE, 16)] * 5
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_one_bad_position_rejects(self):
        # ALLE vergleichbaren Positionen müssen passen (konservativ)
        sig = [BASE] * 5
        other = [BASE, BASE, BASE, BASE, _flip(BASE, 16)]
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_uniform_frames_not_comparable(self):
        # Hash 0 / popcount<4 = schwarzes Bild → zählt nicht; <2 vergleichbar → kein Twin
        sig = [0, 0b1, BASE, 0, 0b11]
        other = [0, 0b1, BASE, 0, 0b11]
        assert _find_visual_twin(sig, {"a.mp4": other}) is None

    def test_none_positions_skipped(self):
        sig = [None, BASE, BASE, None, None]
        other = [BASE, BASE, BASE, BASE, BASE]
        assert _find_visual_twin(sig, {"a.mp4": other}) == "a.mp4"


# ---------------------------------------------------------------------------
# Reel-Peak (_reel_peak_time / _clip_reel_duration)
# ---------------------------------------------------------------------------

class TestReelPeak:
    def test_slow_mo_stretches_reel_duration(self):
        clip = {"start": 0.0, "end": 4.0, "slow_mo": True, "slow_mo_factor": 2.0}
        assert _clip_reel_duration(clip) == 8.0

    def test_peak_at_highest_energy_clip(self):
        clips = [
            {"video": "a.mp4", "start": 0, "end": 5},
            {"video": "b.mp4", "start": 0, "end": 4},
            {"video": "c.mp4", "start": 0, "end": 6},
        ]
        vision = {"b.mp4": {"vision_tags_filtered": [
            {"tag": "CROWD_ENERGY"}, {"tag": "LIGHT_SHOW"}]}}
        peak, total = _reel_peak_time(clips, vision)
        assert total == 15.0
        assert peak == 7.0  # Mitte von b: 5 + 4/2

    def test_fallback_to_drop_reason(self):
        clips = [
            {"video": "a.mp4", "start": 0, "end": 5},
            {"video": "b.mp4", "start": 0, "end": 5, "reason": "the DROP hits"},
        ]
        peak, _ = _reel_peak_time(clips, None)
        assert peak == 7.5  # Mitte von b

    def test_fallback_to_62_percent(self):
        clips = [{"video": "a.mp4", "start": 0, "end": 10}]
        peak, total = _reel_peak_time(clips, None)
        assert total == 10.0
        assert peak == pytest.approx(6.2)

    def test_empty_plan(self):
        assert _reel_peak_time([], None) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Quelldauer-Clamping (verify_edit_plan)
# ---------------------------------------------------------------------------

def _plan(clips: list[EditClip]) -> EditPlan:
    return EditPlan(
        clips=clips,
        narrative="test",
        total_duration=sum(c.duration for c in clips),
        provider_used="test",
        model_used="test",
    )


class TestVerifyEditPlanClamping:
    def test_end_clamped_to_source_duration(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 4.6)
        plan = _plan([EditClip("a.mov", 0.0, 5.0, "hard_cut", "x")])
        out = verify_edit_plan(plan, {}, target_duration=4.6)
        assert out.clips[0].end == 4.6

    def test_clip_starting_past_source_is_dropped(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 3.0)
        plan = _plan([
            EditClip("a.mov", 5.0, 8.0, "hard_cut", "x"),   # start hinter Quellende
            EditClip("a.mov", 0.0, 2.0, "hard_cut", "x"),
        ])
        out = verify_edit_plan(plan, {}, target_duration=2.0)
        assert len(out.clips) == 1
        assert out.clips[0].start == 0.0

    def test_shortfall_recovered_from_headroom(self, monkeypatch):
        import regie_engine
        # Quelle ist 20s lang – Clip endet bei 5s, hat also Headroom
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 20.0)
        plan = _plan([
            EditClip("a.mov", 0.0, 5.0, "hard_cut", "x"),
            EditClip("b.mov", 0.0, 5.0, "hard_cut", "x"),
        ])
        out = verify_edit_plan(plan, {}, target_duration=13.0)
        # +2s max pro Clip → 10 + 2 + 1 = 13 erreichbar
        assert out.total_duration == pytest.approx(13.0, abs=0.1)
        # Startzeiten (beat-aligned) bleiben unangetastet
        assert all(c.start == 0.0 for c in out.clips)

    def test_unknown_duration_skips_clamping(self, monkeypatch):
        import regie_engine
        monkeypatch.setattr(regie_engine, "_source_duration", lambda v: 0.0)
        plan = _plan([EditClip("a.mov", 0.0, 5.0, "hard_cut", "x")])
        out = verify_edit_plan(plan, {}, target_duration=5.0)
        assert out.clips[0].end == 5.0

\\n
### \tests/test_regie_engine.py\n
\\python
"""Offline tests for regie_engine.py – parsing, verification, plan model, providers.

No network: only the JSON parser, verifier, dataclasses and provider availability
logic are exercised. The anthropic/google/openai SDKs are never imported because
their .call() methods are not invoked.
"""
import unittest
import json
import tempfile
from pathlib import Path
from unittest import mock

import regie_engine as re_eng


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
class TestEditClip(unittest.TestCase):
    def test_to_dict_computes_duration_and_rounds(self):
        clip = re_eng.EditClip(
            video="a.mov", start=12.34567, end=18.78912,
            transition="hard_cut_on_beat", reason="drop",
        )
        d = clip.to_dict()
        self.assertEqual(d["start"], 12.346)
        self.assertEqual(d["end"], 18.789)
        self.assertEqual(d["duration"], 6.443)
        self.assertEqual(d["crop"], "9:16")


class TestEditPlan(unittest.TestCase):
    def _plan(self):
        return re_eng.EditPlan(
            clips=[
                re_eng.EditClip("a.mov", 0.0, 4.0, "cut", "r1"),
                re_eng.EditClip("b.mov", 4.0, 9.0, "cut", "r2", slow_mo=True, slow_mo_factor=2.0),
            ],
            narrative="arc",
            total_duration=9.0,
        )

    def test_to_dict_clip_count(self):
        d = self._plan().to_dict()
        self.assertEqual(d["clip_count"], 2)
        self.assertEqual(len(d["clips"]), 2)

    def test_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plan.json"
            self._plan().save(p)
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded["clip_count"], 2)

    def test_to_ffmpeg_commands(self):
        cmds = self._plan().to_ffmpeg_commands(output_dir=Path("output"))
        self.assertEqual(len(cmds), 2)
        # 9:16 crop + lut applied
        self.assertIn("crop=ih*9/16:ih,scale=1080:1920", cmds[0])
        self.assertIn("lut3d=luts/underground_dark.cube", cmds[0])
        # slow-mo clip gets setpts prepended
        self.assertIn("setpts=PTS*2.0", cmds[1])


# --------------------------------------------------------------------------- #
# JSON parsing (the core robustness feature)
# --------------------------------------------------------------------------- #
class TestParseEditPlan(unittest.TestCase):
    VALID = {
        "clips": [
            {"video": "a.mov", "start": 1.0, "end": 5.0,
             "transition": "cut", "reason": "intro"},
        ],
        "narrative": "story",
    }

    def test_plain_json(self):
        plan = re_eng._parse_edit_plan(json.dumps(self.VALID), "claude", "m")
        self.assertEqual(len(plan.clips), 1)
        self.assertEqual(plan.clips[0].video, "a.mov")
        self.assertEqual(plan.narrative, "story")
        self.assertEqual(plan.provider_used, "claude")

    def test_markdown_fenced(self):
        raw = "```json\n" + json.dumps(self.VALID) + "\n```"
        plan = re_eng._parse_edit_plan(raw, "gemini", "m")
        self.assertEqual(len(plan.clips), 1)

    def test_text_wrapped_json(self):
        raw = "Here is your plan:\n" + json.dumps(self.VALID) + "\nHope it helps!"
        plan = re_eng._parse_edit_plan(raw, "deepseek", "m")
        self.assertEqual(len(plan.clips), 1)

    def test_defaults_applied(self):
        minimal = {"clips": [{"video": "x.mov", "start": 0, "end": 3}], "narrative": ""}
        plan = re_eng._parse_edit_plan(json.dumps(minimal), "claude", "m")
        c = plan.clips[0]
        self.assertEqual(c.transition, "cut")
        self.assertEqual(c.crop, "9:16")
        self.assertEqual(c.lut, "underground_dark")

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            re_eng._parse_edit_plan("not json at all", "claude", "m")


# --------------------------------------------------------------------------- #
# Verification / self-healing
# --------------------------------------------------------------------------- #
class TestVerifyEditPlan(unittest.TestCase):
    def test_drops_zero_and_negative_duration(self):
        plan = re_eng.EditPlan(
            clips=[
                re_eng.EditClip("a.mov", 5.0, 5.0, "cut", "zero"),
                re_eng.EditClip("b.mov", 5.0, 3.0, "cut", "negative"),
                re_eng.EditClip("c.mov", 0.0, 4.0, "cut", "ok"),
            ],
            narrative="", total_duration=0.0,
        )
        fixed = re_eng.verify_edit_plan(plan, {}, target_duration=4.0)
        self.assertEqual(len(fixed.clips), 1)
        self.assertEqual(fixed.clips[0].video, "c.mov")
        self.assertAlmostEqual(fixed.total_duration, 4.0)

    def test_trims_overlong_clip(self):
        plan = re_eng.EditPlan(
            clips=[re_eng.EditClip("a.mov", 0.0, 30.0, "cut", "too long")],
            narrative="", total_duration=30.0,
        )
        fixed = re_eng.verify_edit_plan(plan, {}, target_duration=15.0)
        self.assertEqual(fixed.clips[0].duration, 15.0)

    def test_empty_plan_is_safe(self):
        plan = re_eng.EditPlan(clips=[], narrative="", total_duration=0.0)
        self.assertEqual(re_eng.verify_edit_plan(plan, {}).clips, [])


# --------------------------------------------------------------------------- #
# Seamless loop helper
# --------------------------------------------------------------------------- #
class TestSeamlessLoop(unittest.TestCase):
    def test_swaps_halves(self):
        plan = re_eng.create_seamless_loop_plan("v.mov", start=10.0, end=20.0)
        self.assertEqual(len(plan.clips), 2)
        # Second half plays first
        self.assertEqual((plan.clips[0].start, plan.clips[0].end), (15.0, 20.0))
        self.assertEqual((plan.clips[1].start, plan.clips[1].end), (10.0, 15.0))
        self.assertEqual(plan.style, "seamless_loop")


# --------------------------------------------------------------------------- #
# Provider resolution (no API keys involved)
# --------------------------------------------------------------------------- #
class TestProviders(unittest.TestCase):
    def test_get_provider_unknown_raises(self):
        with self.assertRaises(ValueError):
            re_eng.get_provider("does_not_exist")

    def test_get_provider_returns_right_class(self):
        self.assertIsInstance(re_eng.get_provider("claude"), re_eng.ClaudeProvider)
        self.assertIsInstance(re_eng.get_provider("gemini"), re_eng.GeminiProvider)
        self.assertIsInstance(re_eng.get_provider("deepseek"), re_eng.DeepSeekProvider)

    def test_availability_requires_key(self):
        self.assertFalse(re_eng.ClaudeProvider(api_key="").is_available())

    def test_availability_requires_sdk(self):
        # Key present but SDK not importable -> not available (graceful degradation).
        with mock.patch.object(re_eng, "_sdk_installed", return_value=False):
            self.assertFalse(re_eng.DeepSeekProvider(api_key="secret").is_available())
        with mock.patch.object(re_eng, "_sdk_installed", return_value=True):
            self.assertTrue(re_eng.DeepSeekProvider(api_key="secret").is_available())

    def test_resolve_named_provider_without_key_raises(self):
        with mock.patch.object(re_eng.ClaudeProvider, "is_available", return_value=False):
            with self.assertRaises(ValueError):
                re_eng.resolve_provider("claude")

    def test_resolve_auto_without_any_key_raises(self):
        with mock.patch.object(re_eng.ClaudeProvider, "is_available", return_value=False), \
             mock.patch.object(re_eng.GeminiProvider, "is_available", return_value=False), \
             mock.patch.object(re_eng.DeepSeekProvider, "is_available", return_value=False):
            with self.assertRaises(ValueError):
                re_eng.resolve_provider("auto")

    def test_list_available_providers_structure(self):
        providers = re_eng.list_available_providers()
        self.assertEqual({p["name"] for p in providers}, {"claude", "gemini", "deepseek", "local"})
        for p in providers:
            self.assertIn("model", p)
            self.assertIn("available", p)


# --------------------------------------------------------------------------- #
# POV story preset + anti-advice hook
# --------------------------------------------------------------------------- #
class TestPovStoryPreset(unittest.TestCase):
    def test_prompt_includes_pov_section_only_for_pov_story(self):
        pov = re_eng._build_system_prompt("pov_story", 45)
        self.assertIn("ANTI-ADVICE HOOK", pov)
        self.assertIn("hook_text", pov)
        for phase in ("before", "during", "after"):
            self.assertIn(phase, pov)
        # other presets must NOT get the POV story block
        hl = re_eng._build_system_prompt("highlight", 60)
        self.assertNotIn("ANTI-ADVICE HOOK", hl)

    def test_pov_story_is_a_valid_cli_preset(self):
        # the preset name appears in the preset definitions of every prompt
        self.assertIn("pov_story", re_eng._build_system_prompt("highlight", 60))

    def test_parse_reads_hook_text_and_phase(self):
        raw = {
            "clips": [
                {"video": "arrive.mov", "start": 0, "end": 4, "phase": "before"},
                {"video": "drop.mov", "start": 10, "end": 14, "phase": "during"},
                {"video": "pack.mov", "start": 20, "end": 24, "phase": "after"},
            ],
            "narrative": "a day in the life",
            "hook_text": "stop practicing your transitions.",
        }
        plan = re_eng._parse_edit_plan(json.dumps(raw), "claude", "m")
        self.assertEqual(plan.hook_text, "stop practicing your transitions.")
        self.assertEqual([c.phase for c in plan.clips], ["before", "during", "after"])
        # hook_text + phase survive serialization
        d = plan.to_dict()
        self.assertEqual(d["hook_text"], "stop practicing your transitions.")
        self.assertEqual(d["clips"][0]["phase"], "before")

    def test_hook_text_defaults_empty_for_non_pov(self):
        minimal = {"clips": [{"video": "x.mov", "start": 0, "end": 3}], "narrative": ""}
        plan = re_eng._parse_edit_plan(json.dumps(minimal), "claude", "m")
        self.assertEqual(plan.hook_text, "")
        self.assertEqual(plan.clips[0].phase, "")


if __name__ == "__main__":
    unittest.main()

\\n
### \tests/test_vision_engine.py\n
\\python
"""Offline tests for vision_engine.py – taxonomy, scoring, graceful degradation.

No Ollama and no real video decoding: the model call is faked by injecting a
stub `ollama` module, and availability is monkeypatched.
"""
import sys
import json
import unittest
from unittest import mock

import analyzer.vision_engine as ve


class TestTaxonomy(unittest.TestCase):
    def test_new_story_tags_present(self):
        self.assertIn("ARRIVAL", ve.VALID_TAGS)
        self.assertIn("PACKDOWN", ve.VALID_TAGS)

    def test_every_valid_tag_has_a_score(self):
        for tag in ve.VALID_TAGS:
            self.assertIn(tag, ve.TAG_BONUS_SCORES, f"missing score for {tag}")

    def test_story_tags_have_zero_bonus(self):
        self.assertEqual(ve.TAG_BONUS_SCORES["ARRIVAL"], 0.0)
        self.assertEqual(ve.TAG_BONUS_SCORES["PACKDOWN"], 0.0)

    def test_system_prompt_documents_new_tags(self):
        self.assertIn("ARRIVAL", ve.SYSTEM_PROMPT)
        self.assertIn("PACKDOWN", ve.SYSTEM_PROMPT)


class TestFilteringAndScoring(unittest.TestCase):
    def _tags(self):
        return [
            ve.FrameTag(0.0, "ARRIVAL", 0.9, "load-in"),
            ve.FrameTag(5.0, "CROWD_ENERGY", 0.8, "drop"),
            ve.FrameTag(9.0, "PACKDOWN", 0.7, "empty floor"),
            ve.FrameTag(12.0, "UNUSABLE", 0.9, "blurry"),
            ve.FrameTag(15.0, "DJ_SETUP", 0.1, "low conf"),
        ]

    def test_filter_keeps_story_tags_drops_unusable_and_lowconf(self):
        kept = {t.tag for t in ve.filter_unusable(self._tags(), min_confidence=0.3)}
        self.assertEqual(kept, {"ARRIVAL", "CROWD_ENERGY", "PACKDOWN"})

    def test_get_tag_scores(self):
        scores = ve.get_tag_scores(self._tags())
        # story tags contribute nothing; crowd energy contributes 0.8 * 0.8
        self.assertAlmostEqual(scores["0.0"], 0.0)
        self.assertAlmostEqual(scores["9.0"], 0.0)
        self.assertAlmostEqual(scores["5.0"], 0.64)


class TestGracefulDegradation(unittest.TestCase):
    def test_returns_empty_when_backend_down(self):
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.is_available.return_value = False
            self.assertEqual(ve.tag_video_frames("whatever.mov"), [])


class TestBatchTagValidation(unittest.TestCase):
    def test_new_tag_kept_unknown_coerced(self):
        response = [
            {"time": 0.0, "tag": "ARRIVAL", "confidence": 0.9, "description": "load-in"},
            {"time": 5.0, "tag": "ROBOT_DANCE", "confidence": 0.9, "description": "bogus tag"},
        ]
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.describe_frames.return_value = json.dumps(response)
            tags = ve._analyze_frames_batch([(0.0, b"x"), (5.0, b"y")])

        self.assertEqual(tags[0].tag, "ARRIVAL")        # new valid tag preserved
        self.assertEqual(tags[1].tag, "UNUSABLE")        # unknown tag coerced

    def test_concatenated_arrays_are_merged(self):
        # gemma4:e2b often returns one JSON array per image, concatenated.
        raw = (
            '[{"time": 0.0, "tag": "DJ_SETUP", "confidence": 0.95, "description": "a"}]\n'
            '[{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "b"}]'
        )
        with mock.patch.object(ve, "_get_vision_backend") as mock_get:
            mock_get.return_value.describe_frames.return_value = raw
            tags = ve._analyze_frames_batch([(0.0, b"x"), (5.0, b"y")])
        self.assertEqual([t.tag for t in tags], ["DJ_SETUP", "CROWD_ENERGY"])
        self.assertEqual([t.time for t in tags], [0.0, 5.0])


if __name__ == "__main__":
    unittest.main()

\\n