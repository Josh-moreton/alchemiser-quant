"""Business Unit: utilities; Status: current.

Interface layer utilities for application boundary handling.

This package contains utilities specific to the interface layer,
particularly for serialization and data conversion at application boundaries.
"""

from __future__ import annotations

from .serialization import ensure_serialized_dict, to_serializable

__all__ = ["ensure_serialized_dict", "to_serializable"]
