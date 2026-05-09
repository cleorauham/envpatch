"""Deprecation tracker: flags keys that are marked as deprecated via a registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile

# Built-in set of commonly deprecated / legacy key names
_BUILTIN_DEPRECATED: Dict[str, str] = {
    "SECRET_KEY_BASE": "Use APP_SECRET_KEY instead",
    "DATABASE_URL_OLD": "Use DATABASE_URL instead",
    "REDIS_URL_LEGACY": "Use REDIS_URL instead",
    "MAIL_HOST": "Use SMTP_HOST instead",
    "MAIL_PORT": "Use SMTP_PORT instead",
    "S3_ACCESS_KEY": "Use AWS_ACCESS_KEY_ID instead",
    "S3_SECRET_KEY": "Use AWS_SECRET_ACCESS_KEY instead",
}


@dataclass
class DeprecationIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class DeprecationResult:
    issues: List[DeprecationIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "No deprecated keys found."
        lines = ["Deprecated keys detected:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def check_deprecations(
    env: EnvFile,
    extra_deprecated: Optional[Dict[str, str]] = None,
) -> DeprecationResult:
    """Check *env* for deprecated key names.

    Args:
        env: Parsed environment file to inspect.
        extra_deprecated: Optional caller-supplied mapping of key -> reason
            that is merged with (and may override) the built-in registry.

    Returns:
        A :class:`DeprecationResult` containing any issues found.
    """
    registry: Dict[str, str] = {**_BUILTIN_DEPRECATED}
    if extra_deprecated:
        registry.update(extra_deprecated)

    issues: List[DeprecationIssue] = []
    for entry in env.entries:
        if entry.key is None:
            continue
        normalised = entry.key.strip().upper()
        if normalised in registry:
            issues.append(DeprecationIssue(key=entry.key, reason=registry[normalised]))

    return DeprecationResult(issues=issues)
