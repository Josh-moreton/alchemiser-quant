"""Business Unit: shared | Status: current.

Market regime detection and dynamic strategy weighting module.

This module provides HMM-based market regime classification and strategy
weight adjustment based on per-regime Sharpe ratios.

Architecture:
    - RegimeDetector: Classifies current market regime using Hidden Markov Model
    - RegimeWeightAdjuster: Adjusts strategy allocations based on current regime
    - RegimeState: Frozen DTO representing current regime + probability
    - RegimeWeightConfig: Per-strategy Sharpe ratios and weights by regime

The regime detection runs as a separate Lambda after market close,
caching results in DynamoDB. The Strategy Orchestrator reads the cached
regime and adjusts allocations before dispatching strategy workers.
"""

from __future__ import annotations

from .classifier import HMMRegimeClassifier
from .repository import RegimeStateRepository
from .schemas import (
    RegimeState,
    RegimeType,
    RegimeWeightConfig,
    StrategyRegimeMetrics,
)
from .weight_adjuster import RegimeWeightAdjuster

__all__ = [
    "HMMRegimeClassifier",
    "RegimeState",
    "RegimeStateRepository",
    "RegimeType",
    "RegimeWeightConfig",
    "RegimeWeightAdjuster",
    "StrategyRegimeMetrics",
]
