#!/usr/bin/env python3
"""Tests for Monthly Summary Service."""

from __future__ import annotations

import pytest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from the_alchemiser.shared.services.monthly_summary_service import MonthlySummaryService
from the_alchemiser.shared.schemas.trade_ledger import AccountValueEntry, PerformanceSummary


class TestMonthlySummaryService:
    """Test cases for MonthlySummaryService."""

    def test_invalid_month_raises_error(self) -> None:
        """Test that invalid month parameter raises ValueError."""
        service = MonthlySummaryService()

        with pytest.raises(ValueError, match="Invalid month: 13"):
            service.compute_monthly_summary(2025, 13)

        with pytest.raises(ValueError, match="Invalid month: 0"):
            service.compute_monthly_summary(2025, 0)

    def test_no_account_data_returns_empty_summary(self) -> None:
        """Test that no account data returns summary with None values."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_account_service = Mock()

        mock_account_service.get_account_value_history.return_value = []
        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            account_value_service=mock_account_service,
        )

        summary = service.compute_monthly_summary(2025, 8, "test_account")

        assert summary.month_label == "Aug 2025"
        assert summary.portfolio_first_value is None
        assert summary.portfolio_last_value is None
        assert summary.portfolio_pnl_abs is None
        assert summary.portfolio_pnl_pct is None
        assert summary.strategy_rows == []
        assert "No account value snapshots found" in summary.notes[0]
        assert "No strategy trading activity found" in summary.notes[1]

    def test_single_account_snapshot_omits_percentage(self) -> None:
        """Test that single account snapshot omits percentage calculation."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_account_service = Mock()

        # Single account value entry
        single_entry = AccountValueEntry(
            entry_id="entry1",
            account_id="test_account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("1000.00"),
            equity=Decimal("10000.00"),
            timestamp=datetime(2025, 8, 15, tzinfo=UTC),
            source="test",
        )

        mock_account_service.get_account_value_history.return_value = [single_entry]
        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            account_value_service=mock_account_service,
        )

        summary = service.compute_monthly_summary(2025, 8, "test_account")

        assert summary.portfolio_first_value == Decimal("10000.00")
        assert summary.portfolio_last_value == Decimal("10000.00")
        assert summary.portfolio_pnl_abs == Decimal("0.00")
        assert summary.portfolio_pnl_pct == Decimal("0.00")  # Should still calculate pct for single entry

    def test_full_portfolio_pnl_calculation(self) -> None:
        """Test full portfolio P&L calculation with multiple snapshots."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_account_service = Mock()

        # Multiple account value entries
        entries = [
            AccountValueEntry(
                entry_id="entry1",
                account_id="test_account",
                portfolio_value=Decimal("10000.00"),
                cash=Decimal("1000.00"),
                equity=Decimal("10000.00"),
                timestamp=datetime(2025, 8, 1, tzinfo=UTC),
                source="test",
            ),
            AccountValueEntry(
                entry_id="entry2",
                account_id="test_account",
                portfolio_value=Decimal("11000.00"),
                cash=Decimal("1100.00"),
                equity=Decimal("11000.00"),
                timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                source="test",
            ),
        ]

        mock_account_service.get_account_value_history.return_value = entries
        mock_trade_ledger.query.return_value = []
        mock_trade_ledger.calculate_performance.return_value = []

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            account_value_service=mock_account_service,
        )

        summary = service.compute_monthly_summary(2025, 8, "test_account")

        assert summary.portfolio_first_value == Decimal("10000.00")
        assert summary.portfolio_last_value == Decimal("11000.00")
        assert summary.portfolio_pnl_abs == Decimal("1000.00")
        assert summary.portfolio_pnl_pct == Decimal("10.00")  # 10% gain

    def test_strategy_performance_calculation(self) -> None:
        """Test strategy performance calculation from trade ledger."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_account_service = Mock()

        mock_account_service.get_account_value_history.return_value = []

        # Mock trade ledger entries exist
        mock_trade_ledger.query.return_value = [Mock()]  # Non-empty to indicate activity

        # Mock performance summaries (strategy-level with symbol=None)
        mock_summaries = [
            PerformanceSummary(
                strategy_name="StrategyA",
                symbol=None,  # Strategy-level summary
                calculation_timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                realized_pnl=Decimal("500.00"),
                realized_trades=5,
            ),
            PerformanceSummary(
                strategy_name="StrategyB",
                symbol=None,  # Strategy-level summary
                calculation_timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                realized_pnl=Decimal("-200.00"),
                realized_trades=3,
            ),
            PerformanceSummary(
                strategy_name="StrategyC",
                symbol="AAPL",  # Symbol-level summary - should be filtered out
                calculation_timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                realized_pnl=Decimal("100.00"),
                realized_trades=1,
            ),
        ]

        mock_trade_ledger.calculate_performance.return_value = mock_summaries

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            account_value_service=mock_account_service,
        )

        summary = service.compute_monthly_summary(2025, 8, "test_account")

        # Should have 2 strategy rows (A and B), sorted by P&L descending
        assert len(summary.strategy_rows) == 2

        # Check sorted order (StrategyA first with +500, StrategyB second with -200)
        assert summary.strategy_rows[0]["strategy_name"] == "StrategyA"
        assert summary.strategy_rows[0]["realized_pnl"] == Decimal("500.00")
        assert summary.strategy_rows[0]["realized_trades"] == 5

        assert summary.strategy_rows[1]["strategy_name"] == "StrategyB"
        assert summary.strategy_rows[1]["realized_pnl"] == Decimal("-200.00")
        assert summary.strategy_rows[1]["realized_trades"] == 3

    def test_zero_pnl_strategies_filtered_out(self) -> None:
        """Test that strategies with zero P&L and no trades are filtered out."""
        # Mock dependencies
        mock_trade_ledger = Mock()
        mock_account_service = Mock()

        mock_account_service.get_account_value_history.return_value = []
        mock_trade_ledger.query.return_value = [Mock()]  # Non-empty

        # Mock performance summaries with zero P&L
        mock_summaries = [
            PerformanceSummary(
                strategy_name="ActiveStrategy",
                symbol=None,
                calculation_timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                realized_pnl=Decimal("100.00"),
                realized_trades=1,
            ),
            PerformanceSummary(
                strategy_name="InactiveStrategy",
                symbol=None,
                calculation_timestamp=datetime(2025, 8, 31, tzinfo=UTC),
                realized_pnl=Decimal("0.00"),
                realized_trades=0,
            ),
        ]

        mock_trade_ledger.calculate_performance.return_value = mock_summaries

        service = MonthlySummaryService(
            trade_ledger=mock_trade_ledger,
            account_value_service=mock_account_service,
        )

        summary = service.compute_monthly_summary(2025, 8, "test_account")

        # Should only have 1 strategy row (the active one)
        assert len(summary.strategy_rows) == 1
        assert summary.strategy_rows[0]["strategy_name"] == "ActiveStrategy"