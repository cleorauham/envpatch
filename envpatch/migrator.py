"""Migrate .env files by applying a rename map and removing deprecated keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class MigrationIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class MigrationResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[MigrationIssue] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)   # old -> new
    removed: List[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Migration complete — no issues."
        lines = ["Migration issues:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def migrate(
    env: EnvFile,
    rename_map: Optional[Dict[str, str]] = None,
    remove_keys: Optional[List[str]] = None,
) -> MigrationResult:
    """Apply renames and removals to *env*, returning a MigrationResult.

    Args:
        env: Parsed source EnvFile.
        rename_map: Mapping of old key -> new key.
        remove_keys: Keys that should be dropped from the result.

    Returns:
        MigrationResult with transformed entries and any diagnostic issues.
    """
    rename_map = rename_map or {}
    remove_keys_set = set(remove_keys or [])
    issues: List[MigrationIssue] = []
    renamed: Dict[str, str] = {}
    removed: List[str] = []
    out_entries: List[EnvEntry] = []
    seen_new_keys: Dict[str, str] = {}

    for entry in env.entries:
        key = entry.key

        if key in remove_keys_set:
            removed.append(key)
            continue

        new_key = rename_map.get(key, key)

        if new_key != key:
            if new_key in seen_new_keys:
                issues.append(
                    MigrationIssue(
                        key=key,
                        message=f"rename target '{new_key}' already used by '{seen_new_keys[new_key]}'",
                    )
                )
                continue
            renamed[key] = new_key

        seen_new_keys[new_key] = key
        out_entries.append(EnvEntry(key=new_key, value=entry.value, comment=entry.comment))

    for old_key in rename_map:
        if old_key not in {e.key for e in env.entries} and old_key not in remove_keys_set:
            issues.append(
                MigrationIssue(key=old_key, message="rename source key not found in env file")
            )

    return MigrationResult(
        entries=out_entries,
        issues=issues,
        renamed=renamed,
        removed=removed,
    )
