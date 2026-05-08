"""Apply a patch (diff) to a target .env file, producing a patched EnvFile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.differ import ChangeType, DiffResult
from envpatch.parser import EnvEntry, EnvFile


@dataclass
class PatchIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"[PATCH] {self.key}: {self.reason}"


@dataclass
class PatchResult:
    patched: EnvFile
    issues: List[PatchIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean:
            return "Patch applied cleanly."
        lines = ["Patch applied with issues:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def patch(target: EnvFile, diff: DiffResult, skip_missing: bool = False) -> PatchResult:
    """Apply *diff* to *target*, returning a new patched EnvFile.

    Args:
        target: The base .env file to patch.
        diff: A DiffResult describing changes to apply.
        skip_missing: When True, removals of keys absent in target are silently
                      skipped rather than recorded as issues.

    Returns:
        A PatchResult containing the patched EnvFile and any issues encountered.
    """
    entries: dict[str, EnvEntry] = {e.key: e for e in target.entries}
    issues: list[PatchIssue] = []

    for change in diff.changes:
        if change.change_type == ChangeType.ADDED:
            if change.key in entries:
                issues.append(PatchIssue(change.key, "key already exists; overwriting"))
            entries[change.key] = EnvEntry(
                key=change.key,
                value=change.new_value or "",
                comment=None,
                raw=f"{change.key}={change.new_value or ''}",
            )
        elif change.change_type == ChangeType.REMOVED:
            if change.key not in entries:
                if not skip_missing:
                    issues.append(PatchIssue(change.key, "key not found in target"))
            else:
                del entries[change.key]
        elif change.change_type == ChangeType.MODIFIED:
            if change.key not in entries:
                issues.append(PatchIssue(change.key, "key not found; adding as new"))
            entries[change.key] = EnvEntry(
                key=change.key,
                value=change.new_value or "",
                comment=None,
                raw=f"{change.key}={change.new_value or ''}",
            )
        # UNCHANGED entries require no action

    patched_file = EnvFile(
        path=target.path,
        entries=list(entries.values()),
    )
    return PatchResult(patched=patched_file, issues=issues)
