"""Business Unit: shared | Status: current.

Broker abstractions and utilities.

This package provides broker-agnostic interfaces and utilities that allow
the rest of the system to work with trading operations without being tied
to specific broker implementations.

Contains:
- AlpacaManager: Primary broker integration (moved from execution module)
- alpaca_utils: Utility functions for Alpaca integration
"""

from __future__ import annotations

from .alpaca_manager import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
