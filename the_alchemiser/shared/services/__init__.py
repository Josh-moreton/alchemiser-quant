"""Business Unit: shared | Status: current..

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

    from the_alchemiser.execution.brokers.account_service import AccountService
    from the_alchemiser.execution.core.execution_manager import TradingServiceManager
"""

from __future__ import annotations

__all__ = [
    "account",
    "errors",
    "market_data",
    "repository",
    "shared",
    "trading",
]
