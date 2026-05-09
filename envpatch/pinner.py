"""Pin current env values to a lockfile for drift detection."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envpatch.parser import EnvFile


@dataclass
class PinEntry:
    key: str
    checksum: str  # sha256 of the value

    def __str__(self) -> str:
        return f"{self.key}={self.checksum[:12]}..."


@dataclass
class PinResult:
    entries: List[PinEntry] = field(default_factory=list)
    drifted: List[str] = field(default_factory=list)  # keys whose checksums changed
    missing: List[str] = field(default_factory=list)  # keys in lock but not in env
    added: List[str] = field(default_factory=list)    # keys in env but not in lock

    def is_clean(self) -> bool:
        return not self.drifted and not self.missing and not self.added

    def __str__(self) -> str:
        if self.is_clean():
            return "Pin result: no drift detected."
        lines = ["Pin result: drift detected."]
        for k in self.drifted:
            lines.append(f"  ~ {k} (value changed)")
        for k in self.missing:
            lines.append(f"  - {k} (removed from env)")
        for k in self.added:
            lines.append(f"  + {k} (new in env)")
        return "\n".join(lines)


def _checksum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def pin(env: EnvFile) -> PinResult:
    """Create a PinResult capturing checksums for all entries."""
    entries = [
        PinEntry(key=e.key, checksum=_checksum(e.value or ""))
        for e in env.entries
        if e.key is not None
    ]
    return PinResult(entries=entries)


def compare_pin(env: EnvFile, lock: Dict[str, str]) -> PinResult:
    """Compare current env values against a previously saved lockfile dict."""
    current: Dict[str, str] = {
        e.key: _checksum(e.value or "")
        for e in env.entries
        if e.key is not None
    }
    drifted = [k for k in lock if k in current and current[k] != lock[k]]
    missing = [k for k in lock if k not in current]
    added = [k for k in current if k not in lock]
    entries = [PinEntry(key=k, checksum=v) for k, v in current.items()]
    return PinResult(entries=entries, drifted=drifted, missing=missing, added=added)


def save_pin(result: PinResult, path: Path) -> None:
    data = {e.key: e.checksum for e in result.entries}
    path.write_text(json.dumps(data, indent=2))


def load_pin(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())
