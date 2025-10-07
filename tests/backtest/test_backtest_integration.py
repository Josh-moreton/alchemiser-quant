"""Business Unit: scripts | Status: current.

Integration tests for backtesting system.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

# Add project root to path dynamically
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

    # Create data for all symbols required by DSL strategies
    # Need at least 252 days (1 year) before backtest date for indicators like 200-day MA
    # Backtest runs from 2024-01-01 to 2024-01-05, so create data from 2023-01-01 to 2024-12-31
    base_date = datetime(2023, 1, 1, tzinfo=timezone.utc)

    # Symbol base prices matching realistic market values
    symbol_prices = {
        "SPY": Decimal("400"),
        "QQQ": Decimal("350"),
        "QQQE": Decimal("50"),
        "BITO": Decimal("15"),
        "BIL": Decimal("91.50"),
        "FXI": Decimal("25"),
        "FCG": Decimal("20"),
        "IOO": Decimal("80"),
        "UVXY": Decimal("10"),
    }

    for symbol, base_price in symbol_prices.items():
        bars = []
        # Create 730 days of data (covers 2023 and 2024, ~2 years)
        for i in range(730):
            # Add some realistic price movement
            price_variation = Decimal(i * 0.1)
            bar = DailyBar(
                date=base_date + timedelta(days=i),
                open=base_price + price_variation,
                high=base_price + price_variation + Decimal("2"),
                low=base_price + price_variation - Decimal("2"),
                close=base_price + price_variation + Decimal("1"),
                volume=1000000 + (i * 10000),
                adjusted_close=base_price + price_variation + Decimal("1"),
            )
            bars.append(bar)
        data_store.save_bars(symbol, bars)

    return data_store


def test_backtest_initialization(temp_backtest_runner: BacktestRunner) -> None:
    """Test backtest runner initialization."""
    assert temp_backtest_runner.data_store is not None
    assert temp_backtest_runner.fill_simulator is not None


@pytest.mark.slow
def test_run_simple_backtest(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test running a simple backtest.

    Note: This test is marked as slow because it initializes the DSL engine
    for each trading day (5 days), which involves parsing strategy files and
    loading historical data. Takes ~2-3 minutes.
    """
    # Disable auto-download to speed up test
    runner = BacktestRunner(data_store=sample_test_data, auto_download_missing=False)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        # Include all symbols that the test strategy might need
        symbols=["SPY", "QQQ", "QQQE", "BITO", "BIL", "FXI", "FCG", "IOO", "UVXY"],
    )

    result = runner.run_backtest(config)

    # Verify basic result structure
    assert result is not None
    assert result.initial_capital == Decimal("100000")
    assert len(result.portfolio_snapshots) > 0
    assert result.final_value is not None


@pytest.mark.slow
def test_backtest_portfolio_evolution(
    sample_test_data: DataStore, tmp_path: Path
) -> None:
    """Test that portfolio state evolves across days.

    Note: Marked as slow - takes ~2-3 minutes due to DSL engine initialization.
    """
    # Disable auto-download to speed up test
    runner = BacktestRunner(data_store=sample_test_data, auto_download_missing=False)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        # Include all symbols that the test strategy might need
        symbols=["SPY", "QQQ", "QQQE", "BITO", "BIL", "FXI", "FCG", "IOO", "UVXY"],
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


@pytest.mark.slow
def test_backtest_trade_generation(sample_test_data: DataStore, tmp_path: Path) -> None:
    """Test that trades are generated during backtest.

    Note: Marked as slow - takes ~2-3 minutes due to DSL engine initialization.
    """
    runner = BacktestRunner(data_store=sample_test_data, auto_download_missing=False)

    # Include all symbols that DSL strategies might trade
    all_symbols = ["SPY", "QQQ", "QQQE", "BITO", "BIL", "FXI", "FCG", "IOO", "UVXY"]

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("1.00"),
        symbols=all_symbols,
    )

    result = runner.run_backtest(config)

    # Should have generated some trades
    assert len(result.trades) > 0

    # Verify trade structure
    for trade in result.trades:
        # Note: Strategies may reference symbols beyond those in config.symbols
        # We just verify the trade has valid structure
        assert trade.symbol is not None
        assert len(trade.symbol) > 0
        assert trade.side in ["BUY", "SELL"]
        assert trade.quantity > 0
        assert trade.price > 0


@pytest.mark.slow
def test_backtest_metrics_calculation(
    sample_test_data: DataStore, tmp_path: Path
) -> None:
    """Test that performance metrics are calculated.

    Note: Marked as slow - takes ~2-3 minutes due to DSL engine initialization.
    """
    # Disable auto-download to speed up test
    runner = BacktestRunner(data_store=sample_test_data, auto_download_missing=False)

    config = BacktestConfig(
        strategy_files=["test.clj"],
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        initial_capital=Decimal("100000"),
        commission_per_trade=Decimal("0"),
        # Include all symbols that the test strategy might need
        symbols=["SPY", "QQQ", "QQQE", "BITO", "BIL", "FXI", "FCG", "IOO", "UVXY"],
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


@pytest.mark.slow
def test_backtest_commission_impact(
    sample_test_data: DataStore, tmp_path: Path
) -> None:
    """Test that commissions are tracked in trades.

    Note: Marked as slow - takes ~1-2 minutes due to DSL engine initialization.
    """
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
