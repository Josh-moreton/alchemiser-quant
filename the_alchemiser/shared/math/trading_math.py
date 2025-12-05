#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trading Math Utilities for The Alchemiser Quantitative Trading System.

This module contains pure mathematical functions for trading calculations,
including position sizing, dynamic limit price calculation, and slippage
calculations. All functions are side-effect free, making them easy to
unit test and reason about.

The module provides the mathematical foundation for:
- Position sizing based on portfolio weights
- Dynamic limit order pricing strategies
- Slippage and transaction cost calculations
- Allocation discrepancy calculations

For portfolio rebalancing logic, use `portfolio_v2.core.planner.RebalancePlanCalculator`.

All functions follow functional programming principles with no side effects,
ensuring predictable behavior and easy testing.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def _calculate_midpoint_price(bid: float, ask: float, *, side_is_buy: bool) -> float:
    """Calculate midpoint price with fallback logic.

    Args:
        bid: Bid price
        ask: Ask price
        side_is_buy: Whether this is a buy order

    Returns:
        Calculated midpoint or appropriate fallback

    """
    if bid > 0 and ask > 0:
        return (bid + ask) / 2
    return bid if side_is_buy else ask


def _calculate_precision_from_tick_size(tick_size_decimal: Decimal) -> int:
    """Calculate precision from tick size decimal.

    Args:
        tick_size_decimal: Decimal tick size object

    Returns:
        Precision level (minimum 2)

    """
    exponent = tick_size_decimal.as_tuple().exponent
    if isinstance(exponent, int):
        return max(2, -exponent)
    return 2


def calculate_position_size(
    current_price: float, portfolio_weight: float, account_value: float
) -> float:
    """Calculate the number of shares to buy/sell based on portfolio weight.

    This function calculates the appropriate position size (in shares) needed
    to achieve a target portfolio weight. It supports fractional shares and
    handles edge cases like zero or negative prices.

    Args:
        current_price (float): Current price per share. Must be positive.
        portfolio_weight (float): Target weight as a fraction (0.0 to 1.0).
            For example, 0.25 represents 25% of the portfolio.
        account_value (float): Total account value in dollars.

    Returns:
        float: Number of shares to buy/sell, rounded to 6 decimal places
            for fractional share support. Returns 0.0 if price is invalid.

    Example:
        >>> # Target 25% allocation in AAPL at $150/share with $10,000 account
        >>> shares = calculate_position_size(150.0, 0.25, 10000.0)
        >>> print(f"Shares to buy: {shares}")
        Shares to buy: 16.666667

    Note:
        The function rounds to 6 decimal places as this is the maximum
        precision supported by Alpaca for fractional shares.

    """
    if current_price <= 0:
        return 0.0

    # Calculate target dollar amount based on strategy allocation of full account value
    target_value = account_value * portfolio_weight

    # Calculate shares (fractional)
    return round(target_value / current_price, 6)  # 6 decimals is safe for Alpaca


def calculate_position_size_decimal(
    current_price: Decimal, portfolio_weight: Decimal, account_value: Decimal
) -> Decimal:
    """Calculate the number of shares to buy/sell using Decimal for precision.

    This function provides financial-grade precision for position sizing calculations
    by using Decimal arithmetic throughout. Use this version for production trading
    where floating-point precision errors are unacceptable.

    Args:
        current_price (Decimal): Current price per share. Must be positive.
        portfolio_weight (Decimal): Target weight as a fraction (0.0 to 1.0).
            For example, Decimal('0.25') represents 25% of the portfolio.
        account_value (Decimal): Total account value in dollars.

    Returns:
        Decimal: Number of shares to buy/sell, with 6 decimal places precision
            for fractional share support. Returns Decimal('0') if price is invalid.

    Example:
        >>> from decimal import Decimal
        >>> # Target 25% allocation in AAPL at $150/share with $10,000 account
        >>> price = Decimal('150.00')
        >>> weight = Decimal('0.25')
        >>> account = Decimal('10000.00')
        >>> shares = calculate_position_size_decimal(price, weight, account)
        >>> print(f"Shares to buy: {shares}")
        Shares to buy: 16.666667

    Note:
        This function uses Decimal arithmetic per guardrails for money calculations.
        The result is quantized to 6 decimal places (Alpaca's maximum precision).

    """
    if current_price <= 0:
        return Decimal("0")

    # Calculate target dollar amount based on strategy allocation
    target_value = account_value * portfolio_weight

    # Calculate shares (fractional) with Decimal precision
    shares = target_value / current_price

    # Quantize to 6 decimal places (Alpaca's maximum)
    return shares.quantize(Decimal("0.000001"))


def calculate_dynamic_limit_price(
    *,
    side_is_buy: bool,
    bid: float,
    ask: float,
    step: int = 0,
    tick_size: float = 0.01,
    max_steps: int = 5,
) -> float:
    """Calculate a limit price using a dynamic pegging strategy.

    This function implements a progressive limit pricing strategy that starts
    near the bid/ask midpoint and moves toward the market price with each
    retry attempt. This approach balances execution probability with price
    improvement potential.

    The algorithm:
    1. Start near the bid/ask midpoint
    2. For buy orders: move up toward ask price with each step
    3. For sell orders: move down toward bid price with each step
    4. After max_steps, use market price (ask for buys, bid for sells)

    Args:
        side_is_buy (bool): True for buy orders, False for sell orders.
        bid (float): Current bid price from market data.
        ask (float): Current ask price from market data.
        step (int, optional): Current retry step (0 = first attempt).
            Defaults to 0.
        tick_size (float, optional): Price increment for each step.
            Defaults to 0.01 (1 cent).
        max_steps (int, optional): Maximum steps before using market price.
            Defaults to 5.

    Returns:
        float: Calculated limit price rounded to 2 decimal places.

    Example:
        >>> # First attempt at buying with bid=100.00, ask=100.10
        >>> price = calculate_dynamic_limit_price(True, 100.00, 100.10, step=0)
        >>> print(f"Initial buy limit: ${price}")
        Initial buy limit: $100.05

        >>> # Third retry attempt
        >>> price = calculate_dynamic_limit_price(True, 100.00, 100.10, step=2)
        >>> print(f"Retry limit: ${price}")
        Retry limit: $100.07

    Note:
        This is a pure function version of the dynamic pricing logic used
        in the OrderManager class for limit order placement.

    """
    mid = _calculate_midpoint_price(bid, ask, side_is_buy=side_is_buy)

    if step > max_steps:
        return round(ask if side_is_buy else bid, 2)

    if side_is_buy:
        price = min(mid + step * tick_size, ask if ask > 0 else mid)
    else:
        price = max(mid - step * tick_size, bid if bid > 0 else mid)

    return round(price, 2)


class TickSizeProvider(Protocol):
    """Protocol for dynamic tick size providers.

    Implementations return the appropriate tick size for a given symbol and price.
    """

    def get_tick_size(self, symbol: str, price: Decimal) -> Decimal:
        """Return the tick size for `symbol` at `price`."""


def calculate_dynamic_limit_price_with_symbol(
    *,
    side_is_buy: bool,
    bid: float,
    ask: float,
    symbol: str,
    step: int = 0,
    max_steps: int = 5,
    tick_size_provider: TickSizeProvider | None = None,
) -> float:
    """Calculate a limit price using dynamic tick size resolution.

    Phase 7 Enhancement: Uses DynamicTickSizeService for symbol-specific tick sizes
    instead of hardcoded values.

    Args:
        side_is_buy (bool): True for buy orders, False for sell orders.
        bid (float): Current bid price from market data.
        ask (float): Current ask price from market data.
        symbol (str): Trading symbol for tick size resolution.
        step (int, optional): Current retry step (0 = first attempt).
            Defaults to 0.
        max_steps (int, optional): Maximum steps before using market price.
            Defaults to 5.
        tick_size_provider (TickSizeProvider | None): Optional injected tick size
            provider used to resolve symbol-specific tick sizes. Must expose
            get_tick_size(symbol: str, price: Decimal) -> Decimal.

    Returns:
        float: Calculated limit price with appropriate precision.

    Example:
        >>> # Dynamic tick size based on symbol and price
        >>> price = calculate_dynamic_limit_price_with_symbol(True, 100.00, 100.10, "AAPL", step=0)
        >>> print(f"Initial buy limit: ${price}")
        Initial buy limit: $100.05

    """
    from the_alchemiser.shared.services.tick_size_service import (
        DynamicTickSizeService,
    )

    mid_price = _calculate_midpoint_price(bid, ask, side_is_buy=side_is_buy)

    # Get dynamic tick size for this symbol and price
    service = tick_size_provider or DynamicTickSizeService()
    tick_size_decimal = service.get_tick_size(symbol, Decimal(str(mid_price)))
    tick_size = float(tick_size_decimal)

    precision = _calculate_precision_from_tick_size(tick_size_decimal)

    if step > max_steps:
        return round(ask if side_is_buy else bid, precision)

    if side_is_buy:
        price = min(mid_price + step * tick_size, ask if ask > 0 else mid_price)
    else:
        price = max(mid_price - step * tick_size, bid if bid > 0 else mid_price)

    return round(price, precision)


def calculate_slippage_buffer(current_price: float, slippage_bps: float) -> float:
    """Calculate slippage buffer amount in dollars from basis points.

    This function converts a slippage tolerance expressed in basis points
    to a dollar amount based on the current price. The buffer can be used
    for transaction cost estimation or risk management calculations.

    Args:
        current_price (float): Current price of the security in dollars.
        slippage_bps (float): Slippage buffer in basis points.
            For example, 30 basis points = 0.3% = 30 bps.

    Returns:
        float: Slippage buffer amount in dollars.

    Example:
        >>> # Calculate 0.3% (30 bps) slippage on $100 stock
        >>> buffer = calculate_slippage_buffer(100.0, 30.0)
        >>> print(f"Slippage buffer: ${buffer}")
        Slippage buffer: $0.30

        >>> # Calculate 0.05% (5 bps) slippage on $50 stock
        >>> buffer = calculate_slippage_buffer(50.0, 5.0)
        >>> print(f"Slippage buffer: ${buffer}")
        Slippage buffer: $0.025

    Note:
        Basis points are 1/100th of a percent, so 100 bps = 1.0%.
        This is a common way to express small percentages in finance.

    """
    return current_price * (slippage_bps / 10000)


def calculate_allocation_discrepancy(
    target_weight: float, current_value: float, total_portfolio_value: float
) -> tuple[float, float]:
    """Calculate the discrepancy between target and current allocations.

    This function computes how far the current portfolio allocation deviates
    from the target allocation for a specific position. It returns both the
    current weight and the difference that needs to be corrected.

    Args:
        target_weight (float): Target allocation weight (0.0 to 1.0).
            For example, 0.3 represents 30% target allocation.
        current_value (float): Current position value in dollars.
            Can be a string that will be converted to float.
        total_portfolio_value (float): Total portfolio value in dollars.

    Returns:
        tuple[float, float]: A tuple containing:
            - current_weight: Current allocation as a fraction (0.0 to 1.0)
            - weight_difference: Target minus current weight (can be negative)

    Example:
        >>> # Current $3000 position, target 25%, total portfolio $10000
        >>> current_weight, diff = calculate_allocation_discrepancy(0.25, 3000, 10000)
        >>> print(f"Current: {current_weight:.1%}, Difference: {diff:+.1%}")
        Current: 30.0%, Difference: -5.0%

    Note:
        A positive weight_difference means the position is underweight
        and needs to be increased. A negative difference means the position
        is overweight and should be reduced.

    """
    if total_portfolio_value <= 0:
        return 0.0, target_weight

    # Ensure current_value is a float
    try:
        current_value = float(current_value)
    except (ValueError, TypeError):
        current_value = 0.0

    current_weight = current_value / total_portfolio_value
    weight_difference = target_weight - current_weight

    return current_weight, weight_difference


def calculate_allocation_discrepancy_decimal(
    target_weight: Decimal, current_value: Decimal, total_portfolio_value: Decimal
) -> tuple[Decimal, Decimal]:
    """Calculate allocation discrepancy using Decimal for financial precision.

    This function provides financial-grade precision for portfolio allocation
    calculations by using Decimal arithmetic throughout. Use this version for
    production trading where floating-point precision errors are unacceptable.

    Args:
        target_weight (Decimal): Target allocation weight (0.0 to 1.0).
            For example, Decimal('0.3') represents 30% target allocation.
        current_value (Decimal): Current position value in dollars.
        total_portfolio_value (Decimal): Total portfolio value in dollars.

    Returns:
        tuple[Decimal, Decimal]: A tuple containing:
            - current_weight: Current allocation as a fraction (0.0 to 1.0)
            - weight_difference: Target minus current weight (can be negative)

    Example:
        >>> from decimal import Decimal
        >>> # Current $3000 position, target 25%, total portfolio $10000
        >>> target = Decimal('0.25')
        >>> current = Decimal('3000.00')
        >>> portfolio = Decimal('10000.00')
        >>> current_weight, diff = calculate_allocation_discrepancy_decimal(
        ...     target, current, portfolio
        ... )
        >>> print(f"Current: {current_weight:.1%}, Difference: {diff:+.1%}")
        Current: 30.0%, Difference: -5.0%

    Note:
        This function uses Decimal arithmetic per guardrails for money calculations.
        A positive weight_difference means the position is underweight and needs
        to be increased. A negative difference means overweight and should be reduced.

    """
    if total_portfolio_value <= 0:
        return Decimal("0"), target_weight

    current_weight = current_value / total_portfolio_value
    weight_difference = target_weight - current_weight

    return current_weight, weight_difference
