"""Tests for envpatch.comparator and envpatch.cli_compare."""

import argparse
import pytest

from envpatch.parser import EnvFile
from envpatch.parser import EnvEntry
from envpatch.comparator import compare, CompareResult
from envpatch.cli_compare import build_compare_parser, run_compare


def _make_env(path: str, entries: dict) -> EnvFile:
    env_entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", line_number=i + 1)
        for i, (k, v) in enumerate(entries.items())
    ]
    return EnvFile(path=path, entries=env_entries)


def test_compare_identical_files():
    source = _make_env(".env", {"A": "1", "B": "2"})
    target = _make_env(".env.prod", {"A": "1", "B": "2"})
    result = compare(source, target)
    assert result.is_identical
    assert result.common == ["A", "B"]
    assert result.modified == []
    assert result.only_in_source == []
    assert result.only_in_target == []


def test_compare_key_only_in_source():
    source = _make_env(".env", {"A": "1", "EXTRA": "x"})
    target = _make_env(".env.prod", {"A": "1"})
    result = compare(source, target)
    assert "EXTRA" in result.only_in_source
    assert not result.is_identical


def test_compare_key_only_in_target():
    source = _make_env(".env", {"A": "1"})
    target = _make_env(".env.prod", {"A": "1", "NEW": "y"})
    result = compare(source, target)
    assert "NEW" in result.only_in_target
    assert not result.is_identical


def test_compare_modified_key():
    source = _make_env(".env", {"DB": "localhost"})
    target = _make_env(".env.prod", {"DB": "prod-host"})
    result = compare(source, target)
    assert "DB" in result.modified
    assert not result.is_identical


def test_compare_summary_contains_paths():
    source = _make_env("a.env", {"X": "1"})
    target = _make_env("b.env", {"X": "2"})
    result = compare(source, target)
    summary = result.summary()
    assert "a.env" in summary
    assert "b.env" in summary


def test_compare_summary_identical_label():
    source = _make_env(".env", {"K": "v"})
    target = _make_env(".env.prod", {"K": "v"})
    result = compare(source, target)
    assert "identical" in result.summary()


def test_compare_summary_differs_label():
    source = _make_env(".env", {"K": "v1"})
    target = _make_env(".env.prod", {"K": "v2"})
    result = compare(source, target)
    assert "differs" in result.summary()


def test_run_compare_missing_file(tmp_path):
    args = argparse.Namespace(
        source=str(tmp_path / "missing.env"),
        target=str(tmp_path / "also_missing.env"),
        no_color=True,
        summary_only=False,
    )
    rc = run_compare(args)
    assert rc == 2


def test_run_compare_identical_returns_0(tmp_path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("KEY=value\n")
    f2.write_text("KEY=value\n")
    args = argparse.Namespace(
        source=str(f1), target=str(f2), no_color=True, summary_only=True
    )
    assert run_compare(args) == 0


def test_run_compare_differs_returns_1(tmp_path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("KEY=old\n")
    f2.write_text("KEY=new\n")
    args = argparse.Namespace(
        source=str(f1), target=str(f2), no_color=True, summary_only=False
    )
    assert run_compare(args) == 1
