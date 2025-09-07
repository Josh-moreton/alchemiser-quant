"""Business Unit: portfolio | Status: current.

Common portfolio utility functions to eliminate code duplication.

This module provides shared utilities used by both PortfolioRebalancingService
and PortfolioAnalysisService to eliminate the duplication of position value
and portfolio value retrieval logic.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler

if TYPE_CHECKING:
    from the_alchemiser.execution.core.refactored_execution_manager import (
        RefactoredTradingServiceManager as TradingServiceManager,
    )


class PortfolioUtilities:
    """Shared utilities for portfolio operations.

    Provides common functionality for retrieving position values and portfolio
    totals from the trading manager, eliminating code duplication between
    portfolio services.
    """

    def __init__(self, trading_manager: TradingServiceManager) -> None:
        """Initialize with trading manager dependency.

        Args:
            trading_manager: Service for trading operations and market data

        """
        self.trading_manager = trading_manager

    def get_current_position_values(self) -> dict[str, Decimal]:
        """Get current position values from trading manager.

        Returns:
            Dictionary mapping symbol to market value for all positions with positive value

        """
        positions = self.trading_manager.get_all_positions()
        values: dict[str, Decimal] = {}
        for pos in positions:
            try:
                mv = Decimal(str(getattr(pos, "market_value", 0) or 0))
            except Exception:
                mv = Decimal("0")
            if mv > Decimal("0"):
                values[getattr(pos, "symbol", "")] = mv
        return values

    def get_portfolio_value(self) -> Decimal:
        """Get total portfolio value from trading manager.

        Returns:
            Decimal: The portfolio value

        Raises:
            ValueError: If portfolio_dto is None or portfolio_dto.value is not a valid Decimal

        """
        try:
            portfolio_dto = self.trading_manager.get_portfolio_value()

            # Defensive validation: ensure we got a valid PortfolioValueDTO
            if portfolio_dto is None:
                error_handler = TradingSystemErrorHandler()
                error = ValueError("Portfolio DTO is None - potential upstream schema drift")
                error_handler.handle_error(
                    error=error,
                    component="PortfolioUtilities.get_portfolio_value",
                    context="portfolio value retrieval",
                    additional_data={"portfolio_dto": None},
                )
                raise error

            # Defensive validation: ensure portfolio_dto.value is a valid Decimal
            if not isinstance(portfolio_dto.value, Decimal):
                error_handler = TradingSystemErrorHandler()
                error = ValueError(
                    f"Portfolio value is not a Decimal: {type(portfolio_dto.value)} - "
                    f"potential upstream schema drift"
                )
                error_handler.handle_error(
                    error=error,
                    component="PortfolioUtilities.get_portfolio_value",
                    context="portfolio value validation",
                    additional_data={
                        "portfolio_dto_type": str(type(portfolio_dto)),
                        "value_type": str(type(portfolio_dto.value)),
                        "value_repr": repr(portfolio_dto.value),
                    },
                )
                raise error

            return portfolio_dto.value

        except Exception as e:
            # Re-raise if already handled above, otherwise handle and re-raise
            if isinstance(e, ValueError) and "schema drift" in str(e):
                raise

            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
                error=e,
                component="PortfolioUtilities.get_portfolio_value",
                context="portfolio value retrieval - unexpected error",
                additional_data={"error_type": str(type(e))},
            )
            raise

    def get_portfolio_value_simple(self) -> Decimal:
        """Get total portfolio value with simple error handling.

        Simplified version for cases where the full error handling is not needed.
        Used by PortfolioAnalysisService.

        Returns:
            Decimal: The portfolio value

        """
        portfolio_dto = self.trading_manager.get_portfolio_value()
        # PortfolioValueDTO has a 'value' field that contains the Decimal
        return portfolio_dto.value
