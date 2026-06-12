"""
UNREEL – Ingestion & Renaming (Phase 0)

Gerettet aus der (gelöschten) Flask-Web-App `app.py` (_ingest_file / run_watchdog).

Verantwortung:
    1. Dedup    – Duplikate via (Dateigröße + MD5 der ersten 1 MB) erkennen
                  und entfernen. Exakt, deterministisch, offline. Kein KI.
    2. Timestamp – echten Aufnahme-Zeitpunkt aus den Metadaten lesen
                  (ffprobe creation_time), Fallback: Datei-mtime.
    3. Rename   – nach UNREEL_YYYYMMDD_HHMMSS<ext>, mit Kollisions-Counter.

Unterschied zur Web-Version:
    - Kein Dauer-Watchdog (30-s-Polling). Stattdessen einmaliger Lauf über
      den Input-Ordner, gedacht als Pipeline-Phase 0 oder Standalone-CLI.
    - `logging` statt `print`.
    - Dedup-Hash wird pro Lauf frisch aufgebaut (kein modul-globaler Zustand,
      der über Läufe hinweg "leakt").
    - Typisierte Dataclass-Ergebnisse mit `.to_dict()` (Stil-konsistent).
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_HASH_CHUNK_BYTES = 1024 * 1024  # erste 1 MB – schnell & in der Praxis kollisionsarm
_FILENAME_PREFIX = "UNREEL_"
_TS_FORMAT = "%Y%m%d_%H%M%S"


@dataclass
class IngestResult:
    """Ergebnis eines Ingestion-Laufs über einen Ordner."""
    renamed: list[tuple[str, str]] = field(default_factory=list)  # (alt, neu)
    duplicates_removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)   # (datei, grund)
    final_files: list[str] = field(default_factory=list)          # Pfade nach dem Lauf

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


def _is_supported(path: Path) -> bool:
    if path.name.startswith("._"):
        return False
    exts = {e.lower() for e in config.SUPPORTED_EXTENSIONS}
    return path.suffix.lower() in exts


def _quick_hash(path: Path) -> str | None:
    """Dedup-Signatur: '<groesse>_<md5(erste 1MB)>'. None bei Lesefehler."""
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            chunk = f.read(_HASH_CHUNK_BYTES)
        return f"{size}_{hashlib.md5(chunk).hexdigest()}"
    except OSError as e:
        logger.warning("Hash fehlgeschlagen für %s: %s", path.name, e)
        return None


def _read_creation_time(path: Path) -> datetime:
    """
    Echter Aufnahme-Zeitstempel aus den Metadaten (ffprobe creation_time).
    Fallback-Reihenfolge: ffprobe -> Datei-mtime -> jetzt.
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "format_tags=creation_time",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ]
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=10
        ).strip()
        if out:
            # "2025-06-12T14:30:00.000000Z" -> erste 19 Zeichen reichen
            return datetime.strptime(out[:19], "%Y-%m-%dT%H:%M:%S")
    except (subprocess.SubprocessError, ValueError, OSError) as e:
        logger.debug("ffprobe creation_time nicht lesbar für %s: %s", path.name, e)

    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return datetime.now()


def _target_name(path: Path, seen_targets: set[str]) -> Path:
    """
    Liefert den Ziel-Pfad UNREEL_YYYYMMDD_HHMMSS<ext>, kollisionsfrei.
    `seen_targets` verhindert Kollisionen auch innerhalb desselben Laufs.
    """
    ts = _read_creation_time(path).strftime(_TS_FORMAT)
    ext = path.suffix.lower()
    base = f"{_FILENAME_PREFIX}{ts}"
    candidate = path.with_name(f"{base}{ext}")

    counter = 1
    while (candidate.exists() and candidate != path) or str(candidate) in seen_targets:
        candidate = path.with_name(f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def ingest_directory(source_dir: str | Path | None = None) -> IngestResult:
    """
    Verarbeitet alle unterstützten Videos in `source_dir`:
      1. Duplikate löschen, 2. nach UNREEL_<timestamp> umbenennen.

    Bereits korrekt benannte Dateien (Prefix UNREEL_) werden nicht erneut
    umbenannt, aber weiterhin auf Duplikate geprüft.

    Returns:
        IngestResult mit Umbenennungen, gelöschten Duplikaten, Fehlern und
        der finalen Dateiliste (Pfade), die die Pipeline weiterverarbeitet.
    """
    source_dir = Path(source_dir or config.VIDEO_SOURCE_DIR)
    result = IngestResult()

    if not source_dir.exists():
        logger.warning("Input-Ordner existiert nicht: %s", source_dir)
        return result

    seen_hashes: dict[str, Path] = {}   # signatur -> behaltener Pfad
    seen_targets: set[str] = set()      # bereits vergebene Ziel-Pfade (dieser Lauf)

    for path in sorted(source_dir.iterdir()):
        if not path.is_file() or not _is_supported(path):
            result.skipped.append(str(path))
            continue

        # 1) Dedup
        sig = _quick_hash(path)
        if sig is None:
            result.errors.append((str(path), "hash failed"))
            continue
        if sig in seen_hashes:
            try:
                path.unlink()
                result.duplicates_removed.append(str(path))
                logger.info("Duplikat entfernt: %s (== %s)",
                            path.name, seen_hashes[sig].name)
            except OSError as e:
                result.errors.append((str(path), f"delete failed: {e}"))
            continue
        seen_hashes[sig] = path

        # 2) Rename (nur wenn nötig)
        if path.name.startswith(_FILENAME_PREFIX):
            result.final_files.append(str(path))
            seen_targets.add(str(path))
            continue

        target = _target_name(path, seen_targets)
        try:
            path.rename(target)
            result.renamed.append((str(path), str(target)))
            seen_hashes[sig] = target
            seen_targets.add(str(target))
            result.final_files.append(str(target))
            logger.info("Umbenannt: %s -> %s", path.name, target.name)
        except OSError as e:
            result.errors.append((str(path), f"rename failed: {e}"))
            result.final_files.append(str(path))  # trotzdem weiterverarbeiten

    logger.info(
        "Ingestion fertig: %d umbenannt, %d Duplikate entfernt, %d Fehler",
        len(result.renamed), len(result.duplicates_removed), len(result.errors),
    )
    return result


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="UNREEL Ingestion & Renaming (Phase 0)")
    parser.add_argument("source", nargs="?", default=None,
                        help="Input-Ordner (Default: config.VIDEO_SOURCE_DIR)")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    args = parser.parse_args()

    res = ingest_directory(args.source)
    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"  Umbenannt:          {len(res.renamed)}")
        print(f"  Duplikate entfernt: {len(res.duplicates_removed)}")
        print(f"  Fehler:             {len(res.errors)}")
        print(f"  Dateien bereit:     {len(res.final_files)}")
