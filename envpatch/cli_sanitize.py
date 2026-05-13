"""CLI sub-command: sanitize — remove unsafe characters from .env values."""

from __future__ import annotations

import argparse
import sys

from envpatch.parser import parse
from envpatch.sanitizer import sanitize
from envpatch.writer import write_env


def build_sanitize_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "sanitize",
        help="Remove control characters and null bytes from .env values.",
    )
    parser.add_argument("file", help="Path to the .env file to sanitize.")
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write sanitized output back to the original file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report issues without writing any changes.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output when no issues are found.",
    )
    return parser


def run_sanitize(args: argparse.Namespace) -> int:
    try:
        env = parse(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    result = sanitize(env)

    if not result.is_clean():
        print(str(result))
        if args.dry_run:
            return 1

    if result.is_clean() and not args.quiet:
        print("Sanitize: no issues found.")

    if args.in_place and not args.dry_run:
        write_env(result.entries, args.file)
        if not args.quiet:
            print(f"Written sanitized output to {args.file}")

    return 0 if result.is_clean() else 1
