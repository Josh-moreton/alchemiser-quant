#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio calculation utilities for allocation analysis and comparison.

This module provides shared calculation functions for portfolio allocation
analysis, avoiding duplication across modules. These utilities are used by
both CLI formatters and orchestrators for consistent allocation calculations.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.money import Money

logger = get_logger(__name__)


def build_allocation_comparison(
    consolidated_portfolio: dict[str, float],
    account_dict: dict[str, float | int | str],
    positions_dict: dict[str, float],
    correlation_id: str | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Build allocation comparison between target and current portfolio states.

    Args:
        consolidated_portfolio: Target allocation percentages by symbol
        account_dict: Account information including portfolio_value or equity
        positions_dict: Current positions with market values by symbol
        correlation_id: Optional correlation ID for request tracing

    Returns:
        Dictionary containing:
        - target_values: Dict of symbol to target dollar values (Decimal)
        - current_values: Dict of symbol to current dollar values (Decimal)
        - deltas: Dict of symbol to dollar differences (Decimal)

    Raises:
        ConfigurationError: If portfolio value cannot be determined from account info

    """
    logger.info(
        "Starting allocation comparison calculation",
        extra={
            "correlation_id": correlation_id,
            "num_target_symbols": len(consolidated_portfolio),
            "num_current_positions": len(positions_dict),
        },
    )
    # Get portfolio value from account info
    portfolio_value = account_dict.get("portfolio_value")
    # Treat missing or zero portfolio_value as unavailable and fall back to equity
    if portfolio_value in (None, 0, 0.0, "0", "0.0"):
        portfolio_value = account_dict.get("equity")

    if portfolio_value is None:
        logger.error(
            "Portfolio value not available in account info",
            extra={
                "correlation_id": correlation_id,
                "account_keys": list(account_dict.keys()),
            },
        )
        raise ConfigurationError(
            "Portfolio value not available in account info. "
            "Cannot calculate target allocation values without portfolio value."
        )

    # Convert portfolio_value to Money for precise calculations
    portfolio_value_money = Money.from_decimal(Decimal(str(portfolio_value)), "USD")
    logger.debug(
        "Portfolio value determined",
        extra={
            "correlation_id": correlation_id,
            "portfolio_value": str(portfolio_value_money.to_decimal()),
        },
    )

    # Apply cash reserve to avoid buying power issues with broker constraints
    # This ensures we don't try to use 100% of portfolio value which can
    # exceed available buying power
    settings = load_settings()
    usage_multiplier = Decimal(str(1.0 - settings.alpaca.cash_reserve_pct))
    effective_portfolio_value = portfolio_value_money.multiply(usage_multiplier)

    # Calculate target values in dollars using effective portfolio value
    target_values = {}
    for symbol, weight in consolidated_portfolio.items():
        target_money = effective_portfolio_value.multiply(Decimal(str(weight)))
        target_values[symbol] = target_money.to_decimal()

    # Convert current position values to Money then extract Decimal
    current_values = {}
    for symbol, market_value in positions_dict.items():
        current_money = Money.from_decimal(Decimal(str(market_value)), "USD")
        current_values[symbol] = current_money.to_decimal()

    # Calculate deltas (target - current) using Money for precision
    all_symbols = set(target_values.keys()) | set(current_values.keys())
    deltas: dict[str, Decimal] = {}
    for symbol in all_symbols:
        target_val_decimal = target_values.get(symbol, Decimal("0"))
        current_val_decimal = current_values.get(symbol, Decimal("0"))

        target_money = Money.from_decimal(target_val_decimal, "USD")
        current_money = Money.from_decimal(current_val_decimal, "USD")

        # Perform subtraction with Money to ensure precision
        if target_money >= current_money:
            delta_money = target_money.subtract(current_money)
            deltas[symbol] = delta_money.to_decimal()
        else:
            # When current > target, we need a negative delta
            # Since Money doesn't support negative amounts, compute as -(current - target)
            delta_money = current_money.subtract(target_money)
            deltas[symbol] = -delta_money.to_decimal()

    logger.info(
        "Allocation comparison completed",
        extra={
            "correlation_id": correlation_id,
            "num_deltas": len(deltas),
            "symbols_to_increase": sum(1 for d in deltas.values() if d > 0),
            "symbols_to_decrease": sum(1 for d in deltas.values() if d < 0),
        },
    )

    return {
        "target_values": target_values,
        "current_values": current_values,
        "deltas": deltas,
    }
