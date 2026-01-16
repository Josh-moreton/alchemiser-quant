"""Business Unit: shared | Status: current.

Utility functions for options hedging module.

Provides shared utilities for market data access and price fetching.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from ..logging import get_logger
from .constants import DEFAULT_ETF_PRICE_FALLBACK, DEFAULT_ETF_PRICES

if TYPE_CHECKING:
    from ..config.container import ApplicationContainer

logger = get_logger(__name__)


def get_underlying_price(container: ApplicationContainer, symbol: str) -> Decimal:
    """Get current price of underlying ETF.

    Attempts to fetch real-time price via AlpacaManager.
    Falls back to DEFAULT_ETF_PRICES on API failure or invalid data.

    Args:
        container: Application DI container for accessing AlpacaManager
        symbol: ETF symbol (QQQ, SPY, XLK, etc.)

    Returns:
        Current price from market data or fallback estimate

    Note:
        - Uses mid price (bid + ask) / 2 for fair value
        - Validates that prices are positive before using
        - Timeout protection via AlpacaManager's error handling
        - Logs price source for observability

    Examples:
        >>> container = ApplicationContainer.create_for_environment("production")
        >>> price = get_underlying_price(container, "QQQ")
        >>> print(price)  # Decimal('485.50') from live market data

    """
    try:
        # Attempt to get real-time quote via AlpacaManager
        alpaca_manager = container.infrastructure.alpaca_manager()
        quote = alpaca_manager.get_latest_quote(symbol)

        # Validate quote has valid positive prices
        # Note: QuoteModel fields are non-optional, but we check None explicitly
        # for safety. We also require positive prices to ensure valid mid-price calc.
        if quote is not None and quote.bid_price > 0 and quote.ask_price > 0:
            # Use mid price for fair value
            # Explicit Decimal type ensures proper arithmetic
            mid_price: Decimal = (quote.bid_price + quote.ask_price) / Decimal("2")
            logger.info(
                "Using real-time ETF price",
                symbol=symbol,
                price=str(mid_price),
                bid=str(quote.bid_price),
                ask=str(quote.ask_price),
                price_source="live_market_data",
            )
            return mid_price
    except Exception as e:
        logger.warning(
            "Failed to fetch real-time ETF price, using fallback",
            symbol=symbol,
            error=str(e),
            price_source="fallback",
        )

    # Fallback to hardcoded prices
    fallback_price = DEFAULT_ETF_PRICES.get(symbol, DEFAULT_ETF_PRICE_FALLBACK)
    logger.info(
        "Using fallback ETF price",
        symbol=symbol,
        price=str(fallback_price),
        price_source="fallback",
    )
    return fallback_price
