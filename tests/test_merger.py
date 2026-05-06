"""Tests for envpatch.merger."""

import pytest

from envpatch.differ import diff
from envpatch.merger import merge
from envpatch.parser import parse


BASE_ENV = """\
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=old-secret
DEBUG=true
"""

INCOMING_ENV = """\
DB_HOST=localhost
DB_PORT=5433
SECRET_KEY=old-secret
NEW_FEATURE_FLAG=enabled
"""


def _make_diff(base_src: str, incoming_src: str):
    base = parse(base_src)
    incoming = parse(incoming_src)
    return base, diff(base, incoming)


def test_merge_adds_new_key():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["NEW_FEATURE_FLAG"] == "enabled"


def test_merge_marks_removed_key():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    keys = [e.key for e in result.merged.entries if e.key]
    assert "DEBUG" not in keys
    raw_lines = [e.raw_line for e in result.merged.entries]
    assert any("REMOVED" in line and "DEBUG" in line for line in raw_lines)


def test_merge_conflict_on_modified_without_overwrite():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    assert result.has_conflicts
    conflict_keys = [c.key for c in result.conflicts]
    assert "DB_PORT" in conflict_keys


def test_merge_no_conflict_when_overwrite_enabled():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d, overwrite_existing=True)
    assert not result.has_conflicts
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["DB_PORT"] == "5433"


def test_merge_unchanged_keys_preserved():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["DB_HOST"] == "localhost"
    assert merged_dict["SECRET_KEY"] == "old-secret"


def test_merge_no_changes_returns_same_content():
    base = parse(BASE_ENV)
    d = diff(base, base)
    result = merge(base, d)
    assert not result.has_conflicts
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    base_dict = {e.key: e.value for e in base.entries if e.key}
    assert merged_dict == base_dict


def test_merge_result_str_contains_added_key():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    output = str(result)
    assert "NEW_FEATURE_FLAG=enabled" in output


def test_merge_conflict_message_includes_values():
    base, d = _make_diff(BASE_ENV, INCOMING_ENV)
    result = merge(base, d)
    port_conflict = next(c for c in result.conflicts if c.key == "DB_PORT")
    assert "5432" in port_conflict.message
    assert "5433" in port_conflict.message
