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
