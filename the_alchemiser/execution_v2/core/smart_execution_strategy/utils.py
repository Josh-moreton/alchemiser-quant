"""Business Unit: execution | Status: current.

Utility functions for smart execution strategy to reduce cognitive complexity.

This module contains extracted utility functions to help reduce the complexity
of the main strategy functions while keeping them focused and readable.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import QuoteModel

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy.quotes import QuoteProvider
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)


def calculate_price_adjustment(
    original_price: Decimal,
    target_price: Decimal,
    adjustment_factor: Decimal = Decimal("0.5"),
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
    min_improvement: Decimal = Decimal("0.01"),
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
    else:  # SELL
        # For sells, decrease price by minimum improvement
        adjusted_price = new_price - min_improvement

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


def should_consider_repeg(
    placement_time: datetime, current_time: datetime, wait_seconds: float
) -> bool:
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


def fetch_price_for_notional_check(
    symbol: str,
    side: str,
    quote_provider: QuoteProvider,
    alpaca_manager: AlpacaManager,
) -> Decimal | None:
    """Fetch best available price for notional value calculation.

    Args:
        symbol: Trading symbol
        side: Order side ("BUY" or "SELL")
        quote_provider: Quote provider with get_quote_with_validation method
        alpaca_manager: Alpaca manager with get_current_price method

    Returns:
        Price as Decimal, or None if unavailable

    """
    price: Decimal | None = None
    try:
        # Prefer streaming quote if available via QuoteProvider
        validated = quote_provider.get_quote_with_validation(symbol)
        if validated:
            quote, _ = validated
            # Use ask for BUY, bid for SELL to compute conservative notional
            if side.upper() == "BUY":
                price = Decimal(str(quote.ask_price))
            else:
                price = Decimal(str(quote.bid_price))
        else:
            current_price = alpaca_manager.get_current_price(symbol)
            if current_price is not None and current_price > 0:
                price = Decimal(str(current_price))
    except Exception as e:
        logger.warning(f"Failed to fetch price for {symbol}: {e}")
        price = None

    return price


def is_remaining_quantity_too_small(
    remaining_qty: Decimal,
    asset_info: object | None,
    price: Decimal | None,
    min_notional: Decimal,
) -> bool:
    """Check if remaining quantity is too small to pursue.

    Args:
        remaining_qty: Remaining quantity to check
        asset_info: Asset info with fractionable attribute, or None
        price: Current price for notional calculation, or None
        min_notional: Minimum notional value required

    Returns:
        True if remaining is too small and should be considered complete

    """
    if asset_info is not None and getattr(asset_info, "fractionable", False):
        # For fractionable assets, skip if remaining notional is below broker minimum
        if price is not None:
            remaining_notional = (remaining_qty * price).quantize(Decimal("0.01"))
            return remaining_notional < min_notional
    else:
        # For non-fractionable or unknown assets, check if quantity rounds to zero
        # Uses Decimal.quantize which applies default ROUND_HALF_EVEN rounding mode
        return remaining_qty.quantize(Decimal("1")) <= 0

    return False
