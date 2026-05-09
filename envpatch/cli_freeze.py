"""CLI sub-command: freeze / verify an env file against a lock file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.freezer import freeze, load_freeze, save_freeze, verify_freeze
from envpatch.parser import parse


def build_freeze_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "freeze",
        help="Freeze an .env file into a checksum lock or verify against one.",
    )
    p.add_argument("env_file", help="Path to the .env file.")
    p.add_argument(
        "--lock",
        default=".env.lock",
        metavar="LOCK_FILE",
        help="Path to the lock file (default: .env.lock).",
    )
    p.add_argument(
        "--verify",
        action="store_true",
        help="Verify the env file against an existing lock instead of writing one.",
    )
    p.add_argument(
        "--allow-extra",
        action="store_true",
        help="When verifying, do not flag keys present in env but absent from lock.",
    )
    return p


def run_freeze(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    lock_path = Path(args.lock)

    if not env_path.exists():
        print(f"[error] env file not found: {env_path}", file=sys.stderr)
        return 1

    env = parse(env_path.read_text(), source=str(env_path))

    if args.verify:
        if not lock_path.exists():
            print(f"[error] lock file not found: {lock_path}", file=sys.stderr)
            return 1
        lock = load_freeze(lock_path)
        result = verify_freeze(env, lock, allow_extra=args.allow_extra)
        print(result)
        return 0 if result.is_clean() else 1

    # Write mode
    result = freeze(env)
    save_freeze(result, lock_path)
    print(f"Frozen {len(result.entries)} key(s) to {lock_path}")
    return 0
