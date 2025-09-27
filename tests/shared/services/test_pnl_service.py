#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for P&L service functionality.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from the_alchemiser.shared.services.pnl_service import PnLData, PnLService


class TestPnLData:
    """Test cases for P&L data container."""
    
    def test_pnl_data_creation(self) -> None:
        """Test basic P&L data creation."""
        data = PnLData(
            period="1 week",
            start_date="2025-01-01",
            end_date="2025-01-07",
            start_value=Decimal("10000.00"),
            end_value=Decimal("10500.00"),
            total_pnl=Decimal("500.00"),
            total_pnl_pct=Decimal("5.00"),
        )
        
        assert data.period == "1 week"
        assert data.start_date == "2025-01-01"
        assert data.end_date == "2025-01-07"
        assert data.start_value == Decimal("10000.00")
        assert data.end_value == Decimal("10500.00")
        assert data.total_pnl == Decimal("500.00")
        assert data.total_pnl_pct == Decimal("5.00")
        assert data.daily_data == []


class TestPnLService:
    """Test cases for P&L service."""
    
    def test_pnl_service_with_mock_manager(self) -> None:
        """Test P&L service creation with mock Alpaca manager."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        assert service._alpaca_manager == mock_manager
    
    def test_process_history_data(self) -> None:
        """Test processing of portfolio history data."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        
        # Mock portfolio history data
        history_data = {
            "timestamp": [1640995200, 1641081600],  # 2022-01-01, 2022-01-02
            "equity": [10000.00, 10500.00],
            "profit_loss": [0.00, 500.00],
            "profit_loss_pct": [0.00, 5.00],
            "base_value": 10000.00,
            "timeframe": "1Day",
        }
        
        result = service._process_history_data(history_data, "test period")
        
        assert result.period == "test period"
        assert result.start_value == Decimal("10000.00")
        assert result.end_value == Decimal("10500.00")
        assert result.total_pnl == Decimal("500.00")
        assert result.total_pnl_pct == Decimal("5.00")
        assert len(result.daily_data) == 2
    
    def test_process_empty_history_data(self) -> None:
        """Test processing of empty portfolio history data."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        
        history_data = {"timestamp": [], "equity": []}
        result = service._process_history_data(history_data, "test period")
        
        assert result.period == "test period"
        assert result.start_value is None
        assert result.end_value is None
        assert result.total_pnl is None
        assert result.total_pnl_pct is None
        assert result.daily_data == []
    
    def test_format_pnl_report_basic(self) -> None:
        """Test basic P&L report formatting."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        
        pnl_data = PnLData(
            period="1 week",
            start_date="2025-01-01",
            end_date="2025-01-07",
            start_value=Decimal("10000.00"),
            end_value=Decimal("10500.00"),
            total_pnl=Decimal("500.00"),
            total_pnl_pct=Decimal("5.00"),
        )
        
        report = service.format_pnl_report(pnl_data)
        
        assert "📊 Portfolio P&L Report - 1 Week" in report
        assert "Period: 2025-01-01 to 2025-01-07" in report
        assert "Starting Value: $10,000.00" in report
        assert "Ending Value: $10,500.00" in report
        assert "Total P&L: 📈 $+500.00" in report
        assert "Total P&L %: +5.00%" in report
    
    def test_format_pnl_report_negative(self) -> None:
        """Test P&L report formatting with negative values."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        
        pnl_data = PnLData(
            period="1 month",
            start_date="2025-01-01",
            end_date="2025-01-31",
            start_value=Decimal("10000.00"),
            end_value=Decimal("9500.00"),
            total_pnl=Decimal("-500.00"),
            total_pnl_pct=Decimal("-5.00"),
        )
        
        report = service.format_pnl_report(pnl_data)
        
        assert "📊 Portfolio P&L Report - 1 Month" in report
        assert "Total P&L: 📉 $-500.00" in report
        assert "Total P&L %: -5.00%" in report
    
    def test_format_pnl_report_detailed(self) -> None:
        """Test detailed P&L report formatting."""
        mock_manager = Mock()
        service = PnLService(alpaca_manager=mock_manager)
        
        pnl_data = PnLData(
            period="1 week",
            start_date="2025-01-01",
            end_date="2025-01-02",
            start_value=Decimal("10000.00"),
            end_value=Decimal("10500.00"),
            total_pnl=Decimal("500.00"),
            total_pnl_pct=Decimal("5.00"),
            daily_data=[
                {
                    "date": "2025-01-01",
                    "equity": Decimal("10000.00"),
                    "profit_loss": Decimal("0.00"),
                    "profit_loss_pct": Decimal("0.00"),
                },
                {
                    "date": "2025-01-02",
                    "equity": Decimal("10500.00"),
                    "profit_loss": Decimal("500.00"),
                    "profit_loss_pct": Decimal("5.00"),
                },
            ],
        )
        
        report = service.format_pnl_report(pnl_data, detailed=True)
        
        assert "Daily Breakdown:" in report
        assert "2025-01-01: $10,000.00 | P&L: $+0.00 (+0.00%)" in report
        assert "2025-01-02: $10,500.00 | P&L: $+500.00 (+5.00%)" in report
    
    def test_get_period_pnl_with_mock(self) -> None:
        """Test get_period_pnl with mocked Alpaca manager."""
        mock_manager = Mock()
        mock_manager.get_portfolio_history.return_value = {
            "timestamp": [1640995200],
            "equity": [10000.00],
            "profit_loss": [0.00],
            "profit_loss_pct": [0.00],
            "base_value": 10000.00,
            "timeframe": "1Day",
        }
        
        service = PnLService(alpaca_manager=mock_manager)
        result = service.get_period_pnl("1W")
        
        mock_manager.get_portfolio_history.assert_called_once_with(period="1W")
        assert result.period == "1W"
        assert result.start_value == Decimal("10000.00")
    
    def test_get_period_pnl_with_failure(self) -> None:
        """Test get_period_pnl when Alpaca manager fails."""
        mock_manager = Mock()
        mock_manager.get_portfolio_history.return_value = None
        
        service = PnLService(alpaca_manager=mock_manager)
        result = service.get_period_pnl("1W")
        
        assert result.period == "1W"
        assert result.start_value is None
        assert result.end_value is None