"""Encrypt and decrypt sensitive values in an .env file using Fernet symmetric encryption."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile, EnvEntry

_SENSITIVE_SUBSTRINGS = ("secret", "password", "passwd", "token", "api_key", "private", "auth")


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(sub in lower for sub in _SENSITIVE_SUBSTRINGS)


@dataclass
class EncryptIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"[ENCRYPT] {self.key}: {self.reason}"


@dataclass
class EncryptResult:
    entries: List[EnvEntry] = field(default_factory=list)
    issues: List[EncryptIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean():
            return "Encryption complete — no issues."
        lines = ["Encryption issues:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def encrypt_env(env: EnvFile, fernet_key: bytes, sensitive_only: bool = True) -> EncryptResult:
    """Return a new list of EnvEntry with sensitive values encrypted."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:  # pragma: no cover
        raise RuntimeError("cryptography package is required: pip install cryptography")

    f = Fernet(fernet_key)
    result = EncryptResult()

    for entry in env.entries:
        if not entry.key or (sensitive_only and not _is_sensitive(entry.key)):
            result.entries.append(entry)
            continue
        raw = entry.value or ""
        if raw.startswith("enc:"):
            result.issues.append(EncryptIssue(entry.key, "value already encrypted — skipped"))
            result.entries.append(entry)
            continue
        token = f.encrypt(raw.encode()).decode()
        result.entries.append(EnvEntry(key=entry.key, value=f"enc:{token}", comment=entry.comment))

    return result


def decrypt_env(env: EnvFile, fernet_key: bytes) -> EncryptResult:
    """Return a new list of EnvEntry with enc:-prefixed values decrypted."""
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError:  # pragma: no cover
        raise RuntimeError("cryptography package is required: pip install cryptography")

    f = Fernet(fernet_key)
    result = EncryptResult()

    for entry in env.entries:
        raw = entry.value or ""
        if not raw.startswith("enc:"):
            result.entries.append(entry)
            continue
        token = raw[4:]
        try:
            plaintext = f.decrypt(token.encode()).decode()
        except InvalidToken:
            result.issues.append(EncryptIssue(entry.key, "invalid or tampered token — skipped"))
            result.entries.append(entry)
            continue
        result.entries.append(EnvEntry(key=entry.key, value=plaintext, comment=entry.comment))

    return result
