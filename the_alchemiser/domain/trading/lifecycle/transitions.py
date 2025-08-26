"""Domain-level declaration of valid order lifecycle transitions.

Separated from application layer so business rules live in domain.
"""

from __future__ import annotations

from .states import OrderLifecycleState

# (from_state, to_state) -> reason_code
VALID_TRANSITIONS: dict[tuple[OrderLifecycleState, OrderLifecycleState], str] = {
    # From NEW
    (OrderLifecycleState.NEW, OrderLifecycleState.VALIDATED): "order_validated",
    (OrderLifecycleState.NEW, OrderLifecycleState.REJECTED): "validation_failed",
    # From VALIDATED
    (
        OrderLifecycleState.VALIDATED,
        OrderLifecycleState.QUEUED,
    ): "queued_for_submission",
    (OrderLifecycleState.VALIDATED, OrderLifecycleState.SUBMITTED): "direct_submission",
    (
        OrderLifecycleState.VALIDATED,
        OrderLifecycleState.REJECTED,
    ): "pre_submission_rejection",
    # From QUEUED
    (OrderLifecycleState.QUEUED, OrderLifecycleState.SUBMITTED): "submitted_to_broker",
    (
        OrderLifecycleState.QUEUED,
        OrderLifecycleState.CANCELLED,
    ): "cancelled_while_queued",
    (OrderLifecycleState.QUEUED, OrderLifecycleState.EXPIRED): "expired_while_queued",
    # From SUBMITTED
    (
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.ACKNOWLEDGED,
    ): "broker_acknowledged",
    (OrderLifecycleState.SUBMITTED, OrderLifecycleState.FILLED): "direct_fill",
    (
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.PARTIALLY_FILLED,
    ): "direct_partial_fill",
    (OrderLifecycleState.SUBMITTED, OrderLifecycleState.REJECTED): "broker_rejected",
    (
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.CANCEL_PENDING,
    ): "cancel_requested",
    (OrderLifecycleState.SUBMITTED, OrderLifecycleState.ERROR): "submission_error",
    # From ACKNOWLEDGED
    (
        OrderLifecycleState.ACKNOWLEDGED,
        OrderLifecycleState.PARTIALLY_FILLED,
    ): "partial_execution",
    (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.FILLED): "full_execution",
    (
        OrderLifecycleState.ACKNOWLEDGED,
        OrderLifecycleState.CANCEL_PENDING,
    ): "cancel_requested",
    (
        OrderLifecycleState.ACKNOWLEDGED,
        OrderLifecycleState.REJECTED,
    ): "post_ack_rejection",
    (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.EXPIRED): "order_expired",
    (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.ERROR): "execution_error",
    # From PARTIALLY_FILLED
    (
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.PARTIALLY_FILLED,
    ): "additional_partial_fill",
    (
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
    ): "completion_fill",
    (
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.CANCEL_PENDING,
    ): "cancel_remaining",
    (
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.ERROR,
    ): "fill_processing_error",
    # From CANCEL_PENDING
    (
        OrderLifecycleState.CANCEL_PENDING,
        OrderLifecycleState.CANCELLED,
    ): "cancel_confirmed",
    (
        OrderLifecycleState.CANCEL_PENDING,
        OrderLifecycleState.PARTIALLY_FILLED,
    ): "late_partial_fill",
    (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.FILLED): "late_full_fill",
    (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.ERROR): "cancel_error",
    # Terminal idempotent
    (OrderLifecycleState.FILLED, OrderLifecycleState.FILLED): "idempotent_filled",
    (
        OrderLifecycleState.CANCELLED,
        OrderLifecycleState.CANCELLED,
    ): "idempotent_cancelled",
    (OrderLifecycleState.REJECTED, OrderLifecycleState.REJECTED): "idempotent_rejected",
    (OrderLifecycleState.EXPIRED, OrderLifecycleState.EXPIRED): "idempotent_expired",
    (OrderLifecycleState.ERROR, OrderLifecycleState.ERROR): "idempotent_error",
}

__all__ = ["VALID_TRANSITIONS"]
