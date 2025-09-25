"""Tests for execution idempotency utilities."""

import json
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.utils.execution_idempotency import (
    ExecutionIdempotencyStore,
    generate_execution_plan_hash,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItemDTO


@pytest.fixture
def mock_persistence():
    """Mock persistence handler."""
    return Mock()


@pytest.fixture
def sample_rebalance_plan():
    """Sample rebalance plan for testing."""
    from datetime import datetime, UTC
    
    return RebalancePlanDTO(
        plan_id="test-plan-123",
        correlation_id="test-correlation-456",
        causation_id="test-causation-789",
        timestamp=datetime.now(UTC),
        items=[
            RebalancePlanItemDTO(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.4"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("2000.00"),
                current_value=Decimal("1500.00"),
                trade_amount=Decimal("500.00"),
                action="BUY",
                priority=1,
            ),
            RebalancePlanItemDTO(
                symbol="MSFT",
                current_weight=Decimal("0.2"),
                target_weight=Decimal("0.1"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("500.00"),
                current_value=Decimal("1000.00"),
                trade_amount=Decimal("-500.00"),
                action="SELL",
                priority=2,
            ),
        ],
        total_portfolio_value=Decimal("5000.00"),
        total_trade_value=Decimal("1000.00"),
    )


def test_generate_execution_plan_hash_deterministic(sample_rebalance_plan):
    """Test that execution plan hash generation is deterministic."""
    correlation_id = "test-correlation"
    
    hash1 = generate_execution_plan_hash(sample_rebalance_plan, correlation_id)
    hash2 = generate_execution_plan_hash(sample_rebalance_plan, correlation_id)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex string length
    assert isinstance(hash1, str)


def test_generate_execution_plan_hash_different_plans(sample_rebalance_plan):
    """Test that different plans generate different hashes."""
    correlation_id = "test-correlation"
    
    # Create a modified plan (copy the data and change plan_id)
    plan_data = sample_rebalance_plan.model_dump()
    plan_data["plan_id"] = "different-plan-id"
    modified_plan = RebalancePlanDTO.model_validate(plan_data)
    
    hash1 = generate_execution_plan_hash(sample_rebalance_plan, correlation_id)
    hash2 = generate_execution_plan_hash(modified_plan, correlation_id)
    
    assert hash1 != hash2


def test_generate_execution_plan_hash_different_correlations(sample_rebalance_plan):
    """Test that different correlation IDs generate different hashes."""
    hash1 = generate_execution_plan_hash(sample_rebalance_plan, "correlation-1")
    hash2 = generate_execution_plan_hash(sample_rebalance_plan, "correlation-2")
    
    assert hash1 != hash2


def test_execution_idempotency_store_initialization(mock_persistence):
    """Test ExecutionIdempotencyStore initialization."""
    store = ExecutionIdempotencyStore(mock_persistence)
    assert store._persistence is mock_persistence
    assert store._store_key == "execution_attempts"


def test_has_been_executed_no_previous_attempts(mock_persistence):
    """Test has_been_executed returns False when no previous attempts exist."""
    mock_persistence.read_text.return_value = None
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    result = store.has_been_executed("correlation-123", "hash-456")
    
    assert result is False
    mock_persistence.read_text.assert_called_once_with("execution_attempts")


def test_has_been_executed_with_previous_attempt(mock_persistence):
    """Test has_been_executed returns True when attempt exists."""
    # Setup existing attempts
    existing_attempts = {
        "correlation-123_hash-456": {
            "correlation_id": "correlation-123",
            "execution_plan_hash": "hash-456",
            "success": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    }
    mock_persistence.read_text.return_value = json.dumps(existing_attempts)
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    result = store.has_been_executed("correlation-123", "hash-456")
    
    assert result is True


def test_has_been_executed_different_correlation(mock_persistence):
    """Test has_been_executed returns False for different correlation ID."""
    # Setup existing attempts with different correlation
    existing_attempts = {
        "correlation-123_hash-456": {
            "correlation_id": "correlation-123",
            "execution_plan_hash": "hash-456",
            "success": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    }
    mock_persistence.read_text.return_value = json.dumps(existing_attempts)
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    result = store.has_been_executed("correlation-999", "hash-456")
    
    assert result is False


def test_record_execution_attempt(mock_persistence):
    """Test recording execution attempt."""
    mock_persistence.read_text.return_value = None  # No existing attempts
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    # Mock the timestamp function
    with patch.object(store, '_get_current_timestamp', return_value="2024-01-01T00:00:00Z"):
        store.record_execution_attempt(
            correlation_id="correlation-123",
            execution_plan_hash="hash-456",
            success=True,
            metadata={"orders": 5}
        )
    
    # Verify write was called with correct data
    mock_persistence.write_text.assert_called_once()
    args = mock_persistence.write_text.call_args[0]
    
    assert args[0] == "execution_attempts"  # Key
    written_data = json.loads(args[1])  # Data
    
    expected_key = "correlation-123_hash-456"
    assert expected_key in written_data
    
    record = written_data[expected_key]
    assert record["correlation_id"] == "correlation-123"
    assert record["execution_plan_hash"] == "hash-456"
    assert record["success"] is True
    assert record["timestamp"] == "2024-01-01T00:00:00Z"
    assert record["metadata"] == {"orders": 5}


def test_record_execution_attempt_handles_persistence_error(mock_persistence):
    """Test that record_execution_attempt handles persistence errors gracefully."""
    mock_persistence.read_text.side_effect = Exception("Persistence error")
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    # Should not raise exception despite persistence error
    store.record_execution_attempt(
        correlation_id="correlation-123",
        execution_plan_hash="hash-456",
        success=True
    )


def test_has_been_executed_handles_persistence_error(mock_persistence):
    """Test that has_been_executed handles persistence errors gracefully."""
    mock_persistence.read_text.side_effect = Exception("Persistence error")
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    # Should return False on error to be safe
    result = store.has_been_executed("correlation-123", "hash-456")
    
    assert result is False


def test_make_key():
    """Test key generation for storage."""
    store = ExecutionIdempotencyStore(Mock())
    
    key = store._make_key("correlation-123", "hash-456")
    
    assert key == "correlation-123_hash-456"


def test_load_attempts_empty_persistence(mock_persistence):
    """Test loading attempts when persistence is empty."""
    mock_persistence.read_text.return_value = None
    
    store = ExecutionIdempotencyStore(mock_persistence)
    attempts = store._load_attempts()
    
    assert attempts == {}


def test_load_attempts_with_data(mock_persistence):
    """Test loading attempts with existing data."""
    test_data = {"key1": "value1", "key2": "value2"}
    mock_persistence.read_text.return_value = json.dumps(test_data)
    
    store = ExecutionIdempotencyStore(mock_persistence)
    attempts = store._load_attempts()
    
    assert attempts == test_data


def test_get_current_timestamp(mock_persistence):
    """Test timestamp generation."""
    from datetime import datetime, UTC
    
    store = ExecutionIdempotencyStore(mock_persistence)
    
    # Just test that it returns a valid ISO format timestamp
    timestamp = store._get_current_timestamp()
    
    # Should be able to parse back to datetime
    parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    assert parsed.tzinfo is not None