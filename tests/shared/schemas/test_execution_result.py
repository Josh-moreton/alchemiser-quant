"""Business Unit: shared | Status: current.

Comprehensive tests for execution_result schema.

Tests validation, immutability, field constraints, and schema versioning
for the ExecutionResult DTO.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.execution_result import ExecutionResult


class TestExecutionResultValidation:
    """Test ExecutionResult validation and constraints."""

    def test_valid_execution_result_minimal(self):
        """Test creation of valid execution result with minimal fields."""
        timestamp = datetime.now(UTC)
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=timestamp,
        )

        assert result.symbol == "AAPL"
        assert result.side == "buy"
        assert result.quantity == Decimal("10")
        assert result.status == "filled"
        assert result.success is True
        assert result.execution_strategy == "market"
        assert result.timestamp == timestamp
        assert result.schema_version == "1.0"
        assert result.order_id is None
        assert result.price is None
        assert result.error_code is None
        assert result.error_message is None
        assert result.correlation_id is None
        assert result.causation_id is None
        assert result.metadata is None

    def test_valid_execution_result_full(self):
        """Test creation of valid execution result with all fields."""
        timestamp = datetime.now(UTC)
        result = ExecutionResult(
            schema_version="1.0",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100.5"),
            status="filled",
            success=True,
            execution_strategy="limit",
            order_id="order-123",
            price=Decimal("150.75"),
            error_code=None,
            error_message=None,
            timestamp=timestamp,
            correlation_id="corr-456",
            causation_id="cause-789",
            metadata={"broker": "alpaca", "attempt": 1},
        )

        assert result.schema_version == "1.0"
        assert result.symbol == "AAPL"
        assert result.side == "sell"
        assert result.quantity == Decimal("100.5")
        assert result.status == "filled"
        assert result.success is True
        assert result.execution_strategy == "limit"
        assert result.order_id == "order-123"
        assert result.price == Decimal("150.75")
        assert result.timestamp == timestamp
        assert result.correlation_id == "corr-456"
        assert result.causation_id == "cause-789"
        assert result.metadata == {"broker": "alpaca", "attempt": 1}

    def test_valid_execution_result_with_error(self):
        """Test creation of valid execution result with error information."""
        timestamp = datetime.now(UTC)
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="rejected",
            success=False,
            execution_strategy="market",
            error_code="INSUFFICIENT_FUNDS",
            error_message="Not enough buying power",
            timestamp=timestamp,
        )

        assert result.success is False
        assert result.status == "rejected"
        assert result.error_code == "INSUFFICIENT_FUNDS"
        assert result.error_message == "Not enough buying power"

    def test_invalid_side_value(self):
        """Test that invalid side value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="invalid",  # Invalid value
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="market",
                timestamp=datetime.now(UTC),
            )
        assert "side" in str(exc_info.value)

    def test_invalid_status_value(self):
        """Test that invalid status value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("10"),
                status="invalid_status",  # Invalid value
                success=True,
                execution_strategy="market",
                timestamp=datetime.now(UTC),
            )
        assert "status" in str(exc_info.value)

    def test_invalid_execution_strategy_value(self):
        """Test that invalid execution_strategy value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="invalid_strategy",  # Invalid value
                timestamp=datetime.now(UTC),
            )
        assert "execution_strategy" in str(exc_info.value)

    def test_negative_quantity_rejected(self):
        """Test that negative quantity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("-10"),  # Negative value
                status="filled",
                success=True,
                execution_strategy="market",
                timestamp=datetime.now(UTC),
            )
        assert "quantity" in str(exc_info.value)

    def test_zero_quantity_rejected(self):
        """Test that zero quantity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("0"),  # Zero value
                status="filled",
                success=True,
                execution_strategy="market",
                timestamp=datetime.now(UTC),
            )
        assert "quantity" in str(exc_info.value)

    def test_negative_price_rejected(self):
        """Test that negative price raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="market",
                price=Decimal("-150.50"),  # Negative price
                timestamp=datetime.now(UTC),
            )
        assert "price" in str(exc_info.value)

    def test_zero_price_rejected(self):
        """Test that zero price raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="market",
                price=Decimal("0"),  # Zero price
                timestamp=datetime.now(UTC),
            )
        assert "price" in str(exc_info.value)

    def test_empty_symbol_rejected(self):
        """Test that empty symbol raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="",  # Empty string
                side="buy",
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="market",
                timestamp=datetime.now(UTC),
            )
        assert "symbol" in str(exc_info.value)

    def test_missing_timestamp_rejected(self):
        """Test that missing timestamp raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("10"),
                status="filled",
                success=True,
                execution_strategy="market",
                # timestamp missing - should fail
            )
        assert "timestamp" in str(exc_info.value)


class TestExecutionResultImmutability:
    """Test ExecutionResult immutability (frozen model)."""

    def test_execution_result_is_frozen(self):
        """Test that ExecutionResult is immutable after creation."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
        )

        with pytest.raises(ValidationError) as exc_info:
            result.symbol = "GOOGL"  # Should fail - frozen model
        assert "frozen" in str(exc_info.value).lower()

    def test_execution_result_fields_cannot_be_modified(self):
        """Test that individual fields cannot be modified."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
        )

        with pytest.raises(ValidationError):
            result.quantity = Decimal("20")

        with pytest.raises(ValidationError):
            result.success = False


class TestExecutionResultSerialization:
    """Test ExecutionResult serialization and deserialization."""

    def test_execution_result_model_dump(self):
        """Test that ExecutionResult can be serialized to dict."""
        timestamp = datetime(2025, 1, 10, 12, 0, 0, tzinfo=UTC)
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            price=Decimal("150.50"),
            timestamp=timestamp,
            correlation_id="corr-123",
        )

        data = result.model_dump()

        assert data["symbol"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == Decimal("10")
        assert data["status"] == "filled"
        assert data["success"] is True
        assert data["execution_strategy"] == "market"
        assert data["price"] == Decimal("150.50")
        assert data["timestamp"] == timestamp
        assert data["correlation_id"] == "corr-123"
        assert data["schema_version"] == "1.0"

    def test_execution_result_json_serialization(self):
        """Test that ExecutionResult can be serialized to JSON."""
        timestamp = datetime(2025, 1, 10, 12, 0, 0, tzinfo=UTC)
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10.5"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=timestamp,
        )

        json_str = result.model_dump_json()
        assert "AAPL" in json_str
        assert "buy" in json_str
        assert "10.5" in json_str
        assert "filled" in json_str

    def test_execution_result_deserialization(self):
        """Test that ExecutionResult can be deserialized from dict."""
        timestamp = datetime(2025, 1, 10, 12, 0, 0, tzinfo=UTC)
        data = {
            "schema_version": "1.0",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "10.5",  # String decimal
            "status": "filled",
            "success": True,
            "execution_strategy": "market",
            "timestamp": timestamp.isoformat(),
            "correlation_id": "corr-123",
        }

        result = ExecutionResult.model_validate(data)

        assert result.symbol == "AAPL"
        assert result.quantity == Decimal("10.5")
        assert result.correlation_id == "corr-123"


class TestExecutionResultSchemaVersioning:
    """Test ExecutionResult schema versioning."""

    def test_default_schema_version(self):
        """Test that schema_version defaults to 1.0."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
        )

        assert result.schema_version == "1.0"

    def test_explicit_schema_version(self):
        """Test that schema_version can be explicitly set."""
        result = ExecutionResult(
            schema_version="1.1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
        )

        assert result.schema_version == "1.1"


class TestExecutionResultObservability:
    """Test ExecutionResult observability fields."""

    def test_correlation_id_traceability(self):
        """Test that correlation_id can be set for tracing."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
            correlation_id="corr-abc-123",
        )

        assert result.correlation_id == "corr-abc-123"

    def test_causation_id_event_sourcing(self):
        """Test that causation_id can be set for event sourcing."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
            causation_id="cause-xyz-789",
        )

        assert result.causation_id == "cause-xyz-789"

    def test_both_traceability_fields(self):
        """Test that both correlation_id and causation_id can be set."""
        result = ExecutionResult(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            status="filled",
            success=True,
            execution_strategy="market",
            timestamp=datetime.now(UTC),
            correlation_id="corr-abc-123",
            causation_id="cause-xyz-789",
        )

        assert result.correlation_id == "corr-abc-123"
        assert result.causation_id == "cause-xyz-789"
