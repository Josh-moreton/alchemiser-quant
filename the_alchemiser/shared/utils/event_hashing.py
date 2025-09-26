#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event hashing utilities for idempotency and correlation tracking.

Provides deterministic hash generation for event data to support
idempotent event processing and replay detection in event-driven workflows.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types import StrategySignal

logger = get_logger(__name__)


def generate_signal_hash(
    signals_data: dict[str, Any], consolidated_portfolio: dict[str, Any]
) -> str:
    """Generate deterministic hash from signal and portfolio data.

    Creates a stable hash from signal data and consolidated portfolio allocation
    that remains consistent across multiple invocations with the same data.

    Args:
        signals_data: Strategy signals dictionary
        consolidated_portfolio: Consolidated portfolio allocation data

    Returns:
        Hexadecimal hash string for idempotency checking

    """
    try:
        # Create a normalized data structure for hashing
        hash_data = {
            "signals": _normalize_signals_for_hash(signals_data),
            "portfolio": _normalize_portfolio_for_hash(consolidated_portfolio),
        }

        # Convert to deterministic JSON (sorted keys)
        json_data = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(json_data.encode("utf-8"))
        signal_hash = hash_obj.hexdigest()[:16]  # Use first 16 chars for readability

        logger.debug(f"Generated signal hash: {signal_hash} from {len(json_data)} bytes")
        return signal_hash

    except Exception as e:
        logger.error(f"Failed to generate signal hash: {e}")
        # Return a timestamp-based fallback hash to avoid blocking
        fallback = hashlib.sha256(str(datetime.now(UTC)).encode()).hexdigest()[:16]
        logger.warning(f"Using fallback hash: {fallback}")
        return fallback


def generate_market_snapshot_id(signals: list[StrategySignal]) -> str:
    """Generate market snapshot ID from signal data.

    Creates a unique identifier representing the market data state
    when the signals were generated.

    Args:
        signals: List of strategy signals from DSL engine

    Returns:
        Market snapshot identifier string

    """
    try:
        if not signals:
            return f"empty_snapshot_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        # Extract relevant market data points from signals
        snapshot_data = []
        for signal in signals:
            snapshot_data.append(
                {
                    "symbol": signal.symbol.value,
                    "action": signal.action,
                    "allocation": (
                        float(signal.target_allocation) if signal.target_allocation else 0.0
                    ),
                }
            )

            # Sort by symbol for consistency
            # Ensure the sort key is typed as str for mypy (symbol always string here)
            snapshot_data.sort(key=lambda x: cast(str, x["symbol"]))

        # Create snapshot ID with timestamp and content hash
        content_hash = hashlib.sha256(
            json.dumps(snapshot_data, sort_keys=True).encode()
        ).hexdigest()[:8]

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"market_{timestamp}_{content_hash}"

        logger.debug(f"Generated market snapshot ID: {snapshot_id} from {len(signals)} signals")
        return snapshot_id

    except Exception as e:
        logger.error(f"Failed to generate market snapshot ID: {e}")
        # Return timestamp-based fallback
        fallback = f"snapshot_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        logger.warning(f"Using fallback snapshot ID: {fallback}")
        return fallback


def _normalize_signals_for_hash(signals_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize signal data for consistent hashing.

    Removes volatile fields and sorts list values for deterministic ordering.
    """
    normalized: dict[str, Any] = {}
    for strategy_type, signal_data in signals_data.items():
        if isinstance(signal_data, dict):
            stable: dict[str, Any] = {}
            for key, value in signal_data.items():
                if key in {"timestamp", "id", "uuid"}:
                    continue
                if isinstance(value, list):
                    if all(isinstance(x, str) for x in value):
                        stable[key] = sorted(value)
                    else:
                        stable[key] = value
                else:
                    stable[key] = value
            normalized[strategy_type] = stable
    return normalized


def _normalize_portfolio_for_hash(portfolio_data: object) -> object:
    """Normalize portfolio data for consistent hashing.

    Ensures all numeric allocation values are converted to floats, Decimals are
    rounded for deterministic representation, and volatile fields are removed.
    """
    # Primitive numeric conversion
    if isinstance(portfolio_data, Decimal):
        return round(float(portfolio_data), 6)
    if isinstance(portfolio_data, (int, float)):
        return round(float(portfolio_data), 6)

    if isinstance(portfolio_data, dict):  # type: ignore[redundant-expr]
        # Detect direct allocation dict (symbol -> weight)
        if all(
            isinstance(k, str) and isinstance(v, (int, float, Decimal))
            for k, v in portfolio_data.items()
        ):
            return {
                symbol: round(float(allocation), 6)
                for symbol, allocation in sorted(portfolio_data.items())
            }

        stable_data: dict[str, Any] = {}
        for key, value in portfolio_data.items():
            if key in {"timestamp", "correlation_id", "id"}:
                continue  # Skip volatile/unnecessary fields
            stable_data[key] = _normalize_portfolio_for_hash(value)
        return stable_data

    if isinstance(portfolio_data, list):  # type: ignore[redundant-expr]
        return [_normalize_portfolio_for_hash(item) for item in portfolio_data]

    return portfolio_data
