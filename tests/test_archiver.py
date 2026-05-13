"""Tests for envpatch.archiver."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from envpatch.archiver import ArchiveEntry, ArchiveResult, archive

_FIXED_TS = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _write(tmp_path: Path, name: str, content: str = "KEY=value\n") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_archive_creates_timestamped_copy(tmp_path):
    source = _write(tmp_path, ".env")
    archive_dir = tmp_path / "backups"
    result = archive([source], archive_dir=archive_dir, timestamp=_FIXED_TS)

    assert result.is_clean
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.source == source
    assert entry.destination.parent == archive_dir
    assert "20240615T120000" in entry.destination.name
    assert entry.destination.exists()
    assert entry.destination.read_text() == "KEY=value\n"


def test_archive_creates_archive_dir_if_missing(tmp_path):
    source = _write(tmp_path, ".env")
    archive_dir = tmp_path / "nested" / "backups"
    result = archive([source], archive_dir=archive_dir, timestamp=_FIXED_TS)

    assert result.is_clean
    assert archive_dir.is_dir()


def test_archive_missing_source_records_error(tmp_path):
    missing = tmp_path / "does_not_exist.env"
    result = archive([missing], archive_dir=tmp_path / "backups", timestamp=_FIXED_TS)

    assert not result.is_clean
    assert len(result.errors) == 1
    assert "not found" in result.errors[0]


def test_archive_multiple_files(tmp_path):
    a = _write(tmp_path, ".env")
    b = _write(tmp_path, ".env.production", "DB=prod\n")
    archive_dir = tmp_path / "backups"
    result = archive([a, b], archive_dir=archive_dir, timestamp=_FIXED_TS)

    assert result.is_clean
    assert len(result.entries) == 2


def test_archive_result_str_clean(tmp_path):
    source = _write(tmp_path, ".env")
    archive_dir = tmp_path / "backups"
    result = archive([source], archive_dir=archive_dir, timestamp=_FIXED_TS)

    text = str(result)
    assert "Archive summary" in text
    assert ".env" in text


def test_archive_result_str_with_errors(tmp_path):
    missing = tmp_path / "ghost.env"
    result = archive([missing], archive_dir=tmp_path / "backups", timestamp=_FIXED_TS)

    text = str(result)
    assert "errors" in text.lower()
    assert "ERROR" in text


def test_archive_result_str_nothing_archived():
    result = ArchiveResult()
    assert str(result) == "Nothing archived."


def test_archive_entry_str():
    entry = ArchiveEntry(
        source=Path(".env"),
        destination=Path("backups/.env_20240615T120000.env"),
        timestamp=_FIXED_TS,
    )
    text = str(entry)
    assert "Archived" in text
    assert "2024-06-15" in text


def test_archive_default_dir_used_when_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = _write(tmp_path, ".env")
    result = archive([source], timestamp=_FIXED_TS)

    assert result.is_clean
    assert (tmp_path / ".env_archive").is_dir()
