"""Tests for envpatch.transformer."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.transformer import TransformIssue, TransformResult, transform


def _make_env(*pairs: tuple) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


def test_transform_result_is_clean_when_no_issues():
    result = TransformResult()
    assert result.is_clean()


def test_transform_result_not_clean_with_issues():
    result = TransformResult(issues=[TransformIssue("*", "bad")])
    assert not result.is_clean()


def test_transform_result_str_clean():
    assert "no issues" in str(TransformResult())


def test_transform_result_str_with_issues():
    result = TransformResult(issues=[TransformIssue("KEY", "Unknown transform: 'x'")])
    assert "KEY" in str(result)
    assert "Unknown transform" in str(result)


def test_transform_strip_values():
    env = _make_env(("A", "  hello  "), ("B", "world"))
    result = transform(env, ["strip_values"])
    assert result.is_clean()
    values = {e.key: e.value for e in result.entries}
    assert values["A"] == "hello"
    assert values["B"] == "world"


def test_transform_uppercase_keys():
    env = _make_env(("app_host", "localhost"), ("db_port", "5432"))
    result = transform(env, ["uppercase_keys"])
    keys = [e.key for e in result.entries]
    assert "APP_HOST" in keys
    assert "DB_PORT" in keys


def test_transform_uppercase_values():
    env = _make_env(("ENV", "production"))
    result = transform(env, ["uppercase_values"])
    assert result.entries[0].value == "PRODUCTION"


def test_transform_lowercase_values():
    env = _make_env(("ENV", "STAGING"))
    result = transform(env, ["lowercase_values"])
    assert result.entries[0].value == "staging"


def test_transform_quote_values_adds_quotes():
    env = _make_env(("HOST", "localhost"))
    result = transform(env, ["quote_values"])
    assert result.entries[0].value == '"localhost"'


def test_transform_quote_values_skips_already_quoted():
    env = _make_env(("HOST", '"already"'))
    result = transform(env, ["quote_values"])
    assert result.entries[0].value == '"already"'


def test_transform_unquote_values():
    env = _make_env(("HOST", '"localhost"'))
    result = transform(env, ["unquote_values"])
    assert result.entries[0].value == "localhost"


def test_transform_unknown_name_creates_issue():
    env = _make_env(("A", "1"))
    result = transform(env, ["nonexistent_transform"])
    assert not result.is_clean()
    assert any("nonexistent_transform" in str(i) for i in result.issues)


def test_transform_multiple_transforms_applied_in_order():
    env = _make_env(("host", "  LOCALHOST  "))
    result = transform(env, ["uppercase_keys", "strip_values", "lowercase_values"])
    entry = result.entries[0]
    assert entry.key == "HOST"
    assert entry.value == "localhost"


def test_transform_preserves_non_kv_entries():
    from envpatch.parser import EnvEntry
    blank = EnvEntry(key=None, value=None, comment="# comment", raw="# comment")
    env = EnvFile(entries=[blank], path=".env")
    result = transform(env, ["strip_values"])
    assert result.entries[0].key is None
