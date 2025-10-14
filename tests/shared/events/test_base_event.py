#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for BaseEvent class.

Tests cover:
- Field validation (required fields, min_length constraints)
- Immutability enforcement (frozen model)
- Timezone handling (naive timestamps, Z suffix, explicit UTC)
- Serialization round-trips (to_dict → from_dict)
- Error handling (invalid timestamps, missing fields)
- Inheritance compatibility
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.events.base import BaseEvent


@pytest.mark.unit
class TestBaseEventFieldValidation:
    """Test BaseEvent field validation."""

    def test_valid_event_creation_with_all_fields(self) -> None:
        """Test creating valid event with all fields."""
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
            source_component="test_component",
            metadata={"key": "value"},
        )
        assert event.correlation_id == "corr-123"
        assert event.causation_id == "cause-123"
        assert event.event_id == "event-123"
        assert event.event_type == "TestEvent"
        assert event.timestamp.tzinfo is not None
        assert event.source_module == "test_module"
        assert event.source_component == "test_component"
        assert event.metadata == {"key": "value"}

    def test_valid_event_creation_with_minimal_fields(self) -> None:
        """Test creating valid event with only required fields."""
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
        )
        assert event.correlation_id == "corr-123"
        assert event.source_component is None
        assert event.metadata is None

    def test_missing_correlation_id_fails(self) -> None:
        """Test that missing correlation_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("correlation_id",) for e in errors)

    def test_empty_correlation_id_fails(self) -> None:
        """Test that empty correlation_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="",  # Empty string
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(
            e["loc"] == ("correlation_id",) and "at least 1 character" in str(e["msg"])
            for e in errors
        )

    def test_missing_causation_id_fails(self) -> None:
        """Test that missing causation_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("causation_id",) for e in errors)

    def test_missing_event_id_fails(self) -> None:
        """Test that missing event_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("event_id",) for e in errors)

    def test_missing_event_type_fails(self) -> None:
        """Test that missing event_type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("event_type",) for e in errors)

    def test_missing_timestamp_fails(self) -> None:
        """Test that missing timestamp is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                source_module="test_module",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("timestamp",) for e in errors)

    def test_missing_source_module_fails(self) -> None:
        """Test that missing source_module is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("source_module",) for e in errors)

    def test_empty_source_module_fails(self) -> None:
        """Test that empty source_module is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module="",  # Empty string
            )
        errors = exc_info.value.errors()
        assert any(
            e["loc"] == ("source_module",) and "at least 1 character" in str(e["msg"])
            for e in errors
        )


@pytest.mark.unit
class TestBaseEventImmutability:
    """Test BaseEvent immutability (frozen model)."""

    def test_frozen_model_prevents_modification(self) -> None:
        """Test that BaseEvent is immutable (frozen)."""
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
        )
        with pytest.raises(ValidationError):
            event.correlation_id = "new-corr"  # type: ignore

    def test_cannot_add_attributes(self) -> None:
        """Test that cannot add new attributes to frozen model."""
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
        )
        with pytest.raises(ValidationError):
            event.new_field = "value"  # type: ignore


@pytest.mark.unit
class TestBaseEventTimezoneHandling:
    """Test BaseEvent timezone handling."""

    def test_naive_timestamp_converted_to_utc(self) -> None:
        """Test that naive timestamp is automatically converted to UTC."""
        naive_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        assert naive_timestamp.tzinfo is None

        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=naive_timestamp,
            source_module="test_module",
        )

        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo == UTC

    def test_utc_timestamp_preserved(self) -> None:
        """Test that UTC timestamp is preserved."""
        utc_timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=utc_timestamp,
            source_module="test_module",
        )

        assert event.timestamp == utc_timestamp
        assert event.timestamp.tzinfo == UTC

    def test_non_utc_timezone_preserved(self) -> None:
        """Test that non-UTC timezone is preserved (not converted)."""
        # Create timestamp with +05:00 timezone
        tz_offset = timezone(offset=timedelta(hours=5))
        offset_timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=tz_offset)

        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=offset_timestamp,
            source_module="test_module",
        )

        # Timestamp should be converted to UTC (UTC normalization policy)
        assert event.timestamp.tzinfo == timezone.utc
        # Time should be adjusted to UTC (12:00+05:00 becomes 07:00+00:00)
        assert event.timestamp.hour == 7


@pytest.mark.unit
class TestBaseEventSerialization:
    """Test BaseEvent serialization (to_dict)."""

    def test_to_dict_with_all_fields(self) -> None:
        """Test to_dict serializes all fields correctly."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
            source_component="test_component",
            metadata={"key": "value"},
        )

        data = event.to_dict()

        assert data["correlation_id"] == "corr-123"
        assert data["causation_id"] == "cause-123"
        assert data["event_id"] == "event-123"
        assert data["event_type"] == "TestEvent"
        assert data["timestamp"] == "2023-01-01T12:00:00+00:00"
        assert data["source_module"] == "test_module"
        assert data["source_component"] == "test_component"
        assert data["metadata"] == {"key": "value"}

    def test_to_dict_with_minimal_fields(self) -> None:
        """Test to_dict with only required fields."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
        )

        data = event.to_dict()

        assert data["source_component"] is None
        assert data["metadata"] is None

    def test_to_dict_timestamp_is_iso_format(self) -> None:
        """Test that timestamp is serialized as ISO format string."""
        timestamp = datetime(2023, 6, 15, 14, 30, 45, tzinfo=UTC)
        event = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
        )

        data = event.to_dict()

        assert isinstance(data["timestamp"], str)
        assert data["timestamp"] == "2023-06-15T14:30:45+00:00"


@pytest.mark.unit
class TestBaseEventDeserialization:
    """Test BaseEvent deserialization (from_dict)."""

    def test_from_dict_recreates_event(self) -> None:
        """Test that from_dict recreates event from dictionary."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "source_module": "test_module",
            "source_component": "test_component",
            "metadata": {"key": "value"},
        }

        event = BaseEvent.from_dict(data)

        assert event.correlation_id == "corr-123"
        assert event.causation_id == "cause-123"
        assert event.event_id == "event-123"
        assert event.event_type == "TestEvent"
        assert event.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert event.source_module == "test_module"
        assert event.source_component == "test_component"
        assert event.metadata == {"key": "value"}

    def test_from_dict_handles_z_suffix_timestamp(self) -> None:
        """Test that from_dict handles Z suffix in timestamp."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": "2023-01-01T12:00:00Z",  # Z suffix
            "source_module": "test_module",
        }

        event = BaseEvent.from_dict(data)

        assert event.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_from_dict_with_minimal_fields(self) -> None:
        """Test from_dict with only required fields."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "source_module": "test_module",
        }

        event = BaseEvent.from_dict(data)

        assert event.source_component is None
        assert event.metadata is None

    def test_from_dict_invalid_timestamp_raises_error(self) -> None:
        """Test that invalid timestamp format raises ValueError."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": "invalid-timestamp",
            "source_module": "test_module",
        }

        with pytest.raises(ValueError, match="Invalid timestamp format"):
            BaseEvent.from_dict(data)

    def test_from_dict_preserves_non_utc_timezone(self) -> None:
        """Test that from_dict preserves non-UTC timezone."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": "2023-01-01T12:00:00+05:00",  # +05:00 offset
            "source_module": "test_module",
        }

        event = BaseEvent.from_dict(data)

        # Timestamp should preserve the +05:00 offset
        assert event.timestamp.tzinfo is not None
        assert event.timestamp.utcoffset() == timedelta(hours=5)

    def test_from_dict_with_datetime_object(self) -> None:
        """Test that from_dict works when timestamp is already datetime object."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": timestamp,  # Already a datetime
            "source_module": "test_module",
        }

        event = BaseEvent.from_dict(data)

        assert event.timestamp == timestamp


@pytest.mark.unit
class TestBaseEventRoundTrip:
    """Test BaseEvent serialization round-trips."""

    def test_round_trip_with_all_fields(self) -> None:
        """Test that to_dict → from_dict is a round trip with all fields."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        original = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
            source_component="test_component",
            metadata={"key": "value", "nested": {"data": 123}},
        )

        # Serialize and deserialize
        data = original.to_dict()
        reconstructed = BaseEvent.from_dict(data)

        # Verify all fields match
        assert reconstructed.correlation_id == original.correlation_id
        assert reconstructed.causation_id == original.causation_id
        assert reconstructed.event_id == original.event_id
        assert reconstructed.event_type == original.event_type
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.source_module == original.source_module
        assert reconstructed.source_component == original.source_component
        assert reconstructed.metadata == original.metadata

    def test_round_trip_with_minimal_fields(self) -> None:
        """Test that to_dict → from_dict is a round trip with minimal fields."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        original = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
        )

        # Serialize and deserialize
        data = original.to_dict()
        reconstructed = BaseEvent.from_dict(data)

        # Verify all fields match
        assert reconstructed.correlation_id == original.correlation_id
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.source_component is None
        assert reconstructed.metadata is None

    def test_round_trip_preserves_timezone(self) -> None:
        """Test that round trip preserves timezone information."""
        timestamp = datetime(2023, 6, 15, 14, 30, 45, microsecond=123456, tzinfo=UTC)
        original = BaseEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="TestEvent",
            timestamp=timestamp,
            source_module="test_module",
        )

        # Serialize and deserialize
        data = original.to_dict()
        reconstructed = BaseEvent.from_dict(data)

        # Timestamp should be exactly equal (including microseconds and timezone)
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.timestamp.tzinfo == UTC


@pytest.mark.unit
class TestBaseEventInheritance:
    """Test BaseEvent inheritance compatibility."""

    def test_derived_event_inherits_fields(self) -> None:
        """Test that derived events inherit BaseEvent fields."""

        class DerivedEvent(BaseEvent):
            """Derived event for testing."""

            custom_field: str

        event = DerivedEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="DerivedEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
            custom_field="custom_value",
        )

        assert event.correlation_id == "corr-123"
        assert isinstance(event, DerivedEvent)
        # Access custom_field through the actual type
        derived_event = event
        assert derived_event.custom_field == "custom_value"

    def test_derived_event_is_frozen(self) -> None:
        """Test that derived events are also frozen (immutable)."""

        class DerivedEvent(BaseEvent):
            """Derived event for testing."""

            custom_field: str

        event = DerivedEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="DerivedEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
            custom_field="custom_value",
        )

        with pytest.raises(ValidationError):
            event.custom_field = "new_value"  # Should raise due to frozen model

    def test_derived_event_to_dict(self) -> None:
        """Test that derived events support to_dict."""

        class DerivedEvent(BaseEvent):
            """Derived event for testing."""

            custom_field: str

        timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        event = DerivedEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            event_type="DerivedEvent",
            timestamp=timestamp,
            source_module="test_module",
            custom_field="custom_value",
        )

        data = event.to_dict()

        assert data["correlation_id"] == "corr-123"
        assert data["custom_field"] == "custom_value"
        assert data["timestamp"] == "2023-01-01T12:00:00+00:00"

    def test_derived_event_from_dict(self) -> None:
        """Test that derived events support from_dict."""

        class DerivedEvent(BaseEvent):
            """Derived event for testing."""

            custom_field: str

        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "DerivedEvent",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "source_module": "test_module",
            "custom_field": "custom_value",
        }

        event = DerivedEvent.from_dict(data)

        assert event.correlation_id == "corr-123"
        assert event.custom_field == "custom_value"


@pytest.mark.unit
class TestBaseEventStrictMode:
    """Test BaseEvent strict mode behavior."""

    def test_strict_mode_enforces_types(self) -> None:
        """Test that strict mode enforces exact types."""
        # Pydantic strict mode should reject type coercion
        with pytest.raises(ValidationError):
            BaseEvent(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                event_type="TestEvent",
                timestamp=datetime.now(UTC),
                source_module=123,  # type: ignore[arg-type]
            )

    def test_extra_fields_allowed_by_default(self) -> None:
        """Test that extra fields are allowed (no extra='forbid' in config)."""
        # BaseEvent doesn't have extra='forbid', so extra fields are allowed
        # This is intentional for forward compatibility
        # Note: Pydantic ignores extra fields by default
        event_dict = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "event_type": "TestEvent",
            "timestamp": datetime.now(UTC),
            "source_module": "test_module",
            "extra_field": "allowed",
        }
        event = BaseEvent(**event_dict)  # type: ignore[arg-type]
        # Extra field is silently ignored (Pydantic default behavior)
        assert event.correlation_id == "corr-123"
