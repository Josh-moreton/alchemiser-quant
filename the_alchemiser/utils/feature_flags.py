"""Feature flag utilities for staged rollouts.

Flags are controlled via environment variables for simplicity.
"""

from __future__ import annotations

import os
from typing import Final

TYPE_SYSTEM_V2_FLAG: Final[str] = "TYPES_V2_ENABLED"


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_enabled(name: str, default: bool = False) -> bool:
    """Generic flag checker by name."""
    if name in os.environ:
        return _truthy(os.environ.get(name))
    return default


def type_system_v2_enabled(default: bool = False) -> bool:
    """Is the typed DDD path enabled?"""
    return is_enabled(TYPE_SYSTEM_V2_FLAG, default)
