# UNREEL – Anpassung auf Windows VORBEREITEN (Mac-Umzug)

Ziel: Auf Windows fast alles fertigstellen, sodass am MacBook nur noch
`git pull` + MLX-Installation + ein Test übrig bleibt.

## Was geht auf Windows — und was NICHT

| Bereich | Windows | Begründung |
|---|---|---|
| Phasen A–E mit dem Agent umsetzen | ✅ | reiner Python-Code, plattformneutral |
| Import-Gates (A, B, C, E) | ✅ | nur `import`-Checks |
| `pytest -q` (Ingestion-Tests) | ✅ | kein MLX nötig |
| `pip install -r requirements.txt` | ✅ | MLX-Zeilen haben Plattform-Marker → werden auf Windows übersprungen |
| Ollama-Backend echt testen | ✅ | Ollama gibt es für Windows |
| **MLX-Pfade testen (Gate D2)** | ❌ | mlx/mlx-vlm/mlx-lm/outlines[mlxlm] laufen NUR auf Apple Silicon |
| **`LOCAL_REGIE_ENGINE=mlx`** | ❌ | s.o. – braucht Metal-GPU |
| Modell-Benchmarks / RAM-Druck | ❌ | nur auf der echten 16-GB-Hardware sinnvoll |

> Kurz: Die **Logik** verifizierst du auf Windows über das **Ollama-Backend** als
> Stellvertreter. Die **MLX-Pfade** bleiben fürs MacBook.

---

## 0. Windows-Voraussetzungen
```powershell
# Python 3.11
winget install Python.Python.3.11
# ffmpeg + ffprobe (PFLICHT – Ingestion liest Timestamps via ffprobe)
winget install Gyan.FFmpeg
# Git
winget install Git.Git
```
Neues Terminal öffnen, dann prüfen:
```powershell
python --version
ffmpeg -version
ffprobe -version
```

## 1. Projekt + venv
```powershell
cd C:\dev               # oder wohin du willst
git clone <DEIN_REPO_URL> unreel
cd unreel
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2. Phasen A–E umsetzen (mit dem Agent)
Den Agenten (Claude Code ODER Antigravity/Gemini) `CLAUDE_MASTER.md` bzw.
`GEMINI.md` abarbeiten lassen. Auf Windows alle Gates AUSSER D2 anstreben.

## 3. Dependencies installieren (Windows-Variante)
```powershell
pip install -r requirements.txt
```
→ installiert KEINE MLX-Pakete (Marker). Das ist korrekt und erwartet.

## 4. Ollama als Stellvertreter zum Testen der Logik
```powershell
winget install Ollama.Ollama
ollama serve            # in eigenem Terminal lassen
ollama pull gemma3:4b          # Vision-Stellvertreter (multimodal)
ollama pull llama3.2           # Copywriter-Stellvertreter
ollama pull qwen3.5:9b         # lokaler Regisseur-Stellvertreter
```
`.env` für den Windows-Testlauf:
```ini
VISION_BACKEND=ollama
TEXT_BACKEND=ollama
LOCAL_REGIE_ENGINE=ollama
LOCAL_REGIE_MODEL=qwen3.5:9b
# GEMMA_MODEL / COPYWRITER_MODEL ggf. auf die gepullten Modelle setzen
```

## 5. Windows-Gates (das sollte hier grün sein)
```powershell
# Struktur / Imports
python -c "import analyzer.vision_backends, analyzer.text_backends, analyzer.local_regie_provider; print('backends ok')"
python -c "import analyzer.vision_engine, analyzer.copywriter, config; print('engines ok')"
python -c "import analyzer.regie_engine as r; print([p['name'] for p in r.list_available_providers()])"  # enthält 'local'

# Tests
pytest -q

# Echter Logik-Test über Ollama (kein MLX!)
python -m analyzer.ingest .\input --json
python -m analyzer.vision_engine .\input\<clip>.mp4         # via ollama
python -m analyzer.copywriter demo                          # via ollama
python -m analyzer.regie_engine .\output\pipeline_results.json --provider local
```
Wenn diese grün sind, ist die gesamte LOGIK verifiziert.

## 6. Commit + Push
```powershell
git add -A
git commit -m "feat: MLX-ready backends (verified via ollama on windows)"
git push
```

---

## 7. Auf dem MacBook bleibt dann nur noch
```bash
git pull
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # zieht JETZT mlx/mlx-vlm/mlx-lm/outlines
# .env auf mlx umstellen:
#   VISION_BACKEND=mlx / TEXT_BACKEND=mlx / (optional) LOCAL_REGIE_ENGINE=mlx
python -m analyzer.vision_engine input/<clip>.mp4   # Gate D2 (echtes MLX)
# danach: Benchmarks (siehe MLX_SETUP.md / REGIE_BENCHMARK.md)
```

## Stolperfallen (Windows)
- **ffprobe nicht im PATH** → Ingestion fällt still auf mtime zurück. Erst Schritt 0 fixen.
- **Pfad-Trennzeichen**: in `.env`/CLI Windows-Pfade (`.\input`) nutzen; der Code
  selbst arbeitet mit `pathlib` und ist plattformneutral.
- **Zeilenenden (CRLF)**: `.gitattributes` mit `* text=auto` empfohlen, damit der
  Mac später keine LF/CRLF-Diffs sieht.
- **NICHT versuchen**, `mlx*` auf Windows zu installieren – schlägt fehl, ist aber
  dank Marker auch nicht nötig.
