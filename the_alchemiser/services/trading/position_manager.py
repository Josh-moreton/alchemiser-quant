#!/usr/bin/env python3
"""Position Management Utilities.

This module provides helper functions for position management operations,
including position validation, liquidation logic, and buying power checks.
"""

import logging
from typing import Any

from the_alchemiser.infrastructure.logging.logging_utils import get_logger, log_error_with_context
from the_alchemiser.services.errors.exceptions import DataProviderError, TradingClientError


class PositionManager:
    """Handles position management operations including validation and liquidation."""

    def __init__(self, trading_client: Any, data_provider: Any) -> None:
        """Initialize with trading client and data provider."""
        self.trading_client = trading_client
        self.data_provider = data_provider
        self.logger = get_logger(__name__)

    def get_current_positions(self, force_refresh: bool = False) -> dict[str, float]:
        """Get all current positions from Alpaca.

        Args:
            force_refresh: If True, forces fresh data from broker (no cache)

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        try:
            # TODO: Implement actual cache invalidation when force_refresh=True
            # For now, all calls get fresh data
            positions = self.trading_client.get_all_positions()
            return {
                str(getattr(pos, "symbol", "")): float(getattr(pos, "qty", 0))
                for pos in positions
                if float(getattr(pos, "qty", 0)) != 0
            }
        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Failed to get current positions: {e}"),
                "position_retrieval",
                function="get_current_positions",
                error_type=type(e).__name__,
            )
            logging.error(f"Error getting positions: {e}")
            return {}
        except (TradingClientError, DataProviderError, ConnectionError, TimeoutError, OSError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Unexpected error getting positions: {e}"),
                "position_retrieval",
                function="get_current_positions",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error getting positions: {e}")
            return {}

    def validate_sell_position(
        self, symbol: str, requested_qty: float, force_refresh: bool = True
    ) -> tuple[bool, float, str | None]:
        """Validate and adjust sell quantity based on available position.

        Args:
            symbol: Symbol to sell
            requested_qty: Requested quantity to sell
            force_refresh: If True, forces fresh position data from broker

        Returns:
            Tuple of (is_valid, adjusted_qty, warning_message)

        """
        # Force refresh from broker for critical sell operations
        positions = self.get_current_positions(force_refresh=force_refresh)
        available = positions.get(symbol, 0)

        if available <= 0:
            return False, 0.0, f"No position to sell for {symbol}"

        # Smart quantity adjustment - sell only what's actually available
        if requested_qty > available:
            warning_msg = f"Adjusting sell quantity for {symbol}: {requested_qty} -> {available}"
            return True, available, warning_msg

        return True, requested_qty, None

    def should_use_liquidation_api(self, symbol: str, requested_qty: float) -> bool:
        """Determine if liquidation API should be used instead of regular sell order.

        Args:
            symbol: Symbol to sell
            requested_qty: Requested quantity to sell

        Returns:
            True if liquidation API should be used

        """
        positions = self.get_current_positions()
        available = positions.get(symbol, 0)

        if available <= 0:
            return False

        # Use liquidation API for selling 99%+ of position
        return requested_qty >= available * 0.99

    def validate_buying_power(self, symbol: str, qty: float) -> tuple[bool, str | None]:
        """Validate buying power for a purchase.

        Args:
            symbol: Symbol to buy
            qty: Quantity to buy

        Returns:
            Tuple of (is_sufficient, warning_message)

        """
        try:
            account = self.trading_client.get_account()
            buying_power = float(getattr(account, "buying_power", 0) or 0)
            current_price = self.data_provider.get_current_price(symbol)

            if current_price is not None and current_price > 0:
                price_value = float(current_price)
                qty_value = float(qty)
                order_value = qty_value * price_value

                if order_value > buying_power:
                    warning_msg = (
                        f"Order value ${order_value:.2f} exceeds "
                        f"buying power ${buying_power:.2f} for {symbol}"
                    )
                    return False, warning_msg

            return True, None

        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Failed to validate buying power for {symbol}: {e}"),
                "buying_power_validation",
                function="validate_buying_power",
                symbol=symbol,
                quantity=qty,
                error_type=type(e).__name__,
            )
            warning_msg = f"Unable to validate buying power for {symbol}: {e}"
            return True, warning_msg  # Continue with order despite validation error
        except DataProviderError as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "buying_power_validation",
                function="validate_buying_power",
                symbol=symbol,
                quantity=qty,
                error_type=type(e).__name__,
            )
            warning_msg = f"Data provider error validating buying power for {symbol}: {e}"
            return True, warning_msg  # Continue with order despite validation error
        except (TradingClientError, ConnectionError, TimeoutError, OSError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Unexpected error validating buying power for {symbol}: {e}"),
                "buying_power_validation",
                function="validate_buying_power",
                symbol=symbol,
                quantity=qty,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            warning_msg = f"Unexpected error validating buying power for {symbol}: {e}"
            return True, warning_msg  # Continue with order despite validation error

    def execute_liquidation(self, symbol: str) -> str | None:
        """Execute position liquidation using Alpaca's close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed

        """
        try:
            # Verify position exists
            positions = self.get_current_positions(
                force_refresh=True
            )  # Force fresh data for liquidation
            if symbol not in positions or positions[symbol] <= 0:
                logging.warning(f"No position to liquidate for {symbol}")
                return None

            logging.info(f"Liquidating entire position for {symbol} ({positions[symbol]} shares)")

            # Use Alpaca's liquidation API
            response = self.trading_client.close_position(symbol)

            if response:
                order_id = str(getattr(response, "id", "unknown"))
                logging.info(f"Position liquidation order placed for {symbol}: {order_id}")
                return order_id
            logging.error(f"Failed to liquidate position for {symbol}: No response")
            return None

        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Failed to liquidate position for {symbol}: {e}"),
                "position_liquidation",
                function="execute_liquidation",
                symbol=symbol,
                error_type=type(e).__name__,
            )
            logging.error(f"Exception liquidating position for {symbol}: {e}")
            return None
        except (TradingClientError, DataProviderError, ConnectionError, TimeoutError, OSError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Unexpected error liquidating position for {symbol}: {e}"),
                "position_liquidation",
                function="execute_liquidation",
                symbol=symbol,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected exception liquidating position for {symbol}: {e}")
            return None

    def get_pending_orders(self) -> dict[str, dict[str, Any]]:
        """Get pending orders with proper null value handling."""
        try:
            orders = self.trading_client.get_orders()
            pending_orders = {}

            for order in orders:
                # Safe attribute extraction with proper null handling
                qty_raw = getattr(order, "qty", None)
                if qty_raw is None:
                    qty = 0.0
                else:
                    try:
                        qty = float(qty_raw)
                    except (ValueError, TypeError):
                        qty = 0.0

                filled_qty_raw = getattr(order, "filled_qty", None)
                if filled_qty_raw is None:
                    filled_qty = 0.0
                else:
                    try:
                        filled_qty = float(filled_qty_raw)
                    except (ValueError, TypeError):
                        filled_qty = 0.0

                limit_price_raw = getattr(order, "limit_price", None)
                if limit_price_raw is None:
                    limit_price = None
                else:
                    try:
                        limit_price = float(limit_price_raw) if limit_price_raw else None
                    except (ValueError, TypeError):
                        limit_price = None

                pending_orders[str(order.id)] = {
                    "id": str(order.id),
                    "symbol": getattr(order, "symbol", ""),
                    "qty": qty,
                    "filled_qty": filled_qty,
                    "side": str(getattr(order, "side", "")),
                    "status": str(getattr(order, "status", "")),
                    "order_type": str(getattr(order, "order_type", "")),
                    "limit_price": limit_price,
                    "time_in_force": str(getattr(order, "time_in_force", "")),
                    "created_at": str(getattr(order, "created_at", "")),
                    "updated_at": str(getattr(order, "updated_at", "")),
                }

            return pending_orders

        except Exception as e:
            error_context = {
                "function": "get_pending_orders",
                "trading_client": type(self.trading_client).__name__,
                "error_type": type(e).__name__,
            }

            self.logger.error(
                f"Error in pending_orders_retrieval: Failed to get pending orders: {e}",
                extra=error_context,
            )
            self.logger.error(
                "Full traceback for pending_orders_retrieval error:",
                extra=error_context,
                exc_info=True,
            )

            raise TradingClientError(f"Failed to get pending orders: {e}") from e

    def cancel_symbol_orders(self, symbol: str) -> bool:
        """Cancel all pending orders for a specific symbol.

        Args:
            symbol: Symbol to cancel orders for

        Returns:
            True if successful, False otherwise

        """
        try:
            orders_dict = self.get_pending_orders()
            orders = list(orders_dict.values())  # Convert dict values to list
            symbol_orders = [o for o in orders if o["symbol"] == symbol]

            for order in symbol_orders:
                try:
                    self.trading_client.cancel_order_by_id(order["id"])
                    logging.info(f"Cancelled order {order['id']} for {symbol}")
                except (AttributeError, ValueError, TypeError) as e:
                    logger = get_logger(__name__)
                    log_error_with_context(
                        logger,
                        TradingClientError(
                            f"Failed to cancel order {order['id']} for {symbol}: {e}"
                        ),
                        "order_cancellation",
                        function="cancel_symbol_orders",
                        symbol=symbol,
                        order_id=order["id"],
                        error_type=type(e).__name__,
                    )
                    logging.warning(f"Could not cancel order {order['id']}: {e}")
                except (
                    TradingClientError,
                    DataProviderError,
                    ConnectionError,
                    TimeoutError,
                    OSError,
                ) as e:
                    logger = get_logger(__name__)
                    log_error_with_context(
                        logger,
                        TradingClientError(
                            f"Unexpected error cancelling order {order['id']} for {symbol}: {e}"
                        ),
                        "order_cancellation",
                        function="cancel_symbol_orders",
                        symbol=symbol,
                        order_id=order["id"],
                        error_type="unexpected_error",
                        original_error=type(e).__name__,
                    )
                    logging.warning(f"Unexpected error cancelling order {order['id']}: {e}")

            return True
        except (TradingClientError, DataProviderError, ConnectionError, TimeoutError, OSError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Unexpected error cancelling orders for {symbol}: {e}"),
                "symbol_orders_cancellation",
                function="cancel_symbol_orders",
                symbol=symbol,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error cancelling orders for {symbol}: {e}")
            return False

    def cancel_all_orders(self) -> bool:
        """Cancel all pending orders.

        Returns:
            True if successful, False otherwise

        """
        try:
            self.trading_client.cancel_orders()
            logging.info("Cancelled all pending orders")
            return True
        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Failed to cancel all orders: {e}"),
                "all_orders_cancellation",
                function="cancel_all_orders",
                error_type=type(e).__name__,
            )
            logging.error(f"Error cancelling all orders: {e}")
            return False
        except (TradingClientError, DataProviderError, ConnectionError, TimeoutError, OSError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                TradingClientError(f"Unexpected error cancelling all orders: {e}"),
                "all_orders_cancellation",
                function="cancel_all_orders",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error cancelling all orders: {e}")
            return False

    def reconcile_position_after_order(self, order_id: str, symbol: str) -> bool:
        """Force position reconciliation after order execution.

        Args:
            order_id: The order ID that was executed
            symbol: Symbol to reconcile

        Returns:
            True if reconciliation successful, False otherwise

        """
        try:
            logging.info(f"Reconciling position for {symbol} after order {order_id}")

            # Force fresh position data from broker
            self.get_current_positions(force_refresh=True)

            # Get order details to understand what should have happened
            try:
                order = self.trading_client.get_order_by_id(order_id)
                order_status = str(getattr(order, "status", "unknown")).lower()

                if "filled" in order_status:
                    logging.info(
                        f"Order {order_id} for {symbol} confirmed filled - position reconciled"
                    )
                else:
                    logging.warning(f"Order {order_id} for {symbol} status: {order_status}")

            except Exception as e:
                logging.warning(f"Could not get order details for reconciliation: {e}")

            return True

        except Exception as e:
            logging.error(f"Failed to reconcile position for {symbol} after order {order_id}: {e}")
            return False

    def detect_position_drift(self, tolerance: float = 100.0) -> list[dict[str, Any]]:
        """Detect drift between internal and broker positions.

        Args:
            tolerance: Dollar threshold for drift alerts

        Returns:
            List of position drift warnings

        """
        try:
            # Force fresh broker positions
            broker_positions = self.get_current_positions(force_refresh=True)

            drift_alerts = []

            for symbol, qty in broker_positions.items():
                # Get current market value
                try:
                    positions = self.trading_client.get_all_positions()
                    pos = next(
                        (p for p in positions if str(getattr(p, "symbol", "")) == symbol), None
                    )
                    if pos:
                        market_value = float(getattr(pos, "market_value", 0))
                        if abs(market_value) > tolerance:
                            drift_alerts.append(
                                {
                                    "symbol": symbol,
                                    "qty": qty,
                                    "market_value": market_value,
                                    "message": f"Position {symbol}: ${market_value:.2f} (threshold: ${tolerance})",
                                }
                            )
                except Exception:
                    pass

            if drift_alerts:
                logging.warning(f"Detected {len(drift_alerts)} position drift alerts")

            return drift_alerts

        except Exception as e:
            logging.error(f"Failed to detect position drift: {e}")
            return []
