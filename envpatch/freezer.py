"""Freeze an env file into a locked snapshot with checksums for drift detection."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envpatch.parser import EnvFile


@dataclass
class FreezeEntry:
    key: str
    checksum: str  # SHA-256 of value

    def __str__(self) -> str:
        return f"{self.key}={self.checksum[:12]}..."


@dataclass
class FreezeViolation:
    key: str
    reason: str  # 'missing' | 'modified' | 'extra'

    def __str__(self) -> str:
        return f"[{self.reason.upper()}] {self.key}"


@dataclass
class FreezeResult:
    entries: List[FreezeEntry] = field(default_factory=list)
    violations: List[FreezeViolation] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Freeze check passed — no drift detected."
        lines = ["Freeze violations detected:"]
        for v in self.violations:
            lines.append(f"  {v}")
        return "\n".join(lines)


def _checksum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def freeze(env: EnvFile) -> FreezeResult:
    """Produce a FreezeResult containing a checksum entry for every key."""
    entries = [
        FreezeEntry(key=e.key, checksum=_checksum(e.value))
        for e in env.entries
        if not e.is_comment and not e.is_blank
    ]
    return FreezeResult(entries=entries)


def save_freeze(result: FreezeResult, path: Path) -> None:
    """Persist freeze entries to a JSON lock file."""
    data = {e.key: e.checksum for e in result.entries}
    path.write_text(json.dumps(data, indent=2))


def load_freeze(path: Path) -> Dict[str, str]:
    """Load a previously saved freeze lock file."""
    return json.loads(path.read_text())


def verify_freeze(
    env: EnvFile,
    lock: Dict[str, str],
    allow_extra: bool = False,
) -> FreezeResult:
    """Compare *env* against a previously saved *lock* dict."""
    current: Dict[str, str] = {
        e.key: _checksum(e.value)
        for e in env.entries
        if not e.is_comment and not e.is_blank
    }
    violations: List[FreezeViolation] = []

    for key, locked_cs in lock.items():
        if key not in current:
            violations.append(FreezeViolation(key=key, reason="missing"))
        elif current[key] != locked_cs:
            violations.append(FreezeViolation(key=key, reason="modified"))

    if not allow_extra:
        for key in current:
            if key not in lock:
                violations.append(FreezeViolation(key=key, reason="extra"))

    entries = [FreezeEntry(key=k, checksum=cs) for k, cs in current.items()]
    return FreezeResult(entries=entries, violations=violations)
