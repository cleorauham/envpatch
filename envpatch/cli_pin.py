"""CLI subcommand: pin — lock env checksums and detect drift."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.pinner import compare_pin, load_pin, pin, save_pin


def build_pin_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "pin",
        help="Lock .env checksums and detect value drift.",
    )
    p.add_argument("env_file", help="Path to the .env file.")
    p.add_argument(
        "--lockfile",
        default=".env.lock",
        help="Path to the pin lockfile (default: .env.lock).",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Compare against existing lockfile and report drift.",
    )
    p.add_argument(
        "--save",
        action="store_true",
        help="Write current checksums to the lockfile.",
    )
    return p


def run_pin(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    lock_path = Path(args.lockfile)

    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        return 1

    env = parse(env_path.read_text(), source=str(env_path))

    if args.check:
        lock = load_pin(lock_path)
        if not lock:
            print(f"No lockfile found at {lock_path}. Run with --save first.", file=sys.stderr)
            return 1
        result = compare_pin(env, lock)
        print(str(result))
        return 0 if result.is_clean() else 1

    if args.save:
        result = pin(env)
        save_pin(result, lock_path)
        print(f"Pinned {len(result.entries)} keys to {lock_path}.")
        return 0

    # Default: just show current checksums
    result = pin(env)
    for entry in result.entries:
        print(str(entry))
    return 0
