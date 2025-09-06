"""Alpaca broker integration.

NOTE: AlpacaManager has been moved to shared.brokers for architectural compliance.
This module now re-exports for backward compatibility.
"""

from __future__ import annotations

# Re-export from shared module for backward compatibility
from the_alchemiser.shared.brokers import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
