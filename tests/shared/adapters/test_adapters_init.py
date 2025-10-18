#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared/adapters/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
- Module boundaries are enforced
"""

from __future__ import annotations

import sys
from typing import get_type_hints

import pytest


class TestAdaptersModuleInterface:
    """Test suite for adapters module public API."""

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ list matches actual exports."""
        from the_alchemiser.shared import adapters

        assert hasattr(adapters, "__all__"), "Module should define __all__"
        assert isinstance(adapters.__all__, list), "__all__ should be a list"
        assert len(adapters.__all__) > 0, "__all__ should not be empty"

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import adapters

        for name in adapters.__all__:
            assert hasattr(adapters, name), f"Export '{name}' in __all__ but not found in module"

    def test_alpaca_asset_metadata_adapter_export(self) -> None:
        """Test AlpacaAssetMetadataAdapter is correctly exported."""
        from the_alchemiser.shared import adapters

        assert "AlpacaAssetMetadataAdapter" in adapters.__all__, (
            "AlpacaAssetMetadataAdapter should be in __all__"
        )
        assert hasattr(adapters, "AlpacaAssetMetadataAdapter"), (
            "AlpacaAssetMetadataAdapter should be available"
        )

        # Verify it's the actual class
        from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import (
            AlpacaAssetMetadataAdapter,
        )

        assert adapters.AlpacaAssetMetadataAdapter is AlpacaAssetMetadataAdapter, (
            "Should export the same class instance"
        )

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no leaks)."""
        from the_alchemiser.shared import adapters

        public_names = set(adapters.__all__)
        actual_names = {name for name in dir(adapters) if not name.startswith("_")}

        unintended = actual_names - public_names
        # Filter out common acceptable module attributes
        unintended = {
            name
            for name in unintended
            if name not in ["annotations"]  # from __future__ import
        }

        assert len(unintended) == 0, f"Found unintended exports: {unintended}"

    def test_star_import_behavior(self) -> None:
        """Test that 'from adapters import *' only imports __all__ items."""
        # Create a clean namespace
        namespace = {}

        # Execute star import
        exec("from the_alchemiser.shared.adapters import *", namespace)

        # Get imported names (excluding builtins)
        imported_names = {name for name in namespace if not name.startswith("__")}

        from the_alchemiser.shared import adapters

        expected_names = set(adapters.__all__)

        assert imported_names == expected_names, (
            f"Star import should only import __all__. Got: {imported_names}, Expected: {expected_names}"
        )

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.shared import adapters

        assert adapters.__doc__ is not None, "Module should have a docstring"
        assert len(adapters.__doc__) > 50, "Docstring should be comprehensive"
        assert "Business Unit: shared" in adapters.__doc__, "Should have Business Unit header"
        assert "Status: current" in adapters.__doc__, "Should have Status indicator"

    def test_exports_are_classes_or_protocols(self) -> None:
        """Test that all exports are classes or protocols (no functions/constants)."""
        from the_alchemiser.shared import adapters

        for name in adapters.__all__:
            obj = getattr(adapters, name)

            # Should be a class or protocol
            assert isinstance(obj, type), (
                f"Export '{name}' should be a class/protocol, got {type(obj)}"
            )

    def test_relative_imports_work(self) -> None:
        """Test that relative imports within the module work correctly."""
        # This test ensures the __init__.py import statements are valid
        try:
            from the_alchemiser.shared.adapters import (
                AlpacaAssetMetadataAdapter,
            )

            # If we get here, imports succeeded
            assert AlpacaAssetMetadataAdapter is not None

        except ImportError as e:
            pytest.fail(f"Relative imports failed: {e}")

    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        from the_alchemiser.shared import adapters

        first_import = id(adapters.AlpacaAssetMetadataAdapter)

        # Force reimport
        if "the_alchemiser.shared.adapters" in sys.modules:
            # Get fresh reference
            import importlib

            importlib.reload(adapters)

        from the_alchemiser.shared import adapters as adapters_reimport

        second_import = id(adapters_reimport.AlpacaAssetMetadataAdapter)

        # Should be the same object (Python caches modules)
        assert first_import == second_import, "Re-importing should return the same object"

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # If we can import without errors, there are no circular imports
        try:
            from the_alchemiser.shared import adapters

            # Check that submodules are imported
            assert hasattr(adapters, "AlpacaAssetMetadataAdapter")

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

        # Get all Python files in shared/adapters
        adapters_dir = (
            Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("test_"):
                continue  # Skip test files

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "strategy_v2" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass  # Skip files that can't be parsed

        assert len(bad_imports) == 0, f"Found forbidden strategy_v2 imports: {bad_imports}"

    def test_no_portfolio_imports(self) -> None:
        """Test that adapters module doesn't directly import from portfolio_v2."""
        import ast
        from pathlib import Path

        # Get all Python files in shared/adapters
        adapters_dir = (
            Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("test_"):
                continue  # Skip test files

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "portfolio_v2" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass  # Skip files that can't be parsed

        assert len(bad_imports) == 0, f"Found forbidden portfolio_v2 imports: {bad_imports}"

    def test_no_execution_imports(self) -> None:
        """Test that adapters module doesn't directly import from execution_v2."""
        import ast
        from pathlib import Path

        # Get all Python files in shared/adapters
        adapters_dir = (
            Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "adapters"
        )
        python_files = list(adapters_dir.glob("*.py"))

        bad_imports = []
        for file_path in python_files:
            if file_path.name.startswith("test_"):
                continue  # Skip test files

            try:
                with open(file_path) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "execution_v2" in node.module:
                            bad_imports.append(f"{file_path.name}: {node.module}")
            except Exception:
                pass  # Skip files that can't be parsed

        assert len(bad_imports) == 0, f"Found forbidden execution_v2 imports: {bad_imports}"


class TestTypePreservation:
    """Test suite for type information preservation."""

    def test_type_hints_preserved(self) -> None:
        """Test that type hints are preserved through re-export."""
        from the_alchemiser.shared import adapters
        from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import (
            AlpacaAssetMetadataAdapter,
        )

        # Get type hints from both sources
        exported_class = adapters.AlpacaAssetMetadataAdapter
        original_class = AlpacaAssetMetadataAdapter

        # They should be the same class
        assert exported_class is original_class, (
            "Exported class should be the same object as original"
        )

        # Verify __init__ signature is accessible
        assert hasattr(exported_class, "__init__"), "Should have __init__ method"

        # Check that we can get type hints (means they're preserved)
        try:
            hints = get_type_hints(exported_class.__init__)
            assert "alpaca_manager" in hints, "Type hints should include constructor parameters"
        except Exception as e:
            pytest.fail(f"Failed to get type hints: {e}")


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_has_version(self) -> None:
        """Test that module has a __version__ attribute."""
        from the_alchemiser.shared import adapters

        assert hasattr(adapters, "__version__"), "Module should have __version__"
        assert isinstance(adapters.__version__, str), "__version__ should be a string"
        assert len(adapters.__version__) > 0, "__version__ should not be empty"

        # Check version format (should be semantic versioning)
        parts = adapters.__version__.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"

    def test_public_api_documented_in_docstring(self) -> None:
        """Test that public API is documented in module docstring."""
        from the_alchemiser.shared import adapters

        docstring = adapters.__doc__ or ""

        # Check that all __all__ items are mentioned in docstring
        for export_name in adapters.__all__:
            assert export_name in docstring, (
                f"Export '{export_name}' should be documented in module docstring"
            )

    def test_module_boundaries_documented(self) -> None:
        """Test that module boundaries are documented."""
        from the_alchemiser.shared import adapters

        docstring = adapters.__doc__ or ""

        # Check for boundary documentation
        assert "Module boundaries" in docstring or "boundaries" in docstring.lower(), (
            "Module boundaries should be documented"
        )

    def test_no_namespace_pollution(self) -> None:
        """Test that implementation modules don't leak into namespace."""
        from the_alchemiser.shared import adapters

        # These should not be in the public namespace
        assert not hasattr(adapters, "alpaca_asset_metadata_adapter"), (
            "Implementation module should be cleaned up"
        )


class TestImportPatterns:
    """Test suite for import patterns and usage."""

    def test_can_import_from_module_directly(self) -> None:
        """Test direct import pattern works."""
        from the_alchemiser.shared.adapters import AlpacaAssetMetadataAdapter

        assert AlpacaAssetMetadataAdapter is not None, "Should be able to import directly"

    def test_can_import_module_and_access_exports(self) -> None:
        """Test module import pattern works."""
        from the_alchemiser.shared import adapters

        adapter_class = adapters.AlpacaAssetMetadataAdapter
        assert adapter_class is not None, "Should be able to access via module reference"

    def test_star_import_only_imports_public_api(self) -> None:
        """Test that star import respects __all__."""
        namespace = {}
        exec("from the_alchemiser.shared.adapters import *", namespace)

        # Should only have __all__ items (plus builtins)
        non_builtin = {k for k in namespace if not k.startswith("__")}

        from the_alchemiser.shared import adapters

        assert non_builtin == set(adapters.__all__), "Star import should only import __all__"
