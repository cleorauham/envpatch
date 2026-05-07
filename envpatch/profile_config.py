"""Load and save custom profile configurations from TOML/JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set


DEFAULT_CONFIG_NAME = ".envprofiles.json"


def load_profile_config(path: str | Path) -> Dict[str, Set[str]]:
    """Load a profile config JSON file and return a dict of profile -> required keys."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Profile config not found: {config_path}")

    raw = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError("Profile config must be a JSON object at the top level.")

    result: Dict[str, Set[str]] = {}
    for profile_name, keys in raw.items():
        if not isinstance(keys, list):
            raise ValueError(
                f"Profile '{profile_name}' must map to a list of key strings."
            )
        result[profile_name] = set(keys)

    return result


def save_profile_config(profiles: Dict[str, Set[str]], path: str | Path) -> None:
    """Persist a profile config to a JSON file."""
    output_path = Path(path)
    serialisable = {name: sorted(keys) for name, keys in profiles.items()}
    output_path.write_text(
        json.dumps(serialisable, indent=2) + "\n", encoding="utf-8"
    )


def merge_with_builtins(
    custom: Dict[str, Set[str]],
    builtins: Dict[str, Set[str]],
) -> Dict[str, Set[str]]:
    """Merge custom profiles with built-in ones; custom entries take precedence."""
    merged = dict(builtins)
    merged.update(custom)
    return merged
