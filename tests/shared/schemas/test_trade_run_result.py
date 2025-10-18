"""Business Unit: shared | Status: current

Unit tests for trade run result DTOs.

Tests DTO validation, constraints, immutability, and serialization.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.trade_run_result import (
    ExecutionStatus,
    ExecutionSummary,
    OrderAction,
    OrderResultSummary,
    TradeRunResult,
    TradingMode,
)


class TestOrderResultSummary:
    """Test OrderResultSummary DTO validation."""

    def test_valid_order_result(self):
        """Test creation of valid order result."""
        now = datetime.now(UTC)
        result = OrderResultSummary(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10.5"),
            price=Decimal("95.24"),
            success=True,
            timestamp=now,
        )
        assert result.symbol == "AAPL"
        assert result.action == "BUY"
        assert result.trade_amount == Decimal("1000.00")
        assert result.shares == Decimal("10.5")
        assert result.price == Decimal("95.24")
        assert result.success is True
        assert result.timestamp == now
        assert result.schema_version == "1.0"

    def test_immutability(self):
        """Test that DTO is frozen."""
        result = OrderResultSummary(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            success=True,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            result.symbol = "MSFT"  # type: ignore

    def test_action_literal_type_enforcement(self):
        """Test that action field only accepts BUY or SELL."""
        now = datetime.now(UTC)
        # Valid actions
        for action in ["BUY", "SELL"]:
            result = OrderResultSummary(
                symbol="AAPL",
                action=action,  # type: ignore
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=now,
            )
            assert result.action == action

        # Invalid action should fail
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="HOLD",  # type: ignore
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=now,
            )

    def test_timezone_aware_timestamp_required(self):
        """Test that naive datetime is rejected."""
        with pytest.raises(ValidationError, match="timezone-aware"):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=datetime(2025, 1, 1, 12, 0, 0),  # Naive datetime
            )

    def test_negative_trade_amount_rejected(self):
        """Test that negative trade amounts are rejected."""
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("-1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=datetime.now(UTC),
            )

    def test_negative_shares_rejected(self):
        """Test that negative shares are rejected."""
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("-10"),
                success=True,
                timestamp=datetime.now(UTC),
            )

    def test_negative_price_rejected(self):
        """Test that negative or zero price is rejected."""
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                price=Decimal("-95.24"),
                success=True,
                timestamp=datetime.now(UTC),
            )

    def test_order_id_redacted_length_constraint(self):
        """Test that order_id_redacted must be exactly 6 characters."""
        now = datetime.now(UTC)

        # Valid 6-character redacted ID
        result = OrderResultSummary(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            success=True,
            timestamp=now,
            order_id_redacted="abc123",
        )
        assert result.order_id_redacted == "abc123"

        # Too short should fail
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=now,
                order_id_redacted="abc12",
            )

        # Too long should fail
        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=True,
                timestamp=now,
                order_id_redacted="abc1234",
            )

    def test_error_message_max_length(self):
        """Test error_message respects max length."""
        now = datetime.now(UTC)
        long_message = "x" * 1001

        with pytest.raises(ValidationError):
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                success=False,
                error_message=long_message,
                timestamp=now,
            )

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        now = datetime.now(UTC)
        result = OrderResultSummary(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            success=True,
            timestamp=now,
        )
        assert result.price is None
        assert result.order_id_redacted is None
        assert result.order_id_full is None
        assert result.error_message is None


class TestExecutionSummary:
    """Test ExecutionSummary DTO validation."""

    def test_valid_execution_summary(self):
        """Test creation of valid execution summary."""
        summary = ExecutionSummary(
            orders_total=10,
            orders_succeeded=8,
            orders_failed=2,
            total_value=Decimal("50000.00"),
            success_rate=0.8,
            execution_duration_seconds=12.5,
        )
        assert summary.orders_total == 10
        assert summary.orders_succeeded == 8
        assert summary.orders_failed == 2
        assert summary.total_value == Decimal("50000.00")
        assert summary.success_rate == 0.8
        assert summary.execution_duration_seconds == 12.5
        assert summary.schema_version == "1.0"

    def test_order_count_invariant_enforced(self):
        """Test that order counts must sum to total."""
        # Valid: 8 + 2 = 10
        ExecutionSummary(
            orders_total=10,
            orders_succeeded=8,
            orders_failed=2,
            total_value=Decimal("50000.00"),
            success_rate=0.8,
            execution_duration_seconds=12.5,
        )

        # Invalid: 8 + 3 != 10
        with pytest.raises(ValidationError, match="must equal orders_total"):
            ExecutionSummary(
                orders_total=10,
                orders_succeeded=8,
                orders_failed=3,
                total_value=Decimal("50000.00"),
                success_rate=0.8,
                execution_duration_seconds=12.5,
            )

    def test_negative_counts_rejected(self):
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError):
            ExecutionSummary(
                orders_total=-1,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=0.0,
            )

    def test_success_rate_bounds(self):
        """Test that success_rate must be between 0 and 1."""
        # Valid success rates
        for rate in [0.0, 0.5, 1.0]:
            ExecutionSummary(
                orders_total=10,
                orders_succeeded=int(rate * 10),
                orders_failed=10 - int(rate * 10),
                total_value=Decimal("1000.00"),
                success_rate=rate,
                execution_duration_seconds=5.0,
            )

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            ExecutionSummary(
                orders_total=10,
                orders_succeeded=10,
                orders_failed=0,
                total_value=Decimal("1000.00"),
                success_rate=1.5,
                execution_duration_seconds=5.0,
            )

        # Invalid: < 0.0
        with pytest.raises(ValidationError):
            ExecutionSummary(
                orders_total=10,
                orders_succeeded=0,
                orders_failed=10,
                total_value=Decimal("1000.00"),
                success_rate=-0.1,
                execution_duration_seconds=5.0,
            )

    def test_immutability(self):
        """Test that ExecutionSummary is frozen."""
        summary = ExecutionSummary(
            orders_total=10,
            orders_succeeded=8,
            orders_failed=2,
            total_value=Decimal("50000.00"),
            success_rate=0.8,
            execution_duration_seconds=12.5,
        )
        with pytest.raises(ValidationError):
            summary.orders_total = 20  # type: ignore


class TestTradeRunResult:
    """Test TradeRunResult DTO validation and behavior."""

    def test_valid_trade_run_result(self):
        """Test creation of valid trade run result."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=5)

        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=1,
                orders_succeeded=1,
                orders_failed=0,
                total_value=Decimal("1000.00"),
                success_rate=1.0,
                execution_duration_seconds=5.0,
            ),
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-correlation-id",
        )
        assert result.status == "SUCCESS"
        assert result.success is True
        assert result.trading_mode == "PAPER"
        assert result.correlation_id == "test-correlation-id"
        assert result.schema_version == "1.0"

    def test_status_literal_type_enforcement(self):
        """Test that status field only accepts valid values."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=1)

        for status in ["SUCCESS", "FAILURE", "PARTIAL"]:
            result = TradeRunResult(
                status=status,  # type: ignore
                success=(status == "SUCCESS"),
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=1.0,
                ),
                trading_mode="PAPER",
                started_at=started,
                completed_at=completed,
                correlation_id="test-id",
            )
            assert result.status == status

        # Invalid status
        with pytest.raises(ValidationError):
            TradeRunResult(
                status="INVALID",  # type: ignore
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=1.0,
                ),
                trading_mode="PAPER",
                started_at=started,
                completed_at=completed,
                correlation_id="test-id",
            )

    def test_trading_mode_literal_type_enforcement(self):
        """Test that trading_mode field only accepts PAPER or LIVE."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=1)

        for mode in ["PAPER", "LIVE"]:
            result = TradeRunResult(
                status="SUCCESS",
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=1.0,
                ),
                trading_mode=mode,  # type: ignore
                started_at=started,
                completed_at=completed,
                correlation_id="test-id",
            )
            assert result.trading_mode == mode

        # Invalid mode
        with pytest.raises(ValidationError):
            TradeRunResult(
                status="SUCCESS",
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=1.0,
                ),
                trading_mode="UNKNOWN",  # type: ignore
                started_at=started,
                completed_at=completed,
                correlation_id="test-id",
            )

    def test_timezone_aware_datetimes_required(self):
        """Test that naive datetimes are rejected."""
        with pytest.raises(ValidationError, match="timezone-aware"):
            TradeRunResult(
                status="SUCCESS",
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=0.0,
                ),
                trading_mode="PAPER",
                started_at=datetime(2025, 1, 1, 12, 0, 0),  # Naive
                completed_at=datetime.now(UTC),
                correlation_id="test-id",
            )

    def test_temporal_ordering_enforced(self):
        """Test that completed_at must be >= started_at."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed_before = datetime(2025, 1, 1, 11, 59, 59, tzinfo=UTC)

        with pytest.raises(ValidationError, match="must be >="):
            TradeRunResult(
                status="SUCCESS",
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=0.0,
                ),
                trading_mode="PAPER",
                started_at=started,
                completed_at=completed_before,
                correlation_id="test-id",
            )

    def test_duration_seconds_property(self):
        """Test duration_seconds computed property."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 1, 12, 0, 10, tzinfo=UTC)

        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=10.0,
            ),
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-id",
        )
        assert result.duration_seconds == 10.0

    def test_to_json_dict_serialization(self):
        """Test JSON dictionary serialization."""
        started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        completed = datetime(2025, 1, 1, 12, 0, 5, tzinfo=UTC)

        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=1,
                orders_succeeded=1,
                orders_failed=0,
                total_value=Decimal("1234.56"),
                success_rate=1.0,
                execution_duration_seconds=5.0,
            ),
            orders=[
                OrderResultSummary(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1234.56"),
                    shares=Decimal("10"),
                    price=Decimal("123.456"),
                    success=True,
                    timestamp=completed,
                )
            ],
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-correlation-id",
        )

        json_dict = result.to_json_dict()

        assert json_dict["status"] == "SUCCESS"
        assert json_dict["success"] is True
        assert json_dict["trading_mode"] == "PAPER"
        assert json_dict["total_value"] == "1234.56"  # Decimal serialized as string
        assert json_dict["correlation_id"] == "test-correlation-id"
        assert json_dict["duration_seconds"] == 5.0
        assert len(json_dict["orders"]) == 1
        assert json_dict["orders"][0]["symbol"] == "AAPL"
        assert json_dict["orders"][0]["action"] == "BUY"
        assert json_dict["orders"][0]["trade_amount"] == "1234.56"

    def test_immutability(self):
        """Test that TradeRunResult is frozen."""
        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=0.0,
            ),
            trading_mode="PAPER",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            correlation_id="test-id",
        )

        with pytest.raises(ValidationError):
            result.status = "FAILURE"  # type: ignore

    def test_causation_id_field(self):
        """Test that causation_id field is optional."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=1)

        # Without causation_id
        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=1.0,
            ),
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-correlation-id",
        )
        assert result.causation_id is None

        # With causation_id
        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=1.0,
            ),
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-correlation-id",
            causation_id="test-causation-id",
        )
        assert result.causation_id == "test-causation-id"

    def test_warnings_list_max_length(self):
        """Test that warnings list respects max length."""
        started = datetime.now(UTC)
        completed = started + timedelta(seconds=1)

        # Valid: under limit
        result = TradeRunResult(
            status="SUCCESS",
            success=True,
            execution_summary=ExecutionSummary(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=1.0,
            ),
            trading_mode="PAPER",
            started_at=started,
            completed_at=completed,
            correlation_id="test-id",
            warnings=["warning1", "warning2"],
        )
        assert len(result.warnings) == 2

        # Invalid: over limit
        with pytest.raises(ValidationError):
            TradeRunResult(
                status="SUCCESS",
                success=True,
                execution_summary=ExecutionSummary(
                    orders_total=0,
                    orders_succeeded=0,
                    orders_failed=0,
                    total_value=Decimal("0"),
                    success_rate=0.0,
                    execution_duration_seconds=1.0,
                ),
                trading_mode="PAPER",
                started_at=started,
                completed_at=completed,
                correlation_id="test-id",
                warnings=[f"warning{i}" for i in range(101)],  # 101 warnings
            )


class TestTypeAliases:
    """Test that type aliases are properly exported."""

    def test_order_action_type(self):
        """Test OrderAction type alias."""
        action: OrderAction = "BUY"
        assert action == "BUY"

        action = "SELL"
        assert action == "SELL"

    def test_execution_status_type(self):
        """Test ExecutionStatus type alias."""
        status: ExecutionStatus = "SUCCESS"
        assert status == "SUCCESS"

        status = "FAILURE"
        assert status == "FAILURE"

        status = "PARTIAL"
        assert status == "PARTIAL"

    def test_trading_mode_type(self):
        """Test TradingMode type alias."""
        mode: TradingMode = "PAPER"
        assert mode == "PAPER"

        mode = "LIVE"
        assert mode == "LIVE"
