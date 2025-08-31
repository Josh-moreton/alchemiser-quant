"""Business Unit: order execution/placement; Status: current.

Envelope mixin for application contracts providing consistent message metadata.

This module provides the base envelope structure that ensures all application
contracts have consistent metadata for message tracing and correlation across
bounded contexts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EnvelopeV1(BaseModel):
    """Base envelope mixin providing consistent message metadata for all contracts.

    All application contracts should inherit from this to ensure consistent
    message correlation and tracing across bounded contexts.

    Attributes:
        message_id: Unique identifier for this specific contract instance
        correlation_id: Root correlation ID for the entire message chain
        causation_id: ID of the preceding message that caused this one (optional)
        timestamp: UTC timestamp when the contract was created

    """

    message_id: UUID = Field(
        default_factory=uuid4, description="Unique ID for this contract instance"
    )
    correlation_id: UUID = Field(..., description="Root correlation ID for message chain")
    causation_id: UUID | None = Field(None, description="ID of the message that caused this one")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when contract was created",
    )
