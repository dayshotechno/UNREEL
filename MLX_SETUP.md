# UNREEL auf M1 Pro (16 GB) + MLX – Setup & Modellwahl

> Stand der Recherche: Juni 2026. Modelle/Frameworks ändern sich schnell –
> prüfe Versionen beim Einrichten.

## Hardware-Realität (M1 Pro, 16 GB unified memory)
- Real nutzbar für Modelle: **~11–12 GB** (Rest: macOS + Inferenz-Runtime + KV-Cache).
- **Sweet Spot: 7–9B-Modelle @ 4-bit.** Größeres geht in Swap → unbrauchbar langsam.
- **Goldene Regel:** Vision-Modell und Text-Modell **NICHT gleichzeitig** geladen
  halten. Pipeline-Reihenfolge: Vision laden → alle Frames taggen → **entladen**
  → dann Caption-/Text-Modell laden. (Genau dafür hat das MLX-Backend `unload()`.)
- Erwartung: ~18–25 tok/s bei einem ~7B-Textmodell @4bit auf M1 Pro.

## Warum MLX (statt weiter Ollama)
- MLX ist für Apple Silicon gebaut (Metal + unified memory, zero-copy),
  i.d.R. 10–20 % schneller als llama.cpp/Ollama auf M-Chips.
- `mlx-vlm` deckt Vision-Modelle ab (Qwen2.5-VL, Gemma 3, u.a.).

## Architektur-Entscheidung (umgesetzt)
**mlx-vlm als Python-Bibliothek, hinter einer Backend-Abstraktion.**
- Volle RAM-Kontrolle (explizites laden/entladen) – wichtig bei 16 GB.
- Reproduzierbar (im Repo + requirements gepinnt), passt zum CLI-Charakter.
- Die Abstraktion (`vision_backends.py`) erlaubt Umschalten Ollama↔MLX per ENV,
  ohne Code-Fork. Dasselbe Repo läuft auf altem CPU-Rechner UND auf dem M1 Pro.

## Modellempfehlungen (Start; per ENV tauschbar)

### Vision (Frame-Tagging) – beide testen, dann entscheiden
| Modell | RAM @4bit | Tempo | Wann |
|---|---|---|---|
| `mlx-community/Qwen2.5-VL-7B-Instruct-4bit` | ~5–6 GB | langsamer | beste Tag-Qualität |
| `mlx-community/Qwen2.5-VL-3B-Instruct-4bit` | ~2–3 GB | schnell | RAM-schonend, sicher auf 16 GB |

→ Beide sind Upgrades gegenüber dem bisherigen `gemma4:e2b` (sehr klein).
Benchmark auf DEINEM Material (siehe unten), dann ENV festlegen.

### Copywriter (Captions) – Textmodell
| Modell | RAM @4bit | Wann |
|---|---|---|
| `mlx-community/Qwen2.5-7B-Instruct-4bit` | ~4–5 GB | guter Default, auf M1 Pro/16GB validiert |
| `mlx-community/Qwen2.5-3B-Instruct-4bit` | ~2 GB | wenn 7B + Vision zu eng wird |

## Installation auf dem M1 Pro
```bash
# 1. Python 3.11+ (z.B. via Homebrew), frische venv
python3 -m venv .venv && source .venv/bin/activate

# 2. MLX-Stack
pip install mlx mlx-vlm mlx-lm

# 3. Restliche Projekt-Deps (OHNE die alten Cloud-/Web-Sachen, je nach Stand)
pip install -r requirements.txt

# 4. ENV setzen (in .env)
echo 'VISION_BACKEND=mlx'                                            >> .env
echo 'MLX_VISION_MODEL=mlx-community/Qwen2.5-VL-7B-Instruct-4bit'    >> .env
echo 'MLX_TEXT_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit'         >> .env
```
> Erster Lauf lädt die Modelle von Hugging Face (mehrere GB) → einmalig dauert es.

## requirements.txt – Anpassung
- **Hinzufügen** (Apple-Silicon-only, daher mit Markern):
  ```text
  mlx>=0.18 ; sys_platform == "darwin" and platform_machine == "arm64"
  mlx-vlm>=0.1 ; sys_platform == "darwin" and platform_machine == "arm64"
  mlx-lm>=0.18 ; sys_platform == "darwin" and platform_machine == "arm64"
  ```
  (Marker sorgen dafür, dass `pip install` auf Nicht-Apple-Maschinen nicht bricht –
   dort greift dann das Ollama-Backend.)
- `ollama` bleibt drin (Fallback-Backend).
- Cloud-Provider (`anthropic`, `google-generativeai`, `openai`) bleiben für die
  Regie-Phase – die ist davon unberührt.

## Mini-Benchmark (auf echtem Material, beide Vision-Modelle)
```bash
# 7B
VISION_BACKEND=mlx MLX_VISION_MODEL=mlx-community/Qwen2.5-VL-7B-Instruct-4bit \
  time python -m analyzer.vision_engine input/<dein_clip>.mp4

# 3B
VISION_BACKEND=mlx MLX_VISION_MODEL=mlx-community/Qwen2.5-VL-3B-Instruct-4bit \
  time python -m analyzer.vision_engine input/<dein_clip>.mp4
```
Vergleiche: (a) Laufzeit, (b) ob die Tags zu deinem Auge passen, (c) RAM-Druck
(Activity Monitor → „Memory Pressure" bleibt grün?). Wähle danach das ENV-Default.
