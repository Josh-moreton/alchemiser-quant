"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio state reader for building immutable snapshots from live data.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger, log_with_context
from the_alchemiser.shared.types.exceptions import NegativeCashBalanceError

if TYPE_CHECKING:
    from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
        AlpacaDataAdapter,
    )

from ..models.portfolio_snapshot import PortfolioSnapshot

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.core.state_reader"


class PortfolioStateReader:
    """Build immutable portfolio snapshots from live market data.

    Coordinates data fetching from AlpacaDataAdapter and constructs
    consistent PortfolioSnapshot instances for rebalancing calculations.
    """

    def __init__(self, data_adapter: AlpacaDataAdapter) -> None:
        """Initialize state reader with data adapter.

        Args:
            data_adapter: AlpacaDataAdapter for market data access

        """
        self._data_adapter = data_adapter

    def build_portfolio_snapshot(self, symbols: set[str] | None = None) -> PortfolioSnapshot:
        """Build current portfolio snapshot with positions, prices, and cash.

        Args:
            symbols: Optional set of symbols to include prices for.
                    If None, includes all symbols from current positions.

        Returns:
            PortfolioSnapshot with current state

        Raises:
            Exception: If snapshot cannot be built due to data errors

        """
        log_with_context(
            logger,
            logging.DEBUG,
            "Building portfolio snapshot",
            module=MODULE_NAME,
            action="build_snapshot",
            requested_symbols=sorted(symbols) if symbols else None,
        )

        try:
            # Step 1: Get current positions
            positions = self._data_adapter.get_positions()

            # Step 2: Determine which symbols we need prices for
            position_symbols = set(positions.keys())
            price_symbols = position_symbols if symbols is None else symbols.union(position_symbols)

            # Step 3: Get current prices for all required symbols
            prices = {}
            if price_symbols:
                prices = self._data_adapter.get_current_prices(list(price_symbols))

            # Step 4: Get cash balance
            cash = self._data_adapter.get_account_cash()

            # Check for negative or zero cash balance - graceful exit condition
            if cash <= Decimal("0"):
                log_with_context(
                    logger,
                    logging.ERROR,
                    f"Account has non-positive cash balance: ${cash}. Trading cannot proceed.",
                    module=MODULE_NAME,
                    action="build_snapshot",
                    cash_balance=str(cash),
                )
                raise NegativeCashBalanceError(
                    f"Account cash balance is ${cash}. Trading requires positive cash balance.",
                    cash_balance=str(cash),
                    module=MODULE_NAME,
                )

            # Step 5: Calculate total portfolio value
            position_value = Decimal("0")
            for symbol, quantity in positions.items():
                if symbol in prices:
                    position_value += quantity * prices[symbol]
                else:
                    # This should not happen if our logic is correct
                    raise ValueError(f"Missing price for position symbol: {symbol}")

            total_value = position_value + cash

            # Step 6: Create and validate snapshot
            snapshot = PortfolioSnapshot(
                positions=positions, prices=prices, cash=cash, total_value=total_value
            )

            # Validate snapshot consistency
            if not snapshot.validate_total_value():
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Snapshot total value validation failed - continuing anyway",
                    module=MODULE_NAME,
                    action="build_snapshot",
                    calculated_total=str(snapshot.get_total_position_value() + snapshot.cash),
                    snapshot_total=str(snapshot.total_value),
                )

            log_with_context(
                logger,
                logging.DEBUG,
                "Portfolio snapshot built successfully",
                module=MODULE_NAME,
                action="build_snapshot",
                position_count=len(positions),
                price_count=len(prices),
                total_value=str(total_value),
                cash_balance=str(cash),
                position_value=str(position_value),
            )

            return snapshot

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to build portfolio snapshot: {e}",
                module=MODULE_NAME,
                action="build_snapshot",
                error=str(e),
            )
            raise
