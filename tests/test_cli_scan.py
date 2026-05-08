"""Tests for envpatch.cli_scan."""
import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envpatch.cli_scan import build_scan_parser, run_scan


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": ".env", "category": None, "summary": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


ENV_CONTENT = "DB_PASSWORD=secret\nDATABASE_URL=postgres://localhost/db\nWORKERS=4\n"


def test_build_scan_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    p = build_scan_parser(subs)
    assert p is not None


def test_run_scan_missing_file_returns_1(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_scan(args) == 1


def test_run_scan_returns_0_on_valid_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file))
    assert run_scan(args) == 0


def test_run_scan_summary_only(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), summary=True)
    rc = run_scan(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Scan summary" in captured.out


def test_run_scan_filter_by_category(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), category="secret")
    rc = run_scan(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "DB_PASSWORD" in captured.out
    assert "DATABASE_URL" not in captured.out


def test_run_scan_no_matching_category_prints_message(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("WORKERS=4\n")
    args = _make_args(env_file=str(env_file), category="secret")
    rc = run_scan(args)
    assert rc == 0
    assert "No matching" in capsys.readouterr().out
