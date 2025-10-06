"""Business Unit: execution | Status: current

Unit tests for execution_v2/core/__init__.py.

Tests module structure, documentation, imports, and accessibility patterns.
"""

import pytest


class TestExecutionV2CoreInit:
    """Test execution_v2/core __init__.py module structure."""

    def test_module_docstring_exists(self):
        """Test that the module has proper docstring."""
        from the_alchemiser.execution_v2 import core

        assert core.__doc__ is not None
        assert "Business Unit: execution" in core.__doc__
        assert "Status: current" in core.__doc__

    def test_all_exports_defined(self):
        """Test that __all__ is defined with expected exports."""
        from the_alchemiser.execution_v2 import core

        assert hasattr(core, "__all__")
        expected_exports = {
            "ExecutionManager",
            "ExecutionTracker",
            "Executor",
            "SettlementMonitor",
        }
        assert set(core.__all__) == expected_exports

    def test_execution_manager_importable(self):
        """Test that ExecutionManager can be imported from core."""
        from the_alchemiser.execution_v2.core import ExecutionManager

        assert ExecutionManager is not None
        assert hasattr(ExecutionManager, "__init__")

    def test_execution_tracker_importable(self):
        """Test that ExecutionTracker can be imported from core."""
        from the_alchemiser.execution_v2.core import ExecutionTracker

        assert ExecutionTracker is not None
        assert hasattr(ExecutionTracker, "__init__")

    def test_executor_importable(self):
        """Test that Executor can be imported from core."""
        from the_alchemiser.execution_v2.core import Executor

        assert Executor is not None
        assert hasattr(Executor, "__init__")

    def test_settlement_monitor_importable(self):
        """Test that SettlementMonitor can be imported from core."""
        from the_alchemiser.execution_v2.core import SettlementMonitor

        assert SettlementMonitor is not None
        assert hasattr(SettlementMonitor, "__init__")

    def test_all_classes_importable_together(self):
        """Test that all exported classes can be imported together."""
        from the_alchemiser.execution_v2.core import (
            ExecutionManager,
            ExecutionTracker,
            Executor,
            SettlementMonitor,
        )

        # Verify they are all valid classes
        assert ExecutionManager is not None
        assert ExecutionTracker is not None
        assert Executor is not None
        assert SettlementMonitor is not None

    def test_repeated_imports_return_same_object(self):
        """Test that repeated imports return the same class object."""
        from the_alchemiser.execution_v2.core import ExecutionManager as EM1
        from the_alchemiser.execution_v2.core import ExecutionManager as EM2

        assert EM1 is EM2

    def test_invalid_attribute_raises_attribute_error(self):
        """Test that accessing invalid attributes raises AttributeError."""
        from the_alchemiser.execution_v2 import core

        with pytest.raises(AttributeError):
            _ = core.NonExistentClass

    def test_module_is_a_package(self):
        """Test that core is a package (has __path__)."""
        from the_alchemiser.execution_v2 import core

        assert hasattr(core, "__path__")
        assert core.__path__ is not None

    def test_module_has_correct_name(self):
        """Test that core module has correct __name__."""
        from the_alchemiser.execution_v2 import core

        assert core.__name__ == "the_alchemiser.execution_v2.core"

    def test_module_file_location(self):
        """Test that core module __file__ points to correct location."""
        from the_alchemiser.execution_v2 import core

        assert core.__file__ is not None
        assert "__init__.py" in core.__file__
        assert "execution_v2/core" in core.__file__

    def test_all_exports_are_actually_exported(self):
        """Test that all items in __all__ are actually accessible."""
        from the_alchemiser.execution_v2 import core

        for export_name in core.__all__:
            assert hasattr(core, export_name), f"{export_name} not found in module"
            exported_item = getattr(core, export_name)
            assert exported_item is not None

    def test_docstring_describes_purpose(self):
        """Test that docstring describes module purpose."""
        from the_alchemiser.execution_v2 import core

        assert "execution" in core.__doc__.lower()
        assert "core" in core.__doc__.lower() or "orchestration" in core.__doc__.lower()
