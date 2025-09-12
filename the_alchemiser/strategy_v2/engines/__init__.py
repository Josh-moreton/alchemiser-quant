#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Strategy engines (Nuclear, KLM, TECL).

Contains strategy engines moved verbatim from the legacy strategy module.
These engines preserve their original logic and are accessed through
thin adapter wrappers.
"""

from __future__ import annotations

# Strategy engines are available via submodules:
# - nuclear: Nuclear energy trading strategy
# - klm: KLM strategy variants
# - tecl: TECL strategy

__all__ = [
    # Individual engines available via submodule imports
    # Example: from .nuclear.engine import NuclearEngine
]
