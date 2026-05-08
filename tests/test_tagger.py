"""Tests for envpatch.tagger."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.tagger import TagResult, tag_entries


def _make_env(*keys: str) -> EnvFile:
    entries = [EnvEntry(key=k, value="val", raw=f"{k}=val") for k in keys]
    return EnvFile(entries=entries, path=".env")


# ---------------------------------------------------------------------------
# TagResult helpers
# ---------------------------------------------------------------------------

def test_tag_result_is_clean_when_no_issues():
    result = TagResult(tagged={"KEY": frozenset({"infra"})}, issues=[])
    assert result.is_clean()


def test_tag_result_not_clean_with_issues():
    from envpatch.tagger import TagIssue
    result = TagResult(issues=[TagIssue(key="X", message="missing")])
    assert not result.is_clean()


def test_tag_result_tags_for_known_key():
    result = TagResult(tagged={"DB_URL": frozenset({"database", "secret"})})
    assert result.tags_for("DB_URL") == frozenset({"database", "secret"})


def test_tag_result_tags_for_unknown_key_returns_empty():
    result = TagResult(tagged={})
    assert result.tags_for("MISSING") == frozenset()


def test_tag_result_keys_with_tag():
    result = TagResult(
        tagged={
            "DB_URL": frozenset({"database"}),
            "REDIS_URL": frozenset({"database", "cache"}),
            "SECRET_KEY": frozenset({"secret"}),
        }
    )
    assert sorted(result.keys_with_tag("database")) == ["DB_URL", "REDIS_URL"]
    assert result.keys_with_tag("cache") == ["REDIS_URL"]
    assert result.keys_with_tag("nonexistent") == []


def test_tag_result_str_empty():
    result = TagResult(tagged={})
    assert "No tagged" in str(result)


def test_tag_result_str_shows_keys_and_tags():
    result = TagResult(tagged={"API_KEY": frozenset({"secret"})})
    output = str(result)
    assert "API_KEY" in output
    assert "secret" in output


# ---------------------------------------------------------------------------
# tag_entries
# ---------------------------------------------------------------------------

def test_tag_entries_basic():
    env = _make_env("DB_URL", "API_KEY", "DEBUG")
    result = tag_entries(env, {"infra": ["DB_URL"], "secret": ["API_KEY"]})
    assert result.is_clean()
    assert "infra" in result.tags_for("DB_URL")
    assert "secret" in result.tags_for("API_KEY")
    assert result.tags_for("DEBUG") == frozenset()


def test_tag_entries_multiple_tags_on_same_key():
    env = _make_env("DB_PASSWORD")
    result = tag_entries(env, {"secret": ["DB_PASSWORD"], "database": ["DB_PASSWORD"]})
    assert result.tags_for("DB_PASSWORD") == frozenset({"secret", "database"})


def test_tag_entries_strict_missing_key_creates_issue():
    env = _make_env("EXISTING")
    result = tag_entries(env, {"infra": ["MISSING_KEY"]}, strict=True)
    assert not result.is_clean()
    assert any("MISSING_KEY" in str(i) for i in result.issues)


def test_tag_entries_non_strict_missing_key_still_tagged():
    env = _make_env("EXISTING")
    result = tag_entries(env, {"infra": ["GHOST_KEY"]}, strict=False)
    assert result.is_clean()
    assert "infra" in result.tags_for("GHOST_KEY")


def test_tag_entries_invalid_tag_value_creates_issue():
    env = _make_env("KEY")
    # tag_map value is not a list
    result = tag_entries(env, {"bad_tag": "KEY"})  # type: ignore[arg-type]
    assert not result.is_clean()
    assert any("bad_tag" in str(i) for i in result.issues)
