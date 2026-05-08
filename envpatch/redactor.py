"""Redactor: mask sensitive values in an EnvFile for safe display or export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envpatch.parser import EnvEntry, EnvFile

_DEFAULT_SENSITIVE_PATTERNS: Set[str] = {
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "AUTH",
    "CREDENTIAL",
    "DSN",
    "DATABASE_URL",
}

_REDACTED_PLACEHOLDER = "***REDACTED***"


def _is_sensitive(key: str, patterns: Set[str]) -> bool:
    upper = key.upper()
    return any(pat in upper for pat in patterns)


@dataclass
class RedactedEntry:
    original: EnvEntry
    redacted: bool

    @property
    def key(self) -> str:
        return self.original.key

    @property
    def value(self) -> str:
        return _REDACTED_PLACEHOLDER if self.redacted else (self.original.value or "")

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


@dataclass
class RedactResult:
    entries: List[RedactedEntry] = field(default_factory=list)

    @property
    def redacted_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.redacted]

    def as_env_lines(self) -> List[str]:
        return [str(e) for e in self.entries]

    def __str__(self) -> str:
        return "\n".join(self.as_env_lines())


def redact(
    env: EnvFile,
    extra_patterns: Set[str] | None = None,
    patterns: Set[str] | None = None,
) -> RedactResult:
    """Return a RedactResult with sensitive values masked.

    Args:
        env: Parsed EnvFile to redact.
        extra_patterns: Additional substrings to treat as sensitive.
        patterns: Override the full set of sensitive patterns.
    """
    active_patterns: Set[str]
    if patterns is not None:
        active_patterns = {p.upper() for p in patterns}
    else:
        active_patterns = set(_DEFAULT_SENSITIVE_PATTERNS)
        if extra_patterns:
            active_patterns |= {p.upper() for p in extra_patterns}

    result_entries: List[RedactedEntry] = []
    for entry in env.entries:
        sensitive = _is_sensitive(entry.key, active_patterns)
        result_entries.append(RedactedEntry(original=entry, redacted=sensitive))

    return RedactResult(entries=result_entries)
