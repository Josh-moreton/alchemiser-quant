#!/usr/bin/env python3
"""Test suite for shared.schemas.notifications module.

Tests EmailCredentials DTO for:
- Successful instantiation with valid data
- Field validation and constraints
- Frozen/immutability enforcement
- Sensitive data repr behavior
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.notifications import EmailCredentials


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


# Import new DTOs for testing
from decimal import Decimal

from the_alchemiser.shared.schemas.notifications import (
    OrderNotificationDTO,
    OrderSide,
    StrategyDataDTO,
    TradingSummaryDTO,
)


class TestOrderSide:
    """Test OrderSide enum."""

    def test_order_side_values(self):
        """Test OrderSide enum values."""
        assert OrderSide.BUY.value == "BUY"
        assert OrderSide.SELL.value == "SELL"


class TestOrderNotificationDTO:
    """Test OrderNotificationDTO."""

    def test_create_order_notification_valid(self):
        """Test creating OrderNotificationDTO with valid data."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10.5"),
            estimated_value=Decimal("1500.50"),
        )

        assert order.side == OrderSide.BUY
        assert order.symbol == "AAPL"
        assert order.qty == Decimal("10.5")
        assert order.estimated_value == Decimal("1500.50")

    def test_create_order_notification_without_value(self):
        """Test creating OrderNotificationDTO without estimated_value."""
        order = OrderNotificationDTO(
            side=OrderSide.SELL,
            symbol="TSLA",
            qty=Decimal("5"),
        )

        assert order.side == OrderSide.SELL
        assert order.estimated_value is None

    def test_order_notification_frozen(self):
        """Test that OrderNotificationDTO is immutable."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10"),
        )

        with pytest.raises(ValidationError):
            order.symbol = "TSLA"

    def test_order_notification_negative_qty_fails(self):
        """Test that negative qty raises validation error."""
        with pytest.raises(ValidationError):
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("-10"),
            )


class TestTradingSummaryDTO:
    """Test TradingSummaryDTO."""

    def test_create_trading_summary_valid(self):
        """Test creating TradingSummaryDTO with valid data."""
        summary = TradingSummaryDTO(
            total_trades=10,
            total_buy_value=Decimal("50000"),
            total_sell_value=Decimal("30000"),
            net_value=Decimal("20000"),
            buy_orders=6,
            sell_orders=4,
        )

        assert summary.total_trades == 10
        assert summary.total_buy_value == Decimal("50000")
        assert summary.net_value == Decimal("20000")

    def test_trading_summary_frozen(self):
        """Test that TradingSummaryDTO is immutable."""
        summary = TradingSummaryDTO(
            total_trades=5,
            total_buy_value=Decimal("10000"),
            total_sell_value=Decimal("8000"),
            net_value=Decimal("2000"),
            buy_orders=3,
            sell_orders=2,
        )

        with pytest.raises(ValidationError):
            summary.total_trades = 10

    def test_trading_summary_negative_counts_fail(self):
        """Test that negative counts raise validation error."""
        with pytest.raises(ValidationError):
            TradingSummaryDTO(
                total_trades=-1,
                total_buy_value=Decimal("10000"),
                total_sell_value=Decimal("8000"),
                net_value=Decimal("2000"),
                buy_orders=3,
                sell_orders=2,
            )


class TestStrategyDataDTO:
    """Test StrategyDataDTO."""

    def test_create_strategy_data_valid(self):
        """Test creating StrategyDataDTO with valid data."""
        strategy = StrategyDataDTO(
            allocation=0.5,
            signal="BUY",
            symbol="AAPL",
            reason="Strong momentum",
        )

        assert strategy.allocation == 0.5
        assert strategy.signal == "BUY"
        assert strategy.symbol == "AAPL"
        assert strategy.reason == "Strong momentum"

    def test_strategy_data_without_reason(self):
        """Test creating StrategyDataDTO without reason."""
        strategy = StrategyDataDTO(
            allocation=0.3,
            signal="SELL",
            symbol="TSLA",
        )

        assert strategy.reason == ""

    def test_strategy_data_allocation_bounds(self):
        """Test allocation validation (must be 0.0 to 1.0)."""
        # Valid at boundaries
        strategy = StrategyDataDTO(
            allocation=0.0,
            signal="HOLD",
            symbol="MSFT",
        )
        assert strategy.allocation == 0.0

        strategy = StrategyDataDTO(
            allocation=1.0,
            signal="BUY",
            symbol="GOOGL",
        )
        assert strategy.allocation == 1.0

        # Invalid: negative
        with pytest.raises(ValidationError):
            StrategyDataDTO(
                allocation=-0.1,
                signal="BUY",
                symbol="AAPL",
            )

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            StrategyDataDTO(
                allocation=1.5,
                signal="BUY",
                symbol="AAPL",
            )

    def test_strategy_data_frozen(self):
        """Test that StrategyDataDTO is immutable."""
        strategy = StrategyDataDTO(
            allocation=0.5,
            signal="BUY",
            symbol="AAPL",
        )

        with pytest.raises(ValidationError):
            strategy.allocation = 0.7

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

    def test_email_credentials_password_min_length(self):
        """Test that password must have min_length=1."""
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=587,
                email_address="sender@example.com",
                email_password="",  # Empty password should fail
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

    def test_email_credentials_strict_validation(self):
        """Test that strict validation is enabled."""
        # String value for port should fail with strict=True
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port="587",  # type: ignore - intentionally wrong type
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )
