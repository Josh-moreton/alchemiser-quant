"""Business Unit: execution | Status: current

Test execution manager business logic and coordination.

Tests the core business logic of trade execution coordination without external
broker dependencies, focusing on execution flow, result processing, and error handling.
"""

from decimal import Decimal
from unittest.mock import Mock, patch
import uuid

import pytest

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.execution_v2.models.execution_result import ExecutionResult, OrderResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


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
            max_order_value=Decimal("5000"),
            min_order_value=Decimal("10"),
            timeout_seconds=30,
            allow_fractional_shares=True,
            dry_run=False,
        )

    @pytest.fixture
    def execution_manager(self, mock_alpaca_manager, execution_config):
        """Create execution manager instance."""
        return ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=True,
            enable_trade_ledger=False,
        )

    @pytest.fixture
    def sample_rebalance_plan(self):
        """Sample rebalance plan."""
        return RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="BUY",
                    current_quantity=Decimal("0"),
                    target_quantity=Decimal("10"),
                    target_value=Decimal("1500.00"),
                    target_allocation_pct=Decimal("15.0"),
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    action="SELL",
                    current_quantity=Decimal("20"),
                    target_quantity=Decimal("15"),
                    target_value=Decimal("2250.00"),
                    target_allocation_pct=Decimal("22.5"),
                ),
            ],
        )

    def test_execution_manager_initialization(self, mock_alpaca_manager, execution_config):
        """Test execution manager initialization."""
        manager = ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=True,
            enable_trade_ledger=False,
        )
        
        assert manager.alpaca_manager is mock_alpaca_manager
        assert manager.enable_smart_execution is True
        assert manager.enable_trade_ledger is False

    @patch('the_alchemiser.execution_v2.core.execution_manager.Executor')
    def test_execute_rebalance_plan_success(self, mock_executor_class, execution_manager, sample_rebalance_plan):
        """Test successful execution of rebalance plan."""
        # Mock successful execution result
        mock_executor = Mock()
        mock_executor.execute_rebalance_plan.return_value = ExecutionResult(
            status="SUCCESS",
            orders=[
                OrderResult(symbol="AAPL", status="FILLED", quantity=Decimal("10")),
                OrderResult(symbol="MSFT", status="FILLED", quantity=Decimal("-5")),
            ],
            total_value=Decimal("3750.00"),
            execution_time_ms=1500,
        )
        mock_executor_class.return_value = mock_executor
        
        result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)
        
        # Should return successful execution result
        assert result.status == "SUCCESS"
        assert len(result.orders) == 2
        assert result.total_value == Decimal("3750.00")
        
        # Should have called executor with correct plan
        mock_executor.execute_rebalance_plan.assert_called_once_with(sample_rebalance_plan)

    @patch('the_alchemiser.execution_v2.core.execution_manager.Executor')
    def test_execute_rebalance_plan_partial_success(self, mock_executor_class, execution_manager, sample_rebalance_plan):
        """Test execution with partial success."""
        mock_executor = Mock()
        mock_executor.execute_rebalance_plan.return_value = ExecutionResult(
            status="PARTIAL_SUCCESS",
            orders=[
                OrderResult(symbol="AAPL", status="FILLED", quantity=Decimal("10")),
                OrderResult(symbol="MSFT", status="REJECTED", quantity=Decimal("0")),
            ],
            total_value=Decimal("1500.00"),
            execution_time_ms=2000,
            errors=["MSFT order rejected: insufficient buying power"],
        )
        mock_executor_class.return_value = mock_executor
        
        result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)
        
        # Should return partial success result
        assert result.status == "PARTIAL_SUCCESS"
        assert len(result.orders) == 2
        assert len(result.errors) == 1
        assert "MSFT order rejected" in result.errors[0]

    @patch('the_alchemiser.execution_v2.core.execution_manager.Executor')
    def test_execute_rebalance_plan_failure(self, mock_executor_class, execution_manager, sample_rebalance_plan):
        """Test execution failure handling."""
        mock_executor = Mock()
        mock_executor.execute_rebalance_plan.side_effect = Exception("Market data unavailable")
        mock_executor_class.return_value = mock_executor
        
        with pytest.raises(Exception, match="Market data unavailable"):
            execution_manager.execute_rebalance_plan(sample_rebalance_plan)

    def test_execution_config_validation(self, mock_alpaca_manager):
        """Test that execution configuration is properly validated."""
        valid_config = ExecutionConfig(
            max_order_value=Decimal("5000"),
            min_order_value=Decimal("10"),
            timeout_seconds=30,
            allow_fractional_shares=True,
        )
        
        manager = ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=valid_config,
        )
        
        # Should initialize without error
        assert manager is not None

    def test_smart_execution_toggle(self, mock_alpaca_manager, execution_config):
        """Test smart execution can be enabled/disabled."""
        # With smart execution enabled
        manager_smart = ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=True,
        )
        assert manager_smart.enable_smart_execution is True
        
        # With smart execution disabled
        manager_basic = ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=False,
        )
        assert manager_basic.enable_smart_execution is False

    def test_trade_ledger_toggle(self, mock_alpaca_manager, execution_config):
        """Test trade ledger can be enabled/disabled."""
        # With trade ledger enabled
        with patch('the_alchemiser.execution_v2.core.execution_manager.TradeLedgerWriter'):
            manager_with_ledger = ExecutionManager(
                alpaca_manager=mock_alpaca_manager,
                execution_config=execution_config,
                enable_trade_ledger=True,
            )
            assert manager_with_ledger.enable_trade_ledger is True
        
        # With trade ledger disabled
        manager_no_ledger = ExecutionManager(
            alpaca_manager=mock_alpaca_manager,
            execution_config=execution_config,
            enable_trade_ledger=False,
        )
        assert manager_no_ledger.enable_trade_ledger is False

    @patch('the_alchemiser.execution_v2.core.execution_manager.Executor')
    def test_execution_result_processing(self, mock_executor_class, execution_manager, sample_rebalance_plan):
        """Test that execution results are properly processed."""
        # Mock execution with detailed results
        mock_executor = Mock()
        mock_executor.execute_rebalance_plan.return_value = ExecutionResult(
            status="SUCCESS",
            orders=[
                OrderResult(
                    symbol="AAPL", 
                    status="FILLED", 
                    quantity=Decimal("10"),
                    filled_price=Decimal("150.00"),
                    order_id="order_123",
                ),
            ],
            total_value=Decimal("1500.00"),
            execution_time_ms=1200,
            commission=Decimal("0.00"),
        )
        mock_executor_class.return_value = mock_executor
        
        result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)
        
        # Should preserve all execution details
        assert result.status == "SUCCESS"
        assert result.total_value == Decimal("1500.00")
        assert result.execution_time_ms == 1200
        assert result.commission == Decimal("0.00")
        
        # Should preserve order details
        order = result.orders[0]
        assert order.symbol == "AAPL"
        assert order.status == "FILLED"
        assert order.quantity == Decimal("10")
        assert order.filled_price == Decimal("150.00")

    def test_empty_rebalance_plan_handling(self, execution_manager):
        """Test handling of empty rebalance plan."""
        empty_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            items=[],
        )
        
        with patch('the_alchemiser.execution_v2.core.execution_manager.Executor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.execute_rebalance_plan.return_value = ExecutionResult(
                status="SUCCESS",
                orders=[],
                total_value=Decimal("0.00"),
                execution_time_ms=10,
            )
            mock_executor_class.return_value = mock_executor
            
            result = execution_manager.execute_rebalance_plan(empty_plan)
            
            # Should handle empty plan gracefully
            assert result.status == "SUCCESS"
            assert len(result.orders) == 0
            assert result.total_value == Decimal("0.00")

    def test_execution_error_propagation(self, execution_manager, sample_rebalance_plan):
        """Test that execution errors are properly propagated."""
        with patch('the_alchemiser.execution_v2.core.execution_manager.Executor') as mock_executor_class:
            mock_executor = Mock()
            # Simulate broker connection error
            mock_executor.execute_rebalance_plan.side_effect = ConnectionError("Broker API unavailable")
            mock_executor_class.return_value = mock_executor
            
            with pytest.raises(ConnectionError, match="Broker API unavailable"):
                execution_manager.execute_rebalance_plan(sample_rebalance_plan)

    def test_execution_correlation_id_preservation(self, execution_manager, sample_rebalance_plan):
        """Test that correlation IDs are preserved through execution."""
        correlation_id = sample_rebalance_plan.correlation_id
        
        with patch('the_alchemiser.execution_v2.core.execution_manager.Executor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.execute_rebalance_plan.return_value = ExecutionResult(
                status="SUCCESS",
                orders=[],
                total_value=Decimal("0.00"),
                execution_time_ms=50,
                correlation_id=correlation_id,  # Should preserve correlation ID
            )
            mock_executor_class.return_value = mock_executor
            
            result = execution_manager.execute_rebalance_plan(sample_rebalance_plan)
            
            # Should preserve correlation ID for traceability
            assert hasattr(result, 'correlation_id')
            if hasattr(result, 'correlation_id'):
                assert result.correlation_id == correlation_id