"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.types.money import Money


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


# --- Typed Account Summary (feature-flagged consumer) ---


@dataclass(frozen=True)
class AccountMetrics:
    cash_ratio: Decimal
    market_exposure: Decimal
    leverage_ratio: Decimal | None
    available_buying_power_ratio: Decimal


@dataclass(frozen=True)
class AccountSummaryTyped:
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


def account_summary_to_typed(summary: dict[str, Any]) -> AccountSummaryTyped:
    """Convert legacy AccountService summary dict to a typed representation using Money.

    This is part of the anti-corruption layer; it does not change the legacy provider.
    """
    equity_m = to_money_usd(summary.get("equity")) or Money(Decimal("0"), "USD")
    cash_m = to_money_usd(summary.get("cash")) or Money(Decimal("0"), "USD")
    buying_power_m = to_money_usd(summary.get("buying_power")) or Money(Decimal("0"), "USD")
    last_equity_m = to_money_usd(summary.get("last_equity")) or Money(Decimal("0"), "USD")
    # Market value may be precomputed in summary
    market_value_m = to_money_usd(summary.get("market_value")) or Money(Decimal("0"), "USD")

    metrics = summary.get("calculated_metrics", {})
    metrics_t = AccountMetrics(
        cash_ratio=Decimal(str(metrics.get("cash_ratio", 0)) or "0"),
        market_exposure=Decimal(str(metrics.get("market_exposure", 0)) or "0"),
        leverage_ratio=(
            Decimal(str(metrics.get("leverage_ratio")))
            if metrics.get("leverage_ratio") is not None
            else None
        ),
        available_buying_power_ratio=Decimal(
            str(metrics.get("available_buying_power_ratio", 0)) or "0"
        ),
    )

    return AccountSummaryTyped(
        account_id=str(summary.get("account_id", "unknown")),
        equity=equity_m,
        cash=cash_m,
        market_value=market_value_m,
        buying_power=buying_power_m,
        last_equity=last_equity_m,
        day_trade_count=int(summary.get("day_trade_count", 0) or 0),
        pattern_day_trader=bool(summary.get("pattern_day_trader", False)),
        trading_blocked=bool(summary.get("trading_blocked", False)),
        transfers_blocked=bool(summary.get("transfers_blocked", False)),
        account_blocked=bool(summary.get("account_blocked", False)),
        calculated_metrics=metrics_t,
    )


def account_typed_to_serializable(typed: AccountSummaryTyped) -> dict[str, Any]:
    """Serialize AccountSummaryTyped to a JSON-friendly dict of primitives.

    Money amounts become floats. Decimal ratios become floats; leverage_ratio may be None.
    """
    return {
        "account_id": typed.account_id,
        "equity": float(typed.equity.amount),
        "cash": float(typed.cash.amount),
        "market_value": float(typed.market_value.amount),
        "buying_power": float(typed.buying_power.amount),
        "last_equity": float(typed.last_equity.amount),
        "day_trade_count": typed.day_trade_count,
        "pattern_day_trader": typed.pattern_day_trader,
        "trading_blocked": typed.trading_blocked,
        "transfers_blocked": typed.transfers_blocked,
        "account_blocked": typed.account_blocked,
        "calculated_metrics": {
            "cash_ratio": float(typed.calculated_metrics.cash_ratio),
            "market_exposure": float(typed.calculated_metrics.market_exposure),
            "leverage_ratio": (
                float(typed.calculated_metrics.leverage_ratio)
                if typed.calculated_metrics.leverage_ratio is not None
                else None
            ),
            "available_buying_power_ratio": float(
                typed.calculated_metrics.available_buying_power_ratio
            ),
        },
    }
