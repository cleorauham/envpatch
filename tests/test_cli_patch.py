"""Tests for envpatch.cli_patch."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch as mock_patch

import pytest

from envpatch.cli_patch import build_patch_parser, run_patch
from envpatch.parser import EnvEntry, EnvFile
from envpatch.patcher import PatchResult
from envpatch.differ import DiffResult


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(path=".env", entries=entries)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "source": "source.env",
        "target": "target.env",
        "output": None,
        "skip_missing": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_patch_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    build_patch_parser(subparsers)
    args = parser.parse_args(["patch", "src.env", "tgt.env"])
    assert args.source == "src.env"
    assert args.target == "tgt.env"


def test_run_patch_returns_0_on_clean(tmp_path):
    src = tmp_path / "source.env"
    tgt = tmp_path / "target.env"
    src.write_text("A=1\nB=2\n")
    tgt.write_text("A=1\n")
    args = _make_args(source=str(src), target=str(tgt), output=str(tgt))
    result = run_patch(args)
    assert result == 0


def test_run_patch_dry_run_does_not_write(tmp_path):
    src = tmp_path / "source.env"
    tgt = tmp_path / "target.env"
    src.write_text("A=1\nB=2\n")
    tgt.write_text("A=1\n")
    original_content = tgt.read_text()
    args = _make_args(source=str(src), target=str(tgt), dry_run=True)
    run_patch(args)
    assert tgt.read_text() == original_content


def test_run_patch_writes_to_output_path(tmp_path):
    src = tmp_path / "source.env"
    tgt = tmp_path / "target.env"
    out = tmp_path / "out.env"
    src.write_text("A=1\nB=2\n")
    tgt.write_text("A=1\n")
    args = _make_args(source=str(src), target=str(tgt), output=str(out))
    run_patch(args)
    assert out.exists()
    content = out.read_text()
    assert "B" in content
