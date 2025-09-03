"""Business Unit: execution | Status: current.

Alpaca broker adapter implementation.

This module provides the main interface to the Alpaca broker platform
including account management, order execution, and market data integration.
"""

from __future__ import annotations

from .adapter import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
