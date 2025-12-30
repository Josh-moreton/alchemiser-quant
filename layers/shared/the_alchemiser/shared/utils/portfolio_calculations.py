#!/usr/bin/env python3
"""Business Unit: shared | Status: DEPRECATED.

Portfolio calculation utilities for allocation analysis and comparison.

.. deprecated::
    This module applies equity_deployment_pct to total portfolio value rather
    than using the proper equity-based calculation with margin safety validation.
    For margin-aware trading, use `the_alchemiser.portfolio_v2.core.planner.RebalancePlanCalculator` instead.

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
    consolidated_portfolio: dict[str, Decimal],
    account_dict: dict[str, float | int | str],
    positions_dict: dict[str, float],
    correlation_id: str | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Build allocation comparison between target and current portfolio states.

    .. deprecated::
        This function multiplies deployment_pct by total portfolio value.
        For margin-aware trading with proper capital constraints, use
        `RebalancePlanCalculator.build_plan()` which correctly applies
        deployment_pct to base capital (cash + expected sell proceeds).

    Args:
        consolidated_portfolio: Target allocation percentages by symbol (Decimal precision)
        account_dict: Account information including equity (preferred) or portfolio_value
        positions_dict: Current positions with market values by symbol
        correlation_id: Optional correlation ID for request tracing

    Returns:
        Dictionary containing:
        - target_values: Dict of symbol to target dollar values (Decimal)
        - current_values: Dict of symbol to current dollar values (Decimal)
        - deltas: Dict of symbol to dollar differences (Decimal)

    Raises:
        ConfigurationError: If equity cannot be determined from account info

    """
    logger.info(
        "Starting allocation comparison calculation",
        extra={
            "correlation_id": correlation_id,
            "num_target_symbols": len(consolidated_portfolio),
            "num_current_positions": len(positions_dict),
        },
    )
    # Get equity from account info (use equity, not deprecated portfolio_value)
    equity = account_dict.get("equity")
    # Fall back to portfolio_value for backward compatibility with older data
    if equity in (None, 0, 0.0, "0", "0.0"):
        equity = account_dict.get("portfolio_value")

    if equity is None:
        logger.error(
            "Equity not available in account info",
            extra={
                "correlation_id": correlation_id,
                "account_keys": list(account_dict.keys()),
            },
        )
        raise ConfigurationError(
            "Equity not available in account info. "
            "Cannot calculate target allocation values without equity."
        )

    # Convert equity to Money for precise calculations
    equity_money = Money.from_decimal(Decimal(str(equity)), "USD")
    logger.debug(
        "Equity determined",
        extra={
            "correlation_id": correlation_id,
            "equity": str(equity_money.to_decimal()),
        },
    )

    # Apply capital deployment percentage to avoid buying power issues
    # WARNING: This multiplies total portfolio value, not base capital.
    # For margin-aware trading, use RebalancePlanCalculator which multiplies
    # base capital (cash + sell proceeds) instead.
    settings = load_settings()
    deployment_multiplier = Decimal(str(settings.alpaca.effective_deployment_pct))
    effective_equity = equity_money.multiply(deployment_multiplier)

    # Calculate target values in dollars using effective equity
    target_values = {}
    for symbol, weight in consolidated_portfolio.items():
        # Convert weight to Decimal if needed (Money.multiply requires Decimal)
        weight_decimal = weight if isinstance(weight, Decimal) else Decimal(str(weight))
        target_money = effective_equity.multiply(weight_decimal)
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
