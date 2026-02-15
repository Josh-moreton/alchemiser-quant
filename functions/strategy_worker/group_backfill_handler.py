"""Business Unit: strategy | Status: current.

Lambda handler for group backfill worker.

Processes a single group's historical backfill: parses the strategy file,
discovers the target group's AST body, pre-loads market data from S3,
evaluates the group for each trading day, and writes results to S3 Parquet.

Invoked synchronously by the Data Lambda's group backfill orchestrator.
Each worker handles exactly one group to enable parallel fan-out by depth.

This handler lives in the strategy_worker directory so it has access to
the DSL engines (engines.dsl.*). CDK deploys it as a separate Lambda
function with the same code_uri but a different handler entry point.

Payload schema (from orchestrator):
    {
        "group_id": "...",
        "group_name": "...",
        "strategy_file": "...",
        "lookback_days": 45,
        "correlation_id": "...",
        "depth": 0
    }
"""

from __future__ import annotations

import logging as _logging
import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog as _structlog

from the_alchemiser.shared.dsl.strategy_paths import get_strategies_dir
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Deep nesting in FTL Starburst etc.
sys.setrecursionlimit(10000)

configure_application_logging()

logger = get_logger(__name__)

# Suppress noisy logs during backfill evaluation
_structlog.configure(
    wrapper_class=_structlog.make_filtering_bound_logger(_logging.WARNING),
)
for _name in ("strategy_v2", "the_alchemiser", "engines", "indicators", "botocore", "urllib3"):
    _logging.getLogger(_name).setLevel(_logging.WARNING)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle single-group backfill invocation.

    Args:
        event: Payload with group_id, group_name, strategy_file, lookback_days,
            correlation_id, depth.
        context: Lambda context.

    Returns:
        Response dict with status, group_id, rows_written.

    """
    group_id = event.get("group_id", "")
    group_name = event.get("group_name", "")
    strategy_file = event.get("strategy_file", "")
    lookback_days = int(event.get("lookback_days", 45))
    correlation_id = event.get("correlation_id", str(uuid.uuid4()))
    depth = int(event.get("depth", 0))

    logger.info(
        "Group backfill worker invoked",
        extra={
            "group_id": group_id,
            "group_name": group_name,
            "strategy_file": strategy_file,
            "lookback_days": lookback_days,
            "depth": depth,
            "correlation_id": correlation_id,
        },
    )

    if not group_id or not group_name or not strategy_file:
        error_msg = "Missing required fields: group_id, group_name, strategy_file"
        logger.error(error_msg, extra={"correlation_id": correlation_id})
        return {"statusCode": 400, "body": {"status": "error", "error": error_msg}}

    try:
        result = _run_backfill(
            group_id=group_id,
            group_name=group_name,
            strategy_file=strategy_file,
            lookback_days=lookback_days,
            correlation_id=correlation_id,
        )

        logger.info(
            "Group backfill completed",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "days_evaluated": result["days_evaluated"],
                "days_written": result["days_written"],
                "days_failed": result["days_failed"],
                "correlation_id": correlation_id,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "group_id": group_id,
                "group_name": group_name,
                "days_evaluated": result["days_evaluated"],
                "rows_written": result["days_written"],
                "days_failed": result["days_failed"],
            },
        }

    except Exception as exc:
        logger.error(
            "Group backfill worker failed",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "correlation_id": correlation_id,
            },
            exc_info=True,
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "group_id": group_id,
                "group_name": group_name,
                "error": str(exc),
            },
        }


def _run_backfill(
    group_id: str,
    group_name: str,
    strategy_file: str,
    lookback_days: int,
    correlation_id: str,
) -> dict[str, Any]:
    """Execute the full backfill pipeline for a single group.

    1. Parse strategy file to discover the target group's AST body.
    2. Extract symbols from the group body.
    3. Pre-load market data from S3.
    4. Build a DSL engine with in-memory adapter.
    5. Run the backfill evaluation loop.
    6. Write results to S3 via GroupHistoryStore.

    Args:
        group_id: Deterministic group cache key.
        group_name: Human-readable group name.
        strategy_file: Strategy .clj filename.
        lookback_days: Calendar days to backfill.
        correlation_id: Tracing identifier.

    Returns:
        Result dict from backfill_single_group.

    Raises:
        ValueError: If group not found in strategy file.

    """
    from backfill_service import (
        InMemoryAdapter,
        backfill_single_group,
        get_trading_days,
        preload_symbols,
        write_results_to_s3,
    )

    from the_alchemiser.shared.dsl.group_discovery import (
        extract_symbols_from_ast,
        find_filter_targeted_groups,
    )
    from the_alchemiser.shared.dsl.sexpr_parser import SexprParser

    # 1. Locate and parse strategy file
    strategies_dir = get_strategies_dir()
    clj_path = strategies_dir / strategy_file
    if not clj_path.exists():
        raise ValueError(f"Strategy file not found: {clj_path}")

    parser = SexprParser()
    ast = parser.parse_file(str(clj_path))

    # 2. Discover groups and find the target
    all_groups = find_filter_targeted_groups(ast)

    # Deduplicate by name, keeping deepest occurrence
    best_by_name: dict[str, Any] = {}
    for gi in all_groups:
        existing = best_by_name.get(gi.name)
        if existing is None or gi.depth > existing.depth:
            best_by_name[gi.name] = gi

    target_group = best_by_name.get(group_name)
    if target_group is None:
        raise ValueError(
            f"Group '{group_name}' not found in {strategy_file}. "
            f"Available groups: {sorted(best_by_name.keys())}"
        )

    # 3. Extract symbols and pre-load market data
    symbols = extract_symbols_from_ast(target_group.body)
    if not symbols:
        logger.warning(
            "No symbols found in group body",
            group_name=group_name,
            group_id=group_id,
        )
        return {
            "group_name": group_name,
            "group_id": group_id,
            "records": [],
            "days_evaluated": 0,
            "days_written": 0,
            "days_skipped": 0,
            "days_failed": 0,
        }

    preloaded_data = preload_symbols(symbols)

    # 4. Build DSL engine with in-memory adapter
    from engines.dsl.engine import DslEngine
    from engines.dsl.operators.group_scoring import clear_evaluation_caches

    adapter = InMemoryAdapter(preloaded_data)
    engine = DslEngine(
        market_data_adapter=adapter,
        debug_mode=False,
    )
    clear_evaluation_caches()

    # 5. Determine trading days
    end_date = datetime.now(UTC).date()
    trading_days = get_trading_days(end_date, lookback_days)

    # 6. Run backfill
    result = backfill_single_group(
        group_name=group_name,
        group_id=group_id,
        ast_body=target_group.body,
        trading_days=trading_days,
        engine=engine,
        market_data_service=adapter,
        correlation_id=correlation_id,
    )

    # 7. Write to S3
    records = result.get("records", [])
    if records:
        write_ok = write_results_to_s3(group_id, records)
        if not write_ok:
            logger.error(
                "Failed to persist backfill results to S3",
                group_id=group_id,
                records_count=len(records),
                correlation_id=correlation_id,
            )

    return result
