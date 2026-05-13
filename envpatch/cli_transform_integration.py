"""Integration helpers for wiring the transform sub-command into the main CLI."""
from __future__ import annotations

import argparse
from typing import Optional

from envpatch.cli_transform import build_transform_parser, run_transform


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the *transform* sub-command to an existing subparsers group."""
    build_transform_parser(subparsers)


def create_standalone_parser() -> argparse.ArgumentParser:
    """Return a fully configured parser for use as a standalone entry point."""
    parser = argparse.ArgumentParser(
        prog="envpatch-transform",
        description="Apply named transformations to a .env file.",
    )
    sub = parser.add_subparsers(dest="command")
    build_transform_parser(sub)
    return parser


def dispatch(args: Optional[argparse.Namespace] = None) -> int:
    """Parse *args* (or ``sys.argv``) and run the transform command.

    Returns the process exit code.
    """
    parser = create_standalone_parser()
    parsed = parser.parse_args(args)  # type: ignore[arg-type]
    return run_transform(parsed)
