"""Tests for envpatch.sorter."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sorter import (
    SortResult,
    SortedGroup,
    sort_alphabetically,
    sort_by_prefix,
)


def _make_env(*keys: str) -> EnvFile:
    entries = [EnvEntry(key=k, value="val", raw=f"{k}=val") for k in keys]
    return EnvFile(entries=entries, path=".env")


# --- SortedGroup ---

def test_sorted_group_len():
    g = SortedGroup(prefix="APP", entries=[EnvEntry(key="APP_A", value="1", raw="APP_A=1")])
    assert len(g) == 1


# --- SortResult ---

def test_sort_result_all_entries_order():
    g1 = SortedGroup(prefix="A", entries=[EnvEntry(key="A_X", value="1", raw="A_X=1")])
    g2 = SortedGroup(prefix="B", entries=[EnvEntry(key="B_Y", value="2", raw="B_Y=2")])
    ungrouped = [EnvEntry(key="ZZZ", value="3", raw="ZZZ=3")]
    result = SortResult(groups=[g1, g2], ungrouped=ungrouped)
    keys = [e.key for e in result.all_entries]
    assert keys == ["A_X", "B_Y", "ZZZ"]


def test_sort_result_group_names():
    g1 = SortedGroup(prefix="DB")
    g2 = SortedGroup(prefix="APP")
    result = SortResult(groups=[g1, g2])
    assert result.group_names() == ["DB", "APP"]


# --- sort_alphabetically ---

def test_sort_alphabetically_orders_keys():
    env = _make_env("ZEBRA", "APPLE", "MANGO")
    result = sort_alphabetically(env)
    assert len(result.groups) == 1
    keys = [e.key for e in result.groups[0].entries]
    assert keys == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_alphabetically_case_insensitive():
    env = _make_env("b_KEY", "A_KEY", "c_KEY")
    result = sort_alphabetically(env)
    keys = [e.key for e in result.all_entries]
    assert keys == ["A_KEY", "b_KEY", "c_KEY"]


def test_sort_alphabetically_skips_comment_entries():
    entries = [
        EnvEntry(key=None, value=None, raw="# comment"),
        EnvEntry(key="B", value="1", raw="B=1"),
        EnvEntry(key="A", value="2", raw="A=2"),
    ]
    env = EnvFile(entries=entries, path=".env")
    result = sort_alphabetically(env)
    keys = [e.key for e in result.all_entries]
    assert keys == ["A", "B"]


# --- sort_by_prefix ---

def test_sort_by_prefix_groups_correctly():
    env = _make_env("DB_HOST", "DB_PORT", "APP_NAME", "APP_ENV")
    result = sort_by_prefix(env)
    names = result.group_names()
    assert "APP" in names
    assert "DB" in names


def test_sort_by_prefix_entries_sorted_within_group():
    env = _make_env("DB_PORT", "DB_HOST", "DB_NAME")
    result = sort_by_prefix(env)
    assert len(result.groups) == 1
    keys = [e.key for e in result.groups[0].entries]
    assert keys == ["DB_HOST", "DB_NAME", "DB_PORT"]


def test_sort_by_prefix_ungrouped_when_explicit_prefixes():
    env = _make_env("DB_HOST", "APP_NAME", "OTHER_KEY")
    result = sort_by_prefix(env, prefixes=["DB", "APP"])
    ungrouped_keys = [e.key for e in result.ungrouped]
    assert "OTHER_KEY" in ungrouped_keys


def test_sort_by_prefix_explicit_prefixes_respected():
    env = _make_env("DB_HOST", "APP_NAME", "REDIS_URL")
    result = sort_by_prefix(env, prefixes=["APP", "DB"])
    names = result.group_names()
    assert names == ["APP", "DB"]
    ungrouped_keys = [e.key for e in result.ungrouped]
    assert "REDIS_URL" in ungrouped_keys


def test_sort_by_prefix_empty_group_not_included():
    env = _make_env("APP_NAME")
    result = sort_by_prefix(env, prefixes=["APP", "DB"])
    # DB has no entries, should not appear
    assert "DB" not in result.group_names()
