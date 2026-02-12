"""Business Unit: notifications | Status: current.

Lambda handler for event-driven notifications microservice.

Consumes AllTradesCompleted, WorkflowFailed, and HedgeEvaluationCompleted events
from EventBridge and sends email notifications using the NotificationService.

This is a stateless handler - all aggregation logic lives in TradeAggregator.
Each event triggers exactly one notification, eliminating race conditions.
"""

from __future__ import annotations

import decimal
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from service import NotificationService
from strategy_report_service import generate_performance_report_url

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.events.schemas import (
    DataLakeNotificationRequested,
    ErrorNotificationRequested,
    ScheduleNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle AllTradesCompleted and WorkflowFailed events and send notifications.

    This Lambda is triggered by EventBridge:
    - AllTradesCompleted: From TradeAggregator when all trades in a run finish
    - WorkflowFailed: From any alchemiser module on failure

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        # Extract EventBridge envelope metadata
        detail_type = event.get("detail-type", "")
        source = event.get("source", "")

        # Unwrap EventBridge envelope to get the actual event payload
        detail = unwrap_eventbridge_event(event)

        # Extract correlation_id from event if available
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Notifications Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        # Route to appropriate handler based on event type
        if detail_type == "AllStrategiesCompleted":
            return _handle_all_strategies_completed(detail, correlation_id)
        if detail_type == "AllTradesCompleted":
            return _handle_all_trades_completed(detail, correlation_id)
        if detail_type == "WorkflowFailed":
            return _handle_workflow_failed(detail, correlation_id, source)
        if detail_type == "HedgeEvaluationCompleted":
            return _handle_hedge_evaluation_completed(detail, correlation_id)
        if detail_type == "DataLakeUpdateCompleted":
            return _handle_data_lake_update(detail, correlation_id)
        if detail_type == "ScheduleCreated":
            return _handle_schedule_created(detail, correlation_id)
        if detail_type == "Lambda Function Invocation Result - Failure":
            return _handle_lambda_async_failure(detail, correlation_id, source)
        if detail_type == "CloudWatch Alarm State Change":
            return _handle_cloudwatch_alarm(event, correlation_id)

        logger.debug(
            f"Ignoring unsupported event type: {detail_type}",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 200,
            "body": f"Ignored event type: {detail_type}",
        }

    except Exception as e:
        logger.error(
            f"Notifications Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        # Don't raise - notifications shouldn't fail the workflow
        return {
            "statusCode": 500,
            "body": f"Notification failed: {e!s}",
        }


def _handle_all_trades_completed(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle AllTradesCompleted event from TradeAggregator.

    If a notification session exists for this correlation_id (created by the
    Coordinator), defers email to the consolidated AllStrategiesCompleted handler.
    Otherwise, sends email immediately (backward compatible for direct invocations).

    Args:
        detail: The detail payload from AllTradesCompleted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    run_id = detail.get("run_id", "unknown")
    total_trades = detail.get("total_trades", 0)
    succeeded_trades = detail.get("succeeded_trades", 0)
    failed_trades = detail.get("failed_trades", 0)

    logger.info(
        "Processing AllTradesCompleted for run",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "total_trades": total_trades,
            "succeeded_trades": succeeded_trades,
            "failed_trades": failed_trades,
        },
    )

    # Check if a notification session exists (from Coordinator)
    # If so, defer - the consolidated email will be sent by AllStrategiesCompleted
    session = _get_notification_session(correlation_id)
    if session is not None:
        logger.info(
            "Notification session found - deferring email to consolidated handler",
            extra={
                "correlation_id": correlation_id,
                "run_id": run_id,
                "total_strategies": session.get("total_strategies"),
                "completed_strategies": session.get("completed_strategies"),
            },
        )
        return {
            "statusCode": 200,
            "body": f"Deferred to consolidated notification for run {run_id}",
        }

    # No session - backward compatible, send immediately
    logger.info(
        "No notification session - sending per-strategy email",
        extra={"correlation_id": correlation_id, "run_id": run_id},
    )

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Generate strategy performance report and get presigned URL
    report_url = _generate_strategy_report(correlation_id)

    # Build TradingNotificationRequested from AllTradesCompleted event
    notification_event = _build_trading_notification_from_aggregated(
        detail, correlation_id, container, report_url
    )

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "Trading notification sent successfully (no session fallback)",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "trading_success": notification_event.trading_success,
            "orders_placed": notification_event.orders_placed,
            "report_url_included": report_url is not None,
        },
    )

    return {
        "statusCode": 200,
        "body": f"Notification sent for run {run_id}",
    }


def _get_notification_session(correlation_id: str) -> dict[str, Any] | None:
    """Check if a notification session exists for this correlation_id.

    Args:
        correlation_id: Shared workflow correlation ID.

    Returns:
        Session metadata dict, or None if no session exists.

    """
    table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    if not table_name:
        return None

    try:
        from the_alchemiser.shared.services.notification_session_service import (
            NotificationSessionService,
        )

        session_service = NotificationSessionService(table_name=table_name)
        return session_service.get_session(correlation_id)
    except Exception as e:
        logger.warning(
            f"Failed to check notification session: {e}",
            extra={"correlation_id": correlation_id},
        )
        return None


def _handle_all_strategies_completed(
    detail: dict[str, Any], correlation_id: str
) -> dict[str, Any]:
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

    from the_alchemiser.shared.services.notification_session_service import (
        NotificationSessionService,
    )

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
    from the_alchemiser.shared.notifications.templates import (
        render_consolidated_run_html,
        render_consolidated_run_text,
    )

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

    # Collect portfolio snapshot and P&L from the first TRADED strategy
    # (all strategies share the same Alpaca account)
    portfolio_snapshot: dict[str, Any] = {}
    pnl_metrics: dict[str, Any] = {}
    data_freshness: dict[str, Any] = {}
    latest_start_time = ""
    latest_end_time = ""
    all_rebalance_plans: list[dict[str, Any]] = []

    for result in strategy_results:
        outcome = result.get("outcome", "")
        strategy_id = result.get("strategy_id", "unknown")
        dsl_file = result.get("dsl_file", "")

        strategy_summary: dict[str, Any] = {
            "name": strategy_id,
            "dsl_file": dsl_file,
            "outcome": outcome,
            "trade_count": result.get("trade_count", 0),
        }

        if outcome == "TRADED":
            has_traded = True
            exec_detail = result.get("execution_detail", {})

            s_total = exec_detail.get("total_trades", 0)
            s_succeeded = exec_detail.get("succeeded_trades", 0)
            s_failed = exec_detail.get("failed_trades", 0)
            s_skipped = exec_detail.get("skipped_trades", 0)

            total_trades += s_total
            total_succeeded += s_succeeded
            total_failed += s_failed
            total_skipped += s_skipped

            if s_failed > 0:
                has_failures = True

            strategy_summary["succeeded_trades"] = s_succeeded
            strategy_summary["failed_trades"] = s_failed
            strategy_summary["skipped_trades"] = s_skipped
            strategy_summary["failed_symbols"] = exec_detail.get("failed_symbols", [])

            # Collect rebalance plan summary for this strategy
            plan_summary = exec_detail.get("rebalance_plan_summary", [])
            if plan_summary:
                for item in plan_summary:
                    item["strategy"] = strategy_id
                all_rebalance_plans.extend(plan_summary)

            # Use portfolio snapshot from first TRADED strategy (all same account)
            if not portfolio_snapshot:
                ps = exec_detail.get("portfolio_snapshot", {})
                if ps:
                    portfolio_snapshot = ps
                pnl_metrics = exec_detail.get("pnl_metrics", {})
                data_freshness = exec_detail.get("data_freshness", {})

            # Track timing
            started = exec_detail.get("started_at", "")
            ended = exec_detail.get("completed_at", "")
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

    # Determine overall status
    if has_failures:
        if has_traded and total_succeeded > 0:
            overall_status = "PARTIAL_SUCCESS"
        else:
            overall_status = "FAILURE"
    else:
        overall_status = "SUCCESS"

    # Build logs URL
    container = ApplicationContainer.create_for_notifications("production")
    notification_service = NotificationService(container)
    logs_url = notification_service._build_logs_url(correlation_id)

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


def _build_trading_notification_from_aggregated(
    all_trades_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
    report_url: str | None = None,
) -> TradingNotificationRequested:
    """Build TradingNotificationRequested from AllTradesCompleted event.

    Implements partial success logic: if all failures are due to non-fractionable
    assets rounding to zero, classify as partial success rather than failure.

    Args:
        all_trades_detail: The detail payload from AllTradesCompleted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access
        report_url: Optional presigned URL for strategy performance CSV report

    Returns:
        TradingNotificationRequested event ready for processing

    """
    # Determine trading mode from container config
    mode_str = "LIVE" if not container.config.paper_trading() else "PAPER"

    # Extract fields from AllTradesCompleted event
    total_trades = all_trades_detail.get("total_trades", 0)
    succeeded_trades = all_trades_detail.get("succeeded_trades", 0)
    failed_trades = all_trades_detail.get("failed_trades", 0)
    skipped_trades = all_trades_detail.get("skipped_trades", 0)

    # Get pre-aggregated execution data
    aggregated_data = all_trades_detail.get("aggregated_execution_data", {})

    # Get symbols categorized by failure type
    failed_symbols = all_trades_detail.get("failed_symbols", [])
    non_fractionable_skipped_symbols = all_trades_detail.get("non_fractionable_skipped_symbols", [])

    # Determine trading success status with threshold-based partial success logic:
    # - SUCCESS: All trades succeeded (no failures)
    # - PARTIAL_SUCCESS (non-fractionable): Some failures, but ALL are non-fractionable skips
    # - PARTIAL_SUCCESS (with failures): Actual failures exist but below 30% failure rate
    # - FAILURE: Actual failures at 30% or more of total trades
    #
    # Threshold: 30% failure rate is the cutoff for "real" failure emails
    # This prevents a single failed trade out of 20 from triggering a FAILURE notification
    FAILURE_THRESHOLD = 0.30  # 30% failure rate

    has_actual_failures = len(failed_symbols) > 0
    has_non_fractionable_skips = len(non_fractionable_skipped_symbols) > 0

    # Calculate failure rate based on actual failures (not non-fractionable skips)
    actual_failure_count = len(failed_symbols)
    failure_rate = actual_failure_count / total_trades if total_trades > 0 else 0

    if total_trades > 0 and failed_trades == 0:
        # No failures at all - full success
        trading_success = True
        is_partial_success = False
        is_partial_success_with_failures = False
    elif total_trades > 0 and not has_actual_failures and has_non_fractionable_skips:
        # All failures are non-fractionable skips - partial success (non-fractionable)
        trading_success = True  # Mark as success for template selection
        is_partial_success = True
        is_partial_success_with_failures = False
    elif has_actual_failures and failure_rate < FAILURE_THRESHOLD:
        # Actual failures exist but below threshold - partial success with failures
        # This is the case where 19/20 succeed and 1 fails (5% failure rate < 30%)
        trading_success = True  # Mark as partial success, not failure
        is_partial_success = True
        is_partial_success_with_failures = True
    else:
        # Actual failures at or above threshold - true failure
        trading_success = False
        is_partial_success = False
        is_partial_success_with_failures = False

    # Get portfolio snapshot (always fetched from Alpaca by TradeAggregator)
    portfolio_snapshot = all_trades_detail.get("portfolio_snapshot", {})

    # Get timing info
    started_at = all_trades_detail.get("started_at", "")
    completed_at = all_trades_detail.get("completed_at", "")

    # Get data freshness (propagated from strategy workers if available)
    data_freshness = all_trades_detail.get("data_freshness", {})

    # Get P&L metrics (fetched by TradeAggregator from Alpaca)
    pnl_metrics = all_trades_detail.get("pnl_metrics", {})

    # Build execution data for email template with all enriched data
    execution_data: dict[str, Any] = {
        "orders_executed": aggregated_data.get("orders_executed", []),
        "execution_summary": aggregated_data.get("execution_summary", {}),
        # Portfolio snapshot for email template
        "equity": portfolio_snapshot.get("equity", 0),
        "cash": portfolio_snapshot.get("cash", 0),
        "gross_exposure": portfolio_snapshot.get("gross_exposure", 0),
        "net_exposure": portfolio_snapshot.get("net_exposure", 0),
        "top_positions": portfolio_snapshot.get("top_positions", []),
        # Timing info
        "start_time_utc": started_at,
        "end_time_utc": completed_at,
        # Data freshness
        "data_freshness": data_freshness,
        # P&L metrics (monthly and yearly)
        "pnl_metrics": pnl_metrics,
        # Partial success context
        "is_partial_success": is_partial_success,
        "is_partial_success_with_failures": is_partial_success_with_failures,
        "non_fractionable_skipped_symbols": non_fractionable_skipped_symbols,
        "failed_symbols": failed_symbols,
        "failure_rate": failure_rate,
        # Strategy evaluation metadata
        "strategies_evaluated": all_trades_detail.get("strategies_evaluated", 0),
        # Rebalance plan summary for email display
        "rebalance_plan_summary": all_trades_detail.get("rebalance_plan_summary", []),
    }

    # Add report URL to execution_data if available
    if report_url:
        execution_data["strategy_performance_report_url"] = report_url

    # Extract capital deployed percentage (already captured by TradeAggregator)
    capital_deployed_pct = _extract_capital_deployed_pct(all_trades_detail)

    # Build error message - include non-fractionable skips info for partial success
    if is_partial_success:
        error_message = (
            f"Partial success: {len(non_fractionable_skipped_symbols)} symbol(s) skipped "
            f"due to non-fractionable quantity rounding to zero: "
            f"{', '.join(non_fractionable_skipped_symbols)}"
        )
    elif failed_symbols:
        error_message = f"Failed symbols: {', '.join(failed_symbols)}"
    else:
        error_message = None

    return TradingNotificationRequested(
        correlation_id=correlation_id,
        causation_id=all_trades_detail.get("event_id", correlation_id),
        event_id=f"trading-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        trading_success=trading_success,
        trading_mode=mode_str,
        orders_placed=total_trades,
        orders_succeeded=succeeded_trades,
        orders_skipped=skipped_trades,
        capital_deployed_pct=capital_deployed_pct,
        execution_data=execution_data,
        error_message=error_message,
        error_code=None,
    )


def _extract_capital_deployed_pct(event_detail: dict[str, Any]) -> Decimal | None:
    """Extract capital deployed percentage from event.

    Args:
        event_detail: The detail payload from event

    Returns:
        Capital deployed percentage as Decimal, or None if not available

    """
    capital_pct = event_detail.get("capital_deployed_pct")
    if capital_pct is not None:
        try:
            return Decimal(str(capital_pct))
        except (TypeError, ValueError):
            pass
    return None


def _handle_workflow_failed(
    detail: dict[str, Any], correlation_id: str, source: str
) -> dict[str, Any]:
    """Handle WorkflowFailed events by sending error notifications.

    Args:
        detail: The detail payload from WorkflowFailed event
        correlation_id: Correlation ID for tracing
        source: Event source (e.g., alchemiser.strategy, alchemiser.portfolio)

    Returns:
        Response with status code and message

    """
    logger.info(
        "Processing WorkflowFailed event",
        extra={"correlation_id": correlation_id, "source": source},
    )

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Build error notification event
    notification_event = _build_error_notification(detail, correlation_id, source)

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "Error notification processed successfully",
        extra={
            "correlation_id": correlation_id,
            "failure_step": detail.get("failure_step", "unknown"),
            "workflow_type": detail.get("workflow_type", "unknown"),
        },
    )

    return {
        "statusCode": 200,
        "body": f"Error notification sent for correlation_id: {correlation_id}",
    }


def _handle_hedge_evaluation_completed(
    detail: dict[str, Any], correlation_id: str
) -> dict[str, Any]:
    """Handle HedgeEvaluationCompleted events by sending hedge notification.

    Sends a separate hedge evaluation email with full recommendation details,
    independent of the main portfolio notification stream.

    Args:
        detail: The detail payload from HedgeEvaluationCompleted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    skip_reason = detail.get("skip_reason")
    recommendations = detail.get("recommendations", [])

    # Skip notification only when explicitly skipped (kill switch, low exposure, etc.)
    if skip_reason:
        logger.info(
            "Hedge evaluation skipped, no notification sent",
            extra={"correlation_id": correlation_id, "skip_reason": skip_reason},
        )
        return {
            "statusCode": 200,
            "body": f"Hedge skipped ({skip_reason}), no notification for {correlation_id}",
        }

    logger.info(
        "Processing HedgeEvaluationCompleted",
        extra={
            "correlation_id": correlation_id,
            "recommendation_count": len(recommendations),
            "vix_tier": detail.get("vix_tier"),
        },
    )

    context = _build_hedge_success_context(detail, correlation_id)
    _send_hedge_success_email(context, correlation_id)

    return {
        "statusCode": 200,
        "body": f"Hedge evaluation notification sent for {correlation_id}",
    }


def _build_hedge_success_context(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Build template context for hedge evaluation success email.

    Args:
        detail: HedgeEvaluationCompleted event detail
        correlation_id: Correlation ID for log URL generation

    Returns:
        Template context dict for hedge_templates rendering

    """
    stage = os.environ.get("APP__STAGE", "dev")

    # Reuse NotificationService's logs URL builder for consistency
    container = ApplicationContainer.create_for_notifications("production")
    notification_service = NotificationService(container)
    logs_url = notification_service._build_logs_url(correlation_id)

    budget_nav_pct = detail.get("budget_nav_pct", "0")
    try:
        budget_display = str(round(Decimal(str(budget_nav_pct)) * 100, 3))
    except (decimal.InvalidOperation, TypeError, ValueError):
        budget_display = str(budget_nav_pct)

    return {
        "env": stage,
        "run_id": correlation_id,
        "portfolio_nav": detail.get("portfolio_nav", "N/A"),
        "vix_tier": detail.get("vix_tier", "unknown"),
        "template_selected": detail.get("template_selected", "unknown"),
        "template_regime": detail.get("template_regime", "N/A"),
        "template_selection_reason": detail.get("template_selection_reason", ""),
        "total_premium_budget": detail.get("total_premium_budget", "N/A"),
        "budget_nav_pct": budget_display,
        "current_vix": detail.get("current_vix", "N/A"),
        "exposure_multiplier": detail.get("exposure_multiplier", "1.0"),
        "recommendations": detail.get("recommendations", []),
        "logs_url": logs_url,
    }


def _send_hedge_success_email(context: dict[str, Any], correlation_id: str) -> None:
    """Render and send hedge evaluation success email via NotificationService.

    Args:
        context: Template context for rendering.
        correlation_id: Correlation ID for logging and idempotency.

    """
    from the_alchemiser.shared.notifications.hedge_templates import (
        render_hedge_evaluation_success_html,
        render_hedge_evaluation_success_text,
    )

    html_body = render_hedge_evaluation_success_html(context)
    text_body = render_hedge_evaluation_success_text(context)

    container = ApplicationContainer.create_for_notifications("production")
    notification_service = NotificationService(container)
    notification_service.send_notification(
        component="hedge evaluation",
        status="SUCCESS",
        html_body=html_body,
        text_body=text_body,
        correlation_id=correlation_id,
    )

    logger.info(
        "Hedge evaluation notification dispatched via NotificationService",
        extra={"correlation_id": correlation_id},
    )


def _build_error_notification(
    workflow_failed_detail: dict[str, Any],
    correlation_id: str,
    source: str,
) -> ErrorNotificationRequested:
    """Build ErrorNotificationRequested from WorkflowFailed event detail.

    Args:
        workflow_failed_detail: The detail payload from WorkflowFailed event
        correlation_id: Correlation ID for tracing
        source: Event source for context

    Returns:
        ErrorNotificationRequested event ready for processing

    """
    # Extract fields from WorkflowFailed event
    workflow_type = workflow_failed_detail.get("workflow_type", "unknown")
    failure_reason = workflow_failed_detail.get("failure_reason", "Unknown error")
    failure_step = workflow_failed_detail.get("failure_step", "unknown")
    error_details = workflow_failed_detail.get("error_details", {})

    # Determine source module from event source
    source_module = source.replace("alchemiser.", "") if source else "unknown"

    # Hedge evaluation failures are secondary -- main portfolio succeeded
    is_hedge_failure = workflow_type == "hedge_evaluation"
    severity = "MEDIUM" if is_hedge_failure else "CRITICAL"
    priority = "MEDIUM" if is_hedge_failure else "HIGH"

    # Build error report content
    error_report = f"""
Workflow Failure Report
=======================

Workflow Type: {workflow_type}
Failed Step: {failure_step}
Source Module: {source_module}
Correlation ID: {correlation_id}

Failure Reason:
{failure_reason}

Error Details:
{_format_error_details(error_details)}
"""

    return ErrorNotificationRequested(
        correlation_id=correlation_id,
        causation_id=workflow_failed_detail.get("event_id", correlation_id),
        event_id=f"error-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        error_severity=severity,
        error_priority=priority,
        error_title=f"Workflow Failed: {failure_step}",
        error_report=error_report.strip(),
        error_code=error_details.get("exception_type"),
    )


def _format_error_details(error_details: dict[str, Any]) -> str:
    """Format error details dictionary for email display.

    Args:
        error_details: Dictionary of error details

    Returns:
        Formatted string representation

    """
    if not error_details:
        return "No additional details available"

    lines = []
    for key, value in error_details.items():
        lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


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
        # Don't fail the notification if report generation fails
        logger.warning(
            f"Failed to generate strategy performance report: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return None


def _handle_data_lake_update(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle DataLakeUpdateCompleted event.

    Sends detailed notification about data lake refresh with metrics.

    Args:
        detail: The detail payload from DataLakeUpdateCompleted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    total_symbols = detail.get("total_symbols", 0)
    success_count = detail.get("symbols_updated_count", 0)
    failed_count = detail.get("symbols_failed_count", 0)

    logger.info(
        "Processing DataLakeUpdateCompleted",
        extra={
            "correlation_id": correlation_id,
            "total_symbols": total_symbols,
            "success_count": success_count,
            "failed_count": failed_count,
        },
    )

    container = ApplicationContainer.create_for_notifications("production")
    notification_event = _build_data_lake_notification(detail, correlation_id, container)
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    return {
        "statusCode": 200,
        "body": f"Data lake notification sent for correlation_id: {correlation_id}",
    }


def _handle_schedule_created(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle ScheduleCreated event.

    Sends notification about schedule creation, early close, or holiday skip.

    Args:
        detail: The detail payload from ScheduleCreated event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    status = detail.get("status", "scheduled")
    date = detail.get("date", "unknown")
    is_early_close = detail.get("is_early_close", False)

    logger.info(
        "Processing ScheduleCreated",
        extra={
            "correlation_id": correlation_id,
            "status": status,
            "date": date,
            "is_early_close": is_early_close,
        },
    )

    container = ApplicationContainer.create_for_notifications("production")
    notification_event = _build_schedule_notification(detail, correlation_id, container)
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    return {
        "statusCode": 200,
        "body": f"Schedule notification sent for correlation_id: {correlation_id}",
    }


def _build_schedule_notification(
    schedule_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
) -> ScheduleNotificationRequested:
    """Build ScheduleNotificationRequested from ScheduleCreated event.

    Args:
        schedule_detail: The detail payload from ScheduleCreated event
        correlation_id: Correlation ID for tracing
        container: Application container for config access

    Returns:
        ScheduleNotificationRequested event ready for processing

    """
    from the_alchemiser.shared.events.schemas import ScheduleNotificationRequested

    # Build schedule context for templates
    schedule_context = {
        "status": schedule_detail.get("status", "scheduled"),
        "date": schedule_detail.get("date", "unknown"),
        "execution_time": schedule_detail.get("execution_time"),
        "market_close_time": schedule_detail.get("market_close_time"),
        "is_early_close": schedule_detail.get("is_early_close", False),
        "schedule_name": schedule_detail.get("schedule_name"),
        "skip_reason": schedule_detail.get("skip_reason"),
        "env": os.environ.get("APP__STAGE", "dev"),
    }

    return ScheduleNotificationRequested(
        correlation_id=correlation_id,
        causation_id=schedule_detail.get("event_id", correlation_id),
        event_id=f"schedule-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        schedule_context=schedule_context,
    )


def _build_data_lake_notification(
    update_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
) -> DataLakeNotificationRequested:
    """Build DataLakeNotificationRequested from DataLakeUpdateCompleted event.

    Args:
        update_detail: The detail payload from DataLakeUpdateCompleted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access

    Returns:
        DataLakeNotificationRequested event ready for processing

    """
    status_code = update_detail.get("status_code", 500)
    if status_code == 200:
        status = "SUCCESS"
    elif status_code == 206:
        status = "SUCCESS_WITH_WARNINGS"
    else:
        status = "FAILURE"

    data_lake_context = {
        "total_symbols": update_detail.get("total_symbols", 0),
        "symbols_updated": update_detail.get("symbols_updated", []),
        "failed_symbols": update_detail.get("failed_symbols", []),
        "symbols_updated_count": update_detail.get("symbols_updated_count", 0),
        "symbols_failed_count": update_detail.get("symbols_failed_count", 0),
        "total_bars_fetched": update_detail.get("total_bars_fetched", 0),
        "bar_dates": update_detail.get("bar_dates", []),
        "data_source": update_detail.get("data_source", "alpaca_api"),
        "start_time_utc": update_detail.get("start_time_utc", ""),
        "end_time_utc": update_detail.get("end_time_utc", ""),
        "duration_seconds": update_detail.get("duration_seconds", 0),
        "error_message": update_detail.get("error_message"),
        "error_details": update_detail.get("error_details", {}),
    }

    return DataLakeNotificationRequested(
        correlation_id=correlation_id,
        causation_id=update_detail.get("event_id", correlation_id),
        event_id=f"data-lake-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        status=status,
        data_lake_context=data_lake_context,
    )


def _handle_lambda_async_failure(
    detail: dict[str, Any], correlation_id: str, source: str
) -> dict[str, Any]:
    """Handle Lambda async invocation failure events from Lambda Destinations.

    When StrategyOrchestratorFunction invokes StrategyFunction asynchronously and
    all retries are exhausted (throttling, quota exceeded, timeout, crash), AWS
    Lambda Destinations route the failure to EventBridge. This handler converts
    that event into an error notification.

    Args:
        detail: The detail payload from Lambda Destination failure event
        correlation_id: Correlation ID for tracing
        source: Event source (typically "lambda")

    Returns:
        Response with status code and message

    """
    # Extract Lambda Destination failure context
    request_context = detail.get("requestContext", {})
    response_payload = detail.get("responsePayload", {})

    function_arn = request_context.get("functionArn", "unknown")
    condition = request_context.get("condition", "unknown")  # e.g., "RetriesExhausted"
    request_id = request_context.get("requestId", "")

    # Extract error details from response payload
    error_type = response_payload.get("errorType", "UnknownError")
    error_message = response_payload.get("errorMessage", "No error message available")

    # Extract function name from ARN for cleaner display
    function_name = function_arn.split(":")[-1] if ":" in function_arn else function_arn

    logger.warning(
        "Processing Lambda async invocation failure",
        extra={
            "correlation_id": correlation_id,
            "source": source,
            "function_name": function_name,
            "function_arn": function_arn,
            "condition": condition,
            "error_type": error_type,
            "request_id": request_id,
        },
    )

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Build error notification for async Lambda failure
    error_report = f"""
Lambda Async Invocation Failure
===============================

Function: {function_name}
Condition: {condition}
Request ID: {request_id}
Correlation ID: {correlation_id}

Error Type: {error_type}
Error Message: {error_message}

Full Function ARN:
{function_arn}

This failure occurred after all AWS retry attempts were exhausted.
The async invocation (likely from StrategyOrchestratorFunction) failed
without the target function being able to publish a WorkflowFailed event.
"""

    notification_event = ErrorNotificationRequested(
        correlation_id=correlation_id,
        causation_id=request_id or correlation_id,
        event_id=f"lambda-async-failure-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        error_severity="CRITICAL",
        error_priority="HIGH",
        error_title=f"Lambda Async Failure: {function_name} ({condition})",
        error_report=error_report.strip(),
        error_code=error_type,
    )

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "Lambda async failure notification sent",
        extra={
            "correlation_id": correlation_id,
            "function_name": function_name,
            "condition": condition,
        },
    )

    return {
        "statusCode": 200,
        "body": f"Lambda async failure notification sent for {function_name}",
    }


def _handle_cloudwatch_alarm(event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle CloudWatch Alarm State Change events.

    Routes CloudWatch alarms (DLQ alerts, stuck runs, Lambda errors) through
    the unified SES notification channel instead of the deprecated SNS topic.

    Args:
        event: The full EventBridge event (not unwrapped detail)
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    # CloudWatch alarm events come from default EventBridge bus
    # Extract alarm details from the event
    detail = event.get("detail", {})
    alarm_name = detail.get("alarmName", "Unknown Alarm")
    alarm_description = detail.get("configuration", {}).get("description", "")
    state = detail.get("state", {})
    state_value = state.get("value", "UNKNOWN")
    state_reason = state.get("reason", "No reason provided")
    state_timestamp = state.get("timestamp", "")

    # Only process ALARM state (not OK or INSUFFICIENT_DATA)
    if state_value != "ALARM":
        logger.debug(
            f"Ignoring CloudWatch alarm state change: {state_value}",
            extra={"correlation_id": correlation_id, "alarm_name": alarm_name},
        )
        return {
            "statusCode": 200,
            "body": f"Ignored alarm state: {state_value}",
        }

    logger.warning(
        "Processing CloudWatch alarm",
        extra={
            "correlation_id": correlation_id,
            "alarm_name": alarm_name,
            "state_value": state_value,
            "state_reason": state_reason,
        },
    )

    # Determine alarm category and title from alarm name
    alarm_name_lower = alarm_name.lower()
    if "dlq" in alarm_name_lower:
        error_title = "DLQ Alert: Failed Messages Detected"
        impact = "Messages have landed in the dead letter queue after exhausting retries."
    elif "stuck" in alarm_name_lower and "aggregation" in alarm_name_lower:
        error_title = "Stuck Aggregation Session Alert"
        impact = "An aggregation session has been stuck in PENDING state for over 30 minutes. Strategy workers may have failed silently."
    elif "stuck" in alarm_name_lower:
        error_title = "Stuck Execution Run Alert"
        impact = "An execution run has been stuck in RUNNING state for over 30 minutes. Trades may not have completed."
    elif "error" in alarm_name_lower or "orchestrator" in alarm_name_lower:
        error_title = "Lambda Error Alert"
        impact = (
            "A Lambda function has encountered errors (timeouts, crashes, or unhandled exceptions)."
        )
    else:
        error_title = f"CloudWatch Alarm: {alarm_name}"
        impact = "A CloudWatch alarm has triggered."

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Build error report
    error_report = f"""
CloudWatch Alarm Alert
======================

Alarm Name: {alarm_name}
State: {state_value}
Timestamp: {state_timestamp}
Correlation ID: {correlation_id}

Description:
{alarm_description or "No description provided"}

Reason:
{state_reason}

Impact:
{impact}

Quick Actions:
- Check CloudWatch Logs for related Lambda functions
- Review DynamoDB tables for stuck sessions/runs
- Inspect SQS DLQ for failed messages
- Verify recent deployments for potential regressions
"""

    notification_event = ErrorNotificationRequested(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        event_id=f"cloudwatch-alarm-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        error_severity="CRITICAL",
        error_priority="HIGH",
        error_title=error_title,
        error_report=error_report.strip(),
        error_code="CloudWatchAlarm",
    )

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "CloudWatch alarm notification sent",
        extra={
            "correlation_id": correlation_id,
            "alarm_name": alarm_name,
            "error_title": error_title,
        },
    )

    return {
        "statusCode": 200,
        "body": f"CloudWatch alarm notification sent for {alarm_name}",
    }
