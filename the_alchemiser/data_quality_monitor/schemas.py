"""Business Unit: data_quality_monitor | Status: current.

Schemas for data quality validation session tracking.

Defines DTOs for batch processing state management in DynamoDB.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    """Status of a validation batch."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """Status of a validation session."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ValidationBatch:
    """A batch of symbols to validate (max 8 to respect API rate limits)."""

    batch_number: int
    symbols: list[str]
    status: BatchStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ValidationSession:
    """Tracks the overall validation workflow across multiple batches."""

    session_id: str
    correlation_id: str
    total_symbols: int
    total_batches: int
    batches: list[ValidationBatch]
    status: SessionStatus
    lookback_days: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    @property
    def pending_batches(self) -> list[ValidationBatch]:
        """Get all pending batches."""
        return [b for b in self.batches if b.status == BatchStatus.PENDING]

    @property
    def completed_batches_count(self) -> int:
        """Count of completed batches."""
        return sum(1 for b in self.batches if b.status == BatchStatus.COMPLETED)

    @property
    def failed_batches_count(self) -> int:
        """Count of failed batches."""
        return sum(1 for b in self.batches if b.status == BatchStatus.FAILED)

    @property
    def is_complete(self) -> bool:
        """Check if all batches are done (completed or failed)."""
        return self.completed_batches_count + self.failed_batches_count == self.total_batches


@dataclass(frozen=True)
class SymbolValidationResult:
    """Result of validating a single symbol (stored in DynamoDB)."""

    session_id: str
    symbol: str
    passed: bool
    issues: list[str]
    rows_checked: int
    external_source: str
    validated_at: datetime
