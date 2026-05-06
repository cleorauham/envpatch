"""Tests for envpatch.parser and envpatch.differ."""

from __future__ import annotations

import pytest

from envpatch.differ import ChangeType, diff
from envpatch.parser import EnvFile, parse


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

BASIC_ENV = """
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret  # keep private
DEBUG=true
"""


def test_parse_basic_keys():
    env = parse(BASIC_ENV)
    d = env.as_dict()
    assert d["DB_HOST"] == "localhost"
    assert d["DB_PORT"] == "5432"
    assert d["DEBUG"] == "true"


def test_parse_strips_inline_comment():
    env = parse(BASIC_ENV)
    d = env.as_dict()
    assert d["SECRET_KEY"] == "supersecret"


def test_parse_ignores_blank_and_comment_lines():
    env = parse(BASIC_ENV)
    assert len(env.entries) == 4


def test_parse_quoted_value():
    env = parse('MSG="hello world # not a comment"')
    assert env.as_dict()["MSG"] == "hello world # not a comment"


def test_parse_single_quoted_value():
    env = parse("MSG='hello world'")
    assert env.as_dict()["MSG"] == "hello world"


def test_parse_empty_value():
    env = parse("EMPTY=")
    assert env.as_dict()["EMPTY"] == ""


# ---------------------------------------------------------------------------
# Differ tests
# ---------------------------------------------------------------------------

BASE_ENV = "A=1\nB=2\nC=3\n"
NEW_ENV = "A=1\nB=99\nD=4\n"


def test_diff_detects_unchanged():
    result = diff(parse(BASE_ENV), parse(NEW_ENV))
    unchanged = [e for e in result.entries if e.change == ChangeType.UNCHANGED]
    assert any(e.key == "A" for e in unchanged)


def test_diff_detects_modified():
    result = diff(parse(BASE_ENV), parse(NEW_ENV))
    modified = [e for e in result.entries if e.change == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].key == "B"
    assert modified[0].old_value == "2"
    assert modified[0].new_value == "99"


def test_diff_detects_removed():
    result = diff(parse(BASE_ENV), parse(NEW_ENV))
    removed = [e for e in result.entries if e.change == ChangeType.REMOVED]
    assert any(e.key == "C" for e in removed)


def test_diff_detects_added():
    result = diff(parse(BASE_ENV), parse(NEW_ENV))
    added = [e for e in result.entries if e.change == ChangeType.ADDED]
    assert any(e.key == "D" for e in added)


def test_diff_has_changes():
    assert diff(parse(BASE_ENV), parse(NEW_ENV)).has_changes


def test_diff_no_changes():
    result = diff(parse(BASE_ENV), parse(BASE_ENV))
    assert not result.has_changes


def test_diff_summary_format():
    result = diff(parse(BASE_ENV), parse(NEW_ENV))
    summary = result.summary()
    assert "added=1" in summary
    assert "removed=1" in summary
    assert "modified=1" in summary
