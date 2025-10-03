"""Business Unit: shared | Status: current.

Order fill simulation for backtesting.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from scripts.backtest.models.market_data import HistoricalBar
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class SimulatedFill(BaseModel):
    """Result of a simulated order fill."""

    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str = Field(description="Trading symbol")
    action: str = Field(description="BUY or SELL")
    quantity: Decimal = Field(description="Shares filled")
    fill_price: Decimal = Field(description="Fill price (Open)")
    fill_value: Decimal = Field(description="Total fill value")
    commission: Decimal = Field(description="Commission charged", default=Decimal("0"))
    timestamp: datetime = Field(description="Fill timestamp")


class FillSimulator:
    """Simulates order fills for backtesting.
    
    MVP implementation:
    - Market orders only
    - Fills at Open price of the trading day
    - No slippage modeling
    - Configurable flat commission per trade
    """

    def __init__(self, commission_per_trade: Decimal = Decimal("0")) -> None:
        """Initialize fill simulator.
        
        Args:
            commission_per_trade: Flat commission per trade (default: 0)

        """
        self.commission_per_trade = commission_per_trade
        self.logger = logger

    def simulate_market_order(
        self,
        symbol: str,
        action: str,
        quantity: Decimal,
        bar: HistoricalBar,
    ) -> SimulatedFill:
        """Simulate a market order fill at Open price.
        
        Args:
            symbol: Trading symbol
            action: "BUY" or "SELL"
            quantity: Number of shares to trade
            bar: Historical bar containing Open price
            
        Returns:
            Simulated fill result
            
        Raises:
            ValueError: If action is invalid or quantity is non-positive

        """
        if action not in ("BUY", "SELL"):
            raise ValueError(f"Invalid action: {action}. Must be BUY or SELL")

        if quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}. Must be positive")

        # Fill at Open price (simulating market-on-open order)
        fill_price = bar.open_price
        fill_value = fill_price * quantity

        fill = SimulatedFill(
            symbol=symbol,
            action=action,
            quantity=quantity,
            fill_price=fill_price,
            fill_value=fill_value,
            commission=self.commission_per_trade,
            timestamp=bar.date,
        )

        self.logger.debug(
            f"Simulated {action} fill: {quantity} shares of {symbol} @ {fill_price}",
            extra={
                "symbol": symbol,
                "action": action,
                "quantity": str(quantity),
                "fill_price": str(fill_price),
                "commission": str(self.commission_per_trade),
            },
        )

        return fill

    def simulate_rebalance(
        self,
        trades: dict[str, tuple[str, Decimal]],
        bars: dict[str, HistoricalBar],
    ) -> list[SimulatedFill]:
        """Simulate multiple trades for a rebalance operation.
        
        Args:
            trades: Dictionary mapping symbol to (action, quantity) tuples
            bars: Dictionary mapping symbol to historical bar
            
        Returns:
            List of simulated fills

        """
        fills: list[SimulatedFill] = []

        for symbol, (action, quantity) in trades.items():
            if quantity == 0:
                continue

            if symbol not in bars:
                self.logger.warning(
                    f"No bar data for {symbol}, skipping trade",
                    extra={"symbol": symbol, "action": action},
                )
                continue

            try:
                fill = self.simulate_market_order(symbol, action, quantity, bars[symbol])
                fills.append(fill)
            except Exception as e:
                self.logger.error(
                    f"Failed to simulate fill for {symbol}: {e}",
                    extra={"symbol": symbol, "error": str(e)},
                )

        return fills

    def calculate_total_cost(
        self, fills: list[SimulatedFill], include_commission: bool = True
    ) -> Decimal:
        """Calculate total cost of fills.
        
        Args:
            fills: List of simulated fills
            include_commission: Whether to include commissions in total
            
        Returns:
            Total cost (negative for SELL, positive for BUY)

        """
        total = Decimal("0")

        for fill in fills:
            value = fill.fill_value
            if fill.action == "SELL":
                value = -value  # Selling brings in cash

            if include_commission:
                value -= fill.commission

            total += value

        return total
