"""Business Unit: utilities | Status: current.

Fallback configuration constants for DSL strategy profiles and allocations.

This module defines strategy filenames and allocation weights used as fallback
defaults when JSON configuration files fail to load. The primary configuration
source is JSON files in the_alchemiser/config/ package (strategy.dev.json and
strategy.prod.json).

Architecture:
    - Primary: JSON config files (loaded by StrategySettings._get_stage_profile)
    - Fallback: These Python constants (used when JSON load fails)

Maintenance Policy:
    - Keep constants synchronized with JSON config files
    - All allocation weights must sum to 1.0 (100% of portfolio)
    - Changes should be made in JSON files first, then reflected here

Related:
    - the_alchemiser.shared.config.config.StrategySettings
    - the_alchemiser/config/strategy.dev.json
    - the_alchemiser/config/strategy.prod.json
"""

from __future__ import annotations

# Strategy file name constants (nested structure)
# These represent DSL strategy files (Clojure) that define trading logic
# Foundation strategies: Core, stable strategies
STRATEGY_GRAIL = "foundation/grail.clj"  # Grail strategy: High-conviction growth
STRATEGY_KMLM = "foundation/kmlm.clj"  # KMLM strategy: Momentum-based allocation
STRATEGY_SEMICONDUCTORS = "foundation/semiconductors.clj"  # Semiconductors strategy: Chip sector focus

# Tactical strategies: Opportunistic, higher-risk strategies
STRATEGY_BITCOIN = "tactical/bitcoin.clj"  # Bitcoin strategy: Cryptocurrency exposure
STRATEGY_QUANTUM = "tactical/quantum.clj"  # Quantum strategy: Quantum computing sector

# Legacy strategy name constants (for backward compatibility)
# These are deprecated and will be removed in a future version
STRATEGY_NUCLEAR = "2-Nuclear.clj"  # Legacy: Use STRATEGY_SEMICONDUCTORS instead
STRATEGY_STARBURST = "3-Starburst.clj"  # Legacy: Deprecated
STRATEGY_WHAT = "4-What.clj"  # Legacy: Deprecated
STRATEGY_COIN = "5-Coin.clj"  # Legacy: Use STRATEGY_BITCOIN instead
STRATEGY_TQQQ_FLT = "6-TQQQ-FLT.clj"  # Legacy: Deprecated
STRATEGY_PHOENIX = "7-Phoenix.clj"  # Legacy: Deprecated

# Development environment strategy configuration
# Includes all active strategies for testing and evaluation
DEV_DSL_FILES: list[str] = [
    STRATEGY_GRAIL,
    STRATEGY_KMLM,
    STRATEGY_SEMICONDUCTORS,
    STRATEGY_BITCOIN,
    STRATEGY_QUANTUM,
]

# Development environment allocation weights (must sum to 1.0)
# Equal distribution across all strategies for balanced testing
DEV_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_GRAIL: 0.2,
    STRATEGY_KMLM: 0.2,
    STRATEGY_SEMICONDUCTORS: 0.2,
    STRATEGY_BITCOIN: 0.2,
    STRATEGY_QUANTUM: 0.2,
}
# Total: 1.0 (100%) - Validated by tests

# Production environment strategy configuration
# Includes only proven, stable strategies with higher confidence
PROD_DSL_FILES: list[str] = [
    STRATEGY_KMLM,
    STRATEGY_SEMICONDUCTORS,
    STRATEGY_BITCOIN,
]

# Production environment allocation weights (must sum to 1.0)
# Higher allocations to proven foundation strategies
PROD_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_KMLM: 0.4,
    STRATEGY_SEMICONDUCTORS: 0.4,
    STRATEGY_BITCOIN: 0.2,
}
# Total: 1.0 (100%) - Validated by tests

# Public API
__all__ = [
    # Development configuration
    "DEV_DSL_ALLOCATIONS",
    "DEV_DSL_FILES",
    # Production configuration
    "PROD_DSL_ALLOCATIONS",
    "PROD_DSL_FILES",
    # Active strategy name constants
    "STRATEGY_BITCOIN",
    "STRATEGY_GRAIL",
    "STRATEGY_KMLM",
    "STRATEGY_QUANTUM",
    "STRATEGY_SEMICONDUCTORS",
    # Legacy strategy name constants (deprecated)
    "STRATEGY_COIN",
    "STRATEGY_NUCLEAR",
    "STRATEGY_PHOENIX",
    "STRATEGY_STARBURST",
    "STRATEGY_TQQQ_FLT",
    "STRATEGY_WHAT",
]
