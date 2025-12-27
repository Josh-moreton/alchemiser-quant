"""Business Unit: execution | Status: current.

Services module for execution_v2.

This package contains services for the execution layer:
- TradeLedgerService: Records filled orders to trade ledger with S3 persistence
- ExecutionRunService: Manages per-trade execution run state in DynamoDB (re-exported from shared)

Import from this module for convenience:
    from the_alchemiser.execution_v2.services import TradeLedgerService, ExecutionRunService

Or import directly from submodules:
    from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
    from the_alchemiser.shared.services.execution_run_service import ExecutionRunService
"""

from __future__ import annotations

from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService

# ExecutionRunService is in shared/ for cross-module access
from the_alchemiser.shared.services.execution_run_service import (
    ExecutionRunService,
)

__all__ = ["ExecutionRunService", "TradeLedgerService"]

# Version for compatibility tracking
__version__ = "2.0.0"
