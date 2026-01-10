"""Business Unit: utilities | Status: current.

Fallback configuration constants for DSL strategy profiles and allocations.

This module defines strategy filenames and allocation weights used as fallback
defaults when JSON configuration files fail to load. The primary configuration
source is JSON files in the_alchemiser/config/ package (strategy.dev.json and
strategy.prod.json).

Architecture:
    - Primary: JSON config files (loaded by StrategySettings._get_stage_profile)
    - Dynamic overlay: DynamoDB dynamic weights (loaded by get_strategy_profile)
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

from dataclasses import dataclass
from decimal import Decimal

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


@dataclass
class StrategyProfile:
    """Container for strategy configuration profile.

    Attributes:
        files: List of DSL strategy filenames
        allocations: Dict mapping strategy filename to allocation weight (0-1)
        is_dynamic: True if allocations were loaded from dynamic weights table

    """

    files: list[str]
    allocations: dict[str, Decimal]
    is_dynamic: bool = False


def get_strategy_profile(stage: str = "dev", use_dynamic: bool = True) -> StrategyProfile:
    """Get strategy profile with optional dynamic weight overlay.

    Resolution order:
    1. Load baseline allocations from JSON config or fallback constants
    2. If use_dynamic=True, overlay dynamic weights from DynamoDB (if available)
    3. Return profile with final allocations

    Args:
        stage: Deployment stage ("dev", "staging", or "prod")
        use_dynamic: If True, overlay dynamic weights from DynamoDB

    Returns:
        StrategyProfile with files and allocations

    """
    # Load baseline allocations from config (existing code path)
    from .config import StrategySettings

    settings = StrategySettings()

    # Convert float allocations to Decimal for precision
    baseline_allocations = {k: Decimal(str(v)) for k, v in settings.dsl_allocations.items()}
    files = settings.dsl_files

    # Overlay dynamic weights if enabled
    if use_dynamic:
        try:
            import os

            weights_table = os.environ.get("STRATEGY_WEIGHTS__TABLE_NAME")
            if weights_table:
                # Import repository for loading dynamic weights
                from the_alchemiser.shared.repositories import (
                    dynamodb_strategy_weights_repository,
                )

                repo = dynamodb_strategy_weights_repository.DynamoDBStrategyWeightsRepository(
                    weights_table
                )
                dynamic_weights = repo.get_current_weights()

                if dynamic_weights:
                    # Overlay dynamic weights on baseline allocations
                    # Only update strategies that exist in both baseline and dynamic weights
                    for strategy_name, weight in dynamic_weights.items():
                        if strategy_name in baseline_allocations:
                            baseline_allocations[strategy_name] = weight

                    return StrategyProfile(
                        files=files,
                        allocations=baseline_allocations,
                        is_dynamic=True,
                    )
        except Exception as e:
            # Log error but continue with baseline allocations
            import logging

            logging.warning(f"Failed to load dynamic weights, using baseline: {e}")

    # Return baseline allocations (no dynamic overlay)
    return StrategyProfile(
        files=files,
        allocations=baseline_allocations,
        is_dynamic=False,
    )


# Public API
__all__ = [
    # Development configuration
    "DEV_DSL_ALLOCATIONS",
    "DEV_DSL_FILES",
    # Production configuration
    "PROD_DSL_ALLOCATIONS",
    "PROD_DSL_FILES",
    # Strategy name constants
    "STRATEGY_COIN",
    "STRATEGY_KMLM",
    "STRATEGY_NUCLEAR",
    "STRATEGY_PHOENIX",
    "STRATEGY_STARBURST",
    "STRATEGY_TQQQ_FLT",
    "STRATEGY_WHAT",
    # Dynamic profile API
    "StrategyProfile",
    "get_strategy_profile",
]
