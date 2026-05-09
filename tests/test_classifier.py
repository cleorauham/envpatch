"""Tests for envpatch.classifier."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.classifier import (
    EntryCategory,
    ClassifiedEntry,
    ClassifyResult,
    classify,
    _classify_key,
)


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries)


def test_classify_key_database():
    assert _classify_key("DB_HOST") == EntryCategory.DATABASE
    assert _classify_key("POSTGRES_URL") == EntryCategory.DATABASE
    assert _classify_key("DATABASE_NAME") == EntryCategory.DATABASE


def test_classify_key_cache():
    assert _classify_key("REDIS_URL") == EntryCategory.CACHE
    assert _classify_key("CACHE_TTL") == EntryCategory.CACHE


def test_classify_key_auth():
    assert _classify_key("JWT_SECRET") == EntryCategory.AUTH
    assert _classify_key("API_KEY") == EntryCategory.AUTH
    assert _classify_key("AUTH_TOKEN") == EntryCategory.AUTH


def test_classify_key_storage():
    assert _classify_key("S3_BUCKET") == EntryCategory.STORAGE
    assert _classify_key("STORAGE_PATH") == EntryCategory.STORAGE


def test_classify_key_network():
    assert _classify_key("APP_HOST") == EntryCategory.NETWORK
    assert _classify_key("PORT") == EntryCategory.NETWORK
    assert _classify_key("BASE_URL") == EntryCategory.NETWORK


def test_classify_key_feature_flag():
    assert _classify_key("FEATURE_DARK_MODE") == EntryCategory.FEATURE_FLAG
    assert _classify_key("ENABLE_SIGNUP") == EntryCategory.FEATURE_FLAG


def test_classify_key_logging():
    assert _classify_key("LOG_LEVEL") == EntryCategory.LOGGING
    assert _classify_key("SENTRY_DSN") == EntryCategory.LOGGING


def test_classify_key_other():
    assert _classify_key("APP_NAME") == EntryCategory.OTHER
    assert _classify_key("ENVIRONMENT") == EntryCategory.OTHER


def test_classify_returns_all_entries():
    env = _make_env(("DB_HOST", "localhost"), ("APP_NAME", "myapp"), ("REDIS_URL", "redis://"))
    result = classify(env)
    assert len(result.entries) == 3


def test_classify_correct_categories():
    env = _make_env(("DB_HOST", "localhost"), ("LOG_LEVEL", "info"))
    result = classify(env)
    cats = {ce.entry.key: ce.category for ce in result.entries}
    assert cats["DB_HOST"] == EntryCategory.DATABASE
    assert cats["LOG_LEVEL"] == EntryCategory.LOGGING


def test_classify_by_category_groups_correctly():
    env = _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("REDIS_URL", "redis://localhost"),
    )
    result = classify(env)
    grouped = result.by_category()
    assert len(grouped[EntryCategory.DATABASE]) == 2
    assert len(grouped[EntryCategory.CACHE]) == 1


def test_classify_categories_present():
    env = _make_env(("DB_NAME", "mydb"), ("APP_NAME", "app"))
    result = classify(env)
    cats = result.categories_present()
    assert EntryCategory.DATABASE in cats
    assert EntryCategory.OTHER in cats


def test_classify_result_str_no_entries():
    result = ClassifyResult(entries=[])
    assert str(result) == "No entries classified."


def test_classify_result_str_with_entries():
    env = _make_env(("DB_HOST", "localhost"), ("LOG_LEVEL", "debug"))
    result = classify(env)
    output = str(result)
    assert "database" in output
    assert "logging" in output


def test_classified_entry_str():
    entry = EnvEntry(key="DB_HOST", value="localhost", raw="DB_HOST=localhost")
    ce = ClassifiedEntry(entry=entry, category=EntryCategory.DATABASE)
    assert str(ce) == "[database] DB_HOST=localhost"
