"""Write merged .env content back to a file or string."""

from typing import Dict, List, Optional
from envpatch.merger import MergeResult


def _sorted_env_lines(data: Dict[str, str]) -> List[str]:
    """Return sorted KEY=VALUE lines from a dict."""
    return [f"{k}={v}" for k, v in sorted(data.items())]


def render_env(result: MergeResult, include_conflicts: bool = False) -> str:
    """Render a MergeResult to a .env-formatted string.

    Args:
        result: The merge result to render.
        include_conflicts: If True, include conflict markers in output.

    Returns:
        A string suitable for writing to a .env file.
    """
    lines: List[str] = []

    if include_conflicts and result.conflicts:
        lines.append("# === CONFLICTS (resolve manually) ===")
        for conflict in result.conflicts:
            lines.append(f"# CONFLICT: {conflict.key}")
            lines.append(f"# base:   {conflict.base_value}")
            lines.append(f"# target: {conflict.target_value}")
            lines.append(f"# {conflict.key}=<UNRESOLVED>")
        lines.append("")

    lines.extend(_sorted_env_lines(result.merged))
    return "\n".join(lines) + "\n"


def write_env(result: MergeResult, path: str, include_conflicts: bool = False) -> None:
    """Write a MergeResult to a file at the given path.

    Args:
        result: The merge result to write.
        path: Destination file path.
        include_conflicts: Whether to annotate conflicts in the output.
    """
    content = render_env(result, include_conflicts=include_conflicts)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
