"""Tests for envpatch.patcher."""
from __future__ import annotations

import pytest

from envpatch.differ import ChangeType, DiffEntry, DiffResult
from envpatch.parser import EnvEntry, EnvFile
from envpatch.patcher import patch, PatchResult


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(path=".env", entries=entries)


def _make_diff(*changes: DiffEntry) -> DiffResult:
    return DiffResult(changes=list(changes))


def _change(change_type: ChangeType, key: str, old=None, new=None) -> DiffEntry:
    return DiffEntry(change_type=change_type, key=key, old_value=old, new_value=new)


def test_patch_adds_new_key():
    target = _make_env(("A", "1"))
    d = _make_diff(_change(ChangeType.ADDED, "B", new="2"))
    result = patch(target, d)
    keys = {e.key for e in result.patched.entries}
    assert "B" in keys
    assert result.is_clean


def test_patch_removes_existing_key():
    target = _make_env(("A", "1"), ("B", "2"))
    d = _make_diff(_change(ChangeType.REMOVED, "B", old="2"))
    result = patch(target, d)
    keys = {e.key for e in result.patched.entries}
    assert "B" not in keys
    assert result.is_clean


def test_patch_modifies_existing_key():
    target = _make_env(("A", "old"))
    d = _make_diff(_change(ChangeType.MODIFIED, "A", old="old", new="new"))
    result = patch(target, d)
    entry = next(e for e in result.patched.entries if e.key == "A")
    assert entry.value == "new"
    assert result.is_clean


def test_patch_unchanged_key_preserved():
    target = _make_env(("A", "1"), ("B", "2"))
    d = _make_diff(_change(ChangeType.UNCHANGED, "A", old="1", new="1"))
    result = patch(target, d)
    keys = {e.key for e in result.patched.entries}
    assert "A" in keys
    assert "B" in keys


def test_patch_remove_missing_key_records_issue():
    target = _make_env(("A", "1"))
    d = _make_diff(_change(ChangeType.REMOVED, "GHOST", old="x"))
    result = patch(target, d)
    assert not result.is_clean
    assert any("GHOST" in str(i) for i in result.issues)


def test_patch_remove_missing_key_skip_missing_no_issue():
    target = _make_env(("A", "1"))
    d = _make_diff(_change(ChangeType.REMOVED, "GHOST", old="x"))
    result = patch(target, d, skip_missing=True)
    assert result.is_clean


def test_patch_add_existing_key_records_issue_and_overwrites():
    target = _make_env(("A", "old"))
    d = _make_diff(_change(ChangeType.ADDED, "A", new="new"))
    result = patch(target, d)
    assert not result.is_clean
    entry = next(e for e in result.patched.entries if e.key == "A")
    assert entry.value == "new"


def test_patch_result_str_clean():
    target = _make_env(("A", "1"))
    d = _make_diff()
    result = patch(target, d)
    assert "cleanly" in str(result)


def test_patch_result_str_with_issues():
    target = _make_env(("A", "1"))
    d = _make_diff(_change(ChangeType.REMOVED, "GHOST", old="x"))
    result = patch(target, d)
    text = str(result)
    assert "issues" in text.lower()
    assert "GHOST" in text
