"""Promote .env values from one environment to another with conflict detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile


@dataclass
class PromoteIssue:
    key: str
    reason: str
    overwritten: bool = False

    def __str__(self) -> str:
        tag = "OVERWRITTEN" if self.overwritten else "SKIPPED"
        return f"[{tag}] {self.key}: {self.reason}"


@dataclass
class PromoteResult:
    promoted: dict = field(default_factory=dict)
    issues: List[PromoteIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return all(not i.overwritten for i in self.issues)

    def __str__(self) -> str:
        if not self.issues:
            return f"Promoted {len(self.promoted)} key(s) with no conflicts."
        lines = [f"Promoted {len(self.promoted)} key(s):"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def promote(
    source: EnvFile,
    target: EnvFile,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    exclude: Optional[List[str]] = None,
) -> PromoteResult:
    """Promote selected keys from source into target.

    Args:
        source: The environment to pull values from.
        target: The environment to push values into.
        keys: Explicit list of keys to promote; if None, all source keys are used.
        overwrite: Whether to overwrite keys that already exist in target.
        exclude: Keys to skip even if they appear in `keys` or source.

    Returns:
        PromoteResult with merged values and any issues encountered.
    """
    exclude_set = set(exclude or [])
    candidate_keys = keys if keys is not None else [e.key for e in source.entries]

    source_dict = {e.key: e.value for e in source.entries}
    target_dict = {e.key: e.value for e in target.entries}

    promoted: dict = dict(target_dict)
    issues: List[PromoteIssue] = []

    for key in candidate_keys:
        if key in exclude_set:
            continue
        if key not in source_dict:
            issues.append(PromoteIssue(key=key, reason="key not found in source"))
            continue
        if key in target_dict:
            if overwrite:
                promoted[key] = source_dict[key]
                issues.append(
                    PromoteIssue(key=key, reason="existed in target; overwritten", overwritten=True)
                )
            else:
                issues.append(PromoteIssue(key=key, reason="already exists in target; skipped"))
        else:
            promoted[key] = source_dict[key]

    return PromoteResult(promoted=promoted, issues=issues)
