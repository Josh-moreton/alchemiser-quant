"""Mapping utilities for strategy signals to typed domain structures.

This module converts legacy, loosely-typed strategy signal dicts into the
typed StrategySignal structure defined in the domain types. It enables
feature-flagged adoption of typed signals without breaking existing flows.
"""

from __future__ import annotations

from typing import Any, Literal

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.domain.types import StrategySignal

ActionLiteral = Literal["BUY", "SELL", "HOLD"]


def _normalize_action(value: Any) -> ActionLiteral:
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
