"""Business Unit: shared | Status: current.

Legacy compatibility layer for RealTimeQuote and conversion helpers.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING

from .models import RealTimeQuote

if TYPE_CHECKING:
    from the_alchemiser.shared.types.market_data import QuoteModel


def get_real_time_quote_with_warning(
    symbol: str, 
    get_quote_callback: Callable[[str], RealTimeQuote | None]
) -> RealTimeQuote | None:
    """Get real-time quote with deprecation warning.
    
    Args:
        symbol: Stock symbol
        get_quote_callback: Callback to get quote data
        
    Returns:
        RealTimeQuote object or None if not available

    """
    warnings.warn(
        "get_real_time_quote() is deprecated. Use get_quote_data() for new code.",
        DeprecationWarning,
        stacklevel=3,  # Skip this function and the caller
    )
    return get_quote_callback(symbol)


def convert_quote_model_to_legacy(quote_model: QuoteModel) -> RealTimeQuote:
    """Convert QuoteModel to legacy RealTimeQuote format.
    
    Args:
        quote_model: Modern structured quote data
        
    Returns:
        Legacy RealTimeQuote object

    """
    # Calculate mid price as last_price fallback
    mid_price = (quote_model.bid_price + quote_model.ask_price) / 2
    
    return RealTimeQuote(
        bid=quote_model.bid_price,
        ask=quote_model.ask_price,
        last_price=mid_price,
        timestamp=quote_model.timestamp,
    )


def get_best_price_from_quote(quote_model: QuoteModel) -> float:
    """Get the best available price from a quote (mid-price priority).
    
    Args:
        quote_model: Structured quote data
        
    Returns:
        Best available price

    """
    if quote_model.bid_price > 0 and quote_model.ask_price > 0:
        return quote_model.mid_price
    if quote_model.bid_price > 0:
        return quote_model.bid_price
    if quote_model.ask_price > 0:
        return quote_model.ask_price
    return 0.0  # Fallback


def validate_quote_spread(quote_model: QuoteModel) -> bool:
    """Validate that quote has a reasonable spread.
    
    Args:
        quote_model: Quote to validate
        
    Returns:
        True if spread is valid (ask > bid)

    """
    return quote_model.ask_price > quote_model.bid_price