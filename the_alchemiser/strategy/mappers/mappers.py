"""Business Unit: strategy | Status: current.

Consolidated mapping utilities for strategy module.

This module provides conversion functions for:
1. Market data mapping: conversion between typed domain models and DataFrame formats
2. Strategy signal mapping: conversion between different signal formats

Consolidates functionality from market_data_mapping.py and strategy_signal_mapping.py
to provide a single interface for all strategy mapping utilities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

import pandas as pd

from the_alchemiser.execution.orders.schemas import ValidatedOrderDTO
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.core_types import StrategySignal
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy.engines.value_objects.strategy_signal import (
    StrategySignal as TypedStrategySignal,
)
from the_alchemiser.strategy.registry.strategy_registry import StrategyType
from the_alchemiser.strategy.types.bar import BarModel

ActionLiteral = Literal["BUY", "SELL", "HOLD"]

# =============================================================================
# MARKET DATA MAPPING FUNCTIONS
# =============================================================================


def bars_to_dataframe(bars: list[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel domain objects to pandas DataFrame.

    Args:
        bars: List of BarModel domain objects

    Returns:
        DataFrame with OHLCV data indexed by timestamp

    """
    if not bars:
        return pd.DataFrame()

    data = []
    for bar in bars:
        data.append(
            {
                "Open": float(bar.open),
                "High": float(bar.high),
                "Low": float(bar.low),
                "Close": float(bar.close),
                "Volume": float(bar.volume),
            }
        )

    df = pd.DataFrame(data, index=[bar.ts for bar in bars])
    df.index.name = "timestamp"
    return df


def quote_to_tuple(quote: QuoteModel | None) -> tuple[float | None, float | None]:
    """Convert QuoteModel to tuple format for backward compatibility.

    Args:
        quote: QuoteModel domain object or None

    Returns:
        Tuple of (bid_price, ask_price), either can be None if quote unavailable

    """
    if quote is None:
        return (None, None)

    return (float(quote.bid), float(quote.ask))


def symbol_str_to_symbol(symbol: str) -> Symbol:
    """Convert string symbol to Symbol value object.

    Args:
        symbol: String symbol (e.g., "AAPL")

    Returns:
        Symbol value object

    """
    return Symbol(symbol)


def quote_to_current_price(quote: QuoteModel | None) -> float | None:
    """Extract current price from quote as mid-price.

    Args:
        quote: QuoteModel domain object or None

    Returns:
        Mid-price as float, or None if quote unavailable

    """
    if quote is None:
        return None

    return float(quote.mid)


def dataframe_to_bars(df: pd.DataFrame, symbol: Symbol) -> list[BarModel]:
    """Convert pandas DataFrame to list of BarModel objects.

    Args:
        df: DataFrame with OHLCV data indexed by timestamp
        symbol: Symbol value object (unused but kept for interface compatibility)

    Returns:
        List of BarModel domain objects

    """
    if df.empty:
        return []

    bars = []
    for timestamp, row in df.iterrows():
        bar = BarModel(
            ts=pd.to_datetime(timestamp),
            open=Decimal(str(row["Open"])),
            high=Decimal(str(row["High"])),
            low=Decimal(str(row["Low"])),
            close=Decimal(str(row["Close"])),
            volume=Decimal(str(row["Volume"])),
        )
        bars.append(bar)

    return bars


# =============================================================================
# STRATEGY SIGNAL MAPPING FUNCTIONS
# =============================================================================


def _normalize_action(value: Any) -> ActionLiteral:
    """Normalize action value to ActionLiteral.

    Private helper function for signal conversion.
    """
    try:
        s = str(value).upper()
        if s in {"BUY", "SELL", "HOLD"}:
            return s  # type: ignore[return-value]
        # Some strategies may return ActionType values
        if ".BUY" in s:
            return "BUY"
        if ".SELL" in s:
            return "SELL"
        if ".HOLD" in s:
            return "HOLD"
        return "HOLD"
    except Exception:
        return "HOLD"


def legacy_signal_to_typed(legacy: dict[str, Any]) -> StrategySignal:
    """Convert a legacy strategy signal dict to a typed StrategySignal.

    Expected legacy keys: symbol, action, reason or reasoning, optional confidence/allocation.
    """
    # Symbol can be a dict (portfolio); reduce to a label to keep StrategySignal simple
    raw_symbol = legacy.get("symbol")
    if isinstance(raw_symbol, dict):
        symbol = "PORTFOLIO"
    else:
        symbol = str(raw_symbol) if raw_symbol is not None else "N/A"

    action: ActionLiteral = _normalize_action(legacy.get("action"))

    # Support both legacy 'reason' and typed 'reasoning'
    reasoning = str(legacy.get("reason", legacy.get("reasoning", "")))

    # Optional confidence and allocation
    try:
        confidence = float(legacy.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0

    try:
        allocation_percentage = float(legacy.get("allocation_percentage", 0.0) or 0.0)
    except Exception:
        allocation_percentage = 0.0

    return StrategySignal(
        symbol=symbol,
        action=action,  # Literal["BUY","SELL","HOLD"]
        confidence=confidence,
        reasoning=reasoning,
        allocation_percentage=allocation_percentage,
    )


def map_signals_dict(
    legacy_signals: dict[StrategyType, dict[str, Any]],
) -> dict[StrategyType, StrategySignal]:
    """Map a dict of legacy signals keyed by StrategyType to typed signals."""
    return {k: legacy_signal_to_typed(v) for k, v in legacy_signals.items()}


def typed_dict_to_domain_signal(
    typed_dict_signal: StrategySignal,
) -> TypedStrategySignal:
    """Convert legacy TypedDict StrategySignal to new typed domain StrategySignal.

    Args:
        typed_dict_signal: Legacy StrategySignal (TypedDict) from domain.types

    Returns:
        New typed domain StrategySignal with value objects

    """
    from the_alchemiser.shared.types.percentage import Percentage
    from the_alchemiser.shared.value_objects.symbol import Symbol
    from the_alchemiser.strategy.engines.value_objects.confidence import Confidence

    # Extract symbol, handling special cases
    symbol_value = typed_dict_signal["symbol"]
    if isinstance(symbol_value, dict):
        # Portfolio case - use a shorter symbol that fits Symbol validation
        symbol_str = "PORT"  # 4 characters, within Symbol limit
    elif isinstance(symbol_value, str) and (
        "_PORTFOLIO" in symbol_value or "PORTFOLIO" in symbol_value
    ):
        # Handle portfolio string symbols (e.g., "NUCLEAR_PORTFOLIO", "BEAR_PORTFOLIO")
        symbol_str = "PORT"  # Use "PORT" as a placeholder for portfolio symbols
    else:
        symbol_str = str(symbol_value)

    # Convert action to proper format
    action = typed_dict_signal["action"]
    if isinstance(action, str):
        action = action.upper()
        if action not in ("BUY", "SELL", "HOLD"):
            action = "HOLD"  # Default fallback

    # Extract confidence (always present in StrategySignalBase)
    confidence_value: float = float(typed_dict_signal["confidence"])  # TypedDict field

    # Extract allocation percentage
    allocation_value: float = float(typed_dict_signal.get("allocation_percentage", 0.0))

    # Extract reasoning
    _reason_val = typed_dict_signal.get("reasoning", typed_dict_signal.get("reason", ""))
    reasoning: str = str(_reason_val) if _reason_val is not None else ""

    # Create the new typed domain signal
    return TypedStrategySignal(
        symbol=Symbol(symbol_str),
        action=action,  # type: ignore[arg-type]  # We validated above
        confidence=Confidence(Decimal(str(confidence_value))),
        target_allocation=Percentage(
            Decimal(str(allocation_value / 100.0))
            if allocation_value > 1
            else Decimal(str(allocation_value))
        ),
        reasoning=reasoning,
    )


def convert_signals_dict_to_domain(
    legacy_signals_dict: dict[StrategyType, StrategySignal],
) -> dict[StrategyType, TypedStrategySignal]:
    """Convert dict of legacy TypedDict signals to new typed domain signals."""
    return {k: typed_dict_to_domain_signal(v) for k, v in legacy_signals_dict.items()}


def typed_strategy_signal_to_validated_order(
    signal: TypedStrategySignal,
    portfolio_value: Decimal,
    order_type: Literal["market", "limit"] = "market",
    time_in_force: Literal["day", "gtc", "ioc", "fok"] = "day",
    limit_price: Decimal | None = None,
    client_order_id: str | None = None,
) -> ValidatedOrderDTO:
    """Convert typed domain StrategySignal to ValidatedOrderDTO.

    Args:
        signal: Typed domain StrategySignal with value objects
        portfolio_value: Total portfolio value for quantity calculation
        order_type: Order type (market or limit)
        time_in_force: Time in force specification
        limit_price: Limit price for limit orders
        client_order_id: Optional client order ID

    Returns:
        ValidatedOrderDTO instance ready for order execution

    Raises:
        ValueError: If signal action is HOLD or other invalid states
        ValueError: If limit order without limit_price

    """
    # Handle HOLD signals - these should not generate orders
    if signal.action == "HOLD":
        raise ValueError("HOLD signals cannot be converted to orders")

    # Convert action from strategy signal to order side with proper typing
    side: Literal["buy", "sell"]
    if signal.action == "BUY":
        side = "buy"
    elif signal.action == "SELL":
        side = "sell"
    else:
        raise ValueError(f"Invalid signal action: {signal.action}")

    # Calculate quantity from target allocation and portfolio value
    # target_allocation is Percentage (0.0 to 1.0), portfolio_value is Decimal
    allocation_value = portfolio_value * signal.target_allocation.value

    # For now, use allocation_value as quantity (dollar amount)
    # In a real implementation, this might need current stock price to convert to shares
    quantity = allocation_value

    # Validate minimum quantity
    if quantity <= Decimal("0"):
        raise ValueError(f"Calculated quantity must be positive, got: {quantity}")

    # Validate limit price requirement
    if order_type == "limit" and limit_price is None:
        raise ValueError("Limit price required for limit orders")

    # Create ValidatedOrderDTO
    return ValidatedOrderDTO(
        symbol=signal.symbol.value,
        side=side,
        quantity=quantity,
        order_type=order_type,
        time_in_force=time_in_force,
        limit_price=limit_price,
        client_order_id=client_order_id,
        # Derived validation fields
        estimated_value=allocation_value,
        is_fractional=False,  # For now, assume whole dollar amounts
        normalized_quantity=quantity,
        risk_score=Decimal("1.0") - signal.confidence.value,  # Higher confidence = lower risk
        validation_timestamp=datetime.now(UTC),
    )
