"""CLI sub-command: trim — remove keys absent from a reference .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.trimmer import trim
from envpatch.writer import write_env


def build_trim_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Remove keys from TARGET that are not present in REFERENCE."
    if subparsers is not None:
        parser = subparsers.add_parser("trim", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envpatch trim", description=description)

    parser.add_argument("reference", metavar="REFERENCE", help="Reference .env file (defines allowed keys).")
    parser.add_argument("target", metavar="TARGET", help="Target .env file to trim.")
    parser.add_argument(
        "--output", "-o",
        metavar="OUTPUT",
        default=None,
        help="Write trimmed output to OUTPUT instead of overwriting TARGET.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be removed without writing any files.",
    )
    parser.add_argument(
        "--no-keep-comments",
        action="store_true",
        help="Strip blank lines and comments from the output.",
    )
    return parser


def run_trim(args: argparse.Namespace) -> int:
    reference_env = parse(Path(args.reference).read_text())
    target_env = parse(Path(args.target).read_text())

    reference_keys = {e.key for e in reference_env.entries if e.key is not None}
    keep_comments = not args.no_keep_comments

    result = trim(target_env, reference_keys, keep_comments=keep_comments)

    if result.removed:
        print(f"Keys to remove ({len(result.removed)}):")
        for issue in result.removed:
            print(f"  - {issue.key}")
    else:
        print("No unused keys found.")

    if args.dry_run:
        return 0

    dest = Path(args.output) if args.output else Path(args.target)
    write_env(result.kept, dest)
    print(f"Written to {dest}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_trim_parser()
    sys.exit(run_trim(parser.parse_args()))
