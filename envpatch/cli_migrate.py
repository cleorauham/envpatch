"""CLI sub-command: migrate — rename and remove keys in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from envpatch.parser import parse, EnvFile
from envpatch.migrator import migrate
from envpatch.writer import write_env


def build_migrate_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = subparsers.add_parser("migrate", help="Rename or remove keys in a .env file")
    p.add_argument("file", help="Path to the .env file to migrate")
    p.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        default=[],
        help="Rename a key (repeatable)",
    )
    p.add_argument(
        "--remove",
        metavar="KEY",
        action="append",
        default=[],
        help="Remove a key (repeatable)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the result without writing to disk",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of overwriting the source",
    )
    return p


def _parse_renames(raw: List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"Invalid rename spec (expected OLD=NEW): {item!r}")
        old, new = item.split("=", 1)
        result[old.strip()] = new.strip()
    return result


def run_migrate(args: argparse.Namespace) -> int:
    src = Path(args.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 1

    try:
        rename_map = _parse_renames(args.rename)
    except argparse.ArgumentTypeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    env: EnvFile = parse(src)
    result = migrate(env, rename_map=rename_map, remove_keys=args.remove)

    if not result.is_clean():
        print(str(result), file=sys.stderr)

    if args.dry_run:
        for entry in result.entries:
            suffix = f"  # {entry.comment}" if entry.comment else ""
            print(f"{entry.key}={entry.value}{suffix}")
        return 0 if result.is_clean() else 1

    dest = Path(args.output) if args.output else src
    write_env(result.entries, dest)
    print(f"Migrated {src} -> {dest} ({len(result.renamed)} renamed, {len(result.removed)} removed)")
    return 0 if result.is_clean() else 1
