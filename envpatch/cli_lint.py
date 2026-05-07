"""CLI sub-command: lint an .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.linter import LintSeverity, lint
from envpatch.parser import parse


def build_lint_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "lint",
        help="Check an .env file for style and convention issues.",
    )
    p.add_argument("env_file", help="Path to the .env file to lint.")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status on warnings as well as errors.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; only use exit code.",
    )
    return p


def run_lint(args: argparse.Namespace) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env_file = parse(path.read_text())
    result = lint(env_file)

    if not args.quiet:
        if not result.issues:
            print(f"lint: {path} — no issues found.")
        else:
            for issue in result.issues:
                print(str(issue))
            print()
            print(
                f"lint summary: {len(result.errors)} error(s), "
                f"{len(result.warnings)} warning(s)."
            )

    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0
