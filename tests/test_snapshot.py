"""Tests for envpatch.snapshot."""

import json
import os
import tempfile

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.snapshot import (
    Snapshot,
    capture,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_env_file(pairs: dict, path: str = ".env") -> EnvFile:
    entries = [
        EnvEntry(key=k, raw_value=v, comment=None, original_line=f"{k}={v}")
        for k, v in pairs.items()
    ]
    return EnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------

def test_capture_stores_entries():
    env = _make_env_file({"FOO": "bar", "BAZ": "qux"})
    snap = capture(env, source="test.env")
    assert snap.entries == {"FOO": "bar", "BAZ": "qux"}
    assert snap.source == "test.env"


def test_capture_uses_env_path_as_default_source():
    env = _make_env_file({"A": "1"}, path="/project/.env")
    snap = capture(env)
    assert snap.source == "/project/.env"


def test_capture_records_timestamp():
    env = _make_env_file({"X": "y"})
    snap = capture(env, source="x")
    # ISO-8601 with timezone offset
    assert "+" in snap.captured_at or snap.captured_at.endswith("Z") or "UTC" in snap.captured_at or snap.captured_at.endswith("+00:00")


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_snapshot_roundtrip():
    env = _make_env_file({"DB_HOST": "localhost", "PORT": "5432"})
    snap = capture(env, source="prod.env")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        save_snapshot(snap, tmp_path)
        loaded = load_snapshot(tmp_path)
        assert loaded.source == snap.source
        assert loaded.captured_at == snap.captured_at
        assert loaded.entries == snap.entries
    finally:
        os.unlink(tmp_path)


def test_save_snapshot_produces_valid_json():
    env = _make_env_file({"KEY": "value"})
    snap = capture(env, source="test")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        save_snapshot(snap, tmp_path)
        with open(tmp_path) as fh:
            data = json.load(fh)
        assert "entries" in data
        assert data["entries"]["KEY"] == "value"
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_snapshots_detects_added_key():
    old = Snapshot(source="a", captured_at="t1", entries={"A": "1"})
    new = Snapshot(source="b", captured_at="t2", entries={"A": "1", "B": "2"})
    changes = diff_snapshots(old, new)
    assert "B" in changes
    assert changes["B"] == {"old": None, "new": "2"}


def test_diff_snapshots_detects_removed_key():
    old = Snapshot(source="a", captured_at="t1", entries={"A": "1", "B": "2"})
    new = Snapshot(source="b", captured_at="t2", entries={"A": "1"})
    changes = diff_snapshots(old, new)
    assert "B" in changes
    assert changes["B"] == {"old": "2", "new": None}


def test_diff_snapshots_detects_modified_value():
    old = Snapshot(source="a", captured_at="t1", entries={"HOST": "localhost"})
    new = Snapshot(source="b", captured_at="t2", entries={"HOST": "prod.example.com"})
    changes = diff_snapshots(old, new)
    assert changes["HOST"]["old"] == "localhost"
    assert changes["HOST"]["new"] == "prod.example.com"


def test_diff_snapshots_empty_when_identical():
    entries = {"A": "1", "B": "2"}
    old = Snapshot(source="a", captured_at="t1", entries=entries)
    new = Snapshot(source="b", captured_at="t2", entries=entries)
    assert diff_snapshots(old, new) == {}
