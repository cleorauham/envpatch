"""Normalize .env file entries: trim whitespace, fix quoting, uppercase keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class NormalizeIssue:
    key: str
    original: str
    normalized: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason} ({self.original!r} -> {self.normalized!r})"


@dataclass
class NormalizeResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[NormalizeIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "No normalization changes."
        lines = [f"  - {issue}" for issue in self.issues]
        return "Normalization changes:\n" + "\n".join(lines)


def _normalize_key(key: str) -> str:
    return key.strip().upper()


def _normalize_value(value: str) -> str:
    stripped = value.strip()
    # Remove redundant outer quotes of mismatched or unnecessary pairs
    if len(stripped) >= 2:
        for q in ('"', "'"):
            if stripped.startswith(q) and stripped.endswith(q):
                inner = stripped[1:-1]
                # Keep quotes only if inner contains spaces or special chars
                if not any(c in inner for c in (" ", "#", "=", "$")):
                    return inner
    return stripped


def normalize(env: EnvFile) -> NormalizeResult:
    """Return a NormalizeResult with cleaned entries and a list of changes made."""
    result = NormalizeResult()

    for entry in env.entries:
        norm_key = _normalize_key(entry.key)
        norm_value = _normalize_value(entry.value)

        reasons = []
        if norm_key != entry.key:
            reasons.append("key uppercased/trimmed")
        if norm_value != entry.value:
            reasons.append("value trimmed/unquoted")

        if reasons:
            issue = NormalizeIssue(
                key=entry.key,
                original=f"{entry.key}={entry.value}",
                normalized=f"{norm_key}={norm_value}",
                reason="; ".join(reasons),
            )
            result.issues.append(issue)

        result.entries.append(EnvEntry(key=norm_key, value=norm_value, comment=entry.comment))

    return result
