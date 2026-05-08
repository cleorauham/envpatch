"""Tests for envpatch.duplicates and envpatch.cli_duplicates."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from envpatch.duplicates import DuplicateIssue, DuplicateResult, find_duplicates
from envpatch.parser import EnvEntry, EnvFile


def _make_env(*entries) -> EnvFile:
    return EnvFile(path=".env", entries=list(entries))


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, raw_value=value, line_number=line)


# --- DuplicateIssue ---

def test_duplicate_issue_str():
    issue = DuplicateIssue(key="FOO", line_numbers=[2, 7])
    assert "FOO" in str(issue)
    assert "2" in str(issue)
    assert "7" in str(issue)


# --- DuplicateResult ---

def test_duplicate_result_is_clean_when_no_issues():
    result = DuplicateResult()
    assert result.is_clean() is True


def test_duplicate_result_not_clean_with_issues():
    result = DuplicateResult(issues=[DuplicateIssue("X", [1, 3])])
    assert result.is_clean() is False


def test_duplicate_result_str_clean():
    result = DuplicateResult()
    assert "No duplicate" in str(result)


def test_duplicate_result_str_with_issues():
    result = DuplicateResult(issues=[DuplicateIssue("DB_URL", [4, 10])])
    text = str(result)
    assert "DB_URL" in text
    assert "Duplicate keys detected" in text


# --- find_duplicates ---

def test_find_duplicates_no_duplicates():
    env = _make_env(_entry("A", line=1), _entry("B", line=2))
    result = find_duplicates(env)
    assert result.is_clean()


def test_find_duplicates_detects_duplicate():
    env = _make_env(_entry("FOO", line=1), _entry("BAR", line=2), _entry("FOO", line=5))
    result = find_duplicates(env)
    assert not result.is_clean()
    assert len(result.issues) == 1
    assert result.issues[0].key == "FOO"
    assert result.issues[0].line_numbers == [1, 5]


def test_find_duplicates_multiple_duplicate_keys():
    env = _make_env(
        _entry("X", line=1), _entry("X", line=2),
        _entry("Y", line=3), _entry("Y", line=4), _entry("Y", line=5),
    )
    result = find_duplicates(env)
    assert len(result.issues) == 2


def test_find_duplicates_skips_entries_without_key():
    comment = EnvEntry(key=None, raw_value=None, line_number=1)
    env = _make_env(comment, _entry("A", line=2))
    result = find_duplicates(env)
    assert result.is_clean()


# --- CLI ---

def test_run_duplicates_clean_returns_0(tmp_path):
    from envpatch.cli_duplicates import run_duplicates
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=bar\nBAZ=qux\n")
    args = MagicMock(file=str(env_path), strict=False)
    assert run_duplicates(args) == 0


def test_run_duplicates_strict_returns_1_on_duplicates(tmp_path):
    from envpatch.cli_duplicates import run_duplicates
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=bar\nFOO=baz\n")
    args = MagicMock(file=str(env_path), strict=True)
    assert run_duplicates(args) == 1


def test_run_duplicates_non_strict_returns_0_on_duplicates(tmp_path):
    from envpatch.cli_duplicates import run_duplicates
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=bar\nFOO=baz\n")
    args = MagicMock(file=str(env_path), strict=False)
    assert run_duplicates(args) == 0


def test_run_duplicates_missing_file_returns_2():
    from envpatch.cli_duplicates import run_duplicates
    args = MagicMock(file="/nonexistent/.env", strict=False)
    assert run_duplicates(args) == 2
