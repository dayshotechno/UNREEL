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
