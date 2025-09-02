"""Application configuration and dependency injection.

This module contains the application-level configuration that knows about
all modules and sets up dependency injection. It's separate from shared/
to maintain proper module boundaries.
"""

from __future__ import annotations

from .bootstrap import bootstrap_from_container

__all__ = ["bootstrap_from_container"]