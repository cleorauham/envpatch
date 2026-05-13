"""Transform .env entries by applying a set of named transformations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class TransformIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class TransformResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[TransformIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Transform complete — no issues."
        lines = ["Transform issues:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


TransformFn = Callable[[str, str], Optional[str]]

_BUILTIN_TRANSFORMS: Dict[str, TransformFn] = {
    "uppercase_keys": lambda k, v: None,  # handled structurally
    "strip_values": lambda k, v: v.strip(),
    "lowercase_values": lambda k, v: v.lower(),
    "uppercase_values": lambda k, v: v.upper(),
    "quote_values": lambda k, v: f'"{v}"' if not (v.startswith('"') and v.endswith('"')) else v,
    "unquote_values": lambda k, v: v.strip('"').strip("'"),
}


def _resolve_transform(name: str) -> Optional[TransformFn]:
    return _BUILTIN_TRANSFORMS.get(name)


def transform(env: EnvFile, transform_names: List[str]) -> TransformResult:
    """Apply named transforms to all key-value entries in *env*."""
    result = TransformResult()

    fns: List[TransformFn] = []
    for name in transform_names:
        fn = _resolve_transform(name)
        if fn is None:
            result.issues.append(TransformIssue("*", f"Unknown transform: '{name}'"))
        else:
            fns.append(fn)

    for entry in env.entries:
        if entry.key is None:
            result.entries.append(entry)
            continue
        key = entry.key
        value = entry.value or ""

        if "uppercase_keys" in transform_names:
            key = key.upper()

        for fn in fns:
            new_value = fn(key, value)
            if new_value is not None:
                value = new_value

        result.entries.append(EnvEntry(key=key, value=value, comment=entry.comment, raw=entry.raw))

    return result
