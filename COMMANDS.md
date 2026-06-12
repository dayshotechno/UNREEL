# UNREEL V3 – Anleitung & Befehls-Referenz

Diese Anleitung erklärt, **was UNREEL macht**, **wie du in einem Befehl ein fertiges Reel
erzeugst**, und **was in jeder Phase passiert**. Am Ende findest du einen Troubleshooting-Teil
mit den häufigsten Problemen.

> **Wo ausführen?** Immer aus dem Projekt-Root:
> `C:\Users\DAY SHO\Desktop\UNREEL`
>
> **Start-Befehl:** `python main.py …` (kurz) **oder** gleichwertig `python -m src.main …`.
> Beide rufen denselben Orchestrator in `src/main.py` auf.

---

## 1. Was macht UNREEL?

UNREEL verwandelt rohes DJ-Gig-Material (querformatige Clips) automatisch in ein fertiges,
hochkant geschnittenes Instagram-Reel (1080×1920). Die Pipeline durchläuft 6 Stufen:

```
 0 Setup    →  1 Sync   →  2 Vision  →  3 Regie  →  4 Copy   →  5 Export
 (LUTs)        (Audio)      (Tags)       (KI-Plan)   (Captions)  (Schnitt + Reel)
```

| Phase | Name | Was passiert | Braucht | Ergebnis |
|------|------|--------------|---------|----------|
| 0 | **Setup** | Erzeugt die Farb-LUTs (`.cube`), falls sie fehlen | – | `luts/*.cube` |
| 1 | **Sync** | Synchronisiert mehrere Clips per Audio-Kreuzkorrelation; erkennt Kicks/Snares/BPM | ≥2 Clips | `audio_sync.json`, `percussion_map.json` |
| 2 | **Vision** | Taggt Szenen je Clip mit dem lokalen Modell Gemma (z. B. `CROWD_ENERGY`, `ARRIVAL`) | **Ollama läuft** | Tags in `pipeline_results.json` |
| 3 | **Regie** | Schickt die Analyse an eine Cloud-KI → bekommt einen millisekundengenauen Schnittplan | **API-Key** | `edit_plan.json` |
| 4 | **Copy** | Generiert Dateinamen + Instagram-Captions mit lokalem Llama | Ollama läuft | `captions.json` |
| 5 | **Export** | Schneidet jeden Plan-Clip (Trim → 9:16-Crop → LUT) **und fügt alles zum finalen Reel zusammen** | FFmpeg | `snippet_*.mp4`, **`reel_<preset>.mp4`** |

**Wichtig:** Die Phasen geben ihre Ergebnisse innerhalb *eines* Laufs im Speicher weiter und
speichern nach jeder Phase nach `output/pipeline_results.json`. Wenn du nur einzelne Phasen
startest, werden vorhandene Ergebnisse von der Platte nachgeladen (siehe [Abschnitt 5](#5-phasenweise-arbeiten--resume)).

---

## 2. Einmaliges Setup

```powershell
# 1) Python-Abhängigkeiten
python -m pip install -r requirements.txt

# 2) Cloud-AI-SDKs (für die Regie-Phase) und Ollama-Client
python -m pip install anthropic openai google-generativeai ollama

# 3) .env aus der Vorlage anlegen
Copy-Item env.example .env
notepad .env
```

In der `.env` mindestens **einen** Provider-Key eintragen. `REGIE_PROVIDER=auto` nimmt automatisch
den ersten verfügbaren in der Reihenfolge **deepseek → claude → gemini**:

```ini
REGIE_PROVIDER=auto
ANTHROPIC_API_KEY=...          # Claude  (Modell: claude-fable-5)
GEMINI_API_KEY=...             # Gemini  (Modell: gemini-3.1-pro)
DEEPSEEK_API_KEY=...           # DeepSeek (Modell: deepseek-v4-pro)  ← Primär
GEMMA_MODEL=gemma4:e2b         # Vision-Tagging (lokal)
COPYWRITER_MODEL=llama3.2:3b   # Captions (lokal) – exakt der installierte Tag!
DEFAULT_LUT=underground_dark
```

> ⚠️ Trage bei `COPYWRITER_MODEL` **genau den installierten Ollama-Tag** ein
> (`llama3.2:3b`, nicht `llama3.2`), sonst nutzt die Copy-Phase nur den Fallback-Text.

```powershell
# 4) Ollama (lokale Modelle) installieren/starten und Modelle holen
ollama serve
ollama pull gemma4:e2b      # für Phase 2 (Vision)
ollama pull llama3.2:3b     # für Phase 4 (Copywriting)
```

**Prüfen, ob die Provider bereit sind** (kein API-Call, keine Kosten):

```powershell
@'
import regie_engine as r
for p in r.list_available_providers():
    print(f"{p['name']:9s} {p['model']:22s} verfuegbar={p['available']}")
'@ | python -
```

`verfuegbar=True` heißt: **Key in .env UND zugehöriges SDK installiert**.

---

## 3. Schnellstart – ein Befehl, ein Reel

Lege deine Clips in einen Ordner (z. B. `input_pov/`) und starte die komplette Pipeline:

```powershell
python main.py -i ./input_pov -p pov_story -d 45
```

Danach liegt in `output/`:
- **`reel_pov_story.mp4`** – das fertige, zusammengeschnittene Reel
- `snippet_001…00N.mp4` – die einzelnen Clips (Bausteine)
- `edit_plan.json` – der Schnittplan (bei `pov_story` inkl. `hook_text`)
- `captions.json` – Caption-Vorschläge

> Der **Hook-Text** wird **nicht** ins Video gebrannt (bewusst). Du legst ihn beim Posten in den
> ersten ~3 Sekunden als Text-Overlay drüber.

---

## 4. Alle Optionen der Pipeline

```powershell
python main.py [OPTIONEN]
```

| Flag | Werte | Bedeutung |
|------|-------|-----------|
| `-i`, `--input` | Pfad | Ordner mit den Quell-Clips (Default `./input`) |
| `-o`, `--output` | Pfad | Ausgabe-Ordner (Default `./output`) |
| `-p`, `--preset` | siehe unten | Schnitt-Stil (Default `highlight`) |
| `-d`, `--duration` | Sekunden | Ziel-Länge des Reels (Default `60`) |
| `-s`, `--style` | `techno`,`house`,`minimal` | Caption-Stil für Phase 4 (Default `techno`) |
| `--provider` | `deepseek`,`claude`,`gemini`,`auto` | Erzwingt einen Provider (Default: `auto` = aus .env) |
| `--multi` | – | Erzeugt Pläne von **allen** verfügbaren Providern zum Vergleich |
| `--phase` | siehe [Abschnitt 5] | Nur bestimmte Phasen ausführen |
| `--luts` | – | Nur die LUT-Dateien erzeugen und beenden |
| `-v`, `--verbose` | – | Ausführliche Debug-Ausgaben |

### Presets (`-p`)

| Preset | Beschreibung | Typische Länge |
|--------|--------------|----------------|
| `highlight` | Beste Momente, hohe Energie, schnelle Cuts | 60–90 s |
| `drop_focus` | Aufbau → Drop → Aftermath, um die Drops zentriert | 60 s |
| `seamless_loop` | Kurz, Ende fließt nahtlos in den Anfang (algorithmisch, **kein** API-Call) | 15–30 s |
| `moody` | Atmosphärisch, langsamere Cuts, `BREAKDOWN` + `LIGHT_SHOW`-lastig | 60 s |
| `pov_story` | **POV / „A Day in the Life"**: Story `before → during → after` + Anti-Advice-Hook | 30–60 s |

```powershell
# Beispiele
python main.py -i ./input -p highlight -d 60
python main.py -i ./input -p drop_focus -d 60 --provider claude
python main.py -i ./input -p pov_story  -d 45 -v
python main.py -i ./input -p highlight   --multi      # Plan von jedem Provider
```

---

## 5. Phasenweise arbeiten & Resume

Mit `--phase` führst du nur ausgewählte Stufen aus (mehrere möglich). Das ist nützlich, weil die
**Vision-Phase langsam** ist (siehe [Performance](#7-performance--erwartungen)) – du willst sie nicht
bei jedem Regie-Versuch neu rechnen.

```powershell
python main.py -i ./input --phase setup            # Nur LUTs (= --luts)
python main.py -i ./input --phase sync             # Nur Audio-Sync + Percussion
python main.py -i ./input --phase vision           # Nur Szenen-Tagging (Ollama)
python main.py -i ./input --phase analyze          # sync + vision in einem
python main.py -i ./input --phase regie            # Nur Schnittplan (braucht vorh. Vision)
python main.py -i ./input --phase copy             # Nur Captions
python main.py -i ./input --phase export           # Nur Schnitt + finales Reel
python main.py -i ./input --phase regie export     # Plan neu + Reel bauen
```

**So funktioniert Resume (zwei Mechanismen):**

1. **Phasen-Resume:** Startest du nur *einzelne* Phasen, lädt UNREEL die vorhandene
   `output/pipeline_results.json` und nutzt deren Daten. So kann z. B. `--phase regie export`
   die früher erzeugten Vision-Tags weiterverwenden, ohne neu zu taggen.
2. **Clip-Resume (Vision):** Die Vision-Phase speichert **nach jedem Clip**. Bricht der Lauf ab
   (z. B. Ruhezustand), startest du `--phase vision` einfach erneut – bereits getaggte Clips werden
   übersprungen (`Skipping … already tagged`).

> **Faustregel für pov_story:** erst Vision (einmal, dauert), dann beliebig oft Regie+Export:
> ```powershell
> python main.py -i ./input_pov --phase vision
> python main.py -i ./input_pov -p pov_story -d 45 --phase regie export
> ```

---

## 6. pov_story im Detail

Das `pov_story`-Preset baut eine kleine Erzählung über einen Gig-Tag:

- **before** – Ankunft, Vorbereitung, Soundcheck, Backstage (Tags `ARRIVAL`, `BACKSTAGE`, `DJ_SETUP`)
- **during** – das Set, Drops, Crowd (`CROWD_ENERGY`, `LIGHT_SHOW`, `DJ_SETUP`)
- **after** – Abbau, leerer Floor, Comedown (`PACKDOWN`, `BACKSTAGE`, `BREAKDOWN`)

Zusätzlich erzeugt die Regie eine **Anti-Advice-Hook**-Zeile (bewusst konträr/provokant) für die
ersten ~3 s, z. B. *„the crowd doesn't care about your 'journey'."* Sie steht im `edit_plan.json`
unter `hook_text` und in jedem Clip steht `phase` (before/during/after).

**Voraussetzung für gute Phasen:** Die Vision-Phase muss `ARRIVAL`/`PACKDOWN` erkannt haben.
Das Modell `gemma4:e2b` tut das nicht immer zuverlässig – wenn die before/after-Phase dünn wird,
hilft eine bewusste Clip-Auswahl (frühe Tagesclips für „before", späte/Aufräum-Clips für „after").

**Hinweis zu deinem Material:** Die Sync-Phase ist für *gleichzeitige* Multicam-Aufnahmen gedacht.
Wenn deine Clips über den Tag verteilt (sequenziell) sind, ist Sync sinnlos und langsam – lass sie
bei `pov_story` weg (also `--phase vision` + `--phase regie export` statt der vollen Pipeline,
oder die volle Pipeline akzeptiert die unnütze Sync einfach).

---

## 7. Performance & Erwartungen

- **Vision (Phase 2) ist der Flaschenhals:** Auf CPU braucht jeder Ollama-Batch ~60–110 s. Große/lange
  Clips werden komplett dekodiert. Bei vielen oder großen Clips → **viele Minuten bis Stunden.**
  → Für erste Tests eine **kleine Auswahl** (10–15 Clips) verwenden, riesige Dateien (>100 MB) meiden.
- **Regie (Phase 3):** 1 API-Call, ~10–60 s. DeepSeek `deepseek-v4-pro` ist ein **Reasoning-Modell** und
  braucht ein hohes Token-Budget (Default `max_tokens=8192`), sonst kommt leerer JSON-Output zurück.
- **Copy (Phase 4):** 2 Ollama-Calls **pro Clip** → bei vielen Clips schnell 15–25 Min. Wenn du nur das
  Reel willst, kannst du Phase 4 weglassen (`--phase … export` ohne `copy`).
- **Export (Phase 5):** FFmpeg pro Clip + finaler Concat. Slow-Mo-Quellen (120 fps) werden für das
  finale Reel auf `REEL_FPS=30` re-encodiert, damit das Timing stimmt.
- **Lange Läufe:** Verhindere den Ruhezustand des Rechners – sonst bricht die Vision-Phase ab (Resume
  rettet die bereits getaggten Clips, aber der Rest muss erneut laufen).

---

## 8. Module einzeln (Standalone-CLIs)

Praktisch zum Testen einzelner Bausteine:

```powershell
python lut_generator.py                       # LUTs -> luts/*.cube
python audio_sync.py input/*.mov              # Audio-Sync (mind. 2 Clips)
python kick_snare_detector.py input/clip.mov  # Kick/Snare/BPM eines Clips
python vision_engine.py input/clip.mov        # Szenen-Tags (braucht Ollama)
python copywriter.py demo                      # Copywriting-Demo (braucht Ollama)

# Regie direkt aus einer Analyse-JSON (kein erneutes Taggen):
python regie_engine.py output/pipeline_results.json -p pov_story --provider deepseek
python regie_engine.py output/pipeline_results.json -p highlight --multi
```

`regie_engine.py`-Flags: `-p/--preset`, `-d/--duration`, `--provider`, `--multi`, `-o/--output`, `-v`.

---

## 9. Tests

```powershell
python -m unittest discover -s tests -t .            # Alle Offline-Tests (kein API/Ollama/FFmpeg)
python -m unittest discover -s tests -t . -v         # Ausführlich
python -m unittest tests.test_regie_engine           # Eine Datei
python -m unittest tests.test_regie_engine.TestPovStoryPreset   # Eine Klasse
```

---

## 10. Output-Dateien

| Pfad | Inhalt |
|------|--------|
| `output/pipeline_results.json` | Gesammelte Analyse aller Phasen (Eingabe für die Regie). Wird nach jeder Phase aktualisiert. |
| `output/edit_plan.json` | Schnittplan: Clips mit `start`/`end`/`lut`/`transition`; bei `pov_story` zusätzlich `hook_text` + pro Clip `phase`. |
| `output/snippet_001…00N.mp4` | Einzelne geschnittene Clips (Bausteine, in Plan-Reihenfolge). |
| **`output/reel_<preset>.mp4`** | **Das fertige Reel** (alle Snippets zusammengefügt, 1080×1920\@30fps). |
| `output/captions.json` | Dateinamen + Instagram-Captions aus Phase 4. |
| `output/concat_list.txt` | FFmpeg-Liste der Snippets (Reihenfolge); manuell editierbar, dann neu concatenaten. |
| `luts/*.cube` | Farb-LUTs: `underground_dark`, `vhs_analog`, `neon_nights`. |
| `.env` | API-Keys + Konfiguration – **niemals committen.** |

---

## 11. Troubleshooting

| Symptom | Ursache | Lösung |
|--------|---------|--------|
| `ollama package not installed` | Python-Client fehlt | `python -m pip install ollama` (Ollama-Server muss separat laufen) |
| Vision liefert 0 Tags für einen Clip | `gemma4:e2b` antwortete mit leerem JSON (nicht-deterministisch) | Unkritisch; ggf. Clip erneut taggen (Resume überspringt die fertigen) |
| Vision bricht mitten drin ab | Rechner ist eingeschlafen / Prozess gekillt | `--phase vision` erneut starten → macht ab dem letzten Clip weiter; Ruhezustand deaktivieren |
| Regie: `Invalid JSON … char 0` | Reasoning-Modell hat das Token-Budget aufgebraucht | Bereits gelöst (`max_tokens=8192`); bei sehr großen Analysen Provider wechseln |
| Regie: `model not found` | Modell-ID gilt nicht für deinen Account | In `.env` `CLAUDE_MODEL`/`DEEPSEEK_MODEL`/`GEMINI_MODEL` auf eine gültige ID setzen |
| Export: FFmpeg-Fehler bei `lut3d` | Absolute Windows-Pfade brechen den Filtergraphen | Bereits gelöst (relativer LUT-Pfad in Phase 5) – aus dem Projekt-Root starten |
| Reel ist kürzer als `-d` | Plan plante mehr Sekunden, als der Quell-Clip lang ist | Normal – FFmpeg exportiert nur die echte Clip-Länge |
| „No edit plan available – skipping assembly" | Phase 3 lieferte keinen Plan (kein Key / Provider-Fehler) | Provider-Status prüfen ([Abschnitt 2]); ggf. `--provider` setzen |

---

## 12. Kurz-Referenz

```powershell
# Volles pov_story-Reel
python main.py -i ./input_pov -p pov_story -d 45

# Empfohlener pov_story-Ablauf (Vision einmal, dann beliebig oft Plan+Reel)
python main.py -i ./input_pov --phase vision
python main.py -i ./input_pov -p pov_story -d 45 --phase regie export

# Provider-Status (kostenlos)
@'
import regie_engine as r
[print(p["name"], p["model"], p["available"]) for p in r.list_available_providers()]
'@ | python -

# Nur LUTs
python main.py --luts

# Tests
python -m unittest discover -s tests -t .
```
