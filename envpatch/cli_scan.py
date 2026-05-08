"""CLI sub-command: scan — categorise .env keys by pattern."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.scanner import PatternCategory, scan


def build_scan_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("scan", help="Categorise .env keys by pattern (secret, url, path, flag, unknown)")
    p.add_argument("env_file", help="Path to the .env file to scan")
    p.add_argument(
        "--category",
        choices=[c.value for c in PatternCategory],
        default=None,
        help="Filter output to a specific category",
    )
    p.add_argument("--summary", action="store_true", help="Print only the summary line")
    return p


def run_scan(args: argparse.Namespace) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse(path.read_text())
    result = scan(env)

    if args.summary:
        print(result.summary())
        return 0

    entries = result.entries
    if args.category:
        cat = PatternCategory(args.category)
        entries = result.by_category(cat)

    if not entries:
        print("No matching entries.")
        return 0

    for entry in entries:
        print(str(entry))

    print()
    print(result.summary())
    return 0
