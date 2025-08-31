"""Business Unit: order execution/placement | Status: current

EventBus-based execution report publisher adapter.

This adapter implements ExecutionReportPublisherPort using the EventBus infrastructure
to enable decoupled communication with the Portfolio context.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus
from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.execution.application.ports import ExecutionReportPublisherPort
from the_alchemiser.execution.domain.exceptions import PublishError
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError

logger = logging.getLogger(__name__)


class EventBusExecutionReportPublisherAdapter(ExecutionReportPublisherPort):
    """EventBus-based execution report publisher for Execution context.

    This adapter publishes ExecutionReportContractV1 events through the EventBus,
    enabling Portfolio context to receive execution results without direct coupling.
    The EventBus handles idempotency and delivery semantics.
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the publisher with an EventBus instance.

        Args:
            event_bus: EventBus instance for publishing events

        """
        self._event_bus = event_bus

    def publish(self, report: ExecutionReportContractV1) -> None:
        """Publish an execution report through the EventBus.

        Args:
            report: Complete execution report with fills and summary

        Raises:
            ValidationError: Invalid report contract
            PublishError: EventBus publication failure

        """
        try:
            # Basic validation
            if not hasattr(report, "fills"):
                raise ValidationError("Report must have fills attribute")

            # Validate envelope metadata is present
            if not report.message_id:
                raise ValidationError("Report must have message_id (envelope metadata)")
            if not report.correlation_id:
                raise ValidationError("Report must have correlation_id (envelope metadata)")

            logger.debug(
                "Publishing execution report via EventBus (report_id: %s, message_id: %s, fills: %d)",
                report.report_id,
                report.message_id,
                len(report.fills),
            )

            # Publish through EventBus
            self._event_bus.publish(report)

            logger.info(
                "Successfully published execution report with %d fills (report_id: %s, message_id: %s)",
                len(report.fills),
                report.report_id,
                report.message_id,
            )

        except (ValidationError, ValueError) as e:
            logger.error("Execution report validation failed: %s", e)
            raise ValidationError(f"Invalid report contract: {e}") from e
        except Exception as e:
            logger.error("Failed to publish execution report via EventBus: %s", e, exc_info=True)
            raise PublishError(f"EventBus publication failed: {e}") from e
