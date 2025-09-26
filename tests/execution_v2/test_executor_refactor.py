"""Business Unit: execution | Status: current

Test executor refactoring to ensure new modular components work correctly.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.core.market_execution import MarketExecution
from the_alchemiser.execution_v2.core.phase_executor import PhaseExecutor
from the_alchemiser.execution_v2.core.rebalance_workflow import RebalanceWorkflow
from the_alchemiser.execution_v2.core.subscription_service import SubscriptionService
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.execution_result import ExecutionResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItemDTO


class TestExecutorRefactor:
    """Test the refactored executor components."""

    def test_executor_composition(self):
        """Test that Executor properly composes the new collaborators."""
        # Mock dependencies
        mock_alpaca = Mock(spec=AlpacaManager)
        mock_alpaca.api_key = "test_key"
        mock_alpaca.secret_key = "test_secret"
        mock_alpaca.is_paper_trading = True
        
        # Create executor with smart execution disabled to avoid WebSocket setup
        executor = Executor(mock_alpaca, enable_smart_execution=False)
        
        # Verify collaborators are created
        assert isinstance(executor.market_execution, MarketExecution)
        assert isinstance(executor.rebalance_workflow, RebalanceWorkflow)
        assert isinstance(executor.subscription_service, SubscriptionService)
        
        # Verify backward compatibility attributes
        assert executor.validator is executor.market_execution.validator
        assert executor.buying_power_service is executor.market_execution.buying_power_service

    def test_market_execution_creation(self):
        """Test MarketExecution can be created independently."""
        mock_alpaca = Mock(spec=AlpacaManager)
        
        market_execution = MarketExecution(mock_alpaca)
        
        assert market_execution.alpaca_manager is mock_alpaca
        assert market_execution.validator is not None
        assert market_execution.buying_power_service is not None

    def test_phase_executor_creation(self):
        """Test PhaseExecutor can be created independently."""
        mock_alpaca = Mock(spec=AlpacaManager)
        
        phase_executor = PhaseExecutor(mock_alpaca)
        
        assert phase_executor.alpaca_manager is mock_alpaca
        assert isinstance(phase_executor.market_execution, MarketExecution)

    def test_subscription_service_extract_symbols(self):
        """Test SubscriptionService can extract symbols from plan."""
        from datetime import datetime, UTC
        
        subscription_service = SubscriptionService(None, enable_subscriptions=False)
        
        # Create test plan with all required fields
        plan = RebalancePlanDTO(
            plan_id="test_plan",
            correlation_id="test_corr",
            causation_id="test_cause",
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("1300"),
            items=[
                RebalancePlanItemDTO(
                    symbol="AAPL",
                    current_weight=Decimal("0.3"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.2"),
                    target_value=Decimal("5000"),
                    current_value=Decimal("3000"),
                    trade_amount=Decimal("1000"),
                    action="BUY",
                    priority=1
                ),
                RebalancePlanItemDTO(
                    symbol="GOOGL",
                    current_weight=Decimal("0.4"),
                    target_weight=Decimal("0.3"), 
                    weight_diff=Decimal("-0.1"),
                    target_value=Decimal("3000"),
                    current_value=Decimal("4000"),
                    trade_amount=Decimal("-500"),
                    action="SELL",
                    priority=2
                ),
                RebalancePlanItemDTO(
                    symbol="MSFT",
                    current_weight=Decimal("0.2"),
                    target_weight=Decimal("0.2"),
                    weight_diff=Decimal("0.0"),
                    target_value=Decimal("2000"),
                    current_value=Decimal("2000"),
                    trade_amount=Decimal("0"),
                    action="HOLD",  # Should be excluded
                    priority=4
                )
            ]
        )
        
        symbols = subscription_service.extract_all_symbols(plan)
        
        # Should extract unique symbols, excluding HOLD actions, in sorted order
        assert symbols == ["AAPL", "GOOGL"]

    @pytest.mark.asyncio
    async def test_executor_execute_order_fallback(self):
        """Test that execute_order falls back to market execution when smart execution is disabled."""
        mock_alpaca = Mock(spec=AlpacaManager)
        mock_alpaca.api_key = "test_key"
        mock_alpaca.secret_key = "test_secret"
        mock_alpaca.is_paper_trading = True
        
        # Mock the market execution result
        expected_result = ExecutionResult(
            symbol="AAPL",
            side="buy", 
            quantity=Decimal("10"),
            status="submitted",
            success=True,
            execution_strategy="market_order"
        )
        
        executor = Executor(mock_alpaca, enable_smart_execution=False)
        
        # Mock the market execution method
        executor.market_execution.execute_market_order = Mock(return_value=expected_result)
        
        result = await executor.execute_order("AAPL", "buy", Decimal("10"))
        
        assert result == expected_result
        executor.market_execution.execute_market_order.assert_called_once_with(
            "AAPL", "buy", Decimal("10")
        )