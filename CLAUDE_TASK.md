# TASK: Web-App ausgliedern, Ingestion als Pipeline-Phase 0 integrieren

> Diese Datei ist die Arbeitsanweisung für Claude Code. Arbeite die Schritte
> **in Reihenfolge** ab. Nach jedem Schritt gilt ein **Gate** (Verifikation),
> das grün sein muss, bevor du weitermachst. Wenn ein Gate rot ist: **stopp,
> melde dich, rate nicht.**

## Kontext (kurz)
UNREEL ist ein CPU-only CLI-Tool, das rohes DJ-Material zu 9:16-Reels schneidet.
Die saubere Logik lebt in `analyzer/` + `src/main.py`. Es gibt zusätzlich eine
Flask-Web-App (`app.py`, `static/`, `integration_flask_endpoints.py`), aus der das
Projekt herausgewachsen ist. **Die Web-App wird entfernt.** Vorher wird **eine**
Funktion gerettet: **Ingestion & Renaming** (Dedup + `UNREEL_<timestamp>`-Rename),
die ich bereits als fertiges, getestetes Modul mitliefere.

## Constraints (NICHT verletzen)
- CPU-only. Keine GPU/CUDA-Annahmen.
- Keine neuen Dependencies. Im Gegenteil: `flask`, `flask-cors` werden entfernt.
- `pathlib`, relative Pfade über `config.BASE_DIR`. Keine absoluten Pfade.
- `logging` statt `print()` in Library-Code. CLI-Blöcke dürfen printen.
- Bestehende `analyzer/`-Module und `src/main.py`-Logik NICHT umschreiben,
  außer den explizit genannten Stellen.
- Arbeite auf einem Branch. Lösche nichts hart, bevor das Gate in Schritt 5 grün ist.

---

## Schritt 0 — Branch + Bestandsaufnahme
```bash
git checkout -b refactor/cli-only
```
- Lies `src/main.py` vollständig und finde: (a) den argparse-Parser,
  (b) die `main()`-Funktion, (c) die Stelle, an der die Eingabe-Clips erstmals
  ermittelt werden (vermutlich ein `glob`/`listdir` auf dem Input-Ordner).
- **Berichte mir** in 3-5 Zeilen: Wie heißt die Variable mit der Clip-Liste,
  und an welcher Zeile entsteht sie? **Warte auf mein OK, bevor du editierst.**

---

## Schritt 1 — Ingestion-Modul einsetzen
- Lege die mitgelieferte Datei `ingest.py` als **`analyzer/ingest.py`** ab
  (Inhalt unverändert übernehmen).
- Lege die mitgelieferte `test_ingest.py` als **`tests/test_ingest.py`** ab.
- **Gate 1:**
  ```bash
  python -m analyzer.ingest --help            # CLI lädt ohne Fehler
  pytest tests/test_ingest.py -q              # alle Tests grün
  ```

---

## Schritt 2 — config.py prüfen & ergänzen
`analyzer/ingest.py` braucht `config.VIDEO_SOURCE_DIR` und
`config.SUPPORTED_EXTENSIONS`. Prüfe, ob beide existieren.

Führe diesen Smoke-Test gegen die **echte** config aus (er listet ALLE im Code
referenzierten, aber in config fehlenden Keys – nicht nur die für ingest):
```bash
python - <<'PY'
import re, glob, config
src = ""
for f in glob.glob("analyzer/*.py") + ["src/main.py"]:
    src += open(f, encoding="utf-8").read()
refs = set(re.findall(r"config\.([A-Z_][A-Z0-9_]+)", src))
missing = sorted(r for r in refs if not hasattr(config, r))
print("FEHLT in config.py:", missing or "nichts")
PY
```
- Fehlt **nur** `VIDEO_SOURCE_DIR` und/oder `SUPPORTED_EXTENSIONS`: ergänze sie
  sinnvoll (`VIDEO_SOURCE_DIR = INPUT_DIR`, `SUPPORTED_EXTENSIONS = [".mp4",".mov",".MOV"]`
  o.ä. – orientiere dich an bereits vorhandenen Konventionen im File).
- Fehlt **mehr** (z.B. `REEL_CODEC`, `FADE_DURATION_SEC`, `SINGLE_DOWNLOADS_DIR`):
  Das ist ein bekanntes Problem (zwei Config-Welten). **Stopp und melde dich**
  mit der vollständigen Liste, bevor du rätst.
- **Gate 2:** `python -c "import config"` läuft fehlerfrei, Smoke-Test gibt
  `nichts` (oder nur erwartete, von mir freigegebene Keys).

---

## Schritt 3 — Phase 0 in `src/main.py` verdrahten
Ziel: Vor allen anderen Phasen läuft Ingestion einmal über den Input-Ordner,
und die **zurückgegebene `final_files`-Liste** ist die Quelle für die Folge-Phasen.
Der bisherige `glob`/`listdir` auf den Input-Ordner wird dadurch ersetzt.

- Import ergänzen (zu den anderen Top-Level-Imports von `src/main.py`):
  ```python
  from ingest import ingest_directory
  ```
- Phase-Funktion ergänzen (nahe den anderen `phase_*`):
  ```python
  def phase_ingest(input_dir):
      """Phase 0: Duplikate entfernen + nach UNREEL_<timestamp> umbenennen."""
      logger.info("Phase 0: Ingestion & Renaming")
      result = ingest_directory(input_dir)
      return [Path(p) for p in result.final_files]
  ```
- In `main()` die Clip-Ermittlung (aus Schritt 0) ersetzen durch:
  ```python
  clips = phase_ingest(args.input)
  if not clips:
      logger.warning("Keine verarbeitbaren Clips in %s", args.input)
      return
  ```
  **Wichtig:** Passe nur diese eine Stelle an. Wenn die Folge-Phasen Strings
  statt `Path` erwarten, gib stattdessen `result.final_files` (Strings) zurück –
  prüfe den vorhandenen Typ und bleib dabei.
- Optional, falls leicht machbar: ein `--skip-ingest`-Flag, das Phase 0 überspringt.
- **Gate 3 (Dry-Run, ohne echte Schwerlast):**
  ```bash
  python -m src.main --help                      # parser intakt
  # Mit 1-2 Testdateien in ./input prüfen, dass Phase 0 läuft und umbenennt:
  python -m analyzer.ingest ./input --json
  ```

---

## Schritt 4 — Web-App entkoppeln (verschieben, noch nicht löschen)
- Verschiebe (nicht löschen) in einen Ordner `_attic/`:
  `app.py`, `static/`, `integration_flask_endpoints.py`.
- Entferne aus `requirements.txt` alle Pakete, die NUR die Web-App brauchte:
  mindestens `flask`, `flask-cors` (prüfe per grep, ob sie sonst noch
  irgendwo importiert werden – wenn ja: melden, nicht entfernen).
  ```bash
  grep -rn "import flask\|from flask\|flask_cors" --include=*.py . | grep -v _attic
  ```
  Erwartung: keine Treffer außerhalb `_attic/`.
- **Gate 4:**
  ```bash
  grep -rn "flask" --include=*.py . | grep -v _attic   # leer
  pip install -r requirements.txt                       # in frischer venv
  pytest -q                                              # GESAMTE Suite grün
  python -m src.main --help                              # CLI startet
  ```

---

## Schritt 5 — Endgültig entfernen
- Nur wenn Gate 4 grün war: `rm -rf _attic/`.
- Doku angleichen: in `CLAUDE.md` / `README.md` / `COMMANDS.md` die Web-App /
  Flask / `app.py` / Dashboard-Erwähnungen entfernen und Phase 0 (Ingestion)
  + den Befehl `python -m analyzer.ingest` dokumentieren.
- **Gate 5:**
  ```bash
  grep -rni "flask\|app.py\|dashboard\|localhost:5000" --include=*.md .   # nur noch bewusste/leere Treffer
  pytest -q
  ```

---

## Commit-Strategie
Ein Commit pro Schritt, message-Präfix `refactor:` bzw. `feat:` / `test:`:
1. `feat: ingestion module (analyzer/ingest.py) + tests`
2. `fix: ensure config keys for ingestion`
3. `feat: wire ingestion as pipeline phase 0`
4. `refactor: move web app to _attic, drop flask deps`
5. `refactor: remove web app, update docs`

## Definition of Done
- [x] `pytest -q` komplett grün (inkl. neuer ingest-Tests)
- [x] `python -m src.main --help` und ein echter Lauf funktionieren
- [x] Kein `flask`/`flask_cors`-Import mehr im Code
- [x] Keine Web-/Dashboard-Erwähnung mehr in der Doku
- [x] Phase 0 benennt um + entfernt Duplikate, Folge-Phasen nutzen `final_files`
