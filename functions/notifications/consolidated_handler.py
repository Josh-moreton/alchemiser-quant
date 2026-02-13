"""Business Unit: notifications | Status: current.

Handler for AllStrategiesCompleted events -- consolidated daily run email.

When all strategies in a daily run have completed (TRADED, ALL_HOLD, or FAILED),
this module reads per-strategy results from the notification session and sends
a single consolidated email summarising the entire run.
"""

from __future__ import annotations

import os
from typing import Any

from service import NotificationService
from strategy_report_service import generate_performance_report_url

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.notifications.templates import (
    render_consolidated_run_html,
    render_consolidated_run_text,
)
from the_alchemiser.shared.services.notification_session_service import (
    NotificationSessionService,
)

logger = get_logger(__name__)


def handle_all_strategies_completed(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle AllStrategiesCompleted event - send consolidated email.

    This handler fires when all strategies in a daily run have completed
    (TRADED, ALL_HOLD, or FAILED). It reads all per-strategy results from
    the notification session and sends a single consolidated email.

    Args:
        detail: The detail payload from AllStrategiesCompleted event.
        correlation_id: Correlation ID for tracing.

    Returns:
        Response with status code and message.

    """
    total_strategies = detail.get("total_strategies", 0)
    completed_strategies = detail.get("completed_strategies", 0)

    logger.info(
        "Processing AllStrategiesCompleted for consolidated email",
        extra={
            "correlation_id": correlation_id,
            "total_strategies": total_strategies,
            "completed_strategies": completed_strategies,
        },
    )

    table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    if not table_name:
        logger.warning(
            "EXECUTION_RUNS_TABLE_NAME not set - cannot send consolidated email",
            extra={"correlation_id": correlation_id},
        )
        return {"statusCode": 500, "body": "Missing EXECUTION_RUNS_TABLE_NAME"}

    session_service = NotificationSessionService(table_name=table_name)

    # Claim notification lock (atomic, exactly-once)
    if not session_service.try_claim_notification(correlation_id):
        logger.info(
            "Consolidated notification already claimed",
            extra={"correlation_id": correlation_id},
        )
        return {"statusCode": 200, "body": "Notification already claimed"}

    # Read all per-strategy results
    strategy_results = session_service.get_all_strategy_results(correlation_id)

    logger.info(
        "Building consolidated email",
        extra={
            "correlation_id": correlation_id,
            "strategy_count": len(strategy_results),
            "outcomes": [r.get("outcome") for r in strategy_results],
        },
    )

    # Build consolidated email context
    context = _build_consolidated_context(
        correlation_id=correlation_id,
        strategy_results=strategy_results,
        total_strategies=total_strategies,
    )

    # Generate strategy performance report
    report_url = _generate_strategy_report(correlation_id)
    if report_url:
        context["strategy_performance_report_url"] = report_url

    # Render and send consolidated email
    html_body = render_consolidated_run_html(context)
    text_body = render_consolidated_run_text(context)

    container = ApplicationContainer.create_for_notifications("production")
    notification_service = NotificationService(container)
    notification_service.send_notification(
        component="daily rebalance summary",
        status=context["overall_status"],
        html_body=html_body,
        text_body=text_body,
        correlation_id=correlation_id,
    )

    # Mark session as sent
    session_service.mark_session_sent(correlation_id)

    logger.info(
        "Consolidated notification sent successfully",
        extra={
            "correlation_id": correlation_id,
            "total_strategies": total_strategies,
            "overall_status": context["overall_status"],
        },
    )

    return {
        "statusCode": 200,
        "body": f"Consolidated notification sent for {correlation_id}",
    }


def _process_traded_outcome(
    result: dict[str, Any],
    strategy_id: str,
    strategy_summary: dict[str, Any],
) -> dict[str, Any]:
    """Extract trade counts and detail from a TRADED strategy result.

    Args:
        result: Raw strategy result from DynamoDB.
        strategy_id: Strategy identifier for tagging rebalance plans.
        strategy_summary: Mutable summary dict to enrich with trade details.

    Returns:
        Dict with keys: total, succeeded, failed, skipped, has_failures,
        rebalance_plans, portfolio_snapshot, pnl_metrics, data_freshness,
        started_at, completed_at.

    """
    exec_detail = result.get("execution_detail", {})

    s_total = exec_detail.get("total_trades", 0)
    s_succeeded = exec_detail.get("succeeded_trades", 0)
    s_failed = exec_detail.get("failed_trades", 0)
    s_skipped = exec_detail.get("skipped_trades", 0)

    strategy_summary["succeeded_trades"] = s_succeeded
    strategy_summary["failed_trades"] = s_failed
    strategy_summary["skipped_trades"] = s_skipped
    strategy_summary["failed_symbols"] = exec_detail.get("failed_symbols", [])

    rebalance_plans: list[dict[str, Any]] = []
    for item in exec_detail.get("rebalance_plan_summary", []):
        rebalance_plans.append({**item, "strategy": strategy_id})

    return {
        "total": s_total,
        "succeeded": s_succeeded,
        "failed": s_failed,
        "skipped": s_skipped,
        "has_failures": s_failed > 0,
        "rebalance_plans": rebalance_plans,
        "portfolio_snapshot": exec_detail.get("portfolio_snapshot", {}),
        "pnl_metrics": exec_detail.get("pnl_metrics", {}),
        "data_freshness": exec_detail.get("data_freshness", {}),
        "started_at": exec_detail.get("started_at", ""),
        "completed_at": exec_detail.get("completed_at", ""),
    }


def _determine_overall_status(
    *,
    has_failures: bool,
    has_traded: bool,
    total_succeeded: int,
) -> str:
    """Determine overall run status from aggregated strategy outcomes.

    Args:
        has_failures: Whether any strategy had failures.
        has_traded: Whether any strategy executed trades.
        total_succeeded: Total number of succeeded trades across strategies.

    Returns:
        One of 'SUCCESS', 'PARTIAL_SUCCESS', or 'FAILURE'.

    """
    if has_failures:
        if has_traded and total_succeeded > 0:
            return "PARTIAL_SUCCESS"
        return "FAILURE"
    return "SUCCESS"


def _build_consolidated_context(
    correlation_id: str,
    strategy_results: list[dict[str, Any]],
    total_strategies: int,
) -> dict[str, Any]:
    """Build template context for consolidated email from per-strategy results.

    Args:
        correlation_id: Shared workflow correlation ID.
        strategy_results: List of per-strategy result dicts from DynamoDB.
        total_strategies: Total strategies in the run.

    Returns:
        Template context dict for consolidated email rendering.

    """
    stage = os.environ.get("APP__STAGE", "dev")

    strategies: list[dict[str, Any]] = []
    total_trades = 0
    total_succeeded = 0
    total_failed = 0
    total_skipped = 0
    has_failures = False
    has_traded = False

    portfolio_snapshot: dict[str, Any] = {}
    pnl_metrics: dict[str, Any] = {}
    data_freshness: dict[str, Any] = {}
    latest_start_time = ""
    latest_end_time = ""
    all_rebalance_plans: list[dict[str, Any]] = []

    for result in strategy_results:
        outcome = result.get("outcome", "")
        strategy_id = result.get("strategy_id", "unknown")

        strategy_summary: dict[str, Any] = {
            "name": strategy_id,
            "dsl_file": result.get("dsl_file", ""),
            "outcome": outcome,
            "trade_count": result.get("trade_count", 0),
        }

        if outcome == "TRADED":
            has_traded = True
            traded = _process_traded_outcome(result, strategy_id, strategy_summary)

            total_trades += traded["total"]
            total_succeeded += traded["succeeded"]
            total_failed += traded["failed"]
            total_skipped += traded["skipped"]
            if traded["has_failures"]:
                has_failures = True
            all_rebalance_plans.extend(traded["rebalance_plans"])

            if not portfolio_snapshot and traded["portfolio_snapshot"]:
                portfolio_snapshot = traded["portfolio_snapshot"]
                pnl_metrics = traded["pnl_metrics"]
                data_freshness = traded["data_freshness"]

            started = traded["started_at"]
            ended = traded["completed_at"]
            if started and (not latest_start_time or started < latest_start_time):
                latest_start_time = started
            if ended and (not latest_end_time or ended > latest_end_time):
                latest_end_time = ended

        elif outcome == "FAILED":
            has_failures = True
            fail_detail = result.get("failure_detail", {})
            strategy_summary["failure_reason"] = fail_detail.get(
                "error", fail_detail.get("failure_reason", "Unknown error")
            )

        strategies.append(strategy_summary)

    overall_status = _determine_overall_status(
        has_failures=has_failures, has_traded=has_traded, total_succeeded=total_succeeded
    )

    container = ApplicationContainer.create_for_notifications("production")
    notification_service = NotificationService(container)
    logs_url = notification_service.build_logs_url(correlation_id)

    return {
        "env": stage,
        "correlation_id": correlation_id,
        "overall_status": overall_status,
        "total_strategies": total_strategies,
        "strategies": strategies,
        "total_trades": total_trades,
        "total_succeeded": total_succeeded,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "portfolio_snapshot": portfolio_snapshot,
        "pnl_metrics": pnl_metrics,
        "data_freshness": data_freshness,
        "rebalance_plan_summary": all_rebalance_plans,
        "start_time_utc": latest_start_time,
        "end_time_utc": latest_end_time,
        "logs_url": logs_url,
    }


def _generate_strategy_report(correlation_id: str) -> str | None:
    """Generate strategy performance report and return presigned URL.

    Args:
        correlation_id: Correlation ID for tracing

    Returns:
        Presigned URL for CSV download, or None if generation fails

    """
    try:
        report_url = generate_performance_report_url(correlation_id=correlation_id)

        if report_url:
            logger.info(
                "Strategy performance report generated",
                extra={"correlation_id": correlation_id},
            )
        else:
            logger.debug(
                "Strategy performance report not generated (no data or not configured)",
                extra={"correlation_id": correlation_id},
            )

        return report_url

    except Exception as e:
        logger.warning(
            "Failed to generate strategy performance report",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return None
