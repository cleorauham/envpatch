"""Sanitize .env file values by removing control characters and enforcing safe encoding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvEntry, EnvFile

_CONTROL_CHARS = set(range(0, 32)) - {9, 10, 13}  # allow tab, LF, CR


@dataclass
class SanitizeIssue:
    key: str
    original: str
    sanitized: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason} (was {self.original!r}, now {self.sanitized!r})"


@dataclass
class SanitizeResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[SanitizeIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Sanitize: no issues found."
        lines = ["Sanitize issues:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def _remove_control_chars(value: str) -> tuple[str, bool]:
    cleaned = "".join(ch for ch in value if ord(ch) not in _CONTROL_CHARS)
    return cleaned, cleaned != value


def _strip_null_bytes(value: str) -> tuple[str, bool]:
    cleaned = value.replace("\x00", "")
    return cleaned, cleaned != value


def sanitize(env: EnvFile) -> SanitizeResult:
    """Return a SanitizeResult with cleaned entries and a list of issues."""
    result_entries: List[EnvEntry] = []
    issues: List[SanitizeIssue] = []

    for entry in env.entries:
        original = entry.value
        value = original

        value, had_nulls = _strip_null_bytes(value)
        if had_nulls:
            issues.append(SanitizeIssue(entry.key, original, value, "null bytes removed"))

        value, had_controls = _remove_control_chars(value)
        if had_controls:
            issues.append(SanitizeIssue(entry.key, original, value, "control characters removed"))

        new_entry = EnvEntry(
            key=entry.key,
            value=value,
            comment=entry.comment,
            raw=entry.raw,
        )
        result_entries.append(new_entry)

    return SanitizeResult(entries=result_entries, issues=issues)
