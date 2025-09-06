"""Business Unit: portfolio | Status: current.

Base Policy Protocol and Implementation

Defines the common interface that all order validation policies must implement.
Uses pure domain objects to maintain domain layer purity.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.execution.orders.order_request import OrderRequest
from the_alchemiser.execution.types.policy_result import PolicyResult


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


class BasePolicyImpl:
    """Base implementation class for order validation policies.

    Provides common functionality to eliminate code duplication across
    policy implementations, particularly the policy_name property.
    """

    def __init__(self, policy_name: str) -> None:
        """Initialize the base policy implementation.

        Args:
            policy_name: The name of this policy for logging and identification

        """
        self._policy_name = policy_name

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name
