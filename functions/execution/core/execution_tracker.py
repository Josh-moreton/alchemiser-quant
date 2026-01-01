"""Business Unit: execution | Status: current.

Execution tracking and logging utilities for execution_v2.

This module provides structured logging and health monitoring for trade execution.
All logging includes correlation tracking for distributed tracing and uses
structured fields for machine-readable output.
"""

from __future__ import annotations

from models.execution_result import ExecutionResult

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

logger = get_logger(__name__)

# Failure rate thresholds for health monitoring
# These are intentionally simple comparisons (not using math.isclose) as they
# represent policy thresholds, not numerical precision requirements
CRITICAL_FAILURE_THRESHOLD = 0.5  # >50% failure rate triggers critical alert
WARNING_FAILURE_THRESHOLD = 0.2  # >20% failure rate triggers warning


class ExecutionTracker:
    """Basic execution tracking and logging.

    Provides structured logging and health monitoring for trade execution.
    All methods are stateless and thread-safe.
    """

    @staticmethod
    def log_plan_received(plan: RebalancePlan) -> None:
        """Log when rebalance plan is received.

        Args:
            plan: The rebalance plan to log

        Raises:
            AttributeError: If plan is missing required fields (propagated)

        Note:
            Logs include correlation_id and causation_id for traceability.
            Uses structured logging fields for machine-readable output.

        """
        logger.info(
            "Plan received",
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            causation_id=plan.causation_id,
            total_trade_value=str(plan.total_trade_value),
            item_count=len(plan.items),
        )

        for item in plan.items:
            logger.info(
                "Plan item",
                plan_id=plan.plan_id,
                correlation_id=plan.correlation_id,
                action=item.action,
                symbol=item.symbol,
                trade_amount=str(item.trade_amount),
            )

    @staticmethod
    def log_execution_summary(plan: RebalancePlan, result: ExecutionResult) -> None:
        """Log execution summary.

        Args:
            plan: The original rebalance plan
            result: The execution result to summarize

        Raises:
            AttributeError: If plan or result is missing required fields (propagated)

        Note:
            Success rate is calculated as orders_succeeded/orders_placed.
            For zero orders, success_rate property returns 1.0 (100%).

        """
        success_rate_pct = result.success_rate * 100

        logger.info(
            "Execution summary",
            plan_id=plan.plan_id,
            correlation_id=result.correlation_id,
            success_rate=f"{success_rate_pct:.1f}%",
            orders_succeeded=result.orders_succeeded,
            orders_placed=result.orders_placed,
            total_trade_value=str(result.total_trade_value),
            failure_count=result.failure_count,
        )

        if result.failure_count > 0:
            logger.warning(
                "Failed orders detected",
                plan_id=plan.plan_id,
                correlation_id=result.correlation_id,
                failure_count=result.failure_count,
            )
            for order in result.orders:
                if not order.success:
                    logger.warning(
                        "Order failed",
                        plan_id=plan.plan_id,
                        correlation_id=result.correlation_id,
                        symbol=order.symbol,
                        action=order.action,
                        error_message=order.error_message,
                    )

    @staticmethod
    def check_execution_health(result: ExecutionResult) -> None:
        """Check execution health and alert on issues.

        Args:
            result: The execution result to check

        Raises:
            AttributeError: If result is missing required fields (propagated)

        Note:
            Failure rate thresholds:
            - >50%: Critical alert (CRITICAL_FAILURE_THRESHOLD)
            - >20%: Warning alert (WARNING_FAILURE_THRESHOLD)
            - Otherwise: Info log for successful executions

            Thresholds use simple float comparison as they represent policy
            boundaries, not numerical precision requirements.

        """
        failure_rate = 1.0 - result.success_rate

        if failure_rate > CRITICAL_FAILURE_THRESHOLD:
            logger.critical(
                "High failure rate detected",
                correlation_id=result.correlation_id,
                plan_id=result.plan_id,
                failure_rate=f"{failure_rate:.1%}",
                threshold=f"{CRITICAL_FAILURE_THRESHOLD:.1%}",
                orders_placed=result.orders_placed,
                orders_failed=result.failure_count,
            )
        elif failure_rate > WARNING_FAILURE_THRESHOLD:
            logger.warning(
                "Elevated failure rate",
                correlation_id=result.correlation_id,
                plan_id=result.plan_id,
                failure_rate=f"{failure_rate:.1%}",
                threshold=f"{WARNING_FAILURE_THRESHOLD:.1%}",
                orders_placed=result.orders_placed,
                orders_failed=result.failure_count,
            )
        elif result.success:
            logger.info(
                "Healthy execution",
                correlation_id=result.correlation_id,
                plan_id=result.plan_id,
                success_rate=f"{result.success_rate:.1%}",
                orders_placed=result.orders_placed,
                orders_succeeded=result.orders_succeeded,
            )
