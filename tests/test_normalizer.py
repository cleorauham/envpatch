"""Tests for envpatch.normalizer."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.normalizer import NormalizeIssue, NormalizeResult, normalize, _normalize_key, _normalize_value


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, comment=None) for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


# --- unit helpers ---

def test_normalize_key_uppercases():
    assert _normalize_key("db_host") == "DB_HOST"


def test_normalize_key_strips_whitespace():
    assert _normalize_key("  KEY  ") == "KEY"


def test_normalize_value_strips_whitespace():
    assert _normalize_value("  hello  ") == "hello"


def test_normalize_value_removes_unnecessary_double_quotes():
    assert _normalize_value('"simple"') == "simple"


def test_normalize_value_removes_unnecessary_single_quotes():
    assert _normalize_value("'simple'") == "simple"


def test_normalize_value_keeps_quotes_when_spaces_inside():
    assert _normalize_value('"hello world"') == '"hello world"'


def test_normalize_value_keeps_quotes_when_hash_inside():
    assert _normalize_value('"val#ue"') == '"val#ue"'


# --- NormalizeResult ---

def test_normalize_result_is_clean_when_no_issues():
    result = NormalizeResult(entries=[], issues=[])
    assert result.is_clean() is True


def test_normalize_result_not_clean_with_issues():
    issue = NormalizeIssue(key="k", original="k=v", normalized="K=v", reason="key uppercased/trimmed")
    result = NormalizeResult(entries=[], issues=[issue])
    assert result.is_clean() is False


def test_normalize_result_str_clean():
    result = NormalizeResult()
    assert str(result) == "No normalization changes."


def test_normalize_result_str_with_issues():
    issue = NormalizeIssue(key="db", original="db=val", normalized="DB=val", reason="key uppercased/trimmed")
    result = NormalizeResult(issues=[issue])
    output = str(result)
    assert "Normalization changes" in output
    assert "db" in output


# --- normalize() integration ---

def test_normalize_clean_env_produces_no_issues():
    env = _make_env(("DB_HOST", "localhost"), ("PORT", "5432"))
    result = normalize(env)
    assert result.is_clean()
    assert len(result.entries) == 2


def test_normalize_lowercased_key_creates_issue():
    env = _make_env(("db_host", "localhost"))
    result = normalize(env)
    assert not result.is_clean()
    assert result.issues[0].key == "db_host"
    assert result.entries[0].key == "DB_HOST"


def test_normalize_quoted_value_creates_issue():
    env = _make_env(("API_KEY", '"mytoken"'))
    result = normalize(env)
    assert not result.is_clean()
    assert result.entries[0].value == "mytoken"


def test_normalize_preserves_entry_count():
    env = _make_env(("a", "1"), ("b", "2"), ("c", "3"))
    result = normalize(env)
    assert len(result.entries) == 3


def test_normalize_issue_str_format():
    issue = NormalizeIssue(key="x", original="x=y", normalized="X=y", reason="key uppercased/trimmed")
    assert "->" in str(issue)
    assert "key uppercased" in str(issue)
