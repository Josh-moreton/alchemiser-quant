"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio state reader for building immutable snapshots from live data.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.errors.exceptions import NegativeCashBalanceError

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

    def _liquidate_and_recheck(self) -> tuple[Decimal, dict[str, Decimal]]:
        """Liquidate positions and re-check account state.

        Returns:
            Tuple of (updated_cash, updated_positions) after liquidation

        """
        logger.info(
            "Liquidation completed. Re-checking cash balance and positions...",
            module=MODULE_NAME,
            action="build_snapshot",
        )

        # Re-fetch positions (should be empty after liquidation)
        positions = self._data_adapter.get_positions()

        # Re-check cash balance after liquidation
        cash = self._data_adapter.get_account_cash()

        return cash, positions

    def _wait_for_settlement(
        self, max_wait_seconds: int = 30
    ) -> tuple[Decimal, dict[str, Decimal]]:
        """Wait for position liquidation to settle with polling and retry.

        Settlement can take time as positions need to be sold and cash needs
        to appear in the account balance. This method polls the account
        periodically to wait for the cash balance to become positive.

        Args:
            max_wait_seconds: Maximum time to wait for settlement

        Returns:
            Tuple of (updated_cash, updated_positions) after settlement

        """
        logger.info(
            f"Waiting up to {max_wait_seconds}s for liquidation settlement...",
            module=MODULE_NAME,
            action="wait_for_settlement",
        )

        start_time = time.time()
        poll_interval = 2.0  # Poll every 2 seconds
        attempt = 1

        while (time.time() - start_time) < max_wait_seconds:
            positions = self._data_adapter.get_positions()
            cash = self._data_adapter.get_account_cash()

            logger.debug(
                f"Settlement check #{attempt}: cash=${cash}, positions={len(positions)}",
                module=MODULE_NAME,
                action="wait_for_settlement",
                cash_balance=str(cash),
                position_count=len(positions),
                elapsed_seconds=round(time.time() - start_time, 1),
            )

            if cash > Decimal("0"):
                logger.info(
                    f"Settlement completed: cash balance recovered to ${cash} after {round(time.time() - start_time, 1)}s",
                    module=MODULE_NAME,
                    action="wait_for_settlement",
                    cash_balance=str(cash),
                    settlement_time_seconds=round(time.time() - start_time, 1),
                )
                return cash, positions

            attempt += 1
            time.sleep(poll_interval)

        # Timeout reached - get final state
        positions = self._data_adapter.get_positions()
        cash = self._data_adapter.get_account_cash()

        logger.warning(
            f"Settlement timeout after {max_wait_seconds}s: cash=${cash}, positions={len(positions)}",
            module=MODULE_NAME,
            action="wait_for_settlement",
            cash_balance=str(cash),
            position_count=len(positions),
            timeout_seconds=max_wait_seconds,
        )

        return cash, positions

    def _handle_negative_cash_balance(self, cash: Decimal) -> tuple[Decimal, dict[str, Decimal]]:
        """Handle negative cash balance through liquidation.

        Args:
            cash: Current cash balance

        Returns:
            Tuple of (updated_cash, updated_positions) after liquidation attempt

        Raises:
            NegativeCashBalanceError: If cash remains non-positive after liquidation

        """
        logger.error(
            f"Account has non-positive cash balance: ${cash}. Trading cannot proceed.",
            module=MODULE_NAME,
            action="build_snapshot",
            cash_balance=str(cash),
        )

        # Attempt to liquidate all positions
        liquidation_success = self._data_adapter.liquidate_all_positions()

        if not liquidation_success:
            raise NegativeCashBalanceError(
                f"Account cash balance is ${cash} and liquidation failed. Trading cannot proceed.",
                cash_balance=str(cash),
                module=MODULE_NAME,
            )

        # Re-check account state after liquidation with settlement waiting
        cash, positions = self._wait_for_settlement(max_wait_seconds=30)

        if cash > Decimal("0"):
            logger.info(
                "Cash balance recovered after liquidation. Continuing with trading.",
                module=MODULE_NAME,
                action="build_snapshot",
                cash_balance=str(cash),
            )
            return cash, positions

        # Cash still negative after liquidation
        logger.error(
            "Cash balance still non-positive after liquidation",
            module=MODULE_NAME,
            action="build_snapshot",
            cash_balance=str(cash),
        )
        raise NegativeCashBalanceError(
            f"Account cash balance is ${cash} after liquidation. Trading cannot proceed.",
            cash_balance=str(cash),
            module=MODULE_NAME,
        )

    def _calculate_portfolio_value(
        self, positions: dict[str, Decimal], prices: dict[str, Decimal], cash: Decimal
    ) -> Decimal:
        """Calculate total portfolio value from positions, prices and cash.

        Args:
            positions: Current positions
            prices: Current prices
            cash: Cash balance

        Returns:
            Total portfolio value

        Raises:
            ValueError: If price is missing for any position

        """
        position_value = Decimal("0")
        for symbol, quantity in positions.items():
            if symbol in prices:
                position_value += quantity * prices[symbol]
            else:
                raise ValueError(f"Missing price for position symbol: {symbol}")

        return position_value + cash

    def _create_and_validate_snapshot(
        self,
        positions: dict[str, Decimal],
        prices: dict[str, Decimal],
        cash: Decimal,
        total_value: Decimal,
    ) -> PortfolioSnapshot:
        """Create and validate portfolio snapshot.

        Args:
            positions: Current positions
            prices: Current prices
            cash: Cash balance
            total_value: Total portfolio value

        Returns:
            Validated PortfolioSnapshot

        """
        snapshot = PortfolioSnapshot(
            positions=positions, prices=prices, cash=cash, total_value=total_value
        )

        # Validate snapshot consistency
        if not snapshot.validate_total_value():
            logger.warning(
                "Snapshot total value validation failed - continuing anyway",
                module=MODULE_NAME,
                action="build_snapshot",
                calculated_total=str(snapshot.get_total_position_value() + snapshot.cash),
                snapshot_total=str(snapshot.total_value),
            )

        logger.debug(
            "Portfolio snapshot built successfully",
            module=MODULE_NAME,
            action="build_snapshot",
            position_count=len(positions),
            price_count=len(prices),
            total_value=str(total_value),
            cash_balance=str(cash),
            position_value=str(total_value - cash),
        )

        return snapshot

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
        logger.debug(
            "Building portfolio snapshot",
            module=MODULE_NAME,
            action="build_snapshot",
            requested_symbols=sorted(symbols) if symbols else None,
        )

        try:
            # Step 1: Get cash balance first
            cash = self._data_adapter.get_account_cash()

            # Check for negative or zero cash balance - liquidate and retry
            if cash <= Decimal("0"):
                cash, positions = self._handle_negative_cash_balance(cash)
                # After liquidation, positions should be empty, so no prices needed
                # But we still need to fetch prices for any requested symbols
                prices = {}
                if symbols:
                    prices = self._data_adapter.get_current_prices(list(symbols))
            else:
                # Step 2: Get current positions
                positions = self._data_adapter.get_positions()

                # Step 3: Determine which symbols we need prices for
                position_symbols = set(positions.keys())
                price_symbols = (
                    position_symbols if symbols is None else symbols.union(position_symbols)
                )

                # Step 4: Get current prices for all required symbols
                prices = {}
                if price_symbols:
                    prices = self._data_adapter.get_current_prices(list(price_symbols))

            # Step 5: Calculate total portfolio value
            total_value = self._calculate_portfolio_value(positions, prices, cash)

            # Step 6: Create and validate snapshot
            return self._create_and_validate_snapshot(positions, prices, cash, total_value)

        except Exception as e:
            logger.error(
                f"Failed to build portfolio snapshot: {e}",
                module=MODULE_NAME,
                action="build_snapshot",
                error=str(e),
            )
            raise
