"""Business Unit: backtest | Status: current.

Portfolio simulator for backtesting.

Simulates portfolio state over time by tracking positions, cash, and
executing rebalance trades with slippage and commission models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.backtest_v2.core.result import Trade
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.backtest_v2.adapters.historical_market_data import (
        BacktestMarketDataAdapter,
    )

logger = get_logger(__name__)

# Module constant
MODULE_NAME = "backtest_v2.core.simulator"


@dataclass
class Position:
    """Represents a position in a single asset.

    Attributes:
        symbol: Trading symbol
        shares: Number of shares held (can be fractional)
        cost_basis: Average cost per share
        current_price: Latest market price

    """

    symbol: str
    shares: Decimal
    cost_basis: Decimal
    current_price: Decimal

    @property
    def market_value(self) -> Decimal:
        """Current market value of position."""
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit/loss."""
        return self.shares * (self.current_price - self.cost_basis)

    @property
    def unrealized_pnl_pct(self) -> Decimal:
        """Unrealized P&L as percentage of cost basis."""
        if self.cost_basis == 0:
            return Decimal("0")
        return (self.current_price - self.cost_basis) / self.cost_basis


@dataclass
class PortfolioState:
    """Snapshot of portfolio at a point in time.

    Attributes:
        date: Snapshot date
        cash: Available cash
        positions: Dict of symbol -> Position
        total_value: Total portfolio value (cash + positions)

    """

    date: datetime
    cash: Decimal
    positions: dict[str, Position]

    @property
    def total_value(self) -> Decimal:
        """Total portfolio value including cash and positions."""
        position_value = sum(p.market_value for p in self.positions.values())
        return self.cash + position_value

    @property
    def position_weights(self) -> dict[str, Decimal]:
        """Current portfolio weights by symbol."""
        total = self.total_value
        if total == 0:
            return {}

        weights = {}
        for symbol, pos in self.positions.items():
            weights[symbol] = pos.market_value / total

        # Add cash weight
        weights["CASH"] = self.cash / total
        return weights

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat(),
            "cash": str(self.cash),
            "positions": {
                sym: {
                    "shares": str(pos.shares),
                    "cost_basis": str(pos.cost_basis),
                    "current_price": str(pos.current_price),
                    "market_value": str(pos.market_value),
                }
                for sym, pos in self.positions.items()
            },
            "total_value": str(self.total_value),
        }


@dataclass
class PortfolioSimulator:
    """Simulates portfolio rebalancing with transaction costs.

    Tracks positions and cash over time, executes rebalance trades
    with configurable slippage and commission models.

    Attributes:
        market_data: Historical market data adapter for prices
        slippage_bps: Slippage in basis points
        commission_per_share: Commission per share traded
        cash: Current cash balance
        positions: Current positions
        trades: List of executed trades
        equity_history: List of (date, portfolio_value) tuples

    """

    market_data: BacktestMarketDataAdapter
    slippage_bps: Decimal = Decimal("5")
    commission_per_share: Decimal = Decimal("0")
    cash: Decimal = field(default=Decimal("100000"))
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    equity_history: list[tuple[datetime, Decimal]] = field(default_factory=list)

    def initialize(self, initial_capital: Decimal) -> None:
        """Initialize simulator with starting capital.

        Args:
            initial_capital: Starting cash amount

        """
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_history = []

        logger.info(
            "PortfolioSimulator initialized",
            module=MODULE_NAME,
            initial_capital=str(initial_capital),
        )

    def get_current_state(self, date: datetime) -> PortfolioState:
        """Get current portfolio state with updated prices.

        Args:
            date: Current simulation date

        Returns:
            PortfolioState snapshot

        """
        # Update position prices
        for symbol, pos in self.positions.items():
            price = self.market_data.get_close_price_on_date(symbol, date)
            if price is not None:
                # Create new position with updated price (Position is mutable)
                self.positions[symbol] = Position(
                    symbol=pos.symbol,
                    shares=pos.shares,
                    cost_basis=pos.cost_basis,
                    current_price=Decimal(str(price)),
                )

        return PortfolioState(
            date=date,
            cash=self.cash,
            positions=self.positions.copy(),
        )

    def _calculate_slippage(self, price: Decimal, *, is_buy: bool) -> Decimal:
        """Calculate execution price with slippage.

        Slippage works against the trader: buys execute higher, sells lower.

        Args:
            price: Base price
            is_buy: True for buy orders, False for sell

        Returns:
            Price after slippage

        """
        slippage_pct = self.slippage_bps / Decimal("10000")
        if is_buy:
            return price * (1 + slippage_pct)
        return price * (1 - slippage_pct)

    def _execute_trade(
        self,
        date: datetime,
        symbol: str,
        target_shares: Decimal,
        current_shares: Decimal,
        price: Decimal,
    ) -> Trade | None:
        """Execute a single trade.

        Args:
            date: Trade date
            symbol: Symbol to trade
            target_shares: Target position size
            current_shares: Current position size
            price: Base execution price

        Returns:
            Trade record or None if no trade needed

        """
        shares_delta = target_shares - current_shares

        if abs(shares_delta) < Decimal("0.001"):
            return None  # No trade needed

        is_buy = shares_delta > 0
        action = "BUY" if is_buy else "SELL"
        shares_to_trade = abs(shares_delta)

        # Apply slippage
        exec_price = self._calculate_slippage(price, is_buy=is_buy)

        # Calculate trade value and commission
        trade_value = shares_to_trade * exec_price
        commission = shares_to_trade * self.commission_per_share

        # Update cash
        if is_buy:
            self.cash -= trade_value + commission
        else:
            self.cash += trade_value - commission

        # Update position
        if symbol in self.positions:
            pos = self.positions[symbol]
            if is_buy:
                # Update cost basis for buys
                total_cost = pos.shares * pos.cost_basis + shares_to_trade * exec_price
                new_shares = pos.shares + shares_to_trade
                new_cost_basis = total_cost / new_shares if new_shares > 0 else Decimal("0")
            else:
                new_shares = pos.shares - shares_to_trade
                new_cost_basis = pos.cost_basis  # Keep original cost basis

            if new_shares > Decimal("0.001"):
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=new_shares,
                    cost_basis=new_cost_basis,
                    current_price=exec_price,
                )
            else:
                # Position closed
                del self.positions[symbol]
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares_to_trade,
                cost_basis=exec_price,
                current_price=exec_price,
            )

        trade = Trade(
            date=date,
            symbol=symbol,
            action=action,
            shares=shares_to_trade,
            price=exec_price,
            commission=commission,
            value=trade_value,
        )

        self.trades.append(trade)

        logger.debug(
            "Trade executed",
            module=MODULE_NAME,
            date=date.isoformat(),
            symbol=symbol,
            action=action,
            shares=str(shares_to_trade),
            price=str(exec_price),
            commission=str(commission),
        )

        return trade

    def rebalance(
        self,
        date: datetime,
        target_weights: dict[str, Decimal],
    ) -> list[Trade]:
        """Rebalance portfolio to target weights.

        Executes trades to align portfolio with target allocation.
        Sells first to free up cash, then buys.

        Args:
            date: Rebalance date
            target_weights: Dict of symbol -> target weight (0-1)

        Returns:
            List of executed trades

        """
        # Update as_of for market data
        self.market_data.set_as_of(date)

        # Get current state with updated prices
        state = self.get_current_state(date)
        total_value = state.total_value

        logger.debug(
            "Starting rebalance",
            module=MODULE_NAME,
            date=date.isoformat(),
            total_value=str(total_value),
            target_symbols=list(target_weights.keys()),
        )

        # Calculate target positions
        target_positions: dict[str, Decimal] = {}
        for symbol, weight in target_weights.items():
            target_value = total_value * weight
            price = self.market_data.get_close_price_on_date(symbol, date)
            if price and price > 0:
                target_shares = target_value / Decimal(str(price))
                target_positions[symbol] = target_shares
            else:
                logger.warning(
                    "No price available for symbol",
                    module=MODULE_NAME,
                    symbol=symbol,
                    date=date.isoformat(),
                )

        # Get current positions
        current_positions = {sym: pos.shares for sym, pos in self.positions.items()}

        executed_trades: list[Trade] = []

        # SELLS first (free up cash)
        for symbol in list(current_positions.keys()):
            current_shares = current_positions.get(symbol, Decimal("0"))
            target_shares = target_positions.get(symbol, Decimal("0"))

            if target_shares < current_shares:
                price = self.market_data.get_close_price_on_date(symbol, date)
                if price:
                    trade = self._execute_trade(
                        date, symbol, target_shares, current_shares, Decimal(str(price))
                    )
                    if trade:
                        executed_trades.append(trade)

        # BUYS second (use available cash)
        for symbol, target_shares in target_positions.items():
            current_shares = current_positions.get(symbol, Decimal("0"))

            if target_shares > current_shares:
                price = self.market_data.get_close_price_on_date(symbol, date)
                if price:
                    trade = self._execute_trade(
                        date, symbol, target_shares, current_shares, Decimal(str(price))
                    )
                    if trade:
                        executed_trades.append(trade)

        # Record equity after rebalance
        final_state = self.get_current_state(date)
        self.equity_history.append((date, final_state.total_value))

        logger.info(
            "Rebalance completed",
            module=MODULE_NAME,
            date=date.isoformat(),
            trades_executed=len(executed_trades),
            new_portfolio_value=str(final_state.total_value),
        )

        return executed_trades

    def mark_to_market(self, date: datetime) -> Decimal:
        """Update portfolio value without trading.

        Used for days when no rebalance occurs but we still want
        to track equity curve.

        Args:
            date: Current date

        Returns:
            Updated portfolio value

        """
        self.market_data.set_as_of(date)
        state = self.get_current_state(date)
        self.equity_history.append((date, state.total_value))
        return state.total_value

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame.

        Returns:
            DataFrame with 'portfolio_value' column indexed by date

        """
        if not self.equity_history:
            return pd.DataFrame(columns=["portfolio_value"])

        dates, values = zip(*self.equity_history, strict=True)
        df = pd.DataFrame(
            {"portfolio_value": [float(v) for v in values]},
            index=pd.DatetimeIndex(dates),
        )
        df.index.name = "date"
        return df

    def get_trades(self) -> list[Trade]:
        """Get all executed trades."""
        return self.trades.copy()
