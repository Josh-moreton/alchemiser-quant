#!/usr/bin/env python3
"""Test suite for shared.schemas.reporting module.

Tests all reporting DTOs for:
- Successful instantiation with valid data
- Field validation and constraints
- Frozen/immutability enforcement
- Default factory behavior
- Sensitive data repr behavior
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.reporting import (
    BacktestResult,
    DashboardMetrics,
    EmailCredentials,
    EmailReportData,
    EmailSummary,
    MonthlySummaryDTO,
    PerformanceMetrics,
    ReportingData,
)
from the_alchemiser.shared.value_objects.core_types import (
    OrderDetails,
    StrategyPnLSummary,
)


class TestDashboardMetrics:
    """Test DashboardMetrics DTO."""

    def test_create_dashboard_metrics_valid(self):
        """Test creating DashboardMetrics with valid data."""
        metrics = DashboardMetrics(
            total_portfolio_value=Decimal("100000.00"),
            daily_pnl=Decimal("1234.56"),
            daily_pnl_percentage=Decimal("1.23"),
            active_positions=5,
            cash_balance=Decimal("50000.00"),
        )
        
        assert metrics.total_portfolio_value == Decimal("100000.00")
        assert metrics.daily_pnl == Decimal("1234.56")
        assert metrics.daily_pnl_percentage == Decimal("1.23")
        assert metrics.active_positions == 5
        assert metrics.cash_balance == Decimal("50000.00")

    def test_dashboard_metrics_frozen(self):
        """Test that DashboardMetrics is immutable."""
        metrics = DashboardMetrics(
            total_portfolio_value=Decimal("100000.00"),
            daily_pnl=Decimal("1234.56"),
            daily_pnl_percentage=Decimal("1.23"),
            active_positions=5,
            cash_balance=Decimal("50000.00"),
        )
        
        with pytest.raises(ValidationError):
            metrics.total_portfolio_value = Decimal("200000.00")

    def test_dashboard_metrics_negative_positions_rejected(self):
        """Test that negative active_positions is rejected."""
        with pytest.raises(ValidationError):
            DashboardMetrics(
                total_portfolio_value=Decimal("100000.00"),
                daily_pnl=Decimal("1234.56"),
                daily_pnl_percentage=Decimal("1.23"),
                active_positions=-1,
                cash_balance=Decimal("50000.00"),
            )

    def test_dashboard_metrics_negative_pnl(self):
        """Test that negative P&L is allowed."""
        metrics = DashboardMetrics(
            total_portfolio_value=Decimal("100000.00"),
            daily_pnl=Decimal("-1234.56"),
            daily_pnl_percentage=Decimal("-1.23"),
            active_positions=5,
            cash_balance=Decimal("50000.00"),
        )
        
        assert metrics.daily_pnl == Decimal("-1234.56")


class TestReportingData:
    """Test ReportingData DTO."""

    def test_create_reporting_data_valid(self):
        """Test creating ReportingData with valid data."""
        data = ReportingData(
            timestamp="2025-01-08T10:00:00Z",
            portfolio_summary={"equity": "100000.00", "cash": "50000.00"},
            performance_metrics={"sharpe": Decimal("1.5"), "return": Decimal("0.15")},
            recent_trades=[],
        )
        
        assert data.timestamp == "2025-01-08T10:00:00Z"
        assert data.portfolio_summary["equity"] == "100000.00"
        assert data.performance_metrics["sharpe"] == Decimal("1.5")
        assert data.recent_trades == []

    def test_reporting_data_default_factory(self):
        """Test that recent_trades default_factory works."""
        data = ReportingData(
            timestamp="2025-01-08T10:00:00Z",
            portfolio_summary={},
            performance_metrics={},
        )
        
        assert data.recent_trades == []
        assert isinstance(data.recent_trades, list)

    def test_reporting_data_frozen(self):
        """Test that ReportingData is immutable."""
        data = ReportingData(
            timestamp="2025-01-08T10:00:00Z",
            portfolio_summary={},
            performance_metrics={},
        )
        
        with pytest.raises(ValidationError):
            data.timestamp = "2025-01-09T10:00:00Z"


class TestEmailReportData:
    """Test EmailReportData DTO."""

    def test_create_email_report_data_valid(self):
        """Test creating EmailReportData with valid data."""
        data = EmailReportData(
            subject="Trading Report",
            html_content="<html><body>Report</body></html>",
            recipient="user@example.com",
            metadata={"sender": "system"},
        )
        
        assert data.subject == "Trading Report"
        assert data.html_content == "<html><body>Report</body></html>"
        assert data.recipient == "user@example.com"
        assert data.metadata["sender"] == "system"

    def test_email_report_data_default_metadata(self):
        """Test that metadata default_factory works."""
        data = EmailReportData(
            subject="Trading Report",
            html_content="<html><body>Report</body></html>",
            recipient="user@example.com",
        )
        
        assert data.metadata == {}
        assert isinstance(data.metadata, dict)

    def test_email_report_data_frozen(self):
        """Test that EmailReportData is immutable."""
        data = EmailReportData(
            subject="Trading Report",
            html_content="<html><body>Report</body></html>",
            recipient="user@example.com",
        )
        
        with pytest.raises(ValidationError):
            data.subject = "New Subject"


class TestEmailCredentials:
    """Test EmailCredentials DTO."""

    def test_create_email_credentials_valid(self):
        """Test creating EmailCredentials with valid data."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        assert creds.smtp_server == "smtp.example.com"
        assert creds.smtp_port == 587
        assert creds.email_address == "sender@example.com"
        assert creds.email_password == "secret123"
        assert creds.recipient_email == "recipient@example.com"

    def test_email_credentials_password_repr_redacted(self):
        """Test that password is not shown in repr."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        repr_str = repr(creds)
        assert "secret123" not in repr_str
        assert "email_password" not in repr_str or "**" in repr_str

    def test_email_credentials_port_validation(self):
        """Test that smtp_port is validated."""
        # Port must be > 0
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=0,
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )
        
        # Port must be <= 65535
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=65536,
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )

    def test_email_credentials_frozen(self):
        """Test that EmailCredentials is immutable."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        with pytest.raises(ValidationError):
            creds.smtp_port = 465


class TestEmailSummary:
    """Test EmailSummary DTO."""

    def test_create_email_summary_valid(self):
        """Test creating EmailSummary with valid data."""
        summary = EmailSummary(
            total_orders=10,
            recent_orders=[],
            performance_metrics={"sharpe": Decimal("1.5")},
            strategy_summaries={},
        )
        
        assert summary.total_orders == 10
        assert summary.recent_orders == []
        assert summary.performance_metrics["sharpe"] == Decimal("1.5")
        assert summary.strategy_summaries == {}

    def test_email_summary_default_factories(self):
        """Test that all default_factory fields work."""
        summary = EmailSummary(total_orders=0)
        
        assert summary.recent_orders == []
        assert summary.performance_metrics == {}
        assert summary.strategy_summaries == {}

    def test_email_summary_negative_orders_rejected(self):
        """Test that negative total_orders is rejected."""
        with pytest.raises(ValidationError):
            EmailSummary(total_orders=-1)

    def test_email_summary_frozen(self):
        """Test that EmailSummary is immutable."""
        summary = EmailSummary(total_orders=10)
        
        with pytest.raises(ValidationError):
            summary.total_orders = 20


class TestBacktestResult:
    """Test BacktestResult DTO."""

    def test_create_backtest_result_valid(self):
        """Test creating BacktestResult with valid data."""
        result = BacktestResult(
            strategy_name="TestStrategy",
            start_date="2025-01-01",
            end_date="2025-01-08",
            total_return=Decimal("15.5"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-10.2"),
            total_trades=100,
            win_rate=Decimal("65.5"),
            metadata={"version": "1.0"},
        )
        
        assert result.strategy_name == "TestStrategy"
        assert result.start_date == "2025-01-01"
        assert result.end_date == "2025-01-08"
        assert result.total_return == Decimal("15.5")
        assert result.sharpe_ratio == Decimal("1.8")
        assert result.max_drawdown == Decimal("-10.2")
        assert result.total_trades == 100
        assert result.win_rate == Decimal("65.5")

    def test_backtest_result_win_rate_validation(self):
        """Test that win_rate is validated in range [0, 100]."""
        # Win rate above 100 should be rejected
        with pytest.raises(ValidationError):
            BacktestResult(
                strategy_name="TestStrategy",
                start_date="2025-01-01",
                end_date="2025-01-08",
                total_return=Decimal("15.5"),
                sharpe_ratio=Decimal("1.8"),
                max_drawdown=Decimal("-10.2"),
                total_trades=100,
                win_rate=Decimal("150.0"),
            )
        
        # Negative win rate should be rejected
        with pytest.raises(ValidationError):
            BacktestResult(
                strategy_name="TestStrategy",
                start_date="2025-01-01",
                end_date="2025-01-08",
                total_return=Decimal("15.5"),
                sharpe_ratio=Decimal("1.8"),
                max_drawdown=Decimal("-10.2"),
                total_trades=100,
                win_rate=Decimal("-10.0"),
            )

    def test_backtest_result_negative_trades_rejected(self):
        """Test that negative total_trades is rejected."""
        with pytest.raises(ValidationError):
            BacktestResult(
                strategy_name="TestStrategy",
                start_date="2025-01-01",
                end_date="2025-01-08",
                total_return=Decimal("15.5"),
                sharpe_ratio=Decimal("1.8"),
                max_drawdown=Decimal("-10.2"),
                total_trades=-1,
                win_rate=Decimal("65.5"),
            )

    def test_backtest_result_frozen(self):
        """Test that BacktestResult is immutable."""
        result = BacktestResult(
            strategy_name="TestStrategy",
            start_date="2025-01-01",
            end_date="2025-01-08",
            total_return=Decimal("15.5"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-10.2"),
            total_trades=100,
            win_rate=Decimal("65.5"),
        )
        
        with pytest.raises(ValidationError):
            result.total_return = Decimal("20.0")


class TestPerformanceMetrics:
    """Test PerformanceMetrics DTO."""

    def test_create_performance_metrics_valid(self):
        """Test creating PerformanceMetrics with valid data."""
        metrics = PerformanceMetrics(
            returns=[Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")],
            cumulative_return=Decimal("15.5"),
            volatility=Decimal("10.2"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-10.2"),
            calmar_ratio=Decimal("1.52"),
            sortino_ratio=Decimal("2.1"),
        )
        
        assert len(metrics.returns) == 3
        assert metrics.returns[0] == Decimal("0.01")
        assert metrics.cumulative_return == Decimal("15.5")
        assert metrics.volatility == Decimal("10.2")
        assert metrics.sharpe_ratio == Decimal("1.8")
        assert metrics.max_drawdown == Decimal("-10.2")
        assert metrics.calmar_ratio == Decimal("1.52")
        assert metrics.sortino_ratio == Decimal("2.1")

    def test_performance_metrics_default_returns(self):
        """Test that returns default_factory works."""
        metrics = PerformanceMetrics(
            cumulative_return=Decimal("15.5"),
            volatility=Decimal("10.2"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-10.2"),
            calmar_ratio=Decimal("1.52"),
            sortino_ratio=Decimal("2.1"),
        )
        
        assert metrics.returns == []

    def test_performance_metrics_volatility_validation(self):
        """Test that volatility is validated to be non-negative."""
        with pytest.raises(ValidationError):
            PerformanceMetrics(
                cumulative_return=Decimal("15.5"),
                volatility=Decimal("-10.2"),
                sharpe_ratio=Decimal("1.8"),
                max_drawdown=Decimal("-10.2"),
                calmar_ratio=Decimal("1.52"),
                sortino_ratio=Decimal("2.1"),
            )

    def test_performance_metrics_frozen(self):
        """Test that PerformanceMetrics is immutable."""
        metrics = PerformanceMetrics(
            cumulative_return=Decimal("15.5"),
            volatility=Decimal("10.2"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-10.2"),
            calmar_ratio=Decimal("1.52"),
            sortino_ratio=Decimal("2.1"),
        )
        
        with pytest.raises(ValidationError):
            metrics.volatility = Decimal("20.0")


class TestMonthlySummaryDTO:
    """Test MonthlySummaryDTO DTO."""

    def test_create_monthly_summary_valid(self):
        """Test creating MonthlySummaryDTO with valid data."""
        summary = MonthlySummaryDTO(
            month_label="Jan 2025",
            portfolio_first_value=Decimal("100000.00"),
            portfolio_last_value=Decimal("105000.00"),
            portfolio_pnl_abs=Decimal("5000.00"),
            portfolio_pnl_pct=Decimal("5.0"),
            strategy_rows=[{"name": "Strategy1", "pnl": "1000.00"}],
            notes=["Note 1", "Note 2"],
        )
        
        assert summary.month_label == "Jan 2025"
        assert summary.portfolio_first_value == Decimal("100000.00")
        assert summary.portfolio_last_value == Decimal("105000.00")
        assert summary.portfolio_pnl_abs == Decimal("5000.00")
        assert summary.portfolio_pnl_pct == Decimal("5.0")
        assert len(summary.strategy_rows) == 1
        assert len(summary.notes) == 2

    def test_monthly_summary_optional_fields(self):
        """Test that optional fields can be None."""
        summary = MonthlySummaryDTO(
            month_label="Jan 2025",
            portfolio_first_value=None,
            portfolio_last_value=None,
            portfolio_pnl_abs=None,
            portfolio_pnl_pct=None,
        )
        
        assert summary.portfolio_first_value is None
        assert summary.portfolio_last_value is None
        assert summary.portfolio_pnl_abs is None
        assert summary.portfolio_pnl_pct is None

    def test_monthly_summary_default_factories(self):
        """Test that default_factory fields work."""
        summary = MonthlySummaryDTO(month_label="Jan 2025")
        
        assert summary.strategy_rows == []
        assert summary.notes == []

    def test_monthly_summary_frozen(self):
        """Test that MonthlySummaryDTO is immutable."""
        summary = MonthlySummaryDTO(
            month_label="Jan 2025",
            portfolio_first_value=Decimal("100000.00"),
        )
        
        with pytest.raises(ValidationError):
            summary.month_label = "Feb 2025"

    def test_monthly_summary_decimal_precision(self):
        """Test that Decimal precision is preserved."""
        summary = MonthlySummaryDTO(
            month_label="Jan 2025",
            portfolio_first_value=Decimal("100000.123456789"),
        )
        
        # Decimal precision should be preserved
        assert summary.portfolio_first_value == Decimal("100000.123456789")
