"""Generate human-readable summary reports from audit, validation, and diff results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.auditor import AuditResult
from envpatch.differ import DiffResult
from envpatch.validator import ValidationResult


@dataclass
class Report:
    title: str
    sections: List[str] = field(default_factory=list)

    def add_section(self, heading: str, lines: List[str]) -> None:
        block = [f"### {heading}"]
        if lines:
            block.extend(lines)
        else:
            block.append("  (none)")
        self.sections.append("\n".join(block))

    def render(self) -> str:
        parts = [f"# {self.title}"]
        parts.extend(self.sections)
        return "\n\n".join(parts)


def report_diff(diff: DiffResult, title: str = "Diff Report") -> Report:
    report = Report(title=title)
    lines = []
    for entry in diff.entries:
        lines.append(f"  [{entry.change_type.value.upper()}] {entry.key}")
    report.add_section("Changes", lines)
    summary = (
        f"  Added: {diff.added_count}  "
        f"Removed: {diff.removed_count}  "
        f"Modified: {diff.modified_count}  "
        f"Unchanged: {diff.unchanged_count}"
    )
    report.add_section("Summary", [summary])
    return report


def report_validation(result: ValidationResult, title: str = "Validation Report") -> Report:
    report = Report(title=title)
    errors = [f"  ERROR  [{i.key}] {i.message}" for i in result.issues if i.severity == "error"]
    warnings = [f"  WARN   [{i.key}] {i.message}" for i in result.issues if i.severity == "warning"]
    report.add_section("Errors", errors)
    report.add_section("Warnings", warnings)
    status = "PASSED" if result.is_valid() else "FAILED"
    report.add_section("Status", [f"  Validation {status}"])
    return report


def report_audit(result: AuditResult, title: str = "Audit Report") -> Report:
    report = Report(title=title)
    errs = [f"  ERROR  [{i.key}] {i.message}" for i in result.issues if i.severity == "error"]
    warns = [f"  WARN   [{i.key}] {i.message}" for i in result.issues if i.severity == "warning"]
    report.add_section("Errors", errs)
    report.add_section("Warnings", warns)
    status = "CLEAN" if result.is_clean() else "ISSUES FOUND"
    report.add_section("Status", [f"  Audit {status}"])
    return report
