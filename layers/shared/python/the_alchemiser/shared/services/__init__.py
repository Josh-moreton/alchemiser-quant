"""Business Unit: shared | Status: current.

Service layer package.

Lightweight package initializer for the restructured service layer. The
concrete services now live in dedicated subpackages:

- account: Account and position management services
- market_data: Market data retrieval and streaming services
- trading: Order execution and position services/facade
- repository: External provider implementations (e.g., AlpacaManager)
- shared: Cross-cutting concerns (config, secrets, cache, retry)
- errors: Error handling, reporting and exceptions

Note: We intentionally avoid re-exporting concrete classes at the package root
to prevent import-time side effects and circular import issues. Import directly
from the relevant subpackage, for example:

    from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
"""

from __future__ import annotations

# IMPORTANT: No eager imports at package level to avoid import-time side effects.
# This prevents coordinator_v2 (and other lightweight Lambdas) from requiring
# heavy dependencies like alpaca-py when they only need specific services.
#
# Import directly from the appropriate service submodule:
#   from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService
#   from the_alchemiser.shared.services.buying_power_service import BuyingPowerService
#   from the_alchemiser.shared.services.market_clock_service import MarketClockService
#
# This follows the coding guidelines: no hidden I/O or heavy imports in module init.

__all__: list[str] = []
