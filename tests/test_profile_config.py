"""Tests for envpatch.profile_config."""

import json
import pytest
from pathlib import Path

from envpatch.profile_config import (
    load_profile_config,
    save_profile_config,
    merge_with_builtins,
)


def test_load_profile_config_basic(tmp_path: Path):
    config = {"myenv": ["DB_URL", "API_KEY"]}
    cfg_file = tmp_path / ".envprofiles.json"
    cfg_file.write_text(json.dumps(config))

    result = load_profile_config(cfg_file)
    assert "myenv" in result
    assert result["myenv"] == {"DB_URL", "API_KEY"}


def test_load_profile_config_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_profile_config(tmp_path / "nonexistent.json")


def test_load_profile_config_invalid_top_level(tmp_path: Path):
    cfg_file = tmp_path / "bad.json"
    cfg_file.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(ValueError, match="JSON object"):
        load_profile_config(cfg_file)


def test_load_profile_config_invalid_keys_type(tmp_path: Path):
    cfg_file = tmp_path / "bad.json"
    cfg_file.write_text(json.dumps({"myenv": "should_be_a_list"}))
    with pytest.raises(ValueError, match="list"):
        load_profile_config(cfg_file)


def test_save_profile_config_roundtrip(tmp_path: Path):
    profiles = {"prod": {"SECRET_KEY", "DB_URL"}, "dev": set()}
    cfg_file = tmp_path / ".envprofiles.json"
    save_profile_config(profiles, cfg_file)

    loaded = load_profile_config(cfg_file)
    assert loaded["prod"] == {"SECRET_KEY", "DB_URL"}
    assert loaded["dev"] == set()


def test_save_profile_config_sorted_keys(tmp_path: Path):
    cfg_file = tmp_path / ".envprofiles.json"
    save_profile_config({"env": {"Z_KEY", "A_KEY"}}, cfg_file)
    raw = json.loads(cfg_file.read_text())
    assert raw["env"] == ["A_KEY", "Z_KEY"]


def test_merge_with_builtins_custom_overrides():
    builtins = {"production": {"SECRET_KEY", "DB_URL"}}
    custom = {"production": {"MY_CUSTOM_KEY"}}
    merged = merge_with_builtins(custom, builtins)
    assert merged["production"] == {"MY_CUSTOM_KEY"}


def test_merge_with_builtins_preserves_non_overridden():
    builtins = {"production": {"SECRET_KEY"}, "staging": {"DB_URL"}}
    custom = {"newenv": {"CUSTOM_KEY"}}
    merged = merge_with_builtins(custom, builtins)
    assert "staging" in merged
    assert "newenv" in merged
    assert merged["staging"] == {"DB_URL"}
