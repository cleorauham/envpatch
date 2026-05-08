"""Tests for envpatch.grouper and envpatch.cli_group."""
from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path

import pytest

from envpatch.grouper import EntryGroup, GroupResult, group_by_prefix
from envpatch.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries)


# ---------------------------------------------------------------------------
# EntryGroup
# ---------------------------------------------------------------------------

def test_entry_group_len():
    g = EntryGroup(prefix="DB", entries=[EnvEntry(key="DB_HOST", value="localhost", raw="DB_HOST=localhost")])
    assert len(g) == 1


def test_entry_group_str_shows_prefix_and_key():
    g = EntryGroup(prefix="DB", entries=[EnvEntry(key="DB_HOST", value="localhost", raw="DB_HOST=localhost")])
    text = str(g)
    assert "[DB]" in text
    assert "DB_HOST=localhost" in text


def test_entry_group_str_empty():
    g = EntryGroup(prefix="EMPTY")
    assert "empty" in str(g)


# ---------------------------------------------------------------------------
# group_by_prefix
# ---------------------------------------------------------------------------

def test_group_by_prefix_basic():
    env = _make_env(("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("APP_NAME", "myapp"))
    result = group_by_prefix(env)
    assert "DB" in result.group_names
    assert "APP" in result.group_names
    assert len(result.get("DB")) == 2
    assert len(result.get("APP")) == 1


def test_group_by_prefix_no_separator_goes_to_ungrouped():
    env = _make_env(("PORT", "8080"), ("DEBUG", "true"))
    result = group_by_prefix(env)
    assert "" in result.group_names
    assert len(result.ungrouped()) == 2


def test_group_by_prefix_custom_separator():
    env = _make_env(("DB.HOST", "localhost"), ("DB.PORT", "5432"))
    result = group_by_prefix(env, separator=".")
    assert "DB" in result.group_names
    assert len(result.get("DB")) == 2


def test_group_by_prefix_empty_env():
    env = EnvFile(entries=[])
    result = group_by_prefix(env)
    assert result.group_names == []


def test_group_result_get_missing_prefix_returns_none():
    env = _make_env(("APP_NAME", "x"))
    result = group_by_prefix(env)
    assert result.get("MISSING") is None


def test_group_result_str_no_groups():
    result = GroupResult()
    assert "no groups" in str(result)


# ---------------------------------------------------------------------------
# cli_group
# ---------------------------------------------------------------------------

def test_run_group_lists_prefixes(tmp_path: Path):
    from envpatch.cli_group import build_group_parser, run_group

    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nAPP_NAME=myapp\n")

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    build_group_parser(subs)
    args = parser.parse_args(["group", str(env_file), "--list-prefixes"])

    out = StringIO()
    rc = run_group(args, out=out)
    assert rc == 0
    output = out.getvalue()
    assert "DB" in output
    assert "APP" in output


def test_run_group_missing_file(tmp_path: Path):
    from envpatch.cli_group import build_group_parser, run_group

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    build_group_parser(subs)
    args = parser.parse_args(["group", str(tmp_path / "missing.env")])

    out = StringIO()
    rc = run_group(args, out=out)
    assert rc == 1
    assert "not found" in out.getvalue()


def test_run_group_specific_prefix(tmp_path: Path):
    from envpatch.cli_group import build_group_parser, run_group

    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    build_group_parser(subs)
    args = parser.parse_args(["group", str(env_file), "--prefix", "DB"])

    out = StringIO()
    rc = run_group(args, out=out)
    assert rc == 0
    output = out.getvalue()
    assert "DB_HOST" in output
    assert "APP_NAME" not in output
