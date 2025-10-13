"""Tests for trade_result_factory.py

Comprehensive test suite covering all factory functions, validation,
error handling, and edge cases as specified in the file review audit.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from the_alchemiser.shared.schemas.trade_result_factory import (
    ORDER_STATUS_SUCCESS,
    TRADING_MODE_LIVE,
    TRADING_MODE_PAPER,
    TRADING_MODE_UNKNOWN,
    _calculate_execution_summary,
    _calculate_trade_amount,
    _create_single_order_result,
    _determine_execution_status,
    _determine_trading_mode,
    create_failure_result,
    create_success_result,
)
from the_alchemiser.shared.schemas.trade_run_result import ExecutionSummary


class MockOrchestrator:
    """Mock orchestrator for testing."""

    def __init__(self, live: bool):
        self.live_trading = live


class TestCreateFailureResult:
    """Test create_failure_result factory function."""

    def test_creates_failure_dto_with_correct_status(self):
        """Test that failure result has status=FAILURE and success=False."""
        started_at = datetime.now(UTC)
        result = create_failure_result(
            error_message="Test error",
            started_at=started_at,
            correlation_id="test-123",
            warnings=["warning1"],
        )

        assert result.status == "FAILURE"
        assert result.success is False
        assert result.correlation_id == "test-123"
        assert result.trading_mode == TRADING_MODE_PAPER  # Defaults to PAPER for failures
        assert result.execution_summary.orders_total == 0
        assert "Test error" in result.warnings
        assert "warning1" in result.warnings

    def test_includes_error_in_warnings(self):
        """Test that error_message is appended to warnings list."""
        result = create_failure_result(
            error_message="Critical error",
            started_at=datetime.now(UTC),
            correlation_id="test-456",
            warnings=["warn1", "warn2"],
        )

        assert len(result.warnings) == 3
        assert result.warnings[-1] == "Critical error"

    def test_calculates_duration_correctly(self):
        """Test execution duration is calculated correctly."""
        started_at = datetime.now(UTC) - timedelta(seconds=10)
        result = create_failure_result(
            error_message="Error",
            started_at=started_at,
            correlation_id="test",
            warnings=[],
        )

        # Duration should be close to 10 seconds (allowing for test execution time)
        assert 9 <= result.execution_summary.execution_duration_seconds <= 11

    def test_accepts_explicit_completed_at(self):
        """Test that explicit completed_at parameter is used when provided."""
        started_at = datetime.now(UTC) - timedelta(seconds=5)
        completed_at = datetime.now(UTC)

        result = create_failure_result(
            error_message="Error",
            started_at=started_at,
            correlation_id="test",
            warnings=[],
            completed_at=completed_at,
        )

        assert result.completed_at == completed_at
        assert 4 <= result.execution_summary.execution_duration_seconds <= 6

    def test_raises_on_timezone_naive_started_at(self):
        """Test that timezone-naive started_at raises ValueError."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # No timezone

        with pytest.raises(ValueError, match="started_at must be timezone-aware"):
            create_failure_result(
                error_message="Error",
                started_at=naive_dt,
                correlation_id="test",
                warnings=[],
            )

    def test_raises_on_timezone_naive_completed_at(self):
        """Test that timezone-naive completed_at raises ValueError."""
        aware_dt = datetime.now(UTC)
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # No timezone

        with pytest.raises(ValueError, match="completed_at must be timezone-aware"):
            create_failure_result(
                error_message="Error",
                started_at=aware_dt,
                correlation_id="test",
                warnings=[],
                completed_at=naive_dt,
            )


class TestCreateSuccessResult:
    """Test create_success_result factory function."""

    def test_creates_success_dto_with_filled_orders(self):
        """Test success result with filled orders."""
        started_at = datetime.now(UTC) - timedelta(seconds=5)
        completed_at = datetime.now(UTC)

        trading_result = {
            "orders_executed": [
                {
                    "order_id": "abc123def456",
                    "symbol": "AAPL",
                    "side": "buy",
                    "qty": "10",
                    "filled_avg_price": 150.50,
                    "status": "filled",
                    "filled_at": completed_at,
                }
            ]
        }

        orchestrator = MockOrchestrator(live=False)
        result = create_success_result(
            trading_result=trading_result,
            orchestrator=orchestrator,
            started_at=started_at,
            completed_at=completed_at,
            correlation_id="test-789",
            warnings=[],
            success=True,
        )

        assert result.status == "SUCCESS"
        assert result.success is True
        assert result.trading_mode == TRADING_MODE_PAPER
        assert result.execution_summary.orders_total == 1
        assert result.execution_summary.orders_succeeded == 1
        assert len(result.orders) == 1
        assert result.orders[0].symbol == "AAPL"
        assert result.orders[0].shares == Decimal("10")

    def test_handles_empty_orders_list(self):
        """Test success result with no orders."""
        started_at = datetime.now(UTC)
        completed_at = datetime.now(UTC)

        trading_result = {"orders_executed": []}
        orchestrator = MockOrchestrator(live=True)

        result = create_success_result(
            trading_result=trading_result,
            orchestrator=orchestrator,
            started_at=started_at,
            completed_at=completed_at,
            correlation_id="test",
            warnings=[],
            success=True,
        )

        assert result.execution_summary.orders_total == 0
        assert result.execution_summary.success_rate == 1.0  # No orders = 100% success
        assert result.trading_mode == TRADING_MODE_LIVE

    def test_raises_on_timezone_naive_started_at(self):
        """Test that timezone-naive started_at raises ValueError."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        aware_dt = datetime.now(UTC)

        with pytest.raises(ValueError, match="started_at must be timezone-aware"):
            create_success_result(
                trading_result={"orders_executed": []},
                orchestrator=MockOrchestrator(live=False),
                started_at=naive_dt,
                completed_at=aware_dt,
                correlation_id="test",
                warnings=[],
                success=True,
            )

    def test_raises_on_timezone_naive_completed_at(self):
        """Test that timezone-naive completed_at raises ValueError."""
        aware_dt = datetime.now(UTC)
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)

        with pytest.raises(ValueError, match="completed_at must be timezone-aware"):
            create_success_result(
                trading_result={"orders_executed": []},
                orchestrator=MockOrchestrator(live=False),
                started_at=aware_dt,
                completed_at=naive_dt,
                correlation_id="test",
                warnings=[],
                success=True,
            )

    def test_raises_on_invalid_trading_result_type(self):
        """Test that non-dict trading_result raises ValueError."""
        aware_dt = datetime.now(UTC)

        with pytest.raises(ValueError, match="trading_result must be dict"):
            create_success_result(
                trading_result="invalid",  # type: ignore
                orchestrator=MockOrchestrator(live=False),
                started_at=aware_dt,
                completed_at=aware_dt,
                correlation_id="test",
                warnings=[],
                success=True,
            )

    def test_raises_on_invalid_orders_executed_type(self):
        """Test that non-list orders_executed raises ValueError."""
        aware_dt = datetime.now(UTC)

        with pytest.raises(ValueError, match="orders_executed must be list"):
            create_success_result(
                trading_result={"orders_executed": "invalid"},
                orchestrator=MockOrchestrator(live=False),
                started_at=aware_dt,
                completed_at=aware_dt,
                correlation_id="test",
                warnings=[],
                success=True,
            )


class TestCalculateTradeAmount:
    """Test _calculate_trade_amount function."""

    def test_uses_notional_when_present(self):
        """Test that notional value takes precedence."""
        order = {"notional": "1000.00"}
        amount = _calculate_trade_amount(order, Decimal("10"), 99.99)

        assert amount == Decimal("1000.00")

    def test_calculates_from_qty_and_price(self):
        """Test qty * price calculation."""
        order = {}
        amount = _calculate_trade_amount(order, Decimal("10"), 150.50)

        assert amount == Decimal("10") * Decimal("150.50")
        assert amount == Decimal("1505.00")

    def test_returns_zero_when_no_data(self):
        """Test zero returned when no qty or price."""
        order = {}
        amount = _calculate_trade_amount(order, Decimal("0"), None)

        assert amount == Decimal("0")

    def test_returns_zero_when_price_is_none(self):
        """Test zero returned when price is None."""
        order = {}
        amount = _calculate_trade_amount(order, Decimal("10"), None)

        assert amount == Decimal("0")


class TestDetermineExecutionStatus:
    """Test _determine_execution_status function."""

    def test_success_with_no_failures(self):
        """Test SUCCESS status when all orders succeeded."""
        summary = ExecutionSummary(
            orders_total=3,
            orders_succeeded=3,
            orders_failed=0,
            total_value=Decimal("1000"),
            success_rate=1.0,
            execution_duration_seconds=5.0,
        )

        status = _determine_execution_status(success=True, execution_summary=summary)
        assert status == "SUCCESS"

    def test_partial_with_mixed_results(self):
        """Test PARTIAL status when some orders failed."""
        summary = ExecutionSummary(
            orders_total=3,
            orders_succeeded=2,
            orders_failed=1,
            total_value=Decimal("500"),
            success_rate=0.67,
            execution_duration_seconds=5.0,
        )

        status = _determine_execution_status(success=True, execution_summary=summary)
        assert status == "PARTIAL"

    def test_failure_with_no_successes(self):
        """Test FAILURE status when all orders failed."""
        summary = ExecutionSummary(
            orders_total=2,
            orders_succeeded=0,
            orders_failed=2,
            total_value=Decimal("0"),
            success_rate=0.0,
            execution_duration_seconds=5.0,
        )

        status = _determine_execution_status(success=False, execution_summary=summary)
        assert status == "FAILURE"

    def test_failure_when_success_flag_false(self):
        """Test FAILURE status when success flag is False."""
        summary = ExecutionSummary(
            orders_total=2,
            orders_succeeded=0,
            orders_failed=2,
            total_value=Decimal("0"),
            success_rate=0.0,
            execution_duration_seconds=5.0,
        )

        status = _determine_execution_status(success=False, execution_summary=summary)
        assert status == "FAILURE"


class TestDetermineTradingMode:
    """Test _determine_trading_mode function."""

    def test_live_mode_when_live_trading_true(self):
        """Test LIVE mode returned when live_trading=True."""
        orchestrator = MockOrchestrator(live=True)
        mode = _determine_trading_mode(orchestrator)

        assert mode == TRADING_MODE_LIVE

    def test_paper_mode_when_live_trading_false(self):
        """Test PAPER mode returned when live_trading=False."""
        orchestrator = MockOrchestrator(live=False)
        mode = _determine_trading_mode(orchestrator)

        assert mode == TRADING_MODE_PAPER


class TestCreateSingleOrderResult:
    """Test _create_single_order_result function."""

    def test_redacts_order_id_correctly(self):
        """Test order ID redaction (last 6 chars)."""
        order = {
            "order_id": "abc123def456ghi789",
            "symbol": "AAPL",
            "side": "buy",
            "qty": "10",
            "filled_avg_price": 150.0,
            "status": "filled",
        }
        completed_at = datetime.now(UTC)

        result = _create_single_order_result(order, completed_at)

        assert result.order_id_redacted == "ghi789"  # Last 6 chars only
        assert result.order_id_full == "abc123def456ghi789"

    def test_handles_short_order_id(self):
        """Test order ID redaction with short ID."""
        order = {
            "order_id": "abc",
            "symbol": "AAPL",
            "side": "buy",
            "qty": "10",
            "status": "filled",
        }
        completed_at = datetime.now(UTC)

        result = _create_single_order_result(order, completed_at)

        assert result.order_id_redacted is None  # Too short, set to None

    def test_converts_decimals_correctly(self):
        """Test Decimal conversion from string and float."""
        order = {
            "order_id": "test123",
            "symbol": "SPY",
            "side": "sell",
            "qty": "100",
            "filled_avg_price": 420.69,
            "status": "filled",
        }
        completed_at = datetime.now(UTC)

        result = _create_single_order_result(order, completed_at)

        assert isinstance(result.shares, Decimal)
        assert result.shares == Decimal("100")
        assert isinstance(result.price, Decimal)
        assert result.price == Decimal("420.69")
        assert isinstance(result.trade_amount, Decimal)

    def test_marks_filled_orders_as_success(self):
        """Test that FILLED status marks order as successful."""
        order = {
            "order_id": "123",
            "symbol": "A",
            "side": "buy",
            "qty": "1",
            "status": "filled",
        }
        result = _create_single_order_result(order, datetime.now(UTC))

        assert result.success is True

    def test_marks_complete_orders_as_success(self):
        """Test that COMPLETE status marks order as successful."""
        order = {
            "order_id": "123",
            "symbol": "A",
            "side": "buy",
            "qty": "1",
            "status": "complete",
        }
        result = _create_single_order_result(order, datetime.now(UTC))

        assert result.success is True

    def test_marks_other_status_as_failure(self):
        """Test that non-FILLED/COMPLETE status marks order as failure."""
        order = {
            "order_id": "123",
            "symbol": "A",
            "side": "buy",
            "qty": "1",
            "status": "rejected",
        }
        result = _create_single_order_result(order, datetime.now(UTC))

        assert result.success is False

    def test_raises_on_invalid_order_type(self):
        """Test that non-dict order raises ValueError."""
        with pytest.raises(ValueError, match="Order must be dict"):
            _create_single_order_result("invalid", datetime.now(UTC))  # type: ignore

    def test_raises_on_timezone_naive_completed_at(self):
        """Test that timezone-naive completed_at raises ValueError."""
        order = {"order_id": "123", "symbol": "A", "side": "buy", "qty": "1", "status": "filled"}
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)

        with pytest.raises(ValueError, match="completed_at must be timezone-aware"):
            _create_single_order_result(order, naive_dt)

    def test_raises_on_invalid_qty(self):
        """Test that invalid qty raises ValueError."""
        order = {
            "order_id": "123",
            "symbol": "A",
            "side": "buy",
            "qty": "invalid",
            "status": "filled",
        }

        with pytest.raises(ValueError, match="Invalid qty in order"):
            _create_single_order_result(order, datetime.now(UTC))

    def test_raises_on_invalid_filled_price_type(self):
        """Test that invalid filled_avg_price type raises ValueError."""
        order = {
            "order_id": "123",
            "symbol": "A",
            "side": "buy",
            "qty": "10",
            "filled_avg_price": "invalid",  # String instead of number
            "status": "filled",
        }

        with pytest.raises(ValueError, match="Invalid filled_avg_price type"):
            _create_single_order_result(order, datetime.now(UTC))

    def test_handles_non_string_order_id(self):
        """Test that non-string order_id is converted to string."""
        order = {
            "order_id": 123456,  # Integer instead of string
            "symbol": "A",
            "side": "buy",
            "qty": "1",
            "status": "filled",
        }
        result = _create_single_order_result(order, datetime.now(UTC))

        assert isinstance(result.order_id_full, str)
        assert result.order_id_full == "123456"


class TestCalculateExecutionSummary:
    """Test _calculate_execution_summary function."""

    def test_calculates_summary_with_all_successes(self):
        """Test summary calculation with all successful orders."""
        from the_alchemiser.shared.schemas.trade_run_result import OrderResultSummary

        started_at = datetime.now(UTC) - timedelta(seconds=5)
        completed_at = datetime.now(UTC)

        orders = [
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000"),
                shares=Decimal("10"),
                price=Decimal("100"),
                order_id_redacted="123456",
                order_id_full="abc123def456",
                success=True,
                error_message=None,
                timestamp=completed_at,
            ),
            OrderResultSummary(
                symbol="GOOGL",
                action="BUY",
                trade_amount=Decimal("2000"),
                shares=Decimal("20"),
                price=Decimal("100"),
                order_id_redacted="789012",
                order_id_full="ghi789jkl012",
                success=True,
                error_message=None,
                timestamp=completed_at,
            ),
        ]

        summary = _calculate_execution_summary(orders, started_at, completed_at)

        assert summary.orders_total == 2
        assert summary.orders_succeeded == 2
        assert summary.orders_failed == 0
        assert summary.total_value == Decimal("3000")
        assert summary.success_rate == 1.0
        assert 4 <= summary.execution_duration_seconds <= 6

    def test_calculates_summary_with_mixed_results(self):
        """Test summary calculation with mixed success/failure."""
        from the_alchemiser.shared.schemas.trade_run_result import OrderResultSummary

        started_at = datetime.now(UTC) - timedelta(seconds=3)
        completed_at = datetime.now(UTC)

        orders = [
            OrderResultSummary(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000"),
                shares=Decimal("10"),
                price=Decimal("100"),
                order_id_redacted="123456",
                order_id_full="abc123",
                success=True,
                error_message=None,
                timestamp=completed_at,
            ),
            OrderResultSummary(
                symbol="GOOGL",
                action="BUY",
                trade_amount=Decimal("0"),
                shares=Decimal("0"),
                price=None,
                order_id_redacted="789012",
                order_id_full="def456",
                success=False,
                error_message="Insufficient funds",
                timestamp=completed_at,
            ),
        ]

        summary = _calculate_execution_summary(orders, started_at, completed_at)

        assert summary.orders_total == 2
        assert summary.orders_succeeded == 1
        assert summary.orders_failed == 1
        assert summary.total_value == Decimal("1000")
        assert summary.success_rate == 0.5

    def test_calculates_summary_with_empty_orders(self):
        """Test summary calculation with no orders."""
        started_at = datetime.now(UTC)
        completed_at = datetime.now(UTC)

        summary = _calculate_execution_summary([], started_at, completed_at)

        assert summary.orders_total == 0
        assert summary.orders_succeeded == 0
        assert summary.orders_failed == 0
        assert summary.total_value == Decimal("0")
        assert summary.success_rate == 1.0  # Empty = 100% success


class TestModuleConstants:
    """Test module-level constants."""

    def test_order_status_success_contains_expected_values(self):
        """Test ORDER_STATUS_SUCCESS contains FILLED and COMPLETE."""
        assert "FILLED" in ORDER_STATUS_SUCCESS
        assert "COMPLETE" in ORDER_STATUS_SUCCESS
        assert len(ORDER_STATUS_SUCCESS) == 2

    def test_trading_mode_constants_defined(self):
        """Test trading mode constants are defined correctly."""
        assert TRADING_MODE_UNKNOWN == "UNKNOWN"
        assert TRADING_MODE_LIVE == "LIVE"
        assert TRADING_MODE_PAPER == "PAPER"
