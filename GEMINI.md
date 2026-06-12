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
