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
    portfolio selections in DynamoDB for historical lookups.

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

                    # Calculate TTL
                    ttl_timestamp = int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())

                    # Store in DynamoDB
                    item = {
                        "group_id": group_id,
                        "record_date": record_date_str,
                        "selections": selections,
                        "selection_count": len(selections),
                        "evaluated_at": datetime.now(UTC).isoformat(),
                        "ttl": ttl_timestamp,
                    }

                    table.put_item(Item=item)

                    results.append(
                        {
                            "group_id": group_id,
                            "status": "success",
                            "selection_count": len(selections),
                            "selections": selections,
                        }
                    )

                    logger.info(
                        f"Cached group: {group_id}",
                        extra={
                            "group_id": group_id,
                            "selection_count": len(selections),
                            "selections": list(selections.keys()),
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


def _get_strategies_path() -> Path:
    """Get the path to the strategies directory.

    Returns:
        Path to strategies directory (either from Lambda layer or local).

    """
    try:
        return importlib_resources.files("the_alchemiser.shared.strategies")  # type: ignore[return-value]
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
