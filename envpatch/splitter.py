"""Split a single .env file into multiple files by prefix or group."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class SplitIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class SplitResult:
    groups: Dict[str, List[EnvEntry]] = field(default_factory=dict)
    issues: List[SplitIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            lines = [f"Split into {len(self.groups)} group(s):"]
            for name, entries in self.groups.items():
                lines.append(f"  {name}: {len(entries)} key(s)")
            return "\n".join(lines)
        issue_lines = [f"  - {i}" for i in self.issues]
        return "Split issues:\n" + "\n".join(issue_lines)


def split_by_prefix(
    env: EnvFile,
    delimiter: str = "_",
    default_group: str = "misc",
    include_keys: Optional[List[str]] = None,
) -> SplitResult:
    """Split env entries into groups based on key prefix."""
    groups: Dict[str, List[EnvEntry]] = {}
    issues: List[SplitIssue] = []

    entries = [
        e for e in env.entries
        if include_keys is None or e.key in include_keys
    ]

    for entry in entries:
        if delimiter in entry.key:
            prefix = entry.key.split(delimiter, 1)[0].lower()
        else:
            prefix = default_group

        if not prefix:
            issues.append(SplitIssue(entry.key, "empty prefix after split"))
            prefix = default_group

        groups.setdefault(prefix, []).append(entry)

    return SplitResult(groups=groups, issues=issues)
