"""Tests for report metrics calculation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.reporting.metrics import (
    compute_cagr,
    compute_calmar_ratio,
    compute_max_drawdown,
    compute_metrics_from_snapshot,
    compute_sharpe_ratio,
)


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_sharpe_ratio_positive_returns(self) -> None:
        """Test Sharpe ratio with positive returns."""
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("0.015"), Decimal("0.01")]
        sharpe = compute_sharpe_ratio(returns)
        assert isinstance(sharpe, Decimal)
        assert sharpe > 0

    def test_sharpe_ratio_empty_returns(self) -> None:
        """Test Sharpe ratio with empty returns."""
        returns: list[Decimal] = []
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe == Decimal("0.0")

    def test_sharpe_ratio_single_return(self) -> None:
        """Test Sharpe ratio with single return."""
        returns = [Decimal("0.01")]
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe == Decimal("0.0")

    def test_sharpe_ratio_zero_volatility(self) -> None:
        """Test Sharpe ratio with zero volatility."""
        returns = [Decimal("0.01"), Decimal("0.01"), Decimal("0.01")]
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe == Decimal("0.0")


class TestMaxDrawdown:
    """Test maximum drawdown calculation."""

    def test_max_drawdown_declining_equity(self) -> None:
        """Test max drawdown with declining equity."""
        equity_curve = [
            Decimal("100000"),
            Decimal("95000"),
            Decimal("90000"),
            Decimal("85000"),
        ]
        max_dd = compute_max_drawdown(equity_curve)
        assert isinstance(max_dd, Decimal)
        assert max_dd < 0  # Drawdown should be negative

    def test_max_drawdown_increasing_equity(self) -> None:
        """Test max drawdown with increasing equity."""
        equity_curve = [
            Decimal("100000"),
            Decimal("105000"),
            Decimal("110000"),
            Decimal("115000"),
        ]
        max_dd = compute_max_drawdown(equity_curve)
        assert max_dd == Decimal("0.0")

    def test_max_drawdown_empty_curve(self) -> None:
        """Test max drawdown with empty equity curve."""
        equity_curve: list[Decimal] = []
        max_dd = compute_max_drawdown(equity_curve)
        assert max_dd == Decimal("0.0")

    def test_max_drawdown_single_point(self) -> None:
        """Test max drawdown with single equity point."""
        equity_curve = [Decimal("100000")]
        max_dd = compute_max_drawdown(equity_curve)
        assert max_dd == Decimal("0.0")


class TestCAGR:
    """Test CAGR calculation."""

    def test_cagr_positive_growth(self) -> None:
        """Test CAGR with positive growth."""
        start_equity = Decimal("100000")
        end_equity = Decimal("120000")
        days = 365
        cagr = compute_cagr(start_equity, end_equity, days)
        assert isinstance(cagr, Decimal)
        assert cagr > 0

    def test_cagr_zero_days(self) -> None:
        """Test CAGR with zero days."""
        start_equity = Decimal("100000")
        end_equity = Decimal("120000")
        days = 0
        cagr = compute_cagr(start_equity, end_equity, days)
        assert cagr == Decimal("0.0")

    def test_cagr_zero_start_equity(self) -> None:
        """Test CAGR with zero start equity."""
        start_equity = Decimal("0")
        end_equity = Decimal("120000")
        days = 365
        cagr = compute_cagr(start_equity, end_equity, days)
        assert cagr == Decimal("0.0")

    def test_cagr_negative_growth(self) -> None:
        """Test CAGR with negative growth."""
        start_equity = Decimal("100000")
        end_equity = Decimal("80000")
        days = 365
        cagr = compute_cagr(start_equity, end_equity, days)
        assert cagr < 0


class TestCalmarRatio:
    """Test Calmar ratio calculation."""

    def test_calmar_ratio_positive_cagr(self) -> None:
        """Test Calmar ratio with positive CAGR."""
        cagr = Decimal("20.0")
        max_drawdown = Decimal("-10.0")
        calmar = compute_calmar_ratio(cagr, max_drawdown)
        assert isinstance(calmar, Decimal)
        assert calmar > 0

    def test_calmar_ratio_zero_drawdown(self) -> None:
        """Test Calmar ratio with zero drawdown."""
        cagr = Decimal("20.0")
        max_drawdown = Decimal("0.0")
        calmar = compute_calmar_ratio(cagr, max_drawdown)
        assert calmar == Decimal("0.0")

    def test_calmar_ratio_positive_drawdown(self) -> None:
        """Test Calmar ratio with positive drawdown (invalid)."""
        cagr = Decimal("20.0")
        max_drawdown = Decimal("10.0")
        calmar = compute_calmar_ratio(cagr, max_drawdown)
        assert calmar == Decimal("0.0")


class TestComputeMetricsFromSnapshot:
    """Test metrics computation from snapshot."""

    def test_compute_metrics_basic_snapshot(self) -> None:
        """Test metrics computation with basic snapshot."""
        snapshot_data = {
            "alpaca_account": {
                "equity": "100000.00",
                "portfolio_value": "100000.00",
            }
        }

        metrics = compute_metrics_from_snapshot(snapshot_data)

        assert "sharpe_ratio" in metrics
        assert "calmar_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "cagr" in metrics
        assert "current_equity" in metrics
        assert "portfolio_value" in metrics

        assert metrics["current_equity"] == Decimal("100000.00")
        assert metrics["portfolio_value"] == Decimal("100000.00")

    def test_compute_metrics_empty_snapshot(self) -> None:
        """Test metrics computation with empty snapshot."""
        snapshot_data: dict[str, dict[str, str]] = {"alpaca_account": {}}

        metrics = compute_metrics_from_snapshot(snapshot_data)

        assert metrics["current_equity"] == Decimal("0")
        assert metrics["portfolio_value"] == Decimal("0")
