#!/usr/bin/env python3
"""Tests for Monthly Summary Email Template.

Note: These tests import modules directly to avoid pre-existing circular
import issues in the shared schemas __init__.py.
"""

from __future__ import annotations

from decimal import Decimal

# Direct imports to avoid circular import in schemas/__init__.py
import the_alchemiser.shared.schemas.reporting as reporting_module
import the_alchemiser.shared.notifications.templates.monthly as monthly_module

MonthlySummaryDTO = reporting_module.MonthlySummaryDTO
MonthlySummaryEmailBuilder = monthly_module.MonthlySummaryEmailBuilder


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

        # Verify portfolio section (no emoji)
        assert "Portfolio P&L" in html
        assert "$10,000.00" in html  # Start value
        assert "$11,000.00" in html  # End value
        assert "+$1,000.00" in html or "$+1,000.00" in html  # Change (flexible format)
        assert "(+10.00%)" in html  # Percentage

        # Verify strategy section (no emoji)
        assert "Realized P&L by Strategy" in html
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
            notes=["No account value snapshots found for this month"],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should contain warning about no data
        assert "No account value snapshots found" in html
        assert "#FEF3C7" in html  # Warning alert box color

    def test_handles_no_strategy_data(self) -> None:
        """Test handling case with no strategy data."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10500.00"),
            portfolio_pnl_abs=Decimal("500.00"),
            portfolio_pnl_pct=Decimal("5.00"),
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should contain info about no trades
        assert "No realized trades found" in html
        assert "#DBEAFE" in html  # Info alert box color

    def test_handles_negative_portfolio_pnl(self) -> None:
        """Test handling negative portfolio P&L."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("9500.00"),
            portfolio_pnl_abs=Decimal("-500.00"),
            portfolio_pnl_pct=Decimal("-5.00"),
            strategy_rows=[],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should show negative values correctly
        assert "$-500.00" in html or "-$500.00" in html
        assert "(-5.00%)" in html or "-5.00%" in html
        assert "#EF4444" in html  # Red color for negative P&L

    def test_handles_mixed_strategy_pnl(self) -> None:
        """Test handling mixed positive and negative strategy P&L."""
        summary = MonthlySummaryDTO(
            month_label="Aug 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10300.00"),
            portfolio_pnl_abs=Decimal("300.00"),
            portfolio_pnl_pct=Decimal("3.00"),
            strategy_rows=[
                {
                    "strategy_name": "WinningStrategy",
                    "realized_pnl": Decimal("800.00"),
                    "realized_trades": 10,
                },
                {
                    "strategy_name": "LosingStrategy",
                    "realized_pnl": Decimal("-500.00"),
                    "realized_trades": 5,
                },
            ],
            notes=[],
        )

        html = MonthlySummaryEmailBuilder.build(summary)

        # Should show both strategies with appropriate colors
        assert "WinningStrategy" in html
        assert "LosingStrategy" in html
        assert "+$800.00" in html
        assert "$-500.00" in html or "-$500.00" in html

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

    def test_respects_mode_parameter(self) -> None:
        """Test that mode parameter is passed through (for future use)."""
        summary = MonthlySummaryDTO(
            month_label="Sep 2025",
            portfolio_first_value=Decimal("10000.00"),
            portfolio_last_value=Decimal("10100.00"),
            portfolio_pnl_abs=Decimal("100.00"),
            portfolio_pnl_pct=Decimal("1.00"),
            strategy_rows=[],
            notes=[],
        )

        html_paper = MonthlySummaryEmailBuilder.build(summary, "PAPER")
        html_live = MonthlySummaryEmailBuilder.build(summary, "LIVE")

        # Both should build successfully
        assert "Monthly Summary — Sep 2025" in html_paper
        assert "Monthly Summary — Sep 2025" in html_live

    def test_handles_zero_portfolio_pnl(self) -> None:
        """Test handling zero portfolio P&L."""
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

        # Should show zero values with plus sign (non-negative)
        assert "+$0.00" in html
        assert "(+0.00%)" in html
        assert "#10B981" in html  # Green color for non-negative
