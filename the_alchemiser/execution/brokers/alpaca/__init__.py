"""Business Unit: execution | Status: current

Alpaca broker adapter implementation.
"""

from __future__ import annotations

from .adapter import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]