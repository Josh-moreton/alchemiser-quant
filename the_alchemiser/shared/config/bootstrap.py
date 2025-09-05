#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Trading Engine Bootstrap Module.

Encapsulates all TradingEngine dependency injection and initialization paths
into dedicated bootstrap functions that return a typed context bundle.

This module extracts the complex initialization logic from TradingEngine
to improve separation of concerns and testability.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from the_alchemiser.execution.brokers.account_service import AccountService as TypedAccountService
from the_alchemiser.execution.brokers.alpaca import AlpacaManager
from the_alchemiser.execution.core.refactored_execution_manager import (
    RefactoredTradingServiceManager as TradingServiceManager,
)
from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.config.secrets_manager import SecretsManager
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.types.exceptions import ConfigurationError
from the_alchemiser.shared.utils.context import create_error_context
from the_alchemiser.strategy.data.market_data_service import MarketDataService


logger = logging.getLogger(__name__)


class TradingBootstrapContext(TypedDict):
    """Typed dependency bundle for TradingEngine initialization.

    This context carries all dependencies needed by TradingEngine,
    eliminating the need for complex initialization branching logic
    in the engine constructor.
    """

    account_service: TypedAccountService
    market_data_port: MarketDataService
    data_provider: MarketDataService  # DataFrame-compatible service
    alpaca_manager: AlpacaManager
    trading_client: Any  # Alpaca TradingClient
    trading_service_manager: TradingServiceManager | None
    paper_trading: bool
    config_dict: dict[str, Any]


def bootstrap_from_container(
    container: Any,
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies from full DI container.

    Args:
        container: DI container providing all services

    Returns:
        TradingBootstrapContext with all dependencies

    Raises:
        ConfigurationError: If container fails to provide required services

    """
    logger.info("Bootstrapping TradingEngine from DI container")

    try:
        # Core services from container
        account_service = container.services.account_service()
        alpaca_manager = container.infrastructure.alpaca_manager()
        market_data_port = container.infrastructure.market_data_service()

        # Use market data service directly (provides DataFrame compatibility)
        data_provider = market_data_port

        # Optional TradingServiceManager
        try:
            trading_service_manager = container.services.trading_service_manager()
        except (AttributeError, ConfigurationError, ImportError):
            trading_service_manager = None

        # Configuration from container
        paper_trading = container.config.paper_trading()
        config_dict = {
            "alpaca": {
                "api_key": container.config.alpaca_api_key(),
                "secret_key": container.config.alpaca_secret_key(),
                "paper_trading": paper_trading,
            }
        }

        logger.info("Successfully bootstrapped from DI container")
        return TradingBootstrapContext(
            account_service=account_service,
            market_data_port=market_data_port,
            data_provider=data_provider,
            alpaca_manager=alpaca_manager,
            trading_client=alpaca_manager.trading_client,
            trading_service_manager=trading_service_manager,
            paper_trading=paper_trading,
            config_dict=config_dict,
        )

    except (AttributeError, ValueError, ConfigurationError) as e:
        logger.error(f"Failed to bootstrap from DI container: {e}", exc_info=True)
        raise ConfigurationError(f"DI container failed to provide required services: {e}") from e


def bootstrap_from_service_manager(
    trading_service_manager: TradingServiceManager,
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies from TradingServiceManager.

    Args:
        trading_service_manager: Injected TradingServiceManager

    Returns:
        TradingBootstrapContext with all dependencies

    Raises:
        ConfigurationError: If service manager lacks required components

    """
    logger.info("Bootstrapping TradingEngine from TradingServiceManager")
    error_handler = TradingSystemErrorHandler()

    try:
        # Extract AlpacaManager from service manager
        alpaca_manager = trading_service_manager.alpaca_manager
        if alpaca_manager is None:
            raise ConfigurationError("TradingServiceManager missing AlpacaManager")

        # Extract trading client
        trading_client = alpaca_manager.trading_client
        if trading_client is None:
            raise ConfigurationError("AlpacaManager missing trading client")

        # Create market data service
        market_data_port = MarketDataService(alpaca_manager)

        # Use market data service directly (provides DataFrame compatibility)
        data_provider = market_data_port

        # Create account service using the same AlpacaManager
        account_service = TypedAccountService(alpaca_manager)

        paper_trading = alpaca_manager.is_paper_trading
        config_dict: dict[str, Any] = {}

        logger.info("Successfully bootstrapped from TradingServiceManager")
        return TradingBootstrapContext(
            account_service=account_service,
            market_data_port=market_data_port,
            data_provider=data_provider,
            alpaca_manager=alpaca_manager,
            trading_client=trading_client,
            trading_service_manager=trading_service_manager,
            paper_trading=paper_trading,
            config_dict=config_dict,
        )

    except (AttributeError, TypeError, ConfigurationError) as e:
        context = create_error_context(
            operation="bootstrap_from_service_manager",
            component="TradingBootstrap",
            function_name="bootstrap_from_service_manager",
            additional_data={
                "trading_service_manager_type": type(trading_service_manager).__name__
            },
        )
        error_handler.handle_error_with_context(error=e, context=context, should_continue=False)
        raise ConfigurationError(f"TradingServiceManager bootstrap failed: {e}") from e


def bootstrap_traditional(
    paper_trading: bool = True,
    config: Settings | None = None,
) -> TradingBootstrapContext:
    """Bootstrap TradingEngine dependencies using traditional method.

    This method creates dependencies directly using SecretsManager
    and AlpacaManager for backward compatibility.

    Args:
        paper_trading: Whether to use paper trading
        config: Configuration settings

    Returns:
        TradingBootstrapContext with all dependencies

    Raises:
        ConfigurationError: If credentials or initialization fails

    """
    logger.info("Bootstrapping TradingEngine using traditional method")

    # Load configuration
    try:
        resolved_config = config or load_settings()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise ConfigurationError(f"Configuration error: {e}") from e

    # Load credentials
    try:
        secrets_manager = SecretsManager()
        api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=paper_trading)

        if not api_key or not secret_key:
            raise ConfigurationError("Missing Alpaca credentials for traditional initialization")

    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        raise ConfigurationError(f"Credential error: {e}") from e

    # Initialize core dependencies
    try:
        # Core AlpacaManager
        alpaca_manager = AlpacaManager(str(api_key), str(secret_key), paper_trading)

        # Market data service
        market_data_port = MarketDataService(alpaca_manager)

        # Use market data service directly (provides DataFrame compatibility)
        data_provider = market_data_port

        # Account service
        account_service = TypedAccountService(alpaca_manager)

        # Enhanced service manager for downstream operations
        trading_service_manager = TradingServiceManager(
            str(api_key), str(secret_key), paper=paper_trading
        )

        config_dict = resolved_config.model_dump() if resolved_config else {}

        logger.info("Successfully bootstrapped using traditional method")
        return TradingBootstrapContext(
            account_service=account_service,
            market_data_port=market_data_port,
            data_provider=data_provider,
            alpaca_manager=alpaca_manager,
            trading_client=alpaca_manager.trading_client,
            trading_service_manager=trading_service_manager,
            paper_trading=paper_trading,
            config_dict=config_dict,
        )

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise ConfigurationError(f"Service initialization failed: {e}") from e
