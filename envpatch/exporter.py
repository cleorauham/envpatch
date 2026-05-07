"""Export env data and reports to various formats (text, JSON, Markdown)."""
from __future__ import annotations

import json
from typing import Literal

from envpatch.parser import EnvFile
from envpatch.reporter import Report

ExportFormat = Literal["text", "json", "markdown"]


def export_report(report: Report, fmt: ExportFormat = "text") -> str:
    """Render a Report to the requested format string."""
    if fmt == "text":
        return report.render()
    if fmt == "markdown":
        return _report_to_markdown(report)
    if fmt == "json":
        return _report_to_json(report)
    raise ValueError(f"Unsupported export format: {fmt!r}")


def export_env(env: EnvFile, fmt: ExportFormat = "text") -> str:
    """Serialise an EnvFile to the requested format."""
    if fmt == "text":
        return _env_to_text(env)
    if fmt == "json":
        return _env_to_json(env)
    if fmt == "markdown":
        return _env_to_markdown(env)
    raise ValueError(f"Unsupported export format: {fmt!r}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _report_to_markdown(report: Report) -> str:
    lines = [f"# {report.title}"]
    for section in report.sections:
        # sections already use ### headings — just include them
        lines.append(section)
    return "\n\n".join(lines)


def _report_to_json(report: Report) -> str:
    data = {"title": report.title, "sections": []}
    for section in report.sections:
        raw_lines = section.splitlines()
        heading = raw_lines[0].lstrip("# ").strip() if raw_lines else ""
        body = raw_lines[1:] if len(raw_lines) > 1 else []
        data["sections"].append({"heading": heading, "lines": body})
    return json.dumps(data, indent=2)


def _env_to_text(env: EnvFile) -> str:
    lines = []
    for entry in env.entries:
        if entry.comment:
            lines.append(f"{entry.key}={entry.value}  # {entry.comment}")
        else:
            lines.append(f"{entry.key}={entry.value}")
    return "\n".join(lines)


def _env_to_json(env: EnvFile) -> str:
    records = [
        {"key": e.key, "value": e.value, "comment": e.comment}
        for e in env.entries
    ]
    return json.dumps(records, indent=2)


def _env_to_markdown(env: EnvFile) -> str:
    lines = ["| Key | Value | Comment |", "| --- | ----- | ------- |"]
    for e in env.entries:
        lines.append(f"| `{e.key}` | `{e.value}` | {e.comment or ''} |")
    return "\n".join(lines)
