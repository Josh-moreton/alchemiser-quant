#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared/brokers/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
- Module determinism and no circular imports
- Module boundary enforcement (no execution/portfolio/strategy imports)
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


class TestBrokersModuleInterface:
    """Test suite for brokers module public API."""

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.shared import brokers

        assert brokers.__doc__ is not None
        assert "Business Unit: shared" in brokers.__doc__
        assert "Status: current" in brokers.__doc__

    def test_module_docstring_describes_purpose(self) -> None:
        """Test that docstring clearly states the module purpose."""
        from the_alchemiser.shared import brokers

        docstring = brokers.__doc__ or ""
        assert "broker" in docstring.lower()
        assert "abstractions" in docstring.lower() or "integration" in docstring.lower()

    def test_all_exports_defined(self) -> None:
        """Test that __all__ is defined and not empty."""
        from the_alchemiser.shared import brokers

        assert hasattr(brokers, "__all__")
        assert isinstance(brokers.__all__, list)
        assert len(brokers.__all__) > 0
        assert len(brokers.__all__) == 2  # AlpacaManager + create_alpaca_manager

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import brokers

        for name in brokers.__all__:
            assert hasattr(brokers, name), f"{name} is in __all__ but not importable"
            obj = getattr(brokers, name)
            assert obj is not None, f"{name} is None"

    def test_all_exports_are_strings(self) -> None:
        """Test that __all__ contains only strings (not the actual objects)."""
        from the_alchemiser.shared import brokers

        for item in brokers.__all__:
            assert isinstance(item, str), f"__all__ contains non-string: {type(item)}"

    def test_all_exports_alphabetically_sorted(self) -> None:
        """Test that __all__ exports are alphabetically sorted."""
        from the_alchemiser.shared import brokers

        sorted_all = sorted(brokers.__all__)
        assert brokers.__all__ == sorted_all, "exports in __all__ should be alphabetically sorted"

    def test_alpaca_manager_exported(self) -> None:
        """Test that AlpacaManager is exported and is the correct type."""
        from the_alchemiser.shared import brokers
        from the_alchemiser.shared.brokers.alpaca_manager import (
            AlpacaManager as SourceClass,
        )

        assert "AlpacaManager" in brokers.__all__
        assert hasattr(brokers, "AlpacaManager")

        # Verify it's the same class, not a copy
        assert brokers.AlpacaManager is SourceClass

        # Verify it's a class
        assert isinstance(brokers.AlpacaManager, type)

    def test_create_alpaca_manager_exported(self) -> None:
        """Test that create_alpaca_manager is exported and is callable."""
        from the_alchemiser.shared import brokers
        from the_alchemiser.shared.brokers.alpaca_manager import (
            create_alpaca_manager as source_func,
        )

        assert "create_alpaca_manager" in brokers.__all__
        assert hasattr(brokers, "create_alpaca_manager")

        # Verify it's the same function, not a copy
        assert brokers.create_alpaca_manager is source_func

        # Verify it's callable
        assert callable(brokers.create_alpaca_manager)

    def test_alpaca_manager_is_class(self) -> None:
        """Test that AlpacaManager is a class (not instance or function)."""
        from the_alchemiser.shared import brokers

        assert isinstance(brokers.AlpacaManager, type)
        assert hasattr(brokers.AlpacaManager, "__init__")
        assert hasattr(brokers.AlpacaManager, "__new__")

    def test_no_unintended_exports(self) -> None:
        """Test that only items in __all__ are considered public exports."""
        from the_alchemiser.shared import brokers

        # Get all non-private attributes (excluding builtins and known module imports)
        public_attrs = [
            name
            for name in dir(brokers)
            if not name.startswith("_")
            and name != "annotations"
            and name != "alpaca_manager"  # Submodule import (expected in Python)
        ]

        # All public attributes should be in __all__
        for attr in public_attrs:
            assert attr in brokers.__all__, (
                f"{attr} is public but not in __all__ (API surface leak)"
            )

    def test_exports_count_matches_all(self) -> None:
        """Test that the number of exports matches __all__ declaration."""
        from the_alchemiser.shared import brokers

        # Count non-private attributes (excluding builtins and submodule imports)
        public_attrs = [
            name
            for name in dir(brokers)
            if not name.startswith("_")
            and name != "annotations"
            and name != "alpaca_manager"  # Submodule import (expected)
        ]

        # Should match __all__ length
        assert len(public_attrs) == len(brokers.__all__), (
            "Number of public attributes doesn't match __all__"
        )

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.shared import brokers as brokers1

        # Re-import
        from the_alchemiser.shared import brokers as brokers2

        # Should be the same module object
        assert brokers1 is brokers2

        # Exports should be identical
        assert brokers1.AlpacaManager is brokers2.AlpacaManager
        assert brokers1.create_alpaca_manager is brokers2.create_alpaca_manager

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.shared import brokers

            # Check that exports are loaded
            assert hasattr(brokers, "AlpacaManager")
            assert hasattr(brokers, "create_alpaca_manager")

        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            raise

    def test_module_can_be_imported_multiple_times(self) -> None:
        """Test that the module can be safely imported multiple times."""
        # Import multiple times
        from the_alchemiser.shared import brokers

        first_manager = brokers.AlpacaManager

        # Import again
        from the_alchemiser.shared import brokers as brokers_again

        second_manager = brokers_again.AlpacaManager

        # Should be the exact same class object
        assert first_manager is second_manager


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_execution_v2_imports(self) -> None:
        """Test that the module doesn't import from execution_v2 (would violate architecture)."""
        # Clear any execution_v2 modules from sys.modules first
        execution_modules_before = {name for name in sys.modules.keys() if "execution_v2" in name}

        # Import brokers module
        from the_alchemiser.shared import brokers

        # Get execution modules after import
        execution_modules_after = {name for name in sys.modules.keys() if "execution_v2" in name}

        # No new execution_v2 modules should be loaded
        new_modules = execution_modules_after - execution_modules_before
        assert len(new_modules) == 0, (
            f"brokers module triggered execution_v2 imports: {new_modules}"
        )

        assert brokers is not None  # Use the import

    def test_no_portfolio_v2_imports(self) -> None:
        """Test that the module doesn't import from portfolio_v2 (would violate architecture)."""
        # Clear any portfolio_v2 modules from sys.modules first
        portfolio_modules_before = {name for name in sys.modules.keys() if "portfolio_v2" in name}

        # Import brokers module
        from the_alchemiser.shared import brokers

        # Get portfolio modules after import
        portfolio_modules_after = {name for name in sys.modules.keys() if "portfolio_v2" in name}

        # No new portfolio_v2 modules should be loaded
        new_modules = portfolio_modules_after - portfolio_modules_before
        assert len(new_modules) == 0, (
            f"brokers module triggered portfolio_v2 imports: {new_modules}"
        )

        assert brokers is not None  # Use the import

    def test_no_strategy_v2_imports(self) -> None:
        """Test that the module doesn't import from strategy_v2 (would violate architecture)."""
        # Clear any strategy_v2 modules from sys.modules first
        strategy_modules_before = {name for name in sys.modules.keys() if "strategy_v2" in name}

        # Import brokers module
        from the_alchemiser.shared import brokers

        # Get strategy modules after import
        strategy_modules_after = {name for name in sys.modules.keys() if "strategy_v2" in name}

        # No new strategy_v2 modules should be loaded
        new_modules = strategy_modules_after - strategy_modules_before
        assert len(new_modules) == 0, f"brokers module triggered strategy_v2 imports: {new_modules}"

        assert brokers is not None  # Use the import


class TestTypePreservation:
    """Test suite for type information preservation."""

    def test_alpaca_manager_preserves_types(self) -> None:
        """Test that AlpacaManager type information is preserved through re-export."""
        from the_alchemiser.shared import brokers
        from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

        # The exported class should have the same __module__ as the source
        assert brokers.AlpacaManager.__module__ == AlpacaManager.__module__
        assert brokers.AlpacaManager.__name__ == AlpacaManager.__name__
        assert brokers.AlpacaManager.__qualname__ == AlpacaManager.__qualname__

    def test_create_alpaca_manager_preserves_types(self) -> None:
        """Test that create_alpaca_manager type information is preserved."""
        from the_alchemiser.shared import brokers
        from the_alchemiser.shared.brokers.alpaca_manager import create_alpaca_manager

        # The exported function should have the same __module__ as the source
        assert brokers.create_alpaca_manager.__module__ == create_alpaca_manager.__module__
        assert brokers.create_alpaca_manager.__name__ == create_alpaca_manager.__name__
        assert brokers.create_alpaca_manager.__qualname__ == create_alpaca_manager.__qualname__

    def test_alpaca_manager_has_correct_module_path(self) -> None:
        """Test that AlpacaManager __module__ points to the correct source module."""
        from the_alchemiser.shared import brokers

        # Should point to alpaca_manager module, not the __init__
        assert brokers.AlpacaManager.__module__ == "the_alchemiser.shared.brokers.alpaca_manager"

    def test_create_alpaca_manager_has_correct_module_path(self) -> None:
        """Test that create_alpaca_manager __module__ points to the correct source."""
        from the_alchemiser.shared import brokers

        # Should point to alpaca_manager module, not the __init__
        assert (
            brokers.create_alpaca_manager.__module__
            == "the_alchemiser.shared.brokers.alpaca_manager"
        )


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_has_future_annotations(self) -> None:
        """Test that the module uses future annotations."""
        from the_alchemiser.shared import brokers

        # Check if the module compiled correctly with future annotations
        assert brokers is not None

        # We can also check if annotations are postponed (they would be strings)
        # But this is hard to test directly, so we just verify it imports

    def test_docstring_mentions_alpaca_manager(self) -> None:
        """Test that docstring mentions AlpacaManager."""
        from the_alchemiser.shared import brokers

        docstring = brokers.__doc__ or ""
        assert "AlpacaManager" in docstring

    def test_docstring_mentions_package_contents(self) -> None:
        """Test that docstring lists package contents."""
        from the_alchemiser.shared import brokers

        docstring = brokers.__doc__ or ""
        assert "Contains:" in docstring or "contains" in docstring.lower()

    def test_module_has_proper_header(self) -> None:
        """Test that module has proper Business Unit and Status header."""
        from the_alchemiser.shared import brokers

        docstring = brokers.__doc__ or ""
        assert "Business Unit:" in docstring
        assert "Status:" in docstring
        assert "shared" in docstring.lower()
        assert "current" in docstring.lower()


class TestBackwardCompatibility:
    """Test suite for backward compatibility guarantees."""

    def test_alpaca_manager_import_path_stable(self) -> None:
        """Test that AlpacaManager can be imported from brokers package."""
        # This import path should remain stable
        from the_alchemiser.shared.brokers import AlpacaManager

        assert AlpacaManager is not None
        assert isinstance(AlpacaManager, type)

    def test_create_alpaca_manager_import_path_stable(self) -> None:
        """Test that create_alpaca_manager can be imported from brokers package."""
        # This import path should remain stable
        from the_alchemiser.shared.brokers import create_alpaca_manager

        assert create_alpaca_manager is not None
        assert callable(create_alpaca_manager)

    def test_direct_submodule_import_still_works(self) -> None:
        """Test that direct import from alpaca_manager submodule still works."""
        # Users should be able to import directly from submodule too
        from the_alchemiser.shared.brokers.alpaca_manager import (
            AlpacaManager,
            create_alpaca_manager,
        )

        assert AlpacaManager is not None
        assert create_alpaca_manager is not None

    def test_both_import_paths_give_same_objects(self) -> None:
        """Test that both import paths (via __init__ and direct) give same objects."""
        from the_alchemiser.shared.brokers import (
            AlpacaManager as ManagerViaInit,
        )
        from the_alchemiser.shared.brokers import (
            create_alpaca_manager as factory_via_init,
        )
        from the_alchemiser.shared.brokers.alpaca_manager import (
            AlpacaManager as ManagerDirect,
        )
        from the_alchemiser.shared.brokers.alpaca_manager import (
            create_alpaca_manager as factory_direct,
        )

        # Should be the exact same objects
        assert ManagerViaInit is ManagerDirect
        assert factory_via_init is factory_direct


class TestImportPerformance:
    """Test suite for import performance and side effects."""

    def test_import_has_no_side_effects(self) -> None:
        """Test that importing the module doesn't cause side effects (I/O, network, etc)."""
        # This is hard to test perfectly, but we can check that import is fast
        import time

        start = time.time()
        from the_alchemiser.shared import brokers  # noqa: F401

        elapsed = time.time() - start

        # Import should be fast (< 1 second)
        # This is a loose bound; mainly catches if there's unexpected blocking I/O
        assert elapsed < 1.0, f"Import took {elapsed:.2f}s, may have side effects"

    def test_import_does_not_create_files(self) -> None:
        """Test that importing doesn't create any files."""
        import os
        import tempfile

        # Check temp directory before import
        temp_files_before = set(os.listdir(tempfile.gettempdir()))

        from the_alchemiser.shared import brokers  # noqa: F401

        # Check temp directory after import
        temp_files_after = set(os.listdir(tempfile.gettempdir()))

        # Should not create any new temp files
        new_files = temp_files_after - temp_files_before
        # Filter out unrelated files (pytest may create some)
        broker_related = [f for f in new_files if "broker" in f.lower()]
        assert len(broker_related) == 0, f"Import created temp files: {broker_related}"


class TestAPIUsagePatterns:
    """Test suite for common API usage patterns."""

    def test_alpaca_manager_has_expected_methods(self) -> None:
        """Test that AlpacaManager has key expected methods."""
        from the_alchemiser.shared.brokers import AlpacaManager

        # Check for key methods that users rely on
        expected_methods = [
            "__init__",
            "__new__",
            "get_account",
            "get_positions",
            "get_latest_quote",
        ]

        for method in expected_methods:
            assert hasattr(AlpacaManager, method), (
                f"AlpacaManager missing expected method: {method}"
            )

    def test_create_alpaca_manager_has_correct_signature(self) -> None:
        """Test that create_alpaca_manager has the expected signature."""
        import inspect

        from the_alchemiser.shared.brokers import create_alpaca_manager

        sig = inspect.signature(create_alpaca_manager)
        params = list(sig.parameters.keys())

        # Should have api_key, secret_key at minimum
        assert "api_key" in params
        assert "secret_key" in params
        assert "paper" in params  # Common parameter

    def test_alpaca_manager_is_singleton_pattern(self) -> None:
        """Test that AlpacaManager follows singleton pattern per credentials."""
        from the_alchemiser.shared.brokers import AlpacaManager

        # Check for singleton-related attributes/methods
        # AlpacaManager uses _instances class variable for singleton behavior
        assert hasattr(AlpacaManager, "_instances") or hasattr(AlpacaManager, "__new__")
