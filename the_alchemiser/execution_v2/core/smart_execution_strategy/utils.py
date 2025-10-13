"""Business Unit: execution | Status: current.

Utility functions for smart execution strategy to reduce cognitive complexity.

This module contains extracted utility functions to help reduce the complexity
of the main strategy functions while keeping them focused and readable.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.constants import MINIMUM_PRICE
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

    Example:
        >>> calculate_price_adjustment(Decimal("100"), Decimal("110"))
        Decimal('105.00')
        >>> calculate_price_adjustment(Decimal("100"), Decimal("110"), Decimal("0.25"))
        Decimal('102.50')

    """
    adjustment = (target_price - original_price) * adjustment_factor
    return original_price + adjustment


def validate_repeg_price_with_history(
    new_price: Decimal,
    price_history: list[Decimal] | None,
    side: str,
    quote: QuoteModel,
    min_improvement: Decimal = Decimal("0.01"),
    correlation_id: str | None = None,
) -> Decimal:
    """Validate and adjust repeg price to avoid duplicates in history.

    Args:
        new_price: Calculated new price
        price_history: Previous prices to avoid
        side: Order side ("BUY" or "SELL")
        quote: Current market quote
        min_improvement: Minimum price improvement to enforce
        correlation_id: Optional correlation ID for traceability

    Returns:
        Validated and potentially adjusted price

    Example:
        >>> from datetime import datetime, UTC
        >>> quote = QuoteModel(
        ...     symbol="AAPL",
        ...     bid_price=100.0,
        ...     ask_price=100.5,
        ...     bid_size=100.0,
        ...     ask_size=100.0,
        ...     timestamp=datetime.now(UTC),
        ... )
        >>> validate_repeg_price_with_history(
        ...     Decimal("100.00"),
        ...     [Decimal("99.00")],
        ...     "BUY",
        ...     quote
        ... )
        Decimal('100.00')

    """
    # Validate input for NaN/Infinity
    if not ((new_price.is_finite() and new_price.is_normal()) or new_price == 0):
        logger.warning(
            f"Invalid new_price value: {new_price}",
            extra={"correlation_id": correlation_id, "symbol": quote.symbol, "side": side},
        )
        # Return a safe default minimum price
        return MINIMUM_PRICE

    if not price_history or new_price not in price_history:
        return new_price

    log_extra = {
        "correlation_id": correlation_id,
        "symbol": quote.symbol,
        "side": side,
        "new_price": str(new_price),
    }
    logger.info(
        f"🔄 Calculated repeg price ${new_price} already used for {quote.symbol} {side}, "
        f"forcing minimum improvement",
        extra=log_extra,
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
            f"after forced improvement. Price ${adjusted_price} still in history: {price_history}",
            extra={
                **log_extra,
                "adjusted_price": str(adjusted_price),
                "price_history": [str(p) for p in price_history],
            },
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


def ensure_minimum_price(
    price: Decimal,
    min_price: Decimal = MINIMUM_PRICE,
    correlation_id: str | None = None,
) -> Decimal:
    """Ensure price meets minimum requirements.

    Args:
        price: Price to validate
        min_price: Minimum allowed price (defaults to MINIMUM_PRICE constant)
        correlation_id: Optional correlation ID for traceability

    Returns:
        Valid price (at least min_price)

    Example:
        >>> ensure_minimum_price(Decimal("10.00"))
        Decimal('10.00')
        >>> ensure_minimum_price(Decimal("-5.00"))
        Decimal('0.01')

    """
    # Validate input for NaN/Infinity
    if not (price.is_finite() and (price.is_normal() or price == 0)):
        logger.warning(
            f"Invalid price value (NaN/Infinity): {price}, using minimum price {min_price}",
            extra={"correlation_id": correlation_id, "invalid_price": str(price)},
        )
        return min_price

    if price <= 0:
        logger.warning(
            f"Invalid price {price}, using minimum price {min_price}",
            extra={"correlation_id": correlation_id, "invalid_price": str(price)},
        )
        return min_price
    return max(price, min_price)


def fetch_price_for_notional_check(
    symbol: str,
    side: str,
    quote_provider: QuoteProvider,
    alpaca_manager: AlpacaManager,
    correlation_id: str | None = None,
) -> Decimal | None:
    """Fetch best available price for notional value calculation.

    This function attempts to get the most current price from streaming quotes,
    falling back to REST API if streaming is unavailable. Timeouts are handled
    by the underlying services (QuoteProvider and AlpacaManager).

    Args:
        symbol: Trading symbol
        side: Order side ("BUY" or "SELL")
        quote_provider: Quote provider with get_quote_with_validation method
        alpaca_manager: Alpaca manager with get_current_price method
        correlation_id: Optional correlation ID for traceability

    Returns:
        Price as Decimal, or None if unavailable

    Raises:
        DataProviderError: If quote provider encounters an error
        TradingClientError: If Alpaca API encounters an error
        ValueError: If price conversion fails

    Note:
        Timeouts are controlled by the quote_provider and alpaca_manager
        configuration. This function does not implement additional timeout logic.

    Example:
        >>> from unittest.mock import Mock
        >>> quote_provider = Mock()
        >>> alpaca_manager = Mock()
        >>> alpaca_manager.get_current_price.return_value = 100.50
        >>> price = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)

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
    except (ValueError, TypeError) as e:
        # Catch conversion errors explicitly
        logger.warning(
            f"Failed to convert price to Decimal for {symbol}: {e}",
            extra={
                "correlation_id": correlation_id,
                "symbol": symbol,
                "side": side,
                "error": str(e),
            },
        )
        price = None
    except Exception as e:
        # Catch any other unexpected errors but log them for visibility
        logger.warning(
            f"Unexpected error fetching price for {symbol}: {e}",
            extra={
                "correlation_id": correlation_id,
                "symbol": symbol,
                "side": side,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
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

    Example:
        >>> from unittest.mock import Mock
        >>> asset_info = Mock()
        >>> asset_info.fractionable = True
        >>> is_remaining_quantity_too_small(
        ...     Decimal("0.1"),
        ...     asset_info,
        ...     Decimal("5.00"),
        ...     Decimal("1.00")
        ... )
        True

    """
    # Validate input for NaN/Infinity
    if not (remaining_qty.is_finite() and (remaining_qty.is_normal() or remaining_qty == 0)):
        logger.warning(f"Invalid remaining_qty value (NaN/Infinity): {remaining_qty}")
        return True  # Treat invalid quantities as too small

    if price is not None and not (price.is_finite() and (price.is_normal() or price == 0)):
        logger.warning(f"Invalid price value (NaN/Infinity): {price}")
        # Continue without price-based validation

    if asset_info is not None and getattr(asset_info, "fractionable", False):
        # For fractionable assets, skip if remaining notional is below broker minimum
        if price is not None and price.is_finite() and (price.is_normal() or price == 0):
            remaining_notional = (remaining_qty * price).quantize(Decimal("0.01"))
            return remaining_notional < min_notional
    else:
        # For non-fractionable or unknown assets, check if quantity rounds to zero
        # Uses Decimal.quantize which applies default ROUND_HALF_EVEN rounding mode
        return remaining_qty.quantize(Decimal("1")) <= 0

    return False
