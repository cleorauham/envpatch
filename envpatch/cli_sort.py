"""CLI sub-command: sort — reorder .env file entries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.sorter import sort_alphabetically, sort_by_prefix
from envpatch.writer import write_env, render_env


def build_sort_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "sort",
        help="Sort and optionally group keys in a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--by-prefix",
        action="store_true",
        default=False,
        help="Group keys by their prefix (first segment before '_').",
    )
    parser.add_argument(
        "--prefixes",
        nargs="+",
        metavar="PREFIX",
        help="Explicit prefixes to group by (implies --by-prefix).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the sorted output without writing to disk.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write sorted output to FILE instead of overwriting the source.",
    )
    return parser


def run_sort(args: argparse.Namespace) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse(path.read_text())

    use_prefix = args.by_prefix or bool(getattr(args, "prefixes", None))
    if use_prefix:
        result = sort_by_prefix(env, prefixes=getattr(args, "prefixes", None))
    else:
        result = sort_alphabetically(env)

    sorted_env_entries = result.all_entries
    # Build a minimal EnvFile-like mapping for render_env
    from envpatch.parser import EnvFile
    sorted_env = EnvFile(entries=sorted_env_entries, path=env.path)

    rendered = render_env(sorted_env)

    if args.dry_run:
        print(rendered)
        return 0

    dest = Path(args.output) if getattr(args, "output", None) else path
    write_env(sorted_env, dest)
    print(f"Sorted {len(sorted_env_entries)} entries -> {dest}")
    return 0
