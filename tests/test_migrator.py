"""Tests for envpatch.migrator."""
from __future__ import annotations

from envpatch.parser import EnvFile, EnvEntry
from envpatch.migrator import migrate, MigrationIssue, MigrationResult


def _make_env(*pairs: tuple) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries, path=None)


# ---------------------------------------------------------------------------
# MigrationResult helpers
# ---------------------------------------------------------------------------

def test_migration_result_is_clean_when_no_issues():
    r = MigrationResult()
    assert r.is_clean()


def test_migration_result_not_clean_with_issues():
    r = MigrationResult(issues=[MigrationIssue(key="X", message="bad")])
    assert not r.is_clean()


def test_migration_result_str_clean():
    r = MigrationResult()
    assert "no issues" in str(r)


def test_migration_result_str_with_issues():
    r = MigrationResult(issues=[MigrationIssue(key="OLD", message="not found")])
    assert "OLD" in str(r)
    assert "not found" in str(r)


def test_migration_issue_str():
    issue = MigrationIssue(key="FOO", message="oops")
    assert str(issue) == "FOO: oops"


# ---------------------------------------------------------------------------
# migrate() behaviour
# ---------------------------------------------------------------------------

def test_migrate_no_ops_returns_same_entries():
    env = _make_env(("A", "1"), ("B", "2"))
    result = migrate(env)
    assert [e.key for e in result.entries] == ["A", "B"]
    assert result.is_clean()


def test_migrate_renames_key():
    env = _make_env(("OLD_KEY", "hello"))
    result = migrate(env, rename_map={"OLD_KEY": "NEW_KEY"})
    assert result.entries[0].key == "NEW_KEY"
    assert result.entries[0].value == "hello"
    assert result.renamed == {"OLD_KEY": "NEW_KEY"}
    assert result.is_clean()


def test_migrate_removes_key():
    env = _make_env(("KEEP", "yes"), ("DROP", "no"))
    result = migrate(env, remove_keys=["DROP"])
    assert [e.key for e in result.entries] == ["KEEP"]
    assert result.removed == ["DROP"]
    assert result.is_clean()


def test_migrate_rename_and_remove_combined():
    env = _make_env(("OLD", "v"), ("GONE", "x"), ("STAY", "s"))
    result = migrate(env, rename_map={"OLD": "NEW"}, remove_keys=["GONE"])
    keys = [e.key for e in result.entries]
    assert "NEW" in keys
    assert "GONE" not in keys
    assert "STAY" in keys


def test_migrate_missing_rename_source_creates_issue():
    env = _make_env(("A", "1"))
    result = migrate(env, rename_map={"MISSING": "TARGET"})
    assert not result.is_clean()
    assert any("MISSING" in str(i) for i in result.issues)


def test_migrate_duplicate_rename_target_creates_issue():
    env = _make_env(("FOO", "1"), ("BAR", "2"))
    result = migrate(env, rename_map={"FOO": "SHARED", "BAR": "SHARED"})
    assert not result.is_clean()


def test_migrate_preserves_comment():
    entry = EnvEntry(key="K", value="v", comment="keep me")
    env = EnvFile(entries=[entry], path=None)
    result = migrate(env, rename_map={"K": "K2"})
    assert result.entries[0].comment == "keep me"


def test_migrate_remove_takes_priority_over_rename():
    env = _make_env(("X", "val"))
    # X is in both remove_keys and rename_map — remove wins
    result = migrate(env, rename_map={"X": "Y"}, remove_keys=["X"])
    assert all(e.key != "X" and e.key != "Y" for e in result.entries)
    assert "X" in result.removed
