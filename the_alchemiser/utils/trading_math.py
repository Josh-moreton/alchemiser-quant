#!/usr/bin/env python3
"""
Trading Math Utilities.

Contains pure mathematical functions for trading calculations, such as position sizing,
dynamic limit price calculation, slippage buffer, and allocation discrepancy analysis.
All functions are side-effect free and unit-testable.
"""

import logging
from typing import Optional


def calculate_position_size(
    current_price: float, 
    portfolio_weight: float, 
    account_value: float
) -> float:
    """
    Calculate position size based on portfolio weight (fractional shares supported).
    
    This is a pure function with no side effects, making it easy to unit test.
    
    Args:
        current_price: Current price per share
        portfolio_weight: Target weight (0.0 to 1.0)
        account_value: Total account value
        
    Returns:
        Number of shares to buy/sell (float for fractional shares)
    """
    if current_price <= 0:
        return 0.0
        
    # Calculate target dollar amount based on strategy allocation of full account value
    target_value = account_value * portfolio_weight
    
    # Calculate shares (fractional)
    shares = round(target_value / current_price, 6)  # 6 decimals is safe for Alpaca
    
    return shares


def calculate_dynamic_limit_price(
    side_is_buy: bool,
    bid: float,
    ask: float,
    step: int = 0,
    tick_size: float = 0.01,
    max_steps: int = 5,
) -> float:
    """
    Calculate a limit price using a dynamic pegging strategy.
    
    The strategy starts near the bid/ask midpoint and progressively moves
    toward the market on each retry attempt. This is a pure function version
    of the OrderManager method.
    
    Args:
        side_is_buy: True for buy orders, False for sell orders
        bid: Current bid price
        ask: Current ask price
        step: Current retry step (0 = first attempt)
        tick_size: Price increment for each step
        max_steps: Maximum number of steps before using market price
        
    Returns:
        Calculated limit price rounded to 2 decimal places
    """
    if bid > 0 and ask > 0:
        mid = (bid + ask) / 2
    else:
        mid = bid if side_is_buy else ask

    if step > max_steps:
        return round(ask if side_is_buy else bid, 2)

    if side_is_buy:
        price = min(mid + step * tick_size, ask if ask > 0 else mid)
    else:
        price = max(mid - step * tick_size, bid if bid > 0 else mid)

    return round(price, 2)


def calculate_slippage_buffer(current_price: float, slippage_bps: float) -> float:
    """
    Calculate slippage buffer amount based on current price and basis points.
    
    Args:
        current_price: Current price of the security
        slippage_bps: Slippage buffer in basis points (e.g., 30 = 0.3%)
        
    Returns:
        Slippage buffer amount in dollars
    """
    return current_price * (slippage_bps / 10000)


def calculate_allocation_discrepancy(
    target_weight: float, 
    current_value: float, 
    total_portfolio_value: float
) -> tuple[float, float]:
    """
    Calculate the discrepancy between target and current allocations.
    
    Args:
        target_weight: Target allocation weight (0.0 to 1.0)
        current_value: Current position value in dollars
        total_portfolio_value: Total portfolio value in dollars
        
    Returns:
        Tuple of (current_weight, weight_difference)
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


def calculate_rebalance_amounts(
    target_weights: dict[str, float],
    current_values: dict[str, float],
    total_portfolio_value: float,
    min_trade_threshold: float = 0.01  # 1% minimum threshold for trades
) -> dict[str, dict]:
    """
    Calculate rebalancing amounts for all positions.
    
    Args:
        target_weights: Dictionary of symbol -> target weight
        current_values: Dictionary of symbol -> current value
        total_portfolio_value: Total portfolio value
        min_trade_threshold: Minimum weight difference to trigger trade
        
    Returns:
        Dictionary of symbol -> {
            'current_weight': float,
            'target_weight': float, 
            'weight_diff': float,
            'target_value': float,
            'current_value': float,
            'trade_amount': float,
            'needs_rebalance': bool
        }
    """
    rebalance_plan = {}
    
    # Get all symbols from both target and current positions
    all_symbols = set(target_weights.keys()) | set(current_values.keys())
    
    for symbol in all_symbols:
        target_weight = target_weights.get(symbol, 0.0)
        current_value = current_values.get(symbol, 0.0)
        
        # Ensure current_value is a float
        try:
            current_value = float(current_value)
        except (ValueError, TypeError):
            current_value = 0.0
        
        current_weight, weight_diff = calculate_allocation_discrepancy(
            target_weight, current_value, total_portfolio_value
        )
        
        target_value = total_portfolio_value * target_weight
        trade_amount = target_value - current_value
        needs_rebalance = abs(weight_diff) >= min_trade_threshold
        
        rebalance_plan[symbol] = {
            'current_weight': current_weight,
            'target_weight': target_weight,
            'weight_diff': weight_diff,
            'target_value': target_value,
            'current_value': current_value,
            'trade_amount': trade_amount,
            'needs_rebalance': needs_rebalance
        }
    
    return rebalance_plan
