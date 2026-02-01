"""Business Unit: shared | Status: current.

Options hedging module for automated tail protection.

This package provides:
- Sector mapping: Ticker-to-ETF cross-reference for liquid hedge instruments
- Hedge configuration: VIX-adaptive budgets, delta targets, DTE thresholds
- Option schemas: DTOs for contracts, positions, and orders
- Alpaca adapter: Options API integration for chain queries and execution
- Payoff calculator: Scenario-based contract sizing for target payoffs
- Premium tracker: Rolling 12-month spend tracking and cap enforcement
"""

from __future__ import annotations

from .payoff_calculator import (
    PayoffCalculationResult,
    PayoffCalculator,
    PayoffScenario,
)
from .premium_tracker import (
    PremiumSpendRecord,
    PremiumTracker,
    SpendCheckResult,
)

__all__ = [
    "PayoffCalculator",
    "PayoffCalculationResult",
    "PayoffScenario",
    "PremiumTracker",
    "PremiumSpendRecord",
    "SpendCheckResult",
]
