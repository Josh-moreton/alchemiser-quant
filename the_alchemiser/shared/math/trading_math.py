#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trading Math Utilities for The Alchemiser Quantitative Trading System.

This module contains pure mathematical functions for trading calculations,
including position sizing, dynamic limit price calculation, slippage calculations,
and portfolio rebalancing mathematics. All functions are side-effect free,
making them easy to unit test and reason about.

The module provides the mathematical foundation for:
- Position sizing based on portfolio weights
- Dynamic limit order pricing strategies
- Slippage and transaction cost calculations
- Portfolio allocation and rebalancing logic

All functions follow functional programming principles with no side effects,
ensuring predictable behavior and easy testing.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Note: Phase 12 - Types earmarked for future migration to structured trading calculations
# from the_alchemiser.shared.value_objects.core_types import BacktestResult, PerformanceMetrics, TradeAnalysis


@dataclass(frozen=True)
class ThresholdAnalysisData:
    """Data container for threshold analysis logging.

    Reduces parameter count from 11 to 1 for _log_enhanced_threshold_analysis.
    """

    symbol: str
    target_weight: float
    current_value: float
    total_portfolio_value: float
    target_value: float
    trade_amount: float
    weight_diff: float
    current_weight: float
    min_trade_threshold: float
    needs_rebalance: bool


@dataclass(frozen=True)
class BugDetectionData:
    """Data container for critical bug detection logging.

    Reduces parameter count from 9 to 1 for _log_critical_bug_detection.
    """

    symbol: str
    target_weight: float
    weight_diff: float
    needs_rebalance: bool
    trade_amount: float
    target_value: float
    current_value: float
    total_portfolio_value: float


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


def _log_enhanced_threshold_analysis(
    data: ThresholdAnalysisData,
    logger: logging.Logger,
) -> None:
    """Log enhanced threshold analysis for debugging.

    Args:
        data: Threshold analysis data container
        logger: Logger instance

    """
    logger.info(f"=== ENHANCED THRESHOLD ANALYSIS: {data.symbol} ===")
    logger.info(f"TARGET_WEIGHT_RAW: {data.target_weight}")
    logger.info(f"CURRENT_VALUE_RAW: {data.current_value}")
    logger.info(f"TOTAL_PORTFOLIO_VALUE_RAW: {data.total_portfolio_value}")
    logger.info(f"CALCULATED_TARGET_VALUE: ${data.target_value}")
    logger.info(f"CALCULATED_TRADE_AMOUNT: ${data.trade_amount}")
    logger.info(f"WEIGHT_DIFF_ABS: {abs(data.weight_diff)}")
    logger.info(f"MIN_TRADE_THRESHOLD: {data.min_trade_threshold}")
    logger.info(
        f"THRESHOLD_CHECK_RESULT: {abs(data.weight_diff)} >= {data.min_trade_threshold} = {data.needs_rebalance}"
    )

    # Show percentage calculations for clarity
    logger.info(f"CURRENT_WEIGHT_PERCENT: {data.current_weight * 100:.3f}%")
    logger.info(f"TARGET_WEIGHT_PERCENT: {data.target_weight * 100:.3f}%")
    logger.info(f"WEIGHT_DIFF_PERCENT: {data.weight_diff * 100:.3f}%")
    logger.info(f"THRESHOLD_PERCENT: {data.min_trade_threshold * 100:.3f}%")

    # Calculate what the portfolio value should be based on current holdings
    if data.current_value > 0 and data.target_weight > 0:
        implied_portfolio_value = data.current_value / data.target_weight
        logger.info(f"IMPLIED_PORTFOLIO_VALUE_FROM_{data.symbol}: ${implied_portfolio_value:.2f}")

    # Flag potential data issues
    if data.total_portfolio_value <= 0:
        logger.error(f"❌ INVALID_PORTFOLIO_VALUE: {data.total_portfolio_value}")
    if data.current_value < 0:
        logger.error(f"❌ NEGATIVE_CURRENT_VALUE_{data.symbol}: {data.current_value}")
    if data.target_weight < 0 or data.target_weight > 1:
        logger.error(f"❌ INVALID_TARGET_WEIGHT_{data.symbol}: {data.target_weight}")

    # Additional debug info for threshold failures
    if not data.needs_rebalance and abs(data.weight_diff) > 0:
        logger.warning(
            f"⚠️ {data.symbol}_BELOW_THRESHOLD: Need {abs(data.weight_diff) * 100:.3f}% change but threshold is {data.min_trade_threshold * 100:.3f}%"
        )
    elif data.needs_rebalance:
        logger.info(
            f"✅ {data.symbol}_ABOVE_THRESHOLD: Need {abs(data.weight_diff) * 100:.3f}% change, threshold is {data.min_trade_threshold * 100:.3f}%"
        )


def _log_critical_bug_detection(
    data: BugDetectionData,
    logger: logging.Logger,
) -> None:
    """Log critical bug detection for debugging trade calculation issues.

    Args:
        data: Bug detection data container
        logger: Logger instance

    """
    # Detect potential critical bugs that would cause trade loss
    if data.target_weight > 0.01 and abs(data.weight_diff) > 0.05 and not data.needs_rebalance:
        logger.error(
            f"🚨 CRITICAL_BUG_DETECTED_{data.symbol}: Large target weight ({data.target_weight * 100:.1f}%) with large diff ({abs(data.weight_diff) * 100:.1f}%) but needs_rebalance=False"
        )
        logger.error("🚨 This indicates a threshold calculation bug that will cause trade loss")

    if math.isclose(data.trade_amount, 0.0, abs_tol=1e-10) and data.target_weight > 0.01:
        logger.error(
            f"🚨 ZERO_TRADE_AMOUNT_BUG_{data.symbol}: Target weight {data.target_weight * 100:.1f}% but trade_amount=0"
        )
        logger.error(
            f"🚨 This suggests target_value ({data.target_value}) equals current_value ({data.current_value})"
        )

    # CRITICAL: Detect the portfolio value = 0 bug that causes all trade_amounts to be 0
    if data.total_portfolio_value <= 0.0 and data.needs_rebalance:
        logger.error(
            f"🚨 ZERO_PORTFOLIO_VALUE_CAUSES_ZERO_TRADES_{data.symbol}: portfolio_value={data.total_portfolio_value}, needs_rebalance={data.needs_rebalance}, trade_amount={data.trade_amount}"
        )
        logger.error(
            "🚨 ROOT CAUSE: Portfolio value is 0 or negative, making all trades impossible"
        )
        logger.error(
            "🚨 FIX: Ensure portfolio value reflects cash balance for fresh accounts or fix API data fetching"
        )

    # Use math.isclose for float comparison per guardrails (no == on floats)
    if math.isclose(data.total_portfolio_value, 0.0, abs_tol=1e-10) and data.target_weight > 0:
        logger.error(
            "🚨 ZERO_PORTFOLIO_VALUE_BUG: Cannot calculate trades with zero portfolio value"
        )


def _log_rebalance_summary(
    all_symbols: set[str],
    symbols_needing_rebalance: int,
    min_trade_threshold: float,
    total_portfolio_value: float,
    rebalance_plan: dict[str, dict[str, float]],
    logger: logging.Logger,
) -> None:
    """Log comprehensive summary of rebalancing calculation results.

    Args:
        all_symbols: Set of all symbols processed
        symbols_needing_rebalance: Count of symbols requiring rebalancing
        min_trade_threshold: Threshold used for rebalancing decisions
        total_portfolio_value: Total portfolio value
        rebalance_plan: Complete rebalancing plan
        logger: Logger instance

    """
    # Add comprehensive summary logging
    logger.info("=== REBALANCE CALCULATION SUMMARY ===")
    logger.info(f"Total symbols processed: {len(all_symbols)}")
    logger.info(f"Symbols needing rebalance: {symbols_needing_rebalance}")
    logger.info(f"Symbols NOT needing rebalance: {len(all_symbols) - symbols_needing_rebalance}")
    logger.info(f"Threshold used: {min_trade_threshold:.4f} ({min_trade_threshold * 100:.1f}%)")
    logger.info(f"Portfolio value: ${total_portfolio_value:,.2f}")

    # Log which symbols need rebalancing
    symbols_to_rebalance = [
        symbol for symbol, plan in rebalance_plan.items() if plan["needs_rebalance"]
    ]
    symbols_to_skip = [
        symbol for symbol, plan in rebalance_plan.items() if not plan["needs_rebalance"]
    ]

    if symbols_to_rebalance:
        logger.info(f"Symbols TO REBALANCE: {symbols_to_rebalance}")
    else:
        logger.warning(
            "NO SYMBOLS NEED REBALANCING - portfolio already balanced or all diffs below threshold"
        )

    if symbols_to_skip:
        logger.info(f"Symbols to SKIP (below threshold): {symbols_to_skip}")

    logger.debug(
        f"Rebalance calculation complete: {symbols_needing_rebalance}/{len(all_symbols)} symbols need rebalancing"
    )


def _process_symbol_rebalance(
    symbol: str,
    target_weights: dict[str, float],
    current_values: dict[str, float],
    total_portfolio_value: float,
    min_trade_threshold: float,
    logger: logging.Logger,
) -> tuple[dict[str, float], bool]:
    """Process rebalancing calculation for a single symbol.

    Args:
        symbol: Trading symbol to process
        target_weights: Dictionary of target weights
        current_values: Dictionary of current values
        total_portfolio_value: Total portfolio value
        min_trade_threshold: Minimum threshold for rebalancing
        logger: Logger instance

    Returns:
        Tuple of (symbol_plan, needs_rebalance)

    """
    logger.info(f"=== PROCESSING SYMBOL: {symbol} ===")

    target_weight = target_weights.get(symbol, 0.0)
    current_value = current_values.get(symbol, 0.0)

    logger.info(f"SYMBOL_TARGET_WEIGHT: {target_weight}")
    logger.info(f"SYMBOL_CURRENT_VALUE: {current_value}")

    # Ensure current_value is a float
    try:
        current_value = float(current_value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid current_value for {symbol}: {current_value}, using 0.0")
        current_value = 0.0

    current_weight, weight_diff = calculate_allocation_discrepancy(
        target_weight, current_value, total_portfolio_value
    )

    logger.info(f"CALCULATED_CURRENT_WEIGHT: {current_weight}")
    logger.info(f"CALCULATED_WEIGHT_DIFF: {weight_diff}")

    # Apply cash reserve to avoid buying power issues with broker constraints
    # This ensures we don't try to use 100% of portfolio value which can
    # exceed available buying power
    settings = load_settings()
    usage_multiplier = 1.0 - settings.alpaca.cash_reserve_pct
    effective_portfolio_value = total_portfolio_value * usage_multiplier
    target_value = effective_portfolio_value * target_weight
    trade_amount = target_value - current_value
    needs_rebalance = abs(weight_diff) >= min_trade_threshold

    # Enhanced threshold analysis for debugging
    threshold_data = ThresholdAnalysisData(
        symbol=symbol,
        target_weight=target_weight,
        current_value=current_value,
        total_portfolio_value=total_portfolio_value,
        target_value=target_value,
        trade_amount=trade_amount,
        weight_diff=weight_diff,
        current_weight=current_weight,
        min_trade_threshold=min_trade_threshold,
        needs_rebalance=needs_rebalance,
    )
    _log_enhanced_threshold_analysis(threshold_data, logger)

    # Critical bug detection
    bug_data = BugDetectionData(
        symbol=symbol,
        target_weight=target_weight,
        weight_diff=weight_diff,
        needs_rebalance=needs_rebalance,
        trade_amount=trade_amount,
        target_value=target_value,
        current_value=current_value,
        total_portfolio_value=total_portfolio_value,
    )
    _log_critical_bug_detection(bug_data, logger)

    logger.info(f"CALCULATED_TARGET_VALUE: ${target_value}")
    logger.info(f"CALCULATED_TRADE_AMOUNT: ${trade_amount}")
    logger.info(f"WEIGHT_DIFF_ABS: {abs(weight_diff)}")
    logger.info(f"THRESHOLD_CHECK: {abs(weight_diff)} >= {min_trade_threshold} = {needs_rebalance}")

    # Add detailed threshold logging for all symbols (using debug level for verbose output)
    logger.debug(f"=== THRESHOLD CHECK: {symbol} ===")
    logger.debug(
        f"{symbol}: Current {current_weight:.3f}% ({current_weight * 100:.1f}%), Target {target_weight:.3f}% ({target_weight * 100:.1f}%)"
    )
    logger.debug(f"{symbol}: Weight difference {weight_diff:.3f}% ({weight_diff * 100:.1f}%)")
    logger.debug(
        f"{symbol}: Threshold {min_trade_threshold:.3f}% ({min_trade_threshold * 100:.1f}%)"
    )
    logger.debug(
        f"{symbol}: Needs rebalance: {needs_rebalance} (diff {abs(weight_diff):.6f} {'≥' if needs_rebalance else '<'} threshold {min_trade_threshold:.6f})"
    )
    logger.debug(f"{symbol}: Trade amount: ${trade_amount:.2f}")

    if needs_rebalance:
        logger.info(f"{symbol}: ✅ TRADE REQUIRED - will be included in rebalancing plan")
    else:
        logger.debug(f"{symbol}: ❌ NO TRADE NEEDED - below threshold")

    # Check if logger supports isEnabledFor (standard logging) or is_enabled_for (structlog)
    if (hasattr(logger, "isEnabledFor") and logger.isEnabledFor(logging.DEBUG)) or (
        hasattr(logger, "is_enabled_for") and logger.is_enabled_for(logging.DEBUG)
    ):
        logger.debug(
            f"Symbol {symbol}: weight_diff={weight_diff:.4f}, "
            f"threshold={min_trade_threshold:.4f}, needs_rebalance={needs_rebalance}"
        )

    symbol_plan = {
        "current_weight": current_weight,
        "target_weight": target_weight,
        "weight_diff": weight_diff,
        "target_value": target_value,
        "current_value": current_value,
        "trade_amount": trade_amount,
        "needs_rebalance": needs_rebalance,
    }

    logger.info(f"SYMBOL_PLAN_CREATED: {symbol} -> {symbol_plan}")

    return symbol_plan, needs_rebalance


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


def calculate_rebalance_amounts(
    target_weights: dict[str, float],
    current_values: dict[str, float],
    total_portfolio_value: float,
    min_trade_threshold: float = 0.001,  # 0.1% minimum threshold for trades
) -> dict[str, dict[str, float]]:
    """Calculate comprehensive rebalancing plan for all portfolio positions.

    This function analyzes the entire portfolio and calculates the specific
    trades needed to rebalance from current allocations to target allocations.
    It provides detailed information for each position including whether
    rebalancing is needed based on the minimum threshold.

    Args:
        target_weights (dict[str, float]): Dictionary mapping symbols to
            target weights (0.0 to 1.0). Example: {'AAPL': 0.3, 'MSFT': 0.2}
        current_values (dict[str, float]): Dictionary mapping symbols to
            current position values in dollars.
        total_portfolio_value (float): Total portfolio value in dollars.
        min_trade_threshold (float, optional): Minimum weight difference
            to trigger a rebalancing trade. Defaults to 0.001 (0.1%).

    Returns:
        dict[str, dict]: Dictionary mapping each symbol to a detailed
            rebalancing plan with the following structure:
            {
                'current_weight': float,     # Current allocation (0.0-1.0)
                'target_weight': float,      # Target allocation (0.0-1.0)
                'weight_diff': float,        # Difference (target - current)
                'target_value': float,       # Target dollar value
                'current_value': float,      # Current dollar value
                'trade_amount': float,       # Dollar amount to trade (+ = buy, - = sell)
                'needs_rebalance': bool      # Whether trade exceeds threshold
            }

    Example:
        >>> target = {'AAPL': 0.5, 'MSFT': 0.3, 'CASH': 0.2}
        >>> current = {'AAPL': 4000, 'MSFT': 4000, 'CASH': 2000}
        >>> plan = calculate_rebalance_amounts(target, current, 10000)
        >>> for symbol, details in plan.items():
        ...     if details['needs_rebalance']:
        ...         action = "BUY" if details['trade_amount'] > 0 else "SELL"
        ...         print(f"{symbol}: {action} ${abs(details['trade_amount']):.0f}")
        MSFT: SELL $1000

    Note:
        The function handles symbols that exist in either target_weights or
        current_values but not both. Missing positions are treated as 0.0.

    """
    logger = get_logger(__name__)

    # === TRADING_MATH ENTRY POINT LOGGING ===
    logger.info("=== TRADING_MATH: CALCULATE_REBALANCE_AMOUNTS ===")
    logger.info("MATH_FUNCTION_ENTRY")
    logger.info(f"RECEIVED_TARGET_WEIGHTS: {target_weights}")
    logger.info(f"RECEIVED_CURRENT_VALUES: {current_values}")
    logger.info(f"RECEIVED_PORTFOLIO_VALUE: {total_portfolio_value}")
    logger.info(f"RECEIVED_THRESHOLD: {min_trade_threshold}")

    # Validate inputs
    if not target_weights:
        logger.error("❌ TRADING_MATH_RECEIVED_EMPTY_TARGET_WEIGHTS")
        return {}

    if total_portfolio_value <= 0:
        logger.error(f"❌ TRADING_MATH_RECEIVED_INVALID_PORTFOLIO_VALUE: {total_portfolio_value}")
        return {}

    rebalance_plan = {}

    # Get all symbols from both target and current positions
    all_symbols = set(target_weights.keys()) | set(current_values.keys())
    logger.info(f"ALL_SYMBOLS_TO_PROCESS: {all_symbols}")

    symbols_needing_rebalance = 0

    for symbol in all_symbols:
        symbol_plan, needs_rebalance = _process_symbol_rebalance(
            symbol,
            target_weights,
            current_values,
            total_portfolio_value,
            min_trade_threshold,
            logger,
        )

        rebalance_plan[symbol] = symbol_plan

        if needs_rebalance:
            symbols_needing_rebalance += 1

    # Log comprehensive summary
    _log_rebalance_summary(
        all_symbols,
        symbols_needing_rebalance,
        min_trade_threshold,
        total_portfolio_value,
        rebalance_plan,
        logger,
    )

    return rebalance_plan


def calculate_rebalance_amounts_decimal(
    target_weights: dict[str, Decimal],
    current_values: dict[str, Decimal],
    total_portfolio_value: Decimal,
    min_trade_threshold: Decimal = Decimal("0.001"),  # 0.1% minimum threshold
) -> dict[str, dict[str, Decimal]]:
    """Calculate comprehensive rebalancing plan using Decimal for financial precision.

    This function provides financial-grade precision for portfolio rebalancing
    calculations by using Decimal arithmetic throughout. Use this version for
    production trading where floating-point precision errors are unacceptable.

    Args:
        target_weights (dict[str, Decimal]): Dictionary mapping symbols to
            target weights (0.0 to 1.0). Example: {'AAPL': Decimal('0.3')}
        current_values (dict[str, Decimal]): Dictionary mapping symbols to
            current position values in dollars.
        total_portfolio_value (Decimal): Total portfolio value in dollars.
        min_trade_threshold (Decimal, optional): Minimum weight difference
            to trigger a rebalancing trade. Defaults to Decimal('0.001') (0.1%).

    Returns:
        dict[str, dict]: Dictionary mapping each symbol to a detailed
            rebalancing plan with the following structure:
            {
                'current_weight': Decimal,     # Current allocation (0.0-1.0)
                'target_weight': Decimal,      # Target allocation (0.0-1.0)
                'weight_diff': Decimal,        # Difference (target - current)
                'target_value': Decimal,       # Target dollar value
                'current_value': Decimal,      # Current dollar value
                'trade_amount': Decimal,       # Dollar amount to trade (+ = buy, - = sell)
                'needs_rebalance': bool        # Whether trade exceeds threshold
            }

    Example:
        >>> from decimal import Decimal
        >>> target = {'AAPL': Decimal('0.5'), 'MSFT': Decimal('0.3')}
        >>> current = {'AAPL': Decimal('4000'), 'MSFT': Decimal('4000')}
        >>> plan = calculate_rebalance_amounts_decimal(
        ...     target, current, Decimal('10000')
        ... )
        >>> for symbol, details in plan.items():
        ...     if details['needs_rebalance']:
        ...         action = "BUY" if details['trade_amount'] > 0 else "SELL"
        ...         print(f"{symbol}: {action} ${abs(details['trade_amount']):.0f}")
        AAPL: BUY $1000
        MSFT: SELL $1000

    Note:
        This function uses Decimal arithmetic per guardrails for money calculations.
        The function handles symbols that exist in either target_weights or
        current_values but not both. Missing positions are treated as Decimal('0').

    """
    logger = get_logger(__name__)

    # === TRADING_MATH ENTRY POINT LOGGING ===
    logger.info("=== TRADING_MATH: CALCULATE_REBALANCE_AMOUNTS_DECIMAL ===")
    logger.info("MATH_FUNCTION_ENTRY")
    logger.info(f"RECEIVED_TARGET_WEIGHTS: {target_weights}")
    logger.info(f"RECEIVED_CURRENT_VALUES: {current_values}")
    logger.info(f"RECEIVED_PORTFOLIO_VALUE: {total_portfolio_value}")
    logger.info(f"RECEIVED_THRESHOLD: {min_trade_threshold}")

    # Validate inputs
    if not target_weights:
        logger.error("❌ TRADING_MATH_RECEIVED_EMPTY_TARGET_WEIGHTS")
        return {}

    if total_portfolio_value <= 0:
        logger.error(f"❌ TRADING_MATH_RECEIVED_INVALID_PORTFOLIO_VALUE: {total_portfolio_value}")
        return {}

    rebalance_plan = {}

    # Get all symbols from both target and current positions
    all_symbols = set(target_weights.keys()) | set(current_values.keys())
    logger.info(f"ALL_SYMBOLS_TO_PROCESS: {all_symbols}")

    symbols_needing_rebalance = 0

    # Apply cash reserve to avoid buying power issues
    settings = load_settings()
    usage_multiplier = Decimal(str(1.0 - settings.alpaca.cash_reserve_pct))
    effective_portfolio_value = total_portfolio_value * usage_multiplier

    for symbol in all_symbols:
        target_weight = target_weights.get(symbol, Decimal("0"))
        current_value = current_values.get(symbol, Decimal("0"))

        # Calculate using Decimal precision
        current_weight, weight_diff = calculate_allocation_discrepancy_decimal(
            target_weight, current_value, total_portfolio_value
        )

        target_value = effective_portfolio_value * target_weight
        trade_amount = target_value - current_value
        needs_rebalance = abs(weight_diff) >= min_trade_threshold

        symbol_plan: dict[str, Decimal] = {
            "current_weight": current_weight,
            "target_weight": target_weight,
            "weight_diff": weight_diff,
            "target_value": target_value,
            "current_value": current_value,
            "trade_amount": trade_amount,
            "needs_rebalance": Decimal("1") if needs_rebalance else Decimal("0"),
        }

        rebalance_plan[symbol] = symbol_plan

        if needs_rebalance:
            symbols_needing_rebalance += 1

    # Log summary
    logger.info("=== REBALANCE CALCULATION SUMMARY (DECIMAL) ===")
    logger.info(f"Total symbols processed: {len(all_symbols)}")
    logger.info(f"Symbols needing rebalance: {symbols_needing_rebalance}")
    logger.info(f"Portfolio value: ${total_portfolio_value}")

    return rebalance_plan
