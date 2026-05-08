"""Rename keys across an env file, producing a patched result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class RenameIssue:
    old_key: str
    reason: str

    def __str__(self) -> str:
        return f"[RENAME] {self.old_key}: {self.reason}"


@dataclass
class RenameResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[RenameIssue] = field(default_factory=list)
    applied: Dict[str, str] = field(default_factory=dict)  # old -> new

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean:
            applied = ", ".join(f"{o}->{n}" for o, n in self.applied.items())
            return f"RenameResult: {len(self.applied)} rename(s) applied ({applied})"
        lines = [f"RenameResult: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def rename(env: EnvFile, mapping: Dict[str, str]) -> RenameResult:
    """Rename keys in *env* according to *mapping* (old_key -> new_key).

    Rules:
    - If old_key is not present, an issue is recorded (key not found).
    - If new_key already exists in the file, an issue is recorded (conflict).
    - Renamed entries preserve original value and comment.
    """
    issues: List[RenameIssue] = []
    applied: Dict[str, str] = {}
    existing_keys = {e.key for e in env.entries if e.key is not None}

    # Validate mapping before applying
    for old_key, new_key in mapping.items():
        if old_key not in existing_keys:
            issues.append(RenameIssue(old_key, "key not found in env file"))
        elif new_key in existing_keys and new_key != old_key:
            issues.append(RenameIssue(old_key, f"target key '{new_key}' already exists"))

    if issues:
        return RenameResult(entries=list(env.entries), issues=issues, applied={})

    new_entries: List[EnvEntry] = []
    for entry in env.entries:
        if entry.key is not None and entry.key in mapping:
            new_key = mapping[entry.key]
            new_entries.append(
                EnvEntry(key=new_key, value=entry.value, comment=entry.comment, raw=entry.raw)
            )
            applied[entry.key] = new_key
        else:
            new_entries.append(entry)

    return RenameResult(entries=new_entries, issues=[], applied=applied)
