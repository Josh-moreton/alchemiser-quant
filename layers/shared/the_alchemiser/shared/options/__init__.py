"""Business Unit: shared | Status: current.

Options hedging module for automated tail protection.

This package provides:
- Sector mapping: Ticker-to-ETF cross-reference for liquid hedge instruments
- Hedge configuration: VIX-adaptive budgets, delta targets, DTE thresholds
- Option schemas: DTOs for contracts, positions, and orders
- Alpaca adapter: Options API integration for chain queries and execution
- Template chooser: Regime-based template selection for tail_first vs smoothing
"""

from __future__ import annotations

from .template_chooser import (
    RegimeThresholds,
    TemplateChooser,
    TemplateSelectionRationale,
    TemplateType,
)

__all__: list[str] = [
    "RegimeThresholds",
    "TemplateChooser",
    "TemplateSelectionRationale",
    "TemplateType",
]
