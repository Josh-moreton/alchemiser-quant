"""
Base Policy Protocol

Defines the common interface that all order validation policies must implement.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO, AdjustedOrderRequestDTO


class OrderPolicy(Protocol):
    """
    Base protocol for order validation and adjustment policies.
    
    All concrete policy implementations must implement this interface
    to be used by the PolicyOrchestrator.
    """
    
    def validate_and_adjust(
        self, 
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Validate and potentially adjust an order request.
        
        Args:
            order_request: The original order request to validate
            
        Returns:
            AdjustedOrderRequestDTO with validation results and any adjustments
        """
        ...
    
    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...