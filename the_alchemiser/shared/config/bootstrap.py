#!/usr/bin/env python3
"""Business Unit: execution | Status: legacy.

Trading Engine Bootstrap Module.

DEPRECATED: This module is being migrated to use execution_v2.
Legacy imports commented out to remove fallback dependencies.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

# Legacy imports migrated to v2 architecture:
# - AccountService → Use AlpacaManager from shared.brokers
# - TradingServiceManager → Use ExecutionManager from execution_v2.core
from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.types.exceptions import ConfigurationError


def _get_market_data_service():
    """Lazy import MarketDataService to avoid circular imports."""
    # Legacy import migrated to v2 architecture:
    # Use strategy_v2.data.market_data_service.MarketDataService instead
    raise ConfigurationError("Legacy MarketDataService not available - use v2 modules instead")


logger = logging.getLogger(__name__)


class TradingBootstrapContext(TypedDict):
    """Typed dependency bundle for TradingEngine initialization.

    DEPRECATED: This context is being migrated to use execution_v2.
    """

    # account_service: Use AlpacaManager instead (migrated to shared.brokers)
    # market_data_port: Use strategy_v2.data.market_data_service instead
    # data_provider: Use strategy_v2.data providers instead
    alpaca_manager: AlpacaManager
    trading_client: Any  # Alpaca TradingClient
    # trading_service_manager: Use ExecutionManager from execution_v2 instead
    paper_trading: bool
    config_dict: dict[str, Any]


def bootstrap_from_container(
    container: Any,
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies from full DI container.

    DEPRECATED: This function uses legacy execution modules.
    Use execution_v2.ExecutionManager instead.
    """
    raise ConfigurationError(
        "Legacy bootstrap_from_container is deprecated. "
        "Use execution_v2.ExecutionManager directly instead."
    )


def bootstrap_from_service_manager(
    trading_service_manager: Any,  # TradingServiceManager - legacy type
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies from TradingServiceManager.

    DEPRECATED: This function uses legacy execution modules.
    Use execution_v2.ExecutionManager instead.
    """
    raise ConfigurationError(
        "Legacy bootstrap_from_service_manager is deprecated. "
        "Use execution_v2.ExecutionManager directly instead."
    )


def bootstrap_traditional(
    paper_trading: bool | None = None,
    config: Settings | None = None,
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies using traditional method.

    DEPRECATED: This function uses legacy execution modules.
    Use execution_v2.ExecutionManager instead.
    """
    raise ConfigurationError(
        "Legacy bootstrap_traditional is deprecated. "
        "Use execution_v2.ExecutionManager.create_with_config instead."
    )
