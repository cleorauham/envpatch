"""Auditor module: checks .env files for common security and hygiene issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile

_SENSITIVE_PATTERNS = re.compile(
    r"(secret|password|passwd|pwd|token|api_key|apikey|private_key|auth)",
    re.IGNORECASE,
)

_PLACEHOLDER_VALUES = {"changeme", "todo", "fixme", "placeholder", "example", "xxx", "your_value_here"}


@dataclass
class AuditIssue:
    key: str
    message: str
    severity: str  # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class AuditResult:
    issues: List[AuditIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def __str__(self) -> str:
        if self.is_clean:
            return "Audit passed: no issues found."
        lines = [str(issue) for issue in self.issues]
        return "\n".join(lines)


def audit(env_file: EnvFile) -> AuditResult:
    """Run security and hygiene checks on an EnvFile."""
    issues: List[AuditIssue] = []

    for entry in env_file.entries:
        if entry.key is None:
            continue

        key = entry.key
        value = entry.value or ""

        # Check for sensitive key with empty value
        if _SENSITIVE_PATTERNS.search(key) and value.strip() == "":
            issues.append(AuditIssue(
                key=key,
                message="Sensitive key has an empty value.",
                severity="error",
            ))

        # Check for placeholder values in sensitive keys
        if _SENSITIVE_PATTERNS.search(key) and value.strip().lower() in _PLACEHOLDER_VALUES:
            issues.append(AuditIssue(
                key=key,
                message=f"Sensitive key appears to contain a placeholder value: {value!r}.",
                severity="error",
            ))

        # Check for keys with no value at all (not sensitive)
        if not _SENSITIVE_PATTERNS.search(key) and value.strip() == "":
            issues.append(AuditIssue(
                key=key,
                message="Key has an empty value.",
                severity="warning",
            ))

        # Check for overly long values that might be accidental pastes
        if len(value) > 500:
            issues.append(AuditIssue(
                key=key,
                message=f"Value is unusually long ({len(value)} chars); verify it is correct.",
                severity="warning",
            ))

    return AuditResult(issues=issues)
