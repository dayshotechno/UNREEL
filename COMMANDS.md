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

**Tarantino-Preset** erfordert eine Musikdatei (`--music`). Der Drop der Musik wird automatisch mit dem Video-Drop synchronisiert. Die Reel-Länge wird auf 30 s gesetzt, unabhängig von `-d`.

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
