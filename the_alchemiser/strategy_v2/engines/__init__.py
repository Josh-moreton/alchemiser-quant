#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine module.

Contains strategy engine with its core trading logic accessible via submodules.
"""

from __future__ import annotations

# Strategy engines are available via submodules:
# - dsl: DSL-based strategy engine (Clojure-style strategy files)
# Future engines (not yet implemented):
# - nuclear: Nuclear energy trading strategy
# - klm: KLM strategy variants
# - tecl: TECL strategy

# Empty __all__ is intentional - engines accessed via submodule imports
# Example: from the_alchemiser.strategy_v2.engines.dsl import DslEngine
__all__: list[str] = []
