"""High-level resolver: parse, validate, and interpolate an env file in one step."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, parse
from envpatch.validator import ValidationResult, validate
from envpatch.interpolator import InterpolationResult, interpolate


@dataclass
class ResolveResult:
    env_file: EnvFile
    validation: ValidationResult
    interpolation: InterpolationResult

    def is_ok(self) -> bool:
        """True when there are no validation errors and no interpolation issues."""
        return self.validation.is_valid() and self.interpolation.is_clean()

    def summary(self) -> str:
        parts: List[str] = []
        if not self.validation.is_valid():
            parts.append(str(self.validation))
        if not self.interpolation.is_clean():
            parts.append(str(self.interpolation))
        if not parts:
            return "Resolve OK"
        return "\n".join(parts)


def resolve(
    path: Path,
    external: Optional[Dict[str, str]] = None,
) -> ResolveResult:
    """Parse *path*, validate it, then interpolate variable references.

    Parameters
    ----------
    path:
        Location of the .env file to resolve.
    external:
        Optional mapping of additional variables available for interpolation
        (e.g. a subset of ``os.environ``).
    """
    env_file = parse(path)
    validation = validate(env_file)
    interpolation = interpolate(env_file, external=external)
    return ResolveResult(
        env_file=env_file,
        validation=validation,
        interpolation=interpolation,
    )
