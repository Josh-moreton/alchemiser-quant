"""Business Unit: execution | Status: current.

Execution tracking and logging utilities for execution_v2.
"""

from __future__ import annotations

import logging

from the_alchemiser.execution_v2.models.execution_result import ExecutionResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

logger = logging.getLogger(__name__)


class ExecutionTracker:
    """Basic execution tracking and logging."""

    @staticmethod
    def log_plan_received(plan: RebalancePlan) -> None:
        """Log when rebalance plan is received."""
        logger.info(f"📋 Plan received: {plan.plan_id}")
        logger.info(f"  Total value: ${plan.total_trade_value}")
        logger.info(f"  Items: {len(plan.items)}")

        for item in plan.items:
            logger.info(f"  📦 {item.action} ${item.trade_amount} {item.symbol}")

    @staticmethod
    def log_execution_summary(plan: RebalancePlan, result: ExecutionResult) -> None:
        """Log execution summary."""
        success_rate = result.success_rate * 100

        logger.info(f"📊 Execution Summary for {plan.plan_id}:")
        logger.info(
            f"  Success Rate: {success_rate:.1f}% ({result.orders_succeeded}/{result.orders_placed})"
        )
        logger.info(f"  Total Traded: ${result.total_trade_value}")

        if result.failure_count > 0:
            logger.warning(f"  Failed Orders: {result.failure_count}")
            for order in result.orders:
                if not order.success:
                    logger.warning(f"    ❌ {order.symbol}: {order.error_message}")

    @staticmethod
    def check_execution_health(result: ExecutionResult) -> None:
        """Check execution health and alert on issues."""
        failure_rate = 1.0 - result.success_rate

        if failure_rate > 0.5:  # >50% failure rate
            logger.critical(f"🚨 HIGH FAILURE RATE: {failure_rate:.1%}")
        elif failure_rate > 0.2:  # >20% failure rate
            logger.warning(f"⚠️ Elevated failure rate: {failure_rate:.1%}")
        elif result.success:
            logger.info(f"✅ Healthy execution: {result.success_rate:.1%} success rate")
