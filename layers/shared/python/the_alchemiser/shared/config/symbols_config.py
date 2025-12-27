#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Symbol Classification Configuration.

This module defines symbol universes and classification rules for different
asset types used across the trading system.

The symbol universes are immutable to ensure thread-safety in concurrent
environments (e.g., AWS Lambda). To modify the universe, update the source
code or load from an external configuration service.
"""

from __future__ import annotations

from typing import Literal

from ..value_objects.symbol import Symbol

# ETF Symbol Universe
# Major ETFs commonly traded by the system strategies.
# This is an immutable frozenset to ensure thread-safety and prevent
# runtime modifications that could cause race conditions.
# Inclusion criteria: Major ETFs with significant trading volume used in
# system strategies (market indices, leveraged, sector, international, bonds).
KNOWN_ETFS: frozenset[str] = frozenset(
    {
        # Market Indices
        "SPY",  # SPDR S&P 500 ETF
        "QQQ",  # Invesco QQQ (NASDAQ-100)
        "IWM",  # iShares Russell 2000 ETF
        # Leveraged ETFs
        "TECL",  # Direxion Daily Technology Bull 3X Shares
        "TQQQ",  # ProShares UltraPro QQQ
        "SOXL",  # Direxion Daily Semiconductor Bull 3X Shares
        # Sector ETFs
        "XLK",  # Technology Select Sector SPDR Fund
        "SMH",  # VanEck Semiconductor ETF
        "SOXX",  # iShares Semiconductor ETF
        # International
        "EFA",  # iShares MSCI EAFE ETF
        "EEM",  # iShares MSCI Emerging Markets ETF
        # Bonds
        "TLT",  # iShares 20+ Year Treasury Bond ETF
        "HYG",  # iShares iBoxx $ High Yield Corporate Bond ETF
    }
)

# Cryptocurrency Symbols (if supported in future)
# This is an immutable frozenset to ensure thread-safety.
# Inclusion criteria: Major cryptocurrencies with Alpaca support.
KNOWN_CRYPTO: frozenset[str] = frozenset(
    {
        "BTC",  # Bitcoin
        "ETH",  # Ethereum
        "BTCUSD",
        "ETHUSD",
    }
)

# Option Suffixes (basic patterns)
# Note: This is a simplified pattern. Real option symbols have complex formats
# like "AAPL240315C00150000". This may cause false positives for stocks
# ending in C or P. Consider removing or improving if accuracy is critical.
OPTION_PATTERNS: frozenset[str] = frozenset(
    {
        "C",  # Call options
        "P",  # Put options
    }
)

AssetType = Literal["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]


def classify_symbol(symbol: str) -> AssetType:
    """Classify a trading symbol into its asset type.

    Uses the Symbol value object for validation to ensure consistency
    across the system. Invalid symbols will raise ValueError.

    Args:
        symbol: Trading symbol to classify

    Returns:
        Asset type classification

    Raises:
        ValueError: If symbol is invalid (empty, contains spaces, invalid characters,
                   exceeds max length, or has other validation failures)

    Examples:
        >>> classify_symbol("AAPL")
        'STOCK'
        >>> classify_symbol("SPY")
        'ETF'
        >>> classify_symbol("BTCUSD")
        'CRYPTO'
        >>> classify_symbol("")
        ValueError: Symbol must not be empty
        >>> classify_symbol("INVALID@")
        ValueError: Symbol contains invalid characters

    Note:
        Option and future detection is simplified and may have false positives.
        Options: Checks if symbol ends with 'C' or 'P' (real option symbols
                have complex formats like "AAPL240315C00150000")
        Futures: Checks if symbol > 5 chars and ends with 2 digits (real
                futures use specific month/year codes like "ESH23")

    """
    # Validate using Symbol value object for consistency
    validated = Symbol(symbol)
    symbol_upper = validated.value  # Already normalized and validated

    # Check for ETFs first (most specific)
    if symbol_upper in KNOWN_ETFS:
        return "ETF"

    # Check for cryptocurrency
    if symbol_upper in KNOWN_CRYPTO:
        return "CRYPTO"

    # Check for options (basic pattern matching)
    # This is simplified - real option symbols have complex formats
    if any(symbol_upper.endswith(pattern) for pattern in OPTION_PATTERNS):
        return "OPTION"

    # Check for futures (basic pattern matching)
    # Futures often have month/year codes - this is very simplified
    if len(symbol_upper) > 5 and symbol_upper[-2:].isdigit():
        return "FUTURE"

    # Default to stock
    return "STOCK"


def is_etf(symbol: str) -> bool:
    """Check if a symbol is a known ETF.

    Uses the Symbol value object for validation to ensure consistency
    across the system. Invalid symbols will raise ValueError.

    Args:
        symbol: Trading symbol to check

    Returns:
        True if symbol is a known ETF

    Raises:
        ValueError: If symbol is invalid (empty, contains spaces, invalid characters,
                   exceeds max length, or has other validation failures)

    Examples:
        >>> is_etf("SPY")
        True
        >>> is_etf("AAPL")
        False
        >>> is_etf("")
        ValueError: Symbol must not be empty

    """
    # Validate using Symbol value object for consistency
    validated = Symbol(symbol)
    return validated.value in KNOWN_ETFS


def get_etf_symbols() -> frozenset[str]:
    """Get all known ETF symbols.

    Returns:
        Frozenset of ETF symbols (immutable)

    """
    return KNOWN_ETFS


def add_etf_symbol(symbol: str) -> None:
    """Add a new ETF symbol to the known list.

    Args:
        symbol: ETF symbol to add

    Raises:
        NotImplementedError: This function is deprecated. Symbol universes
                           are immutable to ensure thread-safety. To modify
                           the universe, update the source code or load from
                           an external configuration service.

    Note:
        This function is deprecated and will be removed in a future version.
        Runtime modification of symbol universes violates immutability
        principles and creates thread-safety risks in concurrent environments.

        For production use, symbol universes should be:
        - Loaded from an external configuration service (S3, DynamoDB, etc.)
        - Versioned for change tracking
        - Immutable at runtime

    """
    raise NotImplementedError(
        "Runtime symbol addition is not supported. Symbol universes are "
        "immutable to ensure thread-safety. To modify the universe, update "
        "the source code or load from an external configuration service."
    )


def get_symbol_universe() -> dict[str, frozenset[str]]:
    """Get all known symbol universes.

    Returns:
        Dictionary mapping asset types to immutable symbol sets.
        Only includes types with explicitly defined universes (ETF, CRYPTO).
        STOCK, OPTION, and FUTURE types are determined by classification logic.

    """
    return {
        "ETF": KNOWN_ETFS,
        "CRYPTO": KNOWN_CRYPTO,
    }
