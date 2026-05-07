"""Variable interpolation support for .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile

_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationIssue:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] references '${self.ref}': {self.message}"


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    issues: List[InterpolationIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Interpolation OK"
        lines = ["Interpolation issues:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def interpolate(env_file: EnvFile, external: Optional[Dict[str, str]] = None) -> InterpolationResult:
    """Resolve variable references within an EnvFile.

    Values may reference other keys via ${VAR} or $VAR syntax.
    ``external`` provides additional variables (e.g. OS environment).
    """
    base: Dict[str, str] = dict(external or {})
    # Seed with literal values first so forward-references can partially resolve.
    for entry in env_file.entries:
        if entry.key and not entry.is_comment and entry.value is not None:
            base[entry.key] = entry.value

    resolved: Dict[str, str] = {}
    issues: List[InterpolationIssue] = []

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None or entry.value is None:
            continue

        value = entry.value
        missing: List[str] = []

        def _replace(m: re.Match) -> str:  # noqa: E731
            ref = m.group(1) or m.group(2)
            if ref in base:
                return base[ref]
            missing.append(ref)
            return m.group(0)

        interpolated = _VAR_RE.sub(_replace, value)
        resolved[entry.key] = interpolated

        for ref in missing:
            issues.append(
                InterpolationIssue(
                    key=entry.key,
                    ref=ref,
                    message=f"variable '${ref}' is not defined",
                )
            )

    return InterpolationResult(resolved=resolved, issues=issues)
