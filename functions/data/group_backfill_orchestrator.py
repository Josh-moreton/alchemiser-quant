"""Business Unit: data | Status: current.

Group backfill orchestrator for the Data Lambda.

Handles GroupBackfillRequested events by:
1. Parsing the strategy file to discover groups (if not provided).
2. Sorting groups by depth (deepest first).
3. Fan-out: invoking Group Backfill Worker Lambdas synchronously per depth
   level, parallelised within each level via ThreadPoolExecutor.
4. Publishing GroupBackfillCompleted event when all groups finish.

The orchestrator runs inside the Data Lambda (900s timeout). Each worker
Lambda also has 900s timeout. Depth-ordered processing ensures inner
groups complete before outer groups that depend on them.
"""

from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.config import Config

from the_alchemiser.shared.dsl.group_discovery import (
    GroupInfo,
    derive_group_id,
    find_filter_targeted_groups,
)
from the_alchemiser.shared.dsl.sexpr_parser import SexprParser
from the_alchemiser.shared.dsl.strategy_paths import get_strategies_dir
from the_alchemiser.shared.events import GroupBackfillCompleted
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Maximum concurrent worker invocations per depth level.
_MAX_CONCURRENT_WORKERS = 5


def handle_group_backfill(event: dict[str, Any]) -> dict[str, Any]:
    """Orchestrate group backfill for a strategy.

    Can be called synchronously (RequestResponse from Strategy Worker) or
    via EventBridge (GroupBackfillRequested event).

    Args:
        event: Dict with keys: strategy_file, groups (optional),
            lookback_days (default 45), correlation_id, requesting_component.

    Returns:
        Response dict with status, groups_processed, groups_failed.

    """
    # Extract fields (support both direct invocation and EventBridge detail)
    detail = event.get("detail", event)
    strategy_file = detail.get("strategy_file", "")
    groups_list = detail.get("groups", [])
    lookback_days = int(detail.get("lookback_days", 45))
    correlation_id = detail.get("correlation_id", str(uuid.uuid4()))
    requesting_component = detail.get("requesting_component", "unknown")

    logger.info(
        "Group backfill orchestrator invoked",
        extra={
            "strategy_file": strategy_file,
            "groups_count": len(groups_list),
            "lookback_days": lookback_days,
            "requesting_component": requesting_component,
            "correlation_id": correlation_id,
        },
    )

    if not strategy_file:
        return {
            "statusCode": 400,
            "body": {"status": "error", "error": "Missing strategy_file"},
        }

    # Auto-discover groups if not specified
    if not groups_list:
        groups_list = _discover_groups(strategy_file)

    if not groups_list:
        logger.info(
            "No groups require backfill",
            extra={"strategy_file": strategy_file, "correlation_id": correlation_id},
        )
        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "groups_processed": 0,
                "groups_failed": 0,
                "message": "No groups found to backfill",
            },
        }

    # Sort by depth (deepest first)
    depth_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for g in groups_list:
        depth_groups[int(g.get("depth", 0))].append(g)

    # Process depth levels sequentially (deepest first)
    total_processed = 0
    total_failed = 0
    total_rows = 0
    group_details: dict[str, Any] = {}

    worker_function_name = os.environ.get("GROUP_BACKFILL_WORKER_FUNCTION_NAME", "")
    if not worker_function_name:
        stage = os.environ.get("STAGE", os.environ.get("APP__STAGE", "dev"))
        worker_function_name = f"alch-{stage}-group-backfill-worker"

    for depth in sorted(depth_groups.keys(), reverse=True):
        level_groups = depth_groups[depth]

        logger.info(
            "Processing depth level",
            extra={
                "depth": depth,
                "group_count": len(level_groups),
                "correlation_id": correlation_id,
            },
        )

        results = _invoke_workers_parallel(
            worker_function_name=worker_function_name,
            groups=level_groups,
            strategy_file=strategy_file,
            lookback_days=lookback_days,
            correlation_id=correlation_id,
        )

        for group_id, result in results.items():
            if result.get("success"):
                total_processed += 1
                rows = result.get("rows_written", 0)
                total_rows += rows
                group_details[group_id] = {"rows": rows, "status": "success"}
            else:
                total_failed += 1
                group_details[group_id] = {
                    "rows": 0,
                    "status": "failed",
                    "error": result.get("error", "unknown"),
                }

    # Publish completion event
    _publish_completion(
        strategy_file=strategy_file,
        groups_processed=total_processed,
        groups_failed=total_failed,
        total_rows=total_rows,
        group_details=group_details,
        correlation_id=correlation_id,
    )

    return {
        "statusCode": 200,
        "body": {
            "status": "success",
            "groups_processed": total_processed,
            "groups_failed": total_failed,
            "total_rows_written": total_rows,
            "group_details": group_details,
        },
    }


def _discover_groups(strategy_file: str) -> list[dict[str, Any]]:
    """Auto-discover groups from strategy file using shared DSL parser.

    Args:
        strategy_file: Strategy .clj filename.

    Returns:
        List of group target dicts with group_id, group_name, depth,
        parent_filter_metric.

    """
    strategies_dir = get_strategies_dir()
    clj_path = strategies_dir / strategy_file
    if not clj_path.exists():
        logger.error("Strategy file not found", path=str(clj_path))
        return []

    parser = SexprParser()
    ast = parser.parse_file(str(clj_path))
    all_groups = find_filter_targeted_groups(ast)

    # Deduplicate by name, keeping deepest occurrence
    best_by_name: dict[str, GroupInfo] = {}
    for gi in all_groups:
        existing = best_by_name.get(gi.name)
        if existing is None or gi.depth > existing.depth:
            best_by_name[gi.name] = gi

    result: list[dict[str, Any]] = []
    for gi in sorted(best_by_name.values(), key=lambda g: (-g.depth, g.name)):
        result.append(
            {
                "group_id": derive_group_id(gi.name),
                "group_name": gi.name,
                "depth": gi.depth,
                "parent_filter_metric": gi.parent_filter_metric,
            }
        )

    logger.info(
        "Auto-discovered groups",
        groups_count=len(result),
        depths=sorted({g["depth"] for g in result}, reverse=True),
    )
    return result


def _invoke_workers_parallel(
    worker_function_name: str,
    groups: list[dict[str, Any]],
    strategy_file: str,
    lookback_days: int,
    correlation_id: str,
) -> dict[str, dict[str, Any]]:
    """Invoke worker Lambdas in parallel for a set of groups at the same depth.

    Uses ThreadPoolExecutor with synchronous (RequestResponse) invocations.

    Args:
        worker_function_name: Name of the Group Backfill Worker Lambda.
        groups: List of group target dicts.
        strategy_file: Strategy .clj filename.
        lookback_days: Calendar days to backfill.
        correlation_id: Tracing identifier.

    Returns:
        Dict mapping group_id -> result dict with success, rows_written, error.

    """
    results: dict[str, dict[str, Any]] = {}

    # Configure Lambda client with extended timeout for sync invocation
    config = Config(
        read_timeout=910,
        connect_timeout=10,
        retries={"max_attempts": 0},
    )
    lambda_client = boto3.client("lambda", config=config)

    max_workers = min(_MAX_CONCURRENT_WORKERS, len(groups))

    def _invoke_one(group: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        gid = group["group_id"]
        payload = {
            "group_id": gid,
            "group_name": group["group_name"],
            "strategy_file": strategy_file,
            "lookback_days": lookback_days,
            "correlation_id": correlation_id,
            "depth": group.get("depth", 0),
        }

        try:
            response = lambda_client.invoke(
                FunctionName=worker_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload).encode(),
            )

            status_code = response.get("StatusCode", 500)
            response_payload = json.loads(response["Payload"].read().decode())

            if status_code == 200 and response_payload.get("statusCode") == 200:
                body = response_payload.get("body", {})
                return gid, {
                    "success": True,
                    "rows_written": body.get("rows_written", 0),
                    "days_evaluated": body.get("days_evaluated", 0),
                }
            error = response_payload.get("body", {}).get("error", "Worker returned error")
            return gid, {"success": False, "error": error}

        except Exception as exc:
            logger.error(
                "Worker invocation failed",
                extra={
                    "group_id": gid,
                    "group_name": group["group_name"],
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "correlation_id": correlation_id,
                },
            )
            return gid, {"success": False, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_invoke_one, g): g["group_id"] for g in groups}
        for future in as_completed(futures):
            gid, result = future.result()
            results[gid] = result

    processed = sum(1 for r in results.values() if r.get("success"))
    failed = sum(1 for r in results.values() if not r.get("success"))
    logger.info(
        "Depth level processing complete",
        extra={
            "processed": processed,
            "failed": failed,
            "correlation_id": correlation_id,
        },
    )

    return results


def _publish_completion(
    strategy_file: str,
    groups_processed: int,
    groups_failed: int,
    total_rows: int,
    group_details: dict[str, Any],
    correlation_id: str,
) -> None:
    """Publish GroupBackfillCompleted event to EventBridge.

    Args:
        strategy_file: Strategy filename.
        groups_processed: Count of successfully processed groups.
        groups_failed: Count of failed groups.
        total_rows: Total Parquet rows written.
        group_details: Per-group result details.
        correlation_id: Correlation ID.

    """
    try:
        event = GroupBackfillCompleted(
            event_id=f"group-backfill-completed-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime.now(UTC),
            source_module="data_v2",
            source_component="group_backfill_orchestrator",
            strategy_file=strategy_file,
            groups_processed=groups_processed,
            groups_failed=groups_failed,
            total_rows_written=total_rows,
            group_details=group_details,
        )
        publish_to_eventbridge(event)
        logger.info(
            "Published GroupBackfillCompleted event",
            extra={
                "strategy_file": strategy_file,
                "groups_processed": groups_processed,
                "groups_failed": groups_failed,
                "correlation_id": correlation_id,
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to publish GroupBackfillCompleted event",
            extra={"error": str(exc), "correlation_id": correlation_id},
        )
