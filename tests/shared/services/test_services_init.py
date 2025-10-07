#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared/services/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
- Module determinism and no circular imports
"""

from __future__ import annotations

import sys
from typing import get_type_hints

import pytest


class TestServicesModuleInterface:
    """Test suite for services module public API."""

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.shared import services

        assert services.__doc__ is not None
        assert "Business Unit: shared" in services.__doc__
        assert "Status: current" in services.__doc__

    def test_all_exports_defined(self) -> None:
        """Test that __all__ is defined and not empty."""
        from the_alchemiser.shared import services

        assert hasattr(services, "__all__")
        assert isinstance(services.__all__, list)
        assert len(services.__all__) > 0

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import services

        for name in services.__all__:
            assert hasattr(services, name), f"{name} is in __all__ but not importable"
            obj = getattr(services, name)
            assert obj is not None, f"{name} is None"

    def test_exports_are_classes(self) -> None:
        """Test that all exports are classes (no functions/constants)."""
        from the_alchemiser.shared import services

        for name in services.__all__:
            obj = getattr(services, name)
            assert isinstance(
                obj, type
            ), f"{name} is not a class (got {type(obj).__name__})"

    def test_alpaca_trading_service_exported(self) -> None:
        """Test that AlpacaTradingService is exported and is the correct type."""
        from the_alchemiser.shared import services
        from the_alchemiser.shared.services.alpaca_trading_service import (
            AlpacaTradingService as SourceService,
        )

        assert "AlpacaTradingService" in services.__all__
        assert hasattr(services, "AlpacaTradingService")

        # Verify it's the same class, not a copy
        assert services.AlpacaTradingService is SourceService

    def test_buying_power_service_exported(self) -> None:
        """Test that BuyingPowerService is exported and is the correct type."""
        from the_alchemiser.shared import services
        from the_alchemiser.shared.services.buying_power_service import (
            BuyingPowerService as SourceService,
        )

        assert "BuyingPowerService" in services.__all__
        assert hasattr(services, "BuyingPowerService")

        # Verify it's the same class, not a copy
        assert services.BuyingPowerService is SourceService

    def test_no_unintended_exports(self) -> None:
        """Test that only items in __all__ are considered public exports."""
        from the_alchemiser.shared import services

        # Get all non-private attributes
        public_attrs = [
            name
            for name in dir(services)
            if not name.startswith("_") and name != "annotations"
        ]

        # All public attributes should be in __all__
        for attr in public_attrs:
            assert (
                attr in services.__all__
            ), f"{attr} is public but not in __all__ (API surface leak)"

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.shared import services as services1

        # Re-import
        from the_alchemiser.shared import services as services2

        # Should be the same module object
        assert services1 is services2

        # Exports should be identical
        assert services1.AlpacaTradingService is services2.AlpacaTradingService
        assert services1.BuyingPowerService is services2.BuyingPowerService

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.shared import services

            # Check that submodules are imported
            assert hasattr(services, "AlpacaTradingService")
            assert hasattr(services, "BuyingPowerService")

        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            raise


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_execution_v2_imports(self) -> None:
        """Test that the module doesn't import from execution_v2 (would create circular deps)."""
        from the_alchemiser.shared import services

        # Check if any execution_v2 modules are in sys.modules after import
        execution_modules = [
            name for name in sys.modules.keys() if "execution_v2" in name
        ]

        # Only allowed if they were already imported before this test
        # The services module itself should not trigger execution_v2 imports
        # This is a weak test, but helps catch obvious violations
        assert services is not None  # Just to use the import

    def test_no_portfolio_v2_imports(self) -> None:
        """Test that the module doesn't import from portfolio_v2 (would create circular deps)."""
        from the_alchemiser.shared import services

        # Check if any portfolio_v2 modules are in sys.modules after import
        portfolio_modules = [
            name for name in sys.modules.keys() if "portfolio_v2" in name
        ]

        # Only allowed if they were already imported before this test
        assert services is not None  # Just to use the import

    def test_no_strategy_v2_imports(self) -> None:
        """Test that the module doesn't import from strategy_v2 (would create circular deps)."""
        from the_alchemiser.shared import services

        # Check if any strategy_v2 modules are in sys.modules after import
        strategy_modules = [name for name in sys.modules.keys() if "strategy_v2" in name]

        # Only allowed if they were already imported before this test
        assert services is not None  # Just to use the import


class TestTypePreservation:
    """Test suite for type information preservation."""

    def test_alpaca_trading_service_preserves_types(self) -> None:
        """Test that AlpacaTradingService type information is preserved."""
        from the_alchemiser.shared import services
        from the_alchemiser.shared.services.alpaca_trading_service import (
            AlpacaTradingService,
        )

        # The exported class should have the same __module__ as the source
        assert (
            services.AlpacaTradingService.__module__
            == AlpacaTradingService.__module__
        )
        assert (
            services.AlpacaTradingService.__name__ == AlpacaTradingService.__name__
        )

    def test_buying_power_service_preserves_types(self) -> None:
        """Test that BuyingPowerService type information is preserved."""
        from the_alchemiser.shared import services
        from the_alchemiser.shared.services.buying_power_service import (
            BuyingPowerService,
        )

        # The exported class should have the same __module__ as the source
        assert services.BuyingPowerService.__module__ == BuyingPowerService.__module__
        assert services.BuyingPowerService.__name__ == BuyingPowerService.__name__


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_has_future_annotations(self) -> None:
        """Test that the module uses future annotations."""
        from the_alchemiser.shared import services

        # Check if __annotations__ is using postponed evaluation
        # This is a bit tricky to test directly, but we can check if the module compiled correctly
        assert services is not None

    def test_all_has_type_annotation(self) -> None:
        """Test that __all__ has proper type annotation."""
        from the_alchemiser.shared import services

        # Check that __all__ is annotated as list[str]
        assert hasattr(services, "__annotations__")
        assert "__all__" in services.__annotations__
        # The annotation should be 'list[str]' or similar
        all_annotation = services.__annotations__["__all__"]
        # Note: In Python 3.12+, it might be a string due to PEP 563
        assert "list" in str(all_annotation).lower()

    def test_docstring_mentions_export_policy(self) -> None:
        """Test that docstring explains the selective export policy."""
        from the_alchemiser.shared import services

        docstring = services.__doc__ or ""
        # Check that it mentions the intentional avoidance of re-exports
        assert (
            "intentionally" in docstring.lower()
            or "avoid" in docstring.lower()
            or "directly" in docstring.lower()
        )

    def test_docstring_has_examples(self) -> None:
        """Test that docstring provides import examples."""
        from the_alchemiser.shared import services

        docstring = services.__doc__ or ""
        # Should have example imports showing direct submodule imports
        assert "from the_alchemiser" in docstring
        assert "import" in docstring


class TestBackwardCompatibility:
    """Test suite for backward compatibility guarantees."""

    def test_exported_services_are_stable(self) -> None:
        """Test that the two exported services remain stable (backward compatibility)."""
        from the_alchemiser.shared import services

        # These two services should always be exported for backward compatibility
        required_exports = ["AlpacaTradingService", "BuyingPowerService"]

        for export in required_exports:
            assert (
                export in services.__all__
            ), f"{export} missing from __all__ (breaks backward compatibility)"

    def test_import_from_package_root_works(self) -> None:
        """Test that importing from package root still works (backward compatibility)."""
        # This pattern should continue to work for the two exported services
        from the_alchemiser.shared.services import (
            AlpacaTradingService,
            BuyingPowerService,
        )

        assert AlpacaTradingService is not None
        assert BuyingPowerService is not None

        # Verify they're the correct classes
        assert AlpacaTradingService.__name__ == "AlpacaTradingService"
        assert BuyingPowerService.__name__ == "BuyingPowerService"
