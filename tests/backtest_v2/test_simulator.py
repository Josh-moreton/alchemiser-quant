"""Business Unit: backtest | Status: current.

Unit tests for PortfolioSimulator.

Tests portfolio tracking, rebalancing, and trade execution.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from the_alchemiser.backtest_v2.adapters.historical_market_data import (
    BacktestMarketDataAdapter,
)
from the_alchemiser.backtest_v2.core.result import Trade
from the_alchemiser.backtest_v2.core.simulator import (
    PortfolioSimulator,
    PortfolioState,
    Position,
)


class TestPosition:
    """Tests for Position dataclass."""

    def test_market_value(self) -> None:
        """Test market value calculation."""
        pos = Position(
            symbol="SPY",
            shares=Decimal("100"),
            cost_basis=Decimal("450"),
            current_price=Decimal("460"),
        )

        assert pos.market_value == Decimal("46000")

    def test_unrealized_pnl(self) -> None:
        """Test unrealized P&L calculation."""
        pos = Position(
            symbol="SPY",
            shares=Decimal("100"),
            cost_basis=Decimal("450"),
            current_price=Decimal("460"),
        )

        assert pos.unrealized_pnl == Decimal("1000")

    def test_unrealized_pnl_pct(self) -> None:
        """Test unrealized P&L percentage."""
        pos = Position(
            symbol="SPY",
            shares=Decimal("100"),
            cost_basis=Decimal("450"),
            current_price=Decimal("495"),
        )

        # 10% gain
        expected = Decimal("0.1")
        assert pos.unrealized_pnl_pct == expected


class TestPortfolioState:
    """Tests for PortfolioState dataclass."""

    def test_total_value_cash_only(self) -> None:
        """Test total value with cash only."""
        state = PortfolioState(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            cash=Decimal("100000"),
            positions={},
        )

        assert state.total_value == Decimal("100000")

    def test_total_value_with_positions(self) -> None:
        """Test total value with cash and positions."""
        state = PortfolioState(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            cash=Decimal("50000"),
            positions={
                "SPY": Position(
                    symbol="SPY",
                    shares=Decimal("100"),
                    cost_basis=Decimal("450"),
                    current_price=Decimal("500"),
                ),
            },
        )

        # 50000 cash + 100 * 500 = 100000
        assert state.total_value == Decimal("100000")

    def test_position_weights(self) -> None:
        """Test position weight calculation."""
        state = PortfolioState(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            cash=Decimal("50000"),
            positions={
                "SPY": Position(
                    symbol="SPY",
                    shares=Decimal("100"),
                    cost_basis=Decimal("450"),
                    current_price=Decimal("500"),
                ),
            },
        )

        weights = state.position_weights
        assert weights["SPY"] == Decimal("0.5")
        assert weights["CASH"] == Decimal("0.5")


class TestPortfolioSimulator:
    """Tests for PortfolioSimulator."""

    @pytest.fixture
    def mock_market_data(self) -> MagicMock:
        """Create mock market data adapter."""
        mock = MagicMock(spec=BacktestMarketDataAdapter)
        mock.get_close_price_on_date.return_value = 100.0
        return mock

    @pytest.fixture
    def simulator(self, mock_market_data: MagicMock) -> PortfolioSimulator:
        """Create simulator with mock market data."""
        sim = PortfolioSimulator(
            market_data=mock_market_data,
            slippage_bps=Decimal("5"),
            commission_per_share=Decimal("0"),
        )
        sim.initialize(Decimal("100000"))
        return sim

    def test_initialize(self, simulator: PortfolioSimulator) -> None:
        """Test simulator initialization."""
        assert simulator.cash == Decimal("100000")
        assert len(simulator.positions) == 0
        assert len(simulator.trades) == 0

    def test_slippage_buy(self, simulator: PortfolioSimulator) -> None:
        """Test slippage increases buy price."""
        price = Decimal("100")
        slipped = simulator._calculate_slippage(price, is_buy=True)

        # 5 bps = 0.05% = 0.0005
        assert slipped > price
        assert slipped == Decimal("100.05")

    def test_slippage_sell(self, simulator: PortfolioSimulator) -> None:
        """Test slippage decreases sell price."""
        price = Decimal("100")
        slipped = simulator._calculate_slippage(price, is_buy=False)

        assert slipped < price
        assert slipped == Decimal("99.95")

    def test_rebalance_creates_trades(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test that rebalancing creates trades."""
        date = datetime(2024, 1, 1, tzinfo=UTC)
        target_weights = {"SPY": Decimal("0.5"), "QQQ": Decimal("0.5")}

        trades = simulator.rebalance(date, target_weights)

        assert len(trades) == 2
        assert all(t.action == "BUY" for t in trades)

    def test_rebalance_updates_positions(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test that rebalancing updates positions."""
        date = datetime(2024, 1, 1, tzinfo=UTC)
        target_weights = {"SPY": Decimal("1.0")}

        simulator.rebalance(date, target_weights)

        assert "SPY" in simulator.positions

    def test_rebalance_updates_cash(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test that rebalancing reduces cash."""
        initial_cash = simulator.cash
        date = datetime(2024, 1, 1, tzinfo=UTC)
        target_weights = {"SPY": Decimal("1.0")}

        simulator.rebalance(date, target_weights)

        assert simulator.cash < initial_cash

    def test_rebalance_sells_then_buys(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test that rebalancing sells before buying."""
        date = datetime(2024, 1, 1, tzinfo=UTC)

        # Initial position
        simulator.rebalance(date, {"SPY": Decimal("1.0")})

        # Rebalance to different allocation
        date2 = datetime(2024, 1, 2, tzinfo=UTC)
        trades = simulator.rebalance(date2, {"QQQ": Decimal("1.0")})

        # Should have sell SPY, buy QQQ
        actions = [t.action for t in trades]
        sell_idx = next(i for i, a in enumerate(actions) if a == "SELL")
        buy_idx = next(i for i, a in enumerate(actions) if a == "BUY")
        assert sell_idx < buy_idx  # Sell comes first

    def test_mark_to_market(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test mark to market updates equity history."""
        date = datetime(2024, 1, 1, tzinfo=UTC)

        value = simulator.mark_to_market(date)

        assert value == Decimal("100000")
        assert len(simulator.equity_history) == 1

    def test_get_equity_curve(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test equity curve DataFrame generation."""
        simulator.mark_to_market(datetime(2024, 1, 1, tzinfo=UTC))
        simulator.mark_to_market(datetime(2024, 1, 2, tzinfo=UTC))

        curve = simulator.get_equity_curve()

        assert len(curve) == 2
        assert "portfolio_value" in curve.columns

    def test_position_closed_when_target_zero(
        self, simulator: PortfolioSimulator, mock_market_data: MagicMock
    ) -> None:
        """Test that position is removed when target weight is zero."""
        date = datetime(2024, 1, 1, tzinfo=UTC)

        # Create position
        simulator.rebalance(date, {"SPY": Decimal("1.0")})
        assert "SPY" in simulator.positions

        # Close position
        date2 = datetime(2024, 1, 2, tzinfo=UTC)
        simulator.rebalance(date2, {"QQQ": Decimal("1.0")})
        assert "SPY" not in simulator.positions


class TestTradeRecord:
    """Tests for Trade record."""

    def test_net_value_buy(self) -> None:
        """Test net value for buy trade."""
        trade = Trade(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            symbol="SPY",
            action="BUY",
            shares=Decimal("100"),
            price=Decimal("450"),
            commission=Decimal("1"),
            value=Decimal("45000"),
        )

        assert trade.net_value == Decimal("45001")

    def test_net_value_sell(self) -> None:
        """Test net value for sell trade."""
        trade = Trade(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            symbol="SPY",
            action="SELL",
            shares=Decimal("100"),
            price=Decimal("460"),
            commission=Decimal("1"),
            value=Decimal("46000"),
        )

        assert trade.net_value == Decimal("45999")
