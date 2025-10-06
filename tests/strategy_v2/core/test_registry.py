#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Comprehensive tests for strategy registry.

Tests cover:
- Registry initialization
- Strategy registration (single and multiple)
- Strategy retrieval (success and failure cases)
- Listing strategies
- Edge cases (empty IDs, duplicate registration, KeyError handling)
- Thread safety considerations
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from the_alchemiser.strategy_v2.core.registry import (
    StrategyEngine,
    StrategyRegistry,
    get_strategy,
    list_strategies,
    register_strategy,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
    from the_alchemiser.shared.types.market_data_port import MarketDataPort


@pytest.mark.unit
class TestStrategyRegistry:
    """Test StrategyRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance for each test."""
        return StrategyRegistry()

    @pytest.fixture
    def mock_engine(self):
        """Create a mock strategy engine."""

        class MockEngine:
            def __call__(
                self,
                context: datetime | MarketDataPort | dict[str, datetime | MarketDataPort],
            ) -> StrategyAllocation:
                """Mock strategy execution."""
                # This would normally return a StrategyAllocation
                from decimal import Decimal

                from the_alchemiser.shared.schemas.strategy_allocation import (
                    StrategyAllocation,
                )

                return StrategyAllocation(
                    target_weights={"SPY": Decimal("1.0")},
                    correlation_id="test-corr-id",
                )

        return MockEngine()

    def test_init_creates_empty_registry(self, registry):
        """Test that new registry is empty."""
        assert len(registry._strategies) == 0
        assert registry.list_strategies() == []

    def test_register_single_strategy(self, registry, mock_engine):
        """Test registering a single strategy."""
        strategy_id = "test_strategy"
        registry.register(strategy_id, mock_engine)

        assert strategy_id in registry._strategies
        assert registry._strategies[strategy_id] is mock_engine

    def test_register_multiple_strategies(self, registry, mock_engine):
        """Test registering multiple strategies."""
        registry.register("strategy1", mock_engine)
        registry.register("strategy2", mock_engine)
        registry.register("strategy3", mock_engine)

        assert len(registry._strategies) == 3
        assert registry.list_strategies() == ["strategy1", "strategy2", "strategy3"]

    def test_register_overwrites_existing_silently(self, registry):
        """Test that registering same ID overwrites previous (current behavior)."""

        class Engine1:
            def __call__(self, context):
                return "engine1"

        class Engine2:
            def __call__(self, context):
                return "engine2"

        engine1 = Engine1()
        engine2 = Engine2()

        registry.register("test", engine1)
        assert registry._strategies["test"] is engine1

        # Overwrite should happen silently
        registry.register("test", engine2)
        assert registry._strategies["test"] is engine2

    def test_get_strategy_success(self, registry, mock_engine):
        """Test retrieving existing strategy."""
        strategy_id = "test_strategy"
        registry.register(strategy_id, mock_engine)

        retrieved = registry.get_strategy(strategy_id)
        assert retrieved is mock_engine

    def test_get_strategy_not_found_raises_key_error(self, registry):
        """Test that getting non-existent strategy raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            registry.get_strategy("nonexistent")

        error_message = str(exc_info.value)
        assert "nonexistent" in error_message
        assert "not found" in error_message
        assert "Available strategies" in error_message

    def test_get_strategy_error_shows_available_strategies(self, registry, mock_engine):
        """Test that error message includes available strategies for debugging."""
        registry.register("strategy1", mock_engine)
        registry.register("strategy2", mock_engine)

        with pytest.raises(KeyError) as exc_info:
            registry.get_strategy("strategy3")

        error_message = str(exc_info.value)
        assert "strategy1" in error_message
        assert "strategy2" in error_message

    def test_list_strategies_empty(self, registry):
        """Test listing strategies when registry is empty."""
        assert registry.list_strategies() == []

    def test_list_strategies_returns_all_ids(self, registry, mock_engine):
        """Test that list_strategies returns all registered IDs."""
        registry.register("alpha", mock_engine)
        registry.register("beta", mock_engine)
        registry.register("gamma", mock_engine)

        strategies = registry.list_strategies()
        assert sorted(strategies) == ["alpha", "beta", "gamma"]

    def test_list_strategies_returns_copy(self, registry, mock_engine):
        """Test that list_strategies returns a copy, not direct reference."""
        registry.register("test", mock_engine)

        strategies1 = registry.list_strategies()
        strategies2 = registry.list_strategies()

        # Should be equal but not the same object
        assert strategies1 == strategies2
        assert strategies1 is not strategies2

        # Modifying returned list should not affect registry
        strategies1.append("fake_strategy")
        assert "fake_strategy" not in registry.list_strategies()


@pytest.mark.unit
class TestModuleLevelFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture(autouse=True)
    def clear_global_registry(self):
        """Clear global registry before and after each test."""
        # Import the global registry
        from the_alchemiser.strategy_v2.core import registry as registry_module

        # Clear before test
        registry_module._registry = StrategyRegistry()

        yield

        # Clear after test
        registry_module._registry = StrategyRegistry()

    @pytest.fixture
    def mock_engine(self):
        """Create a mock strategy engine."""

        class MockEngine:
            def __call__(
                self,
                context: datetime | MarketDataPort | dict[str, datetime | MarketDataPort],
            ) -> StrategyAllocation:
                from decimal import Decimal

                from the_alchemiser.shared.schemas.strategy_allocation import (
                    StrategyAllocation,
                )

                return StrategyAllocation(
                    target_weights={"SPY": Decimal("1.0")},
                    correlation_id="test-corr-id",
                )

        return MockEngine()

    def test_register_strategy_global_function(self, mock_engine):
        """Test module-level register_strategy function."""
        register_strategy("test_strategy", mock_engine)

        # Verify it's in global registry
        strategies = list_strategies()
        assert "test_strategy" in strategies

    def test_get_strategy_global_function(self, mock_engine):
        """Test module-level get_strategy function."""
        register_strategy("test_strategy", mock_engine)

        retrieved = get_strategy("test_strategy")
        assert retrieved is mock_engine

    def test_get_strategy_not_found_global(self):
        """Test module-level get_strategy raises KeyError for missing strategy."""
        with pytest.raises(KeyError) as exc_info:
            get_strategy("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_list_strategies_global_function(self, mock_engine):
        """Test module-level list_strategies function."""
        register_strategy("strategy1", mock_engine)
        register_strategy("strategy2", mock_engine)

        strategies = list_strategies()
        assert sorted(strategies) == ["strategy1", "strategy2"]

    def test_list_strategies_empty_global(self):
        """Test list_strategies on empty global registry."""
        strategies = list_strategies()
        assert strategies == []


@pytest.mark.unit
class TestStrategyEngineProtocol:
    """Test StrategyEngine protocol compliance."""

    def test_callable_with_datetime_context(self):
        """Test that engine can be called with datetime context."""

        class SimpleEngine:
            def __call__(self, context: datetime) -> StrategyAllocation:
                from decimal import Decimal

                from the_alchemiser.shared.schemas.strategy_allocation import (
                    StrategyAllocation,
                )

                return StrategyAllocation(
                    target_weights={"SPY": Decimal("1.0")},
                    correlation_id="test",
                )

        engine = SimpleEngine()
        assert isinstance(engine, StrategyEngine)

    def test_callable_with_market_data_port(self):
        """Test that engine can be called with MarketDataPort."""

        class MarketDataEngine:
            def __call__(self, context: MarketDataPort) -> StrategyAllocation:
                from decimal import Decimal

                from the_alchemiser.shared.schemas.strategy_allocation import (
                    StrategyAllocation,
                )

                return StrategyAllocation(
                    target_weights={"SPY": Decimal("1.0")},
                    correlation_id="test",
                )

        # Note: This test verifies protocol structure, actual MarketDataPort
        # would be injected at runtime
        engine = MarketDataEngine()
        # Protocol check - should not raise
        assert hasattr(engine, "__call__")


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance for each test."""
        return StrategyRegistry()

    @pytest.fixture
    def mock_engine(self):
        """Create a mock strategy engine."""

        class MockEngine:
            def __call__(self, context):
                return None

        return MockEngine()

    def test_register_empty_strategy_id(self, registry, mock_engine):
        """Test registering with empty string ID (current behavior allows it)."""
        # Current implementation allows empty string
        # This test documents current behavior - may want to add validation later
        registry.register("", mock_engine)
        assert "" in registry._strategies

    def test_register_whitespace_only_id(self, registry, mock_engine):
        """Test registering with whitespace-only ID."""
        # Current implementation allows whitespace
        registry.register("   ", mock_engine)
        assert "   " in registry._strategies

    def test_register_special_characters_in_id(self, registry, mock_engine):
        """Test registering with special characters in ID."""
        special_ids = ["test-strategy", "test_strategy", "test.strategy", "test@123"]
        for strategy_id in special_ids:
            registry.register(strategy_id, mock_engine)
            assert strategy_id in registry._strategies

    def test_get_strategy_with_empty_registry_shows_empty_list(self, registry):
        """Test error message when registry is empty."""
        with pytest.raises(KeyError) as exc_info:
            registry.get_strategy("any_strategy")

        error_message = str(exc_info.value)
        assert "[]" in error_message  # Empty list of available strategies

    def test_registry_preserves_insertion_order(self, registry, mock_engine):
        """Test that registry preserves insertion order (dict guarantee in Python 3.7+)."""
        order = ["zebra", "alpha", "beta", "gamma"]
        for strategy_id in order:
            registry.register(strategy_id, mock_engine)

        # In Python 3.7+, dict preserves insertion order
        assert registry.list_strategies() == order


@pytest.mark.unit
class TestConcurrencyConsiderations:
    """Test considerations for concurrent access (documents current behavior)."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance for each test."""
        return StrategyRegistry()

    def test_sequential_access_works(self, registry):
        """Test that sequential access works correctly."""

        class Engine1:
            def __call__(self, context):
                return "result1"

        class Engine2:
            def __call__(self, context):
                return "result2"

        engine1 = Engine1()
        engine2 = Engine2()

        registry.register("strategy1", engine1)
        registry.register("strategy2", engine2)

        assert registry.get_strategy("strategy1") is engine1
        assert registry.get_strategy("strategy2") is engine2

    def test_registry_is_mutable(self, registry):
        """Test that registry state can be modified (documents current behavior)."""

        class MockEngine:
            def __call__(self, context):
                return None

        engine = MockEngine()

        # Initial state
        assert len(registry.list_strategies()) == 0

        # Mutate
        registry.register("test", engine)
        assert len(registry.list_strategies()) == 1

        # Can continue to mutate
        registry.register("test2", engine)
        assert len(registry.list_strategies()) == 2

        # Note: This test documents that registry is mutable and not thread-safe
        # without external synchronization
