"""Tests for envpatch.renamer."""
from __future__ import annotations

from pathlib import Path

from envpatch.parser import EnvEntry, EnvFile
from envpatch.renamer import RenameIssue, RenameResult, rename


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=Path(".env"), entries=entries)


# ---------------------------------------------------------------------------
# RenameResult helpers
# ---------------------------------------------------------------------------

def test_rename_result_is_clean_when_no_issues():
    result = RenameResult(entries=[], issues=[], applied={})
    assert result.is_clean


def test_rename_result_not_clean_with_issues():
    result = RenameResult(entries=[], issues=[RenameIssue("OLD", "key not found")], applied={})
    assert not result.is_clean


def test_rename_result_str_clean():
    result = RenameResult(entries=[], issues=[], applied={"OLD": "NEW"})
    text = str(result)
    assert "1 rename(s)" in text
    assert "OLD->NEW" in text


def test_rename_result_str_with_issues():
    result = RenameResult(
        entries=[],
        issues=[RenameIssue("MISSING", "key not found in env file")],
        applied={},
    )
    text = str(result)
    assert "1 issue" in text
    assert "MISSING" in text


# ---------------------------------------------------------------------------
# rename() logic
# ---------------------------------------------------------------------------

def test_rename_single_key():
    env = _make_env(("OLD_KEY", "value"), ("OTHER", "x"))
    result = rename(env, {"OLD_KEY": "NEW_KEY"})
    assert result.is_clean
    keys = [e.key for e in result.entries]
    assert "NEW_KEY" in keys
    assert "OLD_KEY" not in keys
    assert result.applied == {"OLD_KEY": "NEW_KEY"}


def test_rename_preserves_value():
    env = _make_env(("FOO", "bar123"))
    result = rename(env, {"FOO": "BAZ"})
    assert result.is_clean
    entry = next(e for e in result.entries if e.key == "BAZ")
    assert entry.value == "bar123"


def test_rename_multiple_keys():
    env = _make_env(("A", "1"), ("B", "2"), ("C", "3"))
    result = rename(env, {"A": "X", "B": "Y"})
    assert result.is_clean
    keys = [e.key for e in result.entries]
    assert keys == ["X", "Y", "C"]


def test_rename_missing_key_creates_issue():
    env = _make_env(("PRESENT", "v"))
    result = rename(env, {"MISSING": "NEW"})
    assert not result.is_clean
    assert result.issues[0].old_key == "MISSING"
    assert "not found" in result.issues[0].reason


def test_rename_conflict_with_existing_key_creates_issue():
    env = _make_env(("A", "1"), ("B", "2"))
    result = rename(env, {"A": "B"})
    assert not result.is_clean
    assert result.issues[0].old_key == "A"
    assert "already exists" in result.issues[0].reason


def test_rename_no_changes_on_issue():
    """When issues exist, original entries are returned unchanged."""
    env = _make_env(("A", "1"))
    result = rename(env, {"MISSING": "NEW"})
    assert not result.is_clean
    assert result.applied == {}
    keys = [e.key for e in result.entries]
    assert keys == ["A"]


def test_rename_issue_str():
    issue = RenameIssue("OLD", "key not found in env file")
    assert "OLD" in str(issue)
    assert "key not found" in str(issue)
