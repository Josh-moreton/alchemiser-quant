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

# Strategy file name constants
# These represent DSL strategy files (Clojure) that define trading logic
STRATEGY_KMLM = "1-KMLM.clj"  # KMLM strategy: Momentum-based allocation
STRATEGY_NUCLEAR = "2-Nuclear.clj"  # Nuclear strategy: High-growth tech focus
STRATEGY_STARBURST = "3-Starburst.clj"  # Starburst strategy: Diversified growth
STRATEGY_WHAT = "4-What.clj"  # What strategy: Experimental allocation
STRATEGY_COIN = "5-Coin.clj"  # Coin strategy: Cryptocurrency exposure
STRATEGY_TQQQ_FLT = "6-TQQQ-FLT.clj"  # TQQQ-FLT strategy: Leveraged tech ETF
STRATEGY_PHOENIX = "7-Phoenix.clj"  # Phoenix strategy: Recovery-focused allocation

# Development environment strategy configuration
# Includes all strategies for testing and evaluation
DEV_DSL_FILES: list[str] = [
    STRATEGY_KMLM,
    STRATEGY_NUCLEAR,
    STRATEGY_STARBURST,
    STRATEGY_WHAT,
    STRATEGY_COIN,
    STRATEGY_TQQQ_FLT,
    STRATEGY_PHOENIX,
]

# Development environment allocation weights (must sum to 1.0)
# Spreads risk across all strategies for testing
DEV_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_KMLM: 0.2,
    STRATEGY_NUCLEAR: 0.15,
    STRATEGY_STARBURST: 0.15,
    STRATEGY_WHAT: 0.1,
    STRATEGY_COIN: 0.1,
    STRATEGY_TQQQ_FLT: 0.15,
    STRATEGY_PHOENIX: 0.15,
}
# Total: 1.0 (100%) - Validated by tests

# Production environment strategy configuration
# Includes only proven, stable strategies with higher confidence
PROD_DSL_FILES: list[str] = [
    STRATEGY_KMLM,
    STRATEGY_NUCLEAR,
    STRATEGY_COIN,
    STRATEGY_TQQQ_FLT,
]

# Production environment allocation weights (must sum to 1.0)
# Higher allocations to proven strategies with strong performance
PROD_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_KMLM: 0.4,
    STRATEGY_NUCLEAR: 0.25,
    STRATEGY_COIN: 0.1,
    STRATEGY_TQQQ_FLT: 0.25,
}
# Total: 1.0 (100%) - Validated by tests

# Public API
__all__ = [
    # Strategy name constants
    "STRATEGY_KMLM",
    "STRATEGY_NUCLEAR",
    "STRATEGY_STARBURST",
    "STRATEGY_WHAT",
    "STRATEGY_COIN",
    "STRATEGY_TQQQ_FLT",
    "STRATEGY_PHOENIX",
    # Development configuration
    "DEV_DSL_FILES",
    "DEV_DSL_ALLOCATIONS",
    # Production configuration
    "PROD_DSL_FILES",
    "PROD_DSL_ALLOCATIONS",
]
