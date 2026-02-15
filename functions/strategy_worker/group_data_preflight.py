"""Business Unit: strategy | Status: current.

Group data preflight check for strategy workers.

Before a strategy worker evaluates a DSL file, this module checks whether
any groups in the strategy require historical data that is stale or missing.
If so, it synchronously invokes the Data Lambda to orchestrate group backfill,
blocking until all groups are populated.

This ensures that when the strategy evaluator reaches a ``(filter ...)``
operator, the group history cache already has the data it needs -- avoiding
slow in-process backfill during live trading runs.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime
from typing import Any

import boto3
from botocore.config import Config as BotoConfig

from the_alchemiser.shared.dsl.group_discovery import derive_group_id
from the_alchemiser.shared.dsl.strategy_paths import get_strategies_dir
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def run_preflight(
    strategy_file: str,
    correlation_id: str,
    *,
    lookback_days: int = 45,
) -> dict[str, Any]:
    """Check group data freshness and trigger backfill if needed.

    Parses the strategy file, discovers filter-targeted groups, checks
    each group's S3 metadata for staleness, and invokes the Data Lambda
    to backfill any groups that need updating.

    This function blocks until backfill completes (synchronous Lambda invoke).

    Args:
        strategy_file: Strategy .clj filename (e.g. "ftl_starburst.clj").
        correlation_id: Workflow correlation ID for tracing.
        lookback_days: Calendar days of history required (default 45).

    Returns:
        Dict with keys: groups_checked, groups_stale, backfill_triggered,
        backfill_result.

    """
    try:
        from the_alchemiser.shared.dsl.group_discovery import find_filter_targeted_groups
        from the_alchemiser.shared.dsl.sexpr_parser import SexprParser
    except ImportError:
        logger.warning(
            "Shared DSL package unavailable, skipping preflight",
            extra={"correlation_id": correlation_id},
        )
        return {"groups_checked": 0, "groups_stale": 0, "backfill_triggered": False}

    # Locate strategy file
    try:
        strategies_dir = get_strategies_dir()
    except ValueError:
        logger.warning(
            "Cannot locate strategies directory for preflight",
            extra={"correlation_id": correlation_id},
        )
        return {"groups_checked": 0, "groups_stale": 0, "backfill_triggered": False}

    clj_path = strategies_dir / strategy_file
    if not clj_path.exists():
        logger.warning(
            "Strategy file not found for preflight",
            extra={"strategy_file": strategy_file, "correlation_id": correlation_id},
        )
        return {"groups_checked": 0, "groups_stale": 0, "backfill_triggered": False}

    # Parse and discover groups
    parser = SexprParser()
    ast = parser.parse_file(str(clj_path))
    all_groups = find_filter_targeted_groups(ast)

    if not all_groups:
        return {"groups_checked": 0, "groups_stale": 0, "backfill_triggered": False}

    # Deduplicate by name, keeping deepest occurrence (matches orchestrator logic)
    best_by_name: dict[str, dict[str, Any]] = {}
    for gi in all_groups:
        existing = best_by_name.get(gi.name)
        if existing is None or gi.depth > existing["depth"]:
            best_by_name[gi.name] = {
                "group_id": derive_group_id(gi.name),
                "group_name": gi.name,
                "depth": gi.depth,
                "parent_filter_metric": gi.parent_filter_metric,
            }
    unique_groups: list[dict[str, Any]] = list(best_by_name.values())

    # Check staleness of each group
    stale_groups = _check_staleness(unique_groups)

    result: dict[str, Any] = {
        "groups_checked": len(unique_groups),
        "groups_stale": len(stale_groups),
        "backfill_triggered": False,
    }

    if not stale_groups:
        logger.info(
            "Preflight: all groups have fresh data",
            extra={
                "groups_checked": len(unique_groups),
                "strategy_file": strategy_file,
                "correlation_id": correlation_id,
            },
        )
        return result

    logger.info(
        "Preflight: stale groups detected, triggering backfill",
        extra={
            "groups_checked": len(unique_groups),
            "groups_stale": len(stale_groups),
            "stale_group_names": [g["group_name"] for g in stale_groups],
            "strategy_file": strategy_file,
            "correlation_id": correlation_id,
        },
    )

    # Trigger backfill via Data Lambda
    backfill_result = _invoke_data_lambda_backfill(
        strategy_file=strategy_file,
        groups=stale_groups,
        lookback_days=lookback_days,
        correlation_id=correlation_id,
    )

    result["backfill_triggered"] = True
    result["backfill_result"] = backfill_result
    return result


def _check_staleness(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Check which groups have stale or missing S3 data.

    A group is considered stale if:
    - No S3 metadata exists (never backfilled)
    - Last record date is more than 2 calendar days old (missed at least 1 trading day)

    Args:
        groups: List of group dicts with group_id, group_name, depth.

    Returns:
        Subset of groups that need backfill.

    """
    stale: list[dict[str, Any]] = []

    try:
        from the_alchemiser.shared.data_v2.group_history_store import GroupHistoryStore

        store = GroupHistoryStore()
    except (ValueError, ImportError):
        # S3 not configured or store unavailable -- all groups are stale
        logger.warning("GroupHistoryStore unavailable, marking all groups stale")
        return list(groups)

    today = datetime.now(UTC).date()
    max_age_days = 2  # Allow weekends

    for group in groups:
        group_id = group["group_id"]
        try:
            metadata = store.get_metadata(group_id)
            if metadata is None:
                stale.append(group)
                continue

            last_date = date.fromisoformat(metadata.last_record_date)
            age_days = (today - last_date).days
            if age_days > max_age_days:
                stale.append(group)
        except Exception:
            stale.append(group)

    return stale


def _invoke_data_lambda_backfill(
    strategy_file: str,
    groups: list[dict[str, Any]],
    lookback_days: int,
    correlation_id: str,
) -> dict[str, Any]:
    """Invoke Data Lambda synchronously for group backfill.

    This blocks the strategy worker Lambda while the Data Lambda orchestrates
    backfill workers.  Both the strategy worker and the Data Lambda have a
    900-second timeout, so the effective budget for this call is bounded by
    whichever Lambda times out first.  The ``read_timeout=910`` on the boto3
    config intentionally exceeds the 900-second Lambda limit so that the
    Lambda timeout (not the SDK) is the controlling constraint.

    For strategies with many nested depth levels, ensure total backfill time
    stays well within the 900-second window.

    Args:
        strategy_file: Strategy filename.
        groups: List of stale group dicts.
        lookback_days: Calendar days to backfill.
        correlation_id: Tracing identifier.

    Returns:
        Response dict from Data Lambda, or error dict.

    """
    data_function_name = os.environ.get("DATA_FUNCTION_NAME", "")
    if not data_function_name:
        logger.warning(
            "Preflight: DATA_FUNCTION_NAME not set, skipping Lambda backfill",
            extra={"correlation_id": correlation_id},
        )
        return {"status": "skipped", "reason": "DATA_FUNCTION_NAME not configured"}

    try:
        config = BotoConfig(
            read_timeout=910,
            connect_timeout=10,
            retries={"max_attempts": 0},
        )
        lambda_client = boto3.client("lambda", config=config)

        payload = {
            "action": "group_backfill",
            "strategy_file": strategy_file,
            "groups": groups,
            "lookback_days": lookback_days,
            "correlation_id": correlation_id,
            "requesting_component": "preflight",
        }

        logger.info(
            "Preflight: invoking Data Lambda for group backfill",
            extra={
                "function_name": data_function_name,
                "groups_count": len(groups),
                "correlation_id": correlation_id,
            },
        )

        response = lambda_client.invoke(
            FunctionName=data_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )

        status_code = response.get("StatusCode", 500)
        response_payload = json.loads(response["Payload"].read().decode())

        if status_code == 200:
            body = response_payload.get("body", {})
            logger.info(
                "Preflight: backfill completed",
                extra={
                    "groups_processed": body.get("groups_processed", 0),
                    "groups_failed": body.get("groups_failed", 0),
                    "correlation_id": correlation_id,
                },
            )
            return dict(body)

        logger.warning(
            "Preflight: Data Lambda returned non-200",
            extra={
                "status_code": status_code,
                "correlation_id": correlation_id,
            },
        )
        return {"status": "error", "status_code": status_code}

    except Exception as exc:
        logger.error(
            "Preflight: Data Lambda invocation failed",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "correlation_id": correlation_id,
            },
        )
        return {"status": "error", "error": str(exc)}
