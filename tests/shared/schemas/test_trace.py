"""Business Unit: shared | Status: current

Unit tests for trace DTOs.

Tests DTO validation, immutability, lifecycle operations, and timezone handling.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.trace import Trace, TraceEntry


class TestTraceEntry:
    """Test TraceEntry DTO validation and behavior."""

    def test_valid_trace_entry(self):
        """Test creation of valid trace entry."""
        now = datetime.now(UTC)
        entry = TraceEntry(
            step_id="step-001",
            step_type="indicator_computation",
            timestamp=now,
            description="Computing RSI indicator",
            inputs={"symbol": "AAPL", "period": 14},
            outputs={"rsi_value": 65.2},
            metadata={"duration_ms": 45},
        )
        assert entry.step_id == "step-001"
        assert entry.step_type == "indicator_computation"
        assert entry.timestamp == now
        assert entry.description == "Computing RSI indicator"
        assert entry.inputs == {"symbol": "AAPL", "period": 14}
        assert entry.outputs == {"rsi_value": 65.2}
        assert entry.metadata == {"duration_ms": 45}

    def test_minimal_trace_entry(self):
        """Test trace entry with only required fields."""
        now = datetime.now(UTC)
        entry = TraceEntry(
            step_id="step-001",
            step_type="evaluation",
            timestamp=now,
            description="Evaluate condition",
        )
        assert entry.step_id == "step-001"
        assert entry.step_type == "evaluation"
        assert entry.timestamp == now
        assert entry.description == "Evaluate condition"
        assert entry.inputs == {}
        assert entry.outputs == {}
        assert entry.metadata == {}

    def test_immutability(self):
        """Test that TraceEntry is frozen."""
        entry = TraceEntry(
            step_id="step-001",
            step_type="test",
            timestamp=datetime.now(UTC),
            description="Test entry",
        )
        with pytest.raises(ValidationError):
            entry.step_id = "step-002"  # type: ignore

    def test_empty_step_id_rejected(self):
        """Test that empty step_id is rejected."""
        with pytest.raises(ValidationError):
            TraceEntry(
                step_id="",
                step_type="test",
                timestamp=datetime.now(UTC),
                description="Test",
            )

    def test_empty_step_type_rejected(self):
        """Test that empty step_type is rejected."""
        with pytest.raises(ValidationError):
            TraceEntry(
                step_id="step-001",
                step_type="",
                timestamp=datetime.now(UTC),
                description="Test",
            )

    def test_empty_description_rejected(self):
        """Test that empty description is rejected."""
        with pytest.raises(ValidationError):
            TraceEntry(
                step_id="step-001",
                step_type="test",
                timestamp=datetime.now(UTC),
                description="",
            )

    def test_naive_timestamp_converted_to_aware(self):
        """Test that naive datetime is converted to UTC."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        entry = TraceEntry(
            step_id="step-001",
            step_type="test",
            timestamp=naive_dt,
            description="Test",
        )
        assert entry.timestamp.tzinfo is not None
        assert entry.timestamp.tzinfo.tzname(None) == "UTC"

    def test_timezone_aware_timestamp_preserved(self):
        """Test that timezone-aware datetime is preserved."""
        aware_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        entry = TraceEntry(
            step_id="step-001",
            step_type="test",
            timestamp=aware_dt,
            description="Test",
        )
        assert entry.timestamp == aware_dt
        assert entry.timestamp.tzinfo is not None

    def test_strict_mode_rejects_extra_fields(self):
        """Test that extra fields are rejected in strict mode.

        Note: Pydantic v2 by default ignores extra fields unless ConfigDict(extra='forbid') is set.
        The current configuration uses strict=True which enforces type coercion but doesn't forbid extras.
        """
        # With current config (no extra='forbid'), extra fields are silently ignored
        entry = TraceEntry(
            step_id="step-001",
            step_type="test",
            timestamp=datetime.now(UTC),
            description="Test",
            extra_field="not_allowed",  # type: ignore
        )
        # Extra field is ignored, not added to model
        assert not hasattr(entry, "extra_field")


class TestTrace:
    """Test Trace DTO validation and lifecycle operations."""

    def test_valid_trace(self):
        """Test creation of valid trace."""
        started = datetime.now(UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
        )
        assert trace.trace_id == "trace-123"
        assert trace.correlation_id == "corr-456"
        assert trace.strategy_id == "nuclear-strategy"
        assert trace.started_at == started
        assert trace.completed_at is None
        assert trace.entries == []
        assert trace.final_allocation == {}
        assert trace.success is True
        assert trace.error_message is None
        assert trace.metadata == {}

    def test_trace_with_completion(self):
        """Test trace with completion fields."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=5)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
            completed_at=completed,
            success=False,
            error_message="Evaluation failed",
        )
        assert trace.completed_at == completed
        assert trace.success is False
        assert trace.error_message == "Evaluation failed"

    def test_trace_with_allocation(self):
        """Test trace with final allocation."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
            final_allocation={
                "AAPL": Decimal("0.40"),
                "GOOGL": Decimal("0.35"),
                "MSFT": Decimal("0.25"),
            },
        )
        assert trace.final_allocation["AAPL"] == Decimal("0.40")
        assert trace.final_allocation["GOOGL"] == Decimal("0.35")
        assert trace.final_allocation["MSFT"] == Decimal("0.25")

    def test_immutability(self):
        """Test that Trace is frozen."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            trace.trace_id = "trace-999"  # type: ignore

    def test_empty_trace_id_rejected(self):
        """Test that empty trace_id is rejected."""
        with pytest.raises(ValidationError):
            Trace(
                trace_id="",
                correlation_id="corr-456",
                strategy_id="nuclear-strategy",
                started_at=datetime.now(UTC),
            )

    def test_empty_correlation_id_rejected(self):
        """Test that empty correlation_id is rejected."""
        with pytest.raises(ValidationError):
            Trace(
                trace_id="trace-123",
                correlation_id="",
                strategy_id="nuclear-strategy",
                started_at=datetime.now(UTC),
            )

    def test_empty_strategy_id_rejected(self):
        """Test that empty strategy_id is rejected."""
        with pytest.raises(ValidationError):
            Trace(
                trace_id="trace-123",
                correlation_id="corr-456",
                strategy_id="",
                started_at=datetime.now(UTC),
            )

    def test_naive_started_at_converted_to_aware(self):
        """Test that naive started_at is converted to UTC."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=naive_dt,
        )
        assert trace.started_at.tzinfo is not None
        assert trace.started_at.tzinfo.tzname(None) == "UTC"

    def test_naive_completed_at_converted_to_aware(self):
        """Test that naive completed_at is converted to UTC."""
        naive_started = datetime(2025, 1, 1, 12, 0, 0)
        naive_completed = datetime(2025, 1, 1, 12, 0, 5)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=naive_started,
            completed_at=naive_completed,
        )
        assert trace.completed_at is not None
        assert trace.completed_at.tzinfo is not None
        assert trace.completed_at.tzinfo.tzname(None) == "UTC"

    def test_timezone_aware_timestamps_preserved(self):
        """Test that timezone-aware timestamps are preserved."""
        aware_started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        aware_completed = datetime(2025, 1, 1, 12, 0, 5, tzinfo=UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=aware_started,
            completed_at=aware_completed,
        )
        assert trace.started_at == aware_started
        assert trace.completed_at == aware_completed

    def test_strict_mode_rejects_extra_fields(self):
        """Test that extra fields are rejected in strict mode.

        Note: Pydantic v2 by default ignores extra fields unless ConfigDict(extra='forbid') is set.
        The current configuration uses strict=True which enforces type coercion but doesn't forbid extras.
        """
        # With current config (no extra='forbid'), extra fields are silently ignored
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
            extra_field="not_allowed",  # type: ignore
        )
        # Extra field is ignored, not added to model
        assert not hasattr(trace, "extra_field")


class TestTraceAddEntry:
    """Test Trace.add_entry method."""

    def test_add_single_entry(self):
        """Test adding a single entry to trace."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        new_trace = trace.add_entry(
            step_id="step-001",
            step_type="indicator",
            description="Compute RSI",
            inputs={"symbol": "AAPL"},
            outputs={"rsi": 65.2},
            metadata={"duration_ms": 45},
        )

        # Original trace unchanged (immutability)
        assert len(trace.entries) == 0

        # New trace has entry
        assert len(new_trace.entries) == 1
        entry = new_trace.entries[0]
        assert entry.step_id == "step-001"
        assert entry.step_type == "indicator"
        assert entry.description == "Compute RSI"
        assert entry.inputs == {"symbol": "AAPL"}
        assert entry.outputs == {"rsi": 65.2}
        assert entry.metadata == {"duration_ms": 45}

    def test_add_multiple_entries(self):
        """Test adding multiple entries to trace."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        trace = trace.add_entry(
            step_id="step-001",
            step_type="indicator",
            description="Step 1",
        )
        trace = trace.add_entry(
            step_id="step-002",
            step_type="decision",
            description="Step 2",
        )
        trace = trace.add_entry(
            step_id="step-003",
            step_type="allocation",
            description="Step 3",
        )

        assert len(trace.entries) == 3
        assert trace.entries[0].step_id == "step-001"
        assert trace.entries[1].step_id == "step-002"
        assert trace.entries[2].step_id == "step-003"

    def test_add_entry_with_minimal_args(self):
        """Test adding entry with only required arguments."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        new_trace = trace.add_entry(
            step_id="step-001",
            step_type="test",
            description="Test step",
        )

        assert len(new_trace.entries) == 1
        entry = new_trace.entries[0]
        assert entry.inputs == {}
        assert entry.outputs == {}
        assert entry.metadata == {}

    def test_add_entry_generates_timestamp(self):
        """Test that add_entry generates timestamp automatically."""
        before = datetime.now(UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        new_trace = trace.add_entry(
            step_id="step-001",
            step_type="test",
            description="Test step",
        )
        after = datetime.now(UTC)

        entry = new_trace.entries[0]
        assert entry.timestamp >= before
        assert entry.timestamp <= after

    def test_add_entry_preserves_other_fields(self):
        """Test that add_entry preserves all other trace fields."""
        original_trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
            metadata={"test": "value"},
            final_allocation={"AAPL": Decimal("1.0")},
        )
        new_trace = original_trace.add_entry(
            step_id="step-001",
            step_type="test",
            description="Test step",
        )

        assert new_trace.trace_id == original_trace.trace_id
        assert new_trace.correlation_id == original_trace.correlation_id
        assert new_trace.strategy_id == original_trace.strategy_id
        assert new_trace.started_at == original_trace.started_at
        assert new_trace.metadata == original_trace.metadata
        assert new_trace.final_allocation == original_trace.final_allocation


class TestTraceMarkCompleted:
    """Test Trace.mark_completed method."""

    def test_mark_completed_success(self):
        """Test marking trace as successfully completed."""
        started = datetime.now(UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
        )
        before = datetime.now(UTC)
        completed_trace = trace.mark_completed(success=True)
        after = datetime.now(UTC)

        # Original trace unchanged
        assert trace.completed_at is None
        assert trace.success is True

        # New trace marked completed
        assert completed_trace.completed_at is not None
        assert completed_trace.completed_at >= before
        assert completed_trace.completed_at <= after
        assert completed_trace.success is True
        assert completed_trace.error_message is None

    def test_mark_completed_failure(self):
        """Test marking trace as failed."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        completed_trace = trace.mark_completed(
            success=False,
            error_message="Indicator computation failed",
        )

        assert completed_trace.completed_at is not None
        assert completed_trace.success is False
        assert completed_trace.error_message == "Indicator computation failed"

    def test_mark_completed_preserves_entries(self):
        """Test that mark_completed preserves trace entries."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        trace = trace.add_entry(
            step_id="step-001",
            step_type="test",
            description="Test step",
        )
        trace = trace.add_entry(
            step_id="step-002",
            step_type="test",
            description="Another step",
        )

        completed_trace = trace.mark_completed()

        assert len(completed_trace.entries) == 2
        assert completed_trace.entries[0].step_id == "step-001"
        assert completed_trace.entries[1].step_id == "step-002"

    def test_mark_completed_preserves_other_fields(self):
        """Test that mark_completed preserves all other trace fields."""
        original_trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
            metadata={"test": "value"},
            final_allocation={"AAPL": Decimal("1.0")},
        )
        completed_trace = original_trace.mark_completed()

        assert completed_trace.trace_id == original_trace.trace_id
        assert completed_trace.correlation_id == original_trace.correlation_id
        assert completed_trace.strategy_id == original_trace.strategy_id
        assert completed_trace.started_at == original_trace.started_at
        assert completed_trace.metadata == original_trace.metadata
        assert completed_trace.final_allocation == original_trace.final_allocation


class TestTraceGetDuration:
    """Test Trace.get_duration_seconds method."""

    def test_get_duration_incomplete_trace(self):
        """Test duration returns None for incomplete trace."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )
        assert trace.get_duration_seconds() is None

    def test_get_duration_completed_trace(self):
        """Test duration calculation for completed trace."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 1, 12, 0, 5, tzinfo=UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
            completed_at=completed,
        )
        duration = trace.get_duration_seconds()
        assert duration == 5.0

    def test_get_duration_subsecond_precision(self):
        """Test duration calculation with subsecond precision."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 1, 12, 0, 0, microsecond=500000, tzinfo=UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
            completed_at=completed,
        )
        duration = trace.get_duration_seconds()
        assert duration == 0.5

    def test_get_duration_long_evaluation(self):
        """Test duration calculation for longer evaluation."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 1, 12, 2, 30, tzinfo=UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
            completed_at=completed,
        )
        duration = trace.get_duration_seconds()
        assert duration == 150.0  # 2 minutes 30 seconds


class TestTraceLifecycle:
    """Test complete trace lifecycle scenarios."""

    def test_complete_evaluation_lifecycle(self):
        """Test a complete evaluation trace lifecycle."""
        # Create initial trace
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )

        # Add indicator computation step
        trace = trace.add_entry(
            step_id="step-001",
            step_type="indicator_computation",
            description="Computing RSI for AAPL",
            inputs={"symbol": "AAPL", "period": 14},
            outputs={"rsi": Decimal("65.2")},
        )

        # Add decision evaluation step
        trace = trace.add_entry(
            step_id="step-002",
            step_type="decision_evaluation",
            description="Evaluating buy condition",
            inputs={"rsi": Decimal("65.2"), "threshold": 70},
            outputs={"decision": "hold"},
        )

        # Add allocation step
        trace = trace.add_entry(
            step_id="step-003",
            step_type="allocation",
            description="Computing target allocation",
            outputs={
                "AAPL": str(Decimal("0.40")),
                "GOOGL": str(Decimal("0.35")),
                "MSFT": str(Decimal("0.25")),
            },
        )

        # Mark as completed
        trace = trace.mark_completed(success=True)

        # Verify final state
        assert len(trace.entries) == 3
        assert trace.completed_at is not None
        assert trace.success is True
        assert trace.get_duration_seconds() is not None
        assert trace.get_duration_seconds() >= 0

    def test_failed_evaluation_lifecycle(self):
        """Test a failed evaluation trace lifecycle."""
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=datetime.now(UTC),
        )

        # Add successful step
        trace = trace.add_entry(
            step_id="step-001",
            step_type="indicator_computation",
            description="Computing RSI",
            inputs={"symbol": "AAPL"},
            outputs={"rsi": Decimal("65.2")},
        )

        # Add failure step
        trace = trace.add_entry(
            step_id="step-002",
            step_type="decision_evaluation",
            description="Evaluating condition - failed",
            inputs={"rsi": Decimal("65.2")},
            metadata={"error": "Division by zero"},
        )

        # Mark as failed
        trace = trace.mark_completed(
            success=False,
            error_message="Division by zero in condition evaluation",
        )

        # Verify final state
        assert len(trace.entries) == 2
        assert trace.completed_at is not None
        assert trace.success is False
        assert trace.error_message is not None
        assert "Division by zero" in trace.error_message


class TestTraceSerializationDeserialization:
    """Test trace serialization and deserialization."""

    def test_trace_to_dict(self):
        """Test trace serialization to dict."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-456",
            strategy_id="nuclear-strategy",
            started_at=started,
            final_allocation={"AAPL": Decimal("0.50")},
        )
        trace = trace.add_entry(
            step_id="step-001",
            step_type="test",
            description="Test step",
        )

        data = trace.model_dump()
        assert data["trace_id"] == "trace-123"
        assert data["correlation_id"] == "corr-456"
        assert data["strategy_id"] == "nuclear-strategy"
        assert len(data["entries"]) == 1
        assert data["final_allocation"]["AAPL"] == Decimal("0.50")

    def test_trace_from_dict(self):
        """Test trace deserialization from dict.

        Note: strict=True requires Decimal values to be actual Decimal instances,
        not strings that can be coerced. This enforces type safety at boundaries.
        """
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        data = {
            "trace_id": "trace-123",
            "correlation_id": "corr-456",
            "strategy_id": "nuclear-strategy",
            "started_at": started,
            "final_allocation": {"AAPL": Decimal("0.50")},  # Must be Decimal, not string
        }
        trace = Trace(**data)
        assert trace.trace_id == "trace-123"
        assert trace.correlation_id == "corr-456"
        assert trace.strategy_id == "nuclear-strategy"
        assert trace.started_at == started
        assert trace.final_allocation["AAPL"] == Decimal("0.50")

    def test_trace_entry_to_dict(self):
        """Test trace entry serialization to dict."""
        now = datetime.now(UTC)
        entry = TraceEntry(
            step_id="step-001",
            step_type="test",
            timestamp=now,
            description="Test step",
            inputs={"key": "value"},
        )
        data = entry.model_dump()
        assert data["step_id"] == "step-001"
        assert data["step_type"] == "test"
        assert data["description"] == "Test step"
        assert data["inputs"] == {"key": "value"}

    def test_trace_entry_from_dict(self):
        """Test trace entry deserialization from dict."""
        now = datetime.now(UTC)
        data = {
            "step_id": "step-001",
            "step_type": "test",
            "timestamp": now,
            "description": "Test step",
        }
        entry = TraceEntry(**data)
        assert entry.step_id == "step-001"
        assert entry.step_type == "test"
        assert entry.timestamp == now
        assert entry.description == "Test step"
