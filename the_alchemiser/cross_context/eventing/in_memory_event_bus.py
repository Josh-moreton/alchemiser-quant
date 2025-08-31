"""Business Unit: utilities | Status: current

In-memory EventBus implementation for synchronous event handling.

This module provides a concrete implementation of the EventBus protocol that handles
events synchronously in the current process with ordered delivery and idempotency.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Type variable for contract types
ContractType = TypeVar("ContractType", bound=BaseModel)


class InMemoryEventBus:
    """In-memory implementation of EventBus for synchronous event processing.

    This implementation provides:
    - Synchronous handler execution in registration order
    - Per-handler idempotency tracking using (handler_id, message_id) pairs
    - Fail-fast error propagation for immediate visibility
    - Thread-safe operation (handlers execute on calling thread)

    The bus maintains handlers grouped by contract type and tracks processed
    message IDs to prevent duplicate side effects when the same event is
    republished.

    Idempotency behavior:
    - Each handler maintains its own set of processed message_ids
    - Re-publishing identical message_id results in skip for that handler
    - New handlers will process all events, even previously published ones

    Error handling:
    - Handler exceptions propagate immediately (fail-fast)
    - Failed handlers do not prevent other handlers from executing
    - Bus state remains consistent even if handlers fail
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty handler and idempotency state."""
        # Map contract type -> list of handlers in registration order
        self._handlers: dict[type[BaseModel], list[Callable[[Any], None]]] = defaultdict(list)

        # Track processed messages per handler: (handler_id, message_id) -> bool
        # Using id(handler) as handler_id for uniqueness
        self._processed_messages: set[tuple[int, UUID]] = set()

    def publish(self, event: ContractType) -> None:
        """Publish an application contract event to registered handlers.

        Executes all handlers for the event's contract type in registration order.
        Handlers that have already processed this message_id are skipped.

        Args:
            event: Application contract with envelope metadata

        Raises:
            ValueError: If event lacks required envelope metadata
            Exception: Any exception from handlers (fail-fast propagation)

        """
        # Validate event has required envelope metadata
        if not hasattr(event, "message_id"):
            raise ValueError("Event must have message_id attribute (envelope metadata)")
        if not hasattr(event, "correlation_id"):
            raise ValueError("Event must have correlation_id attribute (envelope metadata)")

        event_type = type(event)
        message_id = event.message_id

        # Get handlers for this contract type
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(
                "No handlers registered for event type %s (message_id: %s)",
                event_type.__name__,
                message_id,
            )
            return

        logger.debug(
            "Publishing event %s to %d handlers (message_id: %s, correlation_id: %s)",
            event_type.__name__,
            len(handlers),
            message_id,
            event.correlation_id,
        )

        executed_count = 0
        skipped_count = 0

        # Execute handlers in registration order
        for handler in handlers:
            handler_id = id(handler)
            processed_key = (handler_id, message_id)

            # Check idempotency - skip if already processed by this handler
            if processed_key in self._processed_messages:
                logger.debug(
                    "Skipping handler %s for message_id %s (already processed)",
                    handler.__name__ if hasattr(handler, "__name__") else str(handler),
                    message_id,
                )
                skipped_count += 1
                continue

            # Execute handler and mark as processed
            try:
                logger.debug(
                    "Executing handler %s for event %s (message_id: %s)",
                    handler.__name__ if hasattr(handler, "__name__") else str(handler),
                    event_type.__name__,
                    message_id,
                )
                handler(event)
                self._processed_messages.add(processed_key)
                executed_count += 1

            except Exception as e:
                logger.error(
                    "Handler %s failed processing event %s (message_id: %s): %s",
                    handler.__name__ if hasattr(handler, "__name__") else str(handler),
                    event_type.__name__,
                    message_id,
                    e,
                    exc_info=True,
                )
                # Mark as processed even if failed to prevent retry loops
                self._processed_messages.add(processed_key)
                # Re-raise for fail-fast behavior
                raise

        logger.debug(
            "Event publishing complete: %d handlers executed, %d skipped (message_id: %s)",
            executed_count,
            skipped_count,
            message_id,
        )

    def subscribe(
        self, contract_cls: type[ContractType], handler: Callable[[ContractType], None]
    ) -> None:
        """Subscribe a handler to receive events of a specific contract type.

        Args:
            contract_cls: Contract type to subscribe to
            handler: Function to call when events of this type are published

        """
        self._handlers[contract_cls].append(handler)

        logger.debug(
            "Registered handler %s for contract type %s (total handlers: %d)",
            handler.__name__ if hasattr(handler, "__name__") else str(handler),
            contract_cls.__name__,
            len(self._handlers[contract_cls]),
        )

    def reset(self) -> None:
        """Reset idempotency state for testing/development.

        Clears all processed message tracking, allowing events to be reprocessed.
        Does not clear handler registrations.
        """
        processed_count = len(self._processed_messages)
        self._processed_messages.clear()

        logger.debug(
            "Reset event bus idempotency state (%d processed messages cleared)", processed_count
        )

    def get_handler_count(self, contract_cls: type[BaseModel]) -> int:
        """Get the number of registered handlers for a contract type.

        Args:
            contract_cls: Contract type to check

        Returns:
            Number of registered handlers for this type

        """
        return len(self._handlers.get(contract_cls, []))

    def get_processed_count(self) -> int:
        """Get the total number of processed (handler, message_id) pairs.

        Returns:
            Number of processed message/handler combinations

        """
        return len(self._processed_messages)
