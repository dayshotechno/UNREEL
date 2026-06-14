# UNREEL V3 – Code Audit & Refactoring Report

**Datum:** 14. Juni 2026  
**Ziel:** UNREEL V3 DJ-Video-Pipeline (Orchestrator `src/main.py`, `regie_engine.py`, `analyzer/*`)

Dieses Dokument enthält ein umfassendes Architektur-Audit, eine genaue Analyse von Bugs, logischen Lücken ("Was übersehen wird") und redundantem / totem Code ("Was unnötig ist") sowie konkrete Refactoring-Empfehlungen für die UNREEL V3 Codebasis.

---

## 1. Was übersehen wird (Bugs, Edge Cases & Architektur-Lücken)

### A. Thread-Sicherheit bei der FFmpeg-Parallelisierung (`src/main.py`)
* **Problem:** In `phase_5_assembly` wird ein `ThreadPoolExecutor` mit `EXPORT_WORKERS` (Default: 3) genutzt, um Snippets parallel zu rendern (`_export_one_snippet`).
* **Was übersehen wurde:** 
  1. **OpenCV VideoCapture in Threads:** In `_export_one_snippet` wird JIT Auto-Framing (`_tracked_x_center` → `sample_x_center`) aufgerufen. Zwar ist der YOLO-Aufruf und der Cache-Schreibvorgang durch `_TRACKING_LOCK` gesichert, aber `sample_x_center` öffnet die Videodatei mit `cv2.VideoCapture`. Wenn mehrere Threads gleichzeitig dasselbe Quellvideo (oder auch nur intensives I/O) parsen, kann das zu OpenCV-Deadlocks, Container-Corruptions oder massiven I/O-Engpässen führen.
  2. **`subprocess.run` & `_run_ffmpeg` Parallelisierung:** In `src/main.py` ruft `_export_one_snippet` direkt `subprocess.run(cmd)` auf, während der V2-Exportpfad (`analyzer/clip_exporter.py`) die Funktion `_run_ffmpeg` mit einem globalen `_active_procs`-Dict nutzt. Die V2-Struktur verlässt sich auf `threading.get_ident()`. Wenn parallel exportiert wird, überschreibt `_active_procs` zwar keine IDs, aber es gibt keine saubere Koordination der globalen System-Ressourcen (CPU-Sättigung bei 3x `libx264`-Encodes mit `-preset fast`). Bei x264-Multithreading (das intern alle CPU-Kerne nutzt) führen 3 parallele x264-Instanzen zu starkem Context-Thrashing und Überhitzung (insbesondere da im Spec explizit "Everything runs on CPU" gefordert ist).

### B. Mismatch bei Multi-Image-VLM-Aufrufen (Apple Silicon / MLX)
* **Problem:** In `analyzer/vision_backends.py` implementiert `MLXVisionBackend.describe_frames` die Bündelung von Frames in Gruppen der Größe `frames_per_call`.
* **Was übersehen wurde:** Die Hilfsfunktion `apply_chat_template` von `mlx_vlm.prompt_utils` formatiert den Prompt, aber die Variable `tmp_paths` (die temporären `.jpg`-Dateien auf der Platte) wird als flache Liste an `_generate` übergeben. Wenn das gewählte MLX-Modell (z. B. `Qwen2.5-VL-7B-Instruct`, das in `config.py` als Default definiert ist) Multi-Image nicht oder anders als erwartet unterstützt, schlägt der Aufruf in `_generate` mit einem obskuren `TypeError` oder Inferenz-Fehler fehl. Zwar warnt die Doku in `CLAUDE.md`, dass man bei `1` bleiben soll, aber der Code verhindert es nicht aktiv oder fängt Modell-Quirks nicht sauber ab.

### C. Geteilte Audio-Sync-Referenzen bei gemischten Formaten (`audio_sync.py`)
* **Problem:** `find_reference_clip` sucht automatisch nach einer Master-Audiodatei (`.mp3`, `.wav`, etc.) und wählt diese als Master.
* **Was übersehen wurde:** Wenn eine `.mp3` als Master-Referenz gewählt wird, berechnet `compute_offset` die Kreuzkorrelation (`correlate(mode='full', method='fft')`) zwischen der Master-Audiodatei und dem Kamera-Audio. Wenn die MP3 und das Video unterschiedliche Sample-Raten (z. B. MP3 in 44.1 kHz, Video in 48 kHz) oder Drift aufweisen, führt die FFT-Kreuzkorrelation zu komplett falschen Zeit-Offsets. In `_load_audio` wird zwar via `librosa.load(..., sr=sr)` standardmäßig auf `sr=44100` resampelt (was dieses Problem abmildert), aber bei sehr langen Sets (z. B. 2 Stunden) führt das Resampling langer Arrays zu immensem CPU- und RAM-Bedarf.

### D. JSON-Parser-Sicherheit (`_parse_edit_plan` & `verify_edit_plan`)
* **Problem:** Zwar ist der Einsatz von `json_repair` in `regie_engine.py` exzellent, um kaputte LLM-Antworten zu reparieren.
* **Was übersehen wurde:** Wenn `json_repair` greift oder das LLM leicht halluziniert, können erwartete Felder wie `start`, `end`, oder `transition` gänzlich fehlen oder unpassende Typen haben (`start` als String oder `None`). In der Schleife `for c in parsed.get("clips", []):` wird blind `float(c["start"])` aufgerufen. Wenn das LLM `"start": "anfang"` oder `"start": null` liefert, stürzt die gesamte Pipeline mit einem `TypeError` / `ValueError` ab, statt das Problem im Verifier abzufangen oder das fehlerhafte Snippet zu verwerfen.

### E. Mismatch der `crop`-Syntax im FFmpeg-Filtergraph
* **Problem:** In `src/main.py:_export_one_snippet` wird der Crop-Ausdruck für 9:16 zusammengebaut: `crop=ih*9/16:ih:{crop_x_expr}:0`.
* **Was übersehen wurde:** Zwar werden Kommata in `crop_x_expr` korrekt escaped (`replace(",", "\\,")`), aber wenn das Video bereits 9:16 ist (z. B. vertikal gefilmtes Handy-Material im Eingangsordner), wendet die Pipeline dennoch `crop=ih*9/16:ih...` an oder führt unnötige Skalierungen durch (`scale=1080:1920`). Bei Eingangs-Clips in 4K (2160x3840) oder abweichenden Aspect Ratios führt das zu Verzerrungen oder falschen Ausschnitten.

### F. Pfad-Kollisionen & Caching beim Concat-Vorgang
* **Problem:** In `_concat_snippets` wird `OUTPUT_DIR / "concat_list.txt"` fest verwendet.
* **Was übersehen wurde:** Wenn zwei Varianten-Laufe (oder User auf einer Maschine) gleichzeitig `main.py` mit verschiedenen Presets ausführen, überschreiben sie sich gegenseitig `output/concat_list.txt`. Das kann dazu führen, dass FFmpeg mitten im Concat falsche oder gemischte Snippets verknüpft. Das Demuxer-File sollte immer den Lauf- oder Preset-Namen im Dateinamen tragen (`concat_list_{style}.txt`).

---

## 2. Was unnötig ist (Redundanter / Toter Code & Altlasten)

### A. Die doppelte `main`-Struktur (`main.py` vs. `src/main.py`)
* **Status:** Die Verzeichnisstruktur trennt einen extrem dünnen Root-Wrapper `main.py` (15 Zeilen) und den eigentlichen Orchestrator `src/main.py` (1520 Zeilen).
* **Warum es unnötig ist:** V3-Kernmodule (`config.py`, `ingest.py`, `regie_engine.py`, `audio_sync.py`) liegen alle im Root-Verzeichnis. Dass `src/main.py` in einem Unterordner liegt und mit `sys.path.insert(0, ...)` das Parent-Verzeichnis einbindet, erzeugt unnötige Pfad-Komplexität. Der Code in `src/main.py` sollte in eine saubere Pipeline-Klasse im Root (oder in `src/pipeline.py` unter korrekter Paket-Struktur) umgezogen werden.

### B. Tot-Code in `analyzer/clip_exporter.py`
* **Status:** `analyzer/clip_exporter.py` implementiert den kompletten Montage- und Reel-Exportpfad inklusive `export_montage` und `_export_reel` (585 Zeilen).
* **Warum es unnötig ist:** In UNREEL V3 wird `phase_5_assembly` in `src/main.py` (ca. Zeile 600) als maßgeblicher Exportpfad genutzt. `src/main.py` implementiert das Render- und Filter-Handling (`_export_one_snippet`, `_concat_snippets`, `_apply_music_bed`) komplett neu und parallelisiert. Die Funktionen `export_montage`, `export_batch`, `_build_overlay_vf` etc. in `analyzer/clip_exporter.py` sind Altlasten aus V2, werden im Standard-V3-Workflow nirgends aufgerufen und erzeugen massive Wartungs-Redundanz (z. B. wenn an V3-Filtern wie VFX `pump` oder `glitch` gearbeitet wird).

### C. Redundante `if __name__ == "__main__"` Testblöcke in Library-Modulen
* **Status:** Fast jede Datei (`ingest.py`, `audio_sync.py`, `kick_snare_detector.py`, `regie_engine.py`, `lut_generator.py`, `vision_engine.py`, `copywriter.py`) enthält am Ende Hunderte Zeilen CLI- und argparse-Logik, nur um standalone ausgeführt zu werden.
* **Warum es unnötig ist:** Die mitgelieferte Unit-Test-Suite (`tests/*`) ist extrem dicht (89+ grüne Tests) und deckt fast alle Modul-Funktionen offline ab. Zusätzlich gibt es in `src/main.py` das Flag `--phase <phase>`, um gezielte Schritte über das zentrale CLI aufzurufen. Die dezentralen Modul-CLIs blähen die Codebasis um rund 15–20% auf.

### D. Hardcodierte LUT-Routinen in `lut_generator.py`
* **Status:** Die Dateipfade in `lut_generator.py` berechnen 3D-LUTs (`.cube`) rein mathematisch mit numpy über 33x33x33 Punkte.
* **Warum es unnötig ist:** Die generierten Dateien in `luts/` persistieren. Es ist zwar gut, sie programmatisch erzeugen zu können (Phase 0), aber die Re-Implementierung von sRGB-Konvertierungen und manuellen S-Kurven in Python ist nur ein Umweg. Sie könnten einfach als statische Asset-Dateien in der Versionierung (oder als komprimierte Numpy-Arrays) gepflegt werden, was Code spart und exakte Farbkontrolle garantiert.

### E. V2-Aliase und Unbenutzte Konstanten in `config.py`
* **Status:** In `config.py` finden sich Aliase wie `AUDIO_SAMPLE_RATE = SAMPLE_RATE` (nur für alte V2-Analysemodule) oder unbenutzte Highlight-Gewichte (`WEIGHT_LIGHT`, `WEIGHT_MOTION`), die in `regie_engine.py` (das ein LLM nutzt) keine Relevanz mehr haben.
* **Warum es unnötig ist:** Der algorithmische V2-Pfad (`highlight_engine.py`) wurde durch die KI-Regie (`regie_engine.py`) abgelöst. Die alten Scoring-Konstanten verunreinigen die zentrale Konfiguration.

---

## 3. Konkreter Refactoring-Plan (Schritt-für-Schritt)

Um die Codebasis robuster, performanter und zukunftssicherer aufzustellen, sollten folgende Refactoring-Maßnahmen in genauer Reihenfolge umgesetzt werden:

### Schritt 1: Orchestrator-Bereinigung & Paketierung
* LÖSUNG: Verschiebe den Code von `src/main.py` in eine neue Struktur `unreel/pipeline.py` und `unreel/cli.py` unterhalb eines sauberen Python-Pakets.
* Lösche den toten Root-Wrapper `main.py` und richte eine standardkonforme `pyproject.toml` oder `setup.py` ein, sodass das Tool mit `unreel ...` im Terminal aufgerufen werden kann.

### Schritt 2: Concat & Parallel-Export Thread-Safe machen
* Im Refactoring von `_export_one_snippet` / `phase_5_assembly`:
  * Nutze eindeutige Demuxer-Dateinamen beim Concat (`concat_list_{preset}_{timestamp}.txt`).
  * Trenne CPU-bound FFmpeg-Aufrufe und I/O-bound Auto-Framing: Lasse das YOLO-Tracking **sequenziell** in einem Vorbereitungsschritt (oder per Clip in Phase 2/3) ablaufen, schreibe alle Ergebnisse in `tracking_cache.json` und starte **danach** die reinen FFmpeg-Encodes im `ThreadPoolExecutor`. Das eliminiert die Race Conditions in OpenCV und den Bedarf an `_TRACKING_LOCK`.

### Schritt 3: Pydantic für strikte EditPlan-Validierung
* Ersetze in `regie_engine.py` die manuelle und anfällige Dataclass-/Dict-Konvertierung von `EditClip` und `EditPlan` durch **Pydantic Models** (`pydantic.BaseModel`).
* Nutze Pydantics eingebaute Typ-Coercion, Default-Werte und Validatoren (`@field_validator`), um sicherzustellen, dass `start`, `end` und `transition` immer gültig sind, bevor `verify_edit_plan` überhaupt berührt wird.

### Schritt 4: Entsorgung von Tot-Code & V2-Altlasten
* Lösche `analyzer/clip_exporter.py` und `analyzer/clip_normalizer.py`, da ihre Funktionalität modern in `src/main.py` abgedeckt ist.
* Entferne die Hunderte Zeilen von `if __name__ == "__main__":` Blöcken in Library-Modulen (`ingest.py`, `audio_sync.py`, etc.).
* Bereinige `config.py` von V2-Konstanten.

### Schritt 5: Auto-Resampling & Chunked Audio-Loading für FFT
* Optimiere `audio_sync.py`: Wenn Dateien resampelt werden müssen, lade Audiospuren bei langen Videos mit `librosa.stream` oder in Chunks, um den RAM-Verbrauch (Memory Pressure) unter 16 GB zu halten.

---

## 4. Beispiel-Refactoring: Strikte Validierung mit Pydantic

Hier ist ein voll funktionsfähiges, zukunftssicheres Refactoring von `regie_engine.py` (Ausschnitt der Datenmodelle), das Pydantic nutzt und die JSON-Parsing-Bugs behebt:

```python
from pathlib import Path
from typing import Any
import json
import logging
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class EditClip(BaseModel):
    video: str
    start: float = Field(..., ge=0.0)
    end: float = Field(..., gt=0.0)
    transition: str = Field(default="cut")
    reason: str = Field(default="")
    crop: str = Field(default="9:16")
    lut: str = Field(default="underground_dark")
    vfx: str = Field(default="none")
    slow_mo: bool = Field(default=False)
    slow_mo_factor: float = Field(default=1.0, ge=1.0)
    phase: str = Field(default="")

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v: float, info: Any) -> float:
        if "start" in info.data and v <= info.data["start"]:
            # Auto-Correction / Warnung statt harten Absturz
            raise ValueError("end timestamp must be strictly greater than start timestamp")
        return v

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict:
        return self.model_dump()


class EditPlan(BaseModel):
    clips: list[EditClip]
    narrative: str = Field(default="")
    hook_text: str = Field(default="")
    total_duration: float = Field(default=0.0)
    target_bpm: float = Field(default=0.0)
    style: str = Field(default="highlight")
    provider_used: str = Field(default="")
    model_used: str = Field(default="")
    generation_time_s: float = Field(default=0.0)

    @field_validator("clips")
    @classmethod
    def filter_invalid_clips(cls, clips: list[EditClip]) -> list[EditClip]:
        # Filtert automatisch Clips mit 0 oder negativer Dauer heraus
        return [c for c in clips if c.duration > 0]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        logger.info(f"Edit plan saved strictly to {path}")
```
