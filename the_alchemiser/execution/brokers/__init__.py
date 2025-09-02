"""Broker API integrations.

Contains adapters for various broker APIs including Alpaca.
"""

from __future__ import annotations

from .alpaca import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]