#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy engines (Nuclear, KLM, TECL).

Contains strategy engines with their core trading logic accessible through
thin adapter wrappers.
"""

from __future__ import annotations

# Strategy engines are available via submodules:
# - nuclear: Nuclear energy trading strategy
# - klm: KLM strategy variants
# - tecl: TECL strategy

__all__: list[str] = [
    # Individual engines available via submodule imports
    # Example: from .nuclear.engine import NuclearEngine
]
