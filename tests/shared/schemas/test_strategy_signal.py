"""Business Unit: shared | Status: current.

Comprehensive unit tests for StrategySignal DTO.

Tests StrategySignal schema validation, serialization, deserialization,
type safety, immutability, and event-driven field requirements.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.strategy_signal import (
    StrategySignal,
)
from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.value_objects.symbol import Symbol


class TestStrategySignalValidation:
    """Test StrategySignal field validation."""

    def test_minimal_valid_signal(self):
        """Test creating minimal valid signal with required fields only."""
        signal = StrategySignal(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test signal",
        )
        assert signal.symbol.value == "AAPL"
        assert signal.action == "BUY"
        assert signal.reasoning == "Test signal"
        assert signal.schema_version == "1.0"
        assert signal.correlation_id == "test-corr-123"
        assert signal.causation_id == "test-cause-456"

    def test_full_signal_with_all_fields(self):
        """Test creating signal with all optional fields populated."""
        ts = datetime(2025, 1, 7, 12, 0, 0, tzinfo=UTC)
        signal = StrategySignal(
            schema_version="1.0",
            correlation_id="corr-789",
            causation_id="cause-012",
            timestamp=ts,
            symbol=Symbol("SPY"),
            action="SELL",
            reasoning="Market conditions deteriorating",
            strategy_name="dsl_momentum",
            target_allocation=Decimal("0.25"),
            signal_strength=Decimal("0.85"),
            metadata={"confidence": 0.9, "indicators": ["RSI", "MACD"]},
        )
        assert signal.symbol.value == "SPY"
        assert signal.action == "SELL"
        assert signal.target_allocation == Decimal("0.25")
        assert signal.strategy_name == "dsl_momentum"
        assert signal.signal_strength == Decimal("0.85")
        assert signal.metadata is not None
        assert signal.metadata["confidence"] == 0.9

    def test_invalid_action_rejected(self):
        """Test invalid action raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="INVALID",  # type: ignore[arg-type]
                reasoning="Test",
            )
        assert "action" in str(exc_info.value).lower()

    def test_valid_actions_accepted(self):
        """Test all valid actions are accepted."""
        ts = datetime.now(UTC)
        for action in ["BUY", "SELL", "HOLD"]:
            signal = StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=ts,
                symbol="AAPL",
                action=action,  # type: ignore[arg-type]
                reasoning="Test",
            )
            assert signal.action == action

    def test_target_allocation_in_valid_range(self):
        """Test target_allocation within [0, 1]."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5"),
        )
        assert signal.target_allocation == Decimal("0.5")

    def test_target_allocation_zero_accepted(self):
        """Test target_allocation of 0.0 is accepted."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.0"),
        )
        assert signal.target_allocation == Decimal("0.0")

    def test_target_allocation_one_accepted(self):
        """Test target_allocation of 1.0 is accepted."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("1.0"),
        )
        assert signal.target_allocation == Decimal("1.0")

    def test_target_allocation_above_range_rejected(self):
        """Test target_allocation > 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
                target_allocation=Decimal("1.5"),
            )
        assert "target_allocation" in str(exc_info.value).lower()

    def test_target_allocation_below_range_rejected(self):
        """Test target_allocation < 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
                target_allocation=Decimal("-0.1"),
            )
        assert "target_allocation" in str(exc_info.value).lower()

    def test_timezone_aware_datetime_required(self):
        """Test that timezone-aware datetime is required."""
        # This should work with timezone-aware datetime
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
        )
        assert signal.timestamp == ts
        assert signal.timestamp.tzinfo is not None

    def test_reasoning_max_length_enforced(self):
        """Test reasoning field max length validation."""
        long_reasoning = "A" * 1001  # Exceeds 1000 char limit
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning=long_reasoning,
            )
        assert "reasoning" in str(exc_info.value).lower()

    def test_reasoning_at_max_length_accepted(self):
        """Test reasoning at exactly max length is accepted."""
        max_reasoning = "A" * 1000  # Exactly 1000 chars
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning=max_reasoning,
        )
        assert len(signal.reasoning) == 1000

    def test_correlation_id_required(self):
        """Test correlation_id is required."""
        with pytest.raises(ValidationError):
            StrategySignal(
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
            )

    def test_causation_id_required(self):
        """Test causation_id is required."""
        with pytest.raises(ValidationError):
            StrategySignal(
                correlation_id="test-corr",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
            )

    def test_empty_correlation_id_rejected(self):
        """Test empty correlation_id is rejected."""
        with pytest.raises(ValidationError):
            StrategySignal(
                correlation_id="",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
            )

    def test_schema_version_default(self):
        """Test schema_version has correct default."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
        )
        assert signal.schema_version == "1.0"

    def test_schema_version_pattern_validation(self):
        """Test schema_version validates pattern."""
        # Valid versions
        for version in ["1.0", "2.5", "10.99"]:
            signal = StrategySignal(
                schema_version=version,
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
            )
            assert signal.schema_version == version

        # Invalid versions should be rejected
        with pytest.raises(ValidationError):
            StrategySignal(
                schema_version="invalid",
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="BUY",
                reasoning="Test",
            )


class TestStrategySignalInputFlexibility:
    """Test flexible input conversion."""

    def test_string_symbol_converted(self):
        """Test str symbol is converted to Symbol."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="aapl",  # lowercase
            action="BUY",
            reasoning="Test",
        )
        assert isinstance(signal.symbol, Symbol)
        assert signal.symbol.value == "AAPL"  # Should be normalized to uppercase

    def test_symbol_instance_accepted(self):
        """Test Symbol instance is accepted directly."""
        sym = Symbol("SPY")
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol=sym,
            action="BUY",
            reasoning="Test",
        )
        assert signal.symbol.value == "SPY"

    def test_float_allocation_converted(self):
        """Test float allocation is converted to Decimal."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=0.5,  # float
        )
        assert isinstance(signal.target_allocation, Decimal)
        assert signal.target_allocation == Decimal("0.5")

    def test_int_allocation_converted(self):
        """Test int allocation is converted to Decimal."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=1,  # int
        )
        assert isinstance(signal.target_allocation, Decimal)
        assert signal.target_allocation == Decimal("1")

    def test_percentage_allocation_converted(self):
        """Test Percentage allocation is converted to Decimal."""
        pct = Percentage(Decimal("0.3"))
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=pct,
        )
        assert signal.target_allocation == Decimal("0.3")

    def test_decimal_allocation_accepted(self):
        """Test Decimal allocation is accepted directly."""
        alloc = Decimal("0.75")
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=alloc,
        )
        assert signal.target_allocation == alloc


class TestStrategySignalImmutability:
    """Test StrategySignal immutability."""

    def test_immutability(self):
        """Test that StrategySignal is immutable (frozen)."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
        )
        with pytest.raises(ValidationError):
            signal.action = "SELL"  # type: ignore[misc]

    def test_immutability_symbol_field(self):
        """Test that symbol field is immutable."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
        )
        with pytest.raises(ValidationError):
            signal.symbol = Symbol("SPY")  # type: ignore[misc]

    def test_immutability_allocation_field(self):
        """Test that target_allocation field is immutable."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5"),
        )
        with pytest.raises(ValidationError):
            signal.target_allocation = Decimal("0.75")  # type: ignore[misc]


class TestStrategySignalSerialization:
    """Test to_dict and from_dict methods."""

    def test_to_dict_basic(self):
        """Test basic serialization to dictionary."""
        ts = datetime(2025, 1, 7, 12, 0, 0, tzinfo=UTC)
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="AAPL",
            action="BUY",
            reasoning="Test signal",
        )

        data = signal.to_dict()
        assert isinstance(data, dict)
        assert data["correlation_id"] == "test-corr"
        assert data["causation_id"] == "test-cause"
        assert data["symbol"] == "AAPL"
        assert data["action"] == "BUY"
        assert data["reasoning"] == "Test signal"
        assert isinstance(data["timestamp"], str)
        assert data["schema_version"] == "1.0"

    def test_to_dict_with_decimals(self):
        """Test serialization converts Decimal to string."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5"),
            signal_strength=Decimal("0.85"),
        )

        data = signal.to_dict()
        assert isinstance(data["target_allocation"], str)
        assert data["target_allocation"] == "0.5"
        assert isinstance(data["signal_strength"], str)
        assert data["signal_strength"] == "0.85"

    def test_from_dict_basic(self):
        """Test basic deserialization from dictionary."""
        data = {
            "correlation_id": "test-corr",
            "causation_id": "test-cause",
            "timestamp": "2025-01-07T12:00:00+00:00",
            "symbol": "AAPL",
            "action": "BUY",
            "reasoning": "Test signal",
        }

        signal = StrategySignal.from_dict(data)
        assert signal.correlation_id == "test-corr"
        assert signal.causation_id == "test-cause"
        assert signal.symbol.value == "AAPL"
        assert signal.action == "BUY"
        assert signal.reasoning == "Test signal"

    def test_from_dict_with_decimals(self):
        """Test deserialization converts string to Decimal."""
        data = {
            "correlation_id": "test-corr",
            "causation_id": "test-cause",
            "timestamp": "2025-01-07T12:00:00+00:00",
            "symbol": "AAPL",
            "action": "BUY",
            "reasoning": "Test",
            "target_allocation": "0.5",
            "signal_strength": "0.85",
        }

        signal = StrategySignal.from_dict(data)
        assert signal.target_allocation == Decimal("0.5")
        assert signal.signal_strength == Decimal("0.85")

    def test_round_trip_serialization(self):
        """Test serialization round-trip preserves data."""
        original = StrategySignal(
            schema_version="1.0",
            correlation_id="test-corr-789",
            causation_id="test-cause-012",
            timestamp=datetime(2025, 1, 7, 12, 0, 0, tzinfo=UTC),
            symbol="SPY",
            action="SELL",
            reasoning="Market downturn expected",
            strategy_name="dsl_momentum",
            target_allocation=Decimal("0.3"),
            signal_strength=Decimal("0.75"),
            metadata={"confidence": 0.8},
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["target_allocation"], str)
        assert isinstance(data["signal_strength"], str)

        # Deserialize
        restored = StrategySignal.from_dict(data)
        assert restored.correlation_id == original.correlation_id
        assert restored.causation_id == original.causation_id
        assert restored.symbol.value == original.symbol.value
        assert restored.action == original.action
        assert restored.reasoning == original.reasoning
        assert restored.target_allocation == original.target_allocation
        assert restored.signal_strength == original.signal_strength
        assert restored.metadata == original.metadata

    def test_from_dict_with_z_suffix(self):
        """Test deserialization handles Z suffix (Zulu time)."""
        data = {
            "correlation_id": "test-corr",
            "causation_id": "test-cause",
            "timestamp": "2025-01-07T12:00:00Z",  # Z suffix
            "symbol": "AAPL",
            "action": "BUY",
            "reasoning": "Test",
        }

        signal = StrategySignal.from_dict(data)
        assert signal.timestamp.tzinfo is not None

    def test_from_dict_invalid_timestamp_format(self):
        """Test from_dict raises error for invalid timestamp."""
        data = {
            "correlation_id": "test-corr",
            "causation_id": "test-cause",
            "timestamp": "invalid-timestamp",
            "symbol": "AAPL",
            "action": "BUY",
            "reasoning": "Test",
        }

        with pytest.raises(ValueError) as exc_info:
            StrategySignal.from_dict(data)
        assert "timestamp" in str(exc_info.value).lower()

    def test_from_dict_invalid_decimal(self):
        """Test from_dict raises error for invalid Decimal value."""
        data = {
            "correlation_id": "test-corr",
            "causation_id": "test-cause",
            "timestamp": "2025-01-07T12:00:00+00:00",
            "symbol": "AAPL",
            "action": "BUY",
            "reasoning": "Test",
            "target_allocation": "invalid",
        }

        with pytest.raises(ValueError) as exc_info:
            StrategySignal.from_dict(data)
        assert "target_allocation" in str(exc_info.value).lower()


class TestStrategySignalEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_allocation(self):
        """Test very small but valid allocation."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.0001"),
        )
        assert signal.target_allocation == Decimal("0.0001")

    def test_allocation_with_many_decimal_places(self):
        """Test allocation with high precision."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.123456789"),
        )
        assert signal.target_allocation == Decimal("0.123456789")

    def test_symbol_normalization_preserves_validity(self):
        """Test that symbol normalization maintains validity."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="spy",  # lowercase
            action="BUY",
            reasoning="Test",
        )
        assert signal.symbol.value == "SPY"

    def test_whitespace_handling_in_reasoning(self):
        """Test whitespace is stripped from reasoning."""
        signal = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="  Test with spaces  ",
        )
        # Pydantic's str_strip_whitespace should handle this
        assert signal.reasoning.strip() == signal.reasoning


class TestStrategySignalBackwardCompatibility:
    """Test backward compatibility with types version."""

    def test_can_import_from_types_module(self):
        """Test deprecated types module still works."""
        # This should issue a deprecation warning but still work
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from the_alchemiser.shared.types.strategy_value_objects import (
                StrategySignal as TypesSignal,
            )

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

        # Should be the same class
        from the_alchemiser.shared.schemas.strategy_signal import StrategySignal as SchemasSignal

        assert TypesSignal is SchemasSignal


class TestStrategySignalEquality:
    """Test equality and hashing behavior."""

    def test_equal_signals_are_equal(self):
        """Test that signals with same data are equal."""
        ts = datetime(2025, 1, 7, 12, 0, 0, tzinfo=UTC)
        signal1 = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5"),
        )
        signal2 = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5"),
        )
        assert signal1 == signal2

    def test_different_signals_are_not_equal(self):
        """Test that signals with different data are not equal."""
        ts = datetime.now(UTC)
        signal1 = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
        )
        signal2 = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=ts,
            symbol="SPY",  # Different symbol
            action="BUY",
            reasoning="Test",
        )
        assert signal1 != signal2
