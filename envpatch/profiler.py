"""Profile .env files against named environment profiles (e.g. dev, staging, prod)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from envpatch.parser import EnvFile


@dataclass
class ProfileIssue:
    key: str
    message: str
    profile: str

    def __str__(self) -> str:
        return f"[{self.profile}] {self.key}: {self.message}"


@dataclass
class ProfileResult:
    profile: str
    issues: List[ProfileIssue] = field(default_factory=list)

    def is_compliant(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_compliant():
            return f"Profile '{self.profile}': compliant"
        lines = [f"Profile '{self.profile}': {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


# Built-in profile rules: maps profile name -> required keys
_PROFILE_REQUIRED_KEYS: Dict[str, Set[str]] = {
    "production": {"DATABASE_URL", "SECRET_KEY", "ALLOWED_HOSTS"},
    "staging": {"DATABASE_URL", "SECRET_KEY"},
    "development": set(),
}


def check_profile(
    env_file: EnvFile,
    profile: str,
    required_keys: Optional[Set[str]] = None,
) -> ProfileResult:
    """Check an EnvFile against a named profile's required keys."""
    result = ProfileResult(profile=profile)

    if required_keys is None:
        required_keys = _PROFILE_REQUIRED_KEYS.get(profile, set())

    present_keys = {entry.key for entry in env_file.entries if not entry.is_comment and not entry.is_blank}

    for key in sorted(required_keys):
        if key not in present_keys:
            result.issues.append(
                ProfileIssue(key=key, message="required key is missing", profile=profile)
            )
        else:
            matching = [e for e in env_file.entries if e.key == key]
            if matching and not matching[0].value:
                result.issues.append(
                    ProfileIssue(key=key, message="required key has empty value", profile=profile)
                )

    return result


def available_profiles() -> List[str]:
    """Return the list of built-in profile names."""
    return list(_PROFILE_REQUIRED_KEYS.keys())
