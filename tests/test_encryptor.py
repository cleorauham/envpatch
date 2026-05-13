"""Tests for envpatch.encryptor."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.encryptor import (
    _is_sensitive,
    EncryptIssue,
    EncryptResult,
    encrypt_env,
    decrypt_env,
)

try:
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False

pytest.importorskip("cryptography")

TEST_KEY = Fernet.generate_key()


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries)


def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert _is_sensitive("AUTH_TOKEN") is True


def test_is_not_sensitive_plain_key():
    assert _is_sensitive("APP_NAME") is False


def test_encrypt_sensitive_key_adds_enc_prefix():
    env = _make_env(("DB_PASSWORD", "secret123"))
    result = encrypt_env(env, TEST_KEY)
    assert result.entries[0].value.startswith("enc:")


def test_encrypt_non_sensitive_key_unchanged_by_default():
    env = _make_env(("APP_NAME", "myapp"))
    result = encrypt_env(env, TEST_KEY)
    assert result.entries[0].value == "myapp"


def test_encrypt_all_keys_encrypts_non_sensitive():
    env = _make_env(("APP_NAME", "myapp"))
    result = encrypt_env(env, TEST_KEY, sensitive_only=False)
    assert result.entries[0].value.startswith("enc:")


def test_encrypt_already_encrypted_value_skipped():
    env = _make_env(("DB_PASSWORD", "enc:sometoken"))
    result = encrypt_env(env, TEST_KEY)
    assert result.entries[0].value == "enc:sometoken"
    assert len(result.issues) == 1
    assert "already encrypted" in result.issues[0].reason


def test_decrypt_reverses_encrypt():
    env = _make_env(("DB_PASSWORD", "hunter2"), ("APP_NAME", "myapp"))
    encrypted = encrypt_env(env, TEST_KEY)
    env2 = EnvFile(entries=encrypted.entries)
    decrypted = decrypt_env(env2, TEST_KEY)
    values = {e.key: e.value for e in decrypted.entries}
    assert values["DB_PASSWORD"] == "hunter2"
    assert values["APP_NAME"] == "myapp"


def test_decrypt_invalid_token_records_issue():
    env = _make_env(("DB_PASSWORD", "enc:notavalidtoken"))
    result = decrypt_env(env, TEST_KEY)
    assert len(result.issues) == 1
    assert "invalid" in result.issues[0].reason


def test_encrypt_result_is_clean_with_no_issues():
    env = _make_env(("DB_PASSWORD", "secret"))
    result = encrypt_env(env, TEST_KEY)
    assert result.is_clean()


def test_encrypt_result_str_clean():
    result = EncryptResult()
    assert "no issues" in str(result)


def test_encrypt_result_str_with_issues():
    result = EncryptResult(issues=[EncryptIssue(key="DB_PASSWORD", reason="already encrypted — skipped")])
    text = str(result)
    assert "DB_PASSWORD" in text
    assert "already encrypted" in text


def test_encrypt_issue_str():
    issue = EncryptIssue(key="API_KEY", reason="some problem")
    assert "API_KEY" in str(issue)
    assert "some problem" in str(issue)
