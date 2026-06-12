# Lokalen Regisseur benchmarken (auf echten Analyse-JSONs)

Der lokale Provider ist Opt-in. Modell + Engine per ENV tauschbar → vergleiche selbst.
Zwei Engines (`LOCAL_REGIE_ENGINE`):
  - `ollama` – braucht Ollama-Dienst + gezogenes Modell
  - `mlx`    – reines mlx-lm via outlines, KEIN Ollama

## Voraussetzung – Engine A (ollama)
```bash
brew install ollama
ollama serve &
ollama pull qwen3.5:9b
ollama pull qwen2.5:14b
```

## Voraussetzung – Engine B (reines MLX, kein Ollama)
```bash
pip install "outlines[mlxlm]"     # mlx-lm + outlines
# Modelle werden beim ersten Lauf von HF geladen (z.B. Qwen2.5-7B-Instruct-4bit)
```

## Vergleichslauf – Engine A (ollama)
```bash
# benötigt eine vorhandene Analyse: output/pipeline_results.json
for M in qwen3.5:9b qwen2.5:14b; do
  echo "=== ollama / $M ==="
  LOCAL_REGIE_ENGINE=ollama LOCAL_REGIE_MODEL=$M time \
    python -m analyzer.regie_engine output/pipeline_results.json --provider local
done
```

## Vergleichslauf – Engine B (mlx)
```bash
for M in mlx-community/Qwen2.5-7B-Instruct-4bit mlx-community/Qwen3-8B-4bit; do
  echo "=== mlx / $M ==="
  LOCAL_REGIE_ENGINE=mlx LOCAL_REGIE_MODEL=$M time \
    python -m analyzer.regie_engine output/pipeline_results.json --provider local
done
```

## Direktvergleich gegen Cloud (wenn ein Key gesetzt ist)
```bash
python -m analyzer.regie_engine output/pipeline_results.json --provider deepseek
```

## ollama vs. mlx — welche Engine?
- `ollama`: einfachster Weg, breiteste Modellauswahl, sehr robustes Schema-JSON.
- `mlx`: keine Extra-App, voll im venv; outlines wandelt Schema→Regex
  (bei DEINEM flachen EditPlan unkritisch). Etwas mehr Setup (`outlines[mlxlm]`).

## Worauf achten (3 Kriterien)
1. **Schema/Validität:** Kommt ein gültiger EditPlan ohne Parse-Fehler? (Sollte
   dank `format=`-Constraint immer der Fall sein. Wenn nicht → Modell zu klein.)
2. **Inhaltliche Qualität:** Landen Cuts auf Beats/Drops? Erzählt der Plan eine
   Story (before→during→after)? Sind die `reason`-Felder sinnvoll – oder generisch?
3. **Ressourcen/Tempo:** Laufzeit pro Plan; Memory Pressure (Activity Monitor).
   Bei 16 GB: 14B ist eng – wenn Vision-Phase im selben Lauf war, vorher entladen.

## Erwartungshaltung (ehrlich)
- Lokal 9–14B erreicht NICHT die Schnitt-Qualität von Claude/Gemini/DeepSeek bei
  komplexen, langen Schnittlisten. Für einfache Highlight-Reels meist brauchbar.
- Reasoning-Modelle (DeepSeek-R1-Distill etc.) können "denken" und das Schema
  sprengen → mit dem `format=`-Constraint meist abgefangen, aber langsamer.
- Empfehlung bleibt: lokal als kostenlose/offline Option, Cloud für die Stücke,
  bei denen die Schnittqualität zählt.
```
