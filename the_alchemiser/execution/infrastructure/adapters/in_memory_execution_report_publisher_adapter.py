"""Business Unit: order execution/placement | Status: current

In-memory execution report publisher adapter for smoke validation.

TODO: Replace with production message broker adapter (e.g., SQS, Redis, EventBridge)
FIXME: This simplified adapter only stores reports in memory
"""

from uuid import UUID

from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.execution.application.ports import ExecutionReportPublisherPort


class InMemoryExecutionReportPublisherAdapter(ExecutionReportPublisherPort):
    """Simple in-memory execution report publisher for smoke validation.

    TODO: Replace with production message broker implementation
    FIXME: No persistence or delivery guarantees in current implementation
    """

    def __init__(self) -> None:
        self._published_reports: list[ExecutionReportContractV1] = []
        self._published_message_ids: set[UUID] = set()

    def publish(self, report: ExecutionReportContractV1) -> None:
        """Publish an execution report to in-memory storage.

        Args:
            report: Complete execution report with envelope metadata

        Raises:
            ValidationError: Invalid report contract (basic validation)

        """
        # TODO: Replace basic validation with comprehensive schema validation
        # FIXME: Add proper error handling and logging
        if not report.fills:
            from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError

            raise ValidationError("Report must have at least one fill")

        # TODO: Replace with distributed idempotency mechanism (e.g., database-backed)
        # FIXME: Idempotency check - current implementation only works within same process
        if report.message_id not in self._published_message_ids:
            self._published_reports.append(report)
            self._published_message_ids.add(report.message_id)

    def get_published_reports(self) -> list[ExecutionReportContractV1]:
        """Get all published reports (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        return self._published_reports.copy()

    def clear_reports(self) -> None:
        """Clear all published reports (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        self._published_reports.clear()
        self._published_message_ids.clear()
