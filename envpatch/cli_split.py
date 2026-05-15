"""CLI interface for the splitter module."""
from __future__ import annotations

import argparse
import os
from typing import Optional

from envpatch.parser import parse
from envpatch.splitter import split_by_prefix
from envpatch.writer import render_env, write_env


def build_split_parser(subparsers: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Split a .env file into multiple files by key prefix."
    )
    if subparsers is not None:
        parser = subparsers.add_parser("split", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Source .env file")
    parser.add_argument(
        "--delimiter",
        default="_",
        help="Delimiter used to detect prefix (default: _)",
    )
    parser.add_argument(
        "--default-group",
        default="misc",
        help="Group name for keys without a prefix (default: misc)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write split .env files into (default: current dir)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print split groups without writing files",
    )
    return parser


def run_split(args: argparse.Namespace) -> int:
    if not os.path.exists(args.file):
        print(f"Error: file not found: {args.file}")
        return 1

    env = parse(args.file)
    result = split_by_prefix(
        env,
        delimiter=args.delimiter,
        default_group=args.default_group,
    )

    if not result.is_clean():
        for issue in result.issues:
            print(f"Warning: {issue}")

    for group_name, entries in result.groups.items():
        out_path = os.path.join(args.output_dir, f".env.{group_name}")
        content = render_env(entries)
        if args.dry_run:
            print(f"--- {out_path} ({len(entries)} keys) ---")
            print(content)
        else:
            os.makedirs(args.output_dir, exist_ok=True)
            write_env(out_path, content)
            print(f"Written: {out_path} ({len(entries)} keys)")

    return 0
