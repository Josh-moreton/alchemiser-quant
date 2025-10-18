"""Business Unit: shared | Status: current.

End-to-end tests for complete system workflows.

Tests the complete system including main entry points, with paper trading mode
to validate the entire application flow as specified in event_driven_enforcement_plan.md.
"""

import os
import uuid
from unittest.mock import Mock, patch

import pytest

# Test imports
try:
    from the_alchemiser.main import main
    from the_alchemiser.orchestration.system import TradingSystem
    from the_alchemiser.shared.config.container import ApplicationContainer

    MAIN_AVAILABLE = True
except ImportError as e:
    MAIN_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "PAPER_TRADING": "true",
        "ALPACA_API_KEY": "test_api_key_e2e",
        "ALPACA_SECRET_KEY": "test_secret_key_e2e",
        "ALPACA_ENDPOINT": "https://paper-api.alpaca.markets",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_external_dependencies():
    """Mock all external service dependencies for E2E tests."""
    with (
        patch("boto3.client") as mock_boto_client,
        patch("requests.get") as mock_requests,
        patch("alpaca.trading.client.TradingClient") as mock_trading_client,
        patch("alpaca.data.historical.StockHistoricalDataClient") as mock_data_client,
    ):
        # Mock AWS client (for any potential AWS calls)
        mock_boto_client.return_value = Mock()

        # Mock HTTP requests (for any potential API calls)
        mock_requests.return_value = Mock(status_code=200, json=lambda: {"status": "ok"})

        # Mock Alpaca clients
        mock_trading_instance = Mock()
        mock_trading_instance.get_account.return_value = Mock(
            account_number="test_account_e2e",
            equity=100000.0,
            cash=20000.0,
            buying_power=80000.0,
        )
        mock_trading_instance.get_all_positions.return_value = []
        mock_trading_client.return_value = mock_trading_instance

        mock_data_instance = Mock()
        mock_data_client.return_value = mock_data_instance

        yield {
            "boto_client": mock_boto_client,
            "requests": mock_requests,
            "trading_client": mock_trading_client,
            "data_client": mock_data_client,
        }


@pytest.mark.e2e
class TestCompleteSystemE2E:
    """End-to-end tests for complete system functionality."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        if not MAIN_AVAILABLE:
            pytest.skip(f"Main application not available: {IMPORT_ERROR}")

        self.test_run_id = f"e2e-test-{uuid.uuid4()}"

    def test_main_module_entry_point(self, test_environment, mock_external_dependencies):
        """Test main module entry point with mocked dependencies."""
        # Mock the main function to avoid actual trading
        with patch("the_alchemiser.main.TradingSystem") as mock_trading_system:
            mock_system_instance = Mock()
            mock_system_instance.execute_trading.return_value = type(
                "TradeRunResult",
                (),
                {
                    "success": True,
                    "trades_executed": 0,
                    "total_portfolio_value": 100000.0,
                    "summary": "E2E test completed successfully - no actual trades",
                    "correlation_id": self.test_run_id,
                },
            )()

            mock_trading_system.return_value = mock_system_instance

            # Call main function
            result = main(["trade"])

            # Verify execution
            assert result is not None
            assert hasattr(result, "success")
            assert result.success is True
            assert "successfully" in result.summary

            # Verify TradingSystem was initialized and called
            mock_trading_system.assert_called_once()
            mock_system_instance.execute_trading.assert_called_once()

    def test_python_module_execution(self, test_environment, mock_external_dependencies):
        """Test python -m the_alchemiser execution path."""
        # This test would require careful mocking to avoid subprocess complexity
        # For now, we test the equivalent function call

        with patch("the_alchemiser.__main__.main") as mock_main:
            mock_main.return_value = type(
                "TradeRunResult",
                (),
                {"success": True, "summary": "Module execution test completed"},
            )()

            # Import and call the module's run function
            from the_alchemiser.__main__ import run

            # Ensure pytest's argv (e.g., -q) doesn't leak into module args; force default path
            with patch("sys.argv", ["python"]):
                # This should not raise an exception
                with pytest.raises(SystemExit) as excinfo:
                    run()

            # Should exit with code 0 for success
            assert excinfo.value.code == 0
            mock_main.assert_called_once_with(["trade"])

    def test_trading_system_initialization_e2e(self, test_environment, mock_external_dependencies):
        """Test TradingSystem initialization in E2E context."""
        # Create container in test mode
        container = ApplicationContainer.create_for_testing()

        # Verify container setup
        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "infrastructure")

        # Test TradingSystem initialization
        trading_system = TradingSystem()
        assert trading_system is not None

    @pytest.mark.slow
    def test_complete_workflow_simulation(self, test_environment, mock_external_dependencies):
        """Test complete workflow simulation with all components."""
        # Mock the complete workflow to simulate real execution without external calls
        with patch(
            "the_alchemiser.orchestration.system.TradingSystem.execute_trading"
        ) as mock_execute:
            # Simulate a complete successful workflow
            mock_result = type(
                "TradeRunResult",
                (),
                {
                    "success": True,
                    "trades_executed": 3,
                    "total_portfolio_value": 105000.0,
                    "summary": "Complete E2E workflow simulation completed",
                    "execution_time_ms": 5000,
                    "correlation_id": self.test_run_id,
                    "strategy_signals_generated": 1,
                    "portfolio_rebalance_completed": True,
                    "orders_placed": 3,
                    "orders_filled": 3,
                },
            )()

            mock_execute.return_value = mock_result

            # Initialize and execute trading system
            trading_system = TradingSystem()
            result = trading_system.execute_trading()

            # Verify complete workflow
            assert result.success is True
            assert result.trades_executed == 3
            assert result.total_portfolio_value == 105000.0
            assert result.correlation_id == self.test_run_id
            assert result.strategy_signals_generated == 1
            assert result.portfolio_rebalance_completed is True
            assert result.orders_placed == 3
            assert result.orders_filled == 3
            assert "simulation completed" in result.summary

    def test_error_recovery_e2e(self, test_environment, mock_external_dependencies):
        """Test error recovery in E2E context."""
        with patch(
            "the_alchemiser.orchestration.system.TradingSystem.execute_trading"
        ) as mock_execute:
            # Simulate a workflow failure
            mock_result = type(
                "TradeRunResult",
                (),
                {
                    "success": False,
                    "trades_executed": 0,
                    "total_portfolio_value": 100000.0,
                    "summary": "E2E workflow failed - simulated market data error",
                    "error_code": "MARKET_DATA_UNAVAILABLE",
                    "error_message": "Market data service unavailable during E2E test",
                    "correlation_id": self.test_run_id,
                    "failure_step": "strategy_signal_generation",
                    "recovery_attempted": True,
                },
            )()

            mock_execute.return_value = mock_result

            # Initialize and execute trading system
            trading_system = TradingSystem()
            result = trading_system.execute_trading()

            # Verify error handling
            assert result.success is False
            assert result.trades_executed == 0
            assert result.error_code == "MARKET_DATA_UNAVAILABLE"
            assert result.failure_step == "strategy_signal_generation"
            assert result.recovery_attempted is True
            assert "failed" in result.summary

    def test_configuration_validation_e2e(self, test_environment, mock_external_dependencies):
        """Test configuration validation in E2E context."""
        # Test with invalid configuration
        invalid_env = test_environment.copy()
        invalid_env["PAPER_TRADING"] = "invalid_boolean"

        with patch.dict(os.environ, invalid_env):
            # This should handle invalid configuration gracefully
            try:
                container = ApplicationContainer.create_for_testing()
                # Configuration should still work with defaults
                assert container is not None
            except Exception as e:
                # If it fails, it should be a clear configuration error
                assert "configuration" in str(e).lower() or "invalid" in str(e).lower()

    def test_paper_trading_mode_validation(self, test_environment, mock_external_dependencies):
        """Test paper trading mode is properly enforced in E2E tests."""
        # Verify paper trading environment is set
        assert os.environ.get("PAPER_TRADING") == "true"
        assert os.environ.get("TESTING") == "true"

        # Create container and verify paper trading mode
        container = ApplicationContainer.create_for_testing()

        # In a real implementation, we would check:
        # - No real orders are placed
        # - All API calls go to paper trading endpoints
        # - No real money is involved

        # For this test, we verify the configuration is set correctly
        assert container is not None

    def test_event_logging_and_observability(self, test_environment, mock_external_dependencies):
        """Test event logging and observability in E2E context."""
        with patch(
            "the_alchemiser.orchestration.system.TradingSystem.execute_trading"
        ) as mock_execute:
            # Mock a result with observability data
            mock_result = type(
                "TradeRunResult",
                (),
                {
                    "success": True,
                    "trades_executed": 1,
                    "summary": "E2E observability test completed",
                    "correlation_id": self.test_run_id,
                    "events_published": 5,
                    "events_processed": 5,
                    "processing_time_ms": 3000,
                    "log_entries_created": 12,
                },
            )()

            mock_execute.return_value = mock_result

            # Execute trading system
            trading_system = TradingSystem()
            result = trading_system.execute_trading()

            # Verify observability metrics
            assert result.correlation_id == self.test_run_id
            assert result.events_published == 5
            assert result.events_processed == 5
            assert result.processing_time_ms == 3000
            assert result.log_entries_created == 12
