"""Business Unit: scripts | Status: current.

Order fill simulation for backtesting.

Simulates market order fills at daily Open prices.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.models.market_data import DailyBar
from scripts.backtest.models.portfolio_snapshot import TradeRecord
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class FillSimulator:
    """Simulates order fills for backtesting.

    MVP implementation:
    - Market orders only
    - Fill at Open price of the trading day
    - No slippage modeling
    - Configurable commission per trade
    """

    def __init__(self, commission_per_trade: Decimal = Decimal("0")) -> None:
        """Initialize fill simulator.

        Args:
            commission_per_trade: Flat commission per trade

        """
        self.commission_per_trade = commission_per_trade
        logger.info(f"FillSimulator initialized with commission: {commission_per_trade}")

    def simulate_fill(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        bar: DailyBar,
    ) -> TradeRecord:
        """Simulate a market order fill at Open price.

        Args:
            symbol: Stock symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            bar: Market data bar for the trading day

        Returns:
            TradeRecord with execution details

        Raises:
            ValueError: If side is not BUY or SELL

        """
        if side not in ("BUY", "SELL"):
            error_msg = f"Invalid order side: {side}"
            raise ValueError(error_msg)

        if quantity <= 0:
            error_msg = f"Invalid quantity: {quantity}"
            raise ValueError(error_msg)

        # Fill at Open price
        fill_price = bar.open
        fill_time = bar.date

        # Calculate total cost
        if side == "BUY":
            total_cost = (fill_price * quantity) + self.commission_per_trade
        else:  # SELL
            total_cost = (fill_price * quantity) - self.commission_per_trade

        trade_record = TradeRecord(
            timestamp=fill_time,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=fill_price,
            commission=self.commission_per_trade,
            total_cost=total_cost,
        )

        logger.debug(
            f"Simulated {side} fill for {symbol}",
            symbol=symbol,
            side=side,
            quantity=str(quantity),
            price=str(fill_price),
            total_cost=str(total_cost),
        )

        return trade_record

    def simulate_multiple_fills(
        self,
        orders: list[tuple[str, str, Decimal]],
        bars: dict[str, DailyBar],
    ) -> list[TradeRecord]:
        """Simulate fills for multiple orders.

        Args:
            orders: List of (symbol, side, quantity) tuples
            bars: Dictionary mapping symbol to DailyBar

        Returns:
            List of TradeRecord objects

        """
        trades: list[TradeRecord] = []

        for symbol, side, quantity in orders:
            if symbol not in bars:
                logger.warning(
                    f"No market data for {symbol}, skipping order",
                    symbol=symbol,
                )
                continue

            try:
                trade = self.simulate_fill(symbol, side, quantity, bars[symbol])
                trades.append(trade)
            except Exception as e:
                logger.error(
                    f"Failed to simulate fill for {symbol}",
                    symbol=symbol,
                    error=str(e),
                )

        logger.info(f"Simulated {len(trades)} fills out of {len(orders)} orders")

        return trades
