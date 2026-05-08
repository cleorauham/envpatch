"""Tests for envpatch.cli_rename."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

from envpatch.cli_rename import _parse_renames, build_rename_parser, run_rename
from envpatch.parser import EnvEntry, EnvFile
from envpatch.renamer import RenameResult


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "env_file": ".env",
        "renames": ["OLD=NEW"],
        "dry_run": False,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_env_file(path: str = ".env") -> EnvFile:
    return EnvFile(
        path=Path(path),
        entries=[EnvEntry(key="OLD", value="val", comment=None, raw="OLD=val")],
    )


# ---------------------------------------------------------------------------
# _parse_renames
# ---------------------------------------------------------------------------

def test_parse_renames_single():
    assert _parse_renames(["A=B"]) == {"A": "B"}


def test_parse_renames_multiple():
    assert _parse_renames(["A=B", "C=D"]) == {"A": "B", "C": "D"}


def test_parse_renames_invalid_raises():
    import pytest
    with pytest.raises(ValueError, match="OLD_NEW"):
        _parse_renames(["OLD_NEW"])


# ---------------------------------------------------------------------------
# build_rename_parser
# ---------------------------------------------------------------------------

def test_build_rename_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_rename_parser(sub)
    args = root.parse_args(["rename", ".env", "A=B"])
    assert args.cmd == "rename"
    assert args.renames == ["A=B"]


# ---------------------------------------------------------------------------
# run_rename
# ---------------------------------------------------------------------------

def test_run_rename_returns_0_on_success(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OLD=val\n")
    args = _make_args(env_file=str(env_path), renames=["OLD=NEW"])
    result = run_rename(args)
    assert result == 0
    assert "NEW=val" in env_path.read_text()


def test_run_rename_dry_run_does_not_write(tmp_path, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text("OLD=val\n")
    args = _make_args(env_file=str(env_path), renames=["OLD=NEW"], dry_run=True)
    result = run_rename(args)
    assert result == 0
    assert "OLD=val" in env_path.read_text()  # file unchanged
    captured = capsys.readouterr()
    assert "NEW" in captured.out


def test_run_rename_returns_1_on_missing_key(tmp_path, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text("PRESENT=val\n")
    args = _make_args(env_file=str(env_path), renames=["MISSING=NEW"])
    result = run_rename(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "MISSING" in captured.err


def test_run_rename_returns_2_on_bad_pair(tmp_path, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text("A=1\n")
    args = _make_args(env_file=str(env_path), renames=["BADPAIR"])
    result = run_rename(args)
    assert result == 2
