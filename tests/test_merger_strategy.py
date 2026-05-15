"""Tests for envpatch.merger_strategy and envpatch.cli_strategy."""
from __future__ import annotations

import argparse

import pytest

from envpatch.merger_strategy import (
    ConflictPolicy,
    ExtraKeyPolicy,
    FORCE,
    MergeStrategy,
    MissingKeyPolicy,
    PRESETS,
    SAFE,
    STRICT,
    get_preset,
)
from envpatch.cli_strategy import build_strategy_parser, run_strategy


# ---------------------------------------------------------------------------
# MergeStrategy unit tests
# ---------------------------------------------------------------------------

def test_safe_preset_conflict_policy():
    assert SAFE.conflict_policy == ConflictPolicy.KEEP_TARGET


def test_strict_preset_conflict_policy():
    assert STRICT.conflict_policy == ConflictPolicy.ERROR


def test_force_preset_conflict_policy():
    assert FORCE.conflict_policy == ConflictPolicy.TAKE_SOURCE


def test_safe_preset_missing_key_adds():
    assert SAFE.missing_key_policy == MissingKeyPolicy.ADD


def test_strict_preset_extra_key_warns():
    assert STRICT.extra_key_policy == ExtraKeyPolicy.WARN


def test_is_protected_returns_true_for_listed_key():
    strategy = MergeStrategy(
        protected_keys=frozenset({"DATABASE_URL", "SECRET_KEY"})
    )
    assert strategy.is_protected("DATABASE_URL") is True


def test_is_protected_returns_false_for_unlisted_key():
    strategy = MergeStrategy(protected_keys=frozenset({"SECRET_KEY"}))
    assert strategy.is_protected("API_KEY") is False


def test_is_protected_empty_set_always_false():
    assert SAFE.is_protected("ANY_KEY") is False


def test_get_preset_returns_safe():
    assert get_preset("safe") is SAFE


def test_get_preset_case_insensitive():
    assert get_preset("STRICT") is STRICT


def test_get_preset_unknown_returns_none():
    assert get_preset("nonexistent") is None


def test_presets_dict_contains_all_three():
    assert set(PRESETS.keys()) == {"safe", "strict", "force"}


# ---------------------------------------------------------------------------
# CLI strategy tests
# ---------------------------------------------------------------------------

def _make_args(name=None):
    ns = argparse.Namespace()
    ns.name = name
    return ns


def test_run_strategy_no_name_returns_0():
    assert run_strategy(_make_args()) == 0


def test_run_strategy_valid_name_returns_0():
    assert run_strategy(_make_args("safe")) == 0


def test_run_strategy_unknown_name_returns_1():
    assert run_strategy(_make_args("bogus")) == 1


def test_run_strategy_prints_preset_details(capsys):
    run_strategy(_make_args("force"))
    captured = capsys.readouterr()
    assert "force" in captured.out
    assert "take_source" in captured.out


def test_run_strategy_lists_all_presets(capsys):
    run_strategy(_make_args())
    captured = capsys.readouterr()
    for name in ("safe", "strict", "force"):
        assert name in captured.out


def test_build_strategy_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_strategy_parser(sub)
    args = root.parse_args(["strategy"])
    assert args.command == "strategy"
