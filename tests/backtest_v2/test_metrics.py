"""Business Unit: backtest | Status: current.

Unit tests for PerformanceMetrics calculation.

Tests metric calculations using known scenarios.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest

from the_alchemiser.backtest_v2.core.metrics import (
    PerformanceMetrics,
    calculate_benchmark_metrics,
    calculate_metrics,
)
from the_alchemiser.backtest_v2.core.result import Trade


class TestPerformanceMetrics:
    """Tests for performance metrics calculation."""

    @pytest.fixture
    def flat_equity_curve(self) -> pd.DataFrame:
        """Create flat equity curve (no change)."""
        dates = pd.date_range("2024-01-01", periods=252, freq="B", tz="UTC")
        return pd.DataFrame(
            {"portfolio_value": [100000.0] * 252},
            index=dates,
        )

    @pytest.fixture
    def linear_growth_curve(self) -> pd.DataFrame:
        """Create linear growth equity curve (10% annual return)."""
        dates = pd.date_range("2024-01-01", periods=252, freq="B", tz="UTC")
        # 10% return over 252 days
        values = [100000.0 * (1 + 0.10 * i / 252) for i in range(252)]
        return pd.DataFrame(
            {"portfolio_value": values},
            index=dates,
        )

    @pytest.fixture
    def drawdown_curve(self) -> pd.DataFrame:
        """Create curve with 20% drawdown."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B", tz="UTC")
        # Start at 100k, drop to 80k, recover to 90k
        values = (
            [100000.0] * 25  # Flat
            + [100000.0 - i * 800 for i in range(25)]  # Drop 20k
            + [80000.0 + i * 400 for i in range(25)]  # Recover 10k
            + [90000.0] * 25  # Flat
        )
        return pd.DataFrame(
            {"portfolio_value": values},
            index=dates,
        )

    def test_empty_curve_returns_empty_metrics(self) -> None:
        """Test that empty equity curve returns empty metrics."""
        empty = pd.DataFrame(columns=["portfolio_value"])
        metrics = calculate_metrics(empty)

        assert metrics.total_return == Decimal("0")
        assert metrics.sharpe_ratio == 0.0

    def test_single_row_returns_empty_metrics(self) -> None:
        """Test that single-row curve returns empty metrics."""
        single = pd.DataFrame(
            {"portfolio_value": [100000.0]},
            index=pd.DatetimeIndex([datetime(2024, 1, 1, tzinfo=UTC)]),
        )
        metrics = calculate_metrics(single)

        assert metrics.total_return == Decimal("0")

    def test_flat_curve_returns_zero_return(self, flat_equity_curve: pd.DataFrame) -> None:
        """Test that flat curve has zero return."""
        metrics = calculate_metrics(flat_equity_curve)

        assert abs(float(metrics.total_return)) < 0.001
        assert abs(float(metrics.cagr)) < 0.001

    def test_linear_growth_calculates_return(self, linear_growth_curve: pd.DataFrame) -> None:
        """Test that linear growth calculates correct return."""
        metrics = calculate_metrics(linear_growth_curve)

        # Should be approximately 10%
        assert 0.09 < float(metrics.total_return) < 0.11

    def test_drawdown_calculation(self, drawdown_curve: pd.DataFrame) -> None:
        """Test max drawdown calculation."""
        metrics = calculate_metrics(drawdown_curve)

        # Max drawdown should be ~20%
        assert 0.15 < float(metrics.max_drawdown) < 0.25

    def test_sharpe_ratio_positive_for_positive_returns(
        self, linear_growth_curve: pd.DataFrame
    ) -> None:
        """Test that positive returns give positive Sharpe."""
        metrics = calculate_metrics(linear_growth_curve)

        assert metrics.sharpe_ratio > 0

    def test_volatility_is_positive(self, linear_growth_curve: pd.DataFrame) -> None:
        """Test that volatility is calculated as positive value."""
        metrics = calculate_metrics(linear_growth_curve)

        assert float(metrics.volatility) >= 0

    def test_trade_count(self, flat_equity_curve: pd.DataFrame) -> None:
        """Test trade count from trade list."""
        trades = [
            Trade(
                date=datetime(2024, 1, 1, tzinfo=UTC),
                symbol="SPY",
                action="BUY",
                shares=Decimal("100"),
                price=Decimal("450"),
                commission=Decimal("0"),
                value=Decimal("45000"),
            ),
            Trade(
                date=datetime(2024, 6, 1, tzinfo=UTC),
                symbol="SPY",
                action="SELL",
                shares=Decimal("100"),
                price=Decimal("460"),
                commission=Decimal("0"),
                value=Decimal("46000"),
            ),
        ]

        metrics = calculate_metrics(flat_equity_curve, trades=trades)

        assert metrics.total_trades == 2

    def test_benchmark_metrics(self) -> None:
        """Test benchmark metrics calculation."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B", tz="UTC")
        benchmark = pd.DataFrame(
            {"close": [100.0 + i * 0.1 for i in range(100)]},
            index=dates,
        )

        metrics = calculate_benchmark_metrics(benchmark)

        assert float(metrics.total_return) > 0

    def test_empty_metrics_factory(self) -> None:
        """Test PerformanceMetrics.empty() factory method."""
        empty = PerformanceMetrics.empty()

        assert empty.total_return == Decimal("0")
        assert empty.sharpe_ratio == 0.0
        assert empty.total_trades == 0


class TestMetricEdgeCases:
    """Edge case tests for metrics calculation."""

    def test_negative_returns(self) -> None:
        """Test metrics with negative returns."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B", tz="UTC")
        values = [100000.0 - i * 100 for i in range(100)]  # Losing 10k
        curve = pd.DataFrame({"portfolio_value": values}, index=dates)

        metrics = calculate_metrics(curve)

        assert float(metrics.total_return) < 0
        assert metrics.sharpe_ratio < 0

    def test_all_winning_days(self) -> None:
        """Test with all positive daily returns."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B", tz="UTC")
        values = [100000.0 * (1.001 ** i) for i in range(100)]
        curve = pd.DataFrame({"portfolio_value": values}, index=dates)

        # Create dummy trades to get win_rate calculation
        from the_alchemiser.backtest_v2.core.result import Trade
        from decimal import Decimal

        trades = [
            Trade(
                date=dates[0],
                symbol="SPY",
                action="BUY",
                shares=Decimal("100"),
                price=Decimal("100"),
                commission=Decimal("0"),
                value=Decimal("10000"),
            )
        ]

        metrics = calculate_metrics(curve, trades=trades)

        # Win rate is based on positive return days, which should be ~1.0
        assert metrics.win_rate > 0.95

    def test_no_drawdown(self) -> None:
        """Test with continuously increasing curve (no drawdown)."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B", tz="UTC")
        values = [100000.0 + i * 100 for i in range(100)]
        curve = pd.DataFrame({"portfolio_value": values}, index=dates)

        metrics = calculate_metrics(curve)

        assert float(metrics.max_drawdown) == 0.0
        assert metrics.max_drawdown_duration_days == 0
