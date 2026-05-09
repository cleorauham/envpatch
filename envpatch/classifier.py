"""Classify .env entries into semantic categories based on key patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

from envpatch.parser import EnvFile, EnvEntry


class EntryCategory(str, Enum):
    DATABASE = "database"
    CACHE = "cache"
    AUTH = "auth"
    STORAGE = "storage"
    NETWORK = "network"
    FEATURE_FLAG = "feature_flag"
    LOGGING = "logging"
    OTHER = "other"


_PATTERNS: List[tuple[EntryCategory, tuple[str, ...]]] = [
    (EntryCategory.DATABASE, ("DB_", "DATABASE_", "POSTGRES", "MYSQL", "SQLITE", "MONGO")),
    (EntryCategory.CACHE, ("REDIS_", "CACHE_", "MEMCACHE")),
    (EntryCategory.AUTH, ("AUTH_", "JWT_", "SECRET", "TOKEN", "PASSWORD", "API_KEY")),
    (EntryCategory.STORAGE, ("S3_", "BUCKET_", "STORAGE_", "GCS_", "AZURE_BLOB")),
    (EntryCategory.NETWORK, ("HOST", "PORT", "URL", "ENDPOINT", "DOMAIN", "BASE_URL")),
    (EntryCategory.FEATURE_FLAG, ("FEATURE_", "FLAG_", "ENABLE_", "DISABLE_")),
    (EntryCategory.LOGGING, ("LOG_", "LOGGING_", "SENTRY_", "DATADOG_")),
]


def _classify_key(key: str) -> EntryCategory:
    upper = key.upper()
    for category, patterns in _PATTERNS:
        if any(upper.startswith(p) or p in upper for p in patterns):
            return category
    return EntryCategory.OTHER


@dataclass
class ClassifiedEntry:
    entry: EnvEntry
    category: EntryCategory

    def __str__(self) -> str:
        return f"[{self.category.value}] {self.entry.key}={self.entry.value}"


@dataclass
class ClassifyResult:
    entries: List[ClassifiedEntry] = field(default_factory=list)

    def by_category(self) -> Dict[EntryCategory, List[ClassifiedEntry]]:
        result: Dict[EntryCategory, List[ClassifiedEntry]] = {}
        for ce in self.entries:
            result.setdefault(ce.category, []).append(ce)
        return result

    def categories_present(self) -> List[EntryCategory]:
        return list({ce.category for ce in self.entries})

    def __str__(self) -> str:
        grouped = self.by_category()
        lines = []
        for cat, items in sorted(grouped.items(), key=lambda x: x[0].value):
            lines.append(f"[{cat.value}] ({len(items)} entries)")
        return "\n".join(lines) if lines else "No entries classified."


def classify(env: EnvFile) -> ClassifyResult:
    """Classify all entries in an EnvFile by semantic category."""
    classified = [
        ClassifiedEntry(entry=e, category=_classify_key(e.key))
        for e in env.entries
        if e.key is not None
    ]
    return ClassifyResult(entries=classified)
