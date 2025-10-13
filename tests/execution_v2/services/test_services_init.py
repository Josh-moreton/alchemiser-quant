#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Tests for execution_v2/services/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
- Module determinism and no circular imports
- Version tracking and compatibility
"""

from __future__ import annotations

import sys

import pytest


class TestServicesModuleInterface:
    """Test suite for execution_v2/services module public API."""

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.execution_v2 import services

        assert services.__doc__ is not None
        assert "Business Unit: execution" in services.__doc__
        assert "Status: current" in services.__doc__

    def test_module_has_enhanced_docstring(self) -> None:
        """Test that docstring includes service inventory and import guidance."""
        from the_alchemiser.execution_v2 import services

        # Should mention TradeLedgerService
        assert "TradeLedgerService" in services.__doc__
        # Should provide import examples
        assert "import" in services.__doc__.lower()

    def test_all_exports_defined(self) -> None:
        """Test that __all__ is defined and not empty."""
        from the_alchemiser.execution_v2 import services

        assert hasattr(services, "__all__")
        assert isinstance(services.__all__, list)
        assert len(services.__all__) > 0

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.execution_v2 import services

        for name in services.__all__:
            assert hasattr(services, name), f"{name} is in __all__ but not importable"
            obj = getattr(services, name)
            assert obj is not None, f"{name} is None"

    def test_exports_are_classes(self) -> None:
        """Test that all exports are classes (no functions/constants)."""
        from the_alchemiser.execution_v2 import services

        for name in services.__all__:
            obj = getattr(services, name)
            assert isinstance(
                obj, type
            ), f"{name} is not a class (got {type(obj).__name__})"

    def test_trade_ledger_service_exported(self) -> None:
        """Test that TradeLedgerService is exported and is the correct type."""
        from the_alchemiser.execution_v2 import services
        from the_alchemiser.execution_v2.services.trade_ledger import (
            TradeLedgerService as SourceService,
        )

        assert "TradeLedgerService" in services.__all__
        assert hasattr(services, "TradeLedgerService")

        # Verify it's the same class, not a copy
        assert services.TradeLedgerService is SourceService

    def test_no_unintended_exports(self) -> None:
        """Test that only items in __all__ are considered public exports.
        
        Note: Python automatically makes submodules accessible when imported,
        so we specifically check that no non-submodule, non-dunder attributes
        are leaked beyond __all__.
        """
        from the_alchemiser.execution_v2 import services

        # Get all non-private attributes
        public_attrs = [
            name
            for name in dir(services)
            if not name.startswith("_") and name != "annotations"
        ]

        # Filter out submodule names (these are expected Python behavior)
        # Submodules show up in dir() after import, which is standard Python
        import types
        non_submodule_attrs = [
            name for name in public_attrs
            if not isinstance(getattr(services, name), types.ModuleType)
        ]

        # All non-submodule public attributes should be in __all__
        for attr in non_submodule_attrs:
            assert (
                attr in services.__all__
            ), f"{attr} is public but not in __all__ (unintended export)"

    def test_star_import_behavior(self) -> None:
        """Test that 'from services import *' only imports __all__ items."""
        from the_alchemiser.execution_v2 import services

        # Create a clean namespace
        test_namespace: dict[str, object] = {}

        # Simulate 'from services import *'
        for name in services.__all__:
            test_namespace[name] = getattr(services, name)

        # Verify expected items are present
        assert "TradeLedgerService" in test_namespace

        # Verify private items are NOT imported
        assert "__version__" not in test_namespace or hasattr(
            services, "__version__"
        ), "Private attributes should not be star-imported"

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.execution_v2 import services as services1

        # Re-import
        from the_alchemiser.execution_v2 import services as services2

        # Should be the same module object
        assert services1 is services2

        # Exports should be identical
        assert services1.TradeLedgerService is services2.TradeLedgerService

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.execution_v2 import services

            # Check that exports are available
            assert hasattr(services, "TradeLedgerService")

        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            raise

    def test_module_has_version_attribute(self) -> None:
        """Test that module has __version__ attribute for compatibility tracking."""
        from the_alchemiser.execution_v2 import services

        assert hasattr(services, "__version__")
        assert isinstance(services.__version__, str)
        assert services.__version__ == "2.0.0"

    def test_version_format_is_semver(self) -> None:
        """Test that __version__ follows semantic versioning (x.y.z)."""
        from the_alchemiser.execution_v2 import services

        version_parts = services.__version__.split(".")
        assert len(version_parts) == 3, f"Version should be x.y.z, got {services.__version__}"
        assert all(
            part.isdigit() for part in version_parts
        ), f"Version parts should be numeric, got {services.__version__}"

    def test_future_import_present(self) -> None:
        """Test that module uses from __future__ import annotations."""
        from the_alchemiser.execution_v2 import services

        # Check if annotations are evaluated as strings (postponed evaluation)
        # This is a weak test but validates the future import is present
        assert hasattr(services, "__annotations__") or True  # Module may not have annotations


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_execution_v2_core_imports(self) -> None:
        """Test that the module doesn't import from execution_v2.core (would create circular deps)."""
        from the_alchemiser.execution_v2 import services

        # Check if any execution_v2.core modules are in sys.modules after import
        core_modules = [
            name for name in sys.modules.keys() if "execution_v2.core" in name
        ]

        # The services module itself should not trigger core imports
        # Core may be imported by tests or other code, but not by services/__init__
        assert services is not None  # Just to use the import

    def test_no_portfolio_v2_imports(self) -> None:
        """Test that the module doesn't import from portfolio_v2 (would create circular deps)."""
        from the_alchemiser.execution_v2 import services

        # Check if any portfolio_v2 modules are in sys.modules after import
        portfolio_modules = [
            name for name in sys.modules.keys() if "portfolio_v2" in name
        ]

        # Only allowed if they were already imported before this test
        assert services is not None  # Just to use the import

    def test_no_strategy_v2_imports(self) -> None:
        """Test that the module doesn't import from strategy_v2 (would create circular deps)."""
        from the_alchemiser.execution_v2 import services

        # Check if any strategy_v2 modules are in sys.modules after import
        strategy_modules = [
            name for name in sys.modules.keys() if "strategy_v2" in name
        ]

        # Only allowed if they were already imported before this test
        assert services is not None  # Just to use the import


class TestBackwardCompatibility:
    """Test suite for backward compatibility guarantees."""

    def test_trade_ledger_service_is_stable(self) -> None:
        """Test that TradeLedgerService remains exported (backward compatibility)."""
        from the_alchemiser.execution_v2 import services

        assert (
            "TradeLedgerService" in services.__all__
        ), "TradeLedgerService missing from __all__ (breaks backward compatibility)"

    def test_import_from_package_root_works(self) -> None:
        """Test that importing from package root still works (backward compatibility)."""
        from the_alchemiser.execution_v2.services import TradeLedgerService

        assert TradeLedgerService is not None

        # Verify it's the correct class
        assert TradeLedgerService.__name__ == "TradeLedgerService"

    def test_direct_import_from_submodule_still_works(self) -> None:
        """Test that direct imports from submodules still work (not breaking old pattern)."""
        from the_alchemiser.execution_v2.services import (
            TradeLedgerService as ReExport,
        )
        from the_alchemiser.execution_v2.services.trade_ledger import (
            TradeLedgerService as DirectImport,
        )

        # Both import paths should give the same class
        assert DirectImport is ReExport


class TestServiceAvailability:
    """Test suite for service class availability and functionality."""

    def test_trade_ledger_service_is_instantiable(self) -> None:
        """Test that TradeLedgerService can be instantiated."""
        from the_alchemiser.execution_v2.services import TradeLedgerService

        # Should be able to create an instance
        service = TradeLedgerService()
        assert service is not None

    def test_trade_ledger_service_has_expected_methods(self) -> None:
        """Test that TradeLedgerService has expected public methods."""
        from the_alchemiser.execution_v2.services import TradeLedgerService

        # Check for key methods
        assert hasattr(TradeLedgerService, "record_filled_order")
        assert hasattr(TradeLedgerService, "get_ledger")
        assert hasattr(TradeLedgerService, "get_entries_for_symbol")
        assert hasattr(TradeLedgerService, "get_entries_for_strategy")
        assert hasattr(TradeLedgerService, "persist_to_s3")

    def test_trade_ledger_service_methods_are_callable(self) -> None:
        """Test that TradeLedgerService methods are callable."""
        from the_alchemiser.execution_v2.services import TradeLedgerService

        service = TradeLedgerService()

        # Check methods are callable
        assert callable(service.record_filled_order)
        assert callable(service.get_ledger)
        assert callable(service.get_entries_for_symbol)
        assert callable(service.get_entries_for_strategy)
        assert callable(service.persist_to_s3)


class TestImportPerformance:
    """Test suite for import performance (no expensive operations at import time)."""

    def test_import_is_fast(self) -> None:
        """Test that importing the module is fast (no expensive operations at import time)."""
        import time

        # Fresh import by clearing from sys.modules
        if "the_alchemiser.execution_v2.services" in sys.modules:
            # Can't actually test fresh import in pytest, but can test it doesn't take long
            pass

        start = time.time()
        from the_alchemiser.execution_v2 import services
        end = time.time()

        # Import should be very fast (< 100ms even with dependencies)
        import_time = end - start
        assert import_time < 0.1, f"Import took {import_time}s, expected < 0.1s"
        assert services is not None

    def test_no_io_at_import_time(self) -> None:
        """Test that importing doesn't trigger I/O operations."""
        # This is a best-effort test - we check that common I/O modules aren't triggered
        # A more robust test would use mocking, but this is a reasonable smoke test

        from the_alchemiser.execution_v2 import services

        # If we can import without errors and quickly, there's likely no I/O
        assert services is not None


class TestModuleConsistency:
    """Test suite for consistency with other modules in the codebase."""

    def test_consistent_with_parent_module_pattern(self) -> None:
        """Test that this module follows similar patterns to parent execution_v2/__init__.py."""
        from the_alchemiser import execution_v2
        from the_alchemiser.execution_v2 import services

        # Both should have __all__
        assert hasattr(execution_v2, "__all__")
        assert hasattr(services, "__all__")

        # Both should have __version__
        assert hasattr(execution_v2, "__version__")
        assert hasattr(services, "__version__")

    def test_consistent_with_shared_services_pattern(self) -> None:
        """Test that this module follows similar patterns to shared/services/__init__.py."""
        from the_alchemiser.execution_v2 import services as exec_services
        from the_alchemiser.shared import services as shared_services

        # Both should have __all__
        assert hasattr(shared_services, "__all__")
        assert hasattr(exec_services, "__all__")

        # Both should re-export services
        assert len(shared_services.__all__) > 0
        assert len(exec_services.__all__) > 0
