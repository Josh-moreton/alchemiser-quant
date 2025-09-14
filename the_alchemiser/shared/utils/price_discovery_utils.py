#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized Price Discovery Utilities.

This module provides unified price discovery functionality to eliminate duplication
across multiple modules. All price discovery operations should use this centralized
utility to ensure consistent pricing behavior and calculation methods.

Consolidates the following duplicate implementations:
- execution/brokers/alpaca/adapter.py: bid-ask midpoint calculation
- execution/brokers/account_service.py: delegated price retrieval
- strategy/data/market_data_client.py: quote-based pricing
- Multiple protocol definitions with similar interfaces

Key Features:
- Standardized bid-ask midpoint calculation
- Consistent error handling and logging
- Support for both sync and async operations
- Fallback strategies for price retrieval
- Type-safe interfaces with proper null handling
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class QuoteProvider(Protocol):
    """Protocol for providers that can fetch bid-ask quotes."""

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid-ask quote for a symbol.

        Returns:
            Tuple of (bid, ask) prices or None if unavailable

        """
        ...


@runtime_checkable
class PriceProvider(Protocol):
    """Protocol for providers that can fetch current prices directly."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns:
            Current price or None if unavailable

        """
        ...


def calculate_midpoint_price(bid: float, ask: float) -> float | None:
    """Calculate midpoint price from bid-ask spread.

    This is the core price calculation logic that was duplicated across
    multiple implementations.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Midpoint price or None if inputs are invalid

    Example:
        >>> calculate_midpoint_price(100.0, 101.0)
        100.5
        >>> calculate_midpoint_price(0.0, 101.0)  # Invalid bid
        None

    TODO: Consider enhancing with QuoteModel support from structured types
    to leverage bid_size/ask_size for volume-weighted midpoint calculations
    and improved market depth analysis.

    """
    try:
        if bid > 0 and ask > 0 and ask >= bid:
            return (bid + ask) / 2.0
        logger.warning(f"Invalid bid-ask spread: bid={bid}, ask={ask}")
        return None
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating midpoint: {e}")
        return None


def get_current_price_from_quote(quote_provider: QuoteProvider, symbol: str) -> float | None:
    """Get current price from quote provider using bid-ask midpoint.

    This function consolidates the quote-based price discovery logic that was
    duplicated across execution/brokers/alpaca/adapter.py and
    strategy/data/market_data_client.py.

    Args:
        quote_provider: Provider that can fetch bid-ask quotes
        symbol: Stock symbol

    Returns:
        Current price or None if unavailable

    Example:
        >>> # Assuming alpaca_adapter implements QuoteProvider
        >>> price = get_current_price_from_quote(alpaca_adapter, "AAPL")

    """
    try:
        quote = quote_provider.get_latest_quote(symbol)
        if quote is not None:
            bid, ask = quote
            return calculate_midpoint_price(bid, ask)
        logger.warning(f"No quote available for symbol: {symbol}")
        return None
    except Exception as e:
        logger.error(f"Failed to get current price from quote for {symbol}: {e}")
        return None


def get_current_price_with_fallback(
    primary_provider: PriceProvider | QuoteProvider,
    fallback_provider: PriceProvider | QuoteProvider | None,
    symbol: str,
) -> float | None:
    """Get current price with fallback strategy.

    This function implements the fallback pattern used in several implementations
    where a primary provider is tried first, then falls back to a secondary provider.

    Args:
        primary_provider: Primary price or quote provider
        fallback_provider: Fallback price or quote provider
        symbol: Stock symbol

    Returns:
        Current price or None if all providers fail

    Example:
        >>> # Try streaming first, fallback to REST
        >>> price = get_current_price_with_fallback(
        ...     streaming_service, rest_client, "AAPL"
        ... )

    """
    try:
        # Try primary provider first
        price = _get_price_from_provider(primary_provider, symbol)
        if price is not None:
            return price

        # Try fallback provider
        if fallback_provider is not None:
            price = _get_price_from_provider(fallback_provider, symbol)
            if price is not None:
                logger.debug(f"Used fallback provider for {symbol}")
                return price

        logger.warning(f"All price providers failed for symbol: {symbol}")
        return None

    except Exception as e:
        logger.error(f"Error in price discovery with fallback for {symbol}: {e}")
        return None


def get_current_price_as_decimal(
    provider: PriceProvider | QuoteProvider,
    symbol: str,
) -> Decimal | None:
    """Get current price as Decimal for financial calculations.

    This function provides price discovery specifically for portfolio and financial
    calculations that require Decimal precision instead of float.

    Args:
        provider: Price or quote provider
        symbol: Stock symbol

    Returns:
        Current price as Decimal or None if unavailable

    Example:
        >>> # For portfolio calculations
        >>> price = get_current_price_as_decimal(data_provider, "AAPL")
        >>> if price:
        ...     position_value = price * Decimal("100")  # 100 shares

    """
    try:
        price = _get_price_from_provider(provider, symbol)
        if price is not None:
            return Decimal(str(price))  # Convert via string to avoid float precision issues
        return None
    except Exception as e:
        logger.error(f"Error getting decimal price for {symbol}: {e}")
        return None


def _get_price_from_provider(
    provider: PriceProvider | QuoteProvider,
    symbol: str,
) -> float | None:
    """Internal helper to get price from either type of provider.

    Args:
        provider: Either a PriceProvider or QuoteProvider
        symbol: Stock symbol

    Returns:
        Current price or None if unavailable

    """
    try:
        # Check if provider implements PriceProvider interface
        if isinstance(provider, PriceProvider):
            return provider.get_current_price(symbol)
        # Otherwise assume QuoteProvider interface
        if isinstance(provider, QuoteProvider):
            return get_current_price_from_quote(provider, symbol)
        logger.error(f"Provider does not implement expected interface: {type(provider)}")
        return None
    except Exception as e:
        logger.error(f"Error getting price from provider for {symbol}: {e}")
        return None
