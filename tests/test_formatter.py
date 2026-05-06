"""Tests for envpatch.formatter."""

import pytest
from envpatch.differ import ChangeType, DiffEntry, DiffResult
from envpatch.merger import MergeConflict, MergeResult
from envpatch.formatter import format_diff, format_merge_result


def _make_diff_result(entries):
    return DiffResult(entries=entries)


def test_format_diff_added_no_color():
    entry = DiffEntry(key="NEW_KEY", change_type=ChangeType.ADDED, old_value=None, new_value="hello")
    result = _make_diff_result([entry])
    output = format_diff(result, use_color=False)
    assert "+ NEW_KEY=hello" in output


def test_format_diff_removed_no_color():
    entry = DiffEntry(key="OLD_KEY", change_type=ChangeType.REMOVED, old_value="bye", new_value=None)
    result = _make_diff_result([entry])
    output = format_diff(result, use_color=False)
    assert "- OLD_KEY=bye" in output


def test_format_diff_modified_no_color():
    entry = DiffEntry(key="MOD_KEY", change_type=ChangeType.MODIFIED, old_value="old", new_value="new")
    result = _make_diff_result([entry])
    output = format_diff(result, use_color=False)
    assert "~ MOD_KEY" in output
    assert "- old" in output
    assert "+ new" in output


def test_format_diff_unchanged_no_color():
    entry = DiffEntry(key="SAME", change_type=ChangeType.UNCHANGED, old_value="val", new_value="val")
    result = _make_diff_result([entry])
    output = format_diff(result, use_color=False)
    assert "  SAME=val" in output


def test_format_diff_with_color_contains_ansi():
    entry = DiffEntry(key="X", change_type=ChangeType.ADDED, old_value=None, new_value="1")
    result = _make_diff_result([entry])
    output = format_diff(result, use_color=True)
    assert "\033[" in output


def test_format_merge_result_no_conflicts():
    mr = MergeResult(merged={"A": "1", "B": "2"}, conflicts=[])
    output = format_merge_result(mr, use_color=False)
    assert "A=1" in output
    assert "B=2" in output
    assert "CONFLICT" not in output


def test_format_merge_result_with_conflicts():
    conflict = MergeConflict(key="HOST", base_value="localhost", target_value="prod.host")
    mr = MergeResult(merged={"PORT": "5432"}, conflicts=[conflict])
    output = format_merge_result(mr, use_color=False)
    assert "CONFLICT: HOST" in output
    assert "localhost" in output
    assert "prod.host" in output
    assert "PORT=5432" in output
