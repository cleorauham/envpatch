"""CLI sub-command: envpatch strategy — inspect and list merge strategies."""
from __future__ import annotations

import argparse
from typing import List

from envpatch.merger_strategy import PRESETS, MergeStrategy


def build_strategy_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "strategy",
        help="List available merge strategies and their policies.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Show details for a specific strategy preset (safe | strict | force).",
    )
    return parser


def _describe(name: str, strategy: MergeStrategy) -> List[str]:
    lines: List[str] = [
        f"Strategy : {name}",
        f"  conflict_policy   : {strategy.conflict_policy.value}",
        f"  missing_key_policy: {strategy.missing_key_policy.value}",
        f"  extra_key_policy  : {strategy.extra_key_policy.value}",
    ]
    if strategy.protected_keys:
        lines.append(f"  protected_keys    : {', '.join(sorted(strategy.protected_keys))}")
    return lines


def run_strategy(args: argparse.Namespace) -> int:
    name: str | None = getattr(args, "name", None)

    if name is not None:
        strategy = PRESETS.get(name.lower())
        if strategy is None:
            print(f"Unknown strategy '{name}'. Available: {', '.join(PRESETS)}.")
            return 1
        for line in _describe(name.lower(), strategy):
            print(line)
        return 0

    # List all presets
    print(f"Available merge strategies ({len(PRESETS)}):")
    for preset_name, preset in PRESETS.items():
        print()
        for line in _describe(preset_name, preset):
            print(line)
    return 0
