"""Business Unit: execution | Status: current.

Unit tests for execution_v2/utils/__init__.py module interface.

Tests that the utils facade properly exports all intended classes and utilities,
and that the public API is stable and complete.
"""

from typing import Any

import pytest


class TestExecutionUtilsInit:
    """Test execution_v2.utils module interface."""

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported successfully."""
        from the_alchemiser.execution_v2 import utils

        for export_name in utils.__all__:
            assert hasattr(utils, export_name), f"{export_name} not found in utils module"

    def test_exports_match_all_declaration(self) -> None:
        """Test that actual exports match __all__ declaration."""
        from the_alchemiser.execution_v2 import utils

        expected_exports = set(utils.__all__)
        # Exclude submodule names that are imported but not in __all__
        actual_exports = {
            name
            for name in dir(utils)
            if not name.startswith("_")
            and name not in ["execution_validator", "liquidity_analysis", "position_utils"]
        }

        assert expected_exports == actual_exports, (
            f"Mismatch between __all__ and actual exports.\n"
            f"Missing: {expected_exports - actual_exports}\n"
            f"Extra: {actual_exports - expected_exports}"
        )

    def test_star_import_behavior(self) -> None:
        """Test that star import only imports items in __all__."""
        namespace: dict[str, Any] = {}
        exec("from the_alchemiser.execution_v2.utils import *", namespace)

        # Remove builtins
        imported = {k for k in namespace if not k.startswith("_")}

        from the_alchemiser.execution_v2 import utils

        expected = set(utils.__all__)

        assert imported == expected, f"Star import mismatch: {imported} != {expected}"

    def test_execution_validation_error_can_be_raised(self) -> None:
        """Test that ExecutionValidationError can be instantiated and raised."""
        from the_alchemiser.execution_v2.utils import ExecutionValidationError

        error = ExecutionValidationError("Test error", symbol="AAPL", code="TEST")
        assert error.symbol == "AAPL"
        assert error.code == "TEST"
        assert "Test error" in str(error)

        with pytest.raises(ExecutionValidationError) as exc_info:
            raise error

        assert "Test error" in str(exc_info.value)
        assert exc_info.value.symbol == "AAPL"
        assert exc_info.value.code == "TEST"

    def test_type_preservation(self) -> None:
        """Test that imported classes are the same as their source module classes."""
        from the_alchemiser.execution_v2 import utils
        from the_alchemiser.execution_v2.utils import (
            execution_validator,
            liquidity_analysis,
            position_utils,
        )

        # Verify classes are the same objects (not copies)
        assert utils.ExecutionValidator is execution_validator.ExecutionValidator
        assert utils.ExecutionValidationError is execution_validator.ExecutionValidationError
        assert utils.OrderValidationResult is execution_validator.OrderValidationResult

        assert utils.LiquidityAnalyzer is liquidity_analysis.LiquidityAnalyzer
        assert utils.LiquidityAnalysis is liquidity_analysis.LiquidityAnalysis

        assert utils.PositionUtils is position_utils.PositionUtils

    def test_submodule_names_accessible_but_not_in_all(self) -> None:
        """Test that submodule names are accessible but not in __all__."""
        from the_alchemiser.execution_v2 import utils

        # Submodules should be accessible (they're imported)
        assert hasattr(utils, "execution_validator")
        assert hasattr(utils, "liquidity_analysis")
        assert hasattr(utils, "position_utils")

        # But they should NOT be in __all__ (internal use)
        assert "execution_validator" not in utils.__all__
        assert "liquidity_analysis" not in utils.__all__
        assert "position_utils" not in utils.__all__

    def test_all_list_contents(self) -> None:
        """Test that __all__ contains exactly the expected exports."""
        from the_alchemiser.execution_v2 import utils

        expected_exports = {
            "ExecutionValidationError",
            "ExecutionValidator",
            "LiquidityAnalysis",
            "LiquidityAnalyzer",
            "OrderValidationResult",
            "PositionUtils",
        }

        actual_exports = set(utils.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ contents unexpected.\n"
            f"Expected: {sorted(expected_exports)}\n"
            f"Actual: {sorted(actual_exports)}\n"
            f"Missing: {expected_exports - actual_exports}\n"
            f"Extra: {actual_exports - expected_exports}"
        )

    def test_individual_imports(self) -> None:
        """Test that each export can be imported individually."""
        # Test exception
        from the_alchemiser.execution_v2.utils import ExecutionValidationError

        assert issubclass(ExecutionValidationError, Exception)

        # Test validator classes
        from the_alchemiser.execution_v2.utils import ExecutionValidator, OrderValidationResult

        assert ExecutionValidator is not None
        assert OrderValidationResult is not None

        # Test liquidity classes
        from the_alchemiser.execution_v2.utils import LiquidityAnalysis, LiquidityAnalyzer

        assert LiquidityAnalysis is not None
        assert LiquidityAnalyzer is not None

        # Test position utils
        from the_alchemiser.execution_v2.utils import PositionUtils

        assert PositionUtils is not None

    def test_no_repeg_monitoring_in_public_api(self) -> None:
        """Test that RepegMonitoringService is NOT in public API (intentional)."""
        from the_alchemiser.execution_v2 import utils

        # RepegMonitoringService should NOT be in __all__ (internal use only)
        assert "RepegMonitoringService" not in utils.__all__

        # Verify the service is NOT directly accessible from utils
        assert not hasattr(utils, "RepegMonitoringService")
