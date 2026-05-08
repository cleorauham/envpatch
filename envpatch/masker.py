"""Mask sensitive values in an env file for safe display or logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile, EnvEntry

_SENSITIVE_FRAGMENTS = ("secret", "password", "passwd", "token", "key", "api", "auth", "private", "credential")
_DEFAULT_MASK = "***"
_PARTIAL_REVEAL = 2  # characters to reveal at start/end for partial mode


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(frag in lower for frag in _SENSITIVE_FRAGMENTS)


@dataclass
class MaskedEntry:
    original: EnvEntry
    masked_value: str
    was_masked: bool

    @property
    def key(self) -> str:
        return self.original.key

    @property
    def value(self) -> str:
        return self.masked_value

    def __str__(self) -> str:
        return f"{self.key}={self.masked_value}"


@dataclass
class MaskResult:
    entries: List[MaskedEntry] = field(default_factory=list)

    @property
    def masked_count(self) -> int:
        return sum(1 for e in self.entries if e.was_masked)

    def __str__(self) -> str:
        lines = [str(e) for e in self.entries]
        return "\n".join(lines)


def mask(
    env: EnvFile,
    *,
    partial: bool = False,
    mask_char: str = _DEFAULT_MASK,
) -> MaskResult:
    """Return a MaskResult where sensitive values are replaced with a mask.

    Args:
        env: Parsed EnvFile to process.
        partial: If True, reveal the first and last characters of the value.
        mask_char: The string used as the mask token.
    """
    result = MaskResult()
    for entry in env.entries:
        if _is_sensitive(entry.key) and entry.value:
            if partial and len(entry.value) > _PARTIAL_REVEAL * 2:
                masked = entry.value[:_PARTIAL_REVEAL] + mask_char + entry.value[-_PARTIAL_REVEAL:]
            else:
                masked = mask_char
            result.entries.append(MaskedEntry(original=entry, masked_value=masked, was_masked=True))
        else:
            result.entries.append(MaskedEntry(original=entry, masked_value=entry.value, was_masked=False))
    return result
