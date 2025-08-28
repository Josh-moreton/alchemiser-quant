"""Business Unit: utilities; Status: current.

Service layer package for cross-cutting concerns.

This package contains shared utilities and cross-cutting concerns that are used
across multiple bounded contexts:

- errors: Error handling, reporting and exceptions
- shared: Cross-cutting concerns (config, secrets, cache, retry)
- trading: TradingServiceManager facade (pending context-aware refactoring)

The domain-specific services have been migrated to their respective bounded contexts:
- Account/portfolio services → portfolio/infrastructure/adapters/
- Market data services → strategy/infrastructure/market_data/
- Order services → execution/application/orders/
- Repository implementations → execution/infrastructure/brokers/

Note: We intentionally avoid re-exporting concrete classes at the package root
to prevent import-time side effects and circular import issues. Import directly
from the relevant subpackage, for example:

    from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager
    from the_alchemiser.services.errors.exceptions import TradingError
"""

from __future__ import annotations

__all__ = [
    "errors",
    "shared", 
    "trading",
]
