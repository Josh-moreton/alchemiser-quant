"""Business Unit: shared | Status: current.

Broker abstractions and utilities.

This package provides broker-agnostic interfaces and utilities that allow
the rest of the system to work with trading operations without being tied
to specific broker implementations.

Contains:
- AlpacaManager: Primary broker integration (moved from execution module)
- alpaca_utils: Utility functions for Alpaca integration
- alpaca: Modular Alpaca implementation package
"""

from __future__ import annotations

# Conditional imports to handle missing dependencies
try:
    from .alpaca_manager import AlpacaManager, create_alpaca_manager
    __all__ = ["AlpacaManager", "create_alpaca_manager"]
except ImportError:
    # Handle cases where alpaca SDK is not available
    __all__ = []
