"""CLI sub-command: generate a .env.example template from an existing .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.templater import build_template


def build_template_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "template",
        help="Generate a .env.example template from an existing .env file.",
    )
    p.add_argument("source", help="Path to the source .env file.")
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Destination file (default: <source>.example).",
    )
    p.add_argument(
        "--keep-values",
        action="store_true",
        default=False,
        help="Preserve original values instead of replacing with placeholders.",
    )
    p.add_argument(
        "--no-annotate",
        action="store_true",
        default=False,
        help="Do not add inline 'required' comments to redacted entries.",
    )
    return p


def run_template(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        print(f"error: source file not found: {source}", file=sys.stderr)
        return 1

    env_file = parse(source.read_text(encoding="utf-8"))
    result = build_template(
        env_file,
        keep_values=args.keep_values,
        annotate=not args.no_annotate,
    )

    rendered = result.render()

    output_path = Path(args.output) if args.output else source.with_suffix(".example")
    output_path.write_text(rendered + "\n", encoding="utf-8")
    print(f"Template written to {output_path}")
    return 0
