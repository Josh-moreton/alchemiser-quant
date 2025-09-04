"""Business Unit: execution; Status: current.

Enhanced Order Service.

This service provides type-safe, validated order placement operations.
It builds on top of the TradingRepository interface, adding:
- Input validation and sanitization
- Business rule enforcement
- Enhanced error handling
- Type safety throughout
- Logging and monitoring

This represents the service layer from our eventual architecture vision,
providing business logic while depending on domain interfaces.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from enum import Enum

from alpaca.trading.enums import TimeInForce

from the_alchemiser.shared.math.num import floats_equal
from the_alchemiser.shared.protocols.repository import (
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.shared.utils.decorators import translate_trading_errors

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration for type safety."""

    MARKET = "market"
    LIMIT = "limit"


class OrderValidationError(Exception):
    """Exception raised when order validation fails."""


class OrderOperationError(Exception):
    """Exception raised when an order operation (e.g. liquidation) fails."""


class OrderService:
    """Enhanced order service with validation and business logic.

    This service provides a higher-level interface for order operations,
    adding validation, error handling, and business rules on top of the
    basic trading repository operations.
    """

    def __init__(
        self,
        trading_repo: TradingRepository,
        market_data_repo: MarketDataRepository | None = None,
        max_order_value: float = 100000.0,
        min_order_value: float = 1.0,
    ) -> None:
        """Initialize the order service.

        Args:
            trading_repo: Trading repository for order operations
            market_data_repo: Optional market data repository for price validation
            max_order_value: Maximum allowed order value in dollars
            min_order_value: Minimum allowed order value in dollars

        """
        self._trading = trading_repo
        self._market_data = market_data_repo
        self._max_order_value = max_order_value
        self._min_order_value = min_order_value

    # Legacy place_market_order / place_limit_order removed. Use CanonicalOrderExecutor externally.

    @translate_trading_errors()
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order with enhanced error handling.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful

        Raises:
            OrderValidationError: If order_id is invalid
            Exception: If cancellation fails

        """
        if not order_id or not isinstance(order_id, str):
            raise OrderValidationError("Invalid order ID")

        logger.info(f"Cancelling order: {order_id}")
        result = self._trading.cancel_order(order_id)

        if result:
            logger.info(f"✅ Order cancelled successfully: {order_id}")
        else:
            logger.warning(f"⚠️ Order cancellation returned False: {order_id}")

        return result

    @translate_trading_errors()
    def liquidate_position(self, symbol: str) -> str:
        """Liquidate entire position with validation.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID from liquidation order

        Raises:
            OrderValidationError: If symbol invalid or no position
            Exception: If liquidation fails

        """
        symbol = self._validate_and_normalize_symbol(symbol)

        # Verify position exists
        positions = self._trading.get_positions_dict()
        if symbol not in positions or floats_equal(positions[symbol], 0.0):
            raise OrderValidationError(f"No position to liquidate for {symbol}")

        position_size = positions[symbol]
        logger.info(f"Liquidating position: {symbol} ({position_size} shares)")

        order_id = self._trading.liquidate_position(symbol)

        if not order_id:
            raise OrderOperationError("Position liquidation returned None - failed")

        logger.info(f"✅ Position liquidated successfully: {order_id}")
        return order_id

    # Private validation methods

    def _validate_and_normalize_symbol(self, symbol: str) -> str:
        """Validate and normalize stock symbol."""
        if not symbol or not isinstance(symbol, str):
            raise OrderValidationError("Symbol must be a non-empty string")

        symbol = symbol.strip().upper()

        if not symbol.isalpha() or len(symbol) > 5:
            raise OrderValidationError(f"Invalid symbol format: {symbol}")

        return symbol

    def _validate_and_normalize_side(self, side: str) -> str:
        """Validate and normalize order side."""
        if not side or not isinstance(side, str):
            raise OrderValidationError("Side must be a non-empty string")

        side = side.strip().lower()

        if side not in ["buy", "sell"]:
            raise OrderValidationError(f"Side must be 'buy' or 'sell', got: {side}")

        return side

    def _validate_quantity(self, quantity: float) -> float:
        """Validate order quantity."""
        if not isinstance(quantity, int | float | Decimal):
            raise OrderValidationError("Quantity must be a number")

        quantity = float(quantity)

        if quantity <= 0:
            raise OrderValidationError("Quantity must be positive")

        if quantity > 10000:  # Sanity check
            raise OrderValidationError(f"Quantity too large: {quantity}")

        return quantity

    def _validate_notional(self, notional: float) -> float:
        """Validate order notional value."""
        if not isinstance(notional, int | float | Decimal):
            raise OrderValidationError("Notional value must be a number")

        notional = float(notional)

        if notional < self._min_order_value:
            raise OrderValidationError(f"Notional value too small: ${notional:.2f}")

        if notional > self._max_order_value:
            raise OrderValidationError(f"Notional value too large: ${notional:.2f}")

        return notional

    def _validate_price(self, price: float) -> float:
        """Validate price value."""
        if not isinstance(price, int | float | Decimal):
            raise OrderValidationError("Price must be a number")

        price = float(price)

        if price <= 0:
            raise OrderValidationError("Price must be positive")

        if price > 1000000:  # Sanity check
            raise OrderValidationError(f"Price too large: ${price:.2f}")

        return price

    def _validate_time_in_force(self, tif: str) -> TimeInForce:
        """Validate and convert time in force."""
        if not tif or not isinstance(tif, str):
            raise OrderValidationError("Time in force must be a string")

        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
        }

        tif_lower = tif.lower()
        if tif_lower not in tif_map:
            raise OrderValidationError(f"Invalid time in force: {tif}")

        return tif_map[tif_lower]

    def _validate_market_price(self, symbol: str) -> None:
        """Validate that we can get current market price."""
        if not self._market_data:
            return  # Skip if no market data service

        try:
            price = self._market_data.get_current_price(symbol)
            if not price or price <= 0:
                raise OrderValidationError(f"Invalid market price for {symbol}: {price}")
        except Exception as e:
            raise OrderValidationError(f"Cannot validate market price for {symbol}: {e}")

    def _validate_limit_price(self, symbol: str, limit_price: float) -> None:
        """Validate limit price against current market."""
        if not self._market_data:
            return  # Skip if no market data service

        try:
            current_price = self._market_data.get_current_price(symbol)
            if not current_price:
                logger.warning(
                    f"Cannot get current price for {symbol}, skipping limit price validation"
                )
                return

            # Check for reasonable limit prices (within 10% of current price)
            price_diff_pct = abs(limit_price - current_price) / current_price

            if price_diff_pct > 0.10:  # 10% threshold
                logger.warning(
                    f"Limit price ${limit_price:.2f} is {price_diff_pct:.1%} "
                    f"from current price ${current_price:.2f} for {symbol}"
                )

        except Exception as e:
            logger.warning(f"Could not validate limit price for {symbol}: {e}")

    def _validate_sell_position(self, symbol: str, quantity: float | None) -> None:
        """Validate that we have sufficient position for sell order."""
        try:
            positions = self._trading.get_positions_dict()
            current_position = positions.get(symbol, 0.0)

            if current_position <= 0:
                raise OrderValidationError(f"No position to sell for {symbol}")

            if quantity is not None and quantity > current_position:
                raise OrderValidationError(
                    f"Insufficient position: trying to sell {quantity} but only have {current_position}"
                )

        except Exception as e:
            if isinstance(e, OrderValidationError):
                raise
            logger.warning(f"Could not validate sell position for {symbol}: {e}")
            # Don't fail the order if we can't validate position

    # _delegate_to_canonical_executor removed.


# Lifecycle Adapter Integration

from typing import Protocol

from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
from the_alchemiser.execution.monitoring.websocket_order_monitor import (
    OrderCompletionMonitor,
)
from the_alchemiser.execution.protocols.order_lifecycle import (
    OrderLifecycleMonitor,
)


class TradingClientProtocol(Protocol):  # pragma: no cover - structural typing
    """Minimal protocol for the Alpaca trading client used by the websocket monitor."""

    def get_order_by_id(self, order_id: str) -> Any:  # noqa: ANN401 - runtime library object
        """Retrieve order by ID (runtime return type from alpaca-py)."""
        ...


class WebSocketOrderLifecycleAdapter(OrderLifecycleMonitor):  # pragma: no cover - thin adapter
    """Concrete adapter implementing the lifecycle Protocol via websocket-based monitor.
    
    Adapter bridging infrastructure websocket monitor to OrderLifecycleMonitor Protocol.
    Keeps application layer decoupled from infrastructure implementation while
    reusing the existing OrderCompletionMonitor.
    """

    def __init__(
        self,
        trading_client: TradingClientProtocol,
        api_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Create adapter with provided trading client and optional explicit credentials."""
        self._monitor = OrderCompletionMonitor(
            trading_client, api_key=api_key, secret_key=secret_key
        )

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 60
    ) -> WebSocketResultDTO:
        """Delegate to underlying websocket monitor to await terminal order states."""
        return self._monitor.wait_for_order_completion(order_ids, max_wait_seconds=max_wait_seconds)
