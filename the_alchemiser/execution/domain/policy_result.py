"""Business Unit: utilities; Status: current.

Pure domain policy result objects.

These value objects represent the results of policy validation and adjustment
without any dependencies on external frameworks or DTOs. They are used within
the domain layer to maintain purity and separation of concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest


@dataclass(frozen=True)
class PolicyWarning:
    """Domain value object for policy warnings.

    Represents warnings generated during order validation that allow the order
    to proceed but with adjustments or notifications.
    """

    policy_name: str  # e.g., "FractionabilityPolicy", "PositionPolicy"
    action: Literal["adjust", "allow", "reject"]
    message: str
    original_value: str | None = None
    adjusted_value: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"


@dataclass(frozen=True)
class PolicyResult:
    """Domain value object representing the result of a policy validation.

    Contains the order request (potentially adjusted), approval status,
    warnings, and metadata from policy processing. This is the pure domain
    equivalent of AdjustedOrderRequestDTO.
    """

    # The order request after policy processing (may be adjusted)
    order_request: OrderRequest

    # Policy decision
    is_approved: bool

    # Original quantity if adjustments were made
    original_quantity: Decimal | None = None

    # Reason for adjustment or rejection
    adjustment_reason: str | None = None
    rejection_reason: str | None = None

    # Policy warnings and metadata
    warnings: tuple[PolicyWarning, ...] = ()  # Immutable tuple instead of list
    policy_metadata: dict[str, str] | None = None  # Will be created new each time

    # Risk assessment
    total_risk_score: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate consistency of policy result fields."""
        if not self.is_approved and not self.rejection_reason:
            raise ValueError("Rejected orders must have a rejection reason")

        if self.is_approved and self.rejection_reason:
            raise ValueError("Approved orders cannot have a rejection reason")

    @property
    def has_adjustments(self) -> bool:
        """Check if the order was adjusted by policies."""
        return (
            self.original_quantity is not None
            and self.original_quantity != self.order_request.quantity.value
        )

    @property
    def has_warnings(self) -> bool:
        """Check if policies generated warnings."""
        return len(self.warnings) > 0

    def with_warnings(self, new_warnings: tuple[PolicyWarning, ...]) -> PolicyResult:
        """Create a new PolicyResult with additional warnings (immutable pattern)."""
        combined_warnings = self.warnings + new_warnings
        return PolicyResult(
            order_request=self.order_request,
            is_approved=self.is_approved,
            original_quantity=self.original_quantity,
            adjustment_reason=self.adjustment_reason,
            rejection_reason=self.rejection_reason,
            warnings=combined_warnings,
            policy_metadata=self.policy_metadata,
            total_risk_score=self.total_risk_score,
        )

    def with_metadata(self, metadata: dict[str, str]) -> PolicyResult:
        """Create a new PolicyResult with updated metadata (immutable pattern)."""
        combined_metadata = (self.policy_metadata or {}).copy()
        combined_metadata.update(metadata)
        return PolicyResult(
            order_request=self.order_request,
            is_approved=self.is_approved,
            original_quantity=self.original_quantity,
            adjustment_reason=self.adjustment_reason,
            rejection_reason=self.rejection_reason,
            warnings=self.warnings,
            policy_metadata=combined_metadata,
            total_risk_score=self.total_risk_score,
        )

    def with_risk_score(self, risk_score: Decimal) -> PolicyResult:
        """Create a new PolicyResult with updated risk score (immutable pattern)."""
        new_total_score = self.total_risk_score + risk_score
        return PolicyResult(
            order_request=self.order_request,
            is_approved=self.is_approved,
            original_quantity=self.original_quantity,
            adjustment_reason=self.adjustment_reason,
            rejection_reason=self.rejection_reason,
            warnings=self.warnings,
            policy_metadata=self.policy_metadata,
            total_risk_score=new_total_score,
        )


def create_approved_result(
    order_request: OrderRequest,
    original_quantity: Decimal | None = None,
    adjustment_reason: str | None = None,
) -> PolicyResult:
    """Helper function to create an approved policy result."""
    return PolicyResult(
        order_request=order_request,
        is_approved=True,
        original_quantity=original_quantity,
        adjustment_reason=adjustment_reason,
    )


def create_rejected_result(
    order_request: OrderRequest,
    rejection_reason: str,
) -> PolicyResult:
    """Helper function to create a rejected policy result."""
    return PolicyResult(
        order_request=order_request,
        is_approved=False,
        rejection_reason=rejection_reason,
    )
