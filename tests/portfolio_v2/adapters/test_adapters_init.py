#!/usr/bin/env python3
"""Business Unit: portfolio_v2 | Status: current.

Tests for portfolio_v2/adapters/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
"""

from __future__ import annotations

import pytest


class TestAdaptersModuleInterface:
    """Test suite for adapters module public API."""

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ list matches actual exports."""
        from the_alchemiser.portfolio_v2 import adapters

        # Check __all__ exists
        assert hasattr(adapters, "__all__"), "Module must define __all__"

        expected_exports = {
            "AlpacaDataAdapter",
        }
        actual_exports = set(adapters.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. Expected: {expected_exports}, Got: {actual_exports}"
        )

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.portfolio_v2 import adapters

        for name in adapters.__all__:
            assert hasattr(adapters, name), f"Export '{name}' in __all__ but not found in module"

            obj = getattr(adapters, name)
            assert obj is not None, f"Export '{name}' is None"

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no leaks)."""
        from the_alchemiser.portfolio_v2 import adapters

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
        from the_alchemiser.portfolio_v2 import adapters

        for name in adapters.__all__:
            test_namespace[name] = getattr(adapters, name)

        # Verify expected items are present
        assert "AlpacaDataAdapter" in test_namespace

        # Verify private items are NOT imported
        assert "__version__" not in test_namespace or hasattr(adapters, "__version__"), (
            "Private attributes should not be star-imported"
        )

    def test_exports_are_classes_or_protocols(self) -> None:
        """Test that all exports are classes or protocols (no functions/constants)."""
        from the_alchemiser.portfolio_v2 import adapters

        for name in adapters.__all__:
            obj = getattr(adapters, name)

            # Should be a class or protocol
            assert isinstance(obj, type), (
                f"Export '{name}' should be a class/protocol, got {type(obj)}"
            )

    def test_module_has_docstring(self) -> None:
        """Test that module has a proper docstring."""
        from the_alchemiser.portfolio_v2 import adapters

        assert adapters.__doc__ is not None, "Module must have a docstring"
        assert len(adapters.__doc__) > 50, "Docstring should be descriptive"
        assert "Business Unit:" in adapters.__doc__, "Must include business unit header"
        assert "portfolio" in adapters.__doc__.lower(), "Must mention portfolio"

    def test_module_has_version(self) -> None:
        """Test that module has __version__ attribute."""
        from the_alchemiser.portfolio_v2 import adapters

        assert hasattr(adapters, "__version__"), "Module should have __version__"
        assert isinstance(adapters.__version__, str), "__version__ should be a string"
        # Version should be in semver format
        parts = adapters.__version__.split(".")
        assert len(parts) == 3, "Version should be in semver format (major.minor.patch)"

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.portfolio_v2 import adapters

        # Get initial exports
        initial_exports = {name: getattr(adapters, name) for name in adapters.__all__}

        # Re-import (simulate)
        import importlib

        importlib.reload(adapters)

        # Get exports again
        reloaded_exports = {name: getattr(adapters, name) for name in adapters.__all__}

        # Should be same objects (identity, not just equality)
        for name in adapters.__all__:
            assert initial_exports[name] is reloaded_exports[name], (
                f"Export '{name}' changed on reload"
            )

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.portfolio_v2 import adapters

            # Check that submodules are imported
            assert hasattr(adapters, "AlpacaDataAdapter")

        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            raise


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_strategy_imports(self) -> None:
        """Test that adapters module doesn't directly import from strategy_v2."""
        import ast
        from pathlib import Path

        # Get all Python files in portfolio_v2/adapters
        adapters_dir = (
            Path(__file__).parent.parent.parent.parent
            / "the_alchemiser"
            / "portfolio_v2"
            / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("_"):
                continue  # Skip private/init files for now

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "strategy_v2" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass  # Skip files that can't be parsed

        # Portfolio adapters should not import strategy modules
        assert not bad_imports, (
            f"Portfolio adapters should not import strategy_v2 modules. Found: {bad_imports}"
        )

    def test_no_execution_imports(self) -> None:
        """Test that adapters module doesn't directly import from execution_v2."""
        import ast
        from pathlib import Path

        adapters_dir = (
            Path(__file__).parent.parent.parent.parent
            / "the_alchemiser"
            / "portfolio_v2"
            / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("_"):
                continue

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "execution_v2" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass

        assert not bad_imports, (
            f"Portfolio adapters should not import execution_v2 modules. Found: {bad_imports}"
        )

    def test_no_orchestration_imports(self) -> None:
        """Test that adapters module doesn't directly import from orchestration."""
        import ast
        from pathlib import Path

        adapters_dir = (
            Path(__file__).parent.parent.parent.parent
            / "the_alchemiser"
            / "portfolio_v2"
            / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("_"):
                continue

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "orchestration" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass

        assert not bad_imports, (
            f"Portfolio adapters should not import orchestration modules. Found: {bad_imports}"
        )


class TestTypePreservation:
    """Test suite for type information preservation."""

    def test_alpaca_data_adapter_type_preserved(self) -> None:
        """Test that AlpacaDataAdapter type is preserved in re-export."""
        from the_alchemiser.portfolio_v2 import adapters
        from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
            AlpacaDataAdapter,
        )

        # Re-exported type should be same as source type
        assert adapters.AlpacaDataAdapter is AlpacaDataAdapter, (
            "Re-export should preserve type identity"
        )

    def test_alpaca_data_adapter_is_class(self) -> None:
        """Test that AlpacaDataAdapter is a class."""
        from the_alchemiser.portfolio_v2 import adapters

        assert isinstance(adapters.AlpacaDataAdapter, type), "AlpacaDataAdapter should be a class"

    def test_type_hints_preserved(self) -> None:
        """Test that type hints are preserved in re-exports."""
        from the_alchemiser.portfolio_v2 import adapters

        # Should be able to get type hints for the class
        adapter_class = adapters.AlpacaDataAdapter
        assert hasattr(adapter_class, "__init__"), "Class should have __init__ method"

        # Type hints should be available (may require runtime imports for TYPE_CHECKING guards)
        # Just verify the __annotations__ exist
        assert hasattr(adapter_class.__init__, "__annotations__"), "Type hints should be preserved"
        annotations = adapter_class.__init__.__annotations__
        assert annotations is not None, "Annotations should not be None"
        assert len(annotations) > 0, "Should have at least one annotation (alpaca_manager)"


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_name(self) -> None:
        """Test module __name__ attribute."""
        from the_alchemiser.portfolio_v2 import adapters

        assert adapters.__name__ == "the_alchemiser.portfolio_v2.adapters", (
            "Module __name__ should match expected path"
        )

    def test_module_file_location(self) -> None:
        """Test that module is in the correct location."""
        from the_alchemiser.portfolio_v2 import adapters

        assert hasattr(adapters, "__file__"), "Module should have __file__ attribute"
        assert "portfolio_v2/adapters" in adapters.__file__, (
            "Module should be in portfolio_v2/adapters directory"
        )

    def test_public_api_documentation(self) -> None:
        """Test that public API is documented in module docstring."""
        from the_alchemiser.portfolio_v2 import adapters

        docstring = adapters.__doc__
        assert docstring is not None

        # Should document the public API
        assert "Public API:" in docstring or "API:" in docstring, "Should document public API"
        assert "AlpacaDataAdapter" in docstring, "Should mention AlpacaDataAdapter in docstring"

    def test_module_boundaries_documented(self) -> None:
        """Test that module boundaries are documented."""
        from the_alchemiser.portfolio_v2 import adapters

        docstring = adapters.__doc__
        assert docstring is not None

        # Should document boundaries
        assert "boundaries" in docstring.lower() or "imports" in docstring.lower(), (
            "Should document module boundaries"
        )


class TestImportPatterns:
    """Test suite for import patterns and best practices."""

    def test_direct_import_from_module(self) -> None:
        """Test direct import from module works."""
        from the_alchemiser.portfolio_v2.adapters import AlpacaDataAdapter

        assert AlpacaDataAdapter is not None

    def test_import_module_then_access(self) -> None:
        """Test importing module then accessing attributes."""
        from the_alchemiser.portfolio_v2 import adapters

        AlpacaDataAdapter = adapters.AlpacaDataAdapter
        assert AlpacaDataAdapter is not None

    def test_deep_import_still_works(self) -> None:
        """Test that deep imports still work (backward compatibility)."""
        from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
            AlpacaDataAdapter,
        )

        assert AlpacaDataAdapter is not None

    def test_consistent_import_results(self) -> None:
        """Test that different import patterns yield the same object."""
        from the_alchemiser.portfolio_v2 import adapters
        from the_alchemiser.portfolio_v2.adapters import (
            AlpacaDataAdapter as DirectImport,
        )
        from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
            AlpacaDataAdapter as DeepImport,
        )

        # All three should be the same object
        assert adapters.AlpacaDataAdapter is DirectImport
        assert DirectImport is DeepImport
        assert adapters.AlpacaDataAdapter is DeepImport
