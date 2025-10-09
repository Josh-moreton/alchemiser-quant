#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Notification schema DTOs for The Alchemiser Trading System.

This module contains Pydantic models for email notifications and SMTP configuration.
Extracted from reporting.py to provide a focused schema for notification infrastructure.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EmailCredentials(BaseModel):
    """Email service credentials.

    Contains SMTP configuration for sending emails. Sensitive data should
    be redacted from logs. Password field has repr=False to prevent logging.

    Examples:
        >>> creds = EmailCredentials(
        ...     smtp_server="smtp.gmail.com",
        ...     smtp_port=587,
        ...     email_address="sender@example.com",
        ...     email_password="secret_password",
        ...     recipient_email="recipient@example.com"
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    smtp_server: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port", gt=0, le=65535)
    email_address: str = Field(description="Sender email address")
    email_password: str = Field(description="Email password (sensitive)", repr=False, min_length=1)
    recipient_email: str = Field(description="Default recipient email address")


class OrderSide(str, Enum):
    """Order side enumeration for buy/sell operations."""

    BUY = "BUY"
    SELL = "SELL"


class OrderNotificationDTO(BaseModel):
    """DTO for individual order data in email notifications.

    Attributes:
        side: Order side (BUY or SELL)
        symbol: Trading symbol
        qty: Order quantity
        estimated_value: Estimated dollar value of the order (optional)

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    side: OrderSide | str = Field(description="Order side (BUY or SELL)")
    symbol: str = Field(description="Trading symbol")
    qty: Decimal = Field(ge=0, description="Order quantity")
    estimated_value: Decimal | None = Field(
        default=None, ge=0, description="Estimated dollar value of the order"
    )


class TradingSummaryDTO(BaseModel):
    """DTO for trading summary metrics in email notifications.

    Attributes:
        total_trades: Total number of trades executed
        total_buy_value: Total dollar value of buy orders
        total_sell_value: Total dollar value of sell orders
        net_value: Net value (buy - sell)
        buy_orders: Number of buy orders
        sell_orders: Number of sell orders

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    total_trades: int = Field(ge=0, description="Total number of trades executed")
    total_buy_value: Decimal = Field(ge=0, description="Total dollar value of buy orders")
    total_sell_value: Decimal = Field(ge=0, description="Total dollar value of sell orders")
    net_value: Decimal = Field(description="Net value (buy - sell)")
    buy_orders: int = Field(ge=0, description="Number of buy orders")
    sell_orders: int = Field(ge=0, description="Number of sell orders")


class StrategyDataDTO(BaseModel):
    """DTO for individual strategy performance data.

    Attributes:
        allocation: Portfolio allocation percentage (0.0 to 1.0)
        signal: Trading signal (BUY, SELL, HOLD, etc.)
        symbol: Target symbol for the strategy
        reason: Optional reason or description for the signal

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    allocation: float = Field(ge=0, le=1, description="Portfolio allocation percentage (0.0 to 1.0)")
    signal: str = Field(description="Trading signal (BUY, SELL, HOLD, etc.)")
    symbol: str = Field(description="Target symbol for the strategy")
    reason: str = Field(default="", description="Optional reason or description for the signal")


# Public API
__all__ = [
    "EmailCredentials",
    "OrderNotificationDTO",
    "OrderSide",
    "StrategyDataDTO",
    "TradingSummaryDTO",
]
