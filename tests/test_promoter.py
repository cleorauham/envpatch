"""Tests for envpatch.promoter."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.promoter import PromoteIssue, PromoteResult, promote


def _make_env(*pairs: tuple) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", line_number=i + 1)
        for i, (k, v) in enumerate(pairs)
    ]
    return EnvFile(entries=entries, path=None)


def test_promote_adds_new_key():
    source = _make_env(("NEW_KEY", "hello"))
    target = _make_env(("EXISTING", "world"))
    result = promote(source, target)
    assert result.promoted["NEW_KEY"] == "hello"
    assert result.promoted["EXISTING"] == "world"


def test_promote_skips_existing_key_by_default():
    source = _make_env(("KEY", "from_source"))
    target = _make_env(("KEY", "from_target"))
    result = promote(source, target)
    assert result.promoted["KEY"] == "from_target"
    assert len(result.issues) == 1
    assert "skipped" in result.issues[0].reason


def test_promote_overwrites_when_flag_set():
    source = _make_env(("KEY", "new_value"))
    target = _make_env(("KEY", "old_value"))
    result = promote(source, target, overwrite=True)
    assert result.promoted["KEY"] == "new_value"
    assert result.issues[0].overwritten is True


def test_promote_specific_keys_only():
    source = _make_env(("A", "1"), ("B", "2"), ("C", "3"))
    target = _make_env()
    result = promote(source, target, keys=["A", "C"])
    assert "A" in result.promoted
    assert "C" in result.promoted
    assert "B" not in result.promoted


def test_promote_excludes_keys():
    source = _make_env(("A", "1"), ("B", "2"))
    target = _make_env()
    result = promote(source, target, exclude=["B"])
    assert "A" in result.promoted
    assert "B" not in result.promoted


def test_promote_missing_key_in_source_creates_issue():
    source = _make_env(("A", "1"))
    target = _make_env()
    result = promote(source, target, keys=["A", "MISSING"])
    keys_with_issues = [i.key for i in result.issues]
    assert "MISSING" in keys_with_issues


def test_promote_result_is_clean_no_overwrites():
    source = _make_env(("FRESH", "value"))
    target = _make_env()
    result = promote(source, target)
    assert result.is_clean()


def test_promote_result_not_clean_with_overwrite():
    source = _make_env(("KEY", "v"))
    target = _make_env(("KEY", "old"))
    result = promote(source, target, overwrite=True)
    assert not result.is_clean()


def test_promote_result_str_no_issues():
    source = _make_env(("X", "1"))
    target = _make_env()
    result = promote(source, target)
    assert "no conflicts" in str(result)


def test_promote_result_str_with_issues():
    source = _make_env(("KEY", "v"))
    target = _make_env(("KEY", "old"))
    result = promote(source, target, overwrite=True)
    output = str(result)
    assert "KEY" in output
    assert "OVERWRITTEN" in output


def test_promote_issue_str_skipped():
    issue = PromoteIssue(key="FOO", reason="already exists in target; skipped", overwritten=False)
    assert "SKIPPED" in str(issue)
    assert "FOO" in str(issue)


def test_promote_issue_str_overwritten():
    issue = PromoteIssue(key="BAR", reason="existed in target; overwritten", overwritten=True)
    assert "OVERWRITTEN" in str(issue)
    assert "BAR" in str(issue)
