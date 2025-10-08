"""Business Unit: shared | Status: current

Unit tests for broker schema DTOs.

Tests validation, constraints, immutability, serialization, and edge cases
for WebSocketStatus, WebSocketResult, and OrderExecutionResult.
"""

from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.broker import (
    OrderExecutionResult,
    WebSocketResult,
    WebSocketStatus,
)


class TestWebSocketStatus:
    """Test WebSocketStatus enum."""

    @pytest.mark.unit
    def test_enum_values(self):
        """Test that enum has expected values."""
        assert WebSocketStatus.COMPLETED == "completed"
        assert WebSocketStatus.TIMEOUT == "timeout"
        assert WebSocketStatus.ERROR == "error"

    @pytest.mark.unit
    def test_string_conversion(self):
        """Test that enum values can be compared as strings."""
        status = WebSocketStatus.COMPLETED
        assert status == "completed"
        assert status.value == "completed"


class TestWebSocketResult:
    """Test WebSocketResult DTO validation."""

    @pytest.mark.unit
    def test_valid_websocket_result(self):
        """Test creation of valid WebSocket result."""
        result = WebSocketResult(
            status=WebSocketStatus.COMPLETED,
            message="Operation completed successfully",
            completed_order_ids=["order1", "order2"],
            metadata={"duration_ms": 1500},
        )
        assert result.status == WebSocketStatus.COMPLETED
        assert result.message == "Operation completed successfully"
        assert result.completed_order_ids == ["order1", "order2"]
        assert result.metadata == {"duration_ms": 1500}

    @pytest.mark.unit
    def test_default_empty_lists(self):
        """Test that completed_order_ids defaults to empty list."""
        result = WebSocketResult(
            status=WebSocketStatus.TIMEOUT,
            message="Operation timed out",
        )
        assert result.completed_order_ids == []
        assert result.metadata == {}

    @pytest.mark.unit
    def test_immutability(self):
        """Test that WebSocketResult is frozen."""
        result = WebSocketResult(
            status=WebSocketStatus.COMPLETED,
            message="Test",
        )
        with pytest.raises(ValidationError):
            result.status = WebSocketStatus.ERROR

    @pytest.mark.unit
    def test_string_strip_whitespace(self):
        """Test that message whitespace is stripped."""
        result = WebSocketResult(
            status=WebSocketStatus.COMPLETED,
            message="  Test message  ",
        )
        assert result.message == "Test message"

    @pytest.mark.unit
    def test_serialization(self):
        """Test that WebSocketResult can be serialized and deserialized."""
        original = WebSocketResult(
            status=WebSocketStatus.COMPLETED,
            message="Test",
            completed_order_ids=["order1"],
            metadata={"key": "value"},
        )
        
        # Serialize to dict
        data = original.model_dump()
        assert data["status"] == "completed"
        assert data["message"] == "Test"
        
        # Deserialize from dict
        restored = WebSocketResult.model_validate(data)
        assert restored.status == original.status
        assert restored.message == original.message
        assert restored.completed_order_ids == original.completed_order_ids
        assert restored.metadata == original.metadata


class TestOrderExecutionResult:
    """Test OrderExecutionResult DTO validation."""

    @pytest.mark.unit
    def test_valid_filled_order(self):
        """Test creation of valid filled order result."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="abc123",
            status="filled",
            filled_qty=Decimal("10.5"),
            avg_fill_price=Decimal("150.25"),
            submitted_at=now,
            completed_at=now,
        )
        assert result.success is True
        assert result.order_id == "abc123"
        assert result.status == "filled"
        assert result.filled_qty == Decimal("10.5")
        assert result.avg_fill_price == Decimal("150.25")
        assert result.submitted_at == now
        assert result.completed_at == now

    @pytest.mark.unit
    def test_valid_accepted_order(self):
        """Test creation of valid accepted order result."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="xyz789",
            status="accepted",
            filled_qty=Decimal("0"),
            submitted_at=now,
        )
        assert result.status == "accepted"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert result.completed_at is None

    @pytest.mark.unit
    def test_valid_partially_filled_order(self):
        """Test creation of partially filled order result."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="partial123",
            status="partially_filled",
            filled_qty=Decimal("5.25"),
            avg_fill_price=Decimal("100.50"),
            submitted_at=now,
        )
        assert result.status == "partially_filled"
        assert result.filled_qty == Decimal("5.25")

    @pytest.mark.unit
    def test_valid_rejected_order(self):
        """Test creation of rejected order result."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=False,
            error="Insufficient funds",
            order_id="reject456",
            status="rejected",
            filled_qty=Decimal("0"),
            submitted_at=now,
            completed_at=now,
        )
        assert result.success is False
        assert result.error == "Insufficient funds"
        assert result.status == "rejected"
        assert result.filled_qty == Decimal("0")

    @pytest.mark.unit
    def test_valid_canceled_order(self):
        """Test creation of canceled order result."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="cancel789",
            status="canceled",
            filled_qty=Decimal("0"),
            submitted_at=now,
            completed_at=now,
        )
        assert result.status == "canceled"

    @pytest.mark.unit
    def test_negative_filled_qty_fails(self):
        """Test that negative filled_qty raises validation error."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResult(
                success=False,
                order_id="bad123",
                status="rejected",
                filled_qty=Decimal("-1.0"),
                submitted_at=now,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "filled_qty" in str(errors[0])
        assert "cannot be negative" in str(errors[0]["ctx"]["error"]).lower()

    @pytest.mark.unit
    def test_zero_avg_fill_price_fails(self):
        """Test that zero avg_fill_price raises validation error."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResult(
                success=True,
                order_id="bad456",
                status="filled",
                filled_qty=Decimal("10.0"),
                avg_fill_price=Decimal("0"),
                submitted_at=now,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "avg_fill_price" in str(errors[0])
        assert "greater than 0" in str(errors[0]["ctx"]["error"]).lower()

    @pytest.mark.unit
    def test_negative_avg_fill_price_fails(self):
        """Test that negative avg_fill_price raises validation error."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResult(
                success=True,
                order_id="bad789",
                status="filled",
                filled_qty=Decimal("10.0"),
                avg_fill_price=Decimal("-100.50"),
                submitted_at=now,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "avg_fill_price" in str(errors[0])

    @pytest.mark.unit
    def test_none_avg_fill_price_valid(self):
        """Test that None avg_fill_price is valid (for pending orders)."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="pending123",
            status="accepted",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=now,
        )
        assert result.avg_fill_price is None

    @pytest.mark.unit
    def test_immutability(self):
        """Test that OrderExecutionResult is frozen."""
        now = datetime.now(UTC)
        result = OrderExecutionResult(
            success=True,
            order_id="frozen123",
            status="filled",
            filled_qty=Decimal("10.0"),
            avg_fill_price=Decimal("100.0"),
            submitted_at=now,
        )
        
        with pytest.raises(ValidationError):
            result.status = "rejected"
        
        with pytest.raises(ValidationError):
            result.filled_qty = Decimal("20.0")

    @pytest.mark.unit
    def test_serialization(self):
        """Test that OrderExecutionResult can be serialized and deserialized."""
        now = datetime.now(UTC)
        original = OrderExecutionResult(
            success=True,
            order_id="serialize123",
            status="filled",
            filled_qty=Decimal("10.5"),
            avg_fill_price=Decimal("150.25"),
            submitted_at=now,
            completed_at=now,
        )
        
        # Serialize to dict
        data = original.model_dump()
        assert data["order_id"] == "serialize123"
        assert data["status"] == "filled"
        assert data["filled_qty"] == Decimal("10.5")
        
        # Deserialize from dict
        restored = OrderExecutionResult.model_validate(data)
        assert restored.order_id == original.order_id
        assert restored.status == original.status
        assert restored.filled_qty == original.filled_qty
        assert restored.avg_fill_price == original.avg_fill_price
        assert restored.submitted_at == original.submitted_at
        assert restored.completed_at == original.completed_at

    @pytest.mark.unit
    def test_result_base_class_fields(self):
        """Test that OrderExecutionResult inherits success/error from Result."""
        now = datetime.now(UTC)
        
        # Success case
        success_result = OrderExecutionResult(
            success=True,
            order_id="success123",
            status="filled",
            filled_qty=Decimal("10.0"),
            avg_fill_price=Decimal("100.0"),
            submitted_at=now,
        )
        assert success_result.success is True
        assert success_result.error is None
        assert success_result.is_success is True
        
        # Error case
        error_result = OrderExecutionResult(
            success=False,
            error="Order validation failed",
            order_id="error123",
            status="rejected",
            filled_qty=Decimal("0"),
            submitted_at=now,
        )
        assert error_result.success is False
        assert error_result.error == "Order validation failed"
        assert error_result.is_success is False

    @pytest.mark.unit
    def test_status_literals_enforced(self):
        """Test that only valid status literals are accepted."""
        now = datetime.now(UTC)
        
        # Valid statuses
        valid_statuses = ["accepted", "filled", "partially_filled", "rejected", "canceled"]
        for status in valid_statuses:
            result = OrderExecutionResult(
                success=True,
                order_id=f"test_{status}",
                status=status,
                filled_qty=Decimal("0"),
                submitted_at=now,
            )
            assert result.status == status
        
        # Invalid status should fail
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResult(
                success=True,
                order_id="invalid_status",
                status="pending",  # Not in the Literal
                filled_qty=Decimal("0"),
                submitted_at=now,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "status" in str(errors[0])

    @pytest.mark.unit
    def test_decimal_precision_preserved(self):
        """Test that Decimal precision is maintained."""
        now = datetime.now(UTC)
        
        # Use precise decimal values
        filled_qty = Decimal("10.123456789")
        avg_price = Decimal("150.9876543210")
        
        result = OrderExecutionResult(
            success=True,
            order_id="precision123",
            status="filled",
            filled_qty=filled_qty,
            avg_fill_price=avg_price,
            submitted_at=now,
        )
        
        # Verify precision is maintained
        assert result.filled_qty == filled_qty
        assert result.avg_fill_price == avg_price
        assert str(result.filled_qty) == "10.123456789"
        assert str(result.avg_fill_price) == "150.9876543210"

    @pytest.mark.unit
    def test_datetime_fields(self):
        """Test datetime field handling."""
        submitted = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 15, 10, 30, 5, tzinfo=UTC)
        
        result = OrderExecutionResult(
            success=True,
            order_id="datetime123",
            status="filled",
            filled_qty=Decimal("10.0"),
            avg_fill_price=Decimal("100.0"),
            submitted_at=submitted,
            completed_at=completed,
        )
        
        assert result.submitted_at == submitted
        assert result.completed_at == completed
        assert result.submitted_at.tzinfo == UTC
        assert result.completed_at.tzinfo == UTC


class TestOrderExecutionResultEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_very_small_decimal_values(self):
        """Test handling of very small decimal values."""
        now = datetime.now(UTC)
        
        result = OrderExecutionResult(
            success=True,
            order_id="small_decimal",
            status="filled",
            filled_qty=Decimal("0.00000001"),
            avg_fill_price=Decimal("0.01"),
            submitted_at=now,
        )
        
        assert result.filled_qty == Decimal("0.00000001")
        assert result.avg_fill_price == Decimal("0.01")

    @pytest.mark.unit
    def test_very_large_decimal_values(self):
        """Test handling of very large decimal values."""
        now = datetime.now(UTC)
        
        result = OrderExecutionResult(
            success=True,
            order_id="large_decimal",
            status="filled",
            filled_qty=Decimal("999999999.999999"),
            avg_fill_price=Decimal("9999999.99"),
            submitted_at=now,
        )
        
        assert result.filled_qty == Decimal("999999999.999999")
        assert result.avg_fill_price == Decimal("9999999.99")

    @pytest.mark.unit
    def test_empty_order_id(self):
        """Test that empty order_id is allowed (validation at business layer)."""
        now = datetime.now(UTC)
        
        # Empty string is technically valid at DTO level
        result = OrderExecutionResult(
            success=True,
            order_id="",
            status="accepted",
            filled_qty=Decimal("0"),
            submitted_at=now,
        )
        
        assert result.order_id == ""

    @pytest.mark.unit
    def test_completed_at_none(self):
        """Test that completed_at can be None for pending orders."""
        now = datetime.now(UTC)
        
        result = OrderExecutionResult(
            success=True,
            order_id="pending_order",
            status="accepted",
            filled_qty=Decimal("0"),
            submitted_at=now,
            completed_at=None,
        )
        
        assert result.completed_at is None
