"""Tests for envpatch.validator."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger import MergeResult, MergeConflict
from envpatch.validator import (
    ValidationIssue,
    ValidationResult,
    validate_env_file,
    validate_merge_result,
)


def _make_env_file(*entries) -> EnvFile:
    return EnvFile(entries=list(entries))


def _entry(key, value="value", line=1):
    return EnvEntry(key=key, value=value, line_number=line, raw=f"{key}={value}")


# --- ValidationResult ---

def test_validation_result_is_valid_when_no_issues():
    vr = ValidationResult()
    assert vr.is_valid is True


def test_validation_result_str_no_issues():
    vr = ValidationResult()
    assert "No validation issues" in str(vr)


def test_validation_result_str_with_issues():
    vr = ValidationResult(issues=[ValidationIssue(line=3, key="BAD KEY", message="invalid")])
    assert "1 issue(s)" in str(vr)
    assert "BAD KEY" in str(vr)


# --- validate_env_file ---

def test_validate_valid_env_file():
    env = _make_env_file(_entry("APP_NAME", "myapp", 1), _entry("PORT", "8080", 2))
    result = validate_env_file(env)
    assert result.is_valid


def test_validate_invalid_key_with_space():
    env = _make_env_file(_entry("INVALID KEY", "val", 1))
    result = validate_env_file(env)
    assert not result.is_valid
    assert any("Invalid key name" in i.message for i in result.issues)


def test_validate_invalid_key_starts_with_digit():
    env = _make_env_file(_entry("1BAD", "val", 1))
    result = validate_env_file(env)
    assert not result.is_valid


def test_validate_duplicate_keys():
    env = _make_env_file(_entry("FOO", "a", 1), _entry("FOO", "b", 2))
    result = validate_env_file(env)
    assert not result.is_valid
    assert any("Duplicate key" in i.message for i in result.issues)


def test_validate_value_with_newline():
    entry = EnvEntry(key="BAD_VAL", value="line1\nline2", line_number=1, raw="BAD_VAL=line1\nline2")
    env = _make_env_file(entry)
    result = validate_env_file(env)
    assert not result.is_valid
    assert any("newline" in i.message for i in result.issues)


def test_validate_skips_none_key_entries():
    comment_entry = EnvEntry(key=None, value=None, line_number=1, raw="# comment")
    env = _make_env_file(comment_entry, _entry("GOOD_KEY", "ok", 2))
    result = validate_env_file(env)
    assert result.is_valid


# --- validate_merge_result ---

def test_validate_merge_result_no_conflicts():
    mr = MergeResult(entries={"KEY": "value"}, conflicts=[])
    result = validate_merge_result(mr)
    assert result.is_valid


def test_validate_merge_result_with_conflicts():
    conflict = MergeConflict(key="DB_URL", base_value="old", incoming_value="new")
    mr = MergeResult(entries={}, conflicts=[conflict])
    result = validate_merge_result(mr)
    assert not result.is_valid
    assert any("DB_URL" in i.key for i in result.issues)
    assert any("Unresolved conflict" in i.message for i in result.issues)
