"""Tests for envpatch.writer."""

import os
import tempfile
import pytest
from envpatch.merger import MergeConflict, MergeResult
from envpatch.writer import render_env, write_env


def test_render_env_basic():
    mr = MergeResult(merged={"FOO": "bar", "BAZ": "qux"}, conflicts=[])
    output = render_env(mr)
    assert "FOO=bar" in output
    assert "BAZ=qux" in output
    assert output.endswith("\n")


def test_render_env_sorted():
    mr = MergeResult(merged={"Z_KEY": "z", "A_KEY": "a"}, conflicts=[])
    output = render_env(mr)
    lines = [l for l in output.strip().splitlines() if l and not l.startswith("#")]
    assert lines[0].startswith("A_KEY")
    assert lines[1].startswith("Z_KEY")


def test_render_env_no_conflict_markers_by_default():
    conflict = MergeConflict(key="DB", base_value="local", target_value="remote")
    mr = MergeResult(merged={"PORT": "5432"}, conflicts=[conflict])
    output = render_env(mr, include_conflicts=False)
    assert "CONFLICT" not in output
    assert "UNRESOLVED" not in output


def test_render_env_with_conflict_markers():
    conflict = MergeConflict(key="DB", base_value="local", target_value="remote")
    mr = MergeResult(merged={"PORT": "5432"}, conflicts=[conflict])
    output = render_env(mr, include_conflicts=True)
    assert "CONFLICT: DB" in output
    assert "base:   local" in output
    assert "target: remote" in output
    assert "UNRESOLVED" in output


def test_write_env_creates_file():
    mr = MergeResult(merged={"KEY": "value"}, conflicts=[])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".env") as tmp:
        path = tmp.name
    try:
        write_env(mr, path)
        with open(path) as fh:
            content = fh.read()
        assert "KEY=value" in content
    finally:
        os.unlink(path)


def test_write_env_overwrites_existing():
    mr = MergeResult(merged={"NEW": "data"}, conflicts=[])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".env", mode="w") as tmp:
        tmp.write("OLD=stuff\n")
        path = tmp.name
    try:
        write_env(mr, path)
        with open(path) as fh:
            content = fh.read()
        assert "OLD=stuff" not in content
        assert "NEW=data" in content
    finally:
        os.unlink(path)
