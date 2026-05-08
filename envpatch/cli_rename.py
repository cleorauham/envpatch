"""CLI sub-command: rename keys in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envpatch.parser import parse
from envpatch.renamer import rename
from envpatch.writer import write_env


def build_rename_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("rename", help="Rename one or more keys in a .env file")
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "renames",
        nargs="+",
        metavar="OLD=NEW",
        help="Key rename pairs in OLD=NEW format",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print result without writing to disk",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Write output to this file instead of overwriting input",
    )
    return p


def _parse_renames(pairs: List[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid rename pair (expected OLD=NEW): {pair!r}")
        old, _, new = pair.partition("=")
        mapping[old.strip()] = new.strip()
    return mapping


def run_rename(args: argparse.Namespace) -> int:
    try:
        mapping = _parse_renames(args.renames)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    env_file = parse(Path(args.env_file))
    result = rename(env_file, mapping)

    if not result.is_clean:
        for issue in result.issues:
            print(str(issue), file=sys.stderr)
        return 1

    from envpatch.parser import EnvFile
    patched = EnvFile(path=env_file.path, entries=result.entries)

    if args.dry_run:
        from envpatch.writer import render_env
        print(render_env(patched))
        return 0

    dest = Path(args.output) if args.output else env_file.path
    write_env(patched, dest)
    print(f"Renamed {len(result.applied)} key(s) in {dest}")
    return 0
