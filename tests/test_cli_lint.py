"""Tests for envpatch.cli_lint."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envpatch.cli_lint import build_lint_parser, run_lint


def _make_args(
    env_file: str,
    strict: bool = False,
    quiet: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, strict=strict, quiet=quiet)


def test_run_lint_clean_file(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    args = _make_args(str(env))
    code = run_lint(args)
    assert code == 0


def test_run_lint_returns_1_on_error(tmp_path: Path):
    env = tmp_path / ".env"
    # duplicate key triggers an error
    env.write_text("API_KEY=first\nAPI_KEY=second\n")
    args = _make_args(str(env))
    code = run_lint(args)
    assert code == 1


def test_run_lint_strict_returns_1_on_warning(tmp_path: Path):
    env = tmp_path / ".env"
    # lowercase key triggers a warning
    env.write_text("db_host=localhost\n")
    args = _make_args(str(env), strict=True)
    code = run_lint(args)
    assert code == 1


def test_run_lint_non_strict_returns_0_on_warning(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("db_host=localhost\n")
    args = _make_args(str(env), strict=False)
    code = run_lint(args)
    assert code == 0


def test_run_lint_missing_file(tmp_path: Path):
    args = _make_args(str(tmp_path / "nonexistent.env"))
    code = run_lint(args)
    assert code == 2


def test_run_lint_quiet_suppresses_output(tmp_path: Path, capsys):
    env = tmp_path / ".env"
    env.write_text("API_KEY=first\nAPI_KEY=second\n")
    args = _make_args(str(env), quiet=True)
    run_lint(args)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_build_lint_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_lint_parser(sub)
    assert p is not None
    parsed = root.parse_args(["lint", "some.env"])
    assert parsed.env_file == "some.env"
    assert parsed.strict is False
    assert parsed.quiet is False
