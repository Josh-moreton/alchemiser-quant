"""Business Unit: shared | Status: current

Unit tests for base result DTOs.

Tests DTO validation, constraints, immutability, and the success/error pattern.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.base import Result, ResultDTO


class TestResult:
    """Test Result base DTO."""

    def test_success_case(self):
        """Test creation of successful result."""
        result = Result(success=True)
        assert result.success is True
        assert result.error is None
        assert result.is_success is True

    def test_error_case(self):
        """Test creation of failed result."""
        result = Result(success=False, error="Operation failed")
        assert result.success is False
        assert result.error == "Operation failed"
        assert result.is_success is False

    def test_is_success_property(self):
        """Test is_success property mirrors success field."""
        result_success = Result(success=True)
        result_error = Result(success=False, error="Error")

        assert result_success.is_success is True
        assert result_error.is_success is False

    def test_immutability(self):
        """Test that Result is frozen and cannot be modified."""
        result = Result(success=True)

        with pytest.raises(ValidationError):
            result.success = False  # type: ignore

        with pytest.raises(ValidationError):
            result.error = "Cannot modify"  # type: ignore

    def test_strict_validation_bool(self):
        """Test strict validation rejects non-bool for success."""
        with pytest.raises(ValidationError) as exc_info:
            Result(success="true")  # type: ignore

        assert "Input should be a valid boolean" in str(exc_info.value)

    def test_strict_validation_error(self):
        """Test strict validation rejects non-string for error."""
        with pytest.raises(ValidationError) as exc_info:
            Result(success=False, error=123)  # type: ignore

        assert "Input should be a valid string" in str(exc_info.value)

    def test_error_field_optional(self):
        """Test error field defaults to None."""
        result = Result(success=True)
        assert result.error is None

    def test_allows_inconsistent_state_success_with_error(self):
        """Test that Result allows success=True with error message.

        This documents current behavior. Consider adding validation
        to enforce consistency in future versions.
        """
        # Currently allowed (no validation):
        result = Result(success=True, error="Unexpected state")
        assert result.success is True
        assert result.error == "Unexpected state"

    def test_allows_inconsistent_state_failure_without_error(self):
        """Test that Result allows success=False without error message.

        This documents current behavior. Consider adding validation
        to enforce consistency in future versions.
        """
        # Currently allowed (no validation):
        result = Result(success=False)
        assert result.success is False
        assert result.error is None

    def test_model_dump(self):
        """Test Pydantic serialization."""
        result = Result(success=False, error="Test error")
        data = result.model_dump()

        assert data == {"success": False, "error": "Test error"}

    def test_model_dump_json(self):
        """Test JSON serialization."""
        result = Result(success=True)
        json_str = result.model_dump_json()

        assert '"success":true' in json_str
        assert '"error":null' in json_str

    def test_required_field_validation(self):
        """Test that success field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Result()  # type: ignore

        assert "Field required" in str(exc_info.value)
        assert "success" in str(exc_info.value)


class TestResultDTO:
    """Test ResultDTO backward compatibility alias."""

    def test_resultdto_is_result(self):
        """Test ResultDTO is an alias for Result."""
        assert ResultDTO is Result

    def test_resultdto_usage(self):
        """Test ResultDTO can be used like Result."""
        result = ResultDTO(success=True)
        assert isinstance(result, Result)
        assert result.success is True

    def test_resultdto_error_case(self):
        """Test ResultDTO works with error field."""
        result = ResultDTO(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"


class TestResultSubclassing:
    """Test Result as a base class for domain DTOs."""

    def test_subclass_inherits_success_error(self):
        """Test subclass inherits success/error fields."""
        from pydantic import ConfigDict

        class CustomResult(Result):
            model_config = ConfigDict(
                strict=True,
                frozen=True,
                validate_assignment=True,
            )
            value: int

        result = CustomResult(success=True, value=42)
        assert result.success is True
        assert result.error is None
        assert result.value == 42
        assert result.is_success is True

    def test_subclass_can_add_fields(self):
        """Test subclass can add domain-specific fields."""
        from pydantic import ConfigDict

        class PriceResult(Result):
            model_config = ConfigDict(
                strict=True,
                frozen=True,
                validate_assignment=True,
            )
            symbol: str | None = None
            price: Decimal | None = None

        result = PriceResult(success=True, symbol="AAPL", price=Decimal("150.00"))
        assert result.success is True
        assert result.symbol == "AAPL"
        assert result.price == Decimal("150.00")

    def test_subclass_immutability(self):
        """Test subclass inherits immutability."""
        from pydantic import ConfigDict

        class CustomResult(Result):
            model_config = ConfigDict(
                strict=True,
                frozen=True,
                validate_assignment=True,
            )
            value: int

        result = CustomResult(success=True, value=42)

        with pytest.raises(ValidationError):
            result.success = False  # type: ignore

        with pytest.raises(ValidationError):
            result.value = 99  # type: ignore

    def test_subclass_strict_validation(self):
        """Test subclass inherits strict validation."""
        from pydantic import ConfigDict

        class CustomResult(Result):
            model_config = ConfigDict(
                strict=True,
                frozen=True,
                validate_assignment=True,
            )
            value: int

        # Strict mode should reject string for int
        with pytest.raises(ValidationError) as exc_info:
            CustomResult(success=True, value="42")  # type: ignore

        assert "Input should be a valid integer" in str(exc_info.value)

    def test_subclass_with_error(self):
        """Test subclass can use error field."""
        from pydantic import ConfigDict

        class OperationResult(Result):
            model_config = ConfigDict(
                strict=True,
                frozen=True,
                validate_assignment=True,
            )
            operation_id: str | None = None

        result = OperationResult(success=False, error="Operation failed", operation_id="op-123")
        assert result.success is False
        assert result.error == "Operation failed"
        assert result.operation_id == "op-123"
        assert result.is_success is False
