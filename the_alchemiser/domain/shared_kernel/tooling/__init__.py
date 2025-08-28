"""Business Unit: utilities; Status: current.

Shared kernel tooling: cross-context utility functions.

This package contains framework-agnostic utility functions that can be
safely used across different domain contexts without introducing dependencies.
"""

from __future__ import annotations

from .num import floats_equal

__all__ = ["floats_equal"]
