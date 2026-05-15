"""Tests for envpatch.splitter."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.splitter import SplitIssue, SplitResult, split_by_prefix


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


def test_split_result_is_clean_when_no_issues():
    result = SplitResult(groups={"db": []}, issues=[])
    assert result.is_clean()


def test_split_result_not_clean_with_issues():
    result = SplitResult(groups={}, issues=[SplitIssue("KEY", "empty prefix")])
    assert not result.is_clean()


def test_split_result_str_clean():
    result = SplitResult(groups={"db": [_make_env(("DB_HOST", "localhost")).entries[0]]}, issues=[])
    text = str(result)
    assert "Split into 1 group" in text
    assert "db" in text


def test_split_result_str_with_issues():
    result = SplitResult(groups={}, issues=[SplitIssue("_BAD", "empty prefix after split")])
    text = str(result)
    assert "Split issues" in text
    assert "_BAD" in text


def test_split_issue_str():
    issue = SplitIssue("MY_KEY", "some reason")
    assert str(issue) == "MY_KEY: some reason"


def test_split_by_prefix_basic():
    env = _make_env(("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("APP_NAME", "myapp"))
    result = split_by_prefix(env)
    assert "db" in result.groups
    assert "app" in result.groups
    assert len(result.groups["db"]) == 2
    assert len(result.groups["app"]) == 1


def test_split_by_prefix_no_delimiter_goes_to_misc():
    env = _make_env(("PORT", "8080"), ("HOST", "0.0.0.0"))
    result = split_by_prefix(env)
    assert "misc" in result.groups
    assert len(result.groups["misc"]) == 2


def test_split_by_prefix_custom_default_group():
    env = _make_env(("PORT", "8080"))
    result = split_by_prefix(env, default_group="general")
    assert "general" in result.groups


def test_split_by_prefix_custom_delimiter():
    env = _make_env(("DB.HOST", "localhost"), ("DB.PORT", "5432"))
    result = split_by_prefix(env, delimiter=".")
    assert "db" in result.groups
    assert len(result.groups["db"]) == 2


def test_split_by_prefix_include_keys_filters():
    env = _make_env(("DB_HOST", "localhost"), ("APP_NAME", "myapp"), ("CACHE_URL", "redis://"))
    result = split_by_prefix(env, include_keys=["DB_HOST", "APP_NAME"])
    all_keys = {e.key for entries in result.groups.values() for e in entries}
    assert "DB_HOST" in all_keys
    assert "APP_NAME" in all_keys
    assert "CACHE_URL" not in all_keys


def test_split_by_prefix_mixed_case_prefix_lowercased():
    env = _make_env(("AWS_KEY", "abc"), ("AWS_SECRET", "xyz"))
    result = split_by_prefix(env)
    assert "aws" in result.groups
    assert len(result.groups["aws"]) == 2


def test_split_empty_env_returns_empty_groups():
    env = EnvFile(entries=[], path=".env")
    result = split_by_prefix(env)
    assert result.groups == {}
    assert result.is_clean()
