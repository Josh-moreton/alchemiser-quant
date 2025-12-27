"""Business Unit: data_quality_monitor | Status: current.

Tests for validation session schemas.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from the_alchemiser.data_quality_monitor.schemas import (
    BatchStatus,
    SessionStatus,
    ValidationBatch,
    ValidationSession,
)


def test_validation_batch_creation() -> None:
    """Test creating a validation batch."""
    batch = ValidationBatch(
        batch_number=0,
        symbols=["AAPL", "GOOGL", "MSFT"],
        status=BatchStatus.PENDING,
    )

    assert batch.batch_number == 0
    assert len(batch.symbols) == 3
    assert batch.status == BatchStatus.PENDING
    assert batch.started_at is None
    assert batch.completed_at is None


def test_validation_session_pending_batches() -> None:
    """Test getting pending batches from session."""
    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.PENDING),
        ValidationBatch(2, ["MSFT"], BatchStatus.PENDING),
        ValidationBatch(3, ["TSLA"], BatchStatus.PROCESSING),
    ]

    session = ValidationSession(
        session_id="test-session",
        correlation_id="test-corr",
        total_symbols=4,
        total_batches=4,
        batches=batches,
        status=SessionStatus.PROCESSING,
        lookback_days=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    pending = session.pending_batches
    assert len(pending) == 2
    assert all(b.status == BatchStatus.PENDING for b in pending)


def test_validation_session_completed_count() -> None:
    """Test counting completed batches."""
    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.COMPLETED),
        ValidationBatch(2, ["MSFT"], BatchStatus.PENDING),
        ValidationBatch(3, ["TSLA"], BatchStatus.FAILED),
    ]

    session = ValidationSession(
        session_id="test-session",
        correlation_id="test-corr",
        total_symbols=4,
        total_batches=4,
        batches=batches,
        status=SessionStatus.PROCESSING,
        lookback_days=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert session.completed_batches_count == 2
    assert session.failed_batches_count == 1


def test_validation_session_is_complete() -> None:
    """Test checking if session is complete."""
    # Not complete - has pending batch
    batches_pending = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.PENDING),
    ]

    session_pending = ValidationSession(
        session_id="test-session",
        correlation_id="test-corr",
        total_symbols=2,
        total_batches=2,
        batches=batches_pending,
        status=SessionStatus.PROCESSING,
        lookback_days=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert not session_pending.is_complete

    # Complete - all batches done
    batches_complete = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.COMPLETED),
    ]

    session_complete = ValidationSession(
        session_id="test-session",
        correlation_id="test-corr",
        total_symbols=2,
        total_batches=2,
        batches=batches_complete,
        status=SessionStatus.COMPLETED,
        lookback_days=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert session_complete.is_complete


def test_validation_session_batch_splitting() -> None:
    """Test that batches are properly sized (max 8 symbols)."""
    # This would be in the session manager, but test the concept
    symbols = [f"SYM{i}" for i in range(25)]
    batch_size = 8

    batches = []
    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i : i + batch_size]
        batch = ValidationBatch(
            batch_number=len(batches),
            symbols=batch_symbols,
            status=BatchStatus.PENDING,
        )
        batches.append(batch)

    # 25 symbols should create 4 batches: 8, 8, 8, 1
    assert len(batches) == 4
    assert len(batches[0].symbols) == 8
    assert len(batches[1].symbols) == 8
    assert len(batches[2].symbols) == 8
    assert len(batches[3].symbols) == 1
