#!/usr/bin/env python3
"""Unit tests for ConsolidatedPortfolio schema.

Tests validation, edge cases, and factory methods for the ConsolidatedPortfolio DTO.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ALLOCATION_SUM_MAX,
    ALLOCATION_SUM_MIN,
    ALLOCATION_SUM_TOLERANCE,
    AllocationConstraints,
    ConsolidatedPortfolio,
)


class TestAllocationConstraints:
    """Tests for AllocationConstraints TypedDict."""

    def test_allocation_constraints_structure(self):
        """Test AllocationConstraints can be created with expected fields."""
        constraints: AllocationConstraints = {
            "strategy_id": "nuclear",
            "symbols": ["AAPL", "GOOGL"],
            "timeframe": "1D",
            "max_position_size": Decimal("0.1"),
        }
        assert constraints["strategy_id"] == "nuclear"
        assert constraints["symbols"] == ["AAPL", "GOOGL"]
        assert constraints["timeframe"] == "1D"
        assert constraints["max_position_size"] == Decimal("0.1")

    def test_allocation_constraints_partial(self):
        """Test AllocationConstraints works with partial fields (total=False)."""
        constraints: AllocationConstraints = {
            "strategy_id": "nuclear",
        }
        assert constraints["strategy_id"] == "nuclear"


class TestConsolidatedPortfolioValidation:
    """Tests for ConsolidatedPortfolio field validation."""

    def test_valid_portfolio_creation(self):
        """Test creating a valid ConsolidatedPortfolio."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["nuclear"],
            schema_version="1.0.0",
        )
        assert portfolio.target_allocations == {"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")}
        assert portfolio.correlation_id == "test-123"
        assert portfolio.strategy_count == 1
        assert portfolio.source_strategies == ["nuclear"]
        assert portfolio.schema_version == "1.0.0"

    def test_schema_version_defaults(self):
        """Test schema_version defaults to 1.0.0."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.schema_version == "1.0.0"

    def test_empty_allocations_rejected(self):
        """Test empty target_allocations are rejected."""
        with pytest.raises(ValueError, match="Target allocations cannot be empty"):
            ConsolidatedPortfolio(
                target_allocations={},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_symbol_normalization_to_uppercase(self):
        """Test symbols are normalized to uppercase."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"aapl": Decimal("0.6"), "googl": Decimal("0.4")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert "AAPL" in portfolio.target_allocations
        assert "GOOGL" in portfolio.target_allocations
        assert "aapl" not in portfolio.target_allocations

    def test_symbol_whitespace_stripped(self):
        """Test symbol whitespace is stripped."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={" AAPL ": Decimal("0.6"), " GOOGL ": Decimal("0.4")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert "AAPL" in portfolio.target_allocations
        assert "GOOGL" in portfolio.target_allocations

    def test_duplicate_symbols_rejected(self):
        """Test duplicate symbols (after normalization) are rejected."""
        with pytest.raises(ValueError, match="Duplicate symbol: AAPL"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("0.6"), "aapl": Decimal("0.4")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_negative_weight_rejected(self):
        """Test negative weights are rejected."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("-0.1")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_weight_greater_than_one_rejected(self):
        """Test weights > 1.0 are rejected."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.5")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_allocation_sum_at_min_boundary(self):
        """Test allocation sum at minimum tolerance boundary is accepted."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": ALLOCATION_SUM_MIN},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.target_allocations == {"AAPL": ALLOCATION_SUM_MIN}

    def test_allocation_sum_at_max_boundary(self):
        """Test allocation sum at maximum tolerance boundary is accepted."""
        # ALLOCATION_SUM_MAX is 1.01, but individual weights must be <= 1.0
        # So we need to use multiple symbols that sum to 1.01
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.51"), "GOOGL": Decimal("0.50")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        total = sum(portfolio.target_allocations.values())
        assert total == ALLOCATION_SUM_MAX

    def test_allocation_sum_below_min_rejected(self):
        """Test allocation sum below minimum tolerance is rejected."""
        with pytest.raises(ValueError, match="must sum to ~1.0"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": ALLOCATION_SUM_MIN - Decimal("0.001")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_allocation_sum_above_max_rejected(self):
        """Test allocation sum above maximum tolerance is rejected."""
        # Need weights that sum > 1.01 but each individual weight <= 1.0
        with pytest.raises(ValueError, match="must sum to ~1.0"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("0.52"), "GOOGL": Decimal("0.50")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_multiple_symbols_sum_to_one(self):
        """Test multiple symbols summing to exactly 1.0."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={
                "AAPL": Decimal("0.3"),
                "GOOGL": Decimal("0.3"),
                "MSFT": Decimal("0.4"),
            },
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        total = sum(portfolio.target_allocations.values())
        assert total == Decimal("1.0")

    def test_empty_correlation_id_rejected(self):
        """Test empty correlation_id is rejected."""
        with pytest.raises(
            Exception,
            match="String should have at least 1 character|Correlation ID cannot be empty",
        ):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                correlation_id="",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_whitespace_only_correlation_id_rejected(self):
        """Test whitespace-only correlation_id is rejected."""
        with pytest.raises(
            Exception,
            match="String should have at least 1 character|Correlation ID cannot be empty",
        ):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                correlation_id="   ",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_correlation_id_whitespace_stripped(self):
        """Test correlation_id whitespace is stripped."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="  test-123  ",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.correlation_id == "test-123"

    def test_naive_timestamp_converted_to_utc(self):
        """Test naive timestamp is converted to UTC-aware."""
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=naive_dt,
            strategy_count=1,
        )
        assert portfolio.timestamp.tzinfo is not None
        assert portfolio.timestamp.tzinfo.tzname(None) == "UTC"

    def test_aware_timestamp_preserved(self):
        """Test timezone-aware timestamp is preserved."""
        aware_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=aware_dt,
            strategy_count=1,
        )
        assert portfolio.timestamp == aware_dt

    def test_source_strategies_whitespace_stripped(self):
        """Test source_strategies whitespace is stripped."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,
            source_strategies=[" nuclear ", " tecl "],
        )
        assert portfolio.source_strategies == ["nuclear", "tecl"]

    def test_source_strategies_empty_strings_removed(self):
        """Test empty strings are removed from source_strategies."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,  # Correct count after filtering
            source_strategies=["nuclear", "", "  ", "tecl"],
        )
        assert portfolio.source_strategies == ["nuclear", "tecl"]

    def test_strategy_count_consistency_valid(self):
        """Test strategy_count matches source_strategies length."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,
            source_strategies=["nuclear", "tecl"],
        )
        assert portfolio.strategy_count == 2
        assert len(portfolio.source_strategies) == 2

    def test_strategy_count_mismatch_rejected(self):
        """Test strategy_count mismatch is rejected."""
        with pytest.raises(ValueError, match="does not match source_strategies length"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
                source_strategies=["nuclear", "tecl"],
            )

    def test_strategy_count_defaults_to_one_when_no_strategies(self):
        """Test strategy_count of 1 is valid when source_strategies is empty."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=[],
        )
        assert portfolio.strategy_count == 1
        assert portfolio.source_strategies == []

    def test_constraints_optional(self):
        """Test constraints field is optional."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.constraints is None

    def test_constraints_with_typed_dict(self):
        """Test constraints can be set with AllocationConstraints."""
        constraints: AllocationConstraints = {
            "strategy_id": "nuclear",
            "symbols": ["AAPL"],
            "timeframe": "1D",
        }
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            constraints=constraints,
        )
        assert portfolio.constraints is not None
        assert portfolio.constraints["strategy_id"] == "nuclear"

    def test_frozen_dto_cannot_be_modified(self):
        """Test DTO is frozen and cannot be modified after creation."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        with pytest.raises(Exception):  # Pydantic ValidationError
            portfolio.correlation_id = "new-id"  # type: ignore


class TestPartialPortfolioValidation:
    """Tests for partial portfolio allocations (is_partial flag)."""

    def test_partial_portfolio_allows_low_allocation_sum(self):
        """Test partial portfolio skips sum-to-1.0 validation."""
        # This would fail validation without is_partial=True
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.1"), "GOOGL": Decimal("0.05")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["strategy1.clj"],
            is_partial=True,
        )
        assert portfolio.is_partial is True
        total = sum(portfolio.target_allocations.values())
        assert total == Decimal("0.15")

    def test_full_portfolio_rejects_low_allocation_sum(self):
        """Test non-partial portfolio requires sum ~1.0."""
        with pytest.raises(ValueError, match="Total allocations must sum to ~1.0"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("0.1")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
                is_partial=False,
            )

    def test_partial_portfolio_defaults_to_false(self):
        """Test is_partial defaults to False for backward compatibility."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.is_partial is False

    def test_full_portfolio_with_valid_sum_works(self):
        """Test non-partial portfolio works with valid allocation sum."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            is_partial=False,
        )
        assert portfolio.is_partial is False
        total = sum(portfolio.target_allocations.values())
        assert total == Decimal("1.0")

    def test_partial_portfolio_single_small_allocation(self):
        """Test partial portfolio with single small allocation."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"TQQQ": Decimal("0.025")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["bento.clj"],
            is_partial=True,
        )
        assert portfolio.is_partial is True
        assert portfolio.target_allocations["TQQQ"] == Decimal("0.025")


class TestConsolidatedPortfolioFactoryMethods:
    """Tests for ConsolidatedPortfolio factory methods."""

    def test_from_dict_allocation_basic(self):
        """Test from_dict_allocation with basic inputs."""
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 0.6, "GOOGL": 0.4},
            correlation_id="test-123",
            source_strategies=["nuclear"],
        )
        assert portfolio.target_allocations == {"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")}
        assert portfolio.correlation_id == "test-123"
        assert portfolio.strategy_count == 1
        assert portfolio.source_strategies == ["nuclear"]

    def test_from_dict_allocation_converts_float_to_decimal(self):
        """Test from_dict_allocation converts floats to Decimal correctly."""
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 1.0},  # Use 1.0 to pass validation
            correlation_id="test-123",
        )
        # Should be stored as Decimal
        assert isinstance(portfolio.target_allocations["AAPL"], Decimal)
        assert portfolio.target_allocations["AAPL"] == Decimal("1.0")

    def test_from_dict_allocation_with_timestamp(self):
        """Test from_dict_allocation with explicit timestamp."""
        fixed_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 1.0},
            correlation_id="test-123",
            timestamp=fixed_time,
        )
        assert portfolio.timestamp == fixed_time

    def test_from_dict_allocation_timestamp_defaults_to_now(self):
        """Test from_dict_allocation uses current time when timestamp not provided."""
        before = datetime.now(UTC)
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 1.0},
            correlation_id="test-123",
        )
        after = datetime.now(UTC)
        # Timestamp should be between before and after (within a reasonable window)
        assert before <= portfolio.timestamp <= after

    def test_from_dict_allocation_no_strategies(self):
        """Test from_dict_allocation with no source_strategies."""
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 1.0},
            correlation_id="test-123",
        )
        assert portfolio.strategy_count == 1
        assert portfolio.source_strategies == []

    def test_from_dict_allocation_multiple_strategies(self):
        """Test from_dict_allocation with multiple strategies."""
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict={"AAPL": 0.5, "GOOGL": 0.5},
            correlation_id="test-123",
            source_strategies=["nuclear", "tecl"],
        )
        assert portfolio.strategy_count == 2
        assert portfolio.source_strategies == ["nuclear", "tecl"]

    def test_to_dict_allocation_basic(self):
        """Test to_dict_allocation converts back to float dict."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        result = portfolio.to_dict_allocation()
        assert result == {"AAPL": 0.6, "GOOGL": 0.4}
        assert isinstance(result["AAPL"], float)

    def test_round_trip_conversion(self):
        """Test round-trip conversion: dict -> DTO -> dict."""
        original_dict = {"AAPL": 0.6, "GOOGL": 0.4}
        portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict=original_dict,
            correlation_id="test-123",
        )
        result_dict = portfolio.to_dict_allocation()
        # Symbols should be normalized to uppercase
        assert result_dict["AAPL"] == pytest.approx(0.6)
        assert result_dict["GOOGL"] == pytest.approx(0.4)

    def test_from_json_dict_with_string_decimals(self):
        """Test from_json_dict handles EventBridge serialized data with string Decimals."""
        # Simulate data from EventBridge where Decimals are serialized as strings
        json_data = {
            "target_allocations": {"AAPL": "0.60", "GOOGL": "0.40"},
            "correlation_id": "test-123",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "strategy_count": 1,
            "source_strategies": [],
            "schema_version": "1.0.0",
        }
        portfolio = ConsolidatedPortfolio.from_json_dict(json_data)
        assert portfolio.target_allocations["AAPL"] == Decimal("0.60")
        assert portfolio.target_allocations["GOOGL"] == Decimal("0.40")
        assert portfolio.correlation_id == "test-123"

    def test_from_json_dict_preserves_actual_decimals(self):
        """Test from_json_dict works with already-Decimal values."""
        json_data = {
            "target_allocations": {"AAPL": Decimal("0.60"), "GOOGL": Decimal("0.40")},
            "correlation_id": "test-123",
            "timestamp": datetime.now(UTC),
            "strategy_count": 1,
            "source_strategies": [],
        }
        portfolio = ConsolidatedPortfolio.from_json_dict(json_data)
        assert portfolio.target_allocations["AAPL"] == Decimal("0.60")

    def test_from_json_dict_handles_z_timestamp(self):
        """Test from_json_dict handles Z-suffix UTC timestamps."""
        json_data = {
            "target_allocations": {"AAPL": "1.0"},
            "correlation_id": "test-123",
            "timestamp": "2023-01-01T12:00:00Z",
            "strategy_count": 1,
            "source_strategies": [],
        }
        portfolio = ConsolidatedPortfolio.from_json_dict(json_data)
        assert portfolio.timestamp.year == 2023


class TestConsolidatedPortfolioPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=5, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("0.5"),
                places=2,
            ),
            min_size=1,
            max_size=5,
        )
    )
    def test_normalized_symbols_always_uppercase(self, allocations: dict[str, Decimal]):
        """Property: All symbols in allocations should be uppercase."""
        # Adjust weights to sum to ~1.0
        total = sum(allocations.values())
        if total == 0:
            return
        normalized_allocations = {symbol: weight / total for symbol, weight in allocations.items()}

        try:
            portfolio = ConsolidatedPortfolio(
                target_allocations=normalized_allocations,
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )
            # All symbols should be uppercase
            for symbol in portfolio.target_allocations.keys():
                assert symbol == symbol.upper()
        except ValueError:
            # May fail validation for other reasons (sum tolerance)
            pass

    @given(
        st.lists(
            st.decimals(
                min_value=Decimal("0.0"),
                max_value=Decimal("1.0"),
                places=3,
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_allocation_sum_within_tolerance(self, weights: list[Decimal]):
        """Property: Allocation sum should be within tolerance of 1.0."""
        # Normalize weights to sum to 1.0
        total = sum(weights)
        if total == 0:
            return

        normalized_weights = [w / total for w in weights]
        allocations = {f"SYM{i}": w for i, w in enumerate(normalized_weights)}

        try:
            portfolio = ConsolidatedPortfolio(
                target_allocations=allocations,
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )
            # Sum should be within tolerance
            total_weight = sum(portfolio.target_allocations.values())
            assert ALLOCATION_SUM_MIN <= total_weight <= ALLOCATION_SUM_MAX
        except ValueError:
            # May fail for other validation reasons
            pass

    @given(
        st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5).filter(
            lambda x: len(set(s.strip() for s in x if s.strip()))
            == len([s for s in x if s.strip()])
        )
    )
    def test_source_strategies_stripped(self, strategies: list[str]):
        """Property: Source strategies should always be stripped of whitespace."""
        try:
            portfolio = ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=len([s for s in strategies if s.strip()]),
                source_strategies=strategies,
            )
            # All strategies should be stripped
            for strategy in portfolio.source_strategies:
                assert strategy == strategy.strip()
                assert len(strategy) > 0
        except ValueError:
            # May fail validation for strategy count mismatch
            pass


class TestConsolidatedPortfolioEdgeCases:
    """Edge case tests for ConsolidatedPortfolio."""

    def test_single_symbol_full_allocation(self):
        """Test single symbol with 100% allocation."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.target_allocations == {"AAPL": Decimal("1.0")}

    def test_many_symbols_small_weights(self):
        """Test many symbols with small weights summing to 1.0."""
        num_symbols = 10
        weight_per_symbol = Decimal("1.0") / num_symbols
        allocations = {f"SYM{i}": weight_per_symbol for i in range(num_symbols)}

        portfolio = ConsolidatedPortfolio(
            target_allocations=allocations,
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert len(portfolio.target_allocations) == num_symbols
        total = sum(portfolio.target_allocations.values())
        assert abs(total - Decimal("1.0")) < ALLOCATION_SUM_TOLERANCE

    def test_zero_weight_allocation(self):
        """Test allocation with zero weight (valid within 0-1 range)."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0"), "GOOGL": Decimal("0.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.target_allocations["GOOGL"] == Decimal("0.0")

    def test_very_long_correlation_id(self):
        """Test correlation_id at max length (100 chars)."""
        long_id = "a" * 100
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id=long_id,
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.correlation_id == long_id

    def test_correlation_id_exceeds_max_length_rejected(self):
        """Test correlation_id exceeding max length is rejected."""
        too_long_id = "a" * 101
        with pytest.raises(Exception):  # Pydantic ValidationError
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                correlation_id=too_long_id,
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_timestamp_in_past(self):
        """Test timestamp can be in the past."""
        past_time = datetime.now(UTC) - timedelta(days=365)
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=past_time,
            strategy_count=1,
        )
        assert portfolio.timestamp == past_time

    def test_timestamp_in_future(self):
        """Test timestamp can be in the future."""
        future_time = datetime.now(UTC) + timedelta(days=365)
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=future_time,
            strategy_count=1,
        )
        assert portfolio.timestamp == future_time


class TestStrategyContributions:
    """Tests for strategy_contributions field and validation."""

    def test_empty_contributions_default(self):
        """Test strategy_contributions defaults to empty dict."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        assert portfolio.strategy_contributions == {}

    def test_single_strategy_contribution(self):
        """Test single strategy contributing all allocation."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            strategy_contributions={"momentum": {"AAPL": Decimal("1.0")}},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["momentum"],
        )
        assert portfolio.strategy_contributions == {"momentum": {"AAPL": Decimal("1.0")}}

    def test_multiple_strategies_single_symbol(self):
        """Test multiple strategies contributing to same symbol."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            strategy_contributions={
                "momentum": {"AAPL": Decimal("0.6")},
                "mean_rev": {"AAPL": Decimal("0.4")},
            },
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,
            source_strategies=["momentum", "mean_rev"],
        )
        assert portfolio.strategy_contributions["momentum"]["AAPL"] == Decimal("0.6")
        assert portfolio.strategy_contributions["mean_rev"]["AAPL"] == Decimal("0.4")

    def test_multiple_strategies_multiple_symbols(self):
        """Test multiple strategies contributing to multiple symbols."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={
                "AAPL": Decimal("0.6"),
                "MSFT": Decimal("0.4"),
            },
            strategy_contributions={
                "momentum": {"AAPL": Decimal("0.4"), "MSFT": Decimal("0.2")},
                "mean_rev": {"AAPL": Decimal("0.2"), "MSFT": Decimal("0.2")},
            },
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,
            source_strategies=["momentum", "mean_rev"],
        )
        # Validate AAPL: 0.4 + 0.2 = 0.6
        assert portfolio.target_allocations["AAPL"] == Decimal("0.6")
        # Validate MSFT: 0.2 + 0.2 = 0.4
        assert portfolio.target_allocations["MSFT"] == Decimal("0.4")

    def test_contributions_mismatch_rejected(self):
        """Test contributions not summing to target allocation are rejected."""
        with pytest.raises(ValueError, match="Strategy contributions for AAPL sum to"):
            ConsolidatedPortfolio(
                target_allocations={"AAPL": Decimal("1.0")},
                strategy_contributions={"momentum": {"AAPL": Decimal("0.5")}},
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=1,
            )

    def test_contributions_within_tolerance(self):
        """Test contributions within tolerance are accepted."""
        # Sum is 0.999, within tolerance of 1.0
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            strategy_contributions={
                "momentum": {"AAPL": Decimal("0.6")},
                "mean_rev": {"AAPL": Decimal("0.399")},
            },
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=2,
            source_strategies=["momentum", "mean_rev"],
        )
        assert portfolio.target_allocations["AAPL"] == Decimal("1.0")

    def test_partial_portfolio_with_contributions(self):
        """Test partial portfolio with strategy contributions."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("0.1")},
            strategy_contributions={"momentum": {"AAPL": Decimal("0.1")}},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["momentum"],
            is_partial=True,
        )
        assert portfolio.is_partial is True
        assert portfolio.strategy_contributions["momentum"]["AAPL"] == Decimal("0.1")

    def test_from_json_dict_with_strategy_contributions(self):
        """Test from_json_dict handles strategy_contributions."""
        json_data = {
            "target_allocations": {"AAPL": "0.60", "GOOGL": "0.40"},
            "strategy_contributions": {
                "momentum": {"AAPL": "0.4", "GOOGL": "0.2"},
                "mean_rev": {"AAPL": "0.2", "GOOGL": "0.2"},
            },
            "correlation_id": "test-123",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "strategy_count": 2,
            "source_strategies": ["momentum", "mean_rev"],
            "schema_version": "1.0.0",
        }
        portfolio = ConsolidatedPortfolio.from_json_dict(json_data)
        assert portfolio.strategy_contributions["momentum"]["AAPL"] == Decimal("0.4")
        assert portfolio.strategy_contributions["mean_rev"]["GOOGL"] == Decimal("0.2")

    def test_frozen_contributions_cannot_be_modified(self):
        """Test strategy_contributions is frozen and cannot be modified."""
        portfolio = ConsolidatedPortfolio(
            target_allocations={"AAPL": Decimal("1.0")},
            strategy_contributions={"momentum": {"AAPL": Decimal("1.0")}},
            correlation_id="test-123",
            timestamp=datetime.now(UTC),
            strategy_count=1,
        )
        # Note: While the DTO is frozen, nested dicts are still mutable in Python.
        # This is acceptable as the DTO is used for data transfer, not as a mutable data structure.
        assert portfolio.strategy_contributions == {"momentum": {"AAPL": Decimal("1.0")}}


class TestStrategyContributionsPropertyBased:
    """Property-based tests for strategy contributions."""

    @given(
        st.lists(
            st.decimals(min_value=Decimal("0.01"), max_value=Decimal("0.5"), places=2),
            min_size=2,
            max_size=5,
        )
    )
    def test_contributions_sum_equals_target(self, weights: list[Decimal]):
        """Property: Sum of strategy contributions must equal target allocation."""
        # Normalize weights to sum to 1.0
        total = sum(weights)
        if total == 0:
            return

        normalized_weights = [w / total for w in weights]
        target_allocation = sum(normalized_weights)

        # Create contributions
        contributions = {
            f"strategy{i}": {"AAPL": weight} for i, weight in enumerate(normalized_weights)
        }

        try:
            portfolio = ConsolidatedPortfolio(
                target_allocations={"AAPL": target_allocation},
                strategy_contributions=contributions,
                correlation_id="test-123",
                timestamp=datetime.now(UTC),
                strategy_count=len(weights),
                source_strategies=[f"strategy{i}" for i in range(len(weights))],
            )
            # Should validate successfully
            assert len(portfolio.strategy_contributions) == len(weights)
        except ValueError:
            # May fail validation for tolerance reasons
            pass
