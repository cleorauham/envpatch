"""Tests for envpatch.reporter."""
from __future__ import annotations

import pytest

from envpatch.auditor import AuditIssue, AuditResult
from envpatch.differ import ChangeType, DiffEntry, DiffResult
from envpatch.reporter import Report, report_audit, report_diff, report_validation
from envpatch.validator import ValidationIssue, ValidationResult


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

def test_report_render_no_sections():
    r = Report(title="Empty")
    assert r.render() == "# Empty"


def test_report_add_section_with_lines():
    r = Report(title="T")
    r.add_section("Heading", ["line1", "line2"])
    rendered = r.render()
    assert "### Heading" in rendered
    assert "line1" in rendered


def test_report_add_section_empty_lines():
    r = Report(title="T")
    r.add_section("Empty Section", [])
    assert "(none)" in r.render()


# ---------------------------------------------------------------------------
# report_diff
# ---------------------------------------------------------------------------

def _make_diff_result():
    entries = [
        DiffEntry(key="A", change_type=ChangeType.ADDED, old_value=None, new_value="1"),
        DiffEntry(key="B", change_type=ChangeType.REMOVED, old_value="x", new_value=None),
        DiffEntry(key="C", change_type=ChangeType.UNCHANGED, old_value="v", new_value="v"),
    ]
    return DiffResult(entries=entries)


def test_report_diff_contains_keys():
    report = report_diff(_make_diff_result())
    rendered = report.render()
    assert "A" in rendered
    assert "B" in rendered
    assert "C" in rendered


def test_report_diff_summary_counts():
    report = report_diff(_make_diff_result())
    rendered = report.render()
    assert "Added: 1" in rendered
    assert "Removed: 1" in rendered
    assert "Unchanged: 1" in rendered


def test_report_diff_custom_title():
    report = report_diff(_make_diff_result(), title="My Diff")
    assert report.title == "My Diff"
    assert "# My Diff" in report.render()


# ---------------------------------------------------------------------------
# report_validation
# ---------------------------------------------------------------------------

def _make_validation_result(has_error=False):
    issues = []
    if has_error:
        issues.append(ValidationIssue(key="KEY", message="bad value", severity="error"))
    issues.append(ValidationIssue(key="OTHER", message="minor", severity="warning"))
    return ValidationResult(issues=issues)


def test_report_validation_passed():
    report = report_validation(ValidationResult(issues=[]))
    assert "PASSED" in report.render()


def test_report_validation_failed():
    report = report_validation(_make_validation_result(has_error=True))
    assert "FAILED" in report.render()
    assert "KEY" in report.render()


def test_report_validation_warnings():
    report = report_validation(_make_validation_result(has_error=False))
    assert "OTHER" in report.render()


# ---------------------------------------------------------------------------
# report_audit
# ---------------------------------------------------------------------------

def _make_audit_result(has_error=False):
    issues = []
    if has_error:
        issues.append(AuditIssue(key="SECRET", message="empty secret", severity="error"))
    issues.append(AuditIssue(key="TOKEN", message="placeholder", severity="warning"))
    return AuditResult(issues=issues)


def test_report_audit_clean():
    report = report_audit(AuditResult(issues=[]))
    assert "CLEAN" in report.render()


def test_report_audit_issues_found():
    report = report_audit(_make_audit_result(has_error=True))
    assert "ISSUES FOUND" in report.render()
    assert "SECRET" in report.render()


def test_report_audit_warning_present():
    report = report_audit(_make_audit_result())
    assert "TOKEN" in report.render()
