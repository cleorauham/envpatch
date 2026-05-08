"""Group .env entries by prefix (e.g. DB_, AWS_, APP_)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class EntryGroup:
    """A named collection of EnvEntry objects sharing a common prefix."""

    prefix: str  # e.g. "DB" or "" for ungrouped
    entries: List[EnvEntry] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.entries)

    def __str__(self) -> str:
        if not self.entries:
            return f"[{self.prefix or 'ungrouped'}] (empty)"
        lines = [f"[{self.prefix or 'ungrouped'}]"]
        for e in self.entries:
            lines.append(f"  {e.key}={e.value}")
        return "\n".join(lines)


@dataclass
class GroupResult:
    """Result of grouping an EnvFile by key prefix."""

    groups: Dict[str, EntryGroup] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        return list(self.groups.keys())

    def get(self, prefix: str) -> Optional[EntryGroup]:
        return self.groups.get(prefix)

    def ungrouped(self) -> EntryGroup:
        return self.groups.get("", EntryGroup(prefix=""))

    def __str__(self) -> str:
        if not self.groups:
            return "(no groups)"
        return "\n".join(str(g) for g in self.groups.values())


def group_by_prefix(env: EnvFile, separator: str = "_") -> GroupResult:
    """Group entries by the first segment of their key split on *separator*.

    Keys without the separator are placed in the ungrouped ("") bucket.
    Comment/blank lines (entries with no key) are skipped.
    """
    result = GroupResult()

    for entry in env.entries:
        if not entry.key:
            continue
        if separator in entry.key:
            prefix = entry.key.split(separator, 1)[0]
        else:
            prefix = ""

        if prefix not in result.groups:
            result.groups[prefix] = EntryGroup(prefix=prefix)
        result.groups[prefix].entries.append(entry)

    return result
