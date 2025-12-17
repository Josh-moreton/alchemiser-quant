"""Business Unit: strategy | Status: current.

Test strategy_v2 module imports and public API.

Tests that the module's public API exports work correctly.
"""

from __future__ import annotations

import pytest

from the_alchemiser import strategy_v2
from the_alchemiser.strategy_v2 import (
    SingleStrategyOrchestrator,
    StrategyContext,
    get_strategy,
    list_strategies,
    register_strategy,
)


class TestStrategyV2ModuleImports:
    """Test strategy_v2 module imports and exports."""

    def test_import_single_strategy_orchestrator(self) -> None:
        """Test importing SingleStrategyOrchestrator from module."""
        assert SingleStrategyOrchestrator is not None
        assert hasattr(SingleStrategyOrchestrator, "__init__")

    def test_import_strategy_context(self) -> None:
        """Test importing StrategyContext from module."""
        assert StrategyContext is not None
        # StrategyContext is a dataclass, not a regular class
        assert hasattr(StrategyContext, "__dataclass_fields__")

    def test_import_registry_functions(self) -> None:
        """Test importing registry functions from module."""
        assert get_strategy is not None
        assert callable(get_strategy)
        assert list_strategies is not None
        assert callable(list_strategies)
        assert register_strategy is not None
        assert callable(register_strategy)

    def test_getattr_single_strategy_orchestrator(self) -> None:
        """Test __getattr__ for SingleStrategyOrchestrator."""
        orchestrator_class = strategy_v2.SingleStrategyOrchestrator
        assert orchestrator_class is not None

    def test_getattr_strategy_context(self) -> None:
        """Test __getattr__ for StrategyContext."""
        context_class = strategy_v2.StrategyContext
        assert context_class is not None

    def test_getattr_get_strategy(self) -> None:
        """Test __getattr__ for get_strategy."""
        func = strategy_v2.get_strategy
        assert func is not None
        assert callable(func)

    def test_getattr_list_strategies(self) -> None:
        """Test __getattr__ for list_strategies."""
        func = strategy_v2.list_strategies
        assert func is not None
        assert callable(func)

    def test_getattr_register_strategy(self) -> None:
        """Test __getattr__ for register_strategy."""
        func = strategy_v2.register_strategy
        assert func is not None
        assert callable(func)

    def test_getattr_invalid_attribute(self) -> None:
        """Test __getattr__ raises AttributeError for invalid attributes."""
        with pytest.raises(AttributeError) as exc_info:
            _ = strategy_v2.NonExistentAttribute

        assert "has no attribute" in str(exc_info.value)
        assert "NonExistentAttribute" in str(exc_info.value)
        # Verify improved error message includes available attributes
        assert "Available attributes:" in str(exc_info.value)

    def test_all_exports_defined(self) -> None:
        """Test that __all__ is defined and contains expected exports."""
        assert hasattr(strategy_v2, "__all__")
        expected_exports = {
            "SingleStrategyOrchestrator",
            "StrategyContext",
            "get_strategy",
            "list_strategies",
            "register_strategy",
        }
        actual_exports = set(strategy_v2.__all__)
        assert actual_exports == expected_exports

    def test_version_defined(self) -> None:
        """Test that module version is defined."""
        assert hasattr(strategy_v2, "__version__")
        assert isinstance(strategy_v2.__version__, str)
        # Verify semantic versioning format (basic check)
        parts = strategy_v2.__version__.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_module_docstring_present(self) -> None:
        """Test that module has proper docstring with business unit identifier."""
        assert strategy_v2.__doc__ is not None
        assert len(strategy_v2.__doc__) > 0
        assert "Business Unit: strategy" in strategy_v2.__doc__
        assert "Status: current" in strategy_v2.__doc__
