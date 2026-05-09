"""Tests for envpatch.deprecator."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.deprecator import (
    DeprecationIssue,
    DeprecationResult,
    check_deprecations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env(*keys: str) -> EnvFile:
    entries = [EnvEntry(key=k, value="val", raw=f"{k}=val") for k in keys]
    return EnvFile(entries=entries, path=".env")


# ---------------------------------------------------------------------------
# DeprecationIssue
# ---------------------------------------------------------------------------

def test_deprecation_issue_str():
    issue = DeprecationIssue(key="SECRET_KEY_BASE", reason="Use APP_SECRET_KEY instead")
    assert "SECRET_KEY_BASE" in str(issue)
    assert "Use APP_SECRET_KEY instead" in str(issue)


# ---------------------------------------------------------------------------
# DeprecationResult
# ---------------------------------------------------------------------------

def test_deprecation_result_is_clean_when_no_issues():
    result = DeprecationResult(issues=[])
    assert result.is_clean() is True


def test_deprecation_result_not_clean_with_issues():
    result = DeprecationResult(issues=[DeprecationIssue(key="OLD", reason="replaced")])
    assert result.is_clean() is False


def test_deprecation_result_str_clean():
    result = DeprecationResult(issues=[])
    assert "No deprecated" in str(result)


def test_deprecation_result_str_with_issues():
    result = DeprecationResult(
        issues=[DeprecationIssue(key="SECRET_KEY_BASE", reason="Use APP_SECRET_KEY instead")]
    )
    text = str(result)
    assert "Deprecated keys detected" in text
    assert "SECRET_KEY_BASE" in text


# ---------------------------------------------------------------------------
# check_deprecations
# ---------------------------------------------------------------------------

def test_check_deprecations_clean_file():
    env = _make_env("APP_NAME", "PORT", "LOG_LEVEL")
    result = check_deprecations(env)
    assert result.is_clean()


def test_check_deprecations_builtin_hit():
    env = _make_env("APP_NAME", "SECRET_KEY_BASE")
    result = check_deprecations(env)
    assert not result.is_clean()
    assert any(i.key == "SECRET_KEY_BASE" for i in result.issues)


def test_check_deprecations_multiple_builtin_hits():
    env = _make_env("MAIL_HOST", "MAIL_PORT", "DATABASE_URL_OLD")
    result = check_deprecations(env)
    assert len(result.issues) == 3


def test_check_deprecations_extra_registry_extends_builtins():
    env = _make_env("LEGACY_API_KEY", "PORT")
    result = check_deprecations(env, extra_deprecated={"LEGACY_API_KEY": "Use API_KEY instead"})
    assert not result.is_clean()
    assert result.issues[0].key == "LEGACY_API_KEY"
    assert "API_KEY" in result.issues[0].reason


def test_check_deprecations_extra_registry_overrides_builtin_reason():
    env = _make_env("SECRET_KEY_BASE")
    custom_reason = "Custom override reason"
    result = check_deprecations(env, extra_deprecated={"SECRET_KEY_BASE": custom_reason})
    assert result.issues[0].reason == custom_reason


def test_check_deprecations_case_insensitive_key_match():
    env = _make_env("secret_key_base")  # lowercase
    result = check_deprecations(env)
    assert not result.is_clean()
    assert result.issues[0].key == "secret_key_base"
