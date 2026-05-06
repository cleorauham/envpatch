"""Validation utilities for .env files and merge results."""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from envpatch.parser import EnvFile
from envpatch.merger import MergeResult

_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


@dataclass
class ValidationIssue:
    line: int
    key: Optional[str]
    message: str

    def __str__(self) -> str:
        location = f"line {self.line}" if self.line >= 0 else "(unknown line)"
        key_info = f" [{self.key}]" if self.key else ""
        return f"{location}{key_info}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return "No validation issues found."
        lines = [f"{len(self.issues)} issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def validate_env_file(env_file: EnvFile) -> ValidationResult:
    """Validate keys and values in a parsed EnvFile."""
    result = ValidationResult()
    seen_keys: dict = {}

    for entry in env_file.entries:
        if entry.key is None:
            continue

        line = entry.line_number if entry.line_number is not None else -1

        if not _VALID_KEY_RE.match(entry.key):
            result.issues.append(ValidationIssue(
                line=line,
                key=entry.key,
                message=f"Invalid key name '{entry.key}'; must match [A-Za-z_][A-Za-z0-9_]*"
            ))

        if entry.key in seen_keys:
            result.issues.append(ValidationIssue(
                line=line,
                key=entry.key,
                message=f"Duplicate key '{entry.key}' (first seen at line {seen_keys[entry.key]})"
            ))
        else:
            seen_keys[entry.key] = line

        if entry.value is not None and '\n' in entry.value:
            result.issues.append(ValidationIssue(
                line=line,
                key=entry.key,
                message="Value contains unescaped newline"
            ))

    return result


def validate_merge_result(merge_result: MergeResult) -> ValidationResult:
    """Validate that a merge result has no unresolved conflicts."""
    result = ValidationResult()
    if merge_result.has_conflicts:
        for conflict in merge_result.conflicts:
            result.issues.append(ValidationIssue(
                line=-1,
                key=conflict.key,
                message=(
                    f"Unresolved conflict: base='{conflict.base_value}', "
                    f"incoming='{conflict.incoming_value}'"
                )
            ))
    return result
