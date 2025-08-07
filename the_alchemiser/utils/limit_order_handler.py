#!/usr/bin/env python3
"""
Limit Order Handling Utilities

This module handles limit order placement with smart fractionability logic,
validation, and error handling with fallback strategies.
"""

import logging
from decimal import ROUND_DOWN, Decimal
from typing import Any

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest

from the_alchemiser.core.error_handler import get_error_handler
from the_alchemiser.core.exceptions import DataProviderError, TradingClientError
from the_alchemiser.utils.asset_info import fractionability_detector


class LimitOrderHandler:
    """
    Handles limit order placement with smart asset-specific logic.
    """

    def __init__(self, trading_client: Any, position_manager: Any, asset_handler: Any) -> None:
        """Initialize with required dependencies."""
        self.trading_client = trading_client
        self.position_manager = position_manager
        self.asset_handler = asset_handler
        self.error_handler = get_error_handler()

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        limit_price: float,
        cancel_existing: bool = True,
    ) -> str | None:
        """
        Place a limit order with smart fractionability handling.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: OrderSide.BUY or OrderSide.SELL
            limit_price: Limit price for the order
            cancel_existing: Whether to cancel existing orders for this symbol first

        Returns:
            Order ID if successful, None if failed
        """
        # Basic validation
        if qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None

        if limit_price <= 0:
            logging.warning(f"Invalid limit price for {symbol}: {limit_price}")
            return None

        try:
            # Cancel existing orders if requested
            if cancel_existing:
                self.position_manager.cancel_symbol_orders(symbol)
                import time

                time.sleep(0.5)  # Brief pause for cancellations to process

            # For sell orders, validate we have enough to sell
            if side == OrderSide.SELL:
                is_valid, adjusted_qty, warning_msg = self.position_manager.validate_sell_position(
                    symbol, qty
                )
                if not is_valid:
                    logging.warning(warning_msg)
                    return None
                if warning_msg:
                    logging.warning(warning_msg)
                qty = adjusted_qty

            # Prepare order with asset-specific handling
            limit_order_data, conversion_info = self._prepare_limit_order(
                symbol, qty, side, limit_price
            )

            if limit_order_data is None:
                logging.warning(f"Failed to prepare limit order for {symbol}")
                return None

            if conversion_info:
                logging.info(f"Order conversion: {conversion_info}")

            # Submit order with fractionability error handling
            return self._submit_with_fallback(symbol, limit_order_data, qty, side, limit_price)

        except (TradingClientError, DataProviderError) as e:
            self.error_handler.handle_error(
                error=e,
                context="limit_order_create",
                component="LimitOrderHandler.place_limit_order",
                additional_data={
                    "symbol": symbol,
                    "quantity": qty,
                    "side": side.value,
                    "limit_price": limit_price,
                },
            )
            return None

    def _prepare_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> tuple[Any, ...]:  # TODO: Phase 7 - Migrate to LimitOrderResult
        """Prepare limit order with smart asset handling."""
        original_qty = qty
        conversion_info = None

        # Smart handling for non-fractionable assets
        if not fractionability_detector.is_fractionable(symbol):
            adjusted_qty, was_rounded = fractionability_detector.convert_to_whole_shares(
                symbol, qty, limit_price
            )

            if was_rounded:
                qty = adjusted_qty
                if qty <= 0:
                    logging.warning(
                        f"❌ {symbol} quantity rounded to zero whole shares (original: {original_qty})"
                    )
                    return None, None

                conversion_info = (
                    f"🔄 Rounded {symbol} to {qty} whole shares for non-fractionable asset"
                )
        else:
            # Round quantity for regular assets
            qty = float(Decimal(str(qty)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN))

        limit_price = round(limit_price, 2)

        if qty <= 0:
            logging.warning(f"Quantity rounded to zero for {symbol}")
            return None, None

        logging.info(
            f"Placing LIMIT {side.value} order for {symbol}: qty={qty}, price=${limit_price}"
        )

        limit_order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )

        return limit_order_data, conversion_info

    def _submit_with_fallback(
        self,
        symbol: str,
        order_data: LimitOrderRequest,
        original_qty: float,
        side: OrderSide,
        limit_price: float,
    ) -> str | None:
        """Submit order with fractionability fallback logic."""
        try:
            order = self.trading_client.submit_order(order_data)
            order_id = str(getattr(order, "id", "unknown"))

            logging.info(f"Limit order placed for {symbol}: {order_id}")
            return order_id

        except TradingClientError as order_error:
            error_msg = str(order_error)

            # Handle the specific "not fractionable" error for limit orders
            if "not fractionable" in error_msg.lower():
                return self._handle_fractionable_fallback(
                    symbol, original_qty, side, limit_price, error_msg
                )
            else:
                # Re-raise the original error if it's not a fractionability issue
                raise order_error

    def _handle_fractionable_fallback(
        self, symbol: str, original_qty: float, side: OrderSide, limit_price: float, error_msg: str
    ) -> str | None:
        """Handle fractionability errors with whole share fallback."""
        logging.warning(
            f"🔄 {symbol} limit order failed (not fractionable), trying whole shares..."
        )

        # Convert to whole shares if we haven't already
        if fractionability_detector.is_fractionable(symbol):
            whole_qty = int(original_qty)

            if whole_qty <= 0:
                logging.error(f"❌ Cannot place {symbol} order - rounds to zero whole shares")
                return None

            logging.info(f"💰 Retrying with {whole_qty} whole shares instead of {original_qty}")

            fallback_order_data = LimitOrderRequest(
                symbol=symbol,
                qty=whole_qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price,
            )

            try:
                order = self.trading_client.submit_order(fallback_order_data)
                order_id = str(getattr(order, "id", "unknown"))

                logging.info(f"✅ Fallback whole-share limit order placed for {symbol}: {order_id}")
                return order_id

            except TradingClientError as fallback_error:
                self.error_handler.handle_error(
                    error=fallback_error,
                    context="limit_order_fallback",
                    component="LimitOrderHandler._submit_with_fallback",
                    additional_data={
                        "symbol": symbol,
                        "quantity": whole_qty,
                        "side": side.value,
                        "limit_price": limit_price,
                    },
                )
                return None
        else:
            # We already tried whole shares, this is a different issue
            logging.error(f"❌ {symbol} limit order failed even with whole shares: {error_msg}")
            return None
