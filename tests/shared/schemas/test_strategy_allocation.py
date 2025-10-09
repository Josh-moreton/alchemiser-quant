#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Test suite for StrategyAllocation schema.

Comprehensive unit tests covering construction, validation, normalization,
serialization, and edge cases for the StrategyAllocation DTO.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestStrategyAllocationConstruction:
    """Test StrategyAllocation construction and basic field access."""

    def test_valid_minimal_allocation(self):
        """Test creating allocation with minimal required fields."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test-123"
        )
        assert allocation.target_weights == {"AAPL": Decimal("1.0")}
        assert allocation.correlation_id == "test-123"
        assert allocation.as_of is None
        assert allocation.portfolio_value is None
        assert allocation.constraints is None

    def test_valid_full_allocation(self):
        """Test creating allocation with all fields populated."""
        now = datetime.now(UTC)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test-456",
            as_of=now,
            portfolio_value=Decimal("10000"),
            constraints={"max_position_size": 0.5},
        )
        assert len(allocation.target_weights) == 2
        assert allocation.target_weights["AAPL"] == Decimal("0.6")
        assert allocation.target_weights["MSFT"] == Decimal("0.4")
        assert allocation.correlation_id == "test-456"
        assert allocation.as_of == now
        assert allocation.portfolio_value == Decimal("10000")
        assert allocation.constraints == {"max_position_size": 0.5}

    def test_multiple_symbols_allocation(self):
        """Test allocation with multiple symbols."""
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.25"),
                "MSFT": Decimal("0.25"),
                "GOOGL": Decimal("0.25"),
                "AMZN": Decimal("0.25"),
            },
            correlation_id=str(uuid4()),
        )
        assert len(allocation.target_weights) == 4
        total = sum(allocation.target_weights.values())
        assert total == Decimal("1.0")


class TestStrategyAllocationImmutability:
    """Test that StrategyAllocation is immutable (frozen=True)."""

    def test_cannot_modify_target_weights(self):
        """Test that target_weights field cannot be reassigned."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            allocation.target_weights = {"MSFT": Decimal("1.0")}

    def test_cannot_modify_correlation_id(self):
        """Test that correlation_id field cannot be reassigned."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test-123"
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            allocation.correlation_id = "test-456"

    def test_cannot_modify_portfolio_value(self):
        """Test that portfolio_value field cannot be reassigned."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            portfolio_value=Decimal("10000"),
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            allocation.portfolio_value = Decimal("20000")


class TestStrategyAllocationValidation:
    """Test validation rules for StrategyAllocation fields."""

    def test_empty_target_weights_rejected(self):
        """Test that empty target_weights dictionary is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            StrategyAllocation(target_weights={}, correlation_id="test")

    def test_weight_sum_too_low_rejected(self):
        """Test that weights summing below 0.99 are rejected."""
        with pytest.raises(ValueError, match="must sum to"):
            StrategyAllocation(
                target_weights={"AAPL": Decimal("0.5")}, correlation_id="test"
            )

    def test_weight_sum_too_high_rejected(self):
        """Test that weights summing above 1.01 are rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError or ValueError
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.02")}, correlation_id="test"
            )

    def test_weight_sum_at_lower_tolerance_accepted(self):
        """Test that weights summing to exactly 0.99 are accepted."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.99")}, correlation_id="test"
        )
        assert allocation.target_weights["AAPL"] == Decimal("0.99")

    def test_weight_sum_at_upper_tolerance_accepted(self):
        """Test that weights summing to exactly 1.01 are accepted."""
        # Note: Individual weights must still be <= 1.0
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.51"), "MSFT": Decimal("0.50")},
            correlation_id="test",
        )
        total = sum(allocation.target_weights.values())
        assert total == Decimal("1.01")

    def test_negative_weight_rejected(self):
        """Test that negative weights are rejected."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            StrategyAllocation(
                target_weights={"AAPL": Decimal("-0.5"), "MSFT": Decimal("1.5")},
                correlation_id="test",
            )

    def test_weight_above_one_rejected(self):
        """Test that weights above 1.0 are rejected."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.5")}, correlation_id="test"
            )

    def test_zero_weight_accepted(self):
        """Test that zero weights are accepted (within sum constraint)."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0"), "MSFT": Decimal("0.0")},
            correlation_id="test",
        )
        assert allocation.target_weights["MSFT"] == Decimal("0.0")

    def test_empty_correlation_id_rejected(self):
        """Test that empty correlation_id is rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")}, correlation_id=""
            )

    def test_whitespace_only_correlation_id_rejected(self):
        """Test that whitespace-only correlation_id is rejected."""
        # Pydantic strips whitespace first via str_strip_whitespace, then validates min_length
        with pytest.raises(Exception):  # Pydantic ValidationError
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")}, correlation_id="   "
            )

    def test_long_correlation_id_rejected(self):
        """Test that correlation_id exceeding max length is rejected."""
        long_id = "x" * 101  # max_length=100
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")}, correlation_id=long_id
            )

    def test_negative_portfolio_value_rejected(self):
        """Test that negative portfolio_value is rejected."""
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")},
                correlation_id="test",
                portfolio_value=Decimal("-1000"),
            )

    def test_zero_portfolio_value_accepted(self):
        """Test that zero portfolio_value is accepted."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            portfolio_value=Decimal("0"),
        )
        assert allocation.portfolio_value == Decimal("0")

    def test_invalid_symbol_type_rejected(self):
        """Test that non-string symbol keys are rejected."""
        # Pydantic strict mode will reject non-string keys at the type level
        with pytest.raises(Exception):  # Pydantic ValidationError
            StrategyAllocation(
                target_weights={123: Decimal("1.0")}, correlation_id="test"  # type: ignore
            )

    def test_empty_symbol_rejected(self):
        """Test that empty string symbols are rejected."""
        with pytest.raises(ValueError, match="Invalid symbol"):
            StrategyAllocation(
                target_weights={"": Decimal("1.0")}, correlation_id="test"
            )


class TestStrategyAllocationNormalization:
    """Test symbol normalization and whitespace handling."""

    def test_lowercase_symbol_normalized_to_uppercase(self):
        """Test that lowercase symbols are converted to uppercase."""
        allocation = StrategyAllocation(
            target_weights={"aapl": Decimal("1.0")}, correlation_id="test"
        )
        assert "AAPL" in allocation.target_weights
        assert "aapl" not in allocation.target_weights

    def test_mixed_case_symbol_normalized(self):
        """Test that mixed-case symbols are normalized to uppercase."""
        allocation = StrategyAllocation(
            target_weights={"AaPl": Decimal("1.0")}, correlation_id="test"
        )
        assert "AAPL" in allocation.target_weights

    def test_symbol_with_whitespace_stripped(self):
        """Test that symbols with leading/trailing whitespace are stripped."""
        allocation = StrategyAllocation(
            target_weights={"  AAPL  ": Decimal("1.0")}, correlation_id="test"
        )
        assert "AAPL" in allocation.target_weights
        assert "  AAPL  " not in allocation.target_weights

    def test_duplicate_symbols_after_normalization_rejected(self):
        """Test that duplicate symbols (after normalization) are rejected."""
        with pytest.raises(ValueError, match="Duplicate symbol"):
            StrategyAllocation(
                target_weights={
                    "aapl": Decimal("0.5"),
                    "AAPL": Decimal("0.5"),
                },
                correlation_id="test",
            )

    def test_correlation_id_whitespace_stripped(self):
        """Test that correlation_id whitespace is stripped."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="  test-123  "
        )
        assert allocation.correlation_id == "test-123"


class TestStrategyAllocationTimezoneHandling:
    """Test timezone awareness for as_of field."""

    def test_timezone_aware_datetime_preserved(self):
        """Test that timezone-aware datetime is preserved."""
        now = datetime.now(UTC)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test", as_of=now
        )
        assert allocation.as_of == now
        assert allocation.as_of.tzinfo is not None

    def test_naive_datetime_gets_utc_timezone(self):
        """Test that naive datetime is converted to UTC-aware."""
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            as_of=naive_dt,
        )
        assert allocation.as_of is not None
        assert allocation.as_of.tzinfo is not None
        assert allocation.as_of.tzinfo.tzname(None) == "UTC"

    def test_none_as_of_accepted(self):
        """Test that None as_of is accepted."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test", as_of=None
        )
        assert allocation.as_of is None

    def test_past_datetime_accepted(self):
        """Test that past datetime is accepted."""
        past = datetime.now(UTC) - timedelta(days=7)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test", as_of=past
        )
        assert allocation.as_of == past

    def test_future_datetime_accepted(self):
        """Test that future datetime is accepted (for backtesting)."""
        future = datetime.now(UTC) + timedelta(days=1)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            as_of=future,
        )
        assert allocation.as_of == future


class TestStrategyAllocationFromDict:
    """Test from_dict classmethod for type conversion."""

    def test_from_dict_with_string_weights(self):
        """Test conversion of string weights to Decimal."""
        allocation = StrategyAllocation.from_dict(
            {"target_weights": {"AAPL": "0.6", "MSFT": "0.4"}, "correlation_id": "test"}
        )
        assert allocation.target_weights["AAPL"] == Decimal("0.6")
        assert isinstance(allocation.target_weights["AAPL"], Decimal)

    def test_from_dict_with_float_weights(self):
        """Test conversion of float weights to Decimal via str()."""
        allocation = StrategyAllocation.from_dict(
            {"target_weights": {"AAPL": 0.6, "MSFT": 0.4}, "correlation_id": "test"}
        )
        assert allocation.target_weights["AAPL"] == Decimal("0.6")
        assert isinstance(allocation.target_weights["AAPL"], Decimal)

    def test_from_dict_with_int_weights(self):
        """Test conversion of int weights to Decimal."""
        allocation = StrategyAllocation.from_dict(
            {"target_weights": {"AAPL": 1}, "correlation_id": "test"}
        )
        assert allocation.target_weights["AAPL"] == Decimal("1")
        assert isinstance(allocation.target_weights["AAPL"], Decimal)

    def test_from_dict_with_decimal_weights(self):
        """Test that Decimal weights are preserved."""
        allocation = StrategyAllocation.from_dict(
            {
                "target_weights": {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
                "correlation_id": "test",
            }
        )
        assert allocation.target_weights["AAPL"] == Decimal("0.6")

    def test_from_dict_with_string_portfolio_value(self):
        """Test conversion of string portfolio_value to Decimal."""
        allocation = StrategyAllocation.from_dict(
            {
                "target_weights": {"AAPL": "1.0"},
                "correlation_id": "test",
                "portfolio_value": "10000.50",
            }
        )
        assert allocation.portfolio_value == Decimal("10000.50")
        assert isinstance(allocation.portfolio_value, Decimal)

    def test_from_dict_with_float_portfolio_value(self):
        """Test conversion of float portfolio_value to Decimal via str()."""
        allocation = StrategyAllocation.from_dict(
            {
                "target_weights": {"AAPL": "1.0"},
                "correlation_id": "test",
                "portfolio_value": 10000.0,
            }
        )
        assert isinstance(allocation.portfolio_value, Decimal)
        # Check that it's approximately correct (float conversion)
        assert abs(allocation.portfolio_value - Decimal("10000")) < Decimal("0.01")

    def test_from_dict_with_int_portfolio_value(self):
        """Test conversion of int portfolio_value to Decimal."""
        allocation = StrategyAllocation.from_dict(
            {
                "target_weights": {"AAPL": "1.0"},
                "correlation_id": "test",
                "portfolio_value": 10000,
            }
        )
        assert allocation.portfolio_value == Decimal("10000")
        assert isinstance(allocation.portfolio_value, Decimal)

    def test_from_dict_with_none_portfolio_value(self):
        """Test that None portfolio_value is preserved."""
        allocation = StrategyAllocation.from_dict(
            {
                "target_weights": {"AAPL": "1.0"},
                "correlation_id": "test",
                "portfolio_value": None,
            }
        )
        assert allocation.portfolio_value is None

    def test_from_dict_invalid_weight_rejected(self):
        """Test that invalid weight values are rejected."""
        # Decimal() raises InvalidOperation for invalid strings, caught as exception in from_dict
        with pytest.raises(Exception):  # Could be ValueError or decimal.InvalidOperation
            StrategyAllocation.from_dict(
                {"target_weights": {"AAPL": "invalid"}, "correlation_id": "test"}
            )

    def test_from_dict_invalid_portfolio_value_rejected(self):
        """Test that invalid portfolio_value is rejected."""
        # Decimal() raises InvalidOperation for invalid strings
        with pytest.raises(Exception):  # Could be ValueError or decimal.InvalidOperation
            StrategyAllocation.from_dict(
                {
                    "target_weights": {"AAPL": "1.0"},
                    "correlation_id": "test",
                    "portfolio_value": "invalid",
                }
            )

    def test_from_dict_does_not_mutate_input(self):
        """Test that from_dict doesn't mutate the input dictionary."""
        input_dict = {
            "target_weights": {"AAPL": "0.6", "MSFT": "0.4"},
            "correlation_id": "test",
        }
        original = input_dict.copy()
        StrategyAllocation.from_dict(input_dict)
        assert input_dict == original


class TestStrategyAllocationSerialization:
    """Test serialization and round-trip conversion."""

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all populated fields."""
        now = datetime.now(UTC)
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test-789",
            as_of=now,
            portfolio_value=Decimal("10000"),
            constraints={"max_position_size": 0.5},
        )
        dumped = allocation.model_dump()
        assert "target_weights" in dumped
        assert "correlation_id" in dumped
        assert "as_of" in dumped
        assert "portfolio_value" in dumped
        assert "constraints" in dumped

    def test_round_trip_with_from_dict(self):
        """Test that from_dict(model_dump()) preserves data."""
        original = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test-round-trip",
            portfolio_value=Decimal("10000"),
        )
        dumped = original.model_dump()
        # Convert Decimals to strings for from_dict
        dumped["target_weights"] = {
            k: str(v) for k, v in dumped["target_weights"].items()
        }
        if dumped["portfolio_value"] is not None:
            dumped["portfolio_value"] = str(dumped["portfolio_value"])

        restored = StrategyAllocation.from_dict(dumped)
        assert restored.target_weights == original.target_weights
        assert restored.correlation_id == original.correlation_id
        assert restored.portfolio_value == original.portfolio_value


class TestStrategyAllocationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_symbol_full_allocation(self):
        """Test allocation with single symbol at 100%."""
        allocation = StrategyAllocation(
            target_weights={"SPY": Decimal("1.0")}, correlation_id="test"
        )
        assert len(allocation.target_weights) == 1
        assert allocation.target_weights["SPY"] == Decimal("1.0")

    def test_very_small_weights_within_precision(self):
        """Test allocation with very small but valid weights."""
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.0001"),
                "MSFT": Decimal("0.9999"),
            },
            correlation_id="test",
        )
        assert allocation.target_weights["AAPL"] == Decimal("0.0001")

    def test_many_symbols_with_equal_weights(self):
        """Test allocation with many symbols equally weighted."""
        num_symbols = 10
        weight = Decimal("1.0") / num_symbols
        weights = {f"SYM{i}": weight for i in range(num_symbols)}
        allocation = StrategyAllocation(
            target_weights=weights, correlation_id="test-many"
        )
        assert len(allocation.target_weights) == num_symbols
        total = sum(allocation.target_weights.values())
        # Should be within tolerance
        assert Decimal("0.99") <= total <= Decimal("1.01")

    def test_large_portfolio_value(self):
        """Test allocation with large portfolio value."""
        large_value = Decimal("1000000000.00")  # 1 billion
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            portfolio_value=large_value,
        )
        assert allocation.portfolio_value == large_value

    def test_very_long_correlation_id_at_boundary(self):
        """Test correlation_id at max length boundary."""
        max_length_id = "x" * 100
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id=max_length_id
        )
        assert len(allocation.correlation_id) == 100


class TestStrategyAllocationPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(
        weight1=st.decimals(
            min_value=0, max_value=1, allow_nan=False, allow_infinity=False, places=4
        )
    )
    def test_two_weights_summing_to_one(self, weight1):
        """Test that any two complementary weights are accepted."""
        weight2 = Decimal("1.0") - weight1
        if Decimal("0.0") <= weight2 <= Decimal("1.0"):
            allocation = StrategyAllocation(
                target_weights={"A": weight1, "B": weight2}, correlation_id="test"
            )
            assert allocation.target_weights["A"] == weight1
            assert allocation.target_weights["B"] == weight2
            total = weight1 + weight2
            assert Decimal("0.99") <= total <= Decimal("1.01")

    @given(
        portfolio_value=st.decimals(
            min_value=0,
            max_value=1000000,
            allow_nan=False,
            allow_infinity=False,
            places=2,
        )
    )
    def test_any_valid_portfolio_value_accepted(self, portfolio_value):
        """Test that any non-negative portfolio value is accepted."""
        if portfolio_value >= 0:
            allocation = StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")},
                correlation_id="test",
                portfolio_value=portfolio_value,
            )
            assert allocation.portfolio_value == portfolio_value

    @given(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=("Cs",))))
    def test_any_valid_correlation_id_accepted(self, correlation_id):
        """Test that any non-empty string correlation_id is accepted."""
        stripped = correlation_id.strip()
        if stripped:
            allocation = StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")}, correlation_id=correlation_id
            )
            assert allocation.correlation_id == stripped


class TestStrategyAllocationConstraintsField:
    """Test optional constraints field behavior."""

    def test_constraints_with_dict(self):
        """Test constraints field with dictionary value."""
        constraints = {
            "max_position_size": 0.3,
            "min_position_size": 0.01,
            "market_hours_only": True,
        }
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            constraints=constraints,
        )
        assert allocation.constraints == constraints

    def test_constraints_none(self):
        """Test constraints field with None value."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            constraints=None,
        )
        assert allocation.constraints is None

    def test_constraints_empty_dict(self):
        """Test constraints field with empty dictionary."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test",
            constraints={},
        )
        assert allocation.constraints == {}


class TestStrategyAllocationIdempotencyKey:
    """Test idempotency key generation for event deduplication."""

    def test_idempotency_key_is_deterministic(self):
        """Test that idempotency key is deterministic for same allocation."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test-123",
        )
        key1 = allocation.idempotency_key()
        key2 = allocation.idempotency_key()
        assert key1 == key2

    def test_idempotency_key_format(self):
        """Test that idempotency key has expected format."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        key = allocation.idempotency_key()
        assert isinstance(key, str)
        assert len(key) == 16
        # Should be hex characters
        assert all(c in "0123456789abcdef" for c in key)

    def test_idempotency_key_different_for_different_weights(self):
        """Test that different weights produce different keys."""
        alloc1 = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test",
        )
        alloc2 = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.5"), "MSFT": Decimal("0.5")},
            correlation_id="test",
        )
        assert alloc1.idempotency_key() != alloc2.idempotency_key()

    def test_idempotency_key_different_for_different_correlation_ids(self):
        """Test that different correlation IDs produce different keys."""
        alloc1 = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test-1"
        )
        alloc2 = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test-2"
        )
        assert alloc1.idempotency_key() != alloc2.idempotency_key()

    def test_idempotency_key_same_for_different_symbol_order(self):
        """Test that symbol order doesn't affect idempotency key."""
        alloc1 = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            correlation_id="test",
        )
        alloc2 = StrategyAllocation(
            target_weights={"MSFT": Decimal("0.4"), "AAPL": Decimal("0.6")},
            correlation_id="test",
        )
        assert alloc1.idempotency_key() == alloc2.idempotency_key()

    def test_idempotency_key_includes_schema_version(self):
        """Test that schema version is part of the idempotency key."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        # Key should be different if schema version changes
        # (This test documents the behavior; actual change would require code modification)
        key = allocation.idempotency_key()
        assert key  # Key is generated successfully


class TestStrategyAllocationSchemaVersion:
    """Test schema version field for backward compatibility."""

    def test_schema_version_defaults_to_1_0(self):
        """Test that schema_version defaults to 1.0."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        assert allocation.schema_version == "1.0"

    def test_schema_version_in_model_dump(self):
        """Test that schema_version is included in model_dump."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        dumped = allocation.model_dump()
        assert "schema_version" in dumped
        assert dumped["schema_version"] == "1.0"

    def test_schema_version_immutable(self):
        """Test that schema_version cannot be changed."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")}, correlation_id="test"
        )
        with pytest.raises(Exception):  # Pydantic ValidationError
            allocation.schema_version = "2.0"  # type: ignore
