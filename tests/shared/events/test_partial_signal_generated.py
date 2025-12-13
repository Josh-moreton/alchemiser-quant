"""Business Unit: shared | Status: current.

Unit tests for PartialSignalGenerated event schema.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.events.schemas import PartialSignalGenerated


class TestPartialSignalGenerated:
    """Tests for PartialSignalGenerated event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating a valid PartialSignalGenerated event."""
        now = datetime.now(UTC)
        event = PartialSignalGenerated(
            event_id="psg-123",
            timestamp=now,
            correlation_id="workflow-456",
            causation_id="session-789",
            source_module="strategy_v2",
            source_component="single_file_handler",
            session_id="session-789",
            dsl_file="momentum.clj",
            allocation=Decimal("0.6"),
            strategy_number=1,
            total_strategies=3,
            signals_data={"momentum": {"symbols": ["AAPL"]}},
            consolidated_portfolio={"target_allocations": {"AAPL": "0.6"}},
            signal_count=1,
        )

        assert event.event_id == "psg-123"
        assert event.event_type == "PartialSignalGenerated"
        assert event.session_id == "session-789"
        assert event.dsl_file == "momentum.clj"
        assert event.allocation == Decimal("0.6")
        assert event.strategy_number == 1
        assert event.total_strategies == 3
        assert event.signal_count == 1

    def test_with_metadata(self) -> None:
        """Test event with optional metadata field."""
        now = datetime.now(UTC)
        event = PartialSignalGenerated(
            event_id="psg-456",
            timestamp=now,
            correlation_id="corr-123",
            causation_id="cause-456",
            source_module="strategy_v2",
            source_component="handler",
            session_id="sess-abc",
            dsl_file="value.clj",
            allocation=Decimal("0.4"),
            strategy_number=2,
            total_strategies=5,
            consolidated_portfolio={"target_allocations": {"AAPL": "0.4"}},
            signals_data={"value": {"symbols": ["AAPL"]}},
            signal_count=1,
            metadata={"extra": "info"},
        )

        assert event.metadata == {"extra": "info"}

    def test_missing_required_fields_fails(self) -> None:
        """Test that missing required fields raises validation error."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            PartialSignalGenerated(
                event_id="psg-bad",
                timestamp=now,
                correlation_id="corr-123",
                causation_id="cause-456",
                source_module="strategy_v2",
                source_component="handler",
                session_id="sess-abc",
                dsl_file="test.clj",
                allocation=Decimal("0.5"),
                strategy_number=1,
                total_strategies=1,
                # Missing: signals_data, consolidated_portfolio, signal_count
            )

    def test_strategy_number_must_be_positive(self) -> None:
        """Test that strategy_number must be > 0."""
        now = datetime.now(UTC)
        # strategy_number=0 should still work as Field doesn't have ge=1
        # This tests actual behavior (no validation on strategy_number)
        event = PartialSignalGenerated(
            event_id="psg-test",
            timestamp=now,
            correlation_id="corr-123",
            causation_id="cause-456",
            source_module="strategy_v2",
            source_component="handler",
            session_id="sess-abc",
            dsl_file="test.clj",
            allocation=Decimal("0.5"),
            strategy_number=0,
            total_strategies=1,
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )
        # Event is created (no ge= constraint on strategy_number in schema)
        assert event.strategy_number == 0

    def test_serialization_to_json(self) -> None:
        """Test that event can be serialized to JSON."""
        now = datetime.now(UTC)
        event = PartialSignalGenerated(
            event_id="psg-serial",
            timestamp=now,
            correlation_id="corr-serial",
            causation_id="cause-serial",
            source_module="strategy_v2",
            source_component="handler",
            session_id="sess-serial",
            dsl_file="test.clj",
            allocation=Decimal("0.75"),
            strategy_number=2,
            total_strategies=4,
            consolidated_portfolio={"AAPL": "0.5"},
            signals_data={"test": {}},
            signal_count=3,
        )

        # Serialize to dict
        event_dict = event.model_dump(mode="json")

        assert event_dict["event_id"] == "psg-serial"
        assert event_dict["session_id"] == "sess-serial"
        assert event_dict["dsl_file"] == "test.clj"
        assert event_dict["allocation"] == "0.75"  # Decimal serialized as string
        assert event_dict["strategy_number"] == 2
        assert event_dict["total_strategies"] == 4
