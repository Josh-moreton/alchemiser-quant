"""Business Unit: utilities; Status: current.

Trading System Coordinator.

Coordinates between the three bounded context application services:
- StrategyApplication (market data, signals)
- PortfolioApplication (accounts, positions, valuation)
- ExecutionApplication (orders, execution)

This replaces the monolithic TradingServiceManager with a thin coordination layer
that follows DDD principles by not containing business logic but only orchestrating
calls between bounded contexts via their published application interfaces.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from the_alchemiser.strategy.application.strategy_application import StrategyApplication
from the_alchemiser.portfolio.application.portfolio_application import PortfolioApplication
from the_alchemiser.execution.application.execution_application import ExecutionApplication

if TYPE_CHECKING:
    from the_alchemiser.infrastructure.repositories.alpaca_manager import AlpacaManager


class TradingSystemCoordinator:
    """Coordinates trading operations across bounded contexts."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize trading system coordinator."""
        self.logger = logging.getLogger(__name__)
        
        # Import here to avoid circular dependencies
        from the_alchemiser.infrastructure.repositories.alpaca_manager import AlpacaManager
        
        # Single shared infrastructure adapter
        self.alpaca_manager = AlpacaManager(api_key, secret_key, paper)
        
        # Initialize bounded context application services
        self.strategy = StrategyApplication(self.alpaca_manager)
        self.portfolio = PortfolioApplication(self.alpaca_manager)
        self.execution = ExecutionApplication(self.alpaca_manager)
        
        self.logger.info(f"TradingSystemCoordinator initialized with paper={paper}")

    def close(self) -> None:
        """Close all connections."""
        try:
            if hasattr(self.alpaca_manager, 'close'):
                self.alpaca_manager.close()
            self.logger.info("TradingSystemCoordinator closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing TradingSystemCoordinator: {e}")

    # For backward compatibility during migration, expose context services
    @property
    def orders(self):
        """Access to execution context order service."""
        return self.execution.orders

    @property
    def positions(self):
        """Access to execution context position service."""
        return self.execution.positions

    @property
    def market_data(self):
        """Access to strategy context market data service."""
        return self.strategy.market_data

    @property
    def account(self):
        """Access to portfolio context account service."""
        return self.portfolio.account