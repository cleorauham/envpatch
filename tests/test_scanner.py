"""Tests for envpatch.scanner."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.scanner import PatternCategory, ScanEntry, ScanResult, scan


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries)


def test_scan_secret_key():
    env = _make_env(("DB_PASSWORD", "s3cr3t"), ("APP_NAME", "myapp"))
    result = scan(env)
    secrets = result.by_category(PatternCategory.SECRET)
    assert len(secrets) == 1
    assert secrets[0].key == "DB_PASSWORD"


def test_scan_url_key():
    env = _make_env(("DATABASE_URL", "postgres://localhost/db"))
    result = scan(env)
    urls = result.by_category(PatternCategory.URL)
    assert len(urls) == 1
    assert urls[0].key == "DATABASE_URL"


def test_scan_path_key():
    env = _make_env(("LOG_DIR", "/var/log"), ("HOME_PATH", "/home/user"))
    result = scan(env)
    paths = result.by_category(PatternCategory.PATH)
    assert {e.key for e in paths} == {"LOG_DIR", "HOME_PATH"}


def test_scan_flag_key():
    env = _make_env(("ENABLE_CACHE", "true"), ("DEBUG", "false"))
    result = scan(env)
    flags = result.by_category(PatternCategory.FLAG)
    assert {e.key for e in flags} == {"ENABLE_CACHE", "DEBUG"}


def test_scan_unknown_key():
    env = _make_env(("WORKERS", "4"))
    result = scan(env)
    unknown = result.by_category(PatternCategory.UNKNOWN)
    assert len(unknown) == 1
    assert unknown[0].key == "WORKERS"


def test_scan_entry_str():
    entry = ScanEntry(key="DB_PASSWORD", value="x", category=PatternCategory.SECRET)
    assert str(entry) == "[SECRET] DB_PASSWORD"


def test_scan_result_summary_empty():
    result = ScanResult(entries=[])
    assert result.summary() == "No entries scanned."


def test_scan_result_summary_counts():
    env = _make_env(
        ("DB_PASSWORD", "s"),
        ("API_TOKEN", "t"),
        ("DATABASE_URL", "u"),
        ("WORKERS", "4"),
    )
    result = scan(env)
    summary = result.summary()
    assert "secret: 2" in summary
    assert "url: 1" in summary
    assert "unknown: 1" in summary


def test_scan_ignores_entries_without_key():
    entries = [
        EnvEntry(key=None, value=None, raw="# comment"),
        EnvEntry(key="PORT", value="8080", raw="PORT=8080"),
    ]
    env = EnvFile(entries=entries)
    result = scan(env)
    assert len(result.entries) == 1
    assert result.entries[0].key == "PORT"


def test_by_category_returns_empty_list_when_none_match():
    env = _make_env(("WORKERS", "4"))
    result = scan(env)
    assert result.by_category(PatternCategory.SECRET) == []
