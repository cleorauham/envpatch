"""Tag .env entries with arbitrary labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from envpatch.parser import EnvFile


@dataclass
class TagIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class TagResult:
    tagged: Dict[str, FrozenSet[str]] = field(default_factory=dict)
    issues: List[TagIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def tags_for(self, key: str) -> FrozenSet[str]:
        return self.tagged.get(key, frozenset())

    def keys_with_tag(self, tag: str) -> List[str]:
        return [k for k, tags in self.tagged.items() if tag in tags]

    def __str__(self) -> str:
        if not self.tagged:
            return "No tagged entries."
        lines = []
        for key, tags in sorted(self.tagged.items()):
            tag_str = ", ".join(sorted(tags))
            lines.append(f"  {key}: [{tag_str}]")
        return "\n".join(lines)


def tag_entries(
    env: EnvFile,
    tag_map: Dict[str, List[str]],
    strict: bool = False,
) -> TagResult:
    """Apply tags to env entries based on *tag_map* {tag: [key, ...]}.

    Args:
        env: Parsed env file.
        tag_map: Mapping of tag name to list of keys that should carry it.
        strict: When True, referencing a key not present in *env* creates an issue.

    Returns:
        TagResult with per-key tag sets and any issues found.
    """
    existing_keys = {e.key for e in env.entries if e.key is not None}
    result: Dict[str, set] = {}
    issues: List[TagIssue] = []

    for tag, keys in tag_map.items():
        if not isinstance(keys, list):
            issues.append(TagIssue(key=tag, message="tag value must be a list of keys"))
            continue
        for key in keys:
            if strict and key not in existing_keys:
                issues.append(TagIssue(key=key, message=f"key not found in env (tag: '{tag}')"))
                continue
            result.setdefault(key, set()).add(tag)

    frozen: Dict[str, FrozenSet[str]] = {k: frozenset(v) for k, v in result.items()}
    return TagResult(tagged=frozen, issues=issues)
