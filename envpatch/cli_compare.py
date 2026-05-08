"""CLI sub-command: compare two .env files."""

import argparse
import sys
from typing import Optional

from envpatch.parser import parse
from envpatch.comparator import compare
from envpatch.formatter import format_diff


def build_compare_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Compare two .env files and show a structured diff."
    if subparsers is not None:
        parser = subparsers.add_parser("compare", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envpatch compare", description=description)

    parser.add_argument("source", help="Base .env file")
    parser.add_argument("target", help="Target .env file to compare against")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )
    parser.add_argument(
        "--summary-only", action="store_true", help="Print summary line only"
    )
    return parser


def run_compare(args: argparse.Namespace) -> int:
    try:
        source = parse(args.source)
        target = parse(args.target)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = compare(source, target)

    if args.summary_only:
        print(result.summary())
    else:
        print(result.summary())
        print()
        colored = not args.no_color
        print(format_diff(result.diff, color=colored))

    return 0 if result.is_identical else 1
