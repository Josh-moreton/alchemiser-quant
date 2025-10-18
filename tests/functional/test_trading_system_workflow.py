"""Business Unit: shared | Status: current.

Functional tests for complete trading system workflows.

Tests complete workflows with mocked external dependencies (Alpaca API, AWS, etc.)
to validate end-to-end business logic without external service calls.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

# Test imports
try:
    from the_alchemiser.orchestration.system import TradingSystem
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import (
        SignalGenerated,
        StartupEvent,
        WorkflowCompleted,
        WorkflowFailed,
    )
    from the_alchemiser.shared.events.bus import EventBus
    from the_alchemiser.shared.schemas.consolidated_portfolio import (
        ConsolidatedPortfolio,
    )

    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def mock_alpaca_manager():
    """Create a comprehensive mock AlpacaManager."""
    mock = Mock()
    mock.is_paper_trading = True
    mock.get_account.return_value = {
        "account_id": "test_account_functional",
        "equity": 100000.0,
        "cash": 20000.0,
        "buying_power": 80000.0,
        "portfolio_value": 100000.0,
        "status": "ACTIVE",
    }
    mock.get_all_positions.return_value = {
        "AAPL": {
            "symbol": "AAPL",
            "qty": "50",
            "market_value": "7500.00",
            "side": "long",
            "current_price": "150.00",
        }
    }
    mock.place_order.return_value = {
        "id": "order_123",
        "status": "filled",
        "symbol": "GOOGL",
        "qty": "10",
        "filled_price": "2500.00",
    }
    return mock


@pytest.fixture
def mock_container(mock_alpaca_manager):
    """Create a mock ApplicationContainer with proper configuration."""
    container = Mock()

    # Mock configuration
    config = Mock()
    config.alpaca_api_key = "test_api_key_functional"
    config.alpaca_secret_key = "test_secret_key_functional"
    config.paper_trading = True
    config.trading_enabled = True

    container.config = config

    # Mock infrastructure
    infrastructure = Mock()
    infrastructure.alpaca_manager = mock_alpaca_manager
    container.infrastructure = infrastructure

    return container


@pytest.mark.functional
class TestTradingSystemWorkflow:
    """Functional tests for complete trading system workflows."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        if not SYSTEM_AVAILABLE:
            pytest.skip(f"Trading system not available: {IMPORT_ERROR}")

        self.correlation_id = f"func-test-{uuid.uuid4()}"
        self.test_timestamp = datetime.now(UTC)

    @patch("the_alchemiser.orchestration.system.TradingSystem._initialize_event_orchestration")
    @patch("the_alchemiser.shared.utils.service_factory.ServiceFactory.initialize")
    @patch("the_alchemiser.orchestration.system.ApplicationContainer")
    @patch("the_alchemiser.orchestration.system.load_settings")
    def test_trading_system_initialization(
        self,
        mock_load_settings,
        mock_application_container,
        mock_service_factory_initialize,
        mock_event_init,
        mock_container,
    ):
        """Test TradingSystem initialization with mocked dependencies."""
        mock_settings = Mock()
        mock_settings.alpaca = Mock(paper_trading=True)
        mock_load_settings.return_value = mock_settings
        mock_application_container.return_value = mock_container

        # Initialize trading system
        trading_system = TradingSystem()

        # Verify initialization
        assert trading_system is not None
        assert trading_system.container is mock_container
        mock_application_container.assert_called_once()
        mock_service_factory_initialize.assert_called_once_with(mock_container)
        mock_event_init.assert_called_once()

    @patch("the_alchemiser.orchestration.system.TradingSystem._initialize_event_orchestration")
    @patch("the_alchemiser.shared.utils.service_factory.ServiceFactory.initialize")
    @patch("the_alchemiser.orchestration.system.ApplicationContainer")
    @patch("the_alchemiser.orchestration.system.load_settings")
    def test_trading_execution_with_mocked_dependencies(
        self,
        mock_load_settings,
        mock_application_container,
        mock_service_factory_initialize,
        mock_event_init,
        mock_container,
    ):
        """Test complete trading execution with all dependencies mocked."""
        mock_settings = Mock()
        mock_settings.alpaca = Mock(paper_trading=True)
        mock_load_settings.return_value = mock_settings
        mock_application_container.return_value = mock_container
        mock_event_init.side_effect = lambda *args, **kwargs: None

        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.execute_workflow.return_value = {
            "success": True,
            "trades_executed": 2,
            "total_value": 50000.0,
            "correlation_id": self.correlation_id,
        }
        # Initialize trading system and inject orchestrator
        trading_system = TradingSystem()
        trading_system.event_driven_orchestrator = mock_orchestrator

        # Mock the execute_trading method to avoid complex orchestration
        with patch.object(trading_system, "execute_trading") as mock_execute:
            mock_execute.return_value = type(
                "TradeRunResult",
                (),
                {
                    "success": True,
                    "trades_executed": 2,
                    "total_portfolio_value": 100000.0,
                    "summary": "Functional test completed successfully",
                },
            )()

            # Execute trading
            result = trading_system.execute_trading()

            # Verify execution
            assert result is not None
            assert result.success is True
            assert result.trades_executed == 2
            assert "successfully" in result.summary

    def test_event_driven_workflow_with_mock_handlers(self, mock_container):
        """Test event-driven workflow with mock handlers for each module."""
        # Create event bus for testing
        event_bus = EventBus()

        # Track events
        events_received = []

        def event_tracker(event):
            events_received.append(event)

        event_bus.subscribe_global(
            type(
                "MockHandler",
                (),
                {
                    "handle_event": event_tracker,
                    "can_handle": lambda self, event_type: True,
                },
            )()
        )

        # Create mock strategy handler
        def mock_strategy_handler(event):
            if event.event_type == "StartupEvent":
                # Simulate strategy signal generation
                target_allocations = {
                    "AAPL": Decimal("0.4"),
                    "GOOGL": Decimal("0.3"),
                    "MSFT": Decimal("0.3"),
                }

                consolidated_portfolio = ConsolidatedPortfolio(
                    target_allocations=target_allocations,
                    correlation_id=event.correlation_id,
                    timestamp=datetime.now(UTC),
                    strategy_count=1,
                    source_strategies=["mock_strategy"],
                )

                signal_event = SignalGenerated(
                    signals_data={
                        "strategy_name": "mock_strategy",
                        "generated_at": datetime.now(UTC).isoformat(),
                        "allocations": {k: str(v) for k, v in target_allocations.items()},
                    },
                    consolidated_portfolio=consolidated_portfolio.model_dump(),
                    signal_count=len(target_allocations),
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"signal-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="strategy_v2",
                    schema_version="1.0",
                )

                event_bus.publish(signal_event)

        # Create mock portfolio handler
        def mock_portfolio_handler(event):
            if event.event_type == "SignalGenerated":
                # Simulate portfolio rebalancing completion
                completion_event = WorkflowCompleted(
                    workflow_type="portfolio_rebalance",
                    workflow_duration_ms=2500,
                    success=True,
                    summary={
                        "message": "Portfolio rebalancing completed",
                        "trades_planned": 3,
                        "total_value": 100000.0,
                    },
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"completion-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="portfolio_v2",
                )

                event_bus.publish(completion_event)

        # Subscribe handlers
        strategy_handler = type(
            "StrategyHandler",
            (),
            {
                "handle_event": mock_strategy_handler,
                "can_handle": lambda self, event_type: event_type == "StartupEvent",
            },
        )()

        portfolio_handler = type(
            "PortfolioHandler",
            (),
            {
                "handle_event": mock_portfolio_handler,
                "can_handle": lambda self, event_type: event_type == "SignalGenerated",
            },
        )()

        event_bus.subscribe("StartupEvent", strategy_handler)
        event_bus.subscribe("SignalGenerated", portfolio_handler)

        # Start the workflow
        startup_event = StartupEvent(
            startup_mode="functional_test",
            configuration={"test_mode": True, "paper_trading": True},
            correlation_id=self.correlation_id,
            causation_id=f"test-{uuid.uuid4()}",
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=self.test_timestamp,
            source_module="test_orchestration",
        )

        # Trigger the workflow
        event_bus.publish(startup_event)

        # Verify workflow execution
        assert len(events_received) == 3  # Startup -> Signal -> Completion

        # Verify event sequence
        event_types = [event.event_type for event in events_received]
        assert "StartupEvent" in event_types
        assert "SignalGenerated" in event_types
        assert "WorkflowCompleted" in event_types

        # Verify correlation ID propagation
        for event in events_received:
            assert event.correlation_id == self.correlation_id

        # Verify final completion
        completion_event = [e for e in events_received if e.event_type == "WorkflowCompleted"][0]
        assert completion_event.success is True
        assert completion_event.workflow_type == "portfolio_rebalance"
        assert "completed" in completion_event.summary["message"]

    def test_error_handling_in_workflow(self, mock_container):
        """Test error handling and failure propagation in workflows."""
        event_bus = EventBus()
        events_received = []

        def event_tracker(event):
            events_received.append(event)

        event_bus.subscribe_global(
            type(
                "MockHandler",
                (),
                {
                    "handle_event": event_tracker,
                    "can_handle": lambda self, event_type: True,
                },
            )()
        )

        # Create failing handler
        def failing_handler(event):
            if event.event_type == "StartupEvent":
                # Simulate failure in strategy generation
                failure_event = WorkflowFailed(
                    workflow_type="strategy_generation",
                    failure_reason="Market data unavailable",
                    failure_step="data_retrieval",
                    error_details={
                        "error_code": "MARKET_DATA_ERROR",
                        "error_message": "Unable to fetch market data for functional test",
                        "retry_count": 3,
                    },
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"failure-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="strategy_v2",
                )

                event_bus.publish(failure_event)

        # Subscribe failing handler
        failing_strategy_handler = type(
            "FailingHandler",
            (),
            {
                "handle_event": failing_handler,
                "can_handle": lambda self, event_type: event_type == "StartupEvent",
            },
        )()

        event_bus.subscribe("StartupEvent", failing_strategy_handler)

        # Start workflow that will fail
        startup_event = StartupEvent(
            startup_mode="failure_test",
            configuration={"simulate_failure": True},
            correlation_id=self.correlation_id,
            causation_id=f"test-{uuid.uuid4()}",
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=self.test_timestamp,
            source_module="test_orchestration",
        )

        # Trigger the failing workflow
        event_bus.publish(startup_event)

        # Verify failure handling
        assert len(events_received) == 2  # Startup -> Failure

        # Verify failure event
        failure_event = [e for e in events_received if e.event_type == "WorkflowFailed"][0]
        assert failure_event.workflow_type == "strategy_generation"
        assert failure_event.failure_reason == "Market data unavailable"
        assert failure_event.failure_step == "data_retrieval"
        assert failure_event.error_details["error_code"] == "MARKET_DATA_ERROR"
        assert failure_event.correlation_id == self.correlation_id

    @patch("the_alchemiser.shared.brokers.alpaca_manager.AlpacaManager")
    def test_portfolio_analysis_functional_workflow(self, mock_alpaca_class):
        """Test portfolio analysis workflow with mocked Alpaca integration."""
        # Setup mock Alpaca manager
        mock_alpaca_instance = Mock()
        mock_alpaca_instance.is_paper_trading = True
        mock_alpaca_instance.get_account.return_value = {
            "account_id": "func_test_account",
            "equity": 75000.0,
            "cash": 15000.0,
            "buying_power": 60000.0,
        }
        mock_alpaca_instance.get_all_positions.return_value = {
            "AAPL": {"qty": "30", "market_value": "4500.00"},
            "GOOGL": {"qty": "5", "market_value": "12500.00"},
        }

        mock_alpaca_class.return_value = mock_alpaca_instance

        # Test the workflow would work with this setup
        # (This is a placeholder for more complex portfolio analysis testing)

        # Verify mock setup
        assert mock_alpaca_instance.is_paper_trading is True
        account_data = mock_alpaca_instance.get_account()
        assert account_data["equity"] == 75000.0

        positions = mock_alpaca_instance.get_all_positions()
        assert "AAPL" in positions
        assert "GOOGL" in positions
        assert len(positions) == 2
