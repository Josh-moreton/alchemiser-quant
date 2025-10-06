"""Business Unit: shared | Status: current.

Comprehensive unit tests for StrategyType enumeration.

Tests StrategyType enum functionality including member access, values,
iteration, immutability, and usage patterns.
"""

import pytest

from the_alchemiser.shared.types.strategy_types import StrategyType


class TestStrategyTypeEnumMembers:
    """Test StrategyType enum members and values."""

    @pytest.mark.unit
    def test_enum_members_exist(self):
        """Test all expected strategy types are defined."""
        assert hasattr(StrategyType, "NUCLEAR")
        assert hasattr(StrategyType, "TECL")
        assert hasattr(StrategyType, "KLM")
        assert hasattr(StrategyType, "DSL")

    @pytest.mark.unit
    def test_enum_values_are_strings(self):
        """Test enum values are lowercase strategy identifiers."""
        assert StrategyType.NUCLEAR.value == "nuclear"
        assert StrategyType.TECL.value == "tecl"
        assert StrategyType.KLM.value == "klm"
        assert StrategyType.DSL.value == "dsl"

    @pytest.mark.unit
    def test_enum_member_count(self):
        """Test correct number of strategy types are defined."""
        strategies = list(StrategyType)
        assert len(strategies) == 4

    @pytest.mark.unit
    def test_all_members_present(self):
        """Test all expected members are in the enum."""
        strategies = list(StrategyType)
        assert StrategyType.NUCLEAR in strategies
        assert StrategyType.TECL in strategies
        assert StrategyType.KLM in strategies
        assert StrategyType.DSL in strategies


class TestStrategyTypeEnumBehavior:
    """Test StrategyType enum behavior and operations."""

    @pytest.mark.unit
    def test_enum_iteration(self):
        """Test iteration over enum members."""
        strategies = list(StrategyType)
        assert len(strategies) == 4
        # Test that we get actual enum members, not strings
        for strategy in strategies:
            assert isinstance(strategy, StrategyType)

    @pytest.mark.unit
    def test_enum_membership(self):
        """Test enum membership checks."""
        assert StrategyType.DSL in StrategyType
        assert StrategyType.NUCLEAR in StrategyType
        # Values are not members, only enum instances
        # (checking this would be a TypeError in Python 3.12+)

    @pytest.mark.unit
    def test_enum_comparison_equality(self):
        """Test enum comparison operations."""
        assert StrategyType.NUCLEAR == StrategyType.NUCLEAR
        assert StrategyType.NUCLEAR != StrategyType.TECL
        assert StrategyType.DSL == StrategyType.DSL

    @pytest.mark.unit
    def test_enum_comparison_identity(self):
        """Test enum members are singletons."""
        # Enum members should be the same object (identity)
        nuclear1 = StrategyType.NUCLEAR
        nuclear2 = StrategyType.NUCLEAR
        assert nuclear1 is nuclear2

    @pytest.mark.unit
    def test_enum_hashable(self):
        """Test enum members are hashable (can be dict keys)."""
        allocation = {StrategyType.DSL: 1.0}
        assert allocation[StrategyType.DSL] == 1.0

        # Test with multiple keys
        multi_allocation = {
            StrategyType.NUCLEAR: 0.3,
            StrategyType.TECL: 0.5,
            StrategyType.KLM: 0.2,
        }
        assert len(multi_allocation) == 3
        assert multi_allocation[StrategyType.TECL] == 0.5


class TestStrategyTypeImmutability:
    """Test StrategyType immutability and safety."""

    @pytest.mark.unit
    def test_enum_cannot_be_modified(self):
        """Test enum member values cannot be modified."""
        with pytest.raises((AttributeError, TypeError)):
            StrategyType.NUCLEAR.value = "modified"  # type: ignore[misc]

    @pytest.mark.unit
    def test_enum_cannot_add_members(self):
        """Test new enum members cannot be added at runtime."""
        # In Python 3.11+, attempting to add enum members after class definition
        # doesn't raise an error immediately but the new attribute won't be an enum member
        original_members = set(StrategyType)
        try:
            StrategyType.NEW_STRATEGY = "new"  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            # Some Python versions may raise an error
            pass
        else:
            # If no error, verify it's not a valid enum member
            assert StrategyType.NEW_STRATEGY not in StrategyType  # type: ignore[attr-defined]
            assert set(StrategyType) == original_members

    @pytest.mark.unit
    def test_enum_cannot_delete_members(self):
        """Test enum members cannot be deleted."""
        with pytest.raises((AttributeError, TypeError)):
            del StrategyType.NUCLEAR  # type: ignore[attr-defined]


class TestStrategyTypeStringRepresentation:
    """Test StrategyType string representation."""

    @pytest.mark.unit
    def test_enum_string_representation(self):
        """Test string representation of enum members."""
        assert str(StrategyType.NUCLEAR) == "StrategyType.NUCLEAR"
        assert str(StrategyType.DSL) == "StrategyType.DSL"

    @pytest.mark.unit
    def test_enum_repr_representation(self):
        """Test repr representation of enum members."""
        assert repr(StrategyType.NUCLEAR) == "<StrategyType.NUCLEAR: 'nuclear'>"
        assert repr(StrategyType.TECL) == "<StrategyType.TECL: 'tecl'>"
        assert repr(StrategyType.KLM) == "<StrategyType.KLM: 'klm'>"
        assert repr(StrategyType.DSL) == "<StrategyType.DSL: 'dsl'>"

    @pytest.mark.unit
    def test_enum_name_attribute(self):
        """Test enum member name attribute."""
        assert StrategyType.NUCLEAR.name == "NUCLEAR"
        assert StrategyType.TECL.name == "TECL"
        assert StrategyType.KLM.name == "KLM"
        assert StrategyType.DSL.name == "DSL"

    @pytest.mark.unit
    def test_enum_value_attribute(self):
        """Test enum member value attribute."""
        assert StrategyType.NUCLEAR.value == "nuclear"
        assert StrategyType.TECL.value == "tecl"
        assert StrategyType.KLM.value == "klm"
        assert StrategyType.DSL.value == "dsl"


class TestStrategyTypeUsagePatterns:
    """Test common usage patterns with StrategyType."""

    @pytest.mark.unit
    def test_enum_as_dict_key(self):
        """Test using enum as dictionary key (allocation pattern)."""
        allocations = {
            StrategyType.NUCLEAR: 0.3,
            StrategyType.TECL: 0.5,
            StrategyType.KLM: 0.2,
        }
        assert sum(allocations.values()) == pytest.approx(1.0)
        assert StrategyType.NUCLEAR in allocations
        assert allocations[StrategyType.TECL] == 0.5

    @pytest.mark.unit
    def test_enum_iteration_for_validation(self):
        """Test iterating over enum for validation (common pattern)."""
        valid_strategies = {StrategyType.NUCLEAR, StrategyType.TECL, StrategyType.KLM}

        for strategy in StrategyType:
            # This is the pattern used in validation code
            assert isinstance(strategy, StrategyType)
            # Enum member can be compared
            if strategy == StrategyType.DSL:
                assert strategy not in valid_strategies
            else:
                assert strategy in valid_strategies

    @pytest.mark.unit
    def test_enum_value_extraction(self):
        """Test extracting string values from enum (for serialization)."""
        strategies = [strategy.value for strategy in StrategyType]
        assert strategies == ["nuclear", "tecl", "klm", "dsl"]

    @pytest.mark.unit
    def test_enum_filtering(self):
        """Test filtering enum members by value."""
        dsl_strategies = [s for s in StrategyType if s.value == "dsl"]
        assert len(dsl_strategies) == 1
        assert dsl_strategies[0] == StrategyType.DSL

    @pytest.mark.unit
    def test_enum_access_by_name(self):
        """Test accessing enum by name string."""
        # This is how you access enum by name
        nuclear = StrategyType["NUCLEAR"]
        assert nuclear == StrategyType.NUCLEAR

        dsl = StrategyType["DSL"]
        assert dsl == StrategyType.DSL

    @pytest.mark.unit
    def test_enum_access_by_value(self):
        """Test accessing enum by value string."""
        # This is how you access enum by value
        nuclear = StrategyType("nuclear")
        assert nuclear == StrategyType.NUCLEAR

        dsl = StrategyType("dsl")
        assert dsl == StrategyType.DSL

    @pytest.mark.unit
    def test_invalid_enum_access_by_name(self):
        """Test that invalid name raises KeyError."""
        with pytest.raises(KeyError):
            _ = StrategyType["INVALID"]

    @pytest.mark.unit
    def test_invalid_enum_access_by_value(self):
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            _ = StrategyType("invalid")


class TestStrategyTypeTypeChecking:
    """Test StrategyType with type checking patterns."""

    @pytest.mark.unit
    def test_isinstance_check(self):
        """Test isinstance checks work correctly."""
        assert isinstance(StrategyType.NUCLEAR, StrategyType)
        assert isinstance(StrategyType.DSL, StrategyType)
        assert not isinstance("nuclear", StrategyType)
        assert not isinstance(1, StrategyType)

    @pytest.mark.unit
    def test_type_annotation_usage(self):
        """Test usage in type-annotated functions."""

        def get_allocation(strategy: StrategyType) -> float:
            """Example function with type annotation."""
            allocations = {StrategyType.DSL: 1.0}
            return allocations.get(strategy, 0.0)

        # This should work with type checking
        result = get_allocation(StrategyType.DSL)
        assert result == 1.0

        result = get_allocation(StrategyType.NUCLEAR)
        assert result == 0.0

    @pytest.mark.unit
    def test_dict_type_annotation_usage(self):
        """Test usage in dict type annotations."""

        def create_allocations() -> dict[StrategyType, float]:
            """Example function returning typed dict."""
            return {StrategyType.DSL: 1.0}

        allocations = create_allocations()
        assert isinstance(allocations, dict)
        assert StrategyType.DSL in allocations
        assert allocations[StrategyType.DSL] == 1.0
