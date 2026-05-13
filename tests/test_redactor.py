"""Tests for envpatch.redactor."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.redactor import (
    RedactResult,
    RedactedEntry,
    _REDACTED_PLACEHOLDER,
    redact,
)


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


def test_redact_non_sensitive_key_unchanged():
    env = _make_env(("APP_NAME", "myapp"))
    result = redact(env)
    assert result.entries[0].value == "myapp"
    assert not result.entries[0].redacted


def test_redact_secret_key_is_masked():
    env = _make_env(("DB_SECRET", "s3cr3t"))
    result = redact(env)
    assert result.entries[0].value == _REDACTED_PLACEHOLDER
    assert result.entries[0].redacted


def test_redact_password_key_is_masked():
    env = _make_env(("MYSQL_PASSWORD", "hunter2"))
    result = redact(env)
    assert result.entries[0].redacted


def test_redact_token_key_is_masked():
    env = _make_env(("GITHUB_TOKEN", "ghp_abc123"))
    result = redact(env)
    assert result.entries[0].redacted


def test_redact_api_key_is_masked():
    env = _make_env(("STRIPE_API_KEY", "sk_live_xyz"))
    result = redact(env)
    assert result.entries[0].redacted


def test_redact_mixed_file():
    env = _make_env(
        ("APP_ENV", "production"),
        ("SECRET_KEY", "abc"),
        ("PORT", "8080"),
        ("AUTH_TOKEN", "tok"),
    )
    result = redact(env)
    assert not result.entries[0].redacted  # APP_ENV
    assert result.entries[1].redacted      # SECRET_KEY
    assert not result.entries[2].redacted  # PORT
    assert result.entries[3].redacted      # AUTH_TOKEN


def test_redact_result_redacted_keys_list():
    env = _make_env(("SECRET", "x"), ("PLAIN", "y"), ("TOKEN", "z"))
    result = redact(env)
    assert result.redacted_keys == ["SECRET", "TOKEN"]


def test_redact_as_env_lines():
    env = _make_env(("APP", "hello"), ("PASSWORD", "secret"))
    lines = redact(env).as_env_lines()
    assert lines[0] == "APP=hello"
    assert lines[1] == f"PASSWORD={_REDACTED_PLACEHOLDER}"


def test_redact_str_output():
    env = _make_env(("NAME", "foo"), ("API_KEY", "bar"))
    out = str(redact(env))
    assert "NAME=foo" in out
    assert f"API_KEY={_REDACTED_PLACEHOLDER}" in out


def test_redact_extra_patterns():
    env = _make_env(("MY_CUSTOM_CERT", "pem-data"), ("PLAIN", "ok"))
    result = redact(env, extra_patterns={"CERT"})
    assert result.entries[0].redacted
    assert not result.entries[1].redacted


def test_redact_override_patterns_ignores_defaults():
    env = _make_env(("SECRET_KEY", "abc"), ("MY_MAGIC", "xyz"))
    # Only MAGIC is sensitive now; SECRET should NOT be redacted
    result = redact(env, patterns={"MAGIC"})
    assert not result.entries[0].redacted  # SECRET_KEY — not in override
    assert result.entries[1].redacted      # MY_MAGIC


def test_redact_empty_value_sensitive_key():
    """A sensitive key with an empty value should still be marked as redacted."""
    env = _make_env(("DB_PASSWORD", ""))
    result = redact(env)
    assert result.entries[0].redacted
    assert result.entries[0].value == _REDACTED_PLACEHOLDER


def test_redact_empty_file():
    """Redacting an empty EnvFile should return an empty result with no redacted keys."""
    env = EnvFile(entries=[], path=".env")
    result = redact(env)
    assert result.entries == []
    assert result.redacted_keys == []
