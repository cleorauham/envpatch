"""Tests for envpatch.resolver."""
from __future__ import annotations

from pathlib import Path

import pytest

from envpatch.resolver import ResolveResult, resolve


@pytest.fixture()
def simple_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("HOST=localhost\nPORT=5432\nDSN=postgres://${HOST}:${PORT}/db\n")
    return p


@pytest.fixture()
def env_with_undefined(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("URL=http://${UNDEFINED_HOST}/path\n")
    return p


@pytest.fixture()
def env_with_duplicate(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=first\nKEY=second\n")
    return p


def test_resolve_ok_for_valid_file(simple_env: Path):
    result = resolve(simple_env)
    assert result.is_ok()
    assert result.summary() == "Resolve OK"


def test_resolve_interpolates_references(simple_env: Path):
    result = resolve(simple_env)
    assert result.interpolation.resolved["DSN"] == "postgres://localhost:5432/db"


def test_resolve_uses_external_variables(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("URL=${SCHEME}://example.com\n")
    result = resolve(p, external={"SCHEME": "https"})
    assert result.is_ok()
    assert result.interpolation.resolved["URL"] == "https://example.com"


def test_resolve_is_not_ok_with_undefined_ref(env_with_undefined: Path):
    result = resolve(env_with_undefined)
    assert not result.is_ok()
    assert "UNDEFINED_HOST" in result.summary()


def test_resolve_is_not_ok_with_duplicate_key(env_with_duplicate: Path):
    result = resolve(env_with_duplicate)
    # Validation should flag the duplicate key
    assert not result.validation.is_valid()
    assert not result.is_ok()


def test_resolve_summary_contains_both_issues(tmp_path: Path):
    p = tmp_path / ".env"
    # duplicate key AND undefined reference
    p.write_text("KEY=a\nKEY=b\nURL=${GHOST}\n")
    result = resolve(p)
    summary = result.summary()
    assert "KEY" in summary or "duplicate" in summary.lower()
    assert "GHOST" in summary


def test_resolve_result_env_file_populated(simple_env: Path):
    result = resolve(simple_env)
    keys = [e.key for e in result.env_file.entries if not e.is_comment]
    assert "HOST" in keys
    assert "PORT" in keys
    assert "DSN" in keys
