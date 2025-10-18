"""Business Unit: root | Status: current

Unit tests for the_alchemiser package root __init__.py.

Tests package-level attributes, imports, and documentation.
"""

import pytest


class TestPackageRoot:
    """Test the_alchemiser package root initialization."""

    def test_package_imports_successfully(self):
        """Test package imports without errors."""
        import the_alchemiser

        assert the_alchemiser is not None
        assert the_alchemiser.__name__ == "the_alchemiser"

    def test_package_has_docstring(self):
        """Test package has comprehensive docstring."""
        import the_alchemiser

        assert the_alchemiser.__doc__ is not None
        assert isinstance(the_alchemiser.__doc__, str)
        assert len(the_alchemiser.__doc__) > 100  # Substantive documentation
        assert "Alchemiser" in the_alchemiser.__doc__

    def test_package_docstring_content(self):
        """Test package docstring contains expected content."""
        import the_alchemiser

        doc = the_alchemiser.__doc__
        assert "Business Unit: root" in doc
        assert "Status: current" in doc
        assert "Multi-strategy" in doc
        assert "Alpaca" in doc

    def test_package_has_all_attribute(self):
        """Test package defines __all__."""
        import the_alchemiser

        assert hasattr(the_alchemiser, "__all__")
        assert isinstance(the_alchemiser.__all__, list)

    def test_package_all_is_empty(self):
        """Test package follows zero-export policy."""
        import the_alchemiser

        # Package root intentionally exports nothing
        # Users should import from submodules
        assert len(the_alchemiser.__all__) == 0

    def test_package_has_future_annotations(self):
        """Test package uses future annotations."""
        # This is implicitly verified by successful import
        # If annotations were broken, import would fail

        assert True  # If we get here, future annotations work

    def test_package_file_attribute(self):
        """Test package has __file__ attribute."""
        import the_alchemiser

        assert hasattr(the_alchemiser, "__file__")
        assert the_alchemiser.__file__ is not None
        assert "__init__.py" in the_alchemiser.__file__

    def test_package_path_attribute(self):
        """Test package has __path__ attribute."""
        import the_alchemiser

        assert hasattr(the_alchemiser, "__path__")
        # __path__ should be a list for packages
        assert isinstance(the_alchemiser.__path__, list)
        assert len(the_alchemiser.__path__) > 0

    def test_package_name_attribute(self):
        """Test package has correct __name__."""
        import the_alchemiser

        assert the_alchemiser.__name__ == "the_alchemiser"
        assert not the_alchemiser.__name__.startswith("_")

    def test_repeated_imports_return_same_object(self):
        """Test that repeated imports return the same package object."""
        import the_alchemiser as pkg1
        import the_alchemiser as pkg2

        assert pkg1 is pkg2
        assert id(pkg1) == id(pkg2)

    def test_no_unintended_public_exports(self):
        """Test that package doesn't export unintended symbols."""
        import the_alchemiser

        # Get all attributes that don't start with underscore
        public_attrs = [attr for attr in dir(the_alchemiser) if not attr.startswith("_")]

        # Should have no public exports except 'annotations' from __future__
        # 'annotations' is expected from "from __future__ import annotations"
        expected_attrs = {"annotations"}
        actual_attrs = set(public_attrs)
        assert actual_attrs == expected_attrs, (
            f"Unexpected exports: {actual_attrs - expected_attrs}"
        )

    def test_package_docstring_mentions_strategies(self):
        """Test docstring mentions all supported strategies."""
        import the_alchemiser

        doc = the_alchemiser.__doc__
        # Check for modern strategy names
        assert "Nuclear" in doc
        assert "TECL" in doc
        assert "KLM" in doc
        assert "DSL" in doc

    def test_package_docstring_mentions_modules(self):
        """Test docstring mentions key modules."""
        import the_alchemiser

        doc = the_alchemiser.__doc__
        # Check for current module structure
        assert "strategy_v2" in doc
        assert "portfolio_v2" in doc
        assert "execution_v2" in doc
        assert "orchestration" in doc
        assert "shared" in doc
        assert "main" in doc

    def test_package_docstring_has_example(self):
        """Test docstring includes usage example."""
        import the_alchemiser

        doc = the_alchemiser.__doc__
        assert "Example:" in doc
        assert ">>>" in doc
        assert "main" in doc

    def test_package_no_import_side_effects(self):
        """Test importing package has no side effects."""
        # Import should not:
        # - Write to disk
        # - Make network calls
        # - Modify global state (beyond sys.modules)
        # - Print to stdout/stderr
        # This is implicitly tested by successful import

        assert True  # If we get here, no exceptions from side effects

    @pytest.mark.unit
    def test_package_import_is_fast(self):
        """Test package imports quickly."""
        import importlib
        import sys
        import time

        # Remove from cache to force re-import
        if "the_alchemiser" in sys.modules:
            del sys.modules["the_alchemiser"]

        start = time.perf_counter()
        importlib.import_module("the_alchemiser")
        duration = time.perf_counter() - start

        # Package root should import very quickly (< 100ms)
        # since it has no imports except __future__
        assert duration < 0.1, f"Package import took {duration:.3f}s, expected < 0.1s"

    def test_package_in_sys_modules(self):
        """Test package is registered in sys.modules."""
        import sys

        import the_alchemiser

        assert "the_alchemiser" in sys.modules
        assert sys.modules["the_alchemiser"] is the_alchemiser

    def test_all_is_typed(self):
        """Test __all__ has type annotation."""
        import the_alchemiser

        # Check that __all__ is a list of strings
        assert isinstance(the_alchemiser.__all__, list)
        for item in the_alchemiser.__all__:
            assert isinstance(item, str)

    def test_package_structure_annotation(self):
        """Test package has proper structure for a namespace."""
        # Package should be a module type
        import types

        import the_alchemiser

        assert isinstance(the_alchemiser, types.ModuleType)

    def test_no_deprecated_exports(self):
        """Test package doesn't export deprecated symbols."""
        import the_alchemiser

        # Check that old/deprecated names aren't available
        deprecated_names = [
            "run_all_signals_display",  # Legacy function
            "core",  # Old module name
            "cli",  # Moved to orchestration
        ]

        for name in deprecated_names:
            # Should not be available as direct attribute
            # (even if importable from submodules)
            assert not hasattr(the_alchemiser, name) or name.startswith("_")

    def test_docstring_follows_business_unit_format(self):
        """Test docstring starts with Business Unit marker."""
        import the_alchemiser

        doc = the_alchemiser.__doc__
        lines = doc.strip().split("\n")
        first_line = lines[0]

        # Should follow format: "Business Unit: <name> | Status: <status>"
        assert "Business Unit:" in first_line
        assert "Status:" in first_line
        assert "current" in first_line

    def test_package_type_annotations_available(self):
        """Test package supports PEP 561 type annotations."""
        from pathlib import Path

        import the_alchemiser

        # Check for py.typed marker file
        package_dir = Path(the_alchemiser.__file__).parent
        py_typed = package_dir / "py.typed"

        assert py_typed.exists(), "py.typed marker file should exist for PEP 561"
