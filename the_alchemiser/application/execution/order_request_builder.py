"""Centralized order request builder for Alpaca API requests.

This module provides a single construction site for MarketOrderRequest and
LimitOrderRequest objects, eliminating duplication across services and
ensuring consistent request building logic.
"""

from __future__ import annotations

from decimal import Decimal

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest


class OrderRequestBuilder:
    """Centralized builder for Alpaca order requests."""

    @staticmethod
    def build_market_order_request(
        symbol: str,
        side: str,
        qty: float | Decimal | None = None,
        notional: float | Decimal | None = None,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> MarketOrderRequest:
        """Build a MarketOrderRequest with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            time_in_force: Order time in force (default: 'day')
            client_order_id: Optional client order ID

        Returns:
            MarketOrderRequest object

        Raises:
            ValueError: If parameters are invalid
        """
        # Validation
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        if qty is None and notional is None:
            raise ValueError("Either qty or notional must be specified")

        if qty is not None and notional is not None:
            raise ValueError("Cannot specify both qty and notional")

        if qty is not None and qty <= 0:
            raise ValueError("Quantity must be positive")

        if notional is not None and notional <= 0:
            raise ValueError("Notional amount must be positive")

        side_normalized = side.lower().strip()
        if side_normalized not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")

        # Convert side to Alpaca enum
        alpaca_side = OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL

        # Convert time in force to Alpaca enum
        tif_mapping = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
        }

        tif_normalized = time_in_force.lower().strip()
        if tif_normalized not in tif_mapping:
            raise ValueError(f"Invalid time_in_force: {time_in_force}")

        alpaca_tif = tif_mapping[tif_normalized]

        # Build request (ensure Decimal conversion at boundary)
        return MarketOrderRequest(
            symbol=symbol.upper(),
            qty=float(qty) if qty is not None else None,
            notional=float(notional) if notional is not None else None,
            side=alpaca_side,
            time_in_force=alpaca_tif,
            client_order_id=client_order_id,
        )

    @staticmethod
    def build_limit_order_request(
        symbol: str,
        side: str,
        quantity: float | Decimal,
        limit_price: float | Decimal,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> LimitOrderRequest:
        """Build a LimitOrderRequest with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')
            client_order_id: Optional client order ID

        Returns:
            LimitOrderRequest object

        Raises:
            ValueError: If parameters are invalid
        """
        # Validation
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if limit_price <= 0:
            raise ValueError("Limit price must be positive")

        side_normalized = side.lower().strip()
        if side_normalized not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")

        # Convert side to Alpaca enum
        alpaca_side = OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL

        # Convert time in force to Alpaca enum
        tif_mapping = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
        }

        tif_normalized = time_in_force.lower().strip()
        if tif_normalized not in tif_mapping:
            raise ValueError(f"Invalid time_in_force: {time_in_force}")

        alpaca_tif = tif_mapping[tif_normalized]

        # Build request (ensure Decimal conversion at boundary)
        return LimitOrderRequest(
            symbol=symbol.upper(),
            qty=float(quantity),
            side=alpaca_side,
            time_in_force=alpaca_tif,
            limit_price=float(limit_price),
            client_order_id=client_order_id,
        )
