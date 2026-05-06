"""Parser for .env files — handles reading and tokenizing key-value pairs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$"
)


@dataclass
class EnvEntry:
    """Represents a single key-value entry in a .env file."""

    key: str
    value: str
    comment: Optional[str] = None  # inline comment stripped from value
    line_number: int = 0


@dataclass
class EnvFile:
    """Parsed representation of a .env file."""

    entries: List[EnvEntry] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}


def _strip_inline_comment(value: str) -> tuple[str, Optional[str]]:
    """Split value from an optional inline comment."""
    # Only strip unquoted inline comments
    if value.startswith(("'", '"')):
        quote = value[0]
        end = value.find(quote, 1)
        if end != -1:
            return value[1:end], None
    comment_idx = value.find(" #")
    if comment_idx != -1:
        return value[:comment_idx].strip(), value[comment_idx + 1:].strip()
    return value.strip(), None


def parse(text: str) -> EnvFile:
    """Parse the contents of a .env file into an EnvFile object."""
    env_file = EnvFile()
    for lineno, raw in enumerate(text.splitlines(), start=1):
        env_file.raw_lines.append(raw)
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _LINE_RE.match(stripped)
        if match:
            key = match.group("key")
            raw_value = match.group("value")
            value, comment = _strip_inline_comment(raw_value)
            env_file.entries.append(
                EnvEntry(key=key, value=value, comment=comment, line_number=lineno)
            )
    return env_file


def parse_file(path: str) -> EnvFile:
    """Read and parse a .env file from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())
