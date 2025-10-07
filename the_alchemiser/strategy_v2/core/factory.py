#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy orchestrator factory for easy setup.

Provides factory functions for creating properly configured
strategy orchestrators with market data adapters.
"""

from __future__ import annotations

from ...shared.brokers.alpaca_manager import AlpacaManager
from ...shared.errors.exceptions import ConfigurationError
from ...shared.logging import get_logger
from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from .orchestrator import SingleStrategyOrchestrator

logger = get_logger(__name__)

# Component identifier for logging
_COMPONENT = "strategy_v2.core.factory"


def create_orchestrator(
    api_key: str, secret_key: str, *, paper: bool = True
) -> SingleStrategyOrchestrator:
    """Create a strategy orchestrator with Alpaca market data.

    Args:
        api_key: Alpaca API key (must not be empty)
        secret_key: Alpaca secret key (must not be empty)
        paper: Whether to use paper trading (default: True)

    Returns:
        Configured strategy orchestrator

    Raises:
        ConfigurationError: If API credentials are invalid or empty
        ValueError: If factory dependencies fail to initialize

    """
    # Input validation - prevent empty credentials
    if not api_key or not isinstance(api_key, str):
        logger.error(
            "Invalid API key provided to create_orchestrator",
            extra={"component": _COMPONENT, "error": "api_key is empty or invalid"},
        )
        raise ConfigurationError(
            "API key must be a non-empty string",
            config_key="api_key",
        )

    if not secret_key or not isinstance(secret_key, str):
        logger.error(
            "Invalid secret key provided to create_orchestrator",
            extra={"component": _COMPONENT, "error": "secret_key is empty or invalid"},
        )
        raise ConfigurationError(
            "Secret key must be a non-empty string",
            config_key="secret_key",
        )

    try:
        logger.info(
            "Creating strategy orchestrator with Alpaca adapter",
            extra={
                "component": _COMPONENT,
                "paper_mode": paper,
                "api_key_length": len(api_key),
            },
        )

        # Create Alpaca manager
        alpaca_manager = AlpacaManager(
            api_key=api_key, secret_key=secret_key, paper=paper
        )

        # Create market data adapter
        market_data_adapter = StrategyMarketDataAdapter(alpaca_manager)

        # Create orchestrator
        orchestrator = SingleStrategyOrchestrator(market_data_adapter)

        logger.info(
            "Strategy orchestrator created successfully",
            extra={"component": _COMPONENT, "paper_mode": paper},
        )

        return orchestrator

    except Exception as e:
        logger.error(
            f"Failed to create strategy orchestrator: {e}",
            extra={"component": _COMPONENT, "error_type": type(e).__name__},
        )
        raise


def create_orchestrator_with_adapter(
    market_data_adapter: StrategyMarketDataAdapter,
) -> SingleStrategyOrchestrator:
    """Create a strategy orchestrator with existing adapter.

    Args:
        market_data_adapter: Pre-configured market data adapter (must not be None)

    Returns:
        Strategy orchestrator

    Raises:
        ValueError: If market_data_adapter is None or invalid type

    """
    if market_data_adapter is None:
        logger.error(
            "None market_data_adapter provided to create_orchestrator_with_adapter",
            extra={"component": _COMPONENT},
        )
        raise ValueError("market_data_adapter must not be None")

    if not isinstance(market_data_adapter, StrategyMarketDataAdapter):
        logger.error(
            "Invalid market_data_adapter type provided",
            extra={
                "component": _COMPONENT,
                "provided_type": type(market_data_adapter).__name__,
            },
        )
        raise ValueError(
            f"market_data_adapter must be StrategyMarketDataAdapter, "
            f"got {type(market_data_adapter).__name__}"
        )

    logger.info(
        "Creating strategy orchestrator with provided adapter",
        extra={"component": _COMPONENT},
    )

    orchestrator = SingleStrategyOrchestrator(market_data_adapter)

    logger.info(
        "Strategy orchestrator created successfully with adapter",
        extra={"component": _COMPONENT},
    )

    return orchestrator
