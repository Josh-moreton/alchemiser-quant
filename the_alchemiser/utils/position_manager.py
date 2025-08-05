#!/usr/bin/env python3
"""
Position Management Utilities

This module provides helper functions for position management operations,
including position validation, liquidation logic, and buying power checks.
"""

import logging
from typing import Any


class PositionManager:
    """
    Handles position management operations including validation and liquidation.
    """

    def __init__(self, trading_client: Any, data_provider: Any) -> None:
        """Initialize with trading client and data provider."""
        self.trading_client = trading_client
        self.data_provider = data_provider

    def get_current_positions(self) -> dict[str, float]:
        """
        Get all current positions from Alpaca.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.
        """
        try:
            positions = self.trading_client.get_all_positions()
            return {
                str(getattr(pos, "symbol", "")): float(getattr(pos, "qty", 0))
                for pos in positions
                if float(getattr(pos, "qty", 0)) != 0
            }
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return {}

    def validate_sell_position(
        self, symbol: str, requested_qty: float
    ) -> tuple[bool, float, str | None]:
        """
        Validate and adjust sell quantity based on available position.

        Args:
            symbol: Symbol to sell
            requested_qty: Requested quantity to sell

        Returns:
            Tuple of (is_valid, adjusted_qty, warning_message)
        """
        positions = self.get_current_positions()
        available = positions.get(symbol, 0)

        if available <= 0:
            return False, 0.0, f"No position to sell for {symbol}"

        if requested_qty > available:
            warning_msg = f"Reducing sell quantity for {symbol}: {requested_qty} -> {available}"
            return True, available, warning_msg

        return True, requested_qty, None

    def should_use_liquidation_api(self, symbol: str, requested_qty: float) -> bool:
        """
        Determine if liquidation API should be used instead of regular sell order.

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
        """
        Validate buying power for a purchase.

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

        except Exception as e:
            warning_msg = f"Unable to validate buying power for {symbol}: {e}"
            return True, warning_msg  # Continue with order despite validation error

    def execute_liquidation(self, symbol: str) -> str | None:
        """
        Execute position liquidation using Alpaca's close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed
        """
        try:
            # Verify position exists
            positions = self.get_current_positions()
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
            else:
                logging.error(f"Failed to liquidate position for {symbol}: No response")
                return None

        except Exception as e:
            logging.error(f"Exception liquidating position for {symbol}: {e}")
            return None

    def get_pending_orders(self) -> list[dict[str, Any]]:
        """
        Get all pending orders from Alpaca.

        Returns:
            List of pending order information dictionaries.
        """
        try:
            orders = self.trading_client.get_orders()
            return [
                {
                    "id": str(getattr(order, "id", "")),
                    "symbol": str(getattr(order, "symbol", "")),
                    "side": str(getattr(order, "side", "")),
                    "qty": float(getattr(order, "qty", 0)),
                    "status": str(getattr(order, "status", "")),
                }
                for order in orders
            ]
        except Exception as e:
            logging.error(f"Error getting pending orders: {e}")
            return []

    def cancel_symbol_orders(self, symbol: str) -> bool:
        """
        Cancel all pending orders for a specific symbol.

        Args:
            symbol: Symbol to cancel orders for

        Returns:
            True if successful, False otherwise
        """
        try:
            orders = self.get_pending_orders()
            symbol_orders = [o for o in orders if o["symbol"] == symbol]

            for order in symbol_orders:
                try:
                    self.trading_client.cancel_order_by_id(order["id"])
                    logging.info(f"Cancelled order {order['id']} for {symbol}")
                except Exception as e:
                    logging.warning(f"Could not cancel order {order['id']}: {e}")

            return True
        except Exception as e:
            logging.error(f"Error cancelling orders for {symbol}: {e}")
            return False

    def cancel_all_orders(self) -> bool:
        """
        Cancel all pending orders.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.trading_client.cancel_orders()
            logging.info("Cancelled all pending orders")
            return True
        except Exception as e:
            logging.error(f"Error cancelling all orders: {e}")
            return False
