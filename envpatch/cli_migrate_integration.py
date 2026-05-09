"""Standalone entry-point wiring for the migrate sub-command."""
from __future__ import annotations

import argparse
import sys

from envpatch.cli_migrate import build_migrate_parser, run_migrate


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the migrate sub-command on an existing subparsers action."""
    p = build_migrate_parser(subparsers)
    p.set_defaults(func=run_migrate)


def create_standalone_parser() -> argparse.ArgumentParser:
    """Build a self-contained argument parser for the migrate command."""
    root = argparse.ArgumentParser(
        prog="envpatch-migrate",
        description="Rename or remove keys in a .env file",
    )
    sub = root.add_subparsers(dest="command")
    register(sub)
    return root


def dispatch(argv: list[str] | None = None) -> int:
    """Parse *argv* and run the migrate command.  Returns an exit code."""
    parser = create_standalone_parser()
    ns = parser.parse_args(argv)
    if not hasattr(ns, "func"):
        parser.print_help()
        return 0
    return ns.func(ns)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(dispatch())
