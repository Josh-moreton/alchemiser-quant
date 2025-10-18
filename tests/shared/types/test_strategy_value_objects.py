"""Business Unit: shared | Status: current.

Tests for StrategySignal value object.

Comprehensive test coverage for the StrategySignal class including:
- Field validation
- Input normalization
- Immutability
- Type safety
- Property-based testing
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from the_alchemiser.shared.schemas.strategy_signal import (
    ActionLiteral,
    StrategySignal,
)
from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.value_objects.symbol import Symbol


def _default_signal_fields(**overrides: Any) -> dict[str, Any]:
    """Helper to create StrategySignal fields with required correlation/causation IDs.

    Provides default values for:
    - correlation_id: "test-correlation-id"
    - causation_id: "test-causation-id"
    - reasoning: "Test signal reasoning"

    All defaults can be overridden via kwargs.
    """
    defaults = {
        "correlation_id": "test-correlation-id",
        "causation_id": "test-causation-id",
        "reasoning": "Test signal reasoning",
    }
    defaults.update(overrides)
    return defaults


class TestStrategySignalValidation:
    """Test StrategySignal field validation."""

    def test_valid_buy_signal(self) -> None:
        """Test creating valid BUY signal."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                reasoning="Test buy signal",
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.action == "BUY"
        assert signal.symbol.value == "AAPL"
        assert signal.reasoning == "Test buy signal"

    def test_valid_sell_signal(self) -> None:
        """Test creating valid SELL signal."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol=Symbol("SPY"),
                action="SELL",
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.action == "SELL"
        assert signal.symbol.value == "SPY"

    def test_valid_hold_signal(self) -> None:
        """Test creating valid HOLD signal."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="QQQ",
                action="HOLD",
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.action == "HOLD"
        assert signal.symbol.value == "QQQ"

    def test_invalid_action_rejected(self) -> None:
        """Test that invalid actions are rejected at type level."""
        # This should fail type checking, but test runtime behavior
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="INVALID",  # type: ignore[arg-type]
                    timestamp=datetime.now(UTC),
                )
            )
        assert "action" in str(exc_info.value).lower()

    def test_target_allocation_in_valid_range(self) -> None:
        """Test target_allocation within [0, 1]."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.5"),
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.5")

    def test_target_allocation_zero_accepted(self) -> None:
        """Test target_allocation of 0.0 is accepted."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.0"),
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.0")

    def test_target_allocation_one_accepted(self) -> None:
        """Test target_allocation of 1.0 is accepted."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("1.0"),
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("1.0")

    def test_target_allocation_above_range_rejected(self) -> None:
        """Test target_allocation > 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    target_allocation=Decimal("1.5"),
                    timestamp=datetime.now(UTC),
                )
            )
        assert "target_allocation" in str(exc_info.value).lower()

    def test_target_allocation_below_range_rejected(self) -> None:
        """Test target_allocation < 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    target_allocation=Decimal("-0.1"),
                    timestamp=datetime.now(UTC),
                )
            )
        assert "target_allocation" in str(exc_info.value).lower()

    def test_target_allocation_none_accepted(self) -> None:
        """Test None target_allocation is accepted."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=None,
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation is None

    def test_timezone_naive_datetime_converted(self) -> None:
        """Test that timezone-naive datetime is coerced to UTC."""
        naive_timestamp = datetime(2025, 1, 1, 12, 0, 0)
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=naive_timestamp,
            )
        )
        assert signal.timestamp.tzinfo == UTC

    def test_timezone_aware_datetime_accepted(self) -> None:
        """Test that timezone-aware datetime is accepted."""
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=ts,
            )
        )
        assert signal.timestamp == ts
        assert signal.timestamp.tzinfo == UTC

    def test_non_utc_timezone_accepted(self) -> None:
        """Test that non-UTC timezones are accepted (but not recommended)."""
        eastern = timezone(timedelta(hours=-5))
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=eastern)
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=ts,
            )
        )
        assert signal.timestamp.tzinfo == eastern

    def test_reasoning_max_length_enforced(self) -> None:
        """Test reasoning field max length validation."""
        long_reasoning = "A" * 1001  # Exceeds 1000 char limit
        with pytest.raises(ValidationError) as exc_info:
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    reasoning=long_reasoning,
                    timestamp=datetime.now(UTC),
                )
            )
        assert "reasoning" in str(exc_info.value).lower()

    def test_reasoning_empty_string_rejected(self) -> None:
        """Test empty reasoning raises validation error."""
        with pytest.raises(ValidationError):
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    reasoning="",
                    timestamp=datetime.now(UTC),
                )
            )

    def test_immutability(self) -> None:
        """Test that StrategySignal is immutable (frozen)."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        with pytest.raises(ValidationError):
            signal.action = "SELL"  # type: ignore[misc]

    def test_immutability_symbol_field(self) -> None:
        """Test that symbol field is immutable."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        with pytest.raises(ValidationError):
            signal.symbol = Symbol("SPY")  # type: ignore[misc]


class TestStrategySignalInputFlexibility:
    """Test flexible input conversion."""

    def test_string_symbol_converted(self) -> None:
        """Test str symbol is converted to Symbol."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="aapl",  # lowercase
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        assert isinstance(signal.symbol, Symbol)
        assert signal.symbol.value == "AAPL"  # Should be normalized to uppercase

    def test_symbol_instance_accepted(self) -> None:
        """Test Symbol instance is accepted directly."""
        sym = Symbol("SPY")
        signal = StrategySignal(
            **_default_signal_fields(
                symbol=sym,
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.symbol is sym

    def test_float_allocation_converted(self) -> None:
        """Test float allocation is converted to Decimal."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=0.5,  # float
                timestamp=datetime.now(UTC),
            )
        )
        assert isinstance(signal.target_allocation, Decimal)
        assert signal.target_allocation == Decimal("0.5")

    def test_int_allocation_converted(self) -> None:
        """Test int allocation is converted to Decimal."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=1,  # int
                timestamp=datetime.now(UTC),
            )
        )
        assert isinstance(signal.target_allocation, Decimal)
        assert signal.target_allocation == Decimal("1")

    def test_percentage_allocation_converted(self) -> None:
        """Test Percentage allocation is converted to Decimal."""
        pct = Percentage(Decimal("0.3"))
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=pct,
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.3")

    def test_percentage_from_percent_converted(self) -> None:
        """Test Percentage created from percent value."""
        pct = Percentage.from_percent(25.0)  # 25% = 0.25
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=pct,
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.25")

    def test_decimal_allocation_accepted(self) -> None:
        """Test Decimal allocation is accepted directly."""
        alloc = Decimal("0.75")
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=alloc,
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == alloc

    def test_none_timestamp_rejected(self) -> None:
        """Test None timestamp raises validation error."""
        with pytest.raises(ValidationError):
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    timestamp=None,
                )
            )

    def test_explicit_timestamp_used(self) -> None:
        """Test explicit timestamp is used when provided."""
        explicit_ts = datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC)
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=explicit_ts,
            )
        )
        assert signal.timestamp == explicit_ts


class TestStrategySignalExtraFields:
    """Test handling of extra fields (correlation_id, causation_id, etc.)."""

    def test_extra_fields_accepted(self) -> None:
        """Test that extra fields are accepted for event-driven architecture."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=datetime.now(UTC),
                correlation_id="test-correlation-123",
                causation_id="test-causation-456",
                strategy="dsl_momentum",  # type: ignore[call-arg]
            )
        )
        # Correlation and causation IDs are now standard fields, strategy is extra
        assert signal.correlation_id == "test-correlation-123"
        assert signal.causation_id == "test-causation-456"
        # Extra fields are stored in __pydantic_extra__
        if hasattr(signal, "__pydantic_extra__") and signal.__pydantic_extra__:
            assert signal.__pydantic_extra__["strategy"] == "dsl_momentum"  # type: ignore[index]


class TestStrategySignalEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_allocation(self) -> None:
        """Test very small but valid allocation."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.0001"),
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.0001")

    def test_allocation_with_many_decimal_places(self) -> None:
        """Test allocation with high precision."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.123456789"),
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.target_allocation == Decimal("0.123456789")

    def test_symbol_normalization_preserves_validity(self) -> None:
        """Test that symbol normalization maintains validity."""
        # Symbol class normalizes to uppercase and validates
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="spy",
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        assert signal.symbol.value == "SPY"

    def test_invalid_symbol_rejected(self) -> None:
        """Test that invalid symbols are rejected by Symbol validation."""
        with pytest.raises(ValueError):
            StrategySignal(
                **_default_signal_fields(
                    symbol="INVALID SYMBOL WITH SPACES",
                    action="BUY",
                    timestamp=datetime.now(UTC),
                )
            )


class TestStrategySignalPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(
        symbol=st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=1,
            max_size=10,
        ),
        action=st.sampled_from(["BUY", "SELL", "HOLD"]),
        allocation=st.one_of(
            st.none(),
            st.decimals(
                min_value=Decimal("0"),
                max_value=Decimal("1"),
                places=6,
                allow_nan=False,
                allow_infinity=False,
            ),
        ),
        reasoning=st.builds(
            lambda left, core, right: left + core + right,
            st.text(
                alphabet=st.characters(whitelist_categories=("Zs",)),
                max_size=10,
            ),
            st.text(
                alphabet=st.characters(
                    blacklist_categories=("Cc", "Cs", "Zs"),
                ),
                min_size=1,
                max_size=980,
            ),
            st.text(
                alphabet=st.characters(whitelist_categories=("Zs",)),
                max_size=10,
            ),
        ),
    )
    def test_valid_inputs_always_succeed(
        self,
        symbol: str,
        action: ActionLiteral,
        allocation: Decimal | None,
        reasoning: str,
    ) -> None:
        """Test that valid inputs always create valid signals (ASCII alphanumeric symbols only)."""
        ts = datetime.now(UTC)
        signal = StrategySignal(
            **_default_signal_fields(
                symbol=symbol,
                action=action,
                target_allocation=allocation,
                reasoning=reasoning,
                timestamp=ts,
            )
        )
        assert signal.symbol.value == symbol.upper()
        assert signal.action == action
        assert signal.target_allocation == allocation
        # StrategySignal has str_strip_whitespace=True, so compare against stripped version
        assert signal.reasoning == reasoning.strip()
        assert signal.timestamp == ts

    @given(
        allocation=st.one_of(
            st.decimals(
                min_value=Decimal("1.001"),
                max_value=Decimal("10"),
                places=3,
                allow_nan=False,
                allow_infinity=False,
            ),
            st.decimals(
                min_value=Decimal("-10"),
                max_value=Decimal("-0.001"),
                places=3,
                allow_nan=False,
                allow_infinity=False,
            ),
        )
    )
    def test_invalid_allocations_always_rejected(self, allocation: Decimal) -> None:
        """Test that allocations outside [0, 1] are always rejected."""
        with pytest.raises(ValidationError):
            StrategySignal(
                **_default_signal_fields(
                    symbol="AAPL",
                    action="BUY",
                    target_allocation=allocation,
                    timestamp=datetime.now(UTC),
                )
            )


class TestStrategySignalEquality:
    """Test equality and hashing behavior."""

    def test_equal_signals_are_equal(self) -> None:
        """Test that signals with same data are equal."""
        ts = datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC)
        signal1 = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.5"),
                reasoning="Test",
                timestamp=ts,
            )
        )
        signal2 = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.5"),
                reasoning="Test",
                timestamp=ts,
            )
        )
        assert signal1 == signal2

    def test_different_signals_are_not_equal(self) -> None:
        """Test that signals with different data are not equal."""
        ts = datetime.now(UTC)
        signal1 = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=ts,
            )
        )
        signal2 = StrategySignal(
            **_default_signal_fields(
                symbol="SPY",
                action="BUY",
                timestamp=ts,
            )
        )
        assert signal1 != signal2


class TestStrategySignalRepresentation:
    """Test string representation."""

    def test_repr_contains_key_fields(self) -> None:
        """Test that repr contains key fields."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                target_allocation=Decimal("0.5"),
                reasoning="Test signal",
                timestamp=datetime.now(UTC),
            )
        )
        repr_str = repr(signal)
        assert "AAPL" in repr_str
        assert "BUY" in repr_str
        assert "0.5" in repr_str

    def test_str_is_readable(self) -> None:
        """Test that str() produces readable output."""
        signal = StrategySignal(
            **_default_signal_fields(
                symbol="AAPL",
                action="BUY",
                timestamp=datetime.now(UTC),
            )
        )
        str_repr = str(signal)
        assert len(str_repr) > 0
        assert "AAPL" in str_repr
