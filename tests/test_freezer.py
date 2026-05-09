"""Tests for envpatch.freezer and envpatch.cli_freeze."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envpatch.freezer import (
    FreezeEntry,
    FreezeViolation,
    freeze,
    load_freeze,
    save_freeze,
    verify_freeze,
)
from envpatch.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_comment=False, is_blank=False)
        for k, v in pairs
    ]
    return EnvFile(entries=entries, source="test")


def _sha(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


# ---------------------------------------------------------------------------
# freeze()
# ---------------------------------------------------------------------------

def test_freeze_produces_one_entry_per_key():
    env = _make_env(("A", "1"), ("B", "2"))
    result = freeze(env)
    assert len(result.entries) == 2
    assert result.entries[0].key == "A"
    assert result.entries[1].key == "B"


def test_freeze_checksum_is_sha256_of_value():
    env = _make_env(("KEY", "secret"))
    result = freeze(env)
    assert result.entries[0].checksum == _sha("secret")


def test_freeze_result_is_clean_with_no_violations():
    env = _make_env(("X", "y"))
    result = freeze(env)
    assert result.is_clean()


def test_freeze_result_str_clean():
    env = _make_env(("X", "y"))
    result = freeze(env)
    assert "passed" in str(result)


# ---------------------------------------------------------------------------
# save_freeze / load_freeze
# ---------------------------------------------------------------------------

def test_save_and_load_freeze_roundtrip(tmp_path: Path):
    env = _make_env(("DB_URL", "postgres://localhost/db"), ("SECRET", "abc"))
    result = freeze(env)
    lock_path = tmp_path / ".env.lock"
    save_freeze(result, lock_path)
    loaded = load_freeze(lock_path)
    assert loaded["DB_URL"] == _sha("postgres://localhost/db")
    assert loaded["SECRET"] == _sha("abc")


# ---------------------------------------------------------------------------
# verify_freeze()
# ---------------------------------------------------------------------------

def test_verify_freeze_clean_when_unchanged():
    env = _make_env(("A", "1"), ("B", "2"))
    lock = {"A": _sha("1"), "B": _sha("2")}
    result = verify_freeze(env, lock)
    assert result.is_clean()


def test_verify_freeze_detects_modified_value():
    env = _make_env(("A", "changed"))
    lock = {"A": _sha("original")}
    result = verify_freeze(env, lock)
    assert not result.is_clean()
    assert any(v.reason == "modified" and v.key == "A" for v in result.violations)


def test_verify_freeze_detects_missing_key():
    env = _make_env(("B", "2"))
    lock = {"A": _sha("1"), "B": _sha("2")}
    result = verify_freeze(env, lock)
    assert any(v.reason == "missing" and v.key == "A" for v in result.violations)


def test_verify_freeze_detects_extra_key_by_default():
    env = _make_env(("A", "1"), ("NEW", "x"))
    lock = {"A": _sha("1")}
    result = verify_freeze(env, lock)
    assert any(v.reason == "extra" and v.key == "NEW" for v in result.violations)


def test_verify_freeze_allow_extra_suppresses_extra_violation():
    env = _make_env(("A", "1"), ("NEW", "x"))
    lock = {"A": _sha("1")}
    result = verify_freeze(env, lock, allow_extra=True)
    assert result.is_clean()


def test_verify_freeze_str_with_violations():
    env = _make_env(("A", "bad"))
    lock = {"A": _sha("good")}
    result = verify_freeze(env, lock)
    text = str(result)
    assert "MODIFIED" in text
    assert "A" in text


def test_freeze_entry_str_truncates_checksum():
    entry = FreezeEntry(key="MY_KEY", checksum="a" * 64)
    assert str(entry) == "MY_KEY=" + "a" * 12 + "..."


def test_freeze_violation_str():
    v = FreezeViolation(key="TOKEN", reason="missing")
    assert "MISSING" in str(v)
    assert "TOKEN" in str(v)
