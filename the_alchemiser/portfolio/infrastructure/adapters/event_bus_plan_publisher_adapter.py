"""Business Unit: portfolio assessment & management | Status: current

EventBus-based plan publisher adapter.

This adapter implements PlanPublisherPort using the EventBus infrastructure
to enable decoupled communication with the Execution context.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    RebalancePlanContractV1,
)
from the_alchemiser.portfolio.application.ports import PlanPublisherPort
from the_alchemiser.portfolio.domain.exceptions import PublishError
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError

logger = logging.getLogger(__name__)


class EventBusPlanPublisherAdapter(PlanPublisherPort):
    """EventBus-based plan publisher for Portfolio context.

    This adapter publishes RebalancePlanContractV1 events through the EventBus,
    enabling Execution context to receive plans without direct coupling.
    The EventBus handles idempotency and delivery semantics.
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the publisher with an EventBus instance.

        Args:
            event_bus: EventBus instance for publishing events

        """
        self._event_bus = event_bus

    def publish(self, plan: RebalancePlanContractV1) -> None:
        """Publish a rebalance plan through the EventBus.

        Args:
            plan: Complete plan contract with planned orders

        Raises:
            ValidationError: Invalid plan contract
            PublishError: EventBus publication failure

        """
        try:
            # Basic validation
            if not plan.planned_orders:
                logger.warning(
                    "Publishing plan with no orders (plan_id: %s, message_id: %s)",
                    plan.plan_id,
                    plan.message_id,
                )

            # Validate envelope metadata is present
            if not plan.message_id:
                raise ValidationError("Plan must have message_id (envelope metadata)")
            if not plan.correlation_id:
                raise ValidationError("Plan must have correlation_id (envelope metadata)")

            logger.debug(
                "Publishing rebalance plan via EventBus (plan_id: %s, message_id: %s, orders: %d)",
                plan.plan_id,
                plan.message_id,
                len(plan.planned_orders),
            )

            # Publish through EventBus
            self._event_bus.publish(plan)

            logger.info(
                "Successfully published rebalance plan with %d orders (plan_id: %s, message_id: %s)",
                len(plan.planned_orders),
                plan.plan_id,
                plan.message_id,
            )

        except (ValidationError, ValueError) as e:
            logger.error("Plan validation failed: %s", e)
            raise ValidationError(f"Invalid plan contract: {e}") from e
        except Exception as e:
            logger.error("Failed to publish plan via EventBus: %s", e, exc_info=True)
            raise PublishError(f"EventBus publication failed: {e}") from e
