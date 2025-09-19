#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Symbol Classification Configuration.

This module defines symbol universes and classification rules for different
asset types used across the trading system.
"""

from __future__ import annotations

from typing import Literal

# ETF Symbol Universe
# Major ETFs commonly traded by the system strategies
KNOWN_ETFS = {
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

# Cryptocurrency Symbols (if supported in future)
KNOWN_CRYPTO = {
    "BTC",  # Bitcoin
    "ETH",  # Ethereum
    "BTCUSD",
    "ETHUSD",
}

# Option Suffixes (basic patterns)
OPTION_PATTERNS = {
    "C",  # Call options
    "P",  # Put options
}

AssetType = Literal["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]


def classify_symbol(symbol: str) -> AssetType:
    """Classify a trading symbol into its asset type.

    Args:
        symbol: Trading symbol to classify

    Returns:
        Asset type classification

    Examples:
        >>> classify_symbol("AAPL")
        'STOCK'
        >>> classify_symbol("SPY")
        'ETF'
        >>> classify_symbol("BTCUSD")
        'CRYPTO'

    """
    symbol_upper = symbol.upper().strip()

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

    Args:
        symbol: Trading symbol to check

    Returns:
        True if symbol is a known ETF

    """
    return symbol.upper().strip() in KNOWN_ETFS


def get_etf_symbols() -> set[str]:
    """Get all known ETF symbols.

    Returns:
        Set of ETF symbols

    """
    return KNOWN_ETFS.copy()


def add_etf_symbol(symbol: str) -> None:
    """Add a new ETF symbol to the known list.

    Args:
        symbol: ETF symbol to add

    Note:
        This modifies the global KNOWN_ETFS set. In production,
        this configuration should be loaded from a database or
        configuration service rather than modified at runtime.

    """
    KNOWN_ETFS.add(symbol.upper().strip())


def get_symbol_universe() -> dict[str, set[str]]:
    """Get all known symbol universes.

    Returns:
        Dictionary mapping asset types to symbol sets

    """
    return {
        "ETF": KNOWN_ETFS.copy(),
        "CRYPTO": KNOWN_CRYPTO.copy(),
    }
