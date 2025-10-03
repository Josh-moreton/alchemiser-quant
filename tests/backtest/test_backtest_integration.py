"""Business Unit: scripts | Status: current.

Integration tests for backtesting system.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

# Add project root to path
if "/home/runner/work/alchemiser-quant/alchemiser-quant" not in sys.path:
    sys.path.insert(
        0, "/home/runner/work/alchemiser-quant/alchemiser-quant"
    )

from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.models.backtest_result import BacktestConfig
from scripts.backtest.models.market_data import DailyBar
from scripts.backtest.storage.data_store import DataStore


@pytest.fixture
def temp_backtest_runner(tmp_path: Path) -> BacktestRunner:
    """Create a backtest runner with temporary data store."""
    data_store = DataStore(base_path=str(tmp_path / "backtest_data"))
    return BacktestRunner(data_store=data_store)


@pytest.fixture
def sample_test_data(tmp_path: Path) -> DataStore:
    """Create sample test data for backtesting."""
    data_store = DataStore(base_path=str(tmp_path / "backtest_data"))

    # Create 10 days of data for two symbols
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    symbols = ["SPY", "QQQ"]

    for symbol in symbols:
        bars = []
        for i in range(10):
            price = Decimal("100") if symbol == "SPY" else Decimal("200")
            bar = DailyBar(
                date=base_date + timedelta(days=i),
                open=price + Decimal(i),
                high=price + Decimal(i) + Decimal("5"),
                low=price + Decimal(i) - Decimal("5"),
                close=price + Decimal(i) + Decimal("2"),
                volume=1000000 + (i * 10000),
                adjusted_close=price + Decimal(i) + Decimal("2"),
            )
            bars.append(bar)
        data_store.save_bars(symbol, bars)

    return data_store


def test_backtest_initialization(temp_backtest_runner: BacktestRunner) -> None:
    """Test backtest runner initialization."""
    assert temp_backtest_runner.data_store is not None
    assert temp_backtest_runner.fill_simulator is not None


def test_run_simple_backtest(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test running a simple backtest."""
    runner = BacktestRunner(data_store=sample_test_data)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        symbols=["SPY", "QQQ"],
    )

    result = runner.run_backtest(config)

    # Verify basic result structure
    assert result is not None
    assert result.initial_capital == Decimal("100000")
    assert len(result.portfolio_snapshots) > 0
    assert result.final_value is not None


def test_backtest_portfolio_evolution(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test that portfolio state evolves across days."""
    runner = BacktestRunner(data_store=sample_test_data)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        symbols=["SPY"],
    )

    result = runner.run_backtest(config)

    # Verify portfolio snapshots exist for multiple days
    assert len(result.portfolio_snapshots) >= 2

    # Verify first snapshot is initial state
    first_snapshot = result.portfolio_snapshots[0]
    assert first_snapshot.cash == Decimal("100000")
    assert len(first_snapshot.positions) == 0

    # Verify portfolio changes over time
    # After first day, should have positions
    if len(result.portfolio_snapshots) > 1:
        second_snapshot = result.portfolio_snapshots[1]
        # Total value should still be close to initial (minus commission)
        assert second_snapshot.total_value > 0


def test_backtest_trade_generation(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test that trades are generated during backtest."""
    runner = BacktestRunner(data_store=sample_test_data)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("1.00"),
        symbols=["SPY", "QQQ"],
    )

    result = runner.run_backtest(config)

    # Should have generated some trades
    assert len(result.trades) > 0

    # Verify trade structure
    for trade in result.trades:
        assert trade.symbol in ["SPY", "QQQ"]
        assert trade.side in ["BUY", "SELL"]
        assert trade.quantity > 0
        assert trade.price > 0


def test_backtest_metrics_calculation(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test that performance metrics are calculated."""
    runner = BacktestRunner(data_store=sample_test_data)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        symbols=["SPY"],
    )

    result = runner.run_backtest(config)

    # Verify metrics are calculated
    assert result.final_value is not None
    assert result.total_return is not None
    assert result.sharpe_ratio is not None
    assert result.max_drawdown is not None
    assert result.total_trades >= 0


def test_backtest_empty_date_range(temp_backtest_runner: BacktestRunner) -> None:
    """Test backtest with date range that has no data."""
    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2020, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        symbols=["NONEXISTENT"],
    )

    result = temp_backtest_runner.run_backtest(config)

    # Should complete without error
    assert result is not None
    # Should have initial snapshot only
    assert len(result.portfolio_snapshots) == 1
    # Should have no trades
    assert len(result.trades) == 0


def test_backtest_commission_impact(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test that commissions are tracked in trades."""
    # Create runners with different commission rates
    from scripts.backtest.fill_simulator import FillSimulator

    # Run backtest without commission
    runner_no_commission = BacktestRunner(
        data_store=sample_test_data,
        fill_simulator=FillSimulator(commission_per_trade=Decimal("0")),
    )
    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 2, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        symbols=["SPY"],
    )
    result_no_commission = runner_no_commission.run_backtest(config)

    # Verify commission is zero in trades
    if result_no_commission.trades:
        for trade in result_no_commission.trades:
            assert trade.commission == Decimal("0")
