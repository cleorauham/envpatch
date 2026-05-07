"""Tests for envpatch.profiler."""

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.profiler import (
    ProfileIssue,
    ProfileResult,
    check_profile,
    available_profiles,
)


def _make_env_file(pairs: dict) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_comment=False, is_blank=False)
        for k, v in pairs.items()
    ]
    return EnvFile(entries=entries, path=".env")


def test_profile_result_is_compliant_when_no_issues():
    result = ProfileResult(profile="production")
    assert result.is_compliant() is True


def test_profile_result_str_compliant():
    result = ProfileResult(profile="staging")
    assert "compliant" in str(result)


def test_profile_result_str_with_issues():
    result = ProfileResult(
        profile="production",
        issues=[ProfileIssue(key="SECRET_KEY", message="required key is missing", profile="production")],
    )
    text = str(result)
    assert "1 issue" in text
    assert "SECRET_KEY" in text


def test_check_profile_production_missing_keys():
    env = _make_env_file({"APP_NAME": "myapp"})
    result = check_profile(env, "production")
    assert not result.is_compliant()
    missing_keys = {i.key for i in result.issues}
    assert "DATABASE_URL" in missing_keys
    assert "SECRET_KEY" in missing_keys
    assert "ALLOWED_HOSTS" in missing_keys


def test_check_profile_production_all_present():
    env = _make_env_file({
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "supersecret",
        "ALLOWED_HOSTS": "example.com",
    })
    result = check_profile(env, "production")
    assert result.is_compliant()


def test_check_profile_empty_value_flagged():
    env = _make_env_file({
        "DATABASE_URL": "",
        "SECRET_KEY": "s3cr3t",
        "ALLOWED_HOSTS": "localhost",
    })
    result = check_profile(env, "production")
    assert not result.is_compliant()
    assert any(i.key == "DATABASE_URL" and "empty" in i.message for i in result.issues)


def test_check_profile_development_always_compliant():
    env = _make_env_file({})
    result = check_profile(env, "development")
    assert result.is_compliant()


def test_check_profile_custom_required_keys():
    env = _make_env_file({"FOO": "bar"})
    result = check_profile(env, "custom", required_keys={"FOO", "BAR"})
    assert not result.is_compliant()
    assert any(i.key == "BAR" for i in result.issues)
    assert all(i.key != "FOO" for i in result.issues)


def test_available_profiles_returns_builtins():
    profiles = available_profiles()
    assert "production" in profiles
    assert "staging" in profiles
    assert "development" in profiles


def test_profile_issue_str():
    issue = ProfileIssue(key="SECRET_KEY", message="required key is missing", profile="prod")
    assert "prod" in str(issue)
    assert "SECRET_KEY" in str(issue)
