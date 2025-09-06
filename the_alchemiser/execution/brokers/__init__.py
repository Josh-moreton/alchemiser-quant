"""Broker API integrations.

Contains adapters for various broker APIs including Alpaca.

NOTE: AlpacaManager has been moved to shared.brokers for architectural compliance.
This module now re-exports for backward compatibility.
"""

from __future__ import annotations

from .alpaca import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
