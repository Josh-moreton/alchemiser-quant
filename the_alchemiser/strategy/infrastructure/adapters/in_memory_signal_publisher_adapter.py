"""Business Unit: strategy & signal generation | Status: current

In-memory signal publisher adapter for testing and development.
"""

from typing import List
from uuid import UUID
from the_alchemiser.strategy.application.ports import SignalPublisherPort
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1


class InMemorySignalPublisherAdapter(SignalPublisherPort):
    """Simple in-memory signal publisher for testing."""
    
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
        # Basic validation
        if not signal.symbol:
            from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError
            raise ValidationError("Signal must have a symbol")
        
        # Idempotency check
        if signal.message_id not in self._published_message_ids:
            self._published_signals.append(signal)
            self._published_message_ids.add(signal.message_id)
    
    def get_published_signals(self) -> List[SignalContractV1]:
        """Get all published signals (for testing purposes)."""
        return self._published_signals.copy()
    
    def clear_signals(self) -> None:
        """Clear all published signals (for testing purposes)."""
        self._published_signals.clear()
        self._published_message_ids.clear()