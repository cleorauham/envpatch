"""Tests for envpatch.cli_migrate."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envpatch.cli_migrate import build_migrate_parser, run_migrate, _parse_renames
from envpatch.parser import EnvFile, EnvEntry


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": ".env",
        "rename": [],
        "remove": [],
        "dry_run": False,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_env_file(*pairs) -> EnvFile:
    return EnvFile(entries=[EnvEntry(key=k, value=v) for k, v in pairs], path=None)


# ---------------------------------------------------------------------------
# _parse_renames
# ---------------------------------------------------------------------------

def test_parse_renames_single():
    result = _parse_renames(["OLD=NEW"])
    assert result == {"OLD": "NEW"}


def test_parse_renames_multiple():
    result = _parse_renames(["A=B", "C=D"])
    assert result == {"A": "B", "C": "D"}


def test_parse_renames_invalid_raises():
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_renames(["NOEQUALS"])


# ---------------------------------------------------------------------------
# build_migrate_parser
# ---------------------------------------------------------------------------

def test_build_migrate_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_migrate_parser(sub)
    ns = root.parse_args(["migrate", ".env"])
    assert ns.file == ".env"


# ---------------------------------------------------------------------------
# run_migrate
# ---------------------------------------------------------------------------

def test_run_migrate_missing_file_returns_1(tmp_path):
    args = _make_args(file=str(tmp_path / "nonexistent.env"))
    assert run_migrate(args) == 1


def test_run_migrate_returns_0_on_clean(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    args = _make_args(file=str(env_file))
    with patch("envpatch.cli_migrate.write_env") as mock_write:
        code = run_migrate(args)
    assert code == 0
    mock_write.assert_called_once()


def test_run_migrate_dry_run_does_not_write(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("OLD=val\n")
    args = _make_args(file=str(env_file), rename=["OLD=NEW"], dry_run=True)
    with patch("envpatch.cli_migrate.write_env") as mock_write:
        code = run_migrate(args)
    mock_write.assert_not_called()
    captured = capsys.readouterr()
    assert "NEW" in captured.out
    assert code == 0


def test_run_migrate_custom_output(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("A=1\n")
    out_file = tmp_path / "out.env"
    args = _make_args(file=str(env_file), output=str(out_file))
    with patch("envpatch.cli_migrate.write_env") as mock_write:
        run_migrate(args)
    called_path = mock_write.call_args[0][1]
    assert called_path == out_file
