#!/usr/bin/env python3
"""
Test suite for monthly summary functionality.

This module tests the monthly summary service and email template generation.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.application.reporting.monthly_summary_service import MonthlySummaryService
from the_alchemiser.interface.email.templates.monthly_summary import MonthlySummaryBuilder


class TestMonthlySummaryService:
    """Test cases for MonthlySummaryService."""

    def test_init(self):
        """Test service initialization."""
        service = MonthlySummaryService("test_key", "test_secret", paper=True)
        assert service.paper_trading is True
        assert service.alpaca_manager is not None

    @patch("the_alchemiser.application.reporting.monthly_summary_service.AlpacaManager")
    @patch("the_alchemiser.application.reporting.monthly_summary_service.get_strategy_tracker")
    def test_generate_monthly_summary_success(self, mock_tracker, mock_alpaca):
        """Test successful monthly summary generation."""
        # Mock AlpacaManager methods
        mock_alpaca_instance = Mock()
        mock_alpaca.return_value = mock_alpaca_instance

        # Mock account data
        mock_alpaca_instance.get_account.return_value = {
            "portfolio_value": 100000.0,
            "equity": 100000.0,
            "cash": 10000.0,
            "buying_power": 40000.0,
            "day_trades_remaining": 3,
            "status": "ACTIVE",
        }

        # Mock portfolio history
        mock_alpaca_instance.get_portfolio_history.return_value = {
            "equity": [95000.0, 98000.0, 100000.0],
            "profit_loss": [0.0, 3000.0, 5000.0],
            "timestamp": ["2024-01-01", "2024-01-15", "2024-01-31"],
        }

        # Mock trading activities
        mock_alpaca_instance.get_activities.return_value = [
            {
                "symbol": "AAPL",
                "side": "BUY",
                "qty": 10.0,
                "price": 150.0,
                "date": "2024-01-15",
            },
            {
                "symbol": "AAPL",
                "side": "SELL",
                "qty": 5.0,
                "price": 160.0,
                "date": "2024-01-25",
            },
        ]

        # Mock positions
        mock_alpaca_instance.get_positions.return_value = []
        mock_alpaca_instance.get_positions_dict.return_value = {}
        mock_alpaca_instance.get_current_prices.return_value = {}

        # Mock strategy tracker
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.get_all_strategy_pnl.return_value = {}

        # Create service and generate summary
        service = MonthlySummaryService("test_key", "test_secret", paper=True)
        target_month = datetime(2024, 1, 1)

        summary = service.generate_monthly_summary(target_month)

        # Verify summary structure
        assert "month" in summary
        assert "account_summary" in summary
        assert "portfolio_performance" in summary
        assert "trading_activity" in summary
        assert "strategy_performance" in summary
        assert "fees_and_costs" in summary
        assert "positions_summary" in summary
        assert "generated_at" in summary

        # Verify specific data
        assert summary["month"] == "January 2024"
        assert summary["account_summary"]["portfolio_value"] == 100000.0
        assert summary["trading_activity"]["total_trades"] == 2
        assert summary["trading_activity"]["buy_trades"] == 1
        assert summary["trading_activity"]["sell_trades"] == 1

    def test_generate_monthly_summary_default_month(self):
        """Test monthly summary with default month (previous month)."""
        with patch(
            "the_alchemiser.application.reporting.monthly_summary_service.AlpacaManager"
        ) as mock_alpaca:
            mock_alpaca_instance = Mock()
            mock_alpaca.return_value = mock_alpaca_instance

            # Mock minimal data to avoid errors
            mock_alpaca_instance.get_account.return_value = {}
            mock_alpaca_instance.get_portfolio_history.return_value = None
            mock_alpaca_instance.get_activities.return_value = []
            mock_alpaca_instance.get_positions.return_value = []

            with patch(
                "the_alchemiser.application.reporting.monthly_summary_service.get_strategy_tracker"
            ) as mock_tracker:
                mock_tracker_instance = Mock()
                mock_tracker.return_value = mock_tracker_instance
                mock_tracker_instance.get_all_strategy_pnl.return_value = {}

                service = MonthlySummaryService("test_key", "test_secret", paper=True)
                summary = service.generate_monthly_summary()

                # Should generate for previous month
                assert "month" in summary
                assert summary["month"] is not None


class TestMonthlySummaryBuilder:
    """Test cases for MonthlySummaryBuilder."""

    def test_build_monthly_summary_email_basic(self):
        """Test basic monthly summary email generation."""
        # Sample summary data
        summary_data = {
            "month": "January 2024",
            "account_summary": {
                "portfolio_value": 100000.0,
                "equity": 100000.0,
                "cash": 10000.0,
            },
            "portfolio_performance": {
                "start_value": 95000.0,
                "end_value": 100000.0,
                "total_return": 5000.0,
                "total_return_pct": 5.26,
                "max_drawdown_pct": 2.1,
                "trading_days": 21,
            },
            "trading_activity": {
                "total_trades": 10,
                "buy_trades": 6,
                "sell_trades": 4,
                "total_buy_volume": 50000.0,
                "total_sell_volume": 30000.0,
                "symbol_count": 5,
                "symbols_traded": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            },
            "strategy_performance": {
                "strategies": {
                    "nuclear": {
                        "realized_pnl": 1000.0,
                        "unrealized_pnl": 500.0,
                        "total_pnl": 1500.0,
                        "allocation_value": 30000.0,
                        "position_count": 3,
                    },
                    "tecl": {
                        "realized_pnl": 2000.0,
                        "unrealized_pnl": -200.0,
                        "total_pnl": 1800.0,
                        "allocation_value": 50000.0,
                        "position_count": 2,
                    },
                },
                "total_realized_pnl": 3000.0,
                "total_unrealized_pnl": 300.0,
                "total_strategy_pnl": 3300.0,
            },
            "positions_summary": {
                "total_positions": 5,
                "total_market_value": 90000.0,
                "total_unrealized_pnl": 800.0,
                "top_positions": [
                    {
                        "symbol": "AAPL",
                        "qty": 100.0,
                        "market_value": 15000.0,
                        "unrealized_pl": 500.0,
                        "current_price": 150.0,
                    },
                ],
            },
            "fees_and_costs": {
                "total_fees": 0.0,
                "note": "Alpaca provides commission-free trading",
            },
        }

        # Generate email HTML
        html = MonthlySummaryBuilder.build_monthly_summary_email(summary_data)

        # Verify HTML contains key elements
        assert "January 2024" in html
        assert "Monthly Trading Summary" in html
        assert "$100,000" in html  # Portfolio value
        assert "+$5,000" in html  # Monthly return
        assert "+5.3%" in html  # Return percentage
        assert "10" in html  # Total trades
        assert "NUCLEAR" in html  # Strategy name
        assert "AAPL" in html  # Position symbol
        assert "commission-free" in html  # Fees note

    def test_build_monthly_summary_email_empty_data(self):
        """Test monthly summary email with minimal data."""
        summary_data = {
            "month": "February 2024",
            "account_summary": {},
            "portfolio_performance": {},
            "trading_activity": {},
            "strategy_performance": {"strategies": {}},
            "positions_summary": {},
            "fees_and_costs": {},
        }

        # Should handle empty data gracefully
        html = MonthlySummaryBuilder.build_monthly_summary_email(summary_data)
        assert "February 2024" in html
        assert "Monthly Trading Summary" in html
        # Should contain warning messages for missing data
        assert "not available" in html or "No positions" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
