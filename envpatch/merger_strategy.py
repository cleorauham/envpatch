"""Strategy-based merge policies for .env file merging."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Optional


class ConflictPolicy(Enum):
    """How to handle a key that exists in both source and target with different values."""
    KEEP_TARGET = "keep_target"      # Preserve the existing target value (default safe behaviour)
    TAKE_SOURCE = "take_source"      # Always accept the incoming source value
    ERROR = "error"                  # Raise / mark as conflict (strict mode)


class MissingKeyPolicy(Enum):
    """How to handle a key that is present in source but absent in target."""
    ADD = "add"                      # Add the key to the target
    SKIP = "skip"                    # Silently ignore the missing key
    ERROR = "error"                  # Mark as an error


class ExtraKeyPolicy(Enum):
    """How to handle a key that is present in target but absent in source."""
    KEEP = "keep"                    # Leave the extra key untouched
    REMOVE = "remove"                # Remove the key from the target
    WARN = "warn"                    # Keep but emit a warning


@dataclass(frozen=True)
class MergeStrategy:
    """Encapsulates all policies that govern a single merge operation."""
    conflict_policy: ConflictPolicy = ConflictPolicy.ERROR
    missing_key_policy: MissingKeyPolicy = MissingKeyPolicy.ADD
    extra_key_policy: ExtraKeyPolicy = ExtraKeyPolicy.KEEP
    # Keys that are always treated as conflicts regardless of policy
    protected_keys: FrozenSet[str] = field(default_factory=frozenset)

    def is_protected(self, key: str) -> bool:
        return key in self.protected_keys


# ---------------------------------------------------------------------------
# Named presets
# ---------------------------------------------------------------------------

SAFE = MergeStrategy(
    conflict_policy=ConflictPolicy.KEEP_TARGET,
    missing_key_policy=MissingKeyPolicy.ADD,
    extra_key_policy=ExtraKeyPolicy.KEEP,
)

STRICT = MergeStrategy(
    conflict_policy=ConflictPolicy.ERROR,
    missing_key_policy=MissingKeyPolicy.ADD,
    extra_key_policy=ExtraKeyPolicy.WARN,
)

FORCE = MergeStrategy(
    conflict_policy=ConflictPolicy.TAKE_SOURCE,
    missing_key_policy=MissingKeyPolicy.ADD,
    extra_key_policy=ExtraKeyPolicy.KEEP,
)

PRESETS: dict[str, MergeStrategy] = {
    "safe": SAFE,
    "strict": STRICT,
    "force": FORCE,
}


def get_preset(name: str) -> Optional[MergeStrategy]:
    """Return a named preset, or *None* if the name is unknown."""
    return PRESETS.get(name.lower())
