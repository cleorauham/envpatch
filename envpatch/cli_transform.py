"""CLI sub-command: envpatch transform — apply transformations to a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.transformer import transform
from envpatch.writer import write_env

_AVAILABLE = [
    "uppercase_keys",
    "strip_values",
    "lowercase_values",
    "uppercase_values",
    "quote_values",
    "unquote_values",
]


def build_transform_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "transform",
        help="Apply named transformations to a .env file.",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--apply",
        metavar="TRANSFORM",
        action="append",
        dest="transforms",
        default=[],
        help=f"Transformation to apply (repeatable). Available: {', '.join(_AVAILABLE)}",
    )
    p.add_argument("--dry-run", action="store_true", help="Print result without writing")
    p.add_argument("--out", metavar="FILE", help="Write output to FILE instead of overwriting input")
    return p


def run_transform(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse(path.read_text())
    result = transform(env, args.transforms)

    if not result.is_clean():
        for issue in result.issues:
            print(f"warning: {issue}", file=sys.stderr)

    from envpatch.parser import EnvFile
    transformed_env = EnvFile(entries=result.entries, path=env.path)

    if args.dry_run:
        from envpatch.writer import render_env
        print(render_env(transformed_env))
        return 0

    out_path = Path(args.out) if args.out else path
    write_env(transformed_env, out_path)
    print(f"Wrote transformed env to {out_path}")
    return 0
