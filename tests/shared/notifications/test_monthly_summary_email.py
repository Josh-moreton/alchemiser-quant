#!/usr/bin/env python3
"""Tests for Monthly Summary Email Template."""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.notifications.templates.monthly import MonthlySummaryEmailBuilder
from the_alchemiser.shared.schemas.reporting import MonthlySummaryDTO


class TestMonthlySummaryEmail:
    """Test cases for MonthlySummaryEmailBuilder."""

    def test_builds_complete_email_with_data(self) -> None:
        """Test building complete email with portfolio and strategy data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("11000.00"),
            portfolio_pnl_abs=Decimal("1000.00"),
            portfolio_pnl_pct=Decimal("10.00"),
            strategy_rows=[
                {
                    "strategy_name": "StrategyA",
                    "realized_pnl": Decimal("500.00"),
                    "realized_trades": 5,
                },
                {
                    "strategy_name": "StrategyB",
                    "realized_pnl": Decimal("-200.00"),
                    "realized_trades": 3,
                },
            ],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary, "PAPER")

        # Verify basic structure
        assert "Monthly Summary — Aug 2025" in html
        assert "Portfolio Summary" in html
        assert "Strategy Performance" in html
        assert "$10,000.00" in html  # First value
        assert "$11,000.00" in html  # Last value
        assert "+$1,000.00" in html  # Positive P&L
        assert "(+10.00%)" in html  # Percentage

        # Verify strategy details
        assert "StrategyA" in html
        assert "StrategyB" in html
        assert "+$500.00" in html  # Positive P&L
        assert "$-200.00" in html  # Negative P&L

    def test_handles_no_portfolio_data(self) -> None:
        """Test handling case with no portfolio data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=None,
            portfolio_last_value=None,
            portfolio_pnl_abs=None,
            portfolio_pnl_pct=None,
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary, "PAPER")

        assert "Portfolio Data Unavailable" in html
        assert "insufficient account snapshots" in html

    def test_handles_single_portfolio_snapshot(self) -> None:
        """Test handling case with single portfolio snapshot."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=None,
            portfolio_pnl_abs=None,
            portfolio_pnl_pct=None,
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary, "PAPER")

        assert "Portfolio Data Unavailable" in html

    def test_handles_no_strategy_data(self) -> None:
        """Test handling case with no strategy data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("11000.00"),
            portfolio_pnl_abs=Decimal("1000.00"),
            portfolio_pnl_pct=Decimal("10.00"),
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary, "PAPER")

        assert "No Strategy Activity" in html
        assert "No closed trades" in html

    def test_formats_positive_negative_zero_pnl(self) -> None:
        """Test proper formatting and coloring of different P&L values."""
        summary_positive = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("11000.00"),
            portfolio_pnl_abs=Decimal("1000.00"),
            portfolio_pnl_pct=Decimal("10.00"),
            strategy_rows=[],
            notes=[],
        )

        html_pos = MonthlySummaryEmailBuilder.build(summary_positive, "PAPER")
        assert "+$1,000.00" in html_pos
        assert "#10B981" in html_pos  # Green color

        summary_negative = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("9000.00"),
            portfolio_pnl_abs=Decimal("-1000.00"),
            portfolio_pnl_pct=Decimal("-10.00"),
            strategy_rows=[],
            notes=[],
        )

        html_neg = MonthlySummaryEmailBuilder.build(summary_negative, "PAPER")
        assert "$-1,000.00" in html_neg
        assert "#EF4444" in html_neg  # Red color

        summary_zero = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10000.00"),
            portfolio_pnl_abs=Decimal("0.00"),
            portfolio_pnl_pct=Decimal("0.00"),
            strategy_rows=[],
            notes=[],
        )

        html_zero = MonthlySummaryEmailBuilder.build(summary_zero, "PAPER")
        assert "$0.00" in html_zero
        assert "#6B7280" in html_zero  # Gray color

    def test_includes_methodology_footer(self) -> None:
        """Test that methodology footer is included."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("11000.00"),
            portfolio_pnl_abs=Decimal("1000.00"),
            portfolio_pnl_pct=Decimal("10.00"),
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary, "PAPER")

        assert "Summary Methodology" in html
        assert "account value snapshots" in html
        assert "Decimal precision" in html
        assert "UTC-based month windows" in html
