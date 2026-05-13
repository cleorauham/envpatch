"""Tests for envpatch.cli_transform."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envpatch.cli_transform import build_transform_parser, run_transform


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": ".env",
        "transforms": [],
        "dry_run": False,
        "out": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_transform_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_transform_parser(sub)
    assert p is not None


def test_run_transform_missing_file_returns_1(tmp_path):
    args = _make_args(file=str(tmp_path / "missing.env"))
    assert run_transform(args) == 1


def test_run_transform_returns_0_on_clean(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\nPORT=8080\n")
    args = _make_args(file=str(env_file), transforms=["strip_values"])
    assert run_transform(args) == 0


def test_run_transform_dry_run_does_not_write(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\n")
    original_mtime = env_file.stat().st_mtime
    args = _make_args(file=str(env_file), transforms=["uppercase_keys"], dry_run=True)
    rc = run_transform(args)
    assert rc == 0
    assert env_file.stat().st_mtime == original_mtime
    captured = capsys.readouterr()
    assert "HOST" in captured.out


def test_run_transform_writes_to_out_file(tmp_path):
    env_file = tmp_path / ".env"
    out_file = tmp_path / "out.env"
    env_file.write_text("host=localhost\n")
    args = _make_args(file=str(env_file), transforms=["uppercase_keys"], out=str(out_file))
    rc = run_transform(args)
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "HOST" in content


def test_run_transform_unknown_transform_prints_warning(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("A=1\n")
    args = _make_args(file=str(env_file), transforms=["does_not_exist"], dry_run=True)
    rc = run_transform(args)
    captured = capsys.readouterr()
    assert "warning" in captured.err
