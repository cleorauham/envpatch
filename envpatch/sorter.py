"""Sort and group .env file entries by key prefix or alphabetically."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class SortedGroup:
    """A named group of env entries sharing a common prefix."""

    prefix: str
    entries: List[EnvEntry] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.entries)


@dataclass
class SortResult:
    """Result of a sort/group operation."""

    groups: List[SortedGroup]
    ungrouped: List[EnvEntry] = field(default_factory=list)

    @property
    def all_entries(self) -> List[EnvEntry]:
        """Return all entries in sorted group order, then ungrouped."""
        result: List[EnvEntry] = []
        for group in self.groups:
            result.extend(group.entries)
        result.extend(self.ungrouped)
        return result

    def group_names(self) -> List[str]:
        return [g.prefix for g in self.groups]


def sort_alphabetically(env: EnvFile) -> SortResult:
    """Return a SortResult with a single group of alphabetically sorted entries."""
    sorted_entries = sorted(
        [e for e in env.entries if e.key is not None],
        key=lambda e: e.key.upper(),
    )
    group = SortedGroup(prefix="", entries=sorted_entries)
    return SortResult(groups=[group], ungrouped=[])


def sort_by_prefix(
    env: EnvFile,
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
) -> SortResult:
    """Group entries by key prefix, sorting entries within each group.

    Args:
        env: Parsed env file.
        prefixes: Explicit list of prefixes to group by. If None, prefixes are
                  inferred from the first segment of each key.
        separator: Character used to split key into prefix and remainder.
    """
    keyed = [e for e in env.entries if e.key is not None]

    if prefixes is None:
        seen: Dict[str, bool] = {}
        for entry in keyed:
            seg = entry.key.split(separator, 1)[0]
            seen[seg] = True
        prefixes = sorted(seen.keys())

    bucket: Dict[str, List[EnvEntry]] = {p: [] for p in prefixes}
    ungrouped: List[EnvEntry] = []

    for entry in keyed:
        seg = entry.key.split(separator, 1)[0]
        if seg in bucket:
            bucket[seg].append(entry)
        else:
            ungrouped.append(entry)

    groups = [
        SortedGroup(
            prefix=p,
            entries=sorted(bucket[p], key=lambda e: e.key.upper()),
        )
        for p in prefixes
        if bucket[p]
    ]

    ungrouped_sorted = sorted(ungrouped, key=lambda e: e.key.upper())
    return SortResult(groups=groups, ungrouped=ungrouped_sorted)
