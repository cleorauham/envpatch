"""Tests for envpatch.auditor."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.auditor import AuditIssue, AuditResult, audit


def _make_env_file(*entries: tuple) -> EnvFile:
    """Helper: build an EnvFile from (key, value) tuples."""
    env_entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", line_number=i + 1)
        for i, (k, v) in enumerate(entries)
    ]
    return EnvFile(entries=env_entries, path=None)


def test_audit_clean_file():
    env = _make_env_file(("APP_NAME", "myapp"), ("DEBUG", "false"))
    result = audit(env)
    assert result.is_clean
    assert str(result) == "Audit passed: no issues found."


def test_audit_sensitive_key_empty_value_is_error():
    env = _make_env_file(("API_KEY", ""), ("APP_NAME", "myapp"))
    result = audit(env)
    assert not result.is_clean
    errors = result.errors
    assert len(errors) == 1
    assert errors[0].key == "API_KEY"
    assert errors[0].severity == "error"
    assert "empty value" in errors[0].message


def test_audit_sensitive_key_placeholder_is_error():
    env = _make_env_file(("DB_PASSWORD", "changeme"))
    result = audit(env)
    errors = result.errors
    assert any(e.key == "DB_PASSWORD" for e in errors)
    assert any("placeholder" in e.message for e in errors)


def test_audit_non_sensitive_empty_value_is_warning():
    env = _make_env_file(("LOG_LEVEL", ""))
    result = audit(env)
    assert not result.is_clean
    warnings = result.warnings
    assert len(warnings) == 1
    assert warnings[0].key == "LOG_LEVEL"
    assert warnings[0].severity == "warning"


def test_audit_long_value_is_warning():
    long_value = "x" * 501
    env = _make_env_file(("SOME_CONFIG", long_value))
    result = audit(env)
    warnings = result.warnings
    assert any("unusually long" in w.message for w in warnings)


def test_audit_result_str_lists_all_issues():
    env = _make_env_file(
        ("SECRET_KEY", ""),
        ("PORT", ""),
    )
    result = audit(env)
    output = str(result)
    assert "SECRET_KEY" in output
    assert "PORT" in output


def test_audit_errors_and_warnings_properties():
    env = _make_env_file(
        ("AUTH_TOKEN", "placeholder"),  # error
        ("REGION", ""),                 # warning
    )
    result = audit(env)
    assert len(result.errors) >= 1
    assert len(result.warnings) >= 1


def test_audit_multiple_sensitive_placeholders():
    env = _make_env_file(
        ("DB_PASSWORD", "todo"),
        ("API_KEY", "fixme"),
    )
    result = audit(env)
    error_keys = {e.key for e in result.errors}
    assert "DB_PASSWORD" in error_keys
    assert "API_KEY" in error_keys
