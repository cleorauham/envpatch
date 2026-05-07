"""Tests for envpatch.exporter."""
from __future__ import annotations

import json

import pytest

from envpatch.exporter import export_env, export_report
from envpatch.parser import EnvEntry, EnvFile
from envpatch.reporter import Report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report() -> Report:
    r = Report(title="Test Report")
    r.add_section("Alpha", ["  line one", "  line two"])
    r.add_section("Beta", [])
    return r


def _make_env_file() -> EnvFile:
    entries = [
        EnvEntry(key="FOO", value="bar", comment="a comment"),
        EnvEntry(key="BAZ", value="qux", comment=None),
    ]
    return EnvFile(entries=entries, path=None)


# ---------------------------------------------------------------------------
# export_report
# ---------------------------------------------------------------------------

def test_export_report_text_contains_title():
    report = _make_report()
    out = export_report(report, fmt="text")
    assert "# Test Report" in out


def test_export_report_text_contains_sections():
    report = _make_report()
    out = export_report(report, fmt="text")
    assert "Alpha" in out
    assert "line one" in out


def test_export_report_markdown_contains_title():
    report = _make_report()
    out = export_report(report, fmt="markdown")
    assert "# Test Report" in out
    assert "Alpha" in out


def test_export_report_json_structure():
    report = _make_report()
    out = export_report(report, fmt="json")
    data = json.loads(out)
    assert data["title"] == "Test Report"
    assert isinstance(data["sections"], list)
    assert len(data["sections"]) == 2
    assert data["sections"][0]["heading"] == "Alpha"


def test_export_report_invalid_format():
    report = _make_report()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_report(report, fmt="xml")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# export_env
# ---------------------------------------------------------------------------

def test_export_env_text_basic():
    env = _make_env_file()
    out = export_env(env, fmt="text")
    assert "FOO=bar" in out
    assert "BAZ=qux" in out


def test_export_env_text_includes_comment():
    env = _make_env_file()
    out = export_env(env, fmt="text")
    assert "a comment" in out


def test_export_env_json_structure():
    env = _make_env_file()
    out = export_env(env, fmt="json")
    records = json.loads(out)
    assert isinstance(records, list)
    assert records[0]["key"] == "FOO"
    assert records[0]["value"] == "bar"
    assert records[0]["comment"] == "a comment"
    assert records[1]["comment"] is None


def test_export_env_markdown_table():
    env = _make_env_file()
    out = export_env(env, fmt="markdown")
    assert "| Key | Value | Comment |" in out
    assert "`FOO`" in out
    assert "`bar`" in out


def test_export_env_invalid_format():
    env = _make_env_file()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_env(env, fmt="csv")  # type: ignore[arg-type]
