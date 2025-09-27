#!/usr/bin/env python3
"""Tests for Monthly Summary Email Template."""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.notifications.templates.monthly import MonthlySummaryEmailBuilder
from the_alchemiser.shared.schemas.reporting import MonthlySummary


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
        assert "<!DOCTYPE html>" in html
        assert "The Alchemiser — Monthly Summary (Aug 2025)" in html

        # Verify portfolio section
        assert "💰 Portfolio P&L" in html
        assert "$10,000.00" in html  # Start value
        assert "$11,000.00" in html  # End value
        assert "$+1,000.00" in html  # Change
        assert "(+10.00%)" in html   # Percentage

        # Verify strategy section
        assert "📊 Realized P&L by Strategy" in html
        assert "StrategyA" in html
        assert "StrategyB" in html
        assert "+$500.00" in html  # Positive P&L
        assert "$-200.00" in html   # Negative P&L

    def test_handles_no_portfolio_data(self) -> None:
        """Test handling case with no portfolio data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=None,
            portfolio_last_value=None,
            portfolio_pnl_abs=None,
            portfolio_pnl_pct=None,
            strategy_rows=[],
            notes=["No account value snapshots found for this month"],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should contain warning about no data
        assert "No account value snapshots found" in html
        assert "#FEF3C7" in html  # Warning alert box color

    def test_handles_single_portfolio_snapshot(self) -> None:
        """Test handling case with single portfolio snapshot."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=None,  # Only one snapshot
            portfolio_pnl_abs=None,
            portfolio_pnl_pct=None,
            strategy_rows=[],
            notes=["Only one account value snapshot found"],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should show the single value and info alert
        assert "$10,000.00" in html
        assert "Only one account value snapshot found" in html
        assert "#DBEAFE" in html  # Info alert box color

    def test_handles_no_strategy_data(self) -> None:
        """Test handling case with no strategy data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10000.00"),
            portfolio_pnl_abs=Decimal("0.00"),
            portfolio_pnl_pct=Decimal("0.00"),
            strategy_rows=[],
            notes=["No strategy trading activity found for this month"],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should contain message about no strategy activity
        assert "No strategy trading activity found" in html
        assert "📊 Realized P&L by Strategy" in html

    def test_formats_positive_negative_zero_pnl(self) -> None:
        """Test proper formatting and coloring of different P&L values."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("9500.00"),
            portfolio_pnl_abs=Decimal("-500.00"),
            portfolio_pnl_pct=Decimal("-5.00"),
            strategy_rows=[
                {
                    "strategy_name": "WinnerStrategy",
                    "realized_pnl": Decimal("300.00"),
                    "realized_trades": 2,
                },
                {
                    "strategy_name": "LoserStrategy",
                    "realized_pnl": Decimal("-100.00"),
                    "realized_trades": 1,
                },
                {
                    "strategy_name": "BreakevenStrategy",
                    "realized_pnl": Decimal("0.00"),
                    "realized_trades": 1,
                },
            ],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Portfolio should show negative with appropriate icon
        assert "📉" in html  # Negative trend icon
        assert "$-500.00" in html
        assert "(-5.00%)" in html

        # Strategy P&L should be color-coded
        assert 'color: #10B981' in html  # Green for positive
        assert 'color: #EF4444' in html  # Red for negative
        assert 'color: #6B7280' in html  # Gray for zero

    def test_includes_methodology_footer(self) -> None:
        """Test that methodology footer is included."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10000.00"),
            portfolio_pnl_abs=Decimal("0.00"),
            portfolio_pnl_pct=Decimal("0.00"),
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should include methodology explanation
        assert "Aug 2025 Summary Methodology" in html
        assert "Portfolio P&L calculated from account value snapshots" in html
        assert "Per-strategy percentages omitted" in html
        assert "UTC-based month windows" in html