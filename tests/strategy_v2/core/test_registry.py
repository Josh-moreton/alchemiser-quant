"""Business Unit: strategy | Status: current

Comprehensive tests for strategy registry module.

Tests cover basic functionality, error handling, thread safety,
and edge cases for the strategy registry system.
"""

from __future__ import annotations

import threading
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.strategy_v2.core.registry import (
    StrategyEngine,
    StrategyRegistry,
    get_strategy,
    list_strategies,
    register_strategy,
)
from the_alchemiser.strategy_v2.errors import StrategyRegistryError


class TestStrategyRegistry:
    """Test StrategyRegistry class."""

    @pytest.fixture
    def registry(self) -> StrategyRegistry:
        """Create a fresh registry instance for each test."""
        return StrategyRegistry()

    @pytest.fixture
    def mock_engine(self) -> Mock:
        """Create a mock strategy engine."""
        engine = Mock(spec=StrategyEngine)
        engine.return_value = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="test-123",
        )
        return engine

    def test_register_and_get_strategy(self, registry: StrategyRegistry, mock_engine: Mock) -> None:
        """Test basic register and retrieve functionality."""
        strategy_id = "test-strategy"
        registry.register(strategy_id, mock_engine)
        
        retrieved = registry.get_strategy(strategy_id)
        assert retrieved is mock_engine

    def test_list_strategies_empty(self, registry: StrategyRegistry) -> None:
        """Test listing strategies when registry is empty."""
        strategies = registry.list_strategies()
        assert strategies == []

    def test_list_strategies_multiple(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test listing multiple registered strategies."""
        strategy_ids = ["strategy1", "strategy2", "strategy3"]
        
        for strategy_id in strategy_ids:
            registry.register(strategy_id, mock_engine)
        
        strategies = registry.list_strategies()
        assert len(strategies) == 3
        assert set(strategies) == set(strategy_ids)

    def test_get_strategy_not_found(self, registry: StrategyRegistry) -> None:
        """Test getting a non-existent strategy raises StrategyRegistryError."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.get_strategy("non-existent")
        
        assert "not found" in str(exc_info.value)
        assert "non-existent" in str(exc_info.value)

    def test_register_empty_strategy_id(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test registering with empty strategy_id raises error."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.register("", mock_engine)
        
        assert "empty" in str(exc_info.value).lower()

    def test_register_whitespace_only_strategy_id(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test registering with whitespace-only strategy_id raises error."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.register("   ", mock_engine)
        
        assert "empty" in str(exc_info.value).lower()

    def test_register_none_strategy_id(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test registering with None strategy_id raises error."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.register(None, mock_engine)  # type: ignore
        
        assert "non-empty string" in str(exc_info.value).lower()

    def test_register_too_long_strategy_id(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test registering with strategy_id exceeding max length raises error."""
        long_id = "a" * 101
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.register(long_id, mock_engine)
        
        assert "exceeds maximum length" in str(exc_info.value).lower()
        assert "100" in str(exc_info.value)

    def test_register_non_callable_engine(self, registry: StrategyRegistry) -> None:
        """Test registering non-callable engine raises error."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            registry.register("test", "not-callable")  # type: ignore
        
        assert "callable" in str(exc_info.value).lower()

    def test_register_overwrite_existing(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test that registering same strategy_id overwrites previous engine."""
        strategy_id = "test-strategy"
        engine1 = Mock(spec=StrategyEngine)
        engine2 = Mock(spec=StrategyEngine)
        
        registry.register(strategy_id, engine1)
        registry.register(strategy_id, engine2)
        
        retrieved = registry.get_strategy(strategy_id)
        assert retrieved is engine2
        assert retrieved is not engine1

    def test_strategy_id_whitespace_trimmed(
        self, registry: StrategyRegistry, mock_engine: Mock
    ) -> None:
        """Test that strategy_id is trimmed of leading/trailing whitespace."""
        registry.register("  test-strategy  ", mock_engine)
        
        # Should be retrievable with trimmed ID
        retrieved = registry.get_strategy("test-strategy")
        assert retrieved is mock_engine


class TestGlobalRegistryFunctions:
    """Test module-level registry functions."""

    def setup_method(self) -> None:
        """Clear the global registry before each test."""
        # Access the global registry's internal dict to clear it
        from the_alchemiser.strategy_v2.core.registry import _registry
        
        with _registry._lock:
            _registry._strategies.clear()

    def test_register_and_get_global(self) -> None:
        """Test register_strategy and get_strategy functions."""
        engine = Mock(spec=StrategyEngine)
        strategy_id = "global-test"
        
        register_strategy(strategy_id, engine)
        retrieved = get_strategy(strategy_id)
        
        assert retrieved is engine

    def test_list_strategies_global(self) -> None:
        """Test list_strategies function."""
        engine = Mock(spec=StrategyEngine)
        
        register_strategy("strategy1", engine)
        register_strategy("strategy2", engine)
        
        strategies = list_strategies()
        assert len(strategies) == 2
        assert "strategy1" in strategies
        assert "strategy2" in strategies

    def test_get_strategy_not_found_global(self) -> None:
        """Test get_strategy raises StrategyRegistryError for non-existent strategy."""
        with pytest.raises(StrategyRegistryError) as exc_info:
            get_strategy("non-existent")
        
        assert "not found" in str(exc_info.value)


class TestThreadSafety:
    """Test thread safety of registry operations."""

    def setup_method(self) -> None:
        """Clear the global registry before each test."""
        from the_alchemiser.strategy_v2.core.registry import _registry
        
        with _registry._lock:
            _registry._strategies.clear()

    def test_concurrent_registrations(self) -> None:
        """Test concurrent strategy registrations don't cause race conditions."""
        num_threads = 10
        engine = Mock(spec=StrategyEngine)
        
        def register_strategy_thread(thread_id: int) -> None:
            strategy_id = f"strategy-{thread_id}"
            register_strategy(strategy_id, engine)
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=register_strategy_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        strategies = list_strategies()
        assert len(strategies) == num_threads

    def test_concurrent_reads(self) -> None:
        """Test concurrent strategy reads are safe."""
        engine = Mock(spec=StrategyEngine)
        register_strategy("test-strategy", engine)
        
        num_threads = 20
        results: list[Mock | None] = [None] * num_threads
        
        def read_strategy_thread(thread_id: int) -> None:
            results[thread_id] = get_strategy("test-strategy")
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=read_strategy_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should have retrieved the same engine
        assert all(result is engine for result in results)

    def test_concurrent_mixed_operations(self) -> None:
        """Test mixed concurrent reads and writes are safe."""
        engine = Mock(spec=StrategyEngine)
        register_strategy("existing-strategy", engine)
        
        num_threads = 30
        errors: list[Exception | None] = [None] * num_threads
        
        def mixed_operations_thread(thread_id: int) -> None:
            try:
                if thread_id % 3 == 0:
                    register_strategy(f"new-strategy-{thread_id}", engine)
                elif thread_id % 3 == 1:
                    get_strategy("existing-strategy")
                else:
                    list_strategies()
            except Exception as e:
                errors[thread_id] = e
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=mixed_operations_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No exceptions should have occurred
        assert all(error is None for error in errors)
        
        # At least the existing strategy plus some new ones should be registered
        strategies = list_strategies()
        assert len(strategies) >= 1
        assert "existing-strategy" in strategies


class TestPropertyBased:
    """Property-based tests using Hypothesis."""

    def setup_method(self) -> None:
        """Clear the global registry before each test."""
        from the_alchemiser.strategy_v2.core.registry import _registry
        
        with _registry._lock:
            _registry._strategies.clear()

    @given(
        strategy_id=st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
            min_size=1,
            max_size=100,
        ).filter(lambda s: s.strip())
    )
    def test_register_and_retrieve_arbitrary_ids(self, strategy_id: str) -> None:
        """Test that any valid strategy_id can be registered and retrieved."""
        engine = Mock(spec=StrategyEngine)
        
        register_strategy(strategy_id, engine)
        retrieved = get_strategy(strategy_id.strip())
        
        assert retrieved is engine

    @given(
        strategy_id=st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
            min_size=1,
            max_size=100,
        ).filter(lambda s: s.strip())
    )
    def test_strategy_in_list_after_registration(self, strategy_id: str) -> None:
        """Test that registered strategy appears in list_strategies()."""
        engine = Mock(spec=StrategyEngine)
        
        register_strategy(strategy_id, engine)
        strategies = list_strategies()
        
        assert strategy_id.strip() in strategies


class TestStrategyEngineProtocol:
    """Test StrategyEngine protocol behavior."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test that StrategyEngine protocol is runtime checkable."""
        from typing import runtime_checkable
        
        # Verify the decorator is applied
        assert hasattr(StrategyEngine, "__runtime_checkable__")

    def test_callable_satisfies_protocol(self) -> None:
        """Test that a callable satisfies basic protocol check."""
        def mock_strategy(context: datetime) -> StrategyAllocation:
            return StrategyAllocation(
                target_weights={"AAPL": Decimal("1.0")},
                correlation_id="test",
            )
        
        # Should be callable
        assert callable(mock_strategy)

    def test_protocol_signature_documented(self) -> None:
        """Test that StrategyEngine protocol has proper documentation."""
        assert StrategyEngine.__doc__ is not None
        assert "Protocol" in StrategyEngine.__doc__
