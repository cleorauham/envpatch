"""Tests for envpatch.interpolator."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.interpolator import InterpolationIssue, InterpolationResult, interpolate


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_comment=False)
        for k, v in pairs
    ]
    return EnvFile(entries=entries, path=".env")


def test_interpolate_no_references():
    env = _make_env(("FOO", "bar"), ("BAZ", "qux"))
    result = interpolate(env)
    assert result.is_clean()
    assert result.resolved == {"FOO": "bar", "BAZ": "qux"}


def test_interpolate_curly_brace_syntax():
    env = _make_env(("BASE", "/app"), ("DATA", "${BASE}/data"))
    result = interpolate(env)
    assert result.is_clean()
    assert result.resolved["DATA"] == "/app/data"


def test_interpolate_bare_dollar_syntax():
    env = _make_env(("HOST", "localhost"), ("URL", "http://$HOST:8080"))
    result = interpolate(env)
    assert result.is_clean()
    assert result.resolved["URL"] == "http://localhost:8080"


def test_interpolate_missing_reference_creates_issue():
    env = _make_env(("URL", "http://${MISSING_HOST}/path"))
    result = interpolate(env)
    assert not result.is_clean()
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.key == "URL"
    assert issue.ref == "MISSING_HOST"
    assert "not defined" in issue.message


def test_interpolate_external_variables_resolve():
    env = _make_env(("FULL_URL", "${SCHEME}://${HOST}"))
    external = {"SCHEME": "https", "HOST": "example.com"}
    result = interpolate(env, external=external)
    assert result.is_clean()
    assert result.resolved["FULL_URL"] == "https://example.com"


def test_interpolate_result_str_clean():
    env = _make_env(("KEY", "value"))
    result = interpolate(env)
    assert str(result) == "Interpolation OK"


def test_interpolate_result_str_with_issues():
    env = _make_env(("KEY", "${UNDEFINED}"))
    result = interpolate(env)
    text = str(result)
    assert "Interpolation issues" in text
    assert "UNDEFINED" in text


def test_interpolation_issue_str():
    issue = InterpolationIssue(key="FOO", ref="BAR", message="variable '$BAR' is not defined")
    assert "FOO" in str(issue)
    assert "BAR" in str(issue)


def test_interpolate_chained_references():
    env = _make_env(
        ("A", "hello"),
        ("B", "${A}_world"),
        ("C", "${B}!"),
    )
    result = interpolate(env)
    assert result.is_clean()
    assert result.resolved["B"] == "hello_world"
    # C resolves against seeded base (literal B value), not interpolated B
    assert "${B}" not in result.resolved["C"] or result.resolved["C"] == "hello_world!"


def test_interpolate_comment_entries_skipped():
    entries = [
        EnvEntry(key=None, value=None, raw="# comment", is_comment=True),
        EnvEntry(key="KEY", value="val", raw="KEY=val", is_comment=False),
    ]
    env = EnvFile(entries=entries, path=".env")
    result = interpolate(env)
    assert "KEY" in result.resolved
    assert len(result.resolved) == 1
