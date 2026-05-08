"""Trimmer: detect and remove unused keys from a .env file relative to a reference set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class TrimIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class TrimResult:
    kept: List[EnvEntry] = field(default_factory=list)
    removed: List[TrimIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.removed) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Trim result: no unused keys found."
        lines = ["Trim result: unused keys removed:"]
        for issue in self.removed:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def trim(env: EnvFile, reference_keys: Set[str], *, keep_comments: bool = True) -> TrimResult:
    """Return a TrimResult keeping only entries whose keys appear in *reference_keys*.

    Non-key lines (blank lines, comments) are preserved in *kept* when
    *keep_comments* is True so that the output file retains its structure.
    """
    result = TrimResult()
    for entry in env.entries:
        if entry.key is None:
            # blank line or comment
            if keep_comments:
                result.kept.append(entry)
        elif entry.key in reference_keys:
            result.kept.append(entry)
        else:
            result.removed.append(
                TrimIssue(key=entry.key, reason="not present in reference set")
            )
    return result
