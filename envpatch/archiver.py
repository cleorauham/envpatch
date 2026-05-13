"""Archive (backup) an .env file with a timestamped copy."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ArchiveEntry:
    source: Path
    destination: Path
    timestamp: datetime

    def __str__(self) -> str:
        return (
            f"Archived {self.source} -> {self.destination} "
            f"at {self.timestamp.isoformat()}"
        )


@dataclass
class ArchiveResult:
    entries: list[ArchiveEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        if not self.is_clean:
            lines = ["Archive completed with errors:"]
            lines += [f"  ERROR: {e}" for e in self.errors]
            return "\n".join(lines)
        if not self.entries:
            return "Nothing archived."
        lines = ["Archive summary:"]
        lines += [f"  {entry}" for entry in self.entries]
        return "\n".join(lines)


def _build_destination(source: Path, archive_dir: Path, timestamp: datetime) -> Path:
    stamp = timestamp.strftime("%Y%m%dT%H%M%S")
    name = f"{source.stem}_{stamp}{source.suffix}"
    return archive_dir / name


def archive(
    paths: list[Path],
    archive_dir: Optional[Path] = None,
    *,
    timestamp: Optional[datetime] = None,
) -> ArchiveResult:
    """Copy each *path* into *archive_dir* with a timestamped filename."""
    if archive_dir is None:
        archive_dir = Path(".env_archive")

    now = timestamp or datetime.now(tz=timezone.utc)
    result = ArchiveResult()

    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result.errors.append(f"Cannot create archive directory '{archive_dir}': {exc}")
        return result

    for source in paths:
        if not source.exists():
            result.errors.append(f"Source file not found: {source}")
            continue
        destination = _build_destination(source, archive_dir, now)
        try:
            shutil.copy2(source, destination)
            result.entries.append(ArchiveEntry(source=source, destination=destination, timestamp=now))
        except OSError as exc:
            result.errors.append(f"Failed to archive '{source}': {exc}")

    return result
