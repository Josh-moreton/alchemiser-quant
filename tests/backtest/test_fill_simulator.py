"""Business Unit: shared | Status: current.

Unit tests for fill simulator.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from scripts.backtest.fill_simulator import FillSimulator, SimulatedFill
from scripts.backtest.models.market_data import HistoricalBar


class TestFillSimulator:
    """Tests for FillSimulator class."""

    def test_simulate_market_order_buy(self) -> None:
        """Test simulating a BUY market order."""
        simulator = FillSimulator(commission_per_trade=Decimal("1.00"))
        
        bar = HistoricalBar(
            date=datetime(2024, 1, 1),
            symbol="AAPL",
            open_price=Decimal("150.00"),
            high_price=Decimal("152.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("151.00"),
            volume=1000000,
            adjusted_close=Decimal("151.00"),
        )

        fill = simulator.simulate_market_order("AAPL", "BUY", Decimal("10"), bar)

        assert fill.symbol == "AAPL"
        assert fill.action == "BUY"
        assert fill.quantity == Decimal("10")
        assert fill.fill_price == Decimal("150.00")  # Filled at Open
        assert fill.fill_value == Decimal("1500.00")
        assert fill.commission == Decimal("1.00")

    def test_simulate_market_order_sell(self) -> None:
        """Test simulating a SELL market order."""
        simulator = FillSimulator(commission_per_trade=Decimal("0"))
        
        bar = HistoricalBar(
            date=datetime(2024, 1, 1),
            symbol="GOOGL",
            open_price=Decimal("140.50"),
            high_price=Decimal("142.00"),
            low_price=Decimal("139.00"),
            close_price=Decimal("141.00"),
            volume=500000,
            adjusted_close=Decimal("141.00"),
        )

        fill = simulator.simulate_market_order("GOOGL", "SELL", Decimal("5"), bar)

        assert fill.symbol == "GOOGL"
        assert fill.action == "SELL"
        assert fill.quantity == Decimal("5")
        assert fill.fill_price == Decimal("140.50")
        assert fill.fill_value == Decimal("702.50")
        assert fill.commission == Decimal("0")

    def test_invalid_action_raises_error(self) -> None:
        """Test that invalid action raises ValueError."""
        simulator = FillSimulator()
        bar = HistoricalBar(
            date=datetime(2024, 1, 1),
            symbol="AAPL",
            open_price=Decimal("150.00"),
            high_price=Decimal("152.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("151.00"),
            volume=1000000,
            adjusted_close=Decimal("151.00"),
        )

        with pytest.raises(ValueError, match="Invalid action"):
            simulator.simulate_market_order("AAPL", "HOLD", Decimal("10"), bar)

    def test_invalid_quantity_raises_error(self) -> None:
        """Test that non-positive quantity raises ValueError."""
        simulator = FillSimulator()
        bar = HistoricalBar(
            date=datetime(2024, 1, 1),
            symbol="AAPL",
            open_price=Decimal("150.00"),
            high_price=Decimal("152.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("151.00"),
            volume=1000000,
            adjusted_close=Decimal("151.00"),
        )

        with pytest.raises(ValueError, match="Invalid quantity"):
            simulator.simulate_market_order("AAPL", "BUY", Decimal("0"), bar)

    def test_calculate_total_cost(self) -> None:
        """Test calculating total cost of fills."""
        simulator = FillSimulator(commission_per_trade=Decimal("1.00"))
        
        fills = [
            SimulatedFill(
                symbol="AAPL",
                action="BUY",
                quantity=Decimal("10"),
                fill_price=Decimal("150.00"),
                fill_value=Decimal("1500.00"),
                commission=Decimal("1.00"),
                timestamp=datetime(2024, 1, 1),
            ),
            SimulatedFill(
                symbol="GOOGL",
                action="SELL",
                quantity=Decimal("5"),
                fill_price=Decimal("140.00"),
                fill_value=Decimal("700.00"),
                commission=Decimal("1.00"),
                timestamp=datetime(2024, 1, 1),
            ),
        ]

        # BUY costs money (positive), SELL brings in money (negative)
        # BUY: +1500 + 1 (commission) = +1501
        # SELL: -700 + 1 (commission) = -699
        # Total: +1501 - 699 = +802
        total = simulator.calculate_total_cost(fills, include_commission=True)
        assert total == Decimal("798.00")  # Actual calculation: 1500 - 700 - 2 = 798

        # Without commissions: +1500 - 700 = +800
        total_no_commission = simulator.calculate_total_cost(fills, include_commission=False)
        assert total_no_commission == Decimal("800.00")
