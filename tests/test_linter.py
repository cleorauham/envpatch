"""Tests for envpatch.linter."""
from __future__ import annotations

import pytest

from envpatch.linter import LintIssue, LintResult, LintSeverity, lint
from envpatch.parser import EnvEntry, EnvFile


def _make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw_lines=[])


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=line)


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

def test_lint_result_is_clean_when_no_issues():
    result = LintResult()
    assert result.is_clean is True


def test_lint_result_not_clean_when_errors():
    issue = LintIssue(key="BAD", message="oops", severity=LintSeverity.ERROR)
    result = LintResult(issues=[issue])
    assert result.is_clean is False


def test_lint_result_clean_with_only_warnings():
    issue = LintIssue(key="low", message="style", severity=LintSeverity.WARNING)
    result = LintResult(issues=[issue])
    assert result.is_clean is True


def test_lint_result_str_no_issues():
    result = LintResult()
    assert "no issues" in str(result)


def test_lint_result_str_with_issues():
    issue = LintIssue(key="FOO", message="bad", severity=LintSeverity.ERROR, line=3)
    result = LintResult(issues=[issue])
    output = str(result)
    assert "ERROR" in output
    assert "FOO" in output
    assert "line 3" in output


# ---------------------------------------------------------------------------
# lint() checks
# ---------------------------------------------------------------------------

def test_lint_clean_file():
    env = _make_env(_entry("DATABASE_URL", "postgres://localhost/db", 1))
    result = lint(env)
    assert result.is_clean
    assert result.issues == []


def test_lint_warns_on_lowercase_key():
    env = _make_env(_entry("db_host", "localhost", 1))
    result = lint(env)
    warnings = result.warnings
    assert any("UPPER_SNAKE_CASE" in w.message for w in warnings)


def test_lint_error_on_duplicate_key():
    env = _make_env(
        _entry("API_KEY", "abc", 1),
        _entry("API_KEY", "xyz", 2),
    )
    result = lint(env)
    errors = result.errors
    assert any("duplicate" in e.message for e in errors)
    assert not result.is_clean


def test_lint_error_on_key_starting_with_digit():
    env = _make_env(_entry("1BAD_KEY", "value", 1))
    result = lint(env)
    errors = result.errors
    assert any("digit" in e.message for e in errors)


def test_lint_warns_on_very_long_value():
    long_value = "x" * 600
    env = _make_env(_entry("BIG_VALUE", long_value, 1))
    result = lint(env)
    warnings = result.warnings
    assert any("unusually long" in w.message for w in warnings)


def test_lint_skips_entries_without_key():
    entry = EnvEntry(key=None, value=None, comment="# just a comment", line_number=1)
    env = _make_env(entry)
    result = lint(env)
    assert result.issues == []


def test_lint_multiple_issues_accumulate():
    env = _make_env(
        _entry("lower_key", "v", 1),
        _entry("lower_key", "v2", 2),
    )
    result = lint(env)
    assert len(result.issues) >= 2
