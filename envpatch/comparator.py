"""Compare two .env files across environments and produce a structured summary."""

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile, as_dict
from envpatch.differ import diff, DiffResult, ChangeType


@dataclass
class CompareResult:
    source_path: str
    target_path: str
    diff: DiffResult
    only_in_source: List[str] = field(default_factory=list)
    only_in_target: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return (
            not self.only_in_source
            and not self.only_in_target
            and not self.modified
        )

    def summary(self) -> str:
        lines = [
            f"Comparing: {self.source_path} -> {self.target_path}",
            f"  Only in source : {len(self.only_in_source)}",
            f"  Only in target : {len(self.only_in_target)}",
            f"  Modified       : {len(self.modified)}",
            f"  Unchanged      : {len(self.common)}",
        ]
        if self.is_identical:
            lines.append("  Result         : identical")
        else:
            lines.append("  Result         : differs")
        return "\n".join(lines)


def compare(source: EnvFile, target: EnvFile) -> CompareResult:
    """Diff source against target and categorise every key."""
    result = diff(source, target)

    only_in_source: List[str] = []
    only_in_target: List[str] = []
    modified: List[str] = []
    common: List[str] = []

    for entry in result.entries:
        if entry.change == ChangeType.ADDED:
            only_in_target.append(entry.key)
        elif entry.change == ChangeType.REMOVED:
            only_in_source.append(entry.key)
        elif entry.change == ChangeType.MODIFIED:
            modified.append(entry.key)
        else:
            common.append(entry.key)

    return CompareResult(
        source_path=source.path or "<source>",
        target_path=target.path or "<target>",
        diff=result,
        only_in_source=only_in_source,
        only_in_target=only_in_target,
        modified=modified,
        common=common,
    )
