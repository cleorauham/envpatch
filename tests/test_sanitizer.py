"""Tests for envpatch.sanitizer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sanitizer import SanitizeIssue, SanitizeResult, sanitize


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(entries=entries, path=".env")


def test_sanitize_clean_file_has_no_issues():
    env = _make_env(("FOO", "bar"), ("BAZ", "123"))
    result = sanitize(env)
    assert result.is_clean()
    assert result.issues == []


def test_sanitize_removes_null_bytes():
    env = _make_env(("KEY", "val\x00ue"))
    result = sanitize(env)
    assert not result.is_clean()
    assert len(result.issues) == 1
    assert result.issues[0].key == "KEY"
    assert "null bytes" in result.issues[0].reason
    assert result.entries[0].value == "value"


def test_sanitize_removes_control_characters():
    env = _make_env(("KEY", "val\x01ue"))
    result = sanitize(env)
    assert not result.is_clean()
    assert result.entries[0].value == "value"
    assert "control characters" in result.issues[0].reason


def test_sanitize_preserves_tab_and_newline():
    env = _make_env(("KEY", "line1\tline2"))
    result = sanitize(env)
    assert result.is_clean()
    assert result.entries[0].value == "line1\tline2"


def test_sanitize_issue_str():
    issue = SanitizeIssue(key="FOO", original="ba\x00r", sanitized="bar", reason="null bytes removed")
    assert "FOO" in str(issue)
    assert "null bytes removed" in str(issue)


def test_sanitize_result_str_clean():
    result = SanitizeResult(entries=[], issues=[])
    assert "no issues" in str(result)


def test_sanitize_result_str_with_issues():
    issue = SanitizeIssue(key="A", original="\x01", sanitized="", reason="control characters removed")
    result = SanitizeResult(entries=[], issues=[issue])
    text = str(result)
    assert "Sanitize issues" in text
    assert "A" in text


def test_sanitize_preserves_entry_key_and_comment():
    entry = EnvEntry(key="MY_KEY", value="ok\x00", comment="# note", raw="MY_KEY=ok\x00 # note")
    env = EnvFile(entries=[entry], path=".env")
    result = sanitize(env)
    assert result.entries[0].key == "MY_KEY"
    assert result.entries[0].comment == "# note"


def test_sanitize_multiple_issues_on_different_keys():
    env = _make_env(("A", "\x00"), ("B", "\x02"), ("C", "clean"))
    result = sanitize(env)
    assert not result.is_clean()
    issue_keys = {i.key for i in result.issues}
    assert "A" in issue_keys
    assert "B" in issue_keys
    assert "C" not in issue_keys
