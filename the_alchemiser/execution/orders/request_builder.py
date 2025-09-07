"""Business Unit: execution | Status: current.

Centralized order request builder for broker-agnostic order requests.

This module provides a single construction site for order requests using
broker-agnostic types, eliminating duplication across services and
ensuring consistent request building logic. It uses shared broker
abstractions to reduce coupling to specific broker APIs.

This module is the unified implementation after duplicate removal on 2025-01-03.
Duplicate file orders/order_request_builder.py was removed to eliminate redundancy.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.execution.types.broker_requests import (
    AlpacaRequestConverter,
    BrokerLimitOrderRequest,
    BrokerMarketOrderRequest,
)
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide, BrokerTimeInForce


class OrderRequestBuilder:
    """Centralized builder for broker-agnostic order requests."""

    @staticmethod
    def build_market_order_request(
        symbol: str,
        side: str,
        qty: float | Decimal | None = None,
        notional: float | Decimal | None = None,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> Any:  # Returns broker-specific request
        """Build a MarketOrderRequest with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            time_in_force: Order time in force (default: 'day')
            client_order_id: Optional client order ID

        Returns:
            Broker-specific MarketOrderRequest object

        Raises:
            ValueError: If parameters are invalid

        """
        # Convert string parameters to broker-agnostic types
        broker_side = BrokerOrderSide.from_string(side)
        broker_tif = BrokerTimeInForce.from_string(time_in_force)

        # Convert quantities to Decimal
        qty_decimal = Decimal(str(qty)) if qty is not None else None
        notional_decimal = Decimal(str(notional)) if notional is not None else None

        # Build broker-agnostic request (validates parameters)
        broker_request = BrokerMarketOrderRequest(
            symbol=symbol.upper(),
            side=broker_side,
            time_in_force=broker_tif,
            qty=qty_decimal,
            notional=notional_decimal,
            client_order_id=client_order_id,
        )

        # Convert to Alpaca-specific request
        return AlpacaRequestConverter.to_market_order(broker_request)

    @staticmethod
    def build_limit_order_request(
        symbol: str,
        side: str,
        quantity: float | Decimal,
        limit_price: float | Decimal,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> Any:  # Returns broker-specific request
        """Build a LimitOrderRequest with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')
            client_order_id: Optional client order ID

        Returns:
            Broker-specific LimitOrderRequest object

        Raises:
            ValueError: If parameters are invalid

        """
        # Convert string parameters to broker-agnostic types
        broker_side = BrokerOrderSide.from_string(side)
        broker_tif = BrokerTimeInForce.from_string(time_in_force)

        # Convert quantities to Decimal
        qty_decimal = Decimal(str(quantity))
        price_decimal = Decimal(str(limit_price))

        # Build broker-agnostic request (validates parameters)
        broker_request = BrokerLimitOrderRequest(
            symbol=symbol.upper(),
            side=broker_side,
            time_in_force=broker_tif,
            qty=qty_decimal,
            limit_price=price_decimal,
            client_order_id=client_order_id,
        )

        # Convert to Alpaca-specific request
        return AlpacaRequestConverter.to_limit_order(broker_request)
