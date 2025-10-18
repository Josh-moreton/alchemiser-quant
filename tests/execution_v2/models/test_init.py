"""Business Unit: execution | Status: current.

Unit tests for execution_v2/models/__init__.py.

Tests module structure, documentation, imports, and accessibility patterns.
"""

import pytest


class TestExecutionV2ModelsInit:
    """Test execution_v2/models __init__.py module structure."""

    def test_module_docstring_exists(self):
        """Test that the module has proper docstring."""
        from the_alchemiser.execution_v2 import models

        assert models.__doc__ is not None
        assert "Business Unit: execution" in models.__doc__
        assert "Status: current" in models.__doc__

    def test_all_exports_defined(self):
        """Test that __all__ is defined with expected exports."""
        from the_alchemiser.execution_v2 import models

        assert hasattr(models, "__all__")
        expected_exports = {
            "ExecutionResult",
            "ExecutionStatus",
            "OrderResult",
            "SettlementDetails",
        }
        assert set(models.__all__) == expected_exports

    def test_execution_result_importable(self):
        """Test that ExecutionResult can be imported from models."""
        from the_alchemiser.execution_v2.models import ExecutionResult

        assert ExecutionResult is not None
        assert hasattr(ExecutionResult, "__init__")
        assert hasattr(ExecutionResult, "model_config")
        # Verify it's a Pydantic model
        assert hasattr(ExecutionResult, "model_validate")

    def test_order_result_importable(self):
        """Test that OrderResult can be imported from models."""
        from the_alchemiser.execution_v2.models import OrderResult

        assert OrderResult is not None
        assert hasattr(OrderResult, "__init__")
        assert hasattr(OrderResult, "model_config")
        # Verify it's a Pydantic model
        assert hasattr(OrderResult, "model_validate")

    def test_execution_status_importable(self):
        """Test that ExecutionStatus can be imported from models."""
        from the_alchemiser.execution_v2.models import ExecutionStatus

        assert ExecutionStatus is not None
        # Verify it's an Enum
        assert hasattr(ExecutionStatus, "SUCCESS")
        assert hasattr(ExecutionStatus, "PARTIAL_SUCCESS")
        assert hasattr(ExecutionStatus, "FAILURE")

    def test_execution_status_values(self):
        """Test ExecutionStatus enum values are correct."""
        from the_alchemiser.execution_v2.models import ExecutionStatus

        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.PARTIAL_SUCCESS.value == "partial_success"
        assert ExecutionStatus.FAILURE.value == "failure"

    def test_all_models_importable_together(self):
        """Test that all exported models can be imported together."""
        from the_alchemiser.execution_v2.models import (
            ExecutionResult,
            ExecutionStatus,
            OrderResult,
        )

        # Verify they are all valid
        assert ExecutionResult is not None
        assert ExecutionStatus is not None
        assert OrderResult is not None

    def test_repeated_imports_return_same_object(self):
        """Test that repeated imports return the same class object."""
        from the_alchemiser.execution_v2.models import ExecutionResult as ER1
        from the_alchemiser.execution_v2.models import ExecutionResult as ER2

        assert ER1 is ER2

    def test_invalid_attribute_raises_attribute_error(self):
        """Test that accessing invalid attributes raises AttributeError."""
        from the_alchemiser.execution_v2 import models

        with pytest.raises(AttributeError):
            _ = models.NonExistentClass

    def test_module_is_a_package(self):
        """Test that models is a package (has __path__)."""
        from the_alchemiser.execution_v2 import models

        assert hasattr(models, "__path__")
        assert models.__path__ is not None

    def test_module_has_correct_name(self):
        """Test that models module has correct __name__."""
        from the_alchemiser.execution_v2 import models

        assert models.__name__ == "the_alchemiser.execution_v2.models"

    def test_module_file_location(self):
        """Test that models module __file__ points to correct location."""
        from the_alchemiser.execution_v2 import models

        assert models.__file__ is not None
        assert "__init__.py" in models.__file__
        assert "execution_v2/models" in models.__file__

    def test_all_exports_are_actually_exported(self):
        """Test that all items in __all__ are actually accessible."""
        from the_alchemiser.execution_v2 import models

        for export_name in models.__all__:
            assert hasattr(models, export_name), f"{export_name} not found in module"
            exported_item = getattr(models, export_name)
            assert exported_item is not None

    def test_docstring_describes_purpose(self):
        """Test that docstring describes module purpose."""
        from the_alchemiser.execution_v2 import models

        docstring_lower = models.__doc__.lower()
        assert "models" in docstring_lower or "execution" in docstring_lower

    def test_execution_result_has_required_fields(self):
        """Test that ExecutionResult has all required fields."""
        from the_alchemiser.execution_v2.models import ExecutionResult

        # Check model fields exist
        assert "success" in ExecutionResult.model_fields
        assert "status" in ExecutionResult.model_fields
        assert "plan_id" in ExecutionResult.model_fields
        assert "correlation_id" in ExecutionResult.model_fields
        assert "orders" in ExecutionResult.model_fields

    def test_order_result_has_required_fields(self):
        """Test that OrderResult has all required fields."""
        from the_alchemiser.execution_v2.models import OrderResult

        # Check model fields exist
        assert "symbol" in OrderResult.model_fields
        assert "action" in OrderResult.model_fields
        assert "trade_amount" in OrderResult.model_fields
        assert "shares" in OrderResult.model_fields
        assert "success" in OrderResult.model_fields

    def test_models_are_frozen(self):
        """Test that exported models are immutable (frozen)."""
        from the_alchemiser.execution_v2.models import ExecutionResult, OrderResult

        # Check that models are configured as frozen
        assert ExecutionResult.model_config.get("frozen") is True
        assert OrderResult.model_config.get("frozen") is True

    def test_models_are_strict(self):
        """Test that exported models use strict validation."""
        from the_alchemiser.execution_v2.models import ExecutionResult, OrderResult

        # Check that models are configured as strict
        assert ExecutionResult.model_config.get("strict") is True
        assert OrderResult.model_config.get("strict") is True

    def test_import_from_submodule_still_works(self):
        """Test that direct imports from submodule still work."""
        from the_alchemiser.execution_v2.models.execution_result import (
            ExecutionResult,
            ExecutionStatus,
            OrderResult,
        )

        # Verify they work
        assert ExecutionResult is not None
        assert ExecutionStatus is not None
        assert OrderResult is not None

    def test_imports_from_package_and_submodule_are_same(self):
        """Test that imports from package and submodule return same objects."""
        from the_alchemiser.execution_v2.models import (
            ExecutionResult as ER1,
        )
        from the_alchemiser.execution_v2.models import (
            ExecutionStatus as ES1,
        )
        from the_alchemiser.execution_v2.models import (
            OrderResult as OR1,
        )
        from the_alchemiser.execution_v2.models.execution_result import (
            ExecutionResult as ER2,
        )
        from the_alchemiser.execution_v2.models.execution_result import (
            ExecutionStatus as ES2,
        )
        from the_alchemiser.execution_v2.models.execution_result import (
            OrderResult as OR2,
        )

        # Verify they are the same objects
        assert ER1 is ER2
        assert ES1 is ES2
        assert OR1 is OR2

    def test_no_import_star_used(self):
        """Test that the module doesn't use import * pattern."""
        import inspect

        from the_alchemiser.execution_v2 import models

        # Read the source file
        source = inspect.getsource(models)
        # Verify no 'import *' is used
        assert "import *" not in source
