"""Lint .env files for style and convention issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile


class LintSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    key: str
    message: str
    severity: LintSeverity
    line: int = 0

    def __str__(self) -> str:
        loc = f"line {self.line}: " if self.line else ""
        return f"[{self.severity.value.upper()}] {loc}{self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(i.severity == LintSeverity.ERROR for i in self.issues)

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    def __str__(self) -> str:
        if not self.issues:
            return "Lint passed: no issues found."
        lines = [str(i) for i in self.issues]
        return "\n".join(lines)


_UPPER_SNAKE_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def lint(env_file: EnvFile) -> LintResult:
    """Run all lint checks on an EnvFile and return a LintResult."""
    issues: List[LintIssue] = []
    seen_keys: dict[str, int] = {}

    for entry in env_file.entries:
        if entry.key is None:
            continue

        key = entry.key
        line = entry.line_number

        # Check for duplicate keys
        if key in seen_keys:
            issues.append(LintIssue(
                key=key,
                message=f"duplicate key (first seen at line {seen_keys[key]})",
                severity=LintSeverity.ERROR,
                line=line,
            ))
        else:
            seen_keys[key] = line

        # Check key naming convention (UPPER_SNAKE_CASE)
        if not all(c in _UPPER_SNAKE_CHARS for c in key):
            issues.append(LintIssue(
                key=key,
                message="key should use UPPER_SNAKE_CASE",
                severity=LintSeverity.WARNING,
                line=line,
            ))

        # Check for keys starting with a digit
        if key and key[0].isdigit():
            issues.append(LintIssue(
                key=key,
                message="key must not start with a digit",
                severity=LintSeverity.ERROR,
                line=line,
            ))

        # Warn about very long values (potential accidental paste)
        value = entry.value or ""
        if len(value) > 512:
            issues.append(LintIssue(
                key=key,
                message=f"value is unusually long ({len(value)} chars)",
                severity=LintSeverity.WARNING,
                line=line,
            ))

    return LintResult(issues=issues)
