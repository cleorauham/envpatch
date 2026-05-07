"""Tests for envpatch.templater."""
from __future__ import annotations

from envpatch.parser import EnvEntry, EnvFile
from envpatch.templater import TemplateEntry, TemplateResult, build_template, _make_placeholder


def _make_env(*pairs: tuple) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries, raw_lines=[])


# ---------------------------------------------------------------------------
# _make_placeholder
# ---------------------------------------------------------------------------

def test_placeholder_empty_value_stays_empty():
    entry = EnvEntry(key="FOO", value="")
    assert _make_placeholder(entry) == ""


def test_placeholder_boolean_like_preserved():
    for val in ("true", "false", "1", "0", "yes", "no"):
        entry = EnvEntry(key="FLAG", value=val)
        assert _make_placeholder(entry) == val


def test_placeholder_numeric_preserved():
    entry = EnvEntry(key="PORT", value="8080")
    assert _make_placeholder(entry) == "8080"


def test_placeholder_secret_redacted():
    entry = EnvEntry(key="SECRET_KEY", value="super-secret-abc123")
    assert _make_placeholder(entry) == "<secret_key>"


# ---------------------------------------------------------------------------
# build_template — default (redact)
# ---------------------------------------------------------------------------

def test_build_template_redacts_secrets():
    env = _make_env(("DB_PASSWORD", "hunter2"), ("DEBUG", "true"))
    result = build_template(env)
    assert len(result.entries) == 2
    assert result.entries[0].placeholder == "<db_password>"
    assert result.entries[1].placeholder == "true"


def test_build_template_annotates_redacted_entries():
    env = _make_env(("API_KEY", "abc123xyz"))
    result = build_template(env, annotate=True)
    assert result.entries[0].comment == "required"


def test_build_template_no_annotation_when_disabled():
    env = _make_env(("API_KEY", "abc123xyz"))
    result = build_template(env, annotate=False)
    assert result.entries[0].comment is None


def test_build_template_no_comment_for_safe_value():
    env = _make_env(("DEBUG", "true"))
    result = build_template(env, annotate=True)
    assert result.entries[0].comment is None


# ---------------------------------------------------------------------------
# build_template — keep_values
# ---------------------------------------------------------------------------

def test_build_template_keep_values_preserves_original():
    env = _make_env(("SECRET", "my-secret"), ("PORT", "3000"))
    result = build_template(env, keep_values=True)
    assert result.entries[0].placeholder == "my-secret"
    assert result.entries[1].placeholder == "3000"


def test_build_template_keep_values_no_comment():
    env = _make_env(("SECRET", "my-secret"))
    result = build_template(env, keep_values=True)
    assert result.entries[0].comment is None


# ---------------------------------------------------------------------------
# TemplateResult.render
# ---------------------------------------------------------------------------

def test_template_result_render_basic():
    result = TemplateResult(entries=[
        TemplateEntry(key="FOO", placeholder="<foo>", comment="required"),
        TemplateEntry(key="BAR", placeholder="1"),
    ])
    rendered = result.render()
    assert "FOO=<foo>  # required" in rendered
    assert "BAR=1" in rendered


def test_template_entry_render_no_comment():
    entry = TemplateEntry(key="PORT", placeholder="8080")
    assert entry.render() == "PORT=8080"
