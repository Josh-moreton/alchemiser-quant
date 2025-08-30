"""Business Unit: strategy & signal generation | Status: current.

Bootstrap helper for Strategy context Lambda handlers.

Provides dependency injection and initialization for Strategy context use cases
while keeping AWS Lambda specifics isolated from application logic.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from the_alchemiser.anti_corruption.serialization.signal_serializer import SignalSerializer
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ConfigurationError
from the_alchemiser.strategy.application.use_cases.generate_signals import GenerateSignalsUseCase
from the_alchemiser.strategy.infrastructure.adapters.alpaca_market_data_adapter import (
    AlpacaMarketDataAdapter,
)
from the_alchemiser.strategy.infrastructure.adapters.event_bus_signal_publisher_adapter import (
    EventBusSignalPublisherAdapter,
)

logger = logging.getLogger(__name__)


class StrategyBootstrapContext:
    """Dependency bundle for Strategy Lambda handlers."""
    
    def __init__(
        self,
        generate_signals_use_case: GenerateSignalsUseCase,
        signal_serializer: SignalSerializer,
        config: Settings,
    ) -> None:
        self.generate_signals_use_case = generate_signals_use_case
        self.signal_serializer = signal_serializer
        self.config = config


def bootstrap_strategy_context() -> StrategyBootstrapContext:
    """Bootstrap Strategy context dependencies for Lambda execution.
    
    Constructs all required ports, adapters, and use cases while pulling
    configuration from environment variables.
    
    Returns:
        StrategyBootstrapContext with initialized dependencies
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    logger.info("Bootstrapping Strategy context for Lambda execution")
    
    try:
        # Load configuration from environment
        config = load_settings()
        
        # Create market data adapter (using Alpaca)
        # TODO: Add proper credential handling
        alpaca_api_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not alpaca_api_key or not alpaca_secret_key:
            raise ConfigurationError("Missing required Alpaca API credentials")
        
        market_data_adapter = AlpacaMarketDataAdapter(
            api_key=alpaca_api_key,
            secret_key=alpaca_secret_key,
            paper_trading=config.alpaca.paper_trading,
        )
        
        # Create signal publisher (using EventBus)
        signal_publisher = EventBusSignalPublisherAdapter()
        
        # Create use case
        generate_signals_use_case = GenerateSignalsUseCase(
            market_data=market_data_adapter,
            signal_publisher=signal_publisher,
        )
        
        # Create serializer for contract handling
        signal_serializer = SignalSerializer()
        
        logger.info("Strategy context bootstrap completed successfully")
        
        return StrategyBootstrapContext(
            generate_signals_use_case=generate_signals_use_case,
            signal_serializer=signal_serializer,
            config=config,
        )
        
    except Exception as e:
        logger.error(f"Failed to bootstrap Strategy context: {e}", exc_info=True)
        raise ConfigurationError(f"Strategy context bootstrap failed: {e}") from e