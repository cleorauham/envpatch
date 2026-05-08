"""Scanner: detect keys in an .env file that match known pattern categories."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile


class PatternCategory(str, Enum):
    SECRET = "secret"
    URL = "url"
    PATH = "path"
    FLAG = "flag"
    UNKNOWN = "unknown"


_SECRET_FRAGMENTS = ("secret", "password", "passwd", "token", "api_key", "apikey", "private_key", "auth")
_URL_FRAGMENTS = ("url", "uri", "endpoint", "host", "dsn", "database_url")
_PATH_FRAGMENTS = ("path", "dir", "directory", "file", "root", "home")
_FLAG_FRAGMENTS = ("enable", "disable", "flag", "feature", "debug", "verbose", "active")


def _categorise(key: str) -> PatternCategory:
    lower = key.lower()
    if any(f in lower for f in _SECRET_FRAGMENTS):
        return PatternCategory.SECRET
    if any(f in lower for f in _URL_FRAGMENTS):
        return PatternCategory.URL
    if any(f in lower for f in _PATH_FRAGMENTS):
        return PatternCategory.PATH
    if any(f in lower for f in _FLAG_FRAGMENTS):
        return PatternCategory.FLAG
    return PatternCategory.UNKNOWN


@dataclass
class ScanEntry:
    key: str
    value: str
    category: PatternCategory

    def __str__(self) -> str:
        return f"[{self.category.value.upper()}] {self.key}"


@dataclass
class ScanResult:
    entries: List[ScanEntry] = field(default_factory=list)

    def by_category(self, category: PatternCategory) -> List[ScanEntry]:
        return [e for e in self.entries if e.category == category]

    def summary(self) -> str:
        counts: dict[str, int] = {}
        for e in self.entries:
            counts[e.category.value] = counts.get(e.category.value, 0) + 1
        if not counts:
            return "No entries scanned."
        parts = ", ".join(f"{cat}: {n}" for cat, n in sorted(counts.items()))
        return f"Scan summary — {parts}"


def scan(env: EnvFile) -> ScanResult:
    """Categorise every entry in *env* by key-name pattern."""
    entries = [
        ScanEntry(key=e.key, value=e.value or "", category=_categorise(e.key))
        for e in env.entries
        if e.key is not None
    ]
    return ScanResult(entries=entries)
