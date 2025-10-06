"""Business Unit: shared | Status: current.

Comprehensive unit tests for StrategyRegistry bridge class.

Tests StrategyRegistry compatibility types and default allocations
during migration to strategy_v2 per project guardrails.
"""

import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.types.strategy_registry import StrategyRegistry
from the_alchemiser.shared.types.strategy_types import StrategyType


class TestStrategyRegistryGetDefaultAllocations:
    """Test StrategyRegistry.get_default_allocations method."""

    @pytest.mark.unit
    def test_returns_dict_with_strategy_type_keys(self):
        """Test that get_default_allocations returns a dict with StrategyType keys."""
        allocations = StrategyRegistry.get_default_allocations()
        assert isinstance(allocations, dict)
        for key in allocations.keys():
            assert isinstance(key, StrategyType)

    @pytest.mark.unit
    def test_returns_dict_with_float_values(self):
        """Test that get_default_allocations returns a dict with float values."""
        allocations = StrategyRegistry.get_default_allocations()
        for value in allocations.values():
            assert isinstance(value, float)

    @pytest.mark.unit
    def test_dsl_strategy_has_full_allocation(self):
        """Test that DSL strategy has 1.0 allocation in DSL-only phase."""
        allocations = StrategyRegistry.get_default_allocations()
        assert StrategyType.DSL in allocations
        assert allocations[StrategyType.DSL] == 1.0

    @pytest.mark.unit
    def test_returns_non_empty_dict(self):
        """Test that get_default_allocations returns non-empty dict."""
        allocations = StrategyRegistry.get_default_allocations()
        assert len(allocations) > 0

    @pytest.mark.unit
    def test_allocation_values_are_non_negative(self):
        """Test that all allocation values are non-negative."""
        allocations = StrategyRegistry.get_default_allocations()
        for value in allocations.values():
            assert value >= 0.0

    @pytest.mark.unit
    def test_allocation_values_are_at_most_one(self):
        """Test that all allocation values are at most 1.0."""
        allocations = StrategyRegistry.get_default_allocations()
        for value in allocations.values():
            assert value <= 1.0

    @pytest.mark.unit
    def test_allocations_sum_to_one(self):
        """Test that allocation values sum to 1.0 (100%)."""
        allocations = StrategyRegistry.get_default_allocations()
        total = sum(allocations.values())
        # Use tolerance for float comparison per guardrails
        assert abs(total - 1.0) < 1e-10

    @pytest.mark.unit
    def test_multiple_calls_return_same_result(self):
        """Test that multiple calls return consistent results (deterministic)."""
        allocations1 = StrategyRegistry.get_default_allocations()
        allocations2 = StrategyRegistry.get_default_allocations()
        assert allocations1 == allocations2

    @pytest.mark.unit
    def test_returned_dict_is_independent_copy(self):
        """Test that returned dict can be modified without affecting subsequent calls."""
        allocations1 = StrategyRegistry.get_default_allocations()
        original_length = len(allocations1)
        
        # Modify the returned dict
        allocations1[StrategyType.NUCLEAR] = 0.5
        
        # Get fresh allocations
        allocations2 = StrategyRegistry.get_default_allocations()
        
        # Should still have original length (DSL only in current phase)
        assert len(allocations2) == original_length


class TestStrategyRegistryIsStrategyEnabled:
    """Test StrategyRegistry.is_strategy_enabled method."""

    @pytest.mark.unit
    def test_returns_boolean(self):
        """Test that is_strategy_enabled returns a boolean."""
        result = StrategyRegistry.is_strategy_enabled(StrategyType.DSL)
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_dsl_strategy_is_enabled(self):
        """Test that DSL strategy is enabled."""
        assert StrategyRegistry.is_strategy_enabled(StrategyType.DSL) is True

    @pytest.mark.unit
    def test_nuclear_strategy_is_enabled(self):
        """Test that NUCLEAR strategy is enabled (all strategies enabled in DSL-only phase)."""
        assert StrategyRegistry.is_strategy_enabled(StrategyType.NUCLEAR) is True

    @pytest.mark.unit
    def test_tecl_strategy_is_enabled(self):
        """Test that TECL strategy is enabled (all strategies enabled in DSL-only phase)."""
        assert StrategyRegistry.is_strategy_enabled(StrategyType.TECL) is True

    @pytest.mark.unit
    def test_klm_strategy_is_enabled(self):
        """Test that KLM strategy is enabled (all strategies enabled in DSL-only phase)."""
        assert StrategyRegistry.is_strategy_enabled(StrategyType.KLM) is True

    @pytest.mark.unit
    def test_all_strategy_types_are_enabled(self):
        """Test that all StrategyType enum members are enabled."""
        for strategy_type in StrategyType:
            assert StrategyRegistry.is_strategy_enabled(strategy_type) is True

    @pytest.mark.unit
    def test_parameter_is_ignored(self):
        """Test that the parameter is ignored (underscore prefix indicates unused)."""
        # All calls should return True regardless of input
        result1 = StrategyRegistry.is_strategy_enabled(StrategyType.DSL)
        result2 = StrategyRegistry.is_strategy_enabled(StrategyType.NUCLEAR)
        assert result1 is True
        assert result2 is True


class TestStrategyRegistryContract:
    """Test StrategyRegistry contract and API compatibility."""

    @pytest.mark.unit
    def test_has_get_default_allocations_method(self):
        """Test that StrategyRegistry has get_default_allocations method."""
        assert hasattr(StrategyRegistry, 'get_default_allocations')
        assert callable(StrategyRegistry.get_default_allocations)

    @pytest.mark.unit
    def test_has_is_strategy_enabled_method(self):
        """Test that StrategyRegistry has is_strategy_enabled method."""
        assert hasattr(StrategyRegistry, 'is_strategy_enabled')
        assert callable(StrategyRegistry.is_strategy_enabled)

    @pytest.mark.unit
    def test_get_default_allocations_is_static_method(self):
        """Test that get_default_allocations is a static method."""
        # Can be called on class without instantiation
        allocations = StrategyRegistry.get_default_allocations()
        assert isinstance(allocations, dict)

    @pytest.mark.unit
    def test_is_strategy_enabled_is_static_method(self):
        """Test that is_strategy_enabled is a static method."""
        # Can be called on class without instantiation
        result = StrategyRegistry.is_strategy_enabled(StrategyType.DSL)
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_class_can_be_instantiated_but_unnecessary(self):
        """Test that StrategyRegistry can be instantiated (for compatibility)."""
        registry = StrategyRegistry()
        assert registry is not None
        # Methods still work on instance
        allocations = registry.get_default_allocations()
        assert isinstance(allocations, dict)


class TestStrategyRegistryTypeAnnotations:
    """Test that StrategyRegistry has correct type annotations."""

    @pytest.mark.unit
    def test_get_default_allocations_return_type(self):
        """Test that get_default_allocations returns correct type."""
        allocations = StrategyRegistry.get_default_allocations()
        # Should be dict[StrategyType, float]
        assert isinstance(allocations, dict)
        for key, value in allocations.items():
            assert isinstance(key, StrategyType)
            assert isinstance(value, float)

    @pytest.mark.unit
    def test_is_strategy_enabled_parameter_type(self):
        """Test that is_strategy_enabled accepts StrategyType."""
        # Should accept all StrategyType enum members
        for strategy_type in StrategyType:
            result = StrategyRegistry.is_strategy_enabled(strategy_type)
            assert isinstance(result, bool)


@given(st.sampled_from(list(StrategyType)))
@pytest.mark.unit
def test_is_strategy_enabled_property_based(strategy_type: StrategyType):
    """Property-based test: is_strategy_enabled always returns True for any StrategyType."""
    assert StrategyRegistry.is_strategy_enabled(strategy_type) is True


@given(st.integers(min_value=1, max_value=100))
@pytest.mark.unit
def test_get_default_allocations_deterministic_property(call_count: int):
    """Property-based test: get_default_allocations is deterministic across multiple calls."""
    results = [StrategyRegistry.get_default_allocations() for _ in range(call_count)]
    # All results should be equal
    first_result = results[0]
    for result in results[1:]:
        assert result == first_result
