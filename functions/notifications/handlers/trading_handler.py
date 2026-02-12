"""Business Unit: notifications | Status: current.

Handler for AllTradesCompleted events: sends trading notifications.
"""

from __future__ import annotations

import decimal
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from handlers.session_lookup import get_notification_session
from service import NotificationService
from strategy_report_service import generate_performance_report_url

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.schemas import TradingNotificationRequested
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Threshold: 30% failure rate is the cutoff for "real" failure emails
_FAILURE_THRESHOLD = 0.30


class TradingHandler:
    """Handles AllTradesCompleted events."""

    def handle(self, detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        """Process AllTradesCompleted event and send trading notification.

        If a notification session exists, defers to consolidated handler.
        Otherwise sends immediately (backward compatible).

        Args:
            detail: The detail payload from AllTradesCompleted event.
            correlation_id: Correlation ID for tracing.

        Returns:
            Response with status code and message.

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

        session = get_notification_session(correlation_id)
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

        logger.info(
            "No notification session - sending per-strategy email",
            extra={"correlation_id": correlation_id, "run_id": run_id},
        )

        container = ApplicationContainer.create_for_notifications("production")
        report_url = _generate_strategy_report(correlation_id)
        notification_event = _build_trading_notification(
            detail, correlation_id, container, report_url
        )

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


def _generate_strategy_report(correlation_id: str) -> str | None:
    """Generate strategy performance report and return presigned URL."""
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


def _build_trading_notification(
    all_trades_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
    report_url: str | None = None,
) -> TradingNotificationRequested:
    """Build TradingNotificationRequested from AllTradesCompleted event.

    Implements partial success logic: if all failures are due to non-fractionable
    assets rounding to zero, classify as partial success rather than failure.
    """
    mode_str = "LIVE" if not container.config.paper_trading() else "PAPER"

    total_trades = all_trades_detail.get("total_trades", 0)
    succeeded_trades = all_trades_detail.get("succeeded_trades", 0)
    failed_trades = all_trades_detail.get("failed_trades", 0)
    skipped_trades = all_trades_detail.get("skipped_trades", 0)

    aggregated_data = all_trades_detail.get("aggregated_execution_data", {})
    failed_symbols = all_trades_detail.get("failed_symbols", [])
    non_fractionable_skipped_symbols = all_trades_detail.get("non_fractionable_skipped_symbols", [])

    has_actual_failures = len(failed_symbols) > 0
    has_non_fractionable_skips = len(non_fractionable_skipped_symbols) > 0
    actual_failure_count = len(failed_symbols)
    failure_rate = actual_failure_count / total_trades if total_trades > 0 else 0

    if total_trades > 0 and failed_trades == 0:
        trading_success = True
        is_partial_success = False
        is_partial_success_with_failures = False
    elif total_trades > 0 and not has_actual_failures and has_non_fractionable_skips:
        trading_success = True
        is_partial_success = True
        is_partial_success_with_failures = False
    elif has_actual_failures and failure_rate < _FAILURE_THRESHOLD:
        trading_success = True
        is_partial_success = True
        is_partial_success_with_failures = True
    else:
        trading_success = False
        is_partial_success = False
        is_partial_success_with_failures = False

    portfolio_snapshot = all_trades_detail.get("portfolio_snapshot", {})

    execution_data: dict[str, Any] = {
        "orders_executed": aggregated_data.get("orders_executed", []),
        "execution_summary": aggregated_data.get("execution_summary", {}),
        "equity": portfolio_snapshot.get("equity", 0),
        "cash": portfolio_snapshot.get("cash", 0),
        "gross_exposure": portfolio_snapshot.get("gross_exposure", 0),
        "net_exposure": portfolio_snapshot.get("net_exposure", 0),
        "top_positions": portfolio_snapshot.get("top_positions", []),
        "start_time_utc": all_trades_detail.get("started_at", ""),
        "end_time_utc": all_trades_detail.get("completed_at", ""),
        "data_freshness": all_trades_detail.get("data_freshness", {}),
        "pnl_metrics": all_trades_detail.get("pnl_metrics", {}),
        "is_partial_success": is_partial_success,
        "is_partial_success_with_failures": is_partial_success_with_failures,
        "non_fractionable_skipped_symbols": non_fractionable_skipped_symbols,
        "failed_symbols": failed_symbols,
        "failure_rate": failure_rate,
        "strategies_evaluated": all_trades_detail.get("strategies_evaluated", 0),
        "rebalance_plan_summary": all_trades_detail.get("rebalance_plan_summary", []),
    }

    if report_url:
        execution_data["strategy_performance_report_url"] = report_url

    capital_deployed_pct = _extract_capital_deployed_pct(all_trades_detail)

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
    """Extract capital deployed percentage from event."""
    capital_pct = event_detail.get("capital_deployed_pct")
    if capital_pct is not None:
        try:
            return Decimal(str(capital_pct))
        except (TypeError, ValueError, decimal.InvalidOperation):
            pass
    return None
