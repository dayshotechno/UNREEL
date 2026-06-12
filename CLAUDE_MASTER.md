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
