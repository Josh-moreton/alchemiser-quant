"""Business Unit: shared | Status: current.

Tests for error type definitions, constants, and re-exports.

This module provides comprehensive test coverage for the_alchemiser/shared/errors/error_types.py,
ensuring that error severity levels, error categories, type aliases, and schema re-exports
are correct and consistent with the schemas module.
"""

# ruff: noqa: ANN201, S101
from __future__ import annotations

from the_alchemiser.shared.errors.error_types import (
    ContextDict,
    ErrorCategory,
    ErrorData,
    ErrorDetailInfo,
    ErrorList,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSeverity,
    ErrorSummaryData,
)


class TestErrorSeverity:
    """Test ErrorSeverity constant class."""

    def test_low_severity_value(self):
        """Test LOW constant has correct value."""
        assert ErrorSeverity.LOW == "low"

    def test_medium_severity_value(self):
        """Test MEDIUM constant has correct value."""
        assert ErrorSeverity.MEDIUM == "medium"

    def test_high_severity_value(self):
        """Test HIGH constant has correct value."""
        assert ErrorSeverity.HIGH == "high"

    def test_critical_severity_value(self):
        """Test CRITICAL constant has correct value."""
        assert ErrorSeverity.CRITICAL == "critical"

    def test_all_severity_levels_are_strings(self):
        """Test that all severity levels are string values."""
        assert isinstance(ErrorSeverity.LOW, str)
        assert isinstance(ErrorSeverity.MEDIUM, str)
        assert isinstance(ErrorSeverity.HIGH, str)
        assert isinstance(ErrorSeverity.CRITICAL, str)

    def test_severity_values_are_lowercase(self):
        """Test that all severity values are lowercase."""
        assert ErrorSeverity.LOW.islower()
        assert ErrorSeverity.MEDIUM.islower()
        assert ErrorSeverity.HIGH.islower()
        assert ErrorSeverity.CRITICAL.islower()

    def test_severity_values_match_schema_literal(self):
        """Test severity values match SeverityType Literal in schemas.errors."""
        # SeverityType = Literal["low", "medium", "high", "critical"]
        valid_values = {"low", "medium", "high", "critical"}
        actual_values = {
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        }
        assert actual_values == valid_values

    def test_severity_class_has_docstring(self):
        """Test ErrorSeverity class has a docstring."""
        assert ErrorSeverity.__doc__ is not None
        assert len(ErrorSeverity.__doc__) > 0


class TestErrorCategory:
    """Test ErrorCategory constant class."""

    def test_critical_category_value(self):
        """Test CRITICAL constant has correct value."""
        assert ErrorCategory.CRITICAL == "critical"

    def test_trading_category_value(self):
        """Test TRADING constant has correct value."""
        assert ErrorCategory.TRADING == "trading"

    def test_data_category_value(self):
        """Test DATA constant has correct value."""
        assert ErrorCategory.DATA == "data"

    def test_strategy_category_value(self):
        """Test STRATEGY constant has correct value."""
        assert ErrorCategory.STRATEGY == "strategy"

    def test_configuration_category_value(self):
        """Test CONFIGURATION constant has correct value."""
        assert ErrorCategory.CONFIGURATION == "configuration"

    def test_notification_category_value(self):
        """Test NOTIFICATION constant has correct value."""
        assert ErrorCategory.NOTIFICATION == "notification"

    def test_warning_category_value(self):
        """Test WARNING constant has correct value."""
        assert ErrorCategory.WARNING == "warning"

    def test_all_category_values_are_strings(self):
        """Test that all category values are strings."""
        assert isinstance(ErrorCategory.CRITICAL, str)
        assert isinstance(ErrorCategory.TRADING, str)
        assert isinstance(ErrorCategory.DATA, str)
        assert isinstance(ErrorCategory.STRATEGY, str)
        assert isinstance(ErrorCategory.CONFIGURATION, str)
        assert isinstance(ErrorCategory.NOTIFICATION, str)
        assert isinstance(ErrorCategory.WARNING, str)

    def test_category_values_are_lowercase(self):
        """Test that all category values are lowercase."""
        assert ErrorCategory.CRITICAL.islower()
        assert ErrorCategory.TRADING.islower()
        assert ErrorCategory.DATA.islower()
        assert ErrorCategory.STRATEGY.islower()
        assert ErrorCategory.CONFIGURATION.islower()
        assert ErrorCategory.NOTIFICATION.islower()
        assert ErrorCategory.WARNING.islower()

    def test_category_values_match_schema_literal(self):
        """Test category values match ErrorCategoryType Literal in schemas.errors."""
        # ErrorCategoryType = Literal["critical", "trading", "data", "strategy",
        #                             "configuration", "notification", "warning"]
        valid_values = {
            "critical",
            "trading",
            "data",
            "strategy",
            "configuration",
            "notification",
            "warning",
        }
        actual_values = {
            ErrorCategory.CRITICAL,
            ErrorCategory.TRADING,
            ErrorCategory.DATA,
            ErrorCategory.STRATEGY,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.NOTIFICATION,
            ErrorCategory.WARNING,
        }
        assert actual_values == valid_values

    def test_category_class_has_docstring(self):
        """Test ErrorCategory class has a docstring."""
        assert ErrorCategory.__doc__ is not None
        assert len(ErrorCategory.__doc__) > 0


class TestTypeAliases:
    """Test type aliases for error data structures."""

    def test_error_data_type_alias_exists(self):
        """Test ErrorData type alias is defined."""
        # Can't directly test type aliases at runtime, but can test they're in __all__
        from the_alchemiser.shared.errors import error_types

        assert "ErrorData" in error_types.__all__

    def test_error_data_accepts_valid_dict(self):
        """Test ErrorData type alias accepts valid dictionary."""
        # This is a type hint test - validates structure
        data: ErrorData = {
            "string_key": "value",
            "int_key": 42,
            "float_key": 3.14,
            "bool_key": True,
            "none_key": None,
        }
        assert isinstance(data, dict)
        assert len(data) == 5

    def test_error_list_type_alias_exists(self):
        """Test ErrorList type alias is defined."""
        from the_alchemiser.shared.errors import error_types

        assert "ErrorList" in error_types.__all__

    def test_error_list_accepts_list_of_dicts(self):
        """Test ErrorList type alias accepts list of ErrorData."""
        error_list: ErrorList = [
            {"error": "first", "code": 1},
            {"error": "second", "code": 2},
        ]
        assert isinstance(error_list, list)
        assert len(error_list) == 2

    def test_context_dict_type_alias_exists(self):
        """Test ContextDict type alias is defined."""
        from the_alchemiser.shared.errors import error_types

        assert "ContextDict" in error_types.__all__

    def test_context_dict_accepts_valid_dict(self):
        """Test ContextDict type alias accepts valid dictionary."""
        context: ContextDict = {
            "module": "strategy_v2",
            "function": "generate_signals",
            "line": 123,
            "retries": 3,
            "success": False,
        }
        assert isinstance(context, dict)
        assert context["module"] == "strategy_v2"

    def test_error_data_and_context_dict_have_same_structure(self):
        """Test that ErrorData and ContextDict have compatible structures."""
        # Both are dict[str, str | int | float | bool | None]
        # This test validates they can be used interchangeably if needed
        data: ErrorData = {"key": "value", "count": 1}
        context: ContextDict = {"key": "value", "count": 1}

        # Both should accept the same structure
        assert isinstance(data, dict)
        assert isinstance(context, dict)


class TestSchemaReExports:
    """Test that schema classes are correctly re-exported."""

    def test_error_detail_info_is_imported(self):
        """Test ErrorDetailInfo is available from error_types."""
        # Already imported at module level
        assert ErrorDetailInfo is not None

    def test_error_detail_info_is_pydantic_model(self):
        """Test ErrorDetailInfo is a Pydantic BaseModel."""
        from pydantic import BaseModel

        # ErrorDetailInfo should be a Pydantic model class
        assert issubclass(ErrorDetailInfo, BaseModel)

    def test_error_summary_data_is_imported(self):
        """Test ErrorSummaryData is available from error_types."""
        assert ErrorSummaryData is not None

    def test_error_summary_data_is_pydantic_model(self):
        """Test ErrorSummaryData is a Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(ErrorSummaryData, BaseModel)

    def test_error_report_summary_is_imported(self):
        """Test ErrorReportSummary is available from error_types."""
        assert ErrorReportSummary is not None

    def test_error_report_summary_is_pydantic_model(self):
        """Test ErrorReportSummary is a Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(ErrorReportSummary, BaseModel)

    def test_error_notification_data_is_imported(self):
        """Test ErrorNotificationData is available from error_types."""
        assert ErrorNotificationData is not None

    def test_error_notification_data_is_pydantic_model(self):
        """Test ErrorNotificationData is a Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(ErrorNotificationData, BaseModel)

    def test_re_exported_schemas_match_original_imports(self):
        """Test re-exported schemas are same as original imports."""
        from the_alchemiser.shared.schemas.errors import (
            ErrorDetailInfo as OriginalErrorDetailInfo,
        )
        from the_alchemiser.shared.schemas.errors import (
            ErrorNotificationData as OriginalErrorNotificationData,
        )
        from the_alchemiser.shared.schemas.errors import (
            ErrorReportSummary as OriginalErrorReportSummary,
        )
        from the_alchemiser.shared.schemas.errors import (
            ErrorSummaryData as OriginalErrorSummaryData,
        )

        # Re-exports should be the exact same class objects
        assert ErrorDetailInfo is OriginalErrorDetailInfo
        assert ErrorSummaryData is OriginalErrorSummaryData
        assert ErrorReportSummary is OriginalErrorReportSummary
        assert ErrorNotificationData is OriginalErrorNotificationData


class TestModuleExports:
    """Test __all__ export list."""

    def test_all_exports_are_defined(self):
        """Test that all items in __all__ are actually defined."""
        from the_alchemiser.shared.errors import error_types

        for export_name in error_types.__all__:
            assert hasattr(error_types, export_name), f"{export_name} not found"

    def test_all_exports_list_contents(self):
        """Test __all__ contains expected exports."""
        from the_alchemiser.shared.errors import error_types

        expected_exports = {
            "ContextDict",
            "ErrorCategory",
            "ErrorData",
            "ErrorDetailInfo",
            "ErrorList",
            "ErrorNotificationData",
            "ErrorReportSummary",
            "ErrorSeverity",
            "ErrorSummaryData",
        }
        actual_exports = set(error_types.__all__)
        assert actual_exports == expected_exports

    def test_all_exports_count(self):
        """Test __all__ has expected number of exports."""
        from the_alchemiser.shared.errors import error_types

        # Should have exactly 9 exports
        assert len(error_types.__all__) == 9

    def test_no_duplicate_exports(self):
        """Test __all__ has no duplicate entries."""
        from the_alchemiser.shared.errors import error_types

        exports_list = error_types.__all__
        exports_set = set(exports_list)
        assert len(exports_list) == len(exports_set), "Duplicate exports found"


class TestConstantImmutability:
    """Test that constants maintain their values (convention-based)."""

    def test_severity_constants_can_be_read(self):
        """Test that severity constants can be accessed."""
        # This is a smoke test - constants should be readable
        _ = ErrorSeverity.LOW
        _ = ErrorSeverity.MEDIUM
        _ = ErrorSeverity.HIGH
        _ = ErrorSeverity.CRITICAL

    def test_category_constants_can_be_read(self):
        """Test that category constants can be accessed."""
        _ = ErrorCategory.CRITICAL
        _ = ErrorCategory.TRADING
        _ = ErrorCategory.DATA
        _ = ErrorCategory.STRATEGY
        _ = ErrorCategory.CONFIGURATION
        _ = ErrorCategory.NOTIFICATION
        _ = ErrorCategory.WARNING


class TestConsistencyWithSchemas:
    """Test consistency between error_types constants and schemas definitions."""

    def test_severity_values_compatible_with_error_notification_data(self):
        """Test ErrorSeverity values can be used in ErrorNotificationData."""
        # All severity values should be valid for ErrorNotificationData.severity field
        for severity_value in [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]:
            notification = ErrorNotificationData(
                severity=severity_value,  # type: ignore[arg-type]
                priority="urgent",
                title="Test Error",
                error_report="Test report",
                html_content="<p>Test</p>",
                success=True,
                email_sent=True,
            )
            assert notification.severity == severity_value

    def test_category_values_compatible_with_error_detail_info(self):
        """Test ErrorCategory values can be used in ErrorDetailInfo."""
        from datetime import UTC, datetime

        # All category values should be valid for ErrorDetailInfo.category field
        for category_value in [
            ErrorCategory.CRITICAL,
            ErrorCategory.TRADING,
            ErrorCategory.DATA,
            ErrorCategory.STRATEGY,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.NOTIFICATION,
            ErrorCategory.WARNING,
        ]:
            detail = ErrorDetailInfo(
                error_type="TestError",
                error_message="Test message",
                category=category_value,  # type: ignore[arg-type]
                context="test_context",
                component="test_component",
                timestamp=datetime.now(UTC).isoformat(),
                traceback="Test traceback",
            )
            assert detail.category == category_value


class TestImportFromPublicAPI:
    """Test that error_types exports are available from shared.errors public API."""

    def test_error_severity_available_from_shared_errors(self):
        """Test ErrorSeverity can be imported from shared.errors."""
        from the_alchemiser.shared.errors import ErrorSeverity as PublicErrorSeverity

        assert PublicErrorSeverity is ErrorSeverity

    def test_error_category_available_from_shared_errors(self):
        """Test ErrorCategory can be imported from shared.errors."""
        from the_alchemiser.shared.errors import ErrorCategory as PublicErrorCategory

        assert PublicErrorCategory is ErrorCategory

    def test_error_notification_data_available_from_shared_errors(self):
        """Test ErrorNotificationData can be imported from shared.errors."""
        from the_alchemiser.shared.errors import (
            ErrorNotificationData as PublicErrorNotificationData,
        )

        assert PublicErrorNotificationData is ErrorNotificationData
