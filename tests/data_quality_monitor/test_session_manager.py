"""Business Unit: data_quality_monitor | Status: current.

Tests for validation session manager.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from the_alchemiser.data_quality_monitor.schemas import (
    BatchStatus,
    SessionStatus,
)
from the_alchemiser.data_quality_monitor.session_manager import (
    SessionManagerError,
    ValidationSessionManager,
)


@pytest.fixture
def mock_dynamodb_table() -> Mock:
    """Create a mock DynamoDB table."""
    table = Mock()
    table.put_item = Mock()
    table.get_item = Mock()
    table.query = Mock()
    return table


@pytest.fixture
def session_manager(mock_dynamodb_table: Mock) -> ValidationSessionManager:
    """Create session manager with mocked DynamoDB."""
    with patch("boto3.resource") as mock_boto:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_dynamodb_table
        mock_boto.return_value = mock_dynamodb

        manager = ValidationSessionManager(table_name="test-table")
        manager.table = mock_dynamodb_table
        return manager


def test_create_session_splits_into_batches(session_manager: ValidationSessionManager) -> None:
    """Test that create_session splits symbols into batches of 8."""
    symbols = [f"SYM{i}" for i in range(25)]

    session = session_manager.create_session(
        session_id="test-session",
        correlation_id="test-corr",
        symbols=symbols,
        lookback_days=5,
        batch_size=8,
    )

    # 25 symbols should create 4 batches
    assert session.total_batches == 4
    assert len(session.batches) == 4

    # First three batches have 8 symbols
    assert len(session.batches[0].symbols) == 8
    assert len(session.batches[1].symbols) == 8
    assert len(session.batches[2].symbols) == 8

    # Last batch has 1 symbol
    assert len(session.batches[3].symbols) == 1

    # All batches start as pending
    assert all(b.status == BatchStatus.PENDING for b in session.batches)


def test_create_session_persists_to_dynamodb(
    session_manager: ValidationSessionManager,
    mock_dynamodb_table: Mock,
) -> None:
    """Test that create_session writes to DynamoDB."""
    symbols = ["AAPL", "GOOGL", "MSFT"]

    session_manager.create_session(
        session_id="test-session",
        correlation_id="test-corr",
        symbols=symbols,
        lookback_days=5,
        batch_size=8,
    )

    # Verify put_item was called
    mock_dynamodb_table.put_item.assert_called_once()

    # Verify the item structure
    call_args = mock_dynamodb_table.put_item.call_args
    item = call_args.kwargs["Item"]

    assert item["PK"] == "SESSION#test-session"
    assert item["SK"] == "METADATA"
    assert item["session_id"] == "test-session"
    assert item["correlation_id"] == "test-corr"
    assert item["total_symbols"] == 3
    assert item["total_batches"] == 1


def test_update_batch_status_marks_processing(
    session_manager: ValidationSessionManager,
    mock_dynamodb_table: Mock,
) -> None:
    """Test updating batch status to PROCESSING."""
    # Setup: create a session first
    symbols = ["AAPL", "GOOGL"]
    session = session_manager.create_session(
        session_id="test-session",
        correlation_id="test-corr",
        symbols=symbols,
        lookback_days=5,
        batch_size=8,
    )

    # Mock get_item to return the session
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "PK": "SESSION#test-session",
            "SK": "METADATA",
            "session_id": "test-session",
            "correlation_id": "test-corr",
            "total_symbols": 2,
            "total_batches": 1,
            "batches": [
                {
                    "batch_number": 0,
                    "symbols": ["AAPL", "GOOGL"],
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "error_message": None,
                }
            ],
            "status": "pending",
            "lookback_days": 5,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": None,
        }
    }

    # Update batch to PROCESSING
    updated_session = session_manager.update_batch_status(
        session_id="test-session",
        batch_number=0,
        status=BatchStatus.PROCESSING,
    )

    # Verify batch status changed
    assert updated_session.batches[0].status == BatchStatus.PROCESSING
    assert updated_session.batches[0].started_at is not None
    assert updated_session.status == SessionStatus.PROCESSING


def test_update_batch_status_marks_completed(
    session_manager: ValidationSessionManager,
    mock_dynamodb_table: Mock,
) -> None:
    """Test updating batch status to COMPLETED."""
    now = datetime.now(UTC)

    # Mock get_item to return a processing session
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "PK": "SESSION#test-session",
            "SK": "METADATA",
            "session_id": "test-session",
            "correlation_id": "test-corr",
            "total_symbols": 2,
            "total_batches": 1,
            "batches": [
                {
                    "batch_number": 0,
                    "symbols": ["AAPL", "GOOGL"],
                    "status": "processing",
                    "started_at": now.isoformat(),
                    "completed_at": None,
                    "error_message": None,
                }
            ],
            "status": "processing",
            "lookback_days": 5,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "completed_at": None,
        }
    }

    # Update batch to COMPLETED
    updated_session = session_manager.update_batch_status(
        session_id="test-session",
        batch_number=0,
        status=BatchStatus.COMPLETED,
    )

    # Verify batch is completed
    assert updated_session.batches[0].status == BatchStatus.COMPLETED
    assert updated_session.batches[0].completed_at is not None

    # Session should be COMPLETED (all batches done)
    assert updated_session.status == SessionStatus.COMPLETED


def test_calculate_session_status_all_pending() -> None:
    """Test session status calculation when all batches pending."""
    from the_alchemiser.data_quality_monitor.schemas import ValidationBatch

    manager = ValidationSessionManager(table_name="test")

    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.PENDING),
        ValidationBatch(1, ["GOOGL"], BatchStatus.PENDING),
    ]

    status = manager._calculate_session_status(batches)
    assert status == SessionStatus.PENDING


def test_calculate_session_status_processing() -> None:
    """Test session status calculation when batches are processing."""
    from the_alchemiser.data_quality_monitor.schemas import ValidationBatch

    manager = ValidationSessionManager(table_name="test")

    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.PROCESSING),
    ]

    status = manager._calculate_session_status(batches)
    assert status == SessionStatus.PROCESSING


def test_calculate_session_status_all_complete() -> None:
    """Test session status calculation when all batches complete."""
    from the_alchemiser.data_quality_monitor.schemas import ValidationBatch

    manager = ValidationSessionManager(table_name="test")

    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.COMPLETED),
        ValidationBatch(2, ["MSFT"], BatchStatus.COMPLETED),
    ]

    status = manager._calculate_session_status(batches)
    assert status == SessionStatus.COMPLETED


def test_calculate_session_status_with_failures() -> None:
    """Test session status calculation with failed batches."""
    from the_alchemiser.data_quality_monitor.schemas import ValidationBatch

    manager = ValidationSessionManager(table_name="test")

    # Mix of completed and failed - session is COMPLETED (all batches done)
    batches = [
        ValidationBatch(0, ["AAPL"], BatchStatus.COMPLETED),
        ValidationBatch(1, ["GOOGL"], BatchStatus.FAILED),
        ValidationBatch(2, ["MSFT"], BatchStatus.COMPLETED),
    ]

    status = manager._calculate_session_status(batches)
    assert status == SessionStatus.COMPLETED
