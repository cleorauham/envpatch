"""CLI sub-command: detect duplicate keys in a .env file."""
from __future__ import annotations

import argparse
import sys

from envpatch.duplicates import find_duplicates
from envpatch.parser import parse


def build_duplicates_parser(subparsers=None):
    description = "Detect duplicate keys in a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("duplicates", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envpatch duplicates", description=description)

    parser.add_argument("file", help="Path to the .env file to check.")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any duplicates are found.",
    )
    return parser


def run_duplicates(args) -> int:
    try:
        env_file = parse(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2

    result = find_duplicates(env_file)
    print(result)

    if args.strict and not result.is_clean():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_duplicates_parser()
    args = parser.parse_args()
    sys.exit(run_duplicates(args))
