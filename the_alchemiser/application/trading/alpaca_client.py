#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Alpaca Client for Direct API Access.

A streamlined, robust wrapper around Alpaca's trading APIs that provides direct access
to core trading functions. This client has been refactored to use helper modules for
better code organization and maintainability.

Key Features:
    - Direct Alpaca API usage for positions, orders, and trades
    - Position validation to prevent overselling
    - Clean order management with automatic cancellation
    - Liquidation API for safe full position exits
    - Clear error handling with transparent logging
    - Modular design using specialized helper utilities

Order Placement Logic:
    Selling Positions:
        - Partial sales (< 99%): Use market orders
        - Full sales (≥ 99%): Use Alpaca's close_position() API
        - Always validate position exists before selling
        - Automatically cap sell quantity to available shares

    Buying Positions:
        - Use market orders for immediate execution
        - Cancel existing orders first to avoid conflicts
        - Round quantities to avoid fractional share issues
        - Validate positive quantities and prices

Safety Features:
    - Position validation before every sell order
    - Automatic quantity capping to prevent overselling
    - Order cancellation before new orders to prevent conflicts
    - Liquidation API usage for full position exits
    - Smart asset-specific handling for fractionable vs non-fractionable assets
    - Clear logging of all order attempts and results

Example:
    Canonical order placement (preferred):

    >>> from the_alchemiser.application.execution.canonical_executor import CanonicalOrderExecutor
    >>> from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
    >>> from the_alchemiser.domain.trading.value_objects.symbol import Symbol
    >>> from the_alchemiser.domain.trading.value_objects.side import Side
    >>> from the_alchemiser.domain.trading.value_objects.quantity import Quantity
    >>> from the_alchemiser.domain.trading.value_objects.order_type import OrderType
    >>> from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce
    >>> client = AlpacaClient(trading_client, data_provider)
    >>> executor = CanonicalOrderExecutor(client.alpaca_manager)
    >>> req = OrderRequest(symbol=Symbol('AAPL'), side=Side('buy'), quantity=Quantity(Decimal('10')), order_type=OrderType('market'), time_in_force=TimeInForce('day'))  # noqa: E501
    >>> result = executor.execute(req)

"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import (
        DataProvider as ExecDataProvider,
    )
    from the_alchemiser.interfaces.schemas.orders import ValidatedOrderDTO

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.smart_pricing_handler import (
    SmartPricingHandler,
)
from the_alchemiser.application.orders.asset_order_handler import AssetOrderHandler

# DEPRECATED: LimitOrderHandler import removed - use CanonicalOrderExecutor instead
# (Legacy order validation utilities removed with legacy paths)
from the_alchemiser.infrastructure.websocket.websocket_connection_manager import (
    WebSocketConnectionManager,
)
from the_alchemiser.infrastructure.websocket.websocket_order_monitor import (
    OrderCompletionMonitor,
)
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO

# (Legacy exceptions import removed)
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager
from the_alchemiser.services.trading.position_manager import PositionManager

logger = logging.getLogger(__name__)


class AlpacaClient:
    """Streamlined Alpaca API client for reliable order execution.

    This client has been refactored to use specialized helper modules for:
    - Order validation and parameter handling
    - WebSocket-based order monitoring
    - Asset-specific order logic
    - Position management operations

    Attributes:
        alpaca_manager: AlpacaManager instance for centralized Alpaca operations.
        trading_client: Alpaca trading client for API calls (backward compatibility).
        data_provider: Data provider for market quotes and prices.
        validate_buying_power: Whether to validate buying power for buy orders.

    """

    class PriceQuoteProvider(Protocol):
        """Minimal interface for price/quote access used by order helpers."""

        def get_current_price(self, symbol: str) -> float | None: ...

        def get_latest_quote(self, symbol: str) -> tuple[float, float] | None: ...

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        data_provider: ExecDataProvider,
        validate_buying_power: bool = False,
    ) -> None:
        """Initialize AlpacaClient with helper modules.

        Args:
            alpaca_manager: AlpacaManager instance for Alpaca API operations.
            data_provider: Data provider for quotes and prices.
            validate_buying_power: Whether to validate buying power for buy orders.

        """
        self.alpaca_manager = alpaca_manager
        self.trading_client = alpaca_manager.trading_client  # Backward compatibility
        self.data_provider = data_provider
        self.validate_buying_power = validate_buying_power

        # Initialize helper modules
        # Provide API keys to the order monitor from AlpacaManager (authoritative source)
        api_key = getattr(self.alpaca_manager, "api_key", None)
        secret_key = getattr(self.alpaca_manager, "secret_key", None)
        self.order_monitor = OrderCompletionMonitor(
            self.trading_client, api_key=api_key, secret_key=secret_key
        )
        self.asset_handler = AssetOrderHandler(data_provider)
        self.position_manager = PositionManager(self.trading_client, data_provider)
        # DEPRECATED: LimitOrderHandler removed - use CanonicalOrderExecutor instead
        self.pricing_handler = SmartPricingHandler(data_provider)
        self.websocket_manager = WebSocketConnectionManager(self.trading_client)

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions from Alpaca.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        return self.position_manager.get_current_positions()

    def get_pending_orders_validated(self) -> list[ValidatedOrderDTO]:
        """Get all pending orders from Alpaca with type safety.

        Returns:
            List of ValidatedOrderDTO instances for type-safe order handling.

        """
        try:
            raw_orders = self.position_manager.get_pending_orders()

            validated_orders: list[ValidatedOrderDTO] = []
            for order_dict in raw_orders.values():  # Iterate over values, not keys
                try:
                    # Convert dict to OrderRequestDTO first, then to ValidatedOrderDTO
                    from the_alchemiser.application.mapping.orders import (
                        dict_to_order_request_dto,
                        order_request_to_validated_dto,
                    )

                    order_request = dict_to_order_request_dto(order_dict)
                    validated_order = order_request_to_validated_dto(order_request)
                    validated_orders.append(validated_order)
                except Exception as e:
                    order_id = order_dict.get("id", "?") if isinstance(order_dict, dict) else "?"
                    logger.error(f"Failed to validate pending order {order_id}: {e}")

            logger.info(
                f"📋 Retrieved {len(validated_orders)} validated pending orders "
                f"(from {len(raw_orders)} raw orders)"
            )

            return validated_orders

        except Exception as e:
            logger.error(f"Failed to get validated pending orders: {e}")
            return []

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all pending orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol

        Returns:
            True if successful, False otherwise

        """
        if symbol:
            return self.position_manager.cancel_symbol_orders(symbol)
        return self.position_manager.cancel_all_orders()

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using Alpaca's close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed

        """
        # Cancel any pending orders for this symbol first
        self.cancel_all_orders(symbol)
        time.sleep(0.5)  # Brief pause for cancellations to process

        return self.position_manager.execute_liquidation(symbol)

    # Legacy direct order placement methods removed - use CanonicalOrderExecutor externally.

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using canonical executor."""
        from decimal import Decimal

        from the_alchemiser.application.execution.canonical_executor import (
            CanonicalOrderExecutor,
        )
        from the_alchemiser.domain.trading.value_objects.order_request import (
            OrderRequest,
        )
        from the_alchemiser.domain.trading.value_objects.order_type import OrderType
        from the_alchemiser.domain.trading.value_objects.quantity import Quantity
        from the_alchemiser.domain.trading.value_objects.side import Side
        from the_alchemiser.domain.trading.value_objects.symbol import Symbol
        from the_alchemiser.domain.trading.value_objects.time_in_force import (
            TimeInForce,
        )

        try:
            order_request = OrderRequest(
                symbol=Symbol(symbol),
                side=Side("sell"),
                quantity=Quantity(Decimal(str(qty))),
                order_type=OrderType("market"),
                time_in_force=TimeInForce("day"),
                limit_price=None,
            )
            executor = CanonicalOrderExecutor(self.alpaca_manager)
            result = executor.execute(order_request)
            return result.order_id if result.success else None
        except Exception as e:
            logger.error(f"Smart sell order failed: {e}")
            return None

    def get_smart_limit_price(
        self, symbol: str, side: OrderSide, aggressiveness: float = 0.5
    ) -> float | None:
        """Get a smart limit price based on current bid/ask.

        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            aggressiveness: 0.0 = most conservative, 1.0 = most aggressive (market price)

        Returns:
            Calculated limit price, or None if data unavailable

        """
        return self.pricing_handler.get_smart_limit_price(symbol, side, aggressiveness)

    def get_aggressive_sell_price(self, symbol: str) -> float | None:
        """Get aggressive sell pricing for quick liquidation."""
        return self.pricing_handler.get_aggressive_sell_price(symbol)

    def get_conservative_buy_price(self, symbol: str) -> float | None:
        """Get conservative buy pricing for better fills."""
        return self.pricing_handler.get_conservative_buy_price(symbol)

    def wait_for_order_completion(
        self,
        order_ids: list[str],
        max_wait_seconds: int = 60,
    ) -> WebSocketResultDTO:
        """Wait for orders to reach a final state."""
        return self.order_monitor.wait_for_order_completion(order_ids, max_wait_seconds)

    def _prepare_websocket_connection(self) -> bool:
        """Pre-initialize WebSocket connection and wait for it to be ready.

        Returns:
            True if WebSocket is ready, False if it failed to connect

        """
        return self.websocket_manager.prepare_websocket_connection()

    def _cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        self.websocket_manager.cleanup_websocket_connection()

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order details by order ID from the trading client.

        Args:
            order_id: The order ID to lookup

        Returns:
            Order object from Alpaca API, or None if not found

        """
        try:
            return self.trading_client.get_order_by_id(order_id)
        except Exception as e:
            logging.warning(f"Could not retrieve order {order_id}: {e}")
            return None

    # _delegate_to_canonical_executor removed - canonical execution happens outside this client.
