"""Business Unit: order execution/placement; Status: current.

Execution mapping utilities (anti-corruption layer).

Ordered fixes applied (review issues 1→10):
1. DDD boundary alignment: introduce internal normalisation for order objects so
    exported dicts are shape-consistent regardless of source (dict / domain Order).
2. Removed unused timestamp helper; replaced with `_normalize_timestamp_str` and
    applied in quote creation & parsing.
3. Precision policy: split monetary vs quantity/size precision helpers with
    explicit rounding (ROUND_HALF_UP). Quantities/sizes allow 4 dp; money fixed
    to 2 dp.
4. Avoid binary float drift in JSON: monetary & quantity fields serialised as
    strings; computed spread/mid likewise (still parseable downstream).
5. Enum conversions wrapped with contextual ValueError messages.
6. Mixed order shapes eliminated via `_normalize_order_details`.
7. Tests (added separately) cover round-trips, precision, invalid enums.
8. Style: removed shebang, wrapped long lines.
9. Clarified docstring scope (DTO <-> boundary types & domain entity helpers).
10. Timestamp normalisation now guarantees timezone awareness & ISO 8601.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from the_alchemiser.application.mapping.execution_summary_mapping import (
    safe_dict_to_execution_summary_dto,
    safe_dict_to_portfolio_state_dto,
)
from the_alchemiser.shared.value_objects.core_types import AccountInfo, OrderDetails
from the_alchemiser.execution.core.execution_schemas import (
    ExecutionResultDTO,
    LambdaEventDTO,
    OrderHistoryDTO,
    QuoteDTO,
    TradingAction,
    TradingPlanDTO,
    WebSocketResultDTO,
    WebSocketStatus,
)

__all__ = [
    "account_info_to_execution_result_dto",
    "create_quote_dto",
    "create_trading_plan_dto",
    "dict_to_execution_result_dto",
    "dict_to_lambda_event_dto",
    "dict_to_order_history_dto",
    "dict_to_quote_dto",
    "dict_to_trading_plan_dto",
    "dict_to_websocket_result_dto",
    "execution_result_dto_to_dict",
    "lambda_event_dto_to_dict",
    "order_history_dto_to_dict",
    "quote_dto_to_dict",
    "trading_plan_dto_to_dict",
    "websocket_result_dto_to_dict",
]


# ---------------------------------------------------------------------------
# Precision helpers (Issue 3)
# ---------------------------------------------------------------------------


def _to_decimal(value: float | str | Decimal | int | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def ensure_money(value: float | str | Decimal | int | None) -> Decimal:
    """Quantize monetary value to 2 dp using ROUND_HALF_UP."""
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ensure_quantity(value: float | str | Decimal | int | None) -> Decimal:
    """Quantize quantities/sizes to 4 dp (supports fractional shares)."""
    return _to_decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Timestamp normalisation (Issue 2 & 10)
# ---------------------------------------------------------------------------


def _normalize_timestamp_str(ts: str | datetime) -> str:
    if isinstance(ts, str):
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
    else:
        dt = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


# ---------------------------------------------------------------------------
# Order normalisation (Issue 1 & 6)
# ---------------------------------------------------------------------------

_ORDER_KEYS: tuple[str, ...] = (
    "id",
    "symbol",
    "qty",
    "side",
    "order_type",
    "time_in_force",
    "status",
    "filled_qty",
    "filled_avg_price",
    "created_at",
    "updated_at",
)


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:  # pragma: no cover - helper
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalize_order_details(order: Any) -> dict[str, Any]:
    """Return a consistent OrderDetails-like dict from various order representations."""
    result: dict[str, Any] = {}
    for key in _ORDER_KEYS:
        result[key] = _get_attr(order, key)
    return result


def _normalize_orders(orders: Iterable[Any]) -> list[dict[str, Any]]:
    return [_normalize_order_details(o) for o in orders]


def execution_result_dto_to_dict(dto: ExecutionResultDTO) -> dict[str, Any]:
    """Convert ExecutionResultDTO to dictionary for external reporting.

    Args:
        dto: ExecutionResultDTO instance to convert

    Returns:
        Dictionary representation suitable for external reporting/logging

    """
    return {
        "orders_executed": _normalize_orders(dto.orders_executed),
        "account_info_before": dict(dto.account_info_before),
        "account_info_after": dict(dto.account_info_after),
        "execution_summary": dto.execution_summary,
        "final_portfolio_state": dto.final_portfolio_state,
        "execution_type": "trading_cycle",  # metadata
        "orders_count": len(dto.orders_executed),
        "source": "execution_mapping",
    }


def dict_to_execution_result_dto(data: dict[str, Any]) -> ExecutionResultDTO:
    """Convert dictionary to ExecutionResultDTO.

    Args:
        data: Dictionary containing execution result data

    Returns:
        ExecutionResultDTO instance

    """
    return ExecutionResultDTO(
        orders_executed=data.get("orders_executed", []),
        account_info_before=data["account_info_before"],
        account_info_after=data["account_info_after"],
        execution_summary=safe_dict_to_execution_summary_dto(data.get("execution_summary", {})),
        final_portfolio_state=safe_dict_to_portfolio_state_dto(data.get("final_portfolio_state")),
    )


def trading_plan_dto_to_dict(dto: TradingPlanDTO) -> dict[str, Any]:
    """Convert TradingPlanDTO to dictionary (string monetary serialization)."""
    return {
        "symbol": dto.symbol,
        "action": dto.action.value,
        "quantity": str(dto.quantity),
        "estimated_price": str(dto.estimated_price),
        "reasoning": dto.reasoning,
        "plan_type": "trading_plan",
        "estimated_value": str(dto.quantity * dto.estimated_price),
        "source": "execution_mapping",
    }


def dict_to_trading_plan_dto(data: dict[str, Any]) -> TradingPlanDTO:
    """Convert dictionary to TradingPlanDTO.

    Args:
        data: Dictionary containing trading plan data

    Returns:
        TradingPlanDTO instance

    """
    # Normalize action to TradingAction enum
    action_val = data["action"]
    try:
        action = TradingAction(action_val.upper()) if isinstance(action_val, str) else action_val
    except ValueError as exc:  # Issue 5
        raise ValueError(f"Invalid trading action '{action_val}'") from exc

    return TradingPlanDTO(
        symbol=data["symbol"],
        action=action,
        quantity=ensure_quantity(data["quantity"]),
        estimated_price=ensure_money(data["estimated_price"]),
        reasoning=data.get("reasoning", ""),
    )


def websocket_result_dto_to_dict(dto: WebSocketResultDTO) -> dict[str, Any]:
    """Convert WebSocketResultDTO to dictionary for external reporting."""
    return {
        "status": dto.status.value,
        "message": dto.message,
        "orders_completed": dto.orders_completed,
        "result_type": "websocket_result",
        "orders_count": len(dto.orders_completed),
        "source": "execution_mapping",
    }


def dict_to_websocket_result_dto(data: dict[str, Any]) -> WebSocketResultDTO:
    """Convert dictionary to WebSocketResultDTO.

    Args:
        data: Dictionary containing websocket result data

    Returns:
        WebSocketResultDTO instance

    """
    # Normalize status to WebSocketStatus enum
    status_val = data["status"]
    try:
        status = WebSocketStatus(status_val.lower()) if isinstance(status_val, str) else status_val
    except ValueError as exc:  # Issue 5
        raise ValueError(f"Invalid websocket status '{status_val}'") from exc

    return WebSocketResultDTO(
        status=status,
        message=data["message"],
        orders_completed=data.get("orders_completed", []),
    )


def quote_dto_to_dict(dto: QuoteDTO) -> dict[str, Any]:
    """Convert QuoteDTO to dictionary for external reporting.

    Args:
        dto: QuoteDTO instance to convert

    Returns:
        Dictionary representation suitable for external reporting/logging

    """
    return {
        "bid_price": str(dto.bid_price),
        "ask_price": str(dto.ask_price),
        "bid_size": str(dto.bid_size),
        "ask_size": str(dto.ask_size),
        "timestamp": dto.timestamp,
        "quote_type": "real_time_quote",
        "spread": str(dto.ask_price - dto.bid_price),
        "mid_price": str((dto.bid_price + dto.ask_price) / 2),
        "source": "execution_mapping",
    }


def dict_to_quote_dto(data: dict[str, Any]) -> QuoteDTO:
    """Convert dictionary to QuoteDTO.

    Args:
        data: Dictionary containing quote data

    Returns:
        QuoteDTO instance

    """
    return QuoteDTO(
        bid_price=ensure_money(data["bid_price"]),
        ask_price=ensure_money(data["ask_price"]),
        bid_size=ensure_quantity(data["bid_size"]),
        ask_size=ensure_quantity(data["ask_size"]),
        timestamp=_normalize_timestamp_str(data["timestamp"]),
    )


def lambda_event_dto_to_dict(dto: LambdaEventDTO) -> dict[str, Any]:
    """Convert LambdaEventDTO to dictionary for external reporting.

    Args:
        dto: LambdaEventDTO instance to convert

    Returns:
        Dictionary representation suitable for external reporting/logging

    """
    return {
        "mode": dto.mode,
        "trading_mode": dto.trading_mode,
        "ignore_market_hours": dto.ignore_market_hours,
        "arguments": dto.arguments,
        # Additional metadata for reporting
        "event_type": "lambda_event",
        "has_arguments": bool(dto.arguments),
        "source": "execution_mapping",
    }


def dict_to_lambda_event_dto(data: dict[str, Any]) -> LambdaEventDTO:
    """Convert dictionary to LambdaEventDTO.

    Args:
        data: Dictionary containing lambda event data

    Returns:
        LambdaEventDTO instance

    """
    return LambdaEventDTO(
        mode=data.get("mode"),
        trading_mode=data.get("trading_mode"),
        ignore_market_hours=data.get("ignore_market_hours"),
        arguments=data.get("arguments"),
    )


def order_history_dto_to_dict(dto: OrderHistoryDTO) -> dict[str, Any]:
    """Convert OrderHistoryDTO to dictionary for external reporting.

    Args:
        dto: OrderHistoryDTO instance to convert

    Returns:
        Dictionary representation suitable for external reporting/logging

    """
    return {
        "orders": _normalize_orders(dto.orders),
        "metadata": dto.metadata,
        "history_type": "order_history",  # metadata
        "orders_count": len(dto.orders),
        "source": "execution_mapping",
    }


def dict_to_order_history_dto(data: dict[str, Any]) -> OrderHistoryDTO:
    """Convert dictionary to OrderHistoryDTO.

    Args:
        data: Dictionary containing order history data

    Returns:
        OrderHistoryDTO instance

    """
    return OrderHistoryDTO(
        orders=data.get("orders", []),
        metadata=data.get("metadata", {}),
    )


# Domain model to DTO conversions
def account_info_to_execution_result_dto(
    orders_executed: list[OrderDetails],
    account_before: AccountInfo,
    account_after: AccountInfo,
    execution_summary: dict[str, Any] | None = None,
    final_portfolio_state: dict[str, Any] | None = None,
) -> ExecutionResultDTO:
    """Create ExecutionResultDTO from domain models.

    Args:
        orders_executed: List of OrderDetails executed
        account_before: Account state before execution
        account_after: Account state after execution
        execution_summary: Optional execution summary
        final_portfolio_state: Optional portfolio state

    Returns:
        ExecutionResultDTO instance

    """
    return ExecutionResultDTO(
        orders_executed=orders_executed,
        account_info_before=account_before,
        account_info_after=account_after,
        execution_summary=safe_dict_to_execution_summary_dto(execution_summary or {}),
        final_portfolio_state=safe_dict_to_portfolio_state_dto(final_portfolio_state),
    )


def create_trading_plan_dto(
    symbol: str,
    action: str,
    quantity: float | Decimal,
    estimated_price: float | Decimal,
    reasoning: str = "",
) -> TradingPlanDTO:
    """Create TradingPlanDTO from basic parameters.

    Args:
        symbol: Trading symbol
        action: Trading action ("BUY" or "SELL")
        quantity: Quantity to trade
        estimated_price: Estimated execution price
        reasoning: Reasoning behind the trading decision

    Returns:
        TradingPlanDTO instance

    """
    try:
        action_enum = TradingAction(action.upper())
    except ValueError as exc:  # Issue 5
        raise ValueError(f"Invalid trading action '{action}'") from exc

    return TradingPlanDTO(
        symbol=symbol.upper().strip(),
        action=action_enum,
        quantity=ensure_quantity(quantity),
        estimated_price=ensure_money(estimated_price),
        reasoning=reasoning,
    )


def create_quote_dto(
    bid_price: float | Decimal,
    ask_price: float | Decimal,
    bid_size: float | Decimal,
    ask_size: float | Decimal,
    timestamp: str | datetime | None = None,
) -> QuoteDTO:
    """Create QuoteDTO from basic parameters.

    Args:
        bid_price: Bid price
        ask_price: Ask price
        bid_size: Bid size
        ask_size: Ask size
        timestamp: Quote timestamp (defaults to current UTC time)

    Returns:
        QuoteDTO instance

    """
    norm_ts: str
    if timestamp is None:
        norm_ts = _normalize_timestamp_str(datetime.now(UTC))
    else:
        norm_ts = _normalize_timestamp_str(timestamp)

    return QuoteDTO(
        bid_price=ensure_money(bid_price),
        ask_price=ensure_money(ask_price),
        bid_size=ensure_quantity(bid_size),
        ask_size=ensure_quantity(ask_size),
        timestamp=norm_ts,
    )
