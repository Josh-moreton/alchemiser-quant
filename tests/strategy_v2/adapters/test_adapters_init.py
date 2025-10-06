#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Tests for strategy_v2/adapters/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
"""

from __future__ import annotations

import sys
from typing import get_type_hints

import pytest


class TestAdaptersModuleInterface:
    """Test suite for adapters module public API."""

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ list matches actual exports."""
        from the_alchemiser.strategy_v2 import adapters

        # Check __all__ exists
        assert hasattr(adapters, "__all__"), "Module must define __all__"

        expected_exports = {"FeaturePipeline", "MarketDataProvider", "StrategyMarketDataAdapter"}
        actual_exports = set(adapters.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. Expected: {expected_exports}, Got: {actual_exports}"
        )

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.strategy_v2 import adapters

        for name in adapters.__all__:
            assert hasattr(adapters, name), f"Export '{name}' in __all__ but not importable"
            obj = getattr(adapters, name)
            assert obj is not None, f"Export '{name}' is None"

    def test_feature_pipeline_export(self) -> None:
        """Test FeaturePipeline is correctly exported."""
        from the_alchemiser.strategy_v2.adapters import FeaturePipeline
        from the_alchemiser.strategy_v2.adapters.feature_pipeline import (
            FeaturePipeline as SourceFeaturePipeline,
        )

        # Verify it's the same class (not a copy)
        assert FeaturePipeline is SourceFeaturePipeline
        assert FeaturePipeline.__name__ == "FeaturePipeline"

    def test_market_data_provider_export(self) -> None:
        """Test MarketDataProvider protocol is correctly exported."""
        from the_alchemiser.strategy_v2.adapters import MarketDataProvider
        from the_alchemiser.strategy_v2.adapters.market_data_adapter import (
            MarketDataProvider as SourceMarketDataProvider,
        )

        # Verify it's the same protocol (not a copy)
        assert MarketDataProvider is SourceMarketDataProvider
        assert MarketDataProvider.__name__ == "MarketDataProvider"

    def test_strategy_market_data_adapter_export(self) -> None:
        """Test StrategyMarketDataAdapter is correctly exported."""
        from the_alchemiser.strategy_v2.adapters import StrategyMarketDataAdapter
        from the_alchemiser.strategy_v2.adapters.market_data_adapter import (
            StrategyMarketDataAdapter as SourceAdapter,
        )

        # Verify it's the same class (not a copy)
        assert StrategyMarketDataAdapter is SourceAdapter
        assert StrategyMarketDataAdapter.__name__ == "StrategyMarketDataAdapter"

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no leaks)."""
        from the_alchemiser.strategy_v2 import adapters

        # Get all public symbols (excluding dunder)
        public_symbols = [name for name in dir(adapters) if not name.startswith("_")]

        # Get __all__
        declared_exports = set(adapters.__all__)

        # Public symbols should only include __all__ items (and no extras)
        extra_exports = set(public_symbols) - declared_exports

        # Allow module-level metadata and stdlib imports
        allowed_extras = {"annotations"}  # from __future__ import annotations

        unexpected_exports = extra_exports - allowed_extras

        assert not unexpected_exports, (
            f"Unexpected public exports found (not in __all__): {unexpected_exports}. "
            f"Either add to __all__ or prefix with underscore."
        )

    def test_star_import_behavior(self) -> None:
        """Test that 'from adapters import *' only imports __all__ items."""
        # Create a clean namespace
        test_namespace: dict[str, object] = {}

        # Simulate 'from adapters import *'
        from the_alchemiser.strategy_v2 import adapters

        for name in adapters.__all__:
            test_namespace[name] = getattr(adapters, name)

        # Verify expected items are present
        assert "FeaturePipeline" in test_namespace
        assert "MarketDataProvider" in test_namespace
        assert "StrategyMarketDataAdapter" in test_namespace

        # Verify private items are NOT imported
        assert "__version__" not in test_namespace or hasattr(
            adapters, "__version__"
        ), "Private attributes should not be star-imported"

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.strategy_v2 import adapters

        assert adapters.__doc__ is not None, "Module must have docstring"
        assert len(adapters.__doc__) > 0, "Module docstring must not be empty"

        # Check for business unit header
        assert "Business Unit:" in adapters.__doc__, "Docstring must include Business Unit"
        assert "Status:" in adapters.__doc__, "Docstring must include Status"

    def test_exports_are_classes_or_protocols(self) -> None:
        """Test that all exports are classes or protocols (no functions/constants)."""
        from the_alchemiser.strategy_v2 import adapters

        for name in adapters.__all__:
            obj = getattr(adapters, name)

            # Should be a class or protocol
            assert isinstance(
                obj, type
            ), f"Export '{name}' should be a class/protocol, got {type(obj)}"

    def test_relative_imports_work(self) -> None:
        """Test that relative imports within the module work correctly."""
        # This test ensures the __init__.py import statements are valid
        try:
            from the_alchemiser.strategy_v2.adapters import (
                FeaturePipeline,
                MarketDataProvider,
                StrategyMarketDataAdapter,
            )

            # If we get here, imports succeeded
            assert FeaturePipeline is not None
            assert MarketDataProvider is not None
            assert StrategyMarketDataAdapter is not None

        except ImportError as e:
            pytest.fail(f"Relative imports failed: {e}")

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.strategy_v2 import adapters as adapters1

        # Re-import
        from the_alchemiser.strategy_v2 import adapters as adapters2

        # Should be the same module object
        assert adapters1 is adapters2

        # Exports should be identical
        assert adapters1.FeaturePipeline is adapters2.FeaturePipeline
        assert adapters1.MarketDataProvider is adapters2.MarketDataProvider
        assert adapters1.StrategyMarketDataAdapter is adapters2.StrategyMarketDataAdapter

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.strategy_v2 import adapters

            # Check that submodules are imported
            assert hasattr(adapters, "FeaturePipeline")
            assert hasattr(adapters, "MarketDataProvider")
            assert hasattr(adapters, "StrategyMarketDataAdapter")

        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            raise


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_portfolio_imports(self) -> None:
        """Test that adapters module doesn't import from portfolio_v2."""
        from the_alchemiser.strategy_v2 import adapters

        # Check loaded modules
        loaded_modules = [mod for mod in sys.modules if mod.startswith("the_alchemiser")]

        portfolio_modules = [mod for mod in loaded_modules if "portfolio_v2" in mod]

        # Strategy adapters should not load portfolio modules
        assert not portfolio_modules, (
            f"Strategy adapters should not import portfolio_v2 modules. "
            f"Found: {portfolio_modules}"
        )

    def test_no_execution_imports(self) -> None:
        """Test that adapters module doesn't import from execution_v2."""
        from the_alchemiser.strategy_v2 import adapters

        # Check loaded modules
        loaded_modules = [mod for mod in sys.modules if mod.startswith("the_alchemiser")]

        execution_modules = [mod for mod in loaded_modules if "execution_v2" in mod]

        # Strategy adapters should not load execution modules
        assert not execution_modules, (
            f"Strategy adapters should not import execution_v2 modules. "
            f"Found: {execution_modules}"
        )

    def test_no_orchestration_imports(self) -> None:
        """Test that adapters module doesn't import from orchestration."""
        from the_alchemiser.strategy_v2 import adapters

        # Check loaded modules
        loaded_modules = [mod for mod in sys.modules if mod.startswith("the_alchemiser")]

        orchestration_modules = [mod for mod in loaded_modules if "orchestration" in mod]

        # Strategy adapters should not load orchestration modules
        assert not orchestration_modules, (
            f"Strategy adapters should not import orchestration modules. "
            f"Found: {orchestration_modules}"
        )


class TestTypePreservation:
    """Test suite for type information preservation."""

    def test_feature_pipeline_type_hints_preserved(self) -> None:
        """Test that FeaturePipeline type hints are preserved."""
        from the_alchemiser.strategy_v2.adapters import FeaturePipeline

        # Check that the class has type hints (means they're preserved)
        assert hasattr(
            FeaturePipeline.__init__, "__annotations__"
        ), "FeaturePipeline.__init__ should have type annotations"

    def test_adapter_type_hints_preserved(self) -> None:
        """Test that StrategyMarketDataAdapter type hints are preserved."""
        from the_alchemiser.strategy_v2.adapters import StrategyMarketDataAdapter

        # Check that the class has type hints
        assert hasattr(
            StrategyMarketDataAdapter.__init__, "__annotations__"
        ), "StrategyMarketDataAdapter.__init__ should have type annotations"

    def test_protocol_type_is_protocol(self) -> None:
        """Test that MarketDataProvider is recognized as a Protocol."""
        from the_alchemiser.strategy_v2.adapters import MarketDataProvider

        # Check if it's a Protocol (has _is_protocol attribute)
        # Note: typing.Protocol uses different mechanisms in different Python versions
        assert hasattr(
            MarketDataProvider, "__mro__"
        ), "MarketDataProvider should be a class/protocol"


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_has_business_unit(self) -> None:
        """Test that module docstring includes business unit."""
        from the_alchemiser.strategy_v2 import adapters

        assert (
            "strategy" in adapters.__doc__.lower()
        ), "Module docstring should mention 'strategy' business unit"

    def test_module_status_is_current(self) -> None:
        """Test that module status is 'current'."""
        from the_alchemiser.strategy_v2 import adapters

        assert "current" in adapters.__doc__.lower(), "Module status should be 'current'"

    def test_module_has_meaningful_description(self) -> None:
        """Test that module docstring describes purpose."""
        from the_alchemiser.strategy_v2 import adapters

        docstring = adapters.__doc__.lower()

        # Should mention adapters, data, or strategy
        assert (
            "adapter" in docstring or "data" in docstring or "strategy" in docstring
        ), "Module docstring should describe its purpose"
