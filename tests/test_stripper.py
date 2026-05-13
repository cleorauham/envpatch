"""Tests for envpatch.stripper."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.stripper import StripIssue, StripResult, strip


def _make_env(
    entries: list[tuple[str, str]] | None = None,
    raw_lines: list[str] | None = None,
) -> EnvFile:
    env_entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in (entries or [])
    ]
    obj = EnvFile(path=".env", entries=env_entries)
    obj.raw_lines = raw_lines or []
    return obj


# ---------------------------------------------------------------------------
# StripIssue
# ---------------------------------------------------------------------------

def test_strip_issue_str_blank():
    issue = StripIssue(line_number=3, original="", reason="blank")
    assert "Line 3" in str(issue)
    assert "blank" in str(issue)


def test_strip_issue_str_comment():
    issue = StripIssue(line_number=7, original="# hello", reason="comment")
    assert "Line 7" in str(issue)
    assert "comment" in str(issue)


# ---------------------------------------------------------------------------
# StripResult
# ---------------------------------------------------------------------------

def test_strip_result_is_clean_when_no_removals():
    result = StripResult(entries=[])
    assert result.is_clean() is True


def test_strip_result_not_clean_with_removals():
    issue = StripIssue(line_number=1, original="", reason="blank")
    result = StripResult(entries=[], removed=[issue])
    assert result.is_clean() is False


def test_strip_result_str_clean():
    result = StripResult(entries=[])
    assert "nothing to strip" in str(result)


def test_strip_result_str_with_removals():
    issues = [
        StripIssue(line_number=1, original="", reason="blank"),
        StripIssue(line_number=2, original="# comment", reason="comment"),
    ]
    result = StripResult(entries=[], removed=issues)
    text = str(result)
    assert "2 line(s) removed" in text
    assert "Line 1" in text
    assert "Line 2" in text


# ---------------------------------------------------------------------------
# strip()
# ---------------------------------------------------------------------------

def test_strip_no_blanks_or_comments():
    env = _make_env(
        entries=[("KEY", "value")],
        raw_lines=["KEY=value"],
    )
    result = strip(env)
    assert result.is_clean() is True
    assert len(result.entries) == 1


def test_strip_detects_blank_lines():
    env = _make_env(
        entries=[("A", "1")],
        raw_lines=["A=1", "", "   "],
    )
    result = strip(env)
    assert not result.is_clean()
    reasons = [i.reason for i in result.removed]
    assert reasons.count("blank") == 2


def test_strip_detects_comment_lines():
    env = _make_env(
        entries=[("B", "2")],
        raw_lines=["# top comment", "B=2", "# trailing comment"],
    )
    result = strip(env)
    assert not result.is_clean()
    assert len(result.removed) == 2
    assert all(i.reason == "comment" for i in result.removed)


def test_strip_mixed_lines():
    env = _make_env(
        entries=[("X", "10"), ("Y", "20")],
        raw_lines=["# section", "", "X=10", "Y=20"],
    )
    result = strip(env)
    assert len(result.removed) == 2
    assert len(result.entries) == 2


def test_strip_empty_file():
    env = _make_env(entries=[], raw_lines=[])
    result = strip(env)
    assert result.is_clean() is True
    assert result.entries == []
