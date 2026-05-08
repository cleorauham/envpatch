"""Tests for envpatch.masker."""
import pytest
from envpatch.parser import EnvFile, EnvEntry
from envpatch.masker import mask, MaskedEntry, MaskResult, _is_sensitive


def _make_env(*pairs) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


# --- _is_sensitive ---

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_not_sensitive_plain_key():
    assert _is_sensitive("APP_ENV") is False


def test_is_not_sensitive_port():
    assert _is_sensitive("PORT") is False


# --- mask ---

def test_mask_non_sensitive_unchanged():
    env = _make_env(("APP_ENV", "production"), ("PORT", "8080"))
    result = mask(env)
    assert result.masked_count == 0
    for entry in result.entries:
        assert entry.was_masked is False
        assert entry.value == entry.original.value


def test_mask_sensitive_key_is_replaced():
    env = _make_env(("DB_PASSWORD", "supersecret"))
    result = mask(env)
    assert result.masked_count == 1
    assert result.entries[0].masked_value == "***"
    assert result.entries[0].was_masked is True


def test_mask_empty_sensitive_value_not_masked():
    env = _make_env(("DB_PASSWORD", ""))
    result = mask(env)
    # empty value — nothing to mask
    assert result.masked_count == 0
    assert result.entries[0].masked_value == ""


def test_mask_custom_mask_char():
    env = _make_env(("API_KEY", "abc123"))
    result = mask(env, mask_char="[REDACTED]")
    assert result.entries[0].masked_value == "[REDACTED]"


def test_mask_partial_reveals_edges():
    env = _make_env(("SECRET_TOKEN", "abcdefghij"))
    result = mask(env, partial=True)
    entry = result.entries[0]
    assert entry.masked_value.startswith("ab")
    assert entry.masked_value.endswith("ij")
    assert "***" in entry.masked_value


def test_mask_partial_short_value_fully_masked():
    env = _make_env(("SECRET_TOKEN", "ab"))
    result = mask(env, partial=True)
    assert result.entries[0].masked_value == "***"


def test_mask_result_str():
    env = _make_env(("APP_ENV", "dev"), ("DB_PASSWORD", "secret"))
    result = mask(env)
    output = str(result)
    assert "APP_ENV=dev" in output
    assert "DB_PASSWORD=***" in output


def test_masked_entry_key_and_value_properties():
    env = _make_env(("AUTH_TOKEN", "tok_xyz"))
    result = mask(env)
    entry = result.entries[0]
    assert entry.key == "AUTH_TOKEN"
    assert entry.value == "***"


def test_mask_mixed_entries_count():
    env = _make_env(("HOST", "localhost"), ("DB_PASSWORD", "pw"), ("API_KEY", "key123"))
    result = mask(env)
    assert result.masked_count == 2
    assert len(result.entries) == 3
