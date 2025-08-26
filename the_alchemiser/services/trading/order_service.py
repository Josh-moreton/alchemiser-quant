"""Enhanced Order Service.

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

import logging
from decimal import Decimal
from enum import Enum

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest

from the_alchemiser.domain.interfaces import MarketDataRepository, TradingRepository
from the_alchemiser.services.errors.decorators import translate_trading_errors
from the_alchemiser.utils.num import floats_equal

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration for type safety."""

    MARKET = "market"
    LIMIT = "limit"


class OrderValidationError(Exception):
    """Exception raised when order validation fails."""


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

    @translate_trading_errors()
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float | None = None,
        notional: float | None = None,
        validate_price: bool = True,
    ) -> str:
        """Place a validated market order.

        Args:
            symbol: Stock symbol (will be normalized)
            side: "buy" or "sell" (case insensitive)
            quantity: Number of shares to trade
            notional: Dollar amount to trade (alternative to quantity)
            validate_price: Whether to validate current price before ordering

        Returns:
            Order ID from successful order placement

        Raises:
            OrderValidationError: If validation fails
            Exception: If order placement fails

        """
        # Input validation and normalization
        symbol = self._validate_and_normalize_symbol(symbol)
        side = self._validate_and_normalize_side(side)

        # Validate quantity or notional
        if quantity is not None and notional is not None:
            raise OrderValidationError("Cannot specify both quantity and notional")

        if quantity is None and notional is None:
            raise OrderValidationError("Must specify either quantity or notional")

        if quantity is not None:
            quantity = self._validate_quantity(quantity)

        if notional is not None:
            notional = self._validate_notional(notional)

        # Optional price validation
        if validate_price and self._market_data:
            self._validate_market_price(symbol)

        # Position validation for sell orders
        if side == "sell":
            self._validate_sell_position(symbol, quantity, notional)

        # Place the order through repository
        logger.info(
            f"Placing market {side} order for {symbol}: qty={quantity}, notional=${notional}"
        )

        order_result = self._trading.place_market_order(
            symbol=symbol, side=side, qty=quantity, notional=notional
        )

        if not order_result.success:
            raise Exception(f"Order placement failed: {order_result.error}")

        logger.info(f"✅ Market order placed successfully: {order_result.order_id}")
        return order_result.order_id

    @translate_trading_errors()
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
        validate_price: bool = True,
    ) -> str:
        """Place a validated limit order.

        Args:
            symbol: Stock symbol (will be normalized)
            side: "buy" or "sell" (case insensitive)
            quantity: Number of shares to trade
            limit_price: Limit price for the order
            time_in_force: Time in force ("day", "gtc", "ioc", "fok")
            validate_price: Whether to validate limit price against current market

        Returns:
            Order ID from successful order placement

        Raises:
            OrderValidationError: If validation fails
            Exception: If order placement fails

        """
        # Input validation and normalization
        symbol = self._validate_and_normalize_symbol(symbol)
        side = self._validate_and_normalize_side(side)
        quantity = self._validate_quantity(quantity)
        limit_price = self._validate_price(limit_price)
        tif = self._validate_time_in_force(time_in_force)

        # Price reasonableness check
        if validate_price and self._market_data:
            self._validate_limit_price(symbol, side, limit_price)

        # Position validation for sell orders
        if side == "sell":
            self._validate_sell_position(symbol, quantity, None)

        # Create and place limit order
        logger.info(
            f"Placing limit {side} order for {symbol}: "
            f"qty={quantity}, price=${limit_price:.2f}, tif={tif}"
        )

        # Create Alpaca limit order request
        order_request = LimitOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=tif,
            limit_price=limit_price,
        )

        order_result = self._trading.place_order(order_request)

        if not order_result:
            raise Exception("Limit order placement returned None - failed")

        # Extract order ID
        order_id = str(getattr(order_result, "id", order_result))

        logger.info(f"✅ Limit order placed successfully: {order_id}")
        return order_id

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
            raise Exception("Position liquidation returned None - failed")

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

    def _validate_limit_price(self, symbol: str, side: str, limit_price: float) -> None:
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

    def _validate_sell_position(
        self, symbol: str, quantity: float | None, notional: float | None
    ) -> None:
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
