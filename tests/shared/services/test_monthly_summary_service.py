#!/usr/bin/env python3
"""Tests for Monthly Summary Service."""

from __future__ import annotations

import pytest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from the_alchemiser.shared.services.monthly_summary_service import MonthlySummaryService
from the_alchemiser.shared.schemas.trade_ledger import PerformanceSummary


class TestMonthlySummaryService:
    """Test cases for MonthlySummaryService."""

    def test_invalid_month_raises_error(self) -> None:
        """Test that invalid month parameter raises ValueError."""
        service = MonthlySummaryService()

        with pytest.raises(ValueError, match="Invalid month: 13"):
            service.compute_monthly_summary(2025, 13)

        with pytest.raises(ValueError, match="Invalid month: 0"):
            service.compute_monthly_summary(2025, 0)

    def test_no_alpaca_service_returns_empty_portfolio_pnl(self) -> None:
        """Test that no Alpaca service returns summary with None portfolio values."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        
        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            alpaca_account_service=None,  # No Alpaca service
        )

        result = service.compute_monthly_summary(2025, 8)

        assert result.month_label == "Aug 2025"
        assert result.portfolio_first_value is None
        assert result.portfolio_last_value is None
        assert result.portfolio_pnl_abs is None
        assert result.portfolio_pnl_pct is None
        assert result.strategy_rows == []
        assert "No portfolio history found for this month from Alpaca API" in result.notes

    def test_alpaca_portfolio_history_success(self) -> None:
        """Test successful portfolio P&L computation from Alpaca API."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_alpaca_service = Mock()

        # Mock Alpaca portfolio history response
        mock_alpaca_service.get_portfolio_history.return_value = {
            "equity": [10000.0, 10250.0, 10500.0],  # Positive performance
            "timestamp": [1691020800, 1691107200, 1691193600],  # Aug 2023 dates
            "profit_loss": [0.0, 250.0, 500.0],
            "profit_loss_pct": [0.0, 2.5, 5.0],
        }

        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            alpaca_account_service=mock_alpaca_service,
        )

        result = service.compute_monthly_summary(2025, 8)

        # Verify Alpaca API was called with correct parameters
        mock_alpaca_service.get_portfolio_history.assert_called_once_with(
            start_date="2025-08-01",
            end_date="2025-08-31", 
            timeframe="1Day"
        )

        # Verify results
        assert result.month_label == "Aug 2025"
        assert result.portfolio_first_value == Decimal("10000.0")
        assert result.portfolio_last_value == Decimal("10500.0")
        assert result.portfolio_pnl_abs == Decimal("500.0")
        assert result.portfolio_pnl_pct == Decimal("5.0")
        assert result.strategy_rows == []

    def test_alpaca_portfolio_history_empty(self) -> None:
        """Test handling of empty portfolio history from Alpaca API."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_alpaca_service = Mock()

        # Mock empty Alpaca response
        mock_alpaca_service.get_portfolio_history.return_value = {
            "equity": [],
            "timestamp": [],
        }

        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            alpaca_account_service=mock_alpaca_service,
        )

        result = service.compute_monthly_summary(2025, 8)

        assert result.portfolio_first_value is None
        assert result.portfolio_last_value is None
        assert result.portfolio_pnl_abs is None
        assert result.portfolio_pnl_pct is None
        assert "No portfolio history found for this month from Alpaca API" in result.notes

    def test_strategy_performance_calculation(self) -> None:
        """Test strategy performance calculation from trade ledger."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_alpaca_service = Mock()

        # Mock Alpaca response
        mock_alpaca_service.get_portfolio_history.return_value = {
            "equity": [10000.0, 10100.0],
            "timestamp": [1691020800, 1691193600],
        }

        # Mock strategy performance
        mock_trade_ledger.calculate_performance.return_value = [
            PerformanceSummary(
                strategy_name="TestStrategy",
                realized_pnl=Decimal("150.50"),
                realized_trades=5,
            )
        ]

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            alpaca_account_service=mock_alpaca_service,
        )

        result = service.compute_monthly_summary(2025, 8)

        # Verify strategy data
        assert len(result.strategy_rows) == 1
        assert result.strategy_rows[0]["strategy_name"] == "TestStrategy"
        assert result.strategy_rows[0]["realized_pnl"] == Decimal("150.50")
        assert result.strategy_rows[0]["realized_trades"] == 5

    def test_alpaca_service_failure_handling(self) -> None:
        """Test handling of Alpaca service failures."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_alpaca_service = Mock()

        # Mock Alpaca service failure
        mock_alpaca_service.get_portfolio_history.side_effect = Exception("API Error")

        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            alpaca_account_service=mock_alpaca_service,
        )

        result = service.compute_monthly_summary(2025, 8)

        # Should handle the error gracefully
        assert result.portfolio_first_value is None
        assert result.portfolio_last_value is None
        assert result.portfolio_pnl_abs is None
        assert result.portfolio_pnl_pct is None
        assert "No portfolio history found for this month from Alpaca API" in result.notes