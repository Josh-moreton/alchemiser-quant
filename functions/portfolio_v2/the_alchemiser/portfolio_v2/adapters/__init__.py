#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current.

Portfolio data adapters.

Provides thin wrappers around shared data sources for portfolio consumption.

Public API:
    AlpacaDataAdapter: Adapter for accessing portfolio data via shared AlpacaManager

Module boundaries:
    - Imports from shared only (no strategy/execution dependencies)
    - Re-exports adapter interfaces for portfolio orchestration
    - Provides clean interface for positions, prices, and account data access
"""

from __future__ import annotations

from . import alpaca_data_adapter
from .alpaca_data_adapter import AlpacaDataAdapter

__all__ = [
    "AlpacaDataAdapter",
]

# Version for compatibility tracking
__version__ = "2.0.0"

# Clean up namespace to prevent module leakage
del alpaca_data_adapter
