"""Business Unit: orchestration | Status: current

Unit tests for orchestration module __init__.py.

Tests lazy import behavior and module attribute access patterns.
"""

import pytest


class TestOrchestrationInit:
    """Test orchestration __init__.py lazy imports and attributes."""

    def test_lazy_import_event_driven_orchestrator(self):
        """Test that EventDrivenOrchestrator can be imported lazily."""
        from the_alchemiser.orchestration import EventDrivenOrchestrator

        assert EventDrivenOrchestrator is not None
        assert EventDrivenOrchestrator.__name__ == "EventDrivenOrchestrator"

    def test_lazy_import_workflow_state(self):
        """Test that WorkflowState enum can be imported lazily."""
        from the_alchemiser.orchestration import WorkflowState

        assert WorkflowState is not None
        # Verify it's an Enum
        from enum import Enum

        assert issubclass(WorkflowState, Enum)
        # Verify expected states exist
        assert hasattr(WorkflowState, "RUNNING")
        assert hasattr(WorkflowState, "FAILED")
        assert hasattr(WorkflowState, "COMPLETED")

    def test_workflow_state_enum_values(self):
        """Test WorkflowState enum has correct values."""
        from the_alchemiser.orchestration import WorkflowState

        assert WorkflowState.RUNNING.value == "running"
        assert WorkflowState.FAILED.value == "failed"
        assert WorkflowState.COMPLETED.value == "completed"

    def test_invalid_attribute_raises_attribute_error(self):
        """Test that accessing invalid attributes raises AttributeError."""
        import the_alchemiser.orchestration as orchestration_module

        with pytest.raises(AttributeError) as exc_info:
            _ = orchestration_module.NonExistentClass

        error_message = str(exc_info.value)
        assert "has no attribute 'NonExistentClass'" in error_message

    def test_all_exports_defined(self):
        """Test that __all__ contains expected exports."""
        from the_alchemiser import orchestration

        assert hasattr(orchestration, "__all__")
        expected_exports = {"EventDrivenOrchestrator", "WorkflowState"}
        assert set(orchestration.__all__) == expected_exports

    def test_repeated_imports_return_same_object(self):
        """Test that repeated lazy imports return the same class object."""
        from the_alchemiser.orchestration import EventDrivenOrchestrator as EDO1
        from the_alchemiser.orchestration import EventDrivenOrchestrator as EDO2

        assert EDO1 is EDO2

    def test_module_docstring_exists(self):
        """Test that the module has proper docstring."""
        from the_alchemiser import orchestration

        assert orchestration.__doc__ is not None
        assert "Business Unit: orchestration" in orchestration.__doc__
        assert "Status: current" in orchestration.__doc__
