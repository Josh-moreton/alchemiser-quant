"""Business Unit: trade_aggregator | Status: current.

Lambda handler for Trade Aggregator microservice.

The TradeAggregator collects TradeExecuted events from parallel execution
invocations and emits a single AllTradesCompleted event when all trades
in a run finish. This eliminates race conditions in notifications.

Trigger: EventBridge rule matching TradeExecuted events.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from config import TradeAggregatorSettings
from service import TradeAggregatorService

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import AllTradesCompleted, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted events and aggregate trade results.

    This handler:
    1. Extracts trade info from EventBridge event
    2. Checks if all trades in the run have completed
    3. If complete: claims aggregation lock (atomic)
    4. If lock acquired: aggregates results and publishes AllTradesCompleted

    The atomic claim pattern ensures exactly one invocation aggregates,
    eliminating the race condition that plagued the per-trade notification model.

    Args:
        event: EventBridge event containing TradeExecuted
        context: Lambda context

    Returns:
        Response indicating aggregation status.

    """
    # Unwrap EventBridge envelope
    detail = unwrap_eventbridge_event(event)

    # Extract run and trade identifiers from metadata
    metadata = detail.get("metadata", {})
    run_id = metadata.get("run_id", "")
    trade_id = metadata.get("trade_id", "")
    correlation_id = detail.get("correlation_id", "")

    # Skip events without run_id (e.g., legacy or test events)
    if not run_id:
        logger.debug(
            "TradeExecuted event without run_id - skipping aggregation",
            extra={"correlation_id": correlation_id, "trade_id": trade_id},
        )
        return {
            "statusCode": 200,
            "body": {"status": "skipped", "reason": "no_run_id"},
        }

    logger.info(
        "Trade Aggregator received TradeExecuted event",
        extra={
            "run_id": run_id,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
        },
    )

    try:
        # Load settings
        settings = TradeAggregatorSettings.from_environment()

        # Initialize aggregator service
        aggregator_service = TradeAggregatorService(table_name=settings.execution_runs_table_name)

        # Check current completion state
        # Note: Execution Lambda already incremented completed_trades via mark_trade_completed()
        completed, total = aggregator_service.record_trade_completed(run_id, trade_id)

        if total == 0:
            logger.warning(
                "Run not found or has no trades",
                extra={"run_id": run_id, "trade_id": trade_id},
            )
            # Publish WorkflowFailed for observability - this is an anomaly
            # that indicates orphaned TradeExecuted events or data corruption
            try:
                failure_event = WorkflowFailed(
                    correlation_id=correlation_id,
                    causation_id=run_id or trade_id,
                    event_id=f"workflow-failed-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="trade_aggregator",
                    source_component="lambda_handler",
                    workflow_type="trade_aggregation",
                    failure_reason="Run not found or has no trades - orphaned TradeExecuted event",
                    failure_step="run_lookup",
                    error_details={
                        "exception_type": "RunNotFoundError",
                        "run_id": run_id,
                        "trade_id": trade_id,
                    },
                )
                publish_to_eventbridge(failure_event)
            except Exception as pub_error:
                logger.error(
                    "Failed to publish WorkflowFailed event for run_not_found",
                    extra={"error": str(pub_error), "run_id": run_id},
                )
            return {
                "statusCode": 200,
                "body": {"status": "error", "reason": "run_not_found"},
            }

        logger.info(
            "Checked run completion",
            extra={
                "run_id": run_id,
                "completed_trades": completed,
                "total_trades": total,
            },
        )

        # Check if all trades have completed
        if completed < total:
            return {
                "statusCode": 200,
                "body": {
                    "status": "waiting",
                    "run_id": run_id,
                    "completed_trades": completed,
                    "total_trades": total,
                },
            }

        # All trades completed - try to claim aggregation lock
        # This is atomic: only one invocation wins
        if not aggregator_service.try_claim_aggregation(run_id):
            logger.info(
                "Aggregation already claimed by another invocation",
                extra={"run_id": run_id},
            )
            return {
                "statusCode": 200,
                "body": {"status": "already_aggregating", "run_id": run_id},
            }

        # This invocation won the claim - aggregate and emit event
        logger.info(
            "🏁 All trades completed, starting aggregation",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
            },
        )

        # Get run metadata and all trade results
        run_metadata = aggregator_service.get_run_metadata(run_id)
        if not run_metadata:
            raise ValueError(f"Run metadata not found after claiming aggregation: {run_id}")

        trade_results = aggregator_service.get_all_trade_results(run_id)

        # Aggregate trade results
        aggregated_data = aggregator_service.aggregate_trade_results(run_metadata, trade_results)

        # Capture capital deployed percentage and portfolio snapshot
        capital_deployed_pct, portfolio_snapshot = _capture_portfolio_state(correlation_id)

        # Fetch P&L metrics (monthly and yearly) after trades complete
        pnl_metrics = _fetch_pnl_metrics(correlation_id)

        # Get timing info from run metadata
        started_at = run_metadata.get("created_at", "")
        completed_at = datetime.now(UTC).isoformat()

        # Get data freshness from run metadata (stored as JSON string)
        import json

        data_freshness_raw = run_metadata.get("data_freshness")
        data_freshness = None
        if data_freshness_raw:
            try:
                data_freshness = json.loads(data_freshness_raw)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse data_freshness from run metadata",
                    extra={"run_id": run_id, "data_freshness_raw": data_freshness_raw},
                )

        # Get strategies evaluated count (stored in DynamoDB by Portfolio Lambda)
        strategies_evaluated = run_metadata.get("strategies_evaluated", 0)

        # Get rebalance plan summary (stored as JSON string in DynamoDB)
        rebalance_plan_summary_raw = run_metadata.get("rebalance_plan_summary")
        rebalance_plan_summary: list[dict[str, Any]] = []
        if rebalance_plan_summary_raw:
            try:
                rebalance_plan_summary = json.loads(rebalance_plan_summary_raw)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse rebalance_plan_summary from run metadata",
                    extra={"run_id": run_id},
                )

        # Build and publish AllTradesCompleted event
        all_trades_event = AllTradesCompleted(
            event_id=f"all-trades-completed-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=run_id,
            timestamp=datetime.now(UTC),
            source_module="trade_aggregator",
            source_component="TradeAggregator",
            run_id=run_id,
            plan_id=run_metadata.get("plan_id", ""),
            total_trades=run_metadata.get("total_trades", 0),
            succeeded_trades=run_metadata.get("succeeded_trades", 0),
            failed_trades=run_metadata.get("failed_trades", 0),
            skipped_trades=run_metadata.get("skipped_trades", 0),
            aggregated_execution_data=aggregated_data,
            capital_deployed_pct=capital_deployed_pct,
            failed_symbols=aggregated_data.get("failed_symbols", []),
            non_fractionable_skipped_symbols=aggregated_data.get(
                "non_fractionable_skipped_symbols", []
            ),
            started_at=started_at,
            completed_at=completed_at,
            portfolio_snapshot=portfolio_snapshot,
            data_freshness=data_freshness or {},
            pnl_metrics=pnl_metrics,
            strategies_evaluated=strategies_evaluated,
            rebalance_plan_summary=rebalance_plan_summary,
        )

        # Publish to EventBridge (triggers Notifications Lambda)
        publish_to_eventbridge(all_trades_event)

        # Mark run as completed
        aggregator_service.mark_run_completed(run_id)

        logger.info(
            "✅ Aggregation completed successfully",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
                "succeeded_trades": run_metadata.get("succeeded_trades", 0),
                "failed_trades": run_metadata.get("failed_trades", 0),
                "event_id": all_trades_event.event_id,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "aggregated",
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
                "event_id": all_trades_event.event_id,
            },
        }

    except Exception as e:
        logger.error(
            "Trade Aggregator failed",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        # Try to mark run as failed
        try:
            settings = TradeAggregatorSettings.from_environment()
            aggregator_service = TradeAggregatorService(
                table_name=settings.execution_runs_table_name
            )
            aggregator_service.mark_run_failed(run_id, str(e))
        except Exception as mark_error:
            logger.warning(
                "Failed to mark run as failed",
                extra={"run_id": run_id, "error": str(mark_error)},
            )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="trade_aggregator",
                source_component="lambda_handler",
                workflow_type="trade_aggregation",
                failure_reason=str(e),
                failure_step="aggregation",
                error_details={
                    "exception_type": type(e).__name__,
                    "run_id": run_id,
                    "trade_id": trade_id,
                },
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "run_id": run_id,
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }


def _capture_portfolio_state(correlation_id: str) -> tuple[Decimal | None, dict[str, Any]]:
    """Capture portfolio state from Alpaca account.

    Called once per run after all trades complete. Returns both capital deployed
    percentage and full portfolio snapshot for email notifications.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Tuple of (capital_deployed_pct, portfolio_snapshot dict).
        portfolio_snapshot contains: equity, cash, gross_exposure, net_exposure, top_positions

    """
    empty_snapshot: dict[str, Any] = {
        "equity": 0,
        "cash": 0,
        "gross_exposure": 0,
        "net_exposure": 0,
        "top_positions": [],
    }

    try:
        # Create minimal container for Alpaca access
        container = ApplicationContainer.create_for_notifications("production")
        alpaca_manager = container.infrastructure.alpaca_manager()
        account = alpaca_manager.get_account_object()

        if not account:
            logger.warning(
                "Failed to fetch account for portfolio state capture",
                extra={"correlation_id": correlation_id},
            )
            return None, empty_snapshot

        equity = Decimal(str(account.equity))
        cash = Decimal(str(account.cash)) if account.cash else Decimal("0")
        long_market_value = (
            Decimal(str(account.long_market_value)) if account.long_market_value else Decimal("0")
        )
        short_market_value = (
            Decimal(str(account.short_market_value)) if account.short_market_value else Decimal("0")
        )

        # Calculate exposures
        if equity > 0:
            gross_exposure = (long_market_value + abs(short_market_value)) / equity
            net_exposure = (long_market_value - abs(short_market_value)) / equity
            capital_deployed_pct = (long_market_value / equity) * Decimal("100")
        else:
            gross_exposure = Decimal("0")
            net_exposure = Decimal("0")
            capital_deployed_pct = None

        # Fetch positions for top positions list
        top_positions: list[dict[str, Any]] = []
        try:
            positions = alpaca_manager.get_positions()
            if positions and equity > 0:
                # Sort by market value descending
                sorted_positions = sorted(
                    positions,
                    key=lambda p: abs(float(p.market_value)) if p.market_value else 0,
                    reverse=True,
                )
                for pos in sorted_positions[:5]:  # Top 5 positions
                    market_value = (
                        Decimal(str(pos.market_value)) if pos.market_value else Decimal("0")
                    )
                    weight = (market_value / equity) * Decimal("100")
                    top_positions.append(
                        {
                            "symbol": pos.symbol,
                            "weight": float(weight.quantize(Decimal("0.1"))),
                            "market_value": float(market_value),
                            "qty": float(pos.qty) if pos.qty else 0,
                        }
                    )
        except Exception as pos_error:
            logger.warning(
                f"Failed to fetch positions for top positions list: {pos_error}",
                extra={"correlation_id": correlation_id},
            )

        portfolio_snapshot: dict[str, Any] = {
            "equity": float(equity),
            "cash": float(cash),
            "gross_exposure": float(gross_exposure.quantize(Decimal("0.01"))),
            "net_exposure": float(net_exposure.quantize(Decimal("0.01"))),
            "top_positions": top_positions,
        }

        logger.info(
            f"📊 Portfolio captured: equity=${equity:,.2f}, cash=${cash:,.2f}, "
            f"gross={gross_exposure:.2f}x, positions={len(top_positions)}",
            extra={
                "correlation_id": correlation_id,
                "capital_deployed_pct": str(capital_deployed_pct)
                if capital_deployed_pct
                else "N/A",
                "equity": str(equity),
                "cash": str(cash),
            },
        )

        return (
            capital_deployed_pct.quantize(Decimal("0.01")) if capital_deployed_pct else None,
            portfolio_snapshot,
        )

    except Exception as e:
        logger.warning(
            f"Failed to capture portfolio state: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return None, empty_snapshot


def _capture_capital_deployed_pct(correlation_id: str) -> Decimal | None:
    """Capture capital deployed percentage from Alpaca account.

    DEPRECATED: Use _capture_portfolio_state instead which returns both metrics.

    Called once per run after all trades complete.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Capital deployed as a percentage (0-100), or None if calculation fails.

    """
    capital_pct, _ = _capture_portfolio_state(correlation_id)
    return capital_pct


def _fetch_pnl_metrics(correlation_id: str) -> dict[str, Any]:
    """Fetch P&L metrics from Alpaca for email notifications.

    Fetches monthly and yearly P&L using the PnLService. This is called after
    all trades complete so the data reflects the current portfolio state.

    Gracefully handles errors - P&L is informational and shouldn't block notifications.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Dict with monthly_pnl and yearly_pnl data, or empty dicts on failure.
        Each contains: total_pnl (float), total_pnl_pct (float), period (str),
        start_date (str), end_date (str).

    """
    empty_pnl: dict[str, Any] = {
        "monthly_pnl": {},
        "yearly_pnl": {},
    }

    try:
        from the_alchemiser.shared.services.pnl_service import PnLService

        pnl_service = PnLService(correlation_id=correlation_id)

        # Fetch monthly P&L (current month)
        monthly_pnl: dict[str, Any] = {}
        try:
            monthly_data = pnl_service.get_monthly_pnl(months_back=1)
            monthly_pnl = {
                "period": monthly_data.period,
                "start_date": monthly_data.start_date,
                "end_date": monthly_data.end_date,
                "total_pnl": float(monthly_data.total_pnl) if monthly_data.total_pnl else None,
                "total_pnl_pct": (
                    float(monthly_data.total_pnl_pct) if monthly_data.total_pnl_pct else None
                ),
            }
        except Exception as e:
            logger.warning(
                f"Failed to fetch monthly P&L: {e}",
                extra={"correlation_id": correlation_id, "error_type": type(e).__name__},
            )

        # Fetch yearly P&L (1 year / YTD-ish)
        yearly_pnl: dict[str, Any] = {}
        try:
            yearly_data = pnl_service.get_period_pnl("1A")
            yearly_pnl = {
                "period": yearly_data.period,
                "start_date": yearly_data.start_date,
                "end_date": yearly_data.end_date,
                "total_pnl": float(yearly_data.total_pnl) if yearly_data.total_pnl else None,
                "total_pnl_pct": (
                    float(yearly_data.total_pnl_pct) if yearly_data.total_pnl_pct else None
                ),
            }
        except Exception as e:
            logger.warning(
                f"Failed to fetch yearly P&L: {e}",
                extra={"correlation_id": correlation_id, "error_type": type(e).__name__},
            )

        logger.info(
            "📈 P&L metrics fetched successfully",
            extra={
                "correlation_id": correlation_id,
                "monthly_pnl_pct": monthly_pnl.get("total_pnl_pct"),
                "yearly_pnl_pct": yearly_pnl.get("total_pnl_pct"),
            },
        )

        return {
            "monthly_pnl": monthly_pnl,
            "yearly_pnl": yearly_pnl,
        }

    except Exception as e:
        logger.warning(
            f"Failed to initialize PnLService: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return empty_pnl
