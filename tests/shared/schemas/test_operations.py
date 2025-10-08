"""Business Unit: shared | Status: current.

Tests for operation result DTOs.

This module tests the operation result DTOs including instantiation,
validation, immutability, and backward compatibility.
"""

import warnings

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.operations import (
    OperationResult,
    OrderCancellationResult,
    OrderStatusResult,
    TerminalOrderError,
)


class TestTerminalOrderError:
    """Test TerminalOrderError enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert TerminalOrderError.ALREADY_FILLED.value == "already_filled"
        assert TerminalOrderError.ALREADY_CANCELLED.value == "already_cancelled"
        assert TerminalOrderError.ALREADY_REJECTED.value == "already_rejected"
        assert TerminalOrderError.ALREADY_EXPIRED.value == "already_expired"

    def test_enum_string_inheritance(self):
        """Test enum inherits from str for serialization."""
        assert isinstance(TerminalOrderError.ALREADY_FILLED, str)
        assert str(TerminalOrderError.ALREADY_FILLED) == "already_filled"

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert "already_filled" in [e.value for e in TerminalOrderError]
        assert "invalid_state" not in [e.value for e in TerminalOrderError]

    def test_enum_iteration(self):
        """Test enum can be iterated."""
        values = [e.value for e in TerminalOrderError]
        assert len(values) == 4
        assert all(isinstance(v, str) for v in values)


class TestOperationResult:
    """Test OperationResult DTO."""

    def test_success_result_no_details(self):
        """Test creating successful result without details."""
        result = OperationResult(success=True, error=None)
        assert result.success is True
        assert result.error is None
        assert result.details is None
        assert result.is_success is True

    def test_success_result_with_details(self):
        """Test creating successful result with details."""
        result = OperationResult(
            success=True, error=None, details={"key": "value", "count": 42}
        )
        assert result.success is True
        assert result.details == {"key": "value", "count": 42}
        assert result.details["key"] == "value"
        assert result.details["count"] == 42

    def test_error_result(self):
        """Test creating error result."""
        result = OperationResult(
            success=False,
            error="Operation failed",
            details={"reason": "timeout", "code": "500"},
        )
        assert result.success is False
        assert result.error == "Operation failed"
        assert result.details["reason"] == "timeout"
        assert result.details["code"] == "500"
        assert result.is_success is False

    def test_details_with_object_values(self):
        """Test details field accepts various object types."""
        result = OperationResult(
            success=True,
            details={
                "string": "value",
                "number": 123,
                "float": 45.67,
                "bool": True,
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
            },
        )
        assert result.details["string"] == "value"
        assert result.details["number"] == 123
        assert result.details["bool"] is True
        assert result.details["list"] == [1, 2, 3]

    def test_immutability(self):
        """Test result is immutable (frozen=True)."""
        result = OperationResult(success=True)
        with pytest.raises(ValidationError, match="frozen"):
            result.success = False

    def test_immutability_nested_details(self):
        """Test cannot modify details after creation."""
        result = OperationResult(success=True, details={"key": "value"})
        with pytest.raises(ValidationError, match="frozen"):
            result.details = {"new": "dict"}

    def test_strict_validation_success_field(self):
        """Test strict validation rejects type coercion for success."""
        with pytest.raises(ValidationError, match="bool"):
            OperationResult(success="true")  # String not bool

    def test_strict_validation_error_field(self):
        """Test strict validation rejects type coercion for error."""
        with pytest.raises(ValidationError, match="str"):
            OperationResult(success=False, error=123)  # Int not str

    def test_serialization(self):
        """Test DTO can be serialized to dict."""
        result = OperationResult(
            success=True, error=None, details={"key": "value"}
        )
        data = result.model_dump()
        assert data == {
            "success": True,
            "error": None,
            "details": {"key": "value"},
        }

    def test_deserialization(self):
        """Test DTO can be created from dict."""
        data = {"success": False, "error": "Failed", "details": {"code": "500"}}
        result = OperationResult.model_validate(data)
        assert result.success is False
        assert result.error == "Failed"
        assert result.details["code"] == "500"


class TestOrderCancellationResult:
    """Test OrderCancellationResult DTO."""

    def test_successful_cancellation(self):
        """Test successful cancellation."""
        result = OrderCancellationResult(
            success=True, error=None, order_id="order-123"
        )
        assert result.success is True
        assert result.order_id == "order-123"
        assert result.error is None

    def test_failed_cancellation(self):
        """Test failed cancellation."""
        result = OrderCancellationResult(
            success=False, error="Order not found", order_id="order-456"
        )
        assert result.success is False
        assert result.error == "Order not found"
        assert result.order_id == "order-456"

    def test_terminal_state_cancellation(self):
        """Test cancellation of already terminal order."""
        result = OrderCancellationResult(
            success=True, error="already_filled", order_id="order-789"
        )
        assert result.success is True
        assert result.error == "already_filled"
        assert result.order_id == "order-789"

    def test_cancellation_without_order_id(self):
        """Test cancellation result without order_id."""
        result = OrderCancellationResult(success=False, error="Invalid request")
        assert result.success is False
        assert result.order_id is None

    def test_order_id_validator_rejects_empty_string(self):
        """Test validator rejects empty order_id."""
        with pytest.raises(ValidationError, match="order_id must not be empty"):
            OrderCancellationResult(success=True, order_id="")

    def test_order_id_validator_rejects_whitespace_only(self):
        """Test validator rejects whitespace-only order_id."""
        with pytest.raises(ValidationError, match="order_id must not be empty"):
            OrderCancellationResult(success=True, order_id="   ")

    def test_order_id_validator_accepts_valid_string(self):
        """Test validator accepts valid order_id."""
        result = OrderCancellationResult(success=True, order_id="order-123")
        assert result.order_id == "order-123"

    def test_order_id_validator_accepts_none(self):
        """Test validator accepts None for order_id."""
        result = OrderCancellationResult(success=True, order_id=None)
        assert result.order_id is None

    def test_immutability(self):
        """Test result is immutable."""
        result = OrderCancellationResult(success=True, order_id="order-123")
        with pytest.raises(ValidationError, match="frozen"):
            result.success = False

    def test_serialization(self):
        """Test DTO can be serialized."""
        result = OrderCancellationResult(
            success=True, error=None, order_id="order-123"
        )
        data = result.model_dump()
        assert data == {"success": True, "error": None, "order_id": "order-123"}

    def test_deserialization(self):
        """Test DTO can be deserialized."""
        data = {"success": False, "error": "Not found", "order_id": "order-456"}
        result = OrderCancellationResult.model_validate(data)
        assert result.success is False
        assert result.error == "Not found"
        assert result.order_id == "order-456"


class TestOrderStatusResult:
    """Test OrderStatusResult DTO."""

    def test_successful_status_query(self):
        """Test successful status query."""
        result = OrderStatusResult(
            success=True, error=None, order_id="order-123", status="filled"
        )
        assert result.success is True
        assert result.order_id == "order-123"
        assert result.status == "filled"
        assert result.error is None

    def test_failed_status_query(self):
        """Test failed status query."""
        result = OrderStatusResult(
            success=False, error="Order not found", order_id="order-456", status=None
        )
        assert result.success is False
        assert result.error == "Order not found"
        assert result.order_id == "order-456"
        assert result.status is None

    def test_various_order_statuses(self):
        """Test result with various order statuses."""
        statuses = [
            "new",
            "partially_filled",
            "filled",
            "canceled",
            "expired",
            "rejected",
        ]
        for status in statuses:
            result = OrderStatusResult(
                success=True, order_id="order-123", status=status
            )
            assert result.status == status

    def test_status_query_without_order_id(self):
        """Test status query without order_id."""
        result = OrderStatusResult(success=False, error="Invalid request")
        assert result.success is False
        assert result.order_id is None
        assert result.status is None

    def test_order_id_validator_rejects_empty_string(self):
        """Test validator rejects empty order_id."""
        with pytest.raises(ValidationError, match="order_id must not be empty"):
            OrderStatusResult(success=True, order_id="", status="filled")

    def test_order_id_validator_rejects_whitespace_only(self):
        """Test validator rejects whitespace-only order_id."""
        with pytest.raises(ValidationError, match="order_id must not be empty"):
            OrderStatusResult(success=True, order_id="   ", status="filled")

    def test_order_id_validator_accepts_valid_string(self):
        """Test validator accepts valid order_id."""
        result = OrderStatusResult(success=True, order_id="order-123", status="new")
        assert result.order_id == "order-123"

    def test_order_id_validator_accepts_none(self):
        """Test validator accepts None for order_id."""
        result = OrderStatusResult(success=True, order_id=None, status="filled")
        assert result.order_id is None

    def test_immutability(self):
        """Test result is immutable."""
        result = OrderStatusResult(success=True, order_id="order-123", status="new")
        with pytest.raises(ValidationError, match="frozen"):
            result.success = False

    def test_serialization(self):
        """Test DTO can be serialized."""
        result = OrderStatusResult(
            success=True, error=None, order_id="order-123", status="filled"
        )
        data = result.model_dump()
        assert data == {
            "success": True,
            "error": None,
            "order_id": "order-123",
            "status": "filled",
        }

    def test_deserialization(self):
        """Test DTO can be deserialized."""
        data = {
            "success": True,
            "error": None,
            "order_id": "order-456",
            "status": "canceled",
        }
        result = OrderStatusResult.model_validate(data)
        assert result.success is True
        assert result.order_id == "order-456"
        assert result.status == "canceled"


class TestBackwardCompatibilityAliases:
    """Test backward compatibility aliases with deprecation warnings."""

    def test_operation_result_dto_alias_warns(self):
        """Test OperationResultDTO alias emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from the_alchemiser.shared.schemas.operations import OperationResultDTO

            # Should emit deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "OperationResultDTO is deprecated" in str(w[0].message)
            assert "3.0.0" in str(w[0].message)

            # Should still work
            assert OperationResultDTO is OperationResult

    def test_order_cancellation_dto_alias_warns(self):
        """Test OrderCancellationDTO alias emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from the_alchemiser.shared.schemas.operations import (
                OrderCancellationDTO,
            )

            # Should emit deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "OrderCancellationDTO is deprecated" in str(w[0].message)
            assert "3.0.0" in str(w[0].message)

            # Should still work
            assert OrderCancellationDTO is OrderCancellationResult

    def test_order_status_dto_alias_warns(self):
        """Test OrderStatusDTO alias emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from the_alchemiser.shared.schemas.operations import OrderStatusDTO

            # Should emit deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "OrderStatusDTO is deprecated" in str(w[0].message)
            assert "3.0.0" in str(w[0].message)

            # Should still work
            assert OrderStatusDTO is OrderStatusResult

    def test_aliases_still_functional(self):
        """Test that aliases still work for backward compatibility."""
        from the_alchemiser.shared.schemas.operations import (
            OperationResultDTO,
            OrderCancellationDTO,
            OrderStatusDTO,
        )

        # Suppress warnings for functionality test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Should be able to create instances
            op_result = OperationResultDTO(success=True)
            assert isinstance(op_result, OperationResult)

            cancel_result = OrderCancellationDTO(success=True, order_id="123")
            assert isinstance(cancel_result, OrderCancellationResult)

            status_result = OrderStatusDTO(
                success=True, order_id="123", status="filled"
            )
            assert isinstance(status_result, OrderStatusResult)


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_terminal_order_error_in_cancellation_result(self):
        """Test using TerminalOrderError values in OrderCancellationResult."""
        for error in TerminalOrderError:
            result = OrderCancellationResult(
                success=True, error=error.value, order_id="order-123"
            )
            assert result.success is True
            assert result.error == error.value

    def test_round_trip_serialization(self):
        """Test round-trip serialization/deserialization."""
        original = OrderCancellationResult(
            success=False, error="Network timeout", order_id="order-789"
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize from dict
        restored = OrderCancellationResult.model_validate(data)

        # Should be equal
        assert restored.success == original.success
        assert restored.error == original.error
        assert restored.order_id == original.order_id

    def test_json_serialization(self):
        """Test JSON serialization."""
        result = OperationResult(
            success=False, error="Failed", details={"code": "500", "message": "Error"}
        )

        # Serialize to JSON-compatible dict
        json_data = result.model_dump()

        # Should be JSON-serializable
        import json

        json_str = json.dumps(json_data)
        assert "Failed" in json_str
        assert "500" in json_str
