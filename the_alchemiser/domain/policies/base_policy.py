"""Business Unit: utilities; Status: current.

Base Policy Protocol

Defines the common interface that all order validation policies must implement.
Uses pure domain objects to maintain domain layer purity.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.domain.policies.policy_result import PolicyResult
from the_alchemiser.execution.orders.order_request import OrderRequest


class OrderPolicy(Protocol):
    """Base protocol for order validation and adjustment policies.

    All concrete policy implementations must implement this interface
    to be used by the PolicyOrchestrator. Uses pure domain objects
    to maintain separation of concerns and domain layer purity.
    """

    def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
        """Validate and potentially adjust an order request.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with validation results and any adjustments

        """
        ...

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...
