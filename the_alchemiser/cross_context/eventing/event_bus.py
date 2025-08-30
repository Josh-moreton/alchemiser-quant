"""Business Unit: utilities | Status: current

EventBus protocol for publish/subscribe event handling.

This module defines the abstract EventBus interface that enables decoupled
communication between bounded contexts using application contracts as event payloads.
"""

from __future__ import annotations

from typing import Callable, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel

# Type variable for contract types that extend envelope functionality
ContractType = TypeVar("ContractType", bound=BaseModel)


class EventBus(Protocol):
    """Protocol for publishing and subscribing to application contract events.
    
    This EventBus abstraction enables decoupled communication between bounded contexts
    using existing *ContractV1 objects as event payloads. The bus provides:
    
    - Synchronous event delivery with ordered handler execution
    - Idempotency guards based on message_id to prevent duplicate processing
    - Type-safe subscription with contract class matching
    
    Design decisions:
    - Events are the existing application contracts (no additional wrapper needed)
    - Handlers execute synchronously in registration order (documented guarantee)
    - Per-handler idempotency tracking prevents duplicate side effects
    - Handler exceptions propagate immediately (fail-fast for visibility)
    
    Example usage:
        # Publishing an event
        signal = SignalContractV1(...)
        bus.publish(signal)
        
        # Subscribing to events
        def handle_signal(signal: SignalContractV1) -> None:
            # Process signal...
            pass
        
        bus.subscribe(SignalContractV1, handle_signal)
    """
    
    def publish(self, event: ContractType) -> None:
        """Publish an application contract as an event.
        
        The event will be delivered to all registered handlers for the contract type
        in registration order. Idempotency is handled automatically - if the same
        message_id has been processed by a handler before, it will be skipped.
        
        Args:
            event: Application contract instance with envelope metadata
                  (must have message_id, correlation_id, causation_id attributes)
        
        Raises:
            ValueError: If event lacks required envelope metadata
            Exception: Any exception raised by event handlers (fail-fast behavior)
        """
        ...
    
    def subscribe(
        self, 
        contract_cls: type[ContractType], 
        handler: Callable[[ContractType], None]
    ) -> None:
        """Subscribe a handler to receive events of a specific contract type.
        
        Handlers are executed in registration order when matching events are published.
        Each handler maintains its own idempotency tracking based on message_id.
        
        Args:
            contract_cls: Contract type to subscribe to (e.g., SignalContractV1)
            handler: Function that processes the contract event
                    Must accept single argument of contract_cls type
                    Should not return a value (return ignored)
        
        Note:
            Multiple handlers can be registered for the same contract type.
            Registration order determines execution order.
        """
        ...
    
    def reset(self) -> None:
        """Reset the event bus state for testing/development.
        
        This clears all processed message_id tracking, allowing messages to be
        reprocessed. Primarily intended for testing scenarios.
        
        Warning:
            This does not unregister handlers, only clears idempotency state.
        """
        ...