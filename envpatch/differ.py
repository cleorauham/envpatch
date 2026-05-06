"""Diff logic — compares two EnvFile objects and reports changes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from envpatch.parser import EnvFile


class ChangeType(Enum):
    ADDED = auto()
    REMOVED = auto()
    MODIFIED = auto()
    UNCHANGED = auto()


@dataclass
class DiffEntry:
    key: str
    change: ChangeType
    old_value: str | None = None
    new_value: str | None = None

    def __str__(self) -> str:
        if self.change == ChangeType.ADDED:
            return f"+ {self.key}={self.new_value}"
        if self.change == ChangeType.REMOVED:
            return f"- {self.key}={self.old_value}"
        if self.change == ChangeType.MODIFIED:
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"  {self.key}={self.old_value}"


@dataclass
class DiffResult:
    entries: List[DiffEntry]

    @property
    def has_changes(self) -> bool:
        return any(e.change != ChangeType.UNCHANGED for e in self.entries)

    def summary(self) -> str:
        counts = {ct: 0 for ct in ChangeType}
        for e in self.entries:
            counts[e.change] += 1
        return (
            f"added={counts[ChangeType.ADDED]}, "
            f"removed={counts[ChangeType.REMOVED]}, "
            f"modified={counts[ChangeType.MODIFIED]}, "
            f"unchanged={counts[ChangeType.UNCHANGED]}"
        )


def diff(base: EnvFile, incoming: EnvFile) -> DiffResult:
    """Compute the diff between *base* and *incoming* EnvFile objects."""
    base_dict = base.as_dict()
    incoming_dict = incoming.as_dict()

    all_keys = sorted(set(base_dict) | set(incoming_dict))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_base = key in base_dict
        in_incoming = key in incoming_dict

        if in_base and not in_incoming:
            entries.append(DiffEntry(key, ChangeType.REMOVED, old_value=base_dict[key]))
        elif not in_base and in_incoming:
            entries.append(DiffEntry(key, ChangeType.ADDED, new_value=incoming_dict[key]))
        elif base_dict[key] != incoming_dict[key]:
            entries.append(
                DiffEntry(
                    key,
                    ChangeType.MODIFIED,
                    old_value=base_dict[key],
                    new_value=incoming_dict[key],
                )
            )
        else:
            entries.append(DiffEntry(key, ChangeType.UNCHANGED, old_value=base_dict[key]))

    return DiffResult(entries=entries)
