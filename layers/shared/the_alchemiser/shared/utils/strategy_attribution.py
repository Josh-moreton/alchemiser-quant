#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy attribution utilities for extracting primary strategies from contributions.

These utilities support per-strategy order attribution by determining
which strategy is the primary contributor for a given symbol.
"""

from __future__ import annotations

from decimal import Decimal


def get_primary_strategy_for_symbol(
    symbol: str,
    strategy_contributions: dict[str, dict[str, Decimal]],
) -> str | None:
    """Get the primary (highest-weight) contributing strategy for a symbol.

    When multiple strategies contribute to the same symbol, this function
    returns the strategy with the highest allocation weight for order
    attribution purposes.

    Args:
        symbol: The trading symbol to look up
        strategy_contributions: Dict mapping strategy_id -> {symbol: weight}
            Example: {"momentum": {"AAPL": Decimal("0.6")}, "mean_rev": {"AAPL": Decimal("0.4")}}

    Returns:
        The strategy_id with the highest contribution for the symbol,
        or None if no strategy contributes to this symbol.

    Examples:
        >>> contributions = {
        ...     "momentum": {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.3")},
        ...     "mean_rev": {"AAPL": Decimal("0.4")},
        ... }
        >>> get_primary_strategy_for_symbol("AAPL", contributions)
        'momentum'
        >>> get_primary_strategy_for_symbol("MSFT", contributions)
        'momentum'
        >>> get_primary_strategy_for_symbol("GOOGL", contributions)
        None

    """
    if not strategy_contributions:
        return None

    # Normalize symbol for consistent lookup
    symbol_upper = symbol.strip().upper()

    # Find all strategies that contribute to this symbol
    contributing_strategies: list[tuple[str, Decimal]] = []
    for strategy_id, allocations in strategy_contributions.items():
        # Normalize allocation keys for comparison
        normalized_allocations = {k.strip().upper(): v for k, v in allocations.items()}
        if symbol_upper in normalized_allocations:
            weight = normalized_allocations[symbol_upper]
            contributing_strategies.append((strategy_id, weight))

    if not contributing_strategies:
        return None

    # Return the strategy with the highest weight
    primary_strategy = max(contributing_strategies, key=lambda x: x[1])
    return primary_strategy[0]


def get_primary_strategies_for_symbols(
    symbols: list[str],
    strategy_contributions: dict[str, dict[str, Decimal]],
) -> dict[str, str | None]:
    """Get primary strategies for multiple symbols.

    Convenience function to batch-process symbol attribution.

    Args:
        symbols: List of trading symbols
        strategy_contributions: Dict mapping strategy_id -> {symbol: weight}

    Returns:
        Dict mapping symbol -> primary_strategy_id (or None if no contributor)

    Examples:
        >>> contributions = {"momentum": {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.2")}}
        >>> get_primary_strategies_for_symbols(["AAPL", "GOOGL"], contributions)
        {'AAPL': 'momentum', 'GOOGL': None}

    """
    return {
        symbol: get_primary_strategy_for_symbol(symbol, strategy_contributions)
        for symbol in symbols
    }


def get_single_strategy_id(
    strategy_contributions: dict[str, dict[str, Decimal]],
) -> str | None:
    """Get strategy_id when there's only one contributing strategy.

    For single-strategy execution (most common case), returns the lone
    strategy_id. For multi-strategy cases, returns None (caller should
    use per-symbol attribution).

    Args:
        strategy_contributions: Dict mapping strategy_id -> {symbol: weight}

    Returns:
        The single strategy_id if exactly one strategy contributed,
        None otherwise.

    Examples:
        >>> get_single_strategy_id({"momentum": {"AAPL": Decimal("0.5")}})
        'momentum'
        >>> get_single_strategy_id({"momentum": {"AAPL": Decimal("0.6")}, "mean_rev": {"AAPL": Decimal("0.4")}})
        None
        >>> get_single_strategy_id({})
        None

    """
    if not strategy_contributions:
        return None

    if len(strategy_contributions) == 1:
        return next(iter(strategy_contributions.keys()))

    return None
