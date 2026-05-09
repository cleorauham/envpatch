"""Tests for envpatch.pinner."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.pinner import (
    PinEntry,
    PinResult,
    _checksum,
    compare_pin,
    load_pin,
    pin,
    save_pin,
)


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, source="test.env")


def test_checksum_is_sha256_of_value():
    expected = hashlib.sha256(b"hello").hexdigest()
    assert _checksum("hello") == expected


def test_pin_entry_str_truncates_checksum():
    entry = PinEntry(key="FOO", checksum="a" * 64)
    assert str(entry) == "FOO=" + "a" * 12 + "..."


def test_pin_creates_entry_per_key():
    env = _make_env(("FOO", "bar"), ("BAZ", "qux"))
    result = pin(env)
    assert len(result.entries) == 2
    keys = [e.key for e in result.entries]
    assert "FOO" in keys and "BAZ" in keys


def test_pin_result_is_clean_when_no_drift():
    result = PinResult()
    assert result.is_clean() is True


def test_pin_result_not_clean_with_drifted():
    result = PinResult(drifted=["FOO"])
    assert result.is_clean() is False


def test_pin_result_str_clean():
    result = PinResult()
    assert "no drift" in str(result)


def test_pin_result_str_with_changes():
    result = PinResult(drifted=["A"], missing=["B"], added=["C"])
    text = str(result)
    assert "~ A" in text
    assert "- B" in text
    assert "+ C" in text


def test_compare_pin_detects_drift():
    env = _make_env(("FOO", "newvalue"))
    old_checksum = _checksum("oldvalue")
    lock = {"FOO": old_checksum}
    result = compare_pin(env, lock)
    assert "FOO" in result.drifted


def test_compare_pin_detects_missing_key():
    env = _make_env(("FOO", "bar"))
    lock = {"FOO": _checksum("bar"), "GONE": _checksum("x")}
    result = compare_pin(env, lock)
    assert "GONE" in result.missing


def test_compare_pin_detects_added_key():
    env = _make_env(("FOO", "bar"), ("NEW", "val"))
    lock = {"FOO": _checksum("bar")}
    result = compare_pin(env, lock)
    assert "NEW" in result.added


def test_compare_pin_clean_when_identical():
    env = _make_env(("FOO", "bar"))
    lock = {"FOO": _checksum("bar")}
    result = compare_pin(env, lock)
    assert result.is_clean()


def test_save_and_load_pin_roundtrip(tmp_path: Path):
    env = _make_env(("KEY1", "val1"), ("KEY2", "val2"))
    result = pin(env)
    lock_path = tmp_path / ".env.lock"
    save_pin(result, lock_path)
    loaded = load_pin(lock_path)
    assert loaded["KEY1"] == _checksum("val1")
    assert loaded["KEY2"] == _checksum("val2")


def test_load_pin_returns_empty_dict_for_missing_file(tmp_path: Path):
    result = load_pin(tmp_path / "nonexistent.lock")
    assert result == {}
