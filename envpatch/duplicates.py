"""Detect and report duplicate keys in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile


@dataclass
class DuplicateIssue:
    key: str
    line_numbers: List[int]

    def __str__(self) -> str:
        lines = ", ".join(str(n) for n in self.line_numbers)
        return f"Duplicate key '{self.key}' found on lines: {lines}"


@dataclass
class DuplicateResult:
    issues: List[DuplicateIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "No duplicate keys found."
        lines = ["Duplicate keys detected:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def find_duplicates(env_file: EnvFile) -> DuplicateResult:
    """Scan an EnvFile for duplicate keys and return a DuplicateResult."""
    seen: dict[str, List[int]] = {}

    for entry in env_file.entries:
        if entry.key is None:
            continue
        if entry.key not in seen:
            seen[entry.key] = []
        seen[entry.key].append(entry.line_number)

    issues = [
        DuplicateIssue(key=key, line_numbers=line_numbers)
        for key, line_numbers in seen.items()
        if len(line_numbers) > 1
    ]

    return DuplicateResult(issues=issues)
