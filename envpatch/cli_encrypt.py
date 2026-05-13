"""CLI sub-command: encrypt / decrypt sensitive .env values."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from envpatch.parser import parse
from envpatch.encryptor import encrypt_env, decrypt_env
from envpatch.writer import write_env


def build_encrypt_parser(subparsers: argparse.Action) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "encrypt",
        help="Encrypt or decrypt sensitive values in an .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--key",
        default=None,
        help="Fernet key (base64). Falls back to ENVPATCH_FERNET_KEY env var.",
    )
    p.add_argument(
        "--decrypt",
        action="store_true",
        default=False,
        help="Decrypt instead of encrypt",
    )
    p.add_argument(
        "--all-keys",
        action="store_true",
        default=False,
        help="Encrypt all keys, not just sensitive ones",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print result without writing to disk",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Write result to a different file instead of overwriting the source",
    )
    return p


def run_encrypt(args: argparse.Namespace) -> int:
    raw_key = args.key or os.environ.get("ENVPATCH_FERNET_KEY")
    if not raw_key:
        print("Error: Fernet key required via --key or ENVPATCH_FERNET_KEY", file=sys.stderr)
        return 1

    source = Path(args.file)
    if not source.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1

    env = parse(source.read_text())
    fernet_key = raw_key.encode() if isinstance(raw_key, str) else raw_key

    if args.decrypt:
        result = decrypt_env(env, fernet_key)
        action = "Decryption"
    else:
        result = encrypt_env(env, fernet_key, sensitive_only=not args.all_keys)
        action = "Encryption"

    print(str(result))

    if not args.dry_run:
        dest = Path(args.output) if args.output else source
        write_env(dest, result.entries)
        print(f"{action} complete. Written to {dest}")

    return 0 if result.is_clean() else 1
