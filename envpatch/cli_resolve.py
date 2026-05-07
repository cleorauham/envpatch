"""CLI sub-command: resolve — parse, validate and interpolate an env file."""
from __future__ import annotations

import os
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Optional

from envpatch.resolver import resolve


def build_resolve_parser(subparsers) -> None:  # type: ignore[type-arg]
    """Register the *resolve* sub-command onto *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "resolve",
        help="Parse, validate, and interpolate a .env file",
    )
    p.add_argument("env_file", metavar="ENV_FILE", help="Path to the .env file")
    p.add_argument(
        "--external",
        metavar="KEY=VALUE",
        nargs="*",
        default=[],
        help="Extra variables for interpolation, e.g. SCHEME=https",
    )
    p.add_argument(
        "--use-os-env",
        action="store_true",
        default=False,
        help="Seed interpolation with the current OS environment",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with non-zero status if any issues are found",
    )
    p.set_defaults(func=run_resolve)


def _parse_extra(pairs: List[str]) -> dict:
    result = {}
    for pair in pairs:
        if "=" in pair:
            k, _, v = pair.partition("=")
            result[k.strip()] = v.strip()
    return result


def run_resolve(args: Namespace) -> int:
    """Execute the resolve sub-command. Returns an exit code."""
    external: dict = {}
    if args.use_os_env:
        external.update(os.environ)
    external.update(_parse_extra(args.external or []))

    result = resolve(Path(args.env_file), external=external or None)

    print(result.summary())

    if args.strict and not result.is_ok():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    from argparse import ArgumentParser as AP

    root = AP(description="envpatch resolve")
    subs = root.add_subparsers()
    build_resolve_parser(subs)
    parsed = root.parse_args()
    sys.exit(parsed.func(parsed) if hasattr(parsed, "func") else 0)
