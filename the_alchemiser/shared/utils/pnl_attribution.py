#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L attribution utilities for multi-strategy portfolios.

Provides utilities to decompose realized P&L from executed orders back to
contributing strategies based on their allocation weights, enabling per-strategy
performance tracking and attribution analysis.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def decompose_pnl_to_strategies(
    symbol: str,
    total_pnl: Decimal,
    strategy_contributions: dict[str, dict[str, Decimal]],
) -> dict[str, Decimal]:
    """Decompose fill P&L proportionally to contributing strategies.

    Distributes realized P&L from a trade across strategies based on their
    allocation contributions. Each strategy receives a portion of the P&L
    proportional to its contribution to the total allocation for that symbol.

    Args:
        symbol: Trading symbol (e.g., "AAPL")
        total_pnl: Total realized P&L from the executed order (can be positive or negative)
        strategy_contributions: Per-strategy allocation breakdown
            Format: {strategy_id: {symbol: allocation_weight}}

    Returns:
        Dictionary mapping strategy_id to their proportional P&L share
        Format: {strategy_id: pnl_portion}

    Raises:
        ValueError: If symbol has no contributions or total allocation is zero

    Examples:
        >>> contributions = {
        ...     "momentum": {"AAPL": Decimal("0.6")},
        ...     "mean_rev": {"AAPL": Decimal("0.4")}
        ... }
        >>> pnl = decompose_pnl_to_strategies(
        ...     symbol="AAPL",
        ...     total_pnl=Decimal("500.00"),
        ...     strategy_contributions=contributions
        ... )
        >>> pnl
        {'momentum': Decimal('300.00'), 'mean_rev': Decimal('200.00')}

        >>> # Works with losses too
        >>> pnl = decompose_pnl_to_strategies(
        ...     symbol="AAPL",
        ...     total_pnl=Decimal("-100.00"),
        ...     strategy_contributions=contributions
        ... )
        >>> pnl
        {'momentum': Decimal('-60.00'), 'mean_rev': Decimal('-40.00')}

    """
    # Calculate total allocation for this symbol across all strategies
    # Store strategy allocations for efficient access later
    strategy_allocations: dict[str, Decimal] = {}

    for strategy_id, allocations in strategy_contributions.items():
        if symbol in allocations:
            strategy_allocations[strategy_id] = allocations[symbol]

    total_allocation = sum(strategy_allocations.values())

    # Validate that symbol has contributions
    if not strategy_allocations:
        logger.warning(
            "No strategy contributions found for symbol",
            extra={
                "module": "pnl_attribution",
                "function": "decompose_pnl_to_strategies",
                "symbol": symbol,
            },
        )
        raise ValueError(f"Symbol {symbol} has no strategy contributions")

    # Validate total allocation is not zero
    if total_allocation == 0:
        logger.warning(
            "Total allocation is zero for symbol",
            extra={
                "module": "pnl_attribution",
                "function": "decompose_pnl_to_strategies",
                "symbol": symbol,
                "contributing_strategies": list(strategy_allocations.keys()),
            },
        )
        raise ValueError(f"Total allocation for {symbol} is zero")

    # Decompose P&L proportionally to each strategy
    result: dict[str, Decimal] = {}
    for strategy_id, strategy_allocation in strategy_allocations.items():
        # Calculate proportion: strategy_allocation / total_allocation
        proportion = strategy_allocation / total_allocation

        # Decompose P&L: total_pnl * proportion
        strategy_pnl = total_pnl * proportion
        result[strategy_id] = strategy_pnl

    logger.debug(
        "P&L decomposed to strategies",
        extra={
            "module": "pnl_attribution",
            "function": "decompose_pnl_to_strategies",
            "symbol": symbol,
            "total_pnl": str(total_pnl),
            "total_allocation": str(total_allocation),
            "num_strategies": len(result),
        },
    )

    return result
