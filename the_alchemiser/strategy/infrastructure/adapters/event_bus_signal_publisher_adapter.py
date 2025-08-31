"""Business Unit: strategy & signal generation | Status: current

EventBus-based signal publisher adapter.

This adapter implements SignalPublisherPort using the EventBus infrastructure
to enable decoupled communication with the Portfolio context.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1
from the_alchemiser.strategy.application.ports import SignalPublisherPort
from the_alchemiser.strategy.domain.exceptions import PublishError

logger = logging.getLogger(__name__)


class EventBusSignalPublisherAdapter(SignalPublisherPort):
    """EventBus-based signal publisher for Strategy context.

    This adapter publishes SignalContractV1 events through the EventBus,
    enabling Portfolio context to receive signals without direct coupling.
    The EventBus handles idempotency and delivery semantics.
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the publisher with an EventBus instance.

        Args:
            event_bus: EventBus instance for publishing events

        """
        self._event_bus = event_bus

    def publish(self, signal: SignalContractV1) -> None:
        """Publish a strategy signal through the EventBus.

        Args:
            signal: Complete signal contract with envelope metadata

        Raises:
            ValidationError: Invalid signal contract
            PublishError: EventBus publication failure

        """
        try:
            # Basic validation
            if not signal.symbol:
                raise ValidationError("Signal must have a symbol")

            # Validate envelope metadata is present
            if not signal.message_id:
                raise ValidationError("Signal must have message_id (envelope metadata)")
            if not signal.correlation_id:
                raise ValidationError("Signal must have correlation_id (envelope metadata)")

            logger.debug(
                "Publishing signal %s via EventBus (message_id: %s, correlation_id: %s)",
                signal.symbol,
                signal.message_id,
                signal.correlation_id,
            )

            # Publish through EventBus
            self._event_bus.publish(signal)

            logger.info(
                "Successfully published signal %s for %s allocation (message_id: %s)",
                signal.action,
                signal.symbol,
                signal.message_id,
            )

        except (ValidationError, ValueError) as e:
            logger.error("Signal validation failed: %s", e)
            raise ValidationError(f"Invalid signal contract: {e}") from e
        except Exception as e:
            logger.error("Failed to publish signal via EventBus: %s", e, exc_info=True)
            raise PublishError(f"EventBus publication failed: {e}") from e
