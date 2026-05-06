"""Merge logic for applying diffs to .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .differ import ChangeType, DiffResult
from .parser import EnvEntry, EnvFile


@dataclass
class MergeConflict:
    key: str
    base_value: Optional[str]
    incoming_value: Optional[str]
    message: str


@dataclass
class MergeResult:
    merged: EnvFile
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def __str__(self) -> str:
        lines = [str(entry) for entry in self.merged.entries]
        return "\n".join(lines)


def merge(
    base: EnvFile,
    diff: DiffResult,
    overwrite_existing: bool = False,
) -> MergeResult:
    """Apply *diff* to *base*, returning a MergeResult.

    Parameters
    ----------
    base:
        The target .env file to patch.
    diff:
        The diff produced by ``envpatch.differ.diff`` between a reference and
        an incoming environment.
    overwrite_existing:
        When ``True``, MODIFIED entries in *base* are overwritten with the
        incoming value without raising a conflict.
    """
    entries: list[EnvEntry] = list(base.entries)
    key_index: dict[str, int] = {e.key: i for i, e in enumerate(entries) if e.key}
    conflicts: list[MergeConflict] = []

    for change in diff.changes:
        key = change.key

        if change.change_type == ChangeType.ADDED:
            if key not in key_index:
                new_entry = EnvEntry(
                    key=key,
                    value=change.incoming_value,
                    raw_line=f"{key}={change.incoming_value}",
                )
                entries.append(new_entry)
                key_index[key] = len(entries) - 1

        elif change.change_type == ChangeType.REMOVED:
            if key in key_index:
                idx = key_index.pop(key)
                entries[idx] = EnvEntry(
                    key=None,
                    value=None,
                    raw_line=f"# REMOVED: {key}",
                )

        elif change.change_type == ChangeType.MODIFIED:
            if key in key_index:
                if overwrite_existing:
                    idx = key_index[key]
                    entries[idx] = EnvEntry(
                        key=key,
                        value=change.incoming_value,
                        raw_line=f"{key}={change.incoming_value}",
                    )
                else:
                    conflicts.append(
                        MergeConflict(
                            key=key,
                            base_value=change.base_value,
                            incoming_value=change.incoming_value,
                            message=(
                                f"Key '{key}' has diverged: "
                                f"base={change.base_value!r}, "
                                f"incoming={change.incoming_value!r}"
                            ),
                        )
                    )

    return MergeResult(merged=EnvFile(entries=entries), conflicts=conflicts)
