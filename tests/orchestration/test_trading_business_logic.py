"""Business Unit: orchestration | Status: current

Test trading orchestrator business logic and decision-making.

Tests the core business logic of trading workflow coordination, including
signal processing, portfolio analysis, and execution decisions without external dependencies.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator


class TestTradingOrchestratorBusinessLogic:
    """Test trading orchestrator business logic and workflow decisions."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        return {
            "signal_orchestrator": Mock(),
            "portfolio_orchestrator": Mock(),
            "execution_orchestrator": Mock(),
            "notification_service": Mock(),
            "logger": Mock(),
        }

    @pytest.fixture
    def trading_orchestrator(self, mock_dependencies):
        """Create trading orchestrator with mocked dependencies."""
        orchestrator = TradingOrchestrator(
            signal_orchestrator=mock_dependencies["signal_orchestrator"],
            portfolio_orchestrator=mock_dependencies["portfolio_orchestrator"],
            execution_orchestrator=mock_dependencies["execution_orchestrator"],
            notification_service=mock_dependencies["notification_service"],
            live_trading=False,  # Paper trading for tests
        )
        orchestrator.logger = mock_dependencies["logger"]
        return orchestrator

    def test_workflow_state_initialization(self, trading_orchestrator):
        """Test that workflow state is properly initialized."""
        # Check initial workflow state
        state = trading_orchestrator.workflow_state

        assert "signal_generation_in_progress" in state
        assert "rebalancing_in_progress" in state
        assert "trading_in_progress" in state
        assert state["signal_generation_in_progress"] is False
        assert state["rebalancing_in_progress"] is False
        assert state["trading_in_progress"] is False

    def test_successful_signal_generation_workflow(self, trading_orchestrator, mock_dependencies):
        """Test successful signal generation workflow logic."""
        # Mock successful signal generation
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock(), Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        # Mock account data
        mock_account_data = {
            "account_info": Mock(buying_power=Decimal("10000")),
            "current_positions": {"AAPL": Decimal("10")},
            "open_orders": [],
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = mock_account_data

        result = trading_orchestrator.execute_strategy_signals()

        # Should complete signal generation successfully
        assert result is not None
        assert result.get("success") is True
        assert trading_orchestrator.workflow_state["signal_generation_in_progress"] is False
        assert trading_orchestrator.workflow_state["last_successful_step"] == "signal_generation"

    def test_signal_generation_failure_handling(self, trading_orchestrator, mock_dependencies):
        """Test signal generation failure handling."""
        # Mock signal generation failure
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = None

        result = trading_orchestrator.execute_strategy_signals()

        # Should handle failure gracefully
        assert result is None
        assert trading_orchestrator.workflow_state["signal_generation_in_progress"] is False

    def test_account_data_requirement_for_trading(self, trading_orchestrator, mock_dependencies):
        """Test that account data is required for trading workflow."""
        # Mock successful signal generation
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        # Mock missing account data
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = None

        result = trading_orchestrator.execute_strategy_signals_with_trading()

        # Should fail due to missing account data
        assert result is None

    def test_trading_workflow_phase_progression(self, trading_orchestrator, mock_dependencies):
        """Test that trading workflow progresses through phases correctly."""
        # Mock all phases to succeed
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        mock_account_data = {
            "account_info": Mock(buying_power=Decimal("10000")),
            "current_positions": {"AAPL": Decimal("10")},
            "open_orders": [],
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = mock_account_data

        mock_allocation_comparison = {
            "target_allocations": {"AAPL": Decimal("0.5"), "MSFT": Decimal("0.5")},
            "needs_rebalancing": True,
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].analyze_allocation_comparison.return_value = mock_allocation_comparison

        # Mock successful rebalance plan creation
        mock_rebalance_plan = Mock()
        mock_rebalance_plan.items = [Mock()]  # Non-empty plan
        mock_dependencies[
            "portfolio_orchestrator"
        ].create_rebalance_plan.return_value = mock_rebalance_plan

        # Mock successful execution
        mock_execution_result = {
            "success": True,
            "orders_placed": 2,
            "total_value": Decimal("5000"),
        }
        mock_dependencies[
            "execution_orchestrator"
        ].execute_rebalance_plan.return_value = mock_execution_result

        result = trading_orchestrator.execute_strategy_signals_with_trading()

        # Should complete all phases
        assert result is not None
        assert result.get("success") is True

        # Should have proper workflow state tracking
        state = trading_orchestrator.workflow_state
        assert state["last_successful_step"] is not None

    def test_rebalancing_decision_logic(self, trading_orchestrator, mock_dependencies):
        """Test rebalancing decision logic based on allocation comparison."""
        # Mock signal generation success
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        mock_account_data = {
            "account_info": Mock(buying_power=Decimal("10000")),
            "current_positions": {"AAPL": Decimal("10")},
            "open_orders": [],
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = mock_account_data

        # Mock allocation comparison that doesn't need rebalancing
        mock_allocation_comparison = {
            "target_allocations": {"AAPL": Decimal("1.0")},
            "needs_rebalancing": False,
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].analyze_allocation_comparison.return_value = mock_allocation_comparison

        result = trading_orchestrator.execute_strategy_signals_with_trading()

        # Should complete without creating rebalance plan
        assert result is not None
        # Should not call execution if no rebalancing needed
        mock_dependencies["execution_orchestrator"].execute_rebalance_plan.assert_not_called()

    def test_correlation_id_propagation(self, trading_orchestrator, mock_dependencies):
        """Test that correlation IDs are properly propagated through workflow."""
        # Mock signal generation
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        result = trading_orchestrator.execute_strategy_signals()

        # Should generate and track correlation ID
        assert "last_correlation_id" in trading_orchestrator.workflow_state
        correlation_id = trading_orchestrator.workflow_state["last_correlation_id"]
        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_error_handling_in_workflow_phases(self, trading_orchestrator, mock_dependencies):
        """Test error handling across different workflow phases."""
        # Mock signal generation to succeed but portfolio analysis to fail
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        # Mock portfolio orchestrator to raise exception
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.side_effect = Exception("Portfolio service unavailable")

        result = trading_orchestrator.execute_strategy_signals_with_trading()

        # Should handle error gracefully
        assert result is None

    def test_paper_vs_live_trading_mode_handling(self, mock_dependencies):
        """Test different behavior between paper and live trading modes."""
        # Paper trading orchestrator
        paper_orchestrator = TradingOrchestrator(
            signal_orchestrator=mock_dependencies["signal_orchestrator"],
            portfolio_orchestrator=mock_dependencies["portfolio_orchestrator"],
            execution_orchestrator=mock_dependencies["execution_orchestrator"],
            notification_service=mock_dependencies["notification_service"],
            live_trading=False,
        )

        # Live trading orchestrator
        live_orchestrator = TradingOrchestrator(
            signal_orchestrator=mock_dependencies["signal_orchestrator"],
            portfolio_orchestrator=mock_dependencies["portfolio_orchestrator"],
            execution_orchestrator=mock_dependencies["execution_orchestrator"],
            notification_service=mock_dependencies["notification_service"],
            live_trading=True,
        )

        # Both should be initialized but with different modes
        assert paper_orchestrator.live_trading is False
        assert live_orchestrator.live_trading is True

    def test_workflow_state_tracking_across_phases(self, trading_orchestrator, mock_dependencies):
        """Test that workflow state is properly tracked across execution phases."""
        # Start workflow
        trading_orchestrator.workflow_state.update(
            {
                "signal_generation_in_progress": True,
                "last_successful_step": None,
            }
        )

        # Mock successful signal generation
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        mock_account_data = {
            "account_info": Mock(buying_power=Decimal("10000")),
            "current_positions": {},
            "open_orders": [],
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = mock_account_data

        trading_orchestrator.execute_strategy_signals()

        # Check workflow state progression
        state = trading_orchestrator.workflow_state
        assert state["signal_generation_in_progress"] is False
        assert state["last_successful_step"] == "signal_generation"

    def test_empty_signal_result_handling(self, trading_orchestrator, mock_dependencies):
        """Test handling of empty or invalid signal results."""
        # Mock empty signal result
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = {
            "consolidated_portfolio_dto": None,
            "strategy_signals": [],
            "success": False,
        }

        result = trading_orchestrator.execute_strategy_signals()

        # Should handle empty results gracefully
        assert result is None

    def test_execution_result_processing(self, trading_orchestrator, mock_dependencies):
        """Test that execution results are properly processed and returned."""
        # Mock complete successful workflow
        mock_signal_result = {
            "consolidated_portfolio_dto": Mock(),
            "strategy_signals": [Mock()],
            "success": True,
        }
        mock_dependencies["signal_orchestrator"].analyze_signals.return_value = mock_signal_result

        mock_account_data = {
            "account_info": Mock(buying_power=Decimal("10000")),
            "current_positions": {"AAPL": Decimal("5")},
            "open_orders": [],
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].get_comprehensive_account_data.return_value = mock_account_data

        mock_allocation_comparison = {
            "needs_rebalancing": True,
        }
        mock_dependencies[
            "portfolio_orchestrator"
        ].analyze_allocation_comparison.return_value = mock_allocation_comparison

        mock_rebalance_plan = Mock()
        mock_rebalance_plan.items = [Mock()]  # Non-empty
        mock_dependencies[
            "portfolio_orchestrator"
        ].create_rebalance_plan.return_value = mock_rebalance_plan

        mock_execution_result = {
            "success": True,
            "orders_placed": 3,
            "orders_succeeded": 3,
            "total_value": Decimal("7500"),
            "execution_time_ms": 2500,
        }
        mock_dependencies[
            "execution_orchestrator"
        ].execute_rebalance_plan.return_value = mock_execution_result

        result = trading_orchestrator.execute_strategy_signals_with_trading()

        # Should return comprehensive result
        assert result is not None
        assert result["success"] is True
        assert "strategy_signals" in result
        assert "account_data" in result
        assert "execution_result" in result
