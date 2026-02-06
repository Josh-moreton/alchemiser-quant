"""Business Unit: group_cache | Status: current.

Lambda handler for group historical cache service.

This service evaluates filterable groups daily and caches their portfolio
selections in DynamoDB. This enables accurate historical scoring when
a filter operator needs to compute moving-average-return on a group.

Triggered by EventBridge schedule at 4:00 AM ET daily (before market open).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any

import boto3

from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort

# Increase recursion limit for deeply nested DSL strategies
sys.setrecursionlimit(10000)

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)

# Environment variables
GROUP_HISTORY_TABLE = os.environ.get("GROUP_HISTORY_TABLE", "")
TTL_DAYS = int(os.environ.get("CACHE_TTL_DAYS", "30"))

# DynamoDB client
dynamodb = boto3.resource("dynamodb")


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle invocation for group cache update.

    Evaluates all filterable groups defined in manifests and stores their
    portfolio selections and daily returns in DynamoDB for historical lookups.

    The portfolio daily return is a weighted sum of each selected symbol's
    daily return (close-to-close pct change). This enables downstream filter
    scoring to compute metrics like moving-average-return from a pre-built
    return series, matching Composer's approach of using *historical group
    selections* rather than today's snapshot.

    Args:
        event: Lambda event (from EventBridge schedule or manual invocation)
        context: Lambda context

    Returns:
        Response indicating success/failure with details

    """
    correlation_id = event.get("correlation_id", f"group-cache-{datetime.now(UTC).isoformat()}")
    date_override = event.get("date")  # For backfilling historical data

    logger.info(
        "Group cache Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "date_override": date_override,
        },
    )

    if not GROUP_HISTORY_TABLE:
        error_msg = "GROUP_HISTORY_TABLE environment variable not set"
        logger.error(error_msg)
        return {"statusCode": 500, "body": {"status": "error", "error": error_msg}}

    try:
        # Import DSL engine (deferred to avoid cold start overhead if Lambda fails early)
        from engines.dsl.engine import DslEngine
        from wiring import register_strategy

        from the_alchemiser.shared.config.container import ApplicationContainer

        # Resolve strategies directory
        strategies_path = _get_strategies_path()

        # Create application container and wire dependencies
        container = ApplicationContainer()
        register_strategy(container)

        # Get market data adapter
        market_data_adapter = container.strategy_market_data_adapter()

        # Initialize DSL engine
        dsl_engine = DslEngine(
            strategy_config_path=strategies_path,
            market_data_adapter=market_data_adapter,
            debug_mode=False,
        )

        # Get current date (or override for backfilling)
        if date_override:
            record_date = datetime.fromisoformat(date_override.replace("Z", "+00:00")).date()
        else:
            record_date = datetime.now(UTC).date()

        record_date_str = record_date.isoformat()

        # Load all manifests and their groups
        manifests = _load_all_manifests(strategies_path)
        logger.info(
            "Loaded manifests",
            extra={
                "manifest_count": len(manifests),
                "correlation_id": correlation_id,
            },
        )

        # Process each group
        results = []
        table = dynamodb.Table(GROUP_HISTORY_TABLE)

        for manifest in manifests:
            manifest_dir = manifest["directory"]
            for group in manifest["groups"]:
                group_id = group["group_id"]
                group_file = group["strategy_file"]
                group_path = f"filterable_groups/{manifest_dir}/{group_file}"

                logger.info(
                    f"Evaluating group: {group_id}",
                    extra={
                        "group_id": group_id,
                        "group_path": group_path,
                        "correlation_id": correlation_id,
                    },
                )

                try:
                    # Evaluate the group strategy
                    target_allocation, _trace = dsl_engine.evaluate_strategy(
                        strategy_config_path=group_path,
                        correlation_id=f"{correlation_id}-{group_id}",
                    )

                    if target_allocation and target_allocation.target_weights:
                        # Extract symbols and weights
                        selections = {
                            symbol: str(weight)
                            for symbol, weight in target_allocation.target_weights.items()
                            if weight > Decimal("0")
                        }
                    else:
                        selections = {}

                    # Compute portfolio daily return from selected symbols
                    portfolio_daily_return = _compute_portfolio_daily_return(
                        selections=selections,
                        market_data_adapter=market_data_adapter,
                        record_date_str=record_date_str,
                        correlation_id=correlation_id,
                    )

                    # Calculate TTL
                    ttl_timestamp = int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())

                    # Store in DynamoDB with portfolio return
                    item: dict[str, str | int | dict[str, str]] = {
                        "group_id": group_id,
                        "record_date": record_date_str,
                        "selections": selections,
                        "selection_count": len(selections),
                        "evaluated_at": datetime.now(UTC).isoformat(),
                        "ttl": ttl_timestamp,
                    }
                    if portfolio_daily_return is not None:
                        item["portfolio_daily_return"] = str(portfolio_daily_return)  # type: ignore[assignment]

                    table.put_item(Item=item)  # type: ignore[arg-type]

                    results.append(
                        {
                            "group_id": group_id,
                            "status": "success",
                            "selection_count": len(selections),
                            "selections": selections,
                            "portfolio_daily_return": (
                                str(portfolio_daily_return)
                                if portfolio_daily_return is not None
                                else None
                            ),
                        }
                    )

                    logger.info(
                        f"Cached group: {group_id}",
                        extra={
                            "group_id": group_id,
                            "selection_count": len(selections),
                            "selections": list(selections.keys()),
                            "portfolio_daily_return": (
                                str(portfolio_daily_return)
                                if portfolio_daily_return is not None
                                else None
                            ),
                            "correlation_id": correlation_id,
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to evaluate group: {group_id}",
                        extra={
                            "group_id": group_id,
                            "error": str(e),
                            "correlation_id": correlation_id,
                        },
                        exc_info=True,
                    )
                    results.append(
                        {
                            "group_id": group_id,
                            "status": "error",
                            "error": str(e),
                        }
                    )

        # Count successes and failures
        successes = sum(1 for r in results if r["status"] == "success")
        failures = sum(1 for r in results if r["status"] == "error")

        logger.info(
            "Group cache update completed",
            extra={
                "record_date": record_date_str,
                "total_groups": len(results),
                "successes": successes,
                "failures": failures,
                "correlation_id": correlation_id,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "record_date": record_date_str,
                "total_groups": len(results),
                "successes": successes,
                "failures": failures,
                "results": results,
            },
        }

    except Exception as e:
        logger.error(
            "Group cache update failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "error": str(e),
            },
        }


def _compute_portfolio_daily_return(
    selections: dict[str, str],
    market_data_adapter: MarketDataPort,
    record_date_str: str,
    correlation_id: str,
) -> Decimal | None:
    """Compute the weighted portfolio daily return from selected symbols.

    For each symbol in the selection, fetches recent bars to compute the
    close-to-close daily return for the record date. The portfolio return
    is the weighted sum of individual symbol returns.

    Args:
        selections: Symbol-to-weight mapping (weights as strings)
        market_data_adapter: Market data port for fetching bars
        record_date_str: Date string (YYYY-MM-DD) for the record
        correlation_id: Correlation ID for logging

    Returns:
        Weighted portfolio daily return as Decimal (e.g. Decimal("0.0153")
        for +1.53%), or None if computation fails.

    """
    if not selections:
        return Decimal("0")

    from the_alchemiser.shared.value_objects.symbol import Symbol

    weighted_return = Decimal("0")
    total_weight = Decimal("0")

    for symbol_str, weight_str in selections.items():
        weight = Decimal(weight_str)
        if weight <= Decimal("0"):
            continue

        try:
            # Fetch recent bars (30 calendar days covers ~20 trading days)
            bars = market_data_adapter.get_bars(
                symbol=Symbol(symbol_str),
                period="30D",
                timeframe="1Day",
            )

            if len(bars) < 2:
                logger.warning(
                    "Insufficient bars for daily return",
                    extra={
                        "symbol": symbol_str,
                        "bars_count": len(bars),
                        "correlation_id": correlation_id,
                    },
                )
                continue

            # Find the bar for the record date and its predecessor
            daily_return = _extract_daily_return(bars, record_date_str)
            if daily_return is not None:
                weighted_return += weight * daily_return
                total_weight += weight
            else:
                logger.warning(
                    "Could not find daily return for date",
                    extra={
                        "symbol": symbol_str,
                        "record_date": record_date_str,
                        "correlation_id": correlation_id,
                    },
                )

        except Exception as e:
            logger.warning(
                "Failed to compute daily return for symbol",
                extra={
                    "symbol": symbol_str,
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            )

    if total_weight <= Decimal("0"):
        logger.warning(
            "No symbols contributed to portfolio return",
            extra={"correlation_id": correlation_id},
        )
        return None

    # Normalize by total weight (handles partial failures)
    portfolio_return = weighted_return / total_weight

    logger.info(
        "Computed portfolio daily return",
        extra={
            "portfolio_return": str(portfolio_return),
            "symbols_included": str(total_weight),
            "correlation_id": correlation_id,
        },
    )
    return portfolio_return


def _extract_daily_return(bars: list[BarModel], record_date_str: str) -> Decimal | None:
    """Extract the daily close-to-close return for a specific date.

    Searches through bars to find the one matching record_date_str and
    computes (close / prev_close) - 1.

    If the exact date is not found (e.g. weekend/holiday), uses the most
    recent bar on or before that date.

    Args:
        bars: Chronologically ordered list of BarModel objects
        record_date_str: ISO date string (YYYY-MM-DD)

    Returns:
        Daily return as Decimal, or None if not computable.

    """
    # Build date-indexed map for fast lookup
    date_to_idx: dict[str, int] = {}
    for i, bar in enumerate(bars):
        bar_date = bar.timestamp.date().isoformat()
        date_to_idx[bar_date] = i

    # Find bar index - exact match or most recent before
    target_idx = date_to_idx.get(record_date_str)
    if target_idx is None:
        # Find most recent bar on or before the record date
        for i in range(len(bars) - 1, -1, -1):
            if bars[i].timestamp.date().isoformat() <= record_date_str:
                target_idx = i
                break

    if target_idx is None or target_idx < 1:
        return None

    current_close = bars[target_idx].close
    prev_close = bars[target_idx - 1].close

    if prev_close == Decimal("0"):
        return None

    return (current_close / prev_close) - Decimal("1")


def _get_strategies_path() -> Path:
    """Get the path to the strategies directory.

    Returns:
        Path to strategies directory (either from Lambda layer or local).

    """
    try:
        result = importlib_resources.files("the_alchemiser.shared.strategies")
        # importlib.resources.files() may return a MultiplexedPath on Lambda
        # when multiple package sources contribute to the namespace (layer + function).
        # MultiplexedPath's str() returns "MultiplexedPath('...')" not the actual path.
        # Extract the first underlying path from _paths attribute.
        if hasattr(result, "_paths") and result._paths:
            return Path(result._paths[0])
        # Fallback: if it's already a Path-like, use it directly
        return Path(result)  # type: ignore[arg-type]
    except (ModuleNotFoundError, AttributeError):
        # Fallback for local development
        strategies_path = (
            Path(__file__).parent.parent.parent
            / "layers"
            / "shared"
            / "the_alchemiser"
            / "shared"
            / "strategies"
        )
        if not strategies_path.exists():
            raise FileNotFoundError(f"Strategies directory not found at: {strategies_path}")
        logger.warning("Using local strategies path (not Lambda layer)")
        return strategies_path


def _load_all_manifests(strategies_path: Path) -> list[dict[str, Any]]:
    """Load all manifest files from filterable_groups subdirectories.

    Args:
        strategies_path: Path to the strategies directory.

    Returns:
        List of manifest dictionaries with their directory names.

    """
    manifests = []
    filterable_groups_path = Path(strategies_path) / "filterable_groups"

    if not filterable_groups_path.exists():
        logger.warning(f"No filterable_groups directory found at: {filterable_groups_path}")
        return []

    for subdir in filterable_groups_path.iterdir():
        if subdir.is_dir():
            manifest_path = subdir / "_manifest.json"
            if manifest_path.exists():
                try:
                    with manifest_path.open() as f:
                        manifest = json.load(f)
                        manifest["directory"] = subdir.name
                        manifests.append(manifest)
                        logger.info(f"Loaded manifest from: {manifest_path}")
                except Exception:
                    logger.error(f"Failed to load manifest: {manifest_path}", exc_info=True)

    return manifests
