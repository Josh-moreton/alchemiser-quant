"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Alpaca data adapter - thin wrapper around shared.brokers.AlpacaManager
for portfolio-specific data access.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging.logging_utils import log_with_context

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.adapters.alpaca_data_adapter"


class AlpacaDataAdapter:
    """Adapter for accessing portfolio data via shared AlpacaManager.

    Provides a clean interface for portfolio_v2 to access positions,
    prices, and account data without directly depending on Alpaca APIs.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize adapter with AlpacaManager instance.

        Args:
            alpaca_manager: Shared AlpacaManager instance

        """
        self._alpaca_manager = alpaca_manager

    def get_positions(self) -> dict[str, Decimal]:
        """Get current positions as symbol -> quantity mapping.

        Returns:
            Dictionary mapping symbol to quantity (Decimal shares)

        Raises:
            Exception: If positions cannot be retrieved

        """
        log_with_context(
            logger,
            logging.INFO,
            "Fetching current positions",
            module=MODULE_NAME,
            action="get_positions",
        )

        try:
            # Get positions from AlpacaManager
            raw_positions = self._alpaca_manager.get_positions()

            # Convert to symbol -> quantity mapping with Decimal precision
            # Use qty_available instead of qty to account for shares tied up in open orders
            positions = {}
            for position in raw_positions:
                symbol = str(position.symbol).upper()
                # Use qty_available if available, fallback to qty for compatibility
                available_qty = getattr(position, "qty_available", None)
                if available_qty is not None:
                    quantity = Decimal(str(available_qty))
                else:
                    # Fallback to total qty if qty_available is not available
                    quantity = Decimal(str(position.qty))
                positions[symbol] = quantity

            log_with_context(
                logger,
                logging.INFO,
                f"Retrieved {len(positions)} positions",
                module=MODULE_NAME,
                action="get_positions",
                position_count=len(positions),
                symbols=sorted(positions.keys()),
            )

            return positions

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to retrieve positions: {e}",
                module=MODULE_NAME,
                action="get_positions",
                error=str(e),
            )
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, Decimal]:
        """Get current prices for specified symbols.

        Args:
            symbols: List of trading symbols

        Returns:
            Dictionary mapping symbol to current price (Decimal)

        Raises:
            Exception: If prices cannot be retrieved

        """
        if not symbols:
            return {}

        log_with_context(
            logger,
            logging.INFO,
            f"Fetching current prices for {len(symbols)} symbols",
            module=MODULE_NAME,
            action="get_current_prices",
            symbols=sorted(symbols),
        )

        try:
            prices = {}

            # Get prices individually using structured pricing approach
            # Enhanced market data: using current price method with proper error handling
            # Future enhancement: Migrate to QuoteModel and PriceDataModel for richer analytics
            for symbol in symbols:
                symbol_upper = symbol.upper()
                raw_price = self._alpaca_manager.get_current_price(symbol_upper)

                if raw_price is None or raw_price <= 0:
                    raise ValueError(f"Invalid price for {symbol_upper}: {raw_price}")

                prices[symbol_upper] = Decimal(str(raw_price))

            log_with_context(
                logger,
                logging.INFO,
                f"Retrieved prices for {len(prices)} symbols",
                module=MODULE_NAME,
                action="get_current_prices",
                symbol_count=len(prices),
            )

            return prices

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to retrieve prices: {e}",
                module=MODULE_NAME,
                action="get_current_prices",
                error=str(e),
            )
            raise

    def get_account_cash(self) -> Decimal:
        """Get current cash balance.

        Returns:
            Cash balance as Decimal

        Raises:
            Exception: If account data cannot be retrieved

        """
        log_with_context(
            logger,
            logging.INFO,
            "Fetching account cash balance",
            module=MODULE_NAME,
            action="get_account_cash",
        )

        try:
            account_info = self._alpaca_manager.get_account()
            cash = Decimal(str(account_info.cash))

            log_with_context(
                logger,
                logging.INFO,
                f"Retrieved cash balance: ${cash}",
                module=MODULE_NAME,
                action="get_account_cash",
                cash_balance=str(cash),
            )

            return cash

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to retrieve cash balance: {e}",
                module=MODULE_NAME,
                action="get_account_cash",
                error=str(e),
            )
            raise
