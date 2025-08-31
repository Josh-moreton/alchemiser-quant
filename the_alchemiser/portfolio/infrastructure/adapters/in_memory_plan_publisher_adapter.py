"""Business Unit: portfolio assessment & management | Status: current

In-memory plan publisher adapter for smoke validation.

TODO: Replace with production message broker adapter (e.g., SQS, Redis, EventBridge)
FIXME: This simplified adapter only stores plans in memory
"""

from uuid import UUID

from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    RebalancePlanContractV1,
)
from the_alchemiser.portfolio.application.ports import PlanPublisherPort


class InMemoryPlanPublisherAdapter(PlanPublisherPort):
    """Simple in-memory plan publisher for smoke validation.

    TODO: Replace with production message broker implementation
    FIXME: No persistence or delivery guarantees in current implementation
    """

    def __init__(self) -> None:
        self._published_plans: list[RebalancePlanContractV1] = []
        self._published_message_ids: set[UUID] = set()

    def publish(self, plan: RebalancePlanContractV1) -> None:
        """Publish a rebalance plan to in-memory storage.

        Args:
            plan: Complete plan contract with envelope metadata

        Raises:
            ValidationError: Invalid plan contract (basic validation)

        """
        # TODO: Replace basic validation with comprehensive schema validation
        # FIXME: Add proper error handling and logging
        if not plan.planned_orders:
            from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError

            raise ValidationError("Plan must have at least one planned order")

        # TODO: Replace with distributed idempotency mechanism (e.g., database-backed)
        # FIXME: Idempotency check - current implementation only works within same process
        if plan.message_id not in self._published_message_ids:
            self._published_plans.append(plan)
            self._published_message_ids.add(plan.message_id)

    def get_published_plans(self) -> list[RebalancePlanContractV1]:
        """Get all published plans (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        return self._published_plans.copy()

    def clear_plans(self) -> None:
        """Clear all published plans (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        self._published_plans.clear()
        self._published_message_ids.clear()
