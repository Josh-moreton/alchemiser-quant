"""Business Unit: execution | Status: current.

Services module for execution_v2.

This package contains services for the execution layer:
- TradeLedgerService: Records filled orders to trade ledger with S3 persistence

Import from this module for convenience:
    from the_alchemiser.execution_v2.services import TradeLedgerService

Or import directly from submodules:
    from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
"""

from __future__ import annotations

from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService

__all__ = ["TradeLedgerService"]

# Version for compatibility tracking
__version__ = "2.0.0"
