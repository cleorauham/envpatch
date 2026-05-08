"""Integration helpers: register the patch sub-command into the main CLI parser."""
from __future__ import annotations

import argparse
from typing import Optional

from envpatch.cli_patch import build_patch_parser, run_patch


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'patch' command onto an existing subparsers action."""
    p = build_patch_parser(subparsers)
    p.set_defaults(func=run_patch)


def create_standalone_parser() -> argparse.ArgumentParser:
    """Return a standalone argument parser for the patch command (useful for testing)."""
    parser = argparse.ArgumentParser(
        prog="envpatch patch",
        description="Apply changes from a source .env onto a target .env file.",
    )
    parser.add_argument("source", help="Source .env file (desired state).")
    parser.add_argument("target", help="Target .env file to be patched.")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output path (defaults to overwriting target).",
    )
    parser.add_argument(
        "--skip-missing", action="store_true", default=False,
        help="Skip removals of keys absent in target without raising issues.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Print result to stdout without writing to disk.",
    )
    return parser


def dispatch(argv: Optional[list[str]] = None) -> int:
    """Parse *argv* and execute the patch command. Returns an exit code."""
    parser = create_standalone_parser()
    args = parser.parse_args(argv)
    return run_patch(args)
