"""Strip comments and blank lines from .env files, producing a clean output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class StripIssue:
    line_number: int
    original: str
    reason: str  # 'blank' | 'comment'

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.reason!r} — {self.original!r}"


@dataclass
class StripResult:
    entries: List[EnvEntry]
    removed: List[StripIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        """True when nothing was stripped (file already had no comments/blanks)."""
        return len(self.removed) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "StripResult: nothing to strip"
        lines = [f"StripResult: {len(self.removed)} line(s) removed"]
        for issue in self.removed:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def strip(env: EnvFile) -> StripResult:
    """Return a StripResult containing only real key=value entries.

    Blank lines and comment lines present in the original raw source are
    recorded as StripIssue items so callers can report what was removed.
    """
    kept: List[EnvEntry] = []
    removed: List[StripIssue] = []

    for entry in env.entries:
        kept.append(entry)

    # Walk the raw lines to detect blanks and comments that the parser skipped.
    entry_keys = {e.key for e in env.entries}
    raw_lines = getattr(env, "raw_lines", [])

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if stripped == "":
            removed.append(StripIssue(line_number=lineno, original=raw, reason="blank"))
        elif stripped.startswith("#"):
            removed.append(StripIssue(line_number=lineno, original=raw, reason="comment"))

    return StripResult(entries=kept, removed=removed)
