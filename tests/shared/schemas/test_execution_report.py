"""Business Unit: shared | Status: current.

Comprehensive tests for execution_report DTOs.

Tests cover:
- DTO creation and validation
- Field validation (action, status, success_rate, timestamps)
- Serialization/deserialization round-trips
- Timezone awareness enforcement
- Decimal handling and precision
- Idempotency key generation
- Type safety in conversions
- Edge cases and error conditions
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.execution_report import ExecutedOrder, ExecutionReport


class TestExecutedOrder:
    """Tests for ExecutedOrder DTO."""

    def test_valid_order_creation(self) -> None:
        """Test creating a valid ExecutedOrder."""
        order = ExecutedOrder(
            schema_version="1.0",
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        assert order.order_id == "order-123"
        assert order.symbol == "AAPL"
        assert order.action == "BUY"
        assert order.quantity == Decimal("10")
        assert order.status == "FILLED"
        assert order.schema_version == "1.0"

    def test_action_validation_uppercase(self) -> None:
        """Test action normalization to uppercase."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="buy",  # lowercase
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        assert order.action == "BUY"

    def test_action_validation_invalid(self) -> None:
        """Test action validation rejects invalid actions."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutedOrder(
                order_id="order-123",
                symbol="AAPL",
                action="INVALID",
                quantity=Decimal("10"),
                filled_quantity=Decimal("10"),
                price=Decimal("150.50"),
                total_value=Decimal("1505.00"),
                status="FILLED",
                execution_timestamp=datetime.now(UTC),
            )

        assert "Action must be" in str(exc_info.value)

    def test_status_validation_valid_statuses(self) -> None:
        """Test all valid order statuses are accepted."""
        valid_statuses = [
            "FILLED",
            "PARTIAL",
            "REJECTED",
            "CANCELLED",
            "CANCELED",
            "PENDING",
            "PENDING_NEW",
            "FAILED",
            "ACCEPTED",
        ]

        for status in valid_statuses:
            order = ExecutedOrder(
                order_id="order-123",
                symbol="AAPL",
                action="BUY",
                quantity=Decimal("10"),
                filled_quantity=Decimal("10"),
                price=Decimal("150.50"),
                total_value=Decimal("1505.00"),
                status=status,
                execution_timestamp=datetime.now(UTC),
            )
            assert order.status == status

    def test_status_validation_lowercase_normalized(self) -> None:
        """Test status normalization to uppercase."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="filled",  # lowercase
            execution_timestamp=datetime.now(UTC),
        )

        assert order.status == "FILLED"

    def test_status_validation_invalid(self) -> None:
        """Test status validation rejects invalid statuses."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutedOrder(
                order_id="order-123",
                symbol="AAPL",
                action="BUY",
                quantity=Decimal("10"),
                filled_quantity=Decimal("10"),
                price=Decimal("150.50"),
                total_value=Decimal("1505.00"),
                status="INVALID_STATUS",
                execution_timestamp=datetime.now(UTC),
            )

        assert "Status must be" in str(exc_info.value)

    def test_timezone_aware_timestamp(self) -> None:
        """Test timezone awareness is enforced."""
        # Naive datetime should be made timezone-aware
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=naive_dt,
        )

        assert order.execution_timestamp.tzinfo is not None

    def test_decimal_precision(self) -> None:
        """Test Decimal field precision is maintained."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10.123456"),
            filled_quantity=Decimal("10.123456"),
            price=Decimal("150.505050"),
            total_value=Decimal("1523.456789"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        assert order.quantity == Decimal("10.123456")
        assert order.price == Decimal("150.505050")
        assert order.total_value == Decimal("1523.456789")

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="  aapl  ",  # lowercase with whitespace
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        assert order.symbol == "AAPL"

    def test_immutability(self) -> None:
        """Test ExecutedOrder is immutable (frozen)."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        with pytest.raises(ValidationError):
            order.quantity = Decimal("20")  # type: ignore

    def test_optional_fields(self) -> None:
        """Test optional fields can be None."""
        order = ExecutedOrder(
            order_id="order-123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("10"),
            filled_quantity=Decimal("10"),
            price=Decimal("150.50"),
            total_value=Decimal("1505.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
            commission=None,
            fees=None,
            error_message=None,
        )

        assert order.commission is None
        assert order.fees is None
        assert order.error_message is None


class TestExecutionReport:
    """Tests for ExecutionReport DTO."""

    def test_valid_report_creation(self) -> None:
        """Test creating a valid ExecutionReport."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            schema_version="1.0",
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000.00"),
            total_commissions=Decimal("10.00"),
            total_fees=Decimal("5.00"),
            net_cash_flow=Decimal("-10015.00"),
            execution_start_time=now,
            execution_end_time=now + timedelta(seconds=45),
            total_duration_seconds=Decimal("45.5"),
            success_rate=Decimal("1.0"),
        )

        assert report.execution_id == "exec-789"
        assert report.correlation_id == "corr-123"
        assert report.causation_id == "cause-456"
        assert report.total_orders == 5
        assert report.successful_orders == 5
        assert report.failed_orders == 0
        assert report.success_rate == Decimal("1.0")
        assert report.schema_version == "1.0"

    def test_success_rate_boundaries(self) -> None:
        """Test success_rate validation at boundaries."""
        now = datetime.now(UTC)

        # Test 0.0
        report_zero = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=0,
            failed_orders=5,
            total_value_traded=Decimal("0"),
            total_commissions=Decimal("0"),
            total_fees=Decimal("0"),
            net_cash_flow=Decimal("0"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("0"),
            success_rate=Decimal("0"),
        )
        assert report_zero.success_rate == Decimal("0")

        # Test 0.5
        report_half = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=10,
            successful_orders=5,
            failed_orders=5,
            total_value_traded=Decimal("5000"),
            total_commissions=Decimal("5"),
            total_fees=Decimal("2.5"),
            net_cash_flow=Decimal("-5007.50"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("30"),
            success_rate=Decimal("0.5"),
        )
        assert report_half.success_rate == Decimal("0.5")

        # Test 1.0
        report_full = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("45"),
            success_rate=Decimal("1.0"),
        )
        assert report_full.success_rate == Decimal("1.0")

    @pytest.mark.parametrize("invalid_rate", [Decimal("-0.1"), Decimal("1.1"), Decimal("2.0")])
    def test_invalid_success_rate(self, invalid_rate: Decimal) -> None:
        """Test success_rate validation rejects out-of-range values."""
        now = datetime.now(UTC)

        with pytest.raises(ValidationError) as exc_info:
            ExecutionReport(
                correlation_id="corr-123",
                causation_id="cause-456",
                timestamp=now,
                execution_id="exec-789",
                total_orders=5,
                successful_orders=5,
                failed_orders=0,
                total_value_traded=Decimal("10000"),
                total_commissions=Decimal("10"),
                total_fees=Decimal("5"),
                net_cash_flow=Decimal("-10015"),
                execution_start_time=now,
                execution_end_time=now,
                total_duration_seconds=Decimal("45"),
                success_rate=invalid_rate,
            )

        assert "success_rate" in str(exc_info.value).lower()

    def test_serialization_round_trip(self) -> None:
        """Test to_dict() and from_dict() round-trip preserves data."""
        now = datetime.now(UTC)
        original = ExecutionReport(
            schema_version="1.0",
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=4,
            failed_orders=1,
            total_value_traded=Decimal("10000.50"),
            total_commissions=Decimal("10.25"),
            total_fees=Decimal("5.10"),
            net_cash_flow=Decimal("-10015.85"),
            execution_start_time=now,
            execution_end_time=now + timedelta(seconds=45),
            total_duration_seconds=Decimal("45.5"),
            success_rate=Decimal("0.8"),
            average_execution_time_seconds=Decimal("9.1"),
            orders=[
                ExecutedOrder(
                    order_id="order-1",
                    symbol="AAPL",
                    action="BUY",
                    quantity=Decimal("10"),
                    filled_quantity=Decimal("10"),
                    price=Decimal("150.50"),
                    total_value=Decimal("1505.00"),
                    status="FILLED",
                    execution_timestamp=now,
                )
            ],
        )

        # Serialize to dict
        data = original.to_dict()

        # Verify serialization types
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["total_value_traded"], str)
        assert isinstance(data["success_rate"], str)
        assert isinstance(data["total_duration_seconds"], str)

        # Deserialize from dict
        restored = ExecutionReport.from_dict(data)

        # Verify data integrity
        assert restored.execution_id == original.execution_id
        assert restored.correlation_id == original.correlation_id
        assert restored.total_orders == original.total_orders
        assert restored.total_value_traded == original.total_value_traded
        assert restored.success_rate == original.success_rate
        assert restored.total_duration_seconds == original.total_duration_seconds
        assert len(restored.orders) == len(original.orders)
        assert restored.orders[0].order_id == original.orders[0].order_id

    def test_idempotency_key_deterministic(self) -> None:
        """Test idempotency key is consistent for same data."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            schema_version="1.0",
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("45"),
            success_rate=Decimal("1.0"),
        )

        key1 = report.idempotency_key
        key2 = report.idempotency_key

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA-256 hex string length

    def test_idempotency_key_different_for_different_data(self) -> None:
        """Test idempotency key differs for different reports."""
        now = datetime.now(UTC)

        report1 = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("45"),
            success_rate=Decimal("1.0"),
        )

        report2 = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-999",  # Different execution_id
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("45"),
            success_rate=Decimal("1.0"),
        )

        assert report1.idempotency_key != report2.idempotency_key

    def test_correlation_tracking(self) -> None:
        """Test correlation_id and causation_id are properly stored."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            correlation_id="corr-abc-123",
            causation_id="cause-def-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=1,
            successful_orders=1,
            failed_orders=0,
            total_value_traded=Decimal("1000"),
            total_commissions=Decimal("1"),
            total_fees=Decimal("0.5"),
            net_cash_flow=Decimal("-1001.5"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("10"),
            success_rate=Decimal("1.0"),
        )

        assert report.correlation_id == "corr-abc-123"
        assert report.causation_id == "cause-def-456"

    def test_timezone_aware_timestamps(self) -> None:
        """Test all timestamp fields are timezone-aware."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)

        report = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=naive_dt,
            execution_id="exec-789",
            total_orders=1,
            successful_orders=1,
            failed_orders=0,
            total_value_traded=Decimal("1000"),
            total_commissions=Decimal("1"),
            total_fees=Decimal("0.5"),
            net_cash_flow=Decimal("-1001.5"),
            execution_start_time=naive_dt,
            execution_end_time=naive_dt,
            total_duration_seconds=Decimal("10"),
            success_rate=Decimal("1.0"),
        )

        assert report.timestamp.tzinfo is not None
        assert report.execution_start_time.tzinfo is not None
        assert report.execution_end_time.tzinfo is not None

    def test_immutability(self) -> None:
        """Test ExecutionReport is immutable (frozen)."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=5,
            successful_orders=5,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("45"),
            success_rate=Decimal("1.0"),
        )

        with pytest.raises(ValidationError):
            report.total_orders = 10  # type: ignore

    def test_orders_type_safety(self) -> None:
        """Test _convert_orders_from_dict validates types properly."""
        now = datetime.now(UTC)

        # Valid: dict orders
        data_with_dict_orders = {
            "schema_version": "1.0",
            "correlation_id": "corr-123",
            "causation_id": "cause-456",
            "timestamp": now.isoformat(),
            "execution_id": "exec-789",
            "total_orders": 1,
            "successful_orders": 1,
            "failed_orders": 0,
            "total_value_traded": "1000",
            "total_commissions": "1",
            "total_fees": "0.5",
            "net_cash_flow": "-1001.5",
            "execution_start_time": now.isoformat(),
            "execution_end_time": now.isoformat(),
            "total_duration_seconds": "10",
            "success_rate": "1.0",
            "orders": [
                {
                    "order_id": "order-1",
                    "symbol": "AAPL",
                    "action": "BUY",
                    "quantity": "10",
                    "filled_quantity": "10",
                    "price": "150.50",
                    "total_value": "1505.00",
                    "status": "FILLED",
                    "execution_timestamp": now.isoformat(),
                }
            ],
        }

        report = ExecutionReport.from_dict(data_with_dict_orders)
        assert len(report.orders) == 1
        assert isinstance(report.orders[0], ExecutedOrder)

        # Invalid: non-dict, non-ExecutedOrder items should raise TypeError
        data_with_invalid_orders = data_with_dict_orders.copy()
        data_with_invalid_orders["orders"] = ["invalid", 123, None]  # type: ignore

        with pytest.raises(TypeError) as exc_info:
            ExecutionReport.from_dict(data_with_invalid_orders)

        assert "Order data must be dict or ExecutedOrder" in str(exc_info.value)

    def test_negative_net_cash_flow(self) -> None:
        """Test net_cash_flow can be negative (for purchases)."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=1,
            successful_orders=1,
            failed_orders=0,
            total_value_traded=Decimal("10000"),
            total_commissions=Decimal("10"),
            total_fees=Decimal("5"),
            net_cash_flow=Decimal("-10015.00"),  # Negative
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("10"),
            success_rate=Decimal("1.0"),
        )

        assert report.net_cash_flow == Decimal("-10015.00")
        assert report.net_cash_flow < 0

    def test_empty_orders_list(self) -> None:
        """Test ExecutionReport with no orders."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=0,
            successful_orders=0,
            failed_orders=0,
            total_value_traded=Decimal("0"),
            total_commissions=Decimal("0"),
            total_fees=Decimal("0"),
            net_cash_flow=Decimal("0"),
            execution_start_time=now,
            execution_end_time=now,
            total_duration_seconds=Decimal("0"),
            success_rate=Decimal("0"),
            orders=[],
        )

        assert len(report.orders) == 0
        assert report.total_orders == 0

    def test_decimal_consistency(self) -> None:
        """Test total_duration_seconds uses Decimal for consistency."""
        now = datetime.now(UTC)
        report = ExecutionReport(
            correlation_id="corr-123",
            causation_id="cause-456",
            timestamp=now,
            execution_id="exec-789",
            total_orders=1,
            successful_orders=1,
            failed_orders=0,
            total_value_traded=Decimal("1000"),
            total_commissions=Decimal("1"),
            total_fees=Decimal("0.5"),
            net_cash_flow=Decimal("-1001.5"),
            execution_start_time=now,
            execution_end_time=now + timedelta(seconds=45, microseconds=500000),
            total_duration_seconds=Decimal("45.5"),
            success_rate=Decimal("1.0"),
            average_execution_time_seconds=Decimal("9.1"),
        )

        # Both timing fields should be Decimal
        assert isinstance(report.total_duration_seconds, Decimal)
        assert isinstance(report.average_execution_time_seconds, Decimal)
        assert report.total_duration_seconds == Decimal("45.5")
        assert report.average_execution_time_seconds == Decimal("9.1")
