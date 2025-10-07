"""Business Unit: scripts | Status: current.

Unit tests for fill simulator.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import pytest

# Dynamically add project root to path
project_root = Path(__file__).resolve().parents[2]
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from scripts.backtest.fill_simulator import FillSimulator
from scripts.backtest.models.market_data import DailyBar


@pytest.fixture
def fill_simulator() -> FillSimulator:
    """Create fill simulator with zero commission."""
    return FillSimulator(commission_per_trade=Decimal("0"))


@pytest.fixture
def fill_simulator_with_commission() -> FillSimulator:
    """Create fill simulator with commission."""
    return FillSimulator(commission_per_trade=Decimal("1.00"))


@pytest.fixture
def sample_bar() -> DailyBar:
    """Create a sample daily bar."""
    return DailyBar(
        date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("95.00"),
        close=Decimal("102.00"),
        volume=1000000,
        adjusted_close=Decimal("102.00"),
    )


def test_simulate_buy_fill(fill_simulator: FillSimulator, sample_bar: DailyBar) -> None:
    """Test simulating a BUY order fill."""
    trade = fill_simulator.simulate_fill("TEST", "BUY", Decimal("10"), sample_bar)

    assert trade.symbol == "TEST"
    assert trade.side == "BUY"
    assert trade.quantity == Decimal("10")
    assert trade.price == sample_bar.open
    assert trade.commission == Decimal("0")
    assert trade.total_cost == sample_bar.open * Decimal("10")


def test_simulate_sell_fill(fill_simulator: FillSimulator, sample_bar: DailyBar) -> None:
    """Test simulating a SELL order fill."""
    trade = fill_simulator.simulate_fill("TEST", "SELL", Decimal("5"), sample_bar)

    assert trade.symbol == "TEST"
    assert trade.side == "SELL"
    assert trade.quantity == Decimal("5")
    assert trade.price == sample_bar.open
    assert trade.commission == Decimal("0")
    assert trade.total_cost == sample_bar.open * Decimal("5")


def test_simulate_fill_with_commission(
    fill_simulator_with_commission: FillSimulator, sample_bar: DailyBar
) -> None:
    """Test fill simulation with commission."""
    trade = fill_simulator_with_commission.simulate_fill("TEST", "BUY", Decimal("10"), sample_bar)

    expected_cost = (sample_bar.open * Decimal("10")) + Decimal("1.00")
    assert trade.commission == Decimal("1.00")
    assert trade.total_cost == expected_cost


def test_simulate_fill_invalid_side(fill_simulator: FillSimulator, sample_bar: DailyBar) -> None:
    """Test that invalid order side raises error."""
    with pytest.raises(ValueError, match="Invalid order side"):
        fill_simulator.simulate_fill("TEST", "INVALID", Decimal("10"), sample_bar)


def test_simulate_fill_zero_quantity(fill_simulator: FillSimulator, sample_bar: DailyBar) -> None:
    """Test that zero quantity raises error."""
    with pytest.raises(ValueError, match="Invalid quantity"):
        fill_simulator.simulate_fill("TEST", "BUY", Decimal("0"), sample_bar)


def test_simulate_fill_negative_quantity(
    fill_simulator: FillSimulator, sample_bar: DailyBar
) -> None:
    """Test that negative quantity raises error."""
    with pytest.raises(ValueError, match="Invalid quantity"):
        fill_simulator.simulate_fill("TEST", "BUY", Decimal("-10"), sample_bar)


def test_simulate_multiple_fills(fill_simulator: FillSimulator) -> None:
    """Test simulating multiple fills."""
    bars = {
        "AAPL": DailyBar(
            date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("152.00"),
            volume=2000000,
            adjusted_close=Decimal("152.00"),
        ),
        "MSFT": DailyBar(
            date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            open=Decimal("300.00"),
            high=Decimal("305.00"),
            low=Decimal("298.00"),
            close=Decimal("302.00"),
            volume=1500000,
            adjusted_close=Decimal("302.00"),
        ),
    }

    orders = [
        ("AAPL", "BUY", Decimal("10")),
        ("MSFT", "SELL", Decimal("5")),
    ]

    trades = fill_simulator.simulate_multiple_fills(orders, bars)

    assert len(trades) == 2
    assert trades[0].symbol == "AAPL"
    assert trades[0].side == "BUY"
    assert trades[1].symbol == "MSFT"
    assert trades[1].side == "SELL"


def test_simulate_multiple_fills_missing_data(fill_simulator: FillSimulator) -> None:
    """Test that orders for symbols without data are skipped."""
    bars = {
        "AAPL": DailyBar(
            date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("152.00"),
            volume=2000000,
            adjusted_close=Decimal("152.00"),
        ),
    }

    orders = [
        ("AAPL", "BUY", Decimal("10")),
        ("MISSING", "BUY", Decimal("5")),  # No data for this symbol
    ]

    trades = fill_simulator.simulate_multiple_fills(orders, bars)

    # Only AAPL trade should be executed
    assert len(trades) == 1
    assert trades[0].symbol == "AAPL"


def test_fill_at_open_price(fill_simulator: FillSimulator, sample_bar: DailyBar) -> None:
    """Test that fills occur at Open price as per MVP specification."""
    trade = fill_simulator.simulate_fill("TEST", "BUY", Decimal("10"), sample_bar)

    # MVP: Fill at Open price
    assert trade.price == sample_bar.open
    # Not high, low, or close
    assert trade.price != sample_bar.high
    assert trade.price != sample_bar.low
    assert trade.price != sample_bar.close
