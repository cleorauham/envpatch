"""Integration helpers to register the split command into a root CLI parser."""
from __future__ import annotations

import argparse

from envpatch.cli_split import build_split_parser, run_split


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'split' subcommand onto an existing subparsers action."""
    build_split_parser(subparsers)


def create_standalone_parser() -> argparse.ArgumentParser:
    """Return a standalone ArgumentParser for the split command."""
    return build_split_parser()


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch parsed args to run_split and return exit code."""
    return run_split(args)
