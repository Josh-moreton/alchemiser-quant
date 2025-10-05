#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy orchestrator factory for easy setup.

Provides factory functions for creating properly configured
strategy orchestrators with market data adapters.
"""

from __future__ import annotations

from ...shared.brokers.alpaca_manager import AlpacaManager
from ...shared.logging import get_logger
from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from .orchestrator import SingleStrategyOrchestrator

logger = get_logger(__name__)

# Component identifier for structured logging
_FACTORY_COMPONENT = "strategy_v2.core.factory"


def create_orchestrator(
    api_key: str, secret_key: str, *, paper: bool = True
) -> SingleStrategyOrchestrator:
    """Create a strategy orchestrator with Alpaca market data.

    Args:
        api_key: Alpaca API key (non-empty string)
        secret_key: Alpaca secret key (non-empty string)
        paper: Whether to use paper trading (default: True)

    Returns:
        Configured strategy orchestrator

    Raises:
        ValueError: If api_key or secret_key is empty or invalid
        RuntimeError: If Alpaca manager or adapter initialization fails

    Example:
        >>> orchestrator = create_orchestrator(
        ...     api_key=os.environ["ALPACA_API_KEY"],
        ...     secret_key=os.environ["ALPACA_SECRET_KEY"],
        ...     paper=True
        ... )
        >>> allocation = orchestrator.run("nuclear", context)

    """
    # Input validation - fail-closed security posture
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        logger.error(
            "Invalid API key provided to factory",
            extra={"component": _FACTORY_COMPONENT, "paper": paper},
        )
        raise ValueError("API key must be a non-empty string")

    if not secret_key or not isinstance(secret_key, str) or not secret_key.strip():
        logger.error(
            "Invalid secret key provided to factory",
            extra={"component": _FACTORY_COMPONENT, "paper": paper},
        )
        raise ValueError("Secret key must be a non-empty string")

    try:
        logger.info(
            "Creating strategy orchestrator with Alpaca adapter",
            extra={
                "component": _FACTORY_COMPONENT,
                "paper": paper,
                # NOTE: Never log api_key or secret_key values (security)
            },
        )

        # Create Alpaca manager
        alpaca_manager = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper)

        # Create market data adapter
        market_data_adapter = StrategyMarketDataAdapter(alpaca_manager)

        # Create orchestrator
        orchestrator = SingleStrategyOrchestrator(market_data_adapter)

        logger.info(
            "Strategy orchestrator created successfully",
            extra={"component": _FACTORY_COMPONENT, "paper": paper},
        )

        return orchestrator

    except Exception as e:
        logger.error(
            f"Failed to create strategy orchestrator: {e}",
            extra={
                "component": _FACTORY_COMPONENT,
                "paper": paper,
                "error_type": type(e).__name__,
            },
        )
        raise


def create_orchestrator_with_adapter(
    market_data_adapter: StrategyMarketDataAdapter,
) -> SingleStrategyOrchestrator:
    """Create a strategy orchestrator with existing adapter.

    Args:
        market_data_adapter: Pre-configured market data adapter (non-None)

    Returns:
        Strategy orchestrator

    Raises:
        TypeError: If market_data_adapter is None or invalid type

    Example:
        >>> alpaca_manager = AlpacaManager(api_key, secret_key)
        >>> adapter = StrategyMarketDataAdapter(alpaca_manager)
        >>> orchestrator = create_orchestrator_with_adapter(adapter)

    """
    # Input validation - type checking
    if market_data_adapter is None:
        logger.error(
            "None adapter provided to factory",
            extra={"component": _FACTORY_COMPONENT},
        )
        raise TypeError("market_data_adapter cannot be None")

    if not isinstance(market_data_adapter, StrategyMarketDataAdapter):
        logger.error(
            f"Invalid adapter type: {type(market_data_adapter).__name__}",
            extra={
                "component": _FACTORY_COMPONENT,
                "provided_type": type(market_data_adapter).__name__,
            },
        )
        raise TypeError(
            f"market_data_adapter must be StrategyMarketDataAdapter, "
            f"got {type(market_data_adapter).__name__}"
        )

    logger.debug(
        "Creating strategy orchestrator with provided adapter",
        extra={"component": _FACTORY_COMPONENT},
    )

    return SingleStrategyOrchestrator(market_data_adapter)

