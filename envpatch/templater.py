"""Generate .env.example / template files from a parsed EnvFile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile, EnvEntry

# Values that are already safe to expose as-is in a template
_SAFE_PLACEHOLDERS = {"", "true", "false", "1", "0", "yes", "no"}


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    comment: Optional[str] = None
    original_comment: Optional[str] = None

    def render(self) -> str:
        parts: List[str] = []
        if self.original_comment:
            parts.append(self.original_comment)
        line = f"{self.key}={self.placeholder}"
        if self.comment:
            line += f"  # {self.comment}"
        parts.append(line)
        return "\n".join(parts)


@dataclass
class TemplateResult:
    entries: List[TemplateEntry] = field(default_factory=list)

    def render(self) -> str:
        return "\n".join(e.render() for e in self.entries)


def _make_placeholder(entry: EnvEntry) -> str:
    """Return a redacted placeholder for *entry*."""
    val = entry.value or ""
    if val.lower() in _SAFE_PLACEHOLDERS:
        return val
    # Keep non-sensitive looking short numeric/boolean literals
    if val.isdigit():
        return val
    return f"<{entry.key.lower()}>"


def build_template(
    env_file: EnvFile,
    *,
    keep_values: bool = False,
    annotate: bool = True,
) -> TemplateResult:
    """Convert *env_file* into a :class:`TemplateResult`.

    Parameters
    ----------
    env_file:
        Parsed source file.
    keep_values:
        When *True* original values are preserved (useful for non-secret files).
    annotate:
        When *True* a small comment hinting the expected type is appended to
        each redacted entry.
    """
    result = TemplateResult()
    for entry in env_file.entries:
        if keep_values:
            placeholder = entry.value or ""
            comment = None
        else:
            placeholder = _make_placeholder(entry)
            redacted = placeholder != (entry.value or "")
            comment = "required" if (annotate and redacted) else None

        result.entries.append(
            TemplateEntry(
                key=entry.key,
                placeholder=placeholder,
                comment=comment,
                original_comment=entry.comment if hasattr(entry, "comment") else None,
            )
        )
    return result
