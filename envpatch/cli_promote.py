"""CLI sub-command: promote keys between .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.promoter import promote
from envpatch.writer import write_env


def build_promote_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Promote key/value pairs from a source .env into a target .env."
    if subparsers is not None:
        parser = subparsers.add_parser("promote", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envpatch promote", description=description)

    parser.add_argument("source", help="Source .env file to promote values from.")
    parser.add_argument("target", help="Target .env file to promote values into.")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to promote (default: all source keys).",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        metavar="KEY",
        help="Keys to skip during promotion.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite keys that already exist in the target.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would change without writing the target file.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write result to FILE instead of overwriting target.",
    )
    return parser


def run_promote(args: argparse.Namespace) -> int:
    source_path = Path(args.source)
    target_path = Path(args.target)

    if not source_path.exists():
        print(f"error: source file not found: {source_path}", file=sys.stderr)
        return 1
    if not target_path.exists():
        print(f"error: target file not found: {target_path}", file=sys.stderr)
        return 1

    source_env = parse(source_path)
    target_env = parse(target_path)

    result = promote(
        source=source_env,
        target=target_env,
        keys=args.keys,
        overwrite=args.overwrite,
        exclude=args.exclude,
    )

    print(str(result))

    if args.dry_run:
        print("(dry-run: no files written)")
        return 0

    out_path = Path(args.output) if getattr(args, "output", None) else target_path
    write_env(result.promoted, out_path)
    return 0
