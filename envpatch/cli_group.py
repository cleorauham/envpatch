"""CLI sub-command: group — display .env entries grouped by key prefix."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.grouper import group_by_prefix
from envpatch.parser import parse


def build_group_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "group",
        help="Display .env entries grouped by key prefix.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--separator",
        default="_",
        help="Prefix separator character (default: '_').",
    )
    p.add_argument(
        "--prefix",
        default=None,
        help="Show only entries for a specific prefix.",
    )
    p.add_argument(
        "--list-prefixes",
        action="store_true",
        help="List discovered prefix groups and exit.",
    )
    return p


def run_group(args: argparse.Namespace, out=sys.stdout) -> int:
    path = Path(args.file)
    if not path.exists():
        out.write(f"error: file not found: {path}\n")
        return 1

    env = parse(path.read_text())
    result = group_by_prefix(env, separator=args.separator)

    if args.list_prefixes:
        names = result.group_names
        if not names:
            out.write("(no groups found)\n")
        else:
            for name in names:
                label = name if name else "(ungrouped)"
                out.write(f"{label}\n")
        return 0

    if args.prefix is not None:
        group = result.get(args.prefix)
        if group is None:
            out.write(f"(no entries for prefix '{args.prefix}')\n")
            return 0
        out.write(str(group) + "\n")
        return 0

    out.write(str(result) + "\n")
    return 0
