"""Tests for envpatch.cli_split."""
from __future__ import annotations

import os
import argparse

import pytest

from envpatch.cli_split import build_split_parser, run_split


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": ".env",
        "delimiter": "_",
        "default_group": "misc",
        "output_dir": ".",
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_split_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    parser = build_split_parser(sub)
    assert parser is not None


def test_run_split_missing_file_returns_1(tmp_path):
    args = _make_args(file=str(tmp_path / "missing.env"))
    assert run_split(args) == 1


def test_run_split_dry_run_does_not_write(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    out_dir = tmp_path / "out"
    args = _make_args(
        file=str(env_file),
        output_dir=str(out_dir),
        dry_run=True,
    )
    rc = run_split(args)
    assert rc == 0
    assert not out_dir.exists()
    captured = capsys.readouterr()
    assert "db" in captured.out


def test_run_split_writes_files(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nAPP_NAME=myapp\n")
    out_dir = tmp_path / "split_out"
    args = _make_args(
        file=str(env_file),
        output_dir=str(out_dir),
    )
    rc = run_split(args)
    assert rc == 0
    assert (out_dir / ".env.db").exists()
    assert (out_dir / ".env.app").exists()


def test_run_split_output_contains_correct_keys(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    out_dir = tmp_path / "out"
    args = _make_args(file=str(env_file), output_dir=str(out_dir))
    run_split(args)
    db_content = (out_dir / ".env.db").read_text()
    assert "DB_HOST" in db_content
    assert "DB_PORT" in db_content
    assert "APP_NAME" not in db_content
