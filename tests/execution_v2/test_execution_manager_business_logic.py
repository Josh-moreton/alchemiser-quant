"""Business Unit: execution | Status: current

Test execution manager business logic and coordination.

Tests the core business logic of trade execution coordination without external
broker dependencies, focusing on execution flow, result processing, and error handling.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)


def _make_order_result(
    symbol: str,
    *,
    action: str,
    shares: Decimal,
    trade_amount: Decimal,
    success: bool,
    price: Decimal | None = None,
    order_id: str | None = None,
    error_message: str | None = None,
):
    return OrderResult(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        shares=shares,
        price=price,
        order_id=order_id,
        success=success,
        error_message=error_message,
        timestamp=datetime.now(UTC),
        order_type="MARKET",  # Default to MARKET for tests
        filled_at=datetime.now(UTC) if success and price else None,  # Set filled_at if successful
    )


def _make_execution_result(
    *,
    success: bool,
    status: ExecutionStatus,
    orders: list[OrderResult],
    plan_id: str | None = None,
    correlation_id: str | None = None,
    total_trade_value: Decimal | None = None,
    metadata: dict | None = None,
) -> ExecutionResult:
    plan_identifier = plan_id or f"plan-{uuid.uuid4()}"
    correlation_identifier = correlation_id or f"corr-{uuid.uuid4()}"
    orders_placed = len(orders)
    orders_succeeded = sum(1 for order in orders if order.success)
    if total_trade_value is None:
        total_trade_value = sum(order.trade_amount for order in orders)

    return ExecutionResult(
        success=success,
        status=status,
        plan_id=plan_identifier,
        correlation_id=correlation_identifier,
        orders=orders,
        orders_placed=orders_placed,
        orders_succeeded=orders_succeeded,
        total_trade_value=total_trade_value,
        execution_timestamp=datetime.now(UTC),
        metadata=metadata or {},
    )


from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)


class TestExecutionManagerBusinessLogic:
    """Test execution manager business logic."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Mock Alpaca manager."""
        mock = Mock()
        mock.get_account.return_value = Mock(buying_power=Decimal("10000"))
        return mock

    @pytest.fixture
    def execution_config(self):
        """Sample execution configuration."""
        return ExecutionConfig(
            max_spread_percent=Decimal("0.40"),
            repeg_threshold_percent=Decimal("0.08"),
            max_repegs_per_order=3,
        )

    @pytest.fixture
    def sample_rebalance_plan(self):
        """Sample rebalance plan."""
        return RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("3750.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="BUY",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.15"),
                    weight_diff=Decimal("0.15"),
                    current_value=Decimal("0.00"),
                    target_value=Decimal("1500.00"),
                    trade_amount=Decimal("1500.00"),
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    action="SELL",
                    current_weight=Decimal("0.30"),
                    target_weight=Decimal("0.225"),
                    weight_diff=Decimal("-0.075"),
                    current_value=Decimal("3000.00"),
                    target_value=Decimal("2250.00"),
                    trade_amount=Decimal("-750.00"),
                    priority=2,
                ),
            ],
        )

    def test_execution_manager_initialization(self, mock_alpaca_manager, execution_config):
        """Test execution manager initialization."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            mock_executor.execute_rebalance_plan = AsyncMock()
            mock_executor_class.return_value = mock_executor

            manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

        assert manager.alpaca_manager is mock_alpaca_manager
        assert manager.enable_smart_execution is True
        mock_executor_class.assert_called_once()

    def test_execute_rebalance_plan_success(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test successful execution of rebalance plan."""
        # Mock successful execution result
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            success_orders = [
                _make_order_result(
                    symbol="AAPL",
                    action="BUY",
                    shares=Decimal("10"),
                    trade_amount=Decimal("1500.00"),
                    success=True,
                    price=Decimal("150.00"),
                    order_id="order-aapl",
                ),
                _make_order_result(
                    symbol="MSFT",
                    action="SELL",
                    shares=Decimal("5"),
                    trade_amount=Decimal("2250.00"),
                    success=True,
                    price=Decimal("450.00"),
                    order_id="order-msft",
                ),
            ]
            mock_executor.execute_rebalance_plan = AsyncMock(
                return_value=_make_execution_result(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    orders=success_orders,
                    total_trade_value=Decimal("3750.00"),
                )
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)

        # Should return successful execution result
        assert result.status is ExecutionStatus.SUCCESS
        assert len(result.orders) == 2
        assert result.total_trade_value == Decimal("3750.00")

        # Should have called executor with correct plan
        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)

    def test_execute_rebalance_plan_partial_success(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test execution with partial success."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            partial_orders = [
                _make_order_result(
                    symbol="AAPL",
                    action="BUY",
                    shares=Decimal("10"),
                    trade_amount=Decimal("1500.00"),
                    success=True,
                    price=Decimal("150.00"),
                    order_id="order-aapl",
                ),
                _make_order_result(
                    symbol="MSFT",
                    action="SELL",
                    shares=Decimal("5"),
                    trade_amount=Decimal("0.00"),
                    success=False,
                    price=None,
                    order_id="order-msft",
                    error_message="MSFT order rejected: insufficient buying power",
                ),
            ]
            mock_executor.execute_rebalance_plan = AsyncMock(
                return_value=_make_execution_result(
                    success=False,
                    status=ExecutionStatus.PARTIAL_SUCCESS,
                    orders=partial_orders,
                    total_trade_value=Decimal("1500.00"),
                )
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)

        # Should return partial success result
        assert result.status is ExecutionStatus.PARTIAL_SUCCESS
        assert len(result.orders) == 2
        failure_orders = [order for order in result.orders if not order.success]
        assert len(failure_orders) == 1
        assert "MSFT order rejected" in failure_orders[0].error_message

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)

    def test_execute_rebalance_plan_failure(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test execution failure handling."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            mock_executor.execute_rebalance_plan = AsyncMock(
                side_effect=RuntimeError("Market data unavailable")
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            with pytest.raises(RuntimeError, match="Market data unavailable"):
                execution_manager.execute_rebalance_plan(sample_rebalance_plan)

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)

    def test_execution_config_validation(self, mock_alpaca_manager):
        """Test that execution configuration is properly validated."""
        valid_config = ExecutionConfig(max_repegs_per_order=4)

        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            mock_executor.execute_rebalance_plan = AsyncMock()
            mock_executor_class.return_value = mock_executor

            manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=valid_config,
            )

        # Should initialize without error and reflect smart execution status
        assert manager.enable_smart_execution is True
        mock_executor_class.assert_called_once()

    def test_smart_execution_status_reflects_executor(self, mock_alpaca_manager, execution_config):
        """Execution manager exposes executor smart execution availability."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            smart_executor = Mock()
            smart_executor.enable_smart_execution = True
            smart_executor.execute_rebalance_plan = AsyncMock()
            mock_executor_class.return_value = smart_executor

            manager_smart = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )
        assert manager_smart.enable_smart_execution is True

        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            fallback_executor = Mock()
            fallback_executor.enable_smart_execution = False
            fallback_executor.execute_rebalance_plan = AsyncMock()
            mock_executor_class.return_value = fallback_executor

            manager_basic = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )
        assert manager_basic.enable_smart_execution is False

    def test_execution_result_processing(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test that execution results are properly processed."""
        # Mock execution with detailed results
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            detailed_order = _make_order_result(
                symbol="AAPL",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1500.00"),
                success=True,
                price=Decimal("150.00"),
                order_id="order-123",
            )
            mock_executor.execute_rebalance_plan = AsyncMock(
                return_value=_make_execution_result(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    orders=[detailed_order],
                    total_trade_value=Decimal("1500.00"),
                    metadata={"execution_time_ms": 1200, "commission": "0.00"},
                )
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)

        # Should preserve all execution details
        assert result.status is ExecutionStatus.SUCCESS
        assert result.total_trade_value == Decimal("1500.00")
        assert result.orders_succeeded == 1
        assert result.metadata == {"execution_time_ms": 1200, "commission": "0.00"}

        # Should preserve order details
        order = result.orders[0]
        assert order.symbol == "AAPL"
        assert order.action == "BUY"
        assert order.shares == Decimal("10")
        assert order.price == Decimal("150.00")

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)

    def test_empty_rebalance_plan_handling(self, mock_alpaca_manager, execution_config):
        """Test handling of rebalance plan with only HOLD actions (effectively empty)."""
        # Create a plan with only HOLD actions (effectively empty for execution)
        empty_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("1000.00"),
            total_trade_value=Decimal("0.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="HOLD",
                    current_weight=Decimal("1.0"),
                    target_weight=Decimal("1.0"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("1000.00"),
                    target_value=Decimal("1000.00"),
                    trade_amount=Decimal("0.00"),
                    priority=1,
                ),
            ],
        )

        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            mock_executor.execute_rebalance_plan = AsyncMock(
                return_value=_make_execution_result(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    orders=[],
                    total_trade_value=Decimal("0.00"),
                )
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            result = execution_manager.execute_rebalance_plan(empty_plan)

            # Should handle empty plan gracefully
            assert result.status is ExecutionStatus.SUCCESS
            assert len(result.orders) == 0
            assert result.total_trade_value == Decimal("0.00")

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(empty_plan)

    def test_execution_error_propagation(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test that execution errors are properly propagated."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            # Simulate broker connection error
            mock_executor.execute_rebalance_plan = AsyncMock(
                side_effect=ConnectionError("Broker API unavailable")
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            with pytest.raises(ConnectionError, match="Broker API unavailable"):
                execution_manager.execute_rebalance_plan(sample_rebalance_plan)

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)

    def test_execution_correlation_id_preservation(
        self, mock_alpaca_manager, execution_config, sample_rebalance_plan
    ):
        """Test that correlation IDs are preserved through execution."""
        correlation_id = sample_rebalance_plan.correlation_id

        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.Executor"
        ) as mock_executor_class:
            mock_executor = Mock()
            mock_executor.enable_smart_execution = True
            mock_executor.execute_rebalance_plan = AsyncMock(
                return_value=_make_execution_result(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    orders=[],
                    total_trade_value=Decimal("0.00"),
                    correlation_id=correlation_id,
                )
            )
            mock_executor_class.return_value = mock_executor

            execution_manager = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
            )

            result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)

            # Should preserve correlation ID for traceability
            assert hasattr(result, "correlation_id")
            if hasattr(result, "correlation_id"):
                assert result.correlation_id == correlation_id

        mock_executor.execute_rebalance_plan.assert_awaited_once_with(sample_rebalance_plan)
