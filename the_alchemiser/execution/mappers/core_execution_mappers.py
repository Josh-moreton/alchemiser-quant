"""Business Unit: execution | Status: current.

Consolidated core execution and account mapping utilities.

This module consolidates core execution functionality including:
- Execution mapping utilities (anti-corruption layer)
- Account data mapping and Money type conversions
- Precision handling for financial calculations
- DTO boundary mappings

Consolidates execution.py and account_mapping.py for better maintainability.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.utils.timezone_utils import normalize_timestamp_to_utc, to_iso_string

# Account Mapping Section


def to_money_usd(value: str | float | int | Decimal | None) -> Money | None:
    """Map raw numeric portfolio value to Money(USD).

    Returns None if value is None or not coercible.
    """
    if value is None:
        return None
    try:
        dec = Decimal(str(value))
    except Exception:
        return None
    return Money(dec, "USD")


@dataclass(frozen=True)
class AccountMetrics:
    """Calculated account metrics for risk analysis."""

    cash_ratio: Decimal
    market_exposure: Decimal
    leverage_ratio: Decimal | None
    available_buying_power_ratio: Decimal


@dataclass(frozen=True)
class AccountSummaryTyped:
    """Typed account summary with strongly typed fields."""

    account_id: str
    equity: Money
    cash: Money
    market_value: Money
    buying_power: Money
    last_equity: Money
    day_trade_count: int
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    calculated_metrics: AccountMetrics


def account_summary_to_typed(account_data: dict[str, Any]) -> AccountSummaryTyped:
    """Convert raw account dictionary to typed AccountSummaryTyped.

    Args:
        account_data: Raw account data from broker

    Returns:
        AccountSummaryTyped with Money objects and calculated metrics

    """
    # Extract basic account fields
    account_id = str(account_data.get("account_id", "unknown"))
    equity = to_money_usd(account_data.get("equity", 0)) or Money(Decimal("0"), "USD")
    cash = to_money_usd(account_data.get("cash", 0)) or Money(Decimal("0"), "USD")
    market_value = to_money_usd(account_data.get("market_value", 0)) or Money(Decimal("0"), "USD")
    buying_power = to_money_usd(account_data.get("buying_power", 0)) or Money(Decimal("0"), "USD")
    last_equity = to_money_usd(account_data.get("last_equity", 0)) or Money(Decimal("0"), "USD")

    # Extract boolean flags
    day_trade_count = int(account_data.get("day_trade_count", 0))
    pattern_day_trader = bool(account_data.get("pattern_day_trader", False))
    trading_blocked = bool(account_data.get("trading_blocked", False))
    transfers_blocked = bool(account_data.get("transfers_blocked", False))
    account_blocked = bool(account_data.get("account_blocked", False))

    # Calculate metrics
    cash_ratio = Decimal("0")
    market_exposure = Decimal("0")
    leverage_ratio = None
    available_buying_power_ratio = Decimal("0")

    if equity.amount > 0:
        cash_ratio = cash.amount / equity.amount
        market_exposure = market_value.amount / equity.amount
        available_buying_power_ratio = buying_power.amount / equity.amount

        # Calculate leverage if market value > 0
        if market_value.amount > 0:
            leverage_ratio = market_value.amount / cash.amount if cash.amount > 0 else None

    calculated_metrics = AccountMetrics(
        cash_ratio=cash_ratio,
        market_exposure=market_exposure,
        leverage_ratio=leverage_ratio,
        available_buying_power_ratio=available_buying_power_ratio,
    )

    return AccountSummaryTyped(
        account_id=account_id,
        equity=equity,
        cash=cash,
        market_value=market_value,
        buying_power=buying_power,
        last_equity=last_equity,
        day_trade_count=day_trade_count,
        pattern_day_trader=pattern_day_trader,
        trading_blocked=trading_blocked,
        transfers_blocked=transfers_blocked,
        account_blocked=account_blocked,
        calculated_metrics=calculated_metrics,
    )


def account_typed_to_serializable(account: AccountSummaryTyped) -> dict[str, Any]:
    """Convert typed account summary to serializable dictionary.

    Args:
        account: Typed account summary

    Returns:
        Dictionary with Money objects converted to Decimal values

    """
    return {
        "account_id": account.account_id,
        "equity": account.equity.amount,
        "cash": account.cash.amount,
        "market_value": account.market_value.amount,
        "buying_power": account.buying_power.amount,
        "last_equity": account.last_equity.amount,
        "day_trade_count": account.day_trade_count,
        "pattern_day_trader": account.pattern_day_trader,
        "trading_blocked": account.trading_blocked,
        "transfers_blocked": account.transfers_blocked,
        "account_blocked": account.account_blocked,
        "calculated_metrics": {
            "cash_ratio": account.calculated_metrics.cash_ratio,
            "market_exposure": account.calculated_metrics.market_exposure,
            "leverage_ratio": account.calculated_metrics.leverage_ratio,
            "available_buying_power_ratio": account.calculated_metrics.available_buying_power_ratio,
        },
    }


# Execution Mapping Section


def normalize_timestamp_str(timestamp: Any) -> str:
    """Normalize timestamp to ISO 8601 string with timezone awareness.

    Args:
        timestamp: Timestamp in various formats

    Returns:
        ISO 8601 formatted timestamp string

    """
    if timestamp is None:
        return datetime.now(UTC).isoformat()

    # Use centralized timezone normalization
    try:
        normalized_dt = normalize_timestamp_to_utc(timestamp)
        return to_iso_string(normalized_dt)
    except Exception:
        # Ultimate fallback to current time
        return datetime.now(UTC).isoformat()


def normalize_decimal_precision(
    value: Any, precision: int = 2, rounding: str = ROUND_HALF_UP
) -> Decimal:
    """Normalize value to Decimal with specified precision.

    Args:
        value: Value to normalize
        precision: Number of decimal places
        rounding: Rounding mode

    Returns:
        Decimal with specified precision

    """
    if value is None:
        return Decimal("0")

    try:
        decimal_value = Decimal(str(value))
        quantize_exp = Decimal("0.1") ** precision
        return decimal_value.quantize(quantize_exp, rounding=rounding)
    except (ValueError, TypeError):
        return Decimal("0")


def normalize_monetary_precision(value: Any) -> Decimal:
    """Normalize monetary value to 2 decimal places with proper rounding.

    Args:
        value: Monetary value to normalize

    Returns:
        Decimal with 2 decimal places

    """
    return normalize_decimal_precision(value, precision=2)


def normalize_quantity_precision(value: Any) -> Decimal:
    """Normalize quantity value to 4 decimal places for fractional shares.

    Args:
        value: Quantity value to normalize

    Returns:
        Decimal with 4 decimal places

    """
    return normalize_decimal_precision(value, precision=4)


def safe_decimal_conversion(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """Safely convert value to Decimal with fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Decimal value or default

    """
    if value is None:
        return default

    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return default


def normalize_order_details(order: Any) -> dict[str, Any]:
    """Normalize order object to consistent dictionary format.

    Handles both domain Order entities and raw dictionaries from various sources.

    Args:
        order: Order object (domain entity or dict)

    Returns:
        Normalized order dictionary

    """
    if isinstance(order, dict):
        # Already a dict, just normalize values
        normalized = order.copy()
    else:
        # Convert domain entity to dict
        if hasattr(order, "__dict__"):
            normalized = order.__dict__.copy()
        else:
            # Fallback for complex objects
            normalized = {}
            for attr in ["id", "symbol", "qty", "side", "order_type", "status", "filled_qty"]:
                if hasattr(order, attr):
                    normalized[attr] = getattr(order, attr)

    # Normalize key fields
    if "qty" in normalized:
        normalized["qty"] = float(safe_decimal_conversion(normalized["qty"]))

    if "filled_qty" in normalized:
        normalized["filled_qty"] = float(safe_decimal_conversion(normalized["filled_qty"]))

    if "limit_price" in normalized and normalized["limit_price"] is not None:
        normalized["limit_price"] = float(normalize_monetary_precision(normalized["limit_price"]))

    if "avg_fill_price" in normalized and normalized["avg_fill_price"] is not None:
        normalized["avg_fill_price"] = float(
            normalize_monetary_precision(normalized["avg_fill_price"])
        )

    # Normalize timestamps
    for timestamp_field in ["created_at", "updated_at", "submitted_at"]:
        if timestamp_field in normalized:
            normalized[timestamp_field] = normalize_timestamp_str(normalized[timestamp_field])

    return normalized


def create_execution_summary(
    orders: Iterable[Any], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create execution summary from collection of orders.

    Args:
        orders: Collection of order objects
        metadata: Optional metadata to include

    Returns:
        Execution summary dictionary

    """
    normalized_orders = [normalize_order_details(order) for order in orders]

    # Calculate summary statistics
    total_orders = len(normalized_orders)
    filled_orders = sum(1 for order in normalized_orders if order.get("status") == "filled")
    total_value = sum(
        order.get("qty", 0) * order.get("avg_fill_price", 0)
        for order in normalized_orders
        if order.get("avg_fill_price")
    )

    summary = {
        "timestamp": normalize_timestamp_str(None),
        "total_orders": total_orders,
        "filled_orders": filled_orders,
        "fill_rate": filled_orders / total_orders if total_orders > 0 else 0,
        "total_value": normalize_monetary_precision(total_value),
        "orders": normalized_orders,
    }

    if metadata:
        summary["metadata"] = metadata

    return summary


__all__ = [
    # Account mapping
    "to_money_usd",
    "account_summary_to_typed",
    "account_typed_to_serializable",
    "AccountMetrics",
    "AccountSummaryTyped",
    # Execution mapping
    "normalize_timestamp_str",
    "normalize_decimal_precision",
    "normalize_monetary_precision",
    "normalize_quantity_precision",
    "safe_decimal_conversion",
    "normalize_order_details",
    "create_execution_summary",
]
