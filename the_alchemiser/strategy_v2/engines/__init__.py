#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine module.

Contains strategy engine with its core trading logic accessible via submodules.
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
