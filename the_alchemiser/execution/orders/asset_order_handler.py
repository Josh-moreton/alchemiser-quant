#!/usr/bin/env python3
"""Business Unit: execution; Status: current.

Asset-Specific Order Logic.

This module handles asset-specific order placement logic, including
fractionable vs non-fractionable asset handling, order type conversion,
and fallback strategies.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.execution.orders.order_schemas import ValidatedOrderDTO

from the_alchemiser.shared.logging.logging_utils import get_logger, log_error_with_context
from the_alchemiser.shared.math.asset_info import fractionability_detector


# Define DataProviderError locally to avoid circular import
class DataProviderError(Exception):
    """Data provider error exception."""



class AssetOrderHandler:
    """Handles asset-specific order logic including fractionability and conversions."""

    def __init__(self, data_provider: Any) -> None:
        """Initialize with data provider for price fetching."""
        self.data_provider = data_provider

    def prepare_market_order(
        self,
        symbol: str,
        side: Any,  # BrokerOrderSide or compatible
        qty: float | None = None,
        notional: float | None = None,
    ) -> tuple[Any | None, str | None]:  # Returns broker request
        """Prepare a market order request with smart asset handling.

        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            qty: Quantity (if using quantity-based order)
            notional: Dollar amount (if using notional order)

        Returns:
            Tuple of (MarketOrderRequest, conversion_info) or (None, error_message)

        """
        if qty is not None:
            return self._prepare_quantity_order(symbol, side, qty)
        if notional is not None:
            return self._prepare_notional_order(symbol, side, notional)
        return None, "Must provide either qty or notional"

    def prepare_market_order_from_dto(
        self, validated_order: ValidatedOrderDTO
    ) -> tuple[MarketOrderRequest | None, str | None]:
        """Prepare a market order request from ValidatedOrderDTO.

        Args:
            validated_order: ValidatedOrderDTO instance with validation metadata

        Returns:
            Tuple of (MarketOrderRequest, conversion_info) or (None, error_message)

        """
        # Convert DTO side to OrderSide enum
        order_side = OrderSide.BUY if validated_order.side.lower() == "buy" else OrderSide.SELL

        # Use the normalized quantity from validation
        quantity = float(validated_order.normalized_quantity or validated_order.quantity)

        # Prepare the order using existing quantity-based logic
        return self._prepare_quantity_order(validated_order.symbol, order_side, quantity)

    def _prepare_quantity_order(
        self, symbol: str, side: OrderSide, qty: float
    ) -> tuple[MarketOrderRequest | None, str | None]:
        """Prepare quantity-based market order with smart conversion logic."""
        # Get current price for potential conversion
        current_price = None
        try:
            current_price = self.data_provider.get_current_price(symbol)
        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Failed to get current price for {symbol}: {e}"),
                "price_retrieval_for_order",
                function="_prepare_quantity_order",
                symbol=symbol,
                quantity=qty,
                error_type=type(e).__name__,
            )
            logging.warning(f"Could not get current price for {symbol}: {e}")
        except Exception as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Unexpected error getting current price for {symbol}: {e}"),
                "price_retrieval_for_order",
                function="_prepare_quantity_order",
                symbol=symbol,
                quantity=qty,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.warning(f"Unexpected error getting current price for {symbol}: {e}")

        # Check if we should use notional orders for non-fractionable assets
        if (
            current_price
            and current_price > 0
            and side == OrderSide.BUY
            and fractionability_detector.should_use_notional_order(symbol, qty)
        ):
            # Convert to notional order for better handling of non-fractionable assets
            original_notional = qty * current_price
            logging.info(
                f"🔄 Converting {symbol} from qty={qty} to notional=${original_notional:.2f} "
                f"(likely non-fractionable asset)"
            )

            market_order_data = MarketOrderRequest(
                symbol=symbol,
                notional=round(original_notional, 2),
                side=side,
                time_in_force=TimeInForce.DAY,
            )

            conversion_info = f"Converted from qty={qty} to notional=${original_notional:.2f}"
            return market_order_data, conversion_info
        # Regular quantity order with fractional rounding
        qty = float(Decimal(str(qty)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN))

        if qty <= 0:
            return None, f"Quantity rounded to zero for {symbol}"

        market_order_data = MarketOrderRequest(
            symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY
        )

        return market_order_data, None

    def _prepare_notional_order(
        self, symbol: str, side: OrderSide, notional: float
    ) -> tuple[MarketOrderRequest | None, str | None]:
        """Prepare notional-based market order."""
        notional = round(notional, 2)  # Round to cents

        market_order_data = MarketOrderRequest(
            symbol=symbol, notional=notional, side=side, time_in_force=TimeInForce.DAY
        )

        return market_order_data, None

    def prepare_limit_order_quantity(
        self, symbol: str, qty: float, limit_price: float
    ) -> tuple[float, bool]:
        """Prepare quantity for limit order with asset-specific handling.

        Args:
            symbol: Stock symbol
            qty: Original quantity
            limit_price: Limit price

        Returns:
            Tuple of (adjusted_qty, was_converted)

        """
        original_qty = qty
        was_converted = False

        # For non-fractionable assets, convert to whole shares
        if not fractionability_detector.is_fractionable(symbol):
            adjusted_qty, was_rounded = fractionability_detector.convert_to_whole_shares(
                symbol, qty, limit_price
            )

            if was_rounded:
                qty = adjusted_qty
                was_converted = True

                if qty <= 0:
                    logging.warning(
                        f"❌ {symbol} quantity rounded to zero whole shares (original: {original_qty})"
                    )
                    return 0.0, True

                logging.info(
                    f"🔄 Rounded {symbol} to {qty} whole shares for non-fractionable asset"
                )
        else:
            # Round quantity for regular assets
            qty = float(Decimal(str(qty)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN))

        return qty, was_converted
