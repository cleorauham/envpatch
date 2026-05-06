"""Formatting utilities for rendering diff and merge results as human-readable output."""

from typing import List
from envpatch.differ import ChangeType, DiffEntry, DiffResult
from envpatch.merger import MergeConflict, MergeResult


ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_CYAN = "\033[96m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_diff(result: DiffResult, use_color: bool = True) -> str:
    """Render a DiffResult as a unified-style diff string."""
    lines: List[str] = []
    for entry in result.entries:
        if entry.change_type == ChangeType.ADDED:
            line = f"+ {entry.key}={entry.new_value}"
            lines.append(_colorize(line, ANSI_GREEN, use_color))
        elif entry.change_type == ChangeType.REMOVED:
            line = f"- {entry.key}={entry.old_value}"
            lines.append(_colorize(line, ANSI_RED, use_color))
        elif entry.change_type == ChangeType.MODIFIED:
            lines.append(_colorize(f"~ {entry.key}", ANSI_YELLOW, use_color))
            lines.append(_colorize(f"  - {entry.old_value}", ANSI_RED, use_color))
            lines.append(_colorize(f"  + {entry.new_value}", ANSI_GREEN, use_color))
        elif entry.change_type == ChangeType.UNCHANGED:
            line = f"  {entry.key}={entry.old_value}"
            lines.append(line)
    return "\n".join(lines)


def format_merge_result(result: MergeResult, use_color: bool = True) -> str:
    """Render a MergeResult, highlighting conflicts."""
    lines: List[str] = []
    if result.conflicts:
        header = f"=== {len(result.conflicts)} conflict(s) found ==="
        lines.append(_colorize(header, ANSI_BOLD, use_color))
        for conflict in result.conflicts:
            lines.append(_colorize(f"  CONFLICT: {conflict.key}", ANSI_RED, use_color))
            lines.append(f"    base:   {conflict.base_value}")
            lines.append(f"    target: {conflict.target_value}")
        lines.append("")
    for key, value in sorted(result.merged.items()):
        lines.append(f"{key}={value}")
    return "\n".join(lines)
