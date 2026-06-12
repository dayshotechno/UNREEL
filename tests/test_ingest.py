"""
Tests für analyzer/ingest.py – Ingestion & Renaming (Phase 0).

Stil-konsistent zu den übrigen tests/: keine echten Videos, ffprobe wird
über den mtime-Fallback umgangen (für Dummy-Dateien hat ffprobe keine
creation_time, also greift automatisch os.path.getmtime).
"""

import os
import time

import pytest

import ingest


@pytest.fixture
def src(tmp_path, monkeypatch):
    """Isolierter Input-Ordner + gemocktes config.SUPPORTED_EXTENSIONS."""
    monkeypatch.setattr(ingest.config, "VIDEO_SOURCE_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4", ".mov"], raising=False)
    return tmp_path


def _make(path, content: bytes, ts: float | None = None):
    path.write_bytes(content)
    if ts is not None:
        os.utime(path, (ts, ts))
    return path


def _ts(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def test_renames_to_timestamp(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "raw_clip.mp4", b"A" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250612_143000.mp4").exists()
    assert not (src / "raw_clip.mp4").exists()
    assert len(result.renamed) == 1


def test_removes_duplicates(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "a.mp4", b"SAME" * 1000, base)
    _make(src / "b.mp4", b"SAME" * 1000, base + 10)  # identischer Inhalt

    result = ingest.ingest_directory(src)

    remaining = [f for f in os.listdir(src) if f.endswith(".mp4")]
    assert len(remaining) == 1
    assert len(result.duplicates_removed) == 1


def test_skips_hidden_and_unsupported(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "._hidden.mp4", b"x", base)
    _make(src / "notes.txt", b"hello", base)

    result = ingest.ingest_directory(src)

    assert result.renamed == []
    assert result.duplicates_removed == []
    assert (src / "._hidden.mp4").exists()
    assert (src / "notes.txt").exists()


def test_keeps_already_named_files(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "UNREEL_20250101_000000.mp4", b"C" * 4000, base)

    result = ingest.ingest_directory(src)

    assert (src / "UNREEL_20250101_000000.mp4").exists()
    assert result.renamed == []
    assert str(src / "UNREEL_20250101_000000.mp4") in result.final_files


def test_timestamp_collision_gets_counter(src):
    base = _ts("2025-06-12 14:30:00")
    # Zwei unterschiedliche Inhalte, gleiche Endung, gleicher Timestamp.
    _make(src / "first.mp4", b"FIRST" * 1000, base)
    _make(src / "second.mp4", b"SECND" * 1000, base)

    ingest.ingest_directory(src)

    names = sorted(f for f in os.listdir(src) if f.startswith("UNREEL_"))
    assert "UNREEL_20250612_143000.mp4" in names
    assert "UNREEL_20250612_143000_1.mp4" in names


def test_final_files_feeds_pipeline(src):
    base = _ts("2025-06-12 14:30:00")
    _make(src / "x.mp4", b"X" * 4000, base)
    _make(src / "UNREEL_20250101_000000.mov", b"Y" * 4000, base)

    result = ingest.ingest_directory(src)

    # final_files enthält genau die Dateien, die danach existieren & verarbeitbar sind.
    for p in result.final_files:
        assert os.path.exists(p)
    assert len(result.final_files) == 2


def test_missing_source_dir_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest.config, "SUPPORTED_EXTENSIONS", [".mp4"], raising=False)
    result = ingest.ingest_directory(tmp_path / "does_not_exist")
    assert result.final_files == []
    assert result.errors == []
