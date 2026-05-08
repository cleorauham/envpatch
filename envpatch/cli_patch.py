"""CLI sub-command: envpatch patch — apply a diff to a .env file."""
from __future__ import annotations

import argparse
import sys

from envpatch.differ import diff
from envpatch.parser import parse
from envpatch.patcher import patch
from envpatch.writer import write_env


def build_patch_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "patch",
        help="Apply changes from a source .env onto a target .env file.",
    )
    p.add_argument("source", help="Source .env file (contains the desired state).")
    p.add_argument("target", help="Target .env file to be patched.")
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write patched result to this file (defaults to overwriting target).",
    )
    p.add_argument(
        "--skip-missing",
        action="store_true",
        default=False,
        help="Silently skip removals of keys absent in target.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the patched content without writing to disk.",
    )
    return p


def run_patch(args: argparse.Namespace) -> int:
    source_env = parse(args.source)
    target_env = parse(args.target)

    diff_result = diff(target_env, source_env)
    patch_result = patch(target_env, diff_result, skip_missing=args.skip_missing)

    if not patch_result.is_clean:
        for issue in patch_result.issues:
            print(f"WARNING: {issue}", file=sys.stderr)

    if args.dry_run:
        from envpatch.writer import render_env
        print(render_env(patch_result.patched))
        return 0

    output_path = args.output or args.target
    write_env(patch_result.patched, output_path)
    print(f"Patched env written to {output_path}")
    return 0
