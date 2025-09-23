"""Business Unit: execution | Status: current.

Utility functions for smart execution strategy to reduce cognitive complexity.

This module contains extracted utility functions to help reduce the complexity
of the main strategy functions while keeping them focused and readable.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from the_alchemiser.shared.types.market_data import QuoteModel

logger = logging.getLogger(__name__)


def calculate_price_adjustment(
    original_price: Decimal, target_price: Decimal, adjustment_factor: Decimal = Decimal("0.5")
) -> Decimal:
    """Calculate price adjustment moving toward a target price.

    Args:
        original_price: Starting price
        target_price: Target price to move toward
        adjustment_factor: How much to move toward target (0.5 = 50%)

    Returns:
        New price after adjustment

    """
    adjustment = (target_price - original_price) * adjustment_factor
    return original_price + adjustment


def validate_repeg_price_with_history(
    new_price: Decimal, 
    price_history: list[Decimal] | None,
    side: str,
    quote: QuoteModel,
    min_improvement: Decimal = Decimal("0.01")
) -> Decimal:
    """Validate and adjust repeg price to avoid duplicates in history.

    Args:
        new_price: Calculated new price
        price_history: Previous prices to avoid
        side: Order side ("BUY" or "SELL")
        quote: Current market quote
        min_improvement: Minimum price improvement to enforce

    Returns:
        Validated and potentially adjusted price

    """
    if not price_history or new_price not in price_history:
        return new_price

    logger.info(
        f"🔄 Calculated repeg price ${new_price} already used for {quote.symbol} {side}, "
        f"forcing minimum improvement"
    )

    if side.upper() == "BUY":
        # For buys, increase price by minimum improvement
        adjusted_price = new_price + min_improvement
        # Don't exceed ask price
        adjusted_price = min(adjusted_price, Decimal(str(quote.ask_price)))
    else:  # SELL
        # For sells, decrease price by minimum improvement
        adjusted_price = new_price - min_improvement
        # Don't go below bid price
        adjusted_price = max(adjusted_price, Decimal(str(quote.bid_price)))

    # Re-quantize after adjustment
    adjusted_price = adjusted_price.quantize(Decimal("0.01"))

    # If we still have the same price after forced improvement, log warning
    if adjusted_price in price_history:
        logger.warning(
            f"⚠️ Unable to find unique repeg price for {quote.symbol} {side} "
            f"after forced improvement. Price ${adjusted_price} still in history: {price_history}"
        )

    return adjusted_price


def should_escalate_order(repeg_count: int, max_repegs: int) -> bool:
    """Check if order should be escalated to market order.

    Args:
        repeg_count: Current number of repegs
        max_repegs: Maximum allowed repegs

    Returns:
        True if order should be escalated

    """
    return repeg_count >= max_repegs


def should_consider_repeg(placement_time: datetime, current_time: datetime, wait_seconds: float) -> bool:
    """Check if enough time has elapsed to consider re-pegging.

    Args:
        placement_time: When the order was placed
        current_time: Current time
        wait_seconds: Minimum wait time before repeg

    Returns:
        True if order should be considered for repeg

    """
    time_elapsed = (current_time - placement_time).total_seconds()
    return time_elapsed >= wait_seconds


def is_order_completed(status: str) -> bool:
    """Check if order status indicates completion.

    Args:
        status: Order status string

    Returns:
        True if order is completed

    """
    completed_statuses = ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]
    return status in completed_statuses


def quantize_price_safely(price: Decimal) -> Decimal:
    """Safely quantize price to cent precision.

    Args:
        price: Price to quantize

    Returns:
        Price quantized to cent precision

    """
    return price.quantize(Decimal("0.01"))


def ensure_minimum_price(price: Decimal, min_price: Decimal = Decimal("0.01")) -> Decimal:
    """Ensure price meets minimum requirements.

    Args:
        price: Price to validate
        min_price: Minimum allowed price

    Returns:
        Valid price (at least min_price)

    """
    if price <= 0:
        logger.warning(f"Invalid price {price}, using minimum price {min_price}")
        return min_price
    return max(price, min_price)