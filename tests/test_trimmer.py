"""Tests for envpatch.trimmer and envpatch.cli_trim."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.trimmer import TrimIssue, TrimResult, trim
from envpatch.cli_trim import build_trim_parser, run_trim


def _make_env(*keys_and_values) -> EnvFile:
    entries = []
    for k, v in keys_and_values:
        entries.append(EnvEntry(key=k, value=v, raw=f"{k}={v}"))
    return EnvFile(entries=entries, path=None)


# --- TrimIssue ---

def test_trim_issue_str():
    issue = TrimIssue(key="OLD_KEY", reason="not present in reference set")
    assert "OLD_KEY" in str(issue)
    assert "not present" in str(issue)


# --- TrimResult ---

def test_trim_result_is_clean_when_no_removals():
    result = TrimResult(kept=[], removed=[])
    assert result.is_clean()


def test_trim_result_not_clean_with_removals():
    result = TrimResult(kept=[], removed=[TrimIssue("X", "reason")])
    assert not result.is_clean()


def test_trim_result_str_clean():
    result = TrimResult()
    assert "no unused" in str(result)


def test_trim_result_str_with_removals():
    result = TrimResult(removed=[TrimIssue("STALE", "not present in reference set")])
    text = str(result)
    assert "STALE" in text
    assert "removed" in text


# --- trim() ---

def test_trim_keeps_matching_keys():
    env = _make_env(("DB_HOST", "localhost"), ("DB_PORT", "5432"))
    result = trim(env, {"DB_HOST", "DB_PORT"})
    assert result.is_clean()
    assert len(result.kept) == 2


def test_trim_removes_extra_keys():
    env = _make_env(("DB_HOST", "localhost"), ("LEGACY_KEY", "old"))
    result = trim(env, {"DB_HOST"})
    assert not result.is_clean()
    assert len(result.removed) == 1
    assert result.removed[0].key == "LEGACY_KEY"
    kept_keys = [e.key for e in result.kept if e.key]
    assert "DB_HOST" in kept_keys
    assert "LEGACY_KEY" not in kept_keys


def test_trim_keeps_comments_by_default():
    comment_entry = EnvEntry(key=None, value=None, raw="# a comment")
    env = EnvFile(entries=[comment_entry, EnvEntry(key="A", value="1", raw="A=1")], path=None)
    result = trim(env, {"A"})
    assert any(e.key is None for e in result.kept)


def test_trim_strips_comments_when_disabled():
    comment_entry = EnvEntry(key=None, value=None, raw="# a comment")
    env = EnvFile(entries=[comment_entry, EnvEntry(key="A", value="1", raw="A=1")], path=None)
    result = trim(env, {"A"}, keep_comments=False)
    assert all(e.key is not None for e in result.kept)


# --- CLI ---

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "reference": "ref.env",
        "target": "target.env",
        "output": None,
        "dry_run": False,
        "no_keep_comments": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_trim_parser_has_required_args():
    parser = build_trim_parser()
    assert parser is not None


def test_run_trim_dry_run_returns_0(tmp_path):
    ref = tmp_path / "ref.env"
    ref.write_text("DB_HOST=localhost\n")
    target = tmp_path / "target.env"
    target.write_text("DB_HOST=localhost\nLEGACY=old\n")
    args = _make_args(reference=str(ref), target=str(target), dry_run=True)
    assert run_trim(args) == 0


def test_run_trim_writes_output(tmp_path):
    ref = tmp_path / "ref.env"
    ref.write_text("DB_HOST=localhost\n")
    target = tmp_path / "target.env"
    target.write_text("DB_HOST=localhost\nLEGACY=old\n")
    out = tmp_path / "out.env"
    args = _make_args(reference=str(ref), target=str(target), output=str(out))
    rc = run_trim(args)
    assert rc == 0
    content = out.read_text()
    assert "DB_HOST" in content
    assert "LEGACY" not in content
