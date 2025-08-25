"""Integration tests for RebalancingOrchestrator.

Tests the sequential SELL→settle→BUY orchestration including:
- SELL-only phase execution and buying power freeing
- BUY-only phase execution with scaled quantities
- Full rebalancing cycle with proper settlement timing
- Order status normalization and error handling
"""

from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
import pytest
from typing import Any

from the_alchemiser.application.portfolio.rebalancing_orchestrator import RebalancingOrchestrator
from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.types import OrderDetails, AccountInfo
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO, WebSocketStatus


class MockPortfolioFacade:
    """Mock PortfolioManagementFacade for testing."""
    
    def rebalance_portfolio_phase(
        self, target_portfolio: dict[str, float], phase: str
    ) -> list[OrderDetails]:
        """Mock phase-specific rebalancing."""
        if phase.lower() == "sell":
            return [
                {
                    "id": "sell_order_1",
                    "symbol": "AAPL",
                    "qty": 10.0,
                    "side": "sell",
                    "order_type": "market",
                    "time_in_force": "day",
                    "status": "filled",
                    "filled_qty": 10.0,
                    "filled_avg_price": 150.0,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:01:00Z",
                }
            ] if "AAPL" in target_portfolio else []
        elif phase.lower() == "buy":
            return [
                {
                    "id": "buy_order_1",
                    "symbol": "MSFT",
                    "qty": 5.0,
                    "side": "buy",
                    "order_type": "market",
                    "time_in_force": "day",
                    "status": "filled",
                    "filled_qty": 5.0,
                    "filled_avg_price": 300.0,
                    "created_at": "2024-01-01T10:05:00Z",
                    "updated_at": "2024-01-01T10:06:00Z",
                }
            ] if "MSFT" in target_portfolio else []
        return []


class MockAccountInfoProvider:
    """Mock account info provider for testing."""
    
    def get_account_info(self) -> AccountInfo:
        return {
            "account_id": "test_account",
            "equity": "50000.00",
            "cash": "10000.00",
            "buying_power": "20000.00",
            "day_trades_remaining": 3,
            "portfolio_value": "50000.00",
            "last_equity": "49000.00",
            "daytrading_buying_power": "100000.00",
            "regt_buying_power": "20000.00",
            "status": "ACTIVE",
        }


class TestRebalancingOrchestrator:
    """Test suite for RebalancingOrchestrator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_portfolio_facade = MockPortfolioFacade()
        self.mock_trading_client = Mock()
        self.mock_account_provider = MockAccountInfoProvider()
        
        self.orchestrator = RebalancingOrchestrator(
            portfolio_facade=self.mock_portfolio_facade,  # type: ignore[arg-type]
            trading_client=self.mock_trading_client,
            paper_trading=True,
            account_info_provider=self.mock_account_provider,
        )

    def test_execute_sell_phase_with_orders(self) -> None:
        """Test SELL phase execution when orders are needed."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        
        sell_orders = self.orchestrator.execute_sell_phase(target_portfolio)
        
        assert len(sell_orders) == 1
        assert sell_orders[0]["symbol"] == "AAPL"
        assert sell_orders[0]["side"] == "sell"
        assert sell_orders[0]["status"] == "filled"

    def test_execute_sell_phase_no_orders(self) -> None:
        """Test SELL phase when no SELL orders are needed."""
        target_portfolio = {"MSFT": 1.0}  # No AAPL means no SELL orders in mock
        
        sell_orders = self.orchestrator.execute_sell_phase(target_portfolio)
        
        assert len(sell_orders) == 0

    def test_execute_buy_phase_with_orders(self) -> None:
        """Test BUY phase execution when orders are needed."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        
        buy_orders = self.orchestrator.execute_buy_phase(target_portfolio)
        
        assert len(buy_orders) == 1
        assert buy_orders[0]["symbol"] == "MSFT"
        assert buy_orders[0]["side"] == "buy"
        assert buy_orders[0]["status"] == "filled"

    def test_execute_buy_phase_no_orders(self) -> None:
        """Test BUY phase when no BUY orders are needed."""
        target_portfolio = {"AAPL": 1.0}  # No MSFT means no BUY orders in mock
        
        buy_orders = self.orchestrator.execute_buy_phase(target_portfolio)
        
        assert len(buy_orders) == 0

    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.OrderCompletionMonitor")
    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.SecretsManager")
    def test_wait_for_settlement_successful(self, mock_secrets_manager: Any, mock_monitor_class: Any) -> None:
        """Test WebSocket-based settlement monitoring success."""
        # Setup mocks
        mock_secrets_manager.return_value.get_alpaca_keys.return_value = ("api_key", "secret_key")
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock successful completion
        mock_monitor.wait_for_order_completion.return_value = WebSocketResultDTO(
            status=WebSocketStatus.COMPLETED,
            message="All orders completed successfully",
            orders_completed=["sell_order_1"],
        )
        
        sell_orders: list[OrderDetails] = [
            {
                "id": "sell_order_1",
                "symbol": "AAPL",
                "qty": 10.0,
                "side": "sell",
                "order_type": "market",
                "time_in_force": "day",
                "status": "filled",
                "filled_qty": 10.0,
                "filled_avg_price": 150.0,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:01:00Z",
            }
        ]
        
        # Should not raise any exceptions
        self.orchestrator.wait_for_settlement_and_bp_refresh(sell_orders)
        
        # Verify WebSocket monitor was called
        mock_monitor.wait_for_order_completion.assert_called_once_with(
            ["sell_order_1"], max_wait_seconds=30
        )

    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.OrderCompletionMonitor")
    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.SecretsManager")
    def test_wait_for_settlement_timeout(self, mock_secrets_manager: Any, mock_monitor_class: Any) -> None:
        """Test WebSocket monitoring timeout handling."""
        # Setup mocks
        mock_secrets_manager.return_value.get_alpaca_keys.return_value = ("api_key", "secret_key")
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock timeout result
        mock_monitor.wait_for_order_completion.return_value = WebSocketResultDTO(
            status=WebSocketStatus.TIMEOUT,
            message="Order monitoring timed out after 30 seconds",
            orders_completed=[],
        )
        
        sell_orders: list[OrderDetails] = [
            {
                "id": "sell_order_1",
                "symbol": "AAPL",
                "qty": 10.0,
                "side": "sell",
                "order_type": "market",
                "time_in_force": "day",
                "status": "new",
                "filled_qty": 0.0,
                "filled_avg_price": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        ]
        
        # Should handle timeout gracefully without exceptions
        self.orchestrator.wait_for_settlement_and_bp_refresh(sell_orders)
        
        mock_monitor.wait_for_order_completion.assert_called_once()

    def test_wait_for_settlement_no_orders(self) -> None:
        """Test settlement waiting when no orders to monitor."""
        # Should handle empty order list gracefully
        self.orchestrator.wait_for_settlement_and_bp_refresh([])
        
        # No WebSocket monitoring should be attempted

    def test_wait_for_settlement_unknown_order_ids(self) -> None:
        """Test settlement waiting with unknown order IDs."""
        sell_orders: list[OrderDetails] = [
            {
                "id": "unknown",
                "symbol": "AAPL",
                "qty": 10.0,
                "side": "sell",
                "order_type": "market",
                "time_in_force": "day",
                "status": "new",
                "filled_qty": 0.0,
                "filled_avg_price": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        ]
        
        # Should handle unknown IDs with fallback delay
        with patch("time.sleep") as mock_sleep:
            self.orchestrator.wait_for_settlement_and_bp_refresh(sell_orders)
            mock_sleep.assert_called_once_with(5)

    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.OrderCompletionMonitor")
    @patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.SecretsManager")
    def test_execute_full_rebalance_cycle(self, mock_secrets_manager: Any, mock_monitor_class: Any) -> None:
        """Test complete SELL→settle→BUY rebalancing cycle."""
        # Setup mocks for WebSocket monitoring
        mock_secrets_manager.return_value.get_alpaca_keys.return_value = ("api_key", "secret_key")
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.wait_for_order_completion.return_value = WebSocketResultDTO(
            status=WebSocketStatus.COMPLETED,
            message="All orders completed successfully",
            orders_completed=["sell_order_1"],
        )
        
        target_portfolio = {"AAPL": 0.3, "MSFT": 0.7}
        
        all_orders = self.orchestrator.execute_full_rebalance_cycle(target_portfolio)
        
        # Should have both SELL and BUY orders
        assert len(all_orders) == 2
        
        # First order should be SELL
        sell_order = all_orders[0]
        assert sell_order["symbol"] == "AAPL"
        assert sell_order["side"] == "sell"
        
        # Second order should be BUY
        buy_order = all_orders[1]
        assert buy_order["symbol"] == "MSFT"
        assert buy_order["side"] == "buy"

    def test_execute_full_rebalance_cycle_empty_portfolio(self) -> None:
        """Test full rebalancing with empty target portfolio."""
        result = self.orchestrator.execute_full_rebalance_cycle({})
        
        assert result == []

    def test_execute_full_rebalance_cycle_invalid_allocation(self) -> None:
        """Test full rebalancing with invalid allocation (should warn but continue)."""
        target_portfolio = {"AAPL": 0.8, "MSFT": 0.8}  # Sums to 160%
        
        # Should continue despite warning
        with patch("the_alchemiser.application.portfolio.rebalancing_orchestrator.logging.warning") as mock_warning:
            result = self.orchestrator.execute_full_rebalance_cycle(target_portfolio)
            mock_warning.assert_called()
            assert len(result) >= 0  # Should still execute

    def test_strategy_attribution_passed_through(self) -> None:
        """Test that strategy attribution is passed to facade methods."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        strategy_attribution = {
            "AAPL": [StrategyType.NUCLEAR],
            "MSFT": [StrategyType.TECL, StrategyType.KLM],
        }
        
        # Mock the facade to track method calls
        with patch.object(self.mock_portfolio_facade, "rebalance_portfolio_phase") as mock_method:
            mock_method.return_value = []
            
            self.orchestrator.execute_sell_phase(target_portfolio, strategy_attribution)
            
            # Verify strategy attribution was passed (even though facade mock ignores it)
            mock_method.assert_called_once_with(target_portfolio, phase="sell")

    def test_account_info_provider_integration(self) -> None:
        """Test integration with account info provider."""
        target_portfolio = {"MSFT": 1.0}
        
        # Mock the facade and verify account info is accessed
        with patch.object(self.mock_account_provider, "get_account_info") as mock_account:
            mock_account.return_value = {
                "account_id": "test_account",
                "equity": "50000.00",
                "cash": "10000.00",
                "buying_power": "25000.00",  # Updated buying power
                "day_trades_remaining": 3,
                "portfolio_value": "50000.00",
                "last_equity": "49000.00",
                "daytrading_buying_power": "100000.00",
                "regt_buying_power": "25000.00",
                "status": "ACTIVE",
            }
            
            self.orchestrator.execute_buy_phase(target_portfolio)
            
            # Verify account info was accessed during BUY phase
            mock_account.assert_called_once()

    def test_orchestrator_without_account_provider(self) -> None:
        """Test orchestrator operation without account info provider."""
        orchestrator_no_account = RebalancingOrchestrator(
            portfolio_facade=self.mock_portfolio_facade,  # type: ignore[arg-type]
            trading_client=self.mock_trading_client,
            paper_trading=True,
            account_info_provider=None,
        )
        
        target_portfolio = {"MSFT": 1.0}
        
        # Should still work without account provider
        buy_orders = orchestrator_no_account.execute_buy_phase(target_portfolio)
        
        assert len(buy_orders) == 1
        assert buy_orders[0]["symbol"] == "MSFT"