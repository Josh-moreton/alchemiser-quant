#!/usr/bin/env python3
"""Alpaca Client for Direct API Access.

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
    Basic usage for order placement:

    >>> client = AlpacaClient(trading_client, data_provider)
    >>> positions = client.get_current_positions()
    >>> order_id = client.place_market_order('AAPL', OrderSide.BUY, qty=10)
"""

import logging
import time
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import (
        DataProvider as ExecDataProvider,
    )
    from the_alchemiser.interfaces.schemas.orders import ValidatedOrderDTO

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.smart_pricing_handler import SmartPricingHandler
from the_alchemiser.application.orders.asset_order_handler import AssetOrderHandler
from the_alchemiser.application.orders.limit_order_handler import LimitOrderHandler
from the_alchemiser.application.orders.order_validation_utils import (
    validate_notional,
    validate_order_parameters,
    validate_quantity,
)
from the_alchemiser.infrastructure.websocket.websocket_connection_manager import (
    WebSocketConnectionManager,
)
from the_alchemiser.infrastructure.websocket.websocket_order_monitor import OrderCompletionMonitor
from the_alchemiser.services.errors.exceptions import TradingClientError
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
        data_provider: "ExecDataProvider",
        validate_buying_power: bool = False,
    ):
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
        self.limit_order_handler = LimitOrderHandler(
            self.trading_client, self.position_manager, self.asset_handler
        )
        self.pricing_handler = SmartPricingHandler(data_provider)
        self.websocket_manager = WebSocketConnectionManager(self.trading_client)

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions from Alpaca.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.
        """
        return self.position_manager.get_current_positions()

    def get_pending_orders_validated(self) -> list["ValidatedOrderDTO"]:
        """
        Get all pending orders from Alpaca with type safety.

        Returns:
            List of ValidatedOrderDTO instances for type-safe order handling.
        """
        try:
            from the_alchemiser.application.mapping.orders import (
                dict_to_order_request_dto,
                order_request_to_validated_dto,
            )
            from the_alchemiser.interfaces.schemas.orders import ValidatedOrderDTO

            raw_orders = self.position_manager.get_pending_orders()

            validated_orders: list[ValidatedOrderDTO] = []
            for order_dict in raw_orders.values():  # Iterate over values, not keys
                try:
                    # Convert dict to OrderRequestDTO first, then to ValidatedOrderDTO
                    order_request = dict_to_order_request_dto(order_dict)
                    validated_order = order_request_to_validated_dto(
                        request=order_request,
                        estimated_value=None,  # Will be calculated if needed
                        is_fractional=False,
                        normalized_quantity=order_request.quantity,
                    # Calculate estimated_value (price * quantity if available)
                    estimated_value = None
                    if hasattr(order_request, "price") and order_request.price is not None:
                        estimated_value = order_request.price * order_request.quantity
                    # Determine if asset is fractional using AssetOrderHandler
                    is_fractional = False
                    try:
                        is_fractional = AssetOrderHandler.is_fractionable(order_request.symbol)
                    except Exception:
                        is_fractional = False
                    # Calculate risk_score if a utility is available, else set to None
                    risk_score = None
                    validated_order = order_request_to_validated_dto(
                        request=order_request,
                        estimated_value=estimated_value,
                        is_fractional=is_fractional,
                        normalized_quantity=order_request.quantity,
                        risk_score=risk_score,
                    )
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
        """
        Cancel all pending orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol

        Returns:
            True if successful, False otherwise
        """
        if symbol:
            return self.position_manager.cancel_symbol_orders(symbol)
        else:
            return self.position_manager.cancel_all_orders()

    def liquidate_position(self, symbol: str) -> str | None:
        """
        Liquidate entire position using Alpaca's close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed
        """
        # Cancel any pending orders for this symbol first
        self.cancel_all_orders(symbol)
        time.sleep(0.5)  # Brief pause for cancellations to process

        return self.position_manager.execute_liquidation(symbol)

    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        qty: float | None = None,
        notional: float | None = None,
        cancel_existing: bool = True,
    ) -> str | None:
        """
        Place a simple market order using helper modules for validation and asset handling.

        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            qty: Quantity to trade (use either qty OR notional, not both)
            notional: Dollar amount to trade (use either qty OR notional, not both)
            cancel_existing: Whether to cancel existing orders for this symbol first

        Returns:
            Order ID if successful, None if failed
        """
        # Validate parameters
        is_valid, error_msg = validate_order_parameters(symbol, qty, notional)
        if not is_valid:
            logging.warning(error_msg)
            return None

        # Validate and normalize qty/notional
        if qty is not None:
            qty = validate_quantity(qty, symbol)
            if qty is None:
                return None

        if notional is not None:
            notional = validate_notional(notional, symbol)
            if notional is None:
                return None

        try:
            # Cancel existing orders if requested
            if cancel_existing:
                self.cancel_all_orders(symbol)
                time.sleep(0.5)  # Brief pause for cancellations to process

            # For buy orders, validate buying power (if enabled)
            if side == OrderSide.BUY and self.validate_buying_power and qty is not None:
                is_sufficient, warning_msg = self.position_manager.validate_buying_power(
                    symbol, qty
                )
                if not is_sufficient:
                    logging.warning(warning_msg)
                    return None
                elif warning_msg:
                    logging.warning(warning_msg)

            # For sell orders, validate and adjust quantity
            if side == OrderSide.SELL and qty is not None:
                is_valid, adjusted_qty, warning_msg = self.position_manager.validate_sell_position(
                    symbol, qty
                )
                if not is_valid:
                    logging.warning(warning_msg)
                    return None
                if warning_msg:
                    logging.warning(warning_msg)
                qty = adjusted_qty

            # For notional sell orders, basic position check
            if side == OrderSide.SELL and notional is not None:
                positions = self.get_current_positions()
                if positions.get(symbol, 0) <= 0:
                    logging.warning(f"No position to sell for {symbol}")
                    return None

            # Prepare order using asset handler
            market_order_data, conversion_info = self.asset_handler.prepare_market_order(
                symbol, side, qty, notional
            )

            if market_order_data is None:
                logging.warning(f"Failed to prepare market order for {symbol}")
                return None

            if conversion_info:
                logging.info(f"Order conversion: {conversion_info}")

            # Submit the order with error handling for non-fractionable assets
            try:
                order = self.trading_client.submit_order(market_order_data)
                order_id = str(getattr(order, "id", "unknown"))

                logging.info(f"Market order placed for {symbol}: {order_id}")
                return order_id

            except (TradingClientError, ValueError, AttributeError) as order_error:
                # Sonar: consolidate exception handling
                error_msg = str(order_error)

                if "insufficient buying power" in error_msg.lower():
                    logging.error(f"❌ Insufficient buying power for {symbol}: {error_msg}")
                    try:
                        import json

                        if hasattr(order_error, "text"):
                            error_data = json.loads(order_error.text)
                        else:
                            error_data = json.loads(error_msg.split('{"')[1].split("}")[0] + "}")
                        actual_buying_power = error_data.get("buying_power", "unknown")
                        cost_basis = error_data.get("cost_basis", "unknown")
                        logging.error(
                            f"❌ Order cost: ${cost_basis}, Available buying power: ${actual_buying_power}"
                        )
                    except Exception:
                        logging.error("❌ Could not parse buying power details from error")
                    return None

                if "not fractionable" in error_msg.lower() and qty is not None:
                    fallback_order, conversion_info = (
                        self.asset_handler.handle_fractionability_error(
                            symbol, side, qty, error_msg
                        )
                    )

                    if fallback_order is None:
                        logging.error(f"❌ Fallback failed: {conversion_info}")
                        return None

                    logging.info(f"🔄 {conversion_info}")

                    try:
                        order = self.trading_client.submit_order(fallback_order)
                        order_id = str(getattr(order, "id", "unknown"))

                        logging.info(f"✅ Fallback order placed for {symbol}: {order_id}")
                        return order_id

                    except (TradingClientError, ConnectionError, TimeoutError) as fallback_error:
                        logging.error(
                            f"❌ Fallback order also failed for {symbol}: {fallback_error}"
                        )
                        return None

                raise

        except (ConnectionError, TimeoutError, OSError) as e:
            logging.error(f"Network error placing market order for {symbol}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error placing market order for {symbol}: {e}")
            return None

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        limit_price: float,
        cancel_existing: bool = True,
    ) -> str | None:
        """
        Place a limit order using the specialized limit order handler.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: OrderSide.BUY or OrderSide.SELL
            limit_price: Limit price for the order
            cancel_existing: Whether to cancel existing orders for this symbol first

        Returns:
            Order ID if successful, None if failed
        """
        return self.limit_order_handler.place_limit_order(
            symbol, qty, side, limit_price, cancel_existing
        )

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """
        Smart sell order that uses liquidation API for full position sells.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed
        """
        positions = self.get_current_positions()
        available = positions.get(symbol, 0)

        if available <= 0:
            logging.warning(f"No position to sell for {symbol}")
            return None

        # If selling 99%+ of position, use liquidation API
        if qty >= available * 0.99:
            logging.info(
                f"Selling {qty}/{available} shares ({qty/available:.1%}) - using liquidation API"
            )
            return self.liquidate_position(symbol)
        else:
            logging.info(
                f"Selling {qty}/{available} shares ({qty/available:.1%}) - using market order"
            )
            return self.place_market_order(symbol, OrderSide.SELL, qty=qty)

    def get_smart_limit_price(
        self, symbol: str, side: OrderSide, aggressiveness: float = 0.5
    ) -> float | None:
        """
        Get a smart limit price based on current bid/ask.

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
    ) -> dict[str, str]:
        """Wait for orders to reach a final state."""
        return self.order_monitor.wait_for_order_completion(order_ids, max_wait_seconds)

    def _prepare_websocket_connection(self) -> bool:
        """
        Pre-initialize WebSocket connection and wait for it to be ready.

        Returns:
            True if WebSocket is ready, False if it failed to connect
        """
        return self.websocket_manager.prepare_websocket_connection()

    def _cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        self.websocket_manager.cleanup_websocket_connection()

    def get_order_by_id(self, order_id: str) -> Any:
        """
        Get order details by order ID from the trading client.

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
