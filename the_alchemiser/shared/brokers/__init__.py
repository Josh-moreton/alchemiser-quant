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

# Import AlpacaManager for backward compatibility
# Note: This may show deprecation warnings when instantiated
try:
    from .alpaca_manager import AlpacaManager, create_alpaca_manager

    _alpaca_available = True
except ImportError:
    # Handle cases where dependencies are not available
    _alpaca_available = False
    AlpacaManager = None  # type: ignore[misc,assignment]
    create_alpaca_manager = None  # type: ignore[assignment]

if _alpaca_available:
    __all__ = ["AlpacaManager", "create_alpaca_manager"]
else:
    __all__ = []
