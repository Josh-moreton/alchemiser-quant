"""Business Unit: strategy & signal generation | Status: current

In-memory signal publisher adapter for testing and development.

TODO: Replace with production message broker adapter (e.g., SQS, Redis, EventBridge)
FIXME: This simplified adapter only stores signals in memory
"""

from typing import List
from uuid import UUID
from the_alchemiser.strategy.application.ports import SignalPublisherPort
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1


class InMemorySignalPublisherAdapter(SignalPublisherPort):
    """Simple in-memory signal publisher for testing.
    
    TODO: Replace with production message broker implementation
    FIXME: No persistence or delivery guarantees in current implementation
    """
    
    def __init__(self) -> None:
        self._published_signals: List[SignalContractV1] = []
        self._published_message_ids: set[UUID] = set()
    
    def publish(self, signal: SignalContractV1) -> None:
        """Publish a strategy signal to in-memory storage.
        
        Args:
            signal: Complete signal contract with envelope metadata
            
        Raises:
            ValidationError: Invalid signal contract (basic validation)
        """
        # TODO: Replace basic validation with comprehensive schema validation
        # FIXME: Add proper error handling and logging
        if not signal.symbol:
            from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError
            raise ValidationError("Signal must have a symbol")
        
        # TODO: Replace with distributed idempotency mechanism (e.g., database-backed)
        # FIXME: Idempotency check - current implementation only works within same process
        if signal.message_id not in self._published_message_ids:
            self._published_signals.append(signal)
            self._published_message_ids.add(signal.message_id)
    
    def get_published_signals(self) -> List[SignalContractV1]:
        """Get all published signals (for testing purposes).
        
        TODO: Remove this method in production - only needed for testing
        """
        return self._published_signals.copy()
    
    def clear_signals(self) -> None:
        """Clear all published signals (for testing purposes).
        
        TODO: Remove this method in production - only needed for testing
        """
        self._published_signals.clear()
        self._published_message_ids.clear()