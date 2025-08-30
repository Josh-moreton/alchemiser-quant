"""Business Unit: order execution/placement | Status: current

Use case for executing rebalance plans and publishing reports.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
    FillV1,
)
from the_alchemiser.execution.application.ports import ExecutionReportPublisherPort
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    RebalancePlanContractV1,
)

logger = logging.getLogger(__name__)


class ExecutePlanUseCase:
    """Executes rebalance plans and publishes execution reports."""
    
    def __init__(self, execution_report_publisher: ExecutionReportPublisherPort) -> None:
        """Initialize the use case with required dependencies.
        
        Args:
            execution_report_publisher: Port for publishing execution reports

        """
        self._execution_report_publisher = execution_report_publisher
    
    def handle_plan(self, plan: RebalancePlanContractV1) -> None:
        """Handle incoming rebalance plan and execute orders.
        
        Args:
            plan: Rebalance plan to execute

        """
        logger.info(
            "Executing rebalance plan with %d orders (plan_id: %s, correlation_id: %s)",
            len(plan.planned_orders),
            plan.plan_id,
            plan.correlation_id
        )
        
        try:
            # TODO: Replace simplified execution with proper domain logic
            # FIXME: Move order execution logic to domain layer
            # This is a simplified example - real logic would involve:
            # - Order validation and risk checks
            # - Smart execution algorithms
            # - Real broker communication
            # - Fill aggregation and reporting
            
            fills = []
            
            # Simulate execution of each planned order
            for planned_order in plan.planned_orders:
                # Create simulated fill
                fill = FillV1(
                    fill_id=uuid4(),
                    order_id=planned_order.order_id,
                    symbol=planned_order.symbol,
                    side=planned_order.side,
                    quantity=planned_order.quantity,
                    price=Decimal("100.0"),  # TODO: Replace with real market price
                    filled_at=datetime.now(UTC)  # Current time for simulation
                )
                fills.append(fill)
                
                logger.debug(
                    "Simulated execution: %s %s %s @ %s",
                    planned_order.side,
                    planned_order.quantity,
                    planned_order.symbol,
                    fill.price
                )
            
            # Create execution report
            report = ExecutionReportContractV1(
                correlation_id=plan.correlation_id,
                causation_id=plan.message_id,  # This report was caused by the plan
                fills=fills,
                summary=f"Executed {len(fills)} orders from plan {plan.plan_id}"
            )
            
            # Publish the execution report
            self._execution_report_publisher.publish(report)
            
            logger.info(
                "Executed plan and published report with %d fills (report_id: %s, caused_by: %s)",
                len(report.fills),
                report.report_id,
                plan.message_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to execute plan %s: %s",
                plan.message_id,
                e,
                exc_info=True
            )
            raise