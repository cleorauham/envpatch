"""Snapshot utilities: capture and compare .env file states over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, as_dict


@dataclass
class Snapshot:
    """A point-in-time capture of an .env file's key-value pairs."""

    source: str
    captured_at: str
    entries: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "entries": self.entries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            source=data["source"],
            captured_at=data["captured_at"],
            entries=data.get("entries", {}),
        )


def capture(env_file: EnvFile, source: str = "") -> Snapshot:
    """Create a Snapshot from a parsed EnvFile."""
    now = datetime.now(timezone.utc).isoformat()
    return Snapshot(
        source=source or env_file.path or "<unknown>",
        captured_at=now,
        entries=as_dict(env_file),
    )


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)
        fh.write("\n")


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def diff_snapshots(old: Snapshot, new: Snapshot) -> Dict[str, dict]:
    """Return a mapping of changed keys between two snapshots.

    Each value is a dict with 'old' and 'new' fields.  Only keys whose
    values differ (or that were added / removed) are included.
    """
    all_keys = set(old.entries) | set(new.entries)
    changes: Dict[str, dict] = {}
    for key in sorted(all_keys):
        old_val = old.entries.get(key)
        new_val = new.entries.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes
