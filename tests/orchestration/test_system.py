"""Business Unit: orchestration | Status: current

Unit tests for system.py orchestration components.

Tests TradingSystem initialization, DI wiring, and MinimalOrchestrator.
"""

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.orchestration.system import MinimalOrchestrator, TradingSystem


class TestMinimalOrchestrator:
    """Test MinimalOrchestrator adapter class."""

    def test_minimal_orchestrator_paper_trading_mode(self):
        """Test MinimalOrchestrator in paper trading mode."""
        orchestrator = MinimalOrchestrator(paper_trading=True)

        assert orchestrator.live_trading is False

    def test_minimal_orchestrator_live_trading_mode(self):
        """Test MinimalOrchestrator in live trading mode."""
        orchestrator = MinimalOrchestrator(paper_trading=False)

        assert orchestrator.live_trading is True

    def test_minimal_orchestrator_initialization(self):
        """Test MinimalOrchestrator initializes with required attributes."""
        orchestrator = MinimalOrchestrator(paper_trading=True)

        # Verify it has the live_trading attribute
        assert hasattr(orchestrator, "live_trading")


class TestTradingSystemInitialization:
    """Test TradingSystem initialization and setup."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.paper_trading = True
        return settings

    def test_trading_system_initializes_with_default_settings(self):
        """Test TradingSystem initializes with default settings when none provided."""
        with patch("the_alchemiser.orchestration.system.load_settings") as mock_load:
            mock_settings = Mock()
            mock_load.return_value = mock_settings

            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch(
                        "the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"
                    ) as mock_edo:
                        system = TradingSystem()

                        # Verify settings were loaded
                        mock_load.assert_called_once()
                        assert system.settings == mock_settings

    def test_trading_system_uses_provided_settings(self, mock_settings):
        """Test TradingSystem uses provided settings instead of loading."""
        with patch("the_alchemiser.orchestration.system.load_settings") as mock_load:
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem(settings=mock_settings)

                        # Verify settings were not loaded (provided settings used)
                        mock_load.assert_not_called()
                        assert system.settings == mock_settings

    def test_trading_system_initializes_error_handler(self):
        """Test TradingSystem initializes error handler."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        assert system.error_handler is not None
                        assert hasattr(system.error_handler, "__class__")

    def test_trading_system_initializes_logger(self):
        """Test TradingSystem initializes logger."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        assert system.logger is not None


class TestTradingSystemDIInitialization:
    """Test TradingSystem dependency injection initialization."""

    def test_initialize_di_creates_container(self):
        """Test that _initialize_di creates ApplicationContainer."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch(
                "the_alchemiser.orchestration.system.ApplicationContainer"
            ) as mock_container_class:
                mock_container_instance = Mock()
                mock_container_class.create_for_environment.return_value = mock_container_instance

                with patch("the_alchemiser.orchestration.system.ServiceFactory") as mock_sf:
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        # Verify container was created via create_for_environment
                        mock_container_class.create_for_environment.assert_called_once_with("development")
                        assert system.container == mock_container_instance

    def test_initialize_di_initializes_service_factory(self):
        """Test that _initialize_di calls ServiceFactory.initialize."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory") as mock_sf:
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        # Verify ServiceFactory.initialize was called
                        mock_sf.initialize.assert_called_once()


class TestTradingSystemEventOrchestration:
    """Test TradingSystem event orchestration initialization."""

    def test_initialize_event_orchestration_creates_orchestrator(self):
        """Test that _initialize_event_orchestration creates EventDrivenOrchestrator."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch(
                        "the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"
                    ) as mock_edo:
                        mock_orchestrator_instance = Mock()
                        mock_edo.return_value = mock_orchestrator_instance

                        system = TradingSystem()

                        # Verify EventDrivenOrchestrator was created
                        mock_edo.assert_called_once_with(system.container)
                        assert system.event_driven_orchestrator == mock_orchestrator_instance

    def test_initialize_event_orchestration_raises_if_no_container(self):
        """Test that _initialize_event_orchestration raises RuntimeError if container is None."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            # Manually create system and set container to None
            with patch(
                "the_alchemiser.orchestration.system.ApplicationContainer"
            ) as mock_container_class:
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        # Manually break the container
                        system.container = None

                        # Now try to initialize event orchestration
                        with pytest.raises(RuntimeError) as exc_info:
                            system._initialize_event_orchestration()

                        assert "DI container not ready" in str(exc_info.value)


class TestTradingSystemEmitStartupEvent:
    """Test TradingSystem startup event emission."""

    @pytest.fixture
    def mock_system(self):
        """Create a mock TradingSystem for testing."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()

                        # Mock the event bus
                        system.container.services = Mock()
                        mock_event_bus = Mock()
                        system.container.services.event_bus.return_value = mock_event_bus

                        return system

    def test_emit_startup_event_publishes_to_event_bus(self, mock_system):
        """Test that _emit_startup_event publishes StartupEvent to event bus."""
        # Call the method
        mock_system._emit_startup_event("paper")

        # Get the event bus
        event_bus = mock_system.container.services.event_bus()

        # Verify publish was called
        assert event_bus.publish.called

        # Get the published event
        published_event = event_bus.publish.call_args[0][0]

        # Verify event properties
        assert published_event.event_type == "StartupEvent"
        assert published_event.startup_mode == "paper"
        assert published_event.source_module == "orchestration.system"

    def test_emit_startup_event_includes_configuration(self, mock_system):
        """Test that startup event includes configuration details."""
        mock_system.container.config.paper_trading = Mock(return_value=True)

        mock_system._emit_startup_event("paper")

        # Get the published event
        event_bus = mock_system.container.services.event_bus()
        published_event = event_bus.publish.call_args[0][0]

        # Verify configuration is included
        assert published_event.configuration is not None
        assert isinstance(published_event.configuration, dict)


class TestTradingSystemExecuteTrading:
    """Test TradingSystem execute_trading method."""

    @pytest.fixture
    def mock_system(self):
        """Create a mock TradingSystem for testing."""
        with patch("the_alchemiser.orchestration.system.load_settings") as mock_load:
            mock_settings = Mock()
            mock_settings.paper_trading = True
            mock_load.return_value = mock_settings

            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch(
                        "the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"
                    ) as mock_edo:
                        mock_orchestrator = Mock()
                        mock_orchestrator.start_trading_workflow.return_value = "test-correlation-id"
                        mock_orchestrator.wait_for_workflow_completion.return_value = {
                            "success": True,
                            "duration_seconds": 1.5,
                            "warnings": [],
                        }
                        mock_edo.return_value = mock_orchestrator

                        system = TradingSystem()
                        system.event_driven_orchestrator = mock_orchestrator

                        # Mock the emit startup event
                        system._emit_startup_event = Mock()

                        return system

    def test_execute_trading_calls_event_driven_orchestrator(self, mock_system):
        """Test that execute_trading uses event-driven orchestrator."""
        result = mock_system.execute_trading()

        # Verify orchestrator methods were called
        assert mock_system.event_driven_orchestrator.start_trading_workflow.called
        assert mock_system.event_driven_orchestrator.wait_for_workflow_completion.called

        # Verify result
        assert result is not None
        assert hasattr(result, "success")


class TestTradingSystemDisplayPostExecution:
    """Test TradingSystem display post-execution tracking."""

    @pytest.fixture
    def mock_system(self):
        """Create a mock TradingSystem for testing."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()
                        return system

    def test_display_post_execution_tracking_with_paper_trading(self, mock_system):
        """Test display post-execution tracking in paper mode."""
        # Should not raise any exceptions
        mock_system._display_post_execution_tracking(paper_trading=True)

    def test_display_post_execution_tracking_with_live_trading(self, mock_system):
        """Test display post-execution tracking in live mode."""
        # Should not raise any exceptions
        mock_system._display_post_execution_tracking(paper_trading=False)


class TestTradingSystemExecuteTradingErrorPaths:
    """Test TradingSystem execute_trading error handling."""

    def test_execute_trading_fails_when_container_is_none(self):
        """Test that execute_trading fails gracefully when container is None."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()
                        # Manually break the container
                        system.container = None

                        result = system.execute_trading()

                        # Verify failure result
                        assert result is not None
                        assert result.success is False

    def test_execute_trading_fails_when_orchestrator_is_none(self):
        """Test that execute_trading fails when event orchestrator is None."""
        with patch("the_alchemiser.orchestration.system.load_settings"):
            with patch("the_alchemiser.orchestration.system.ApplicationContainer"):
                with patch("the_alchemiser.orchestration.system.ServiceFactory"):
                    with patch("the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator"):
                        system = TradingSystem()
                        # Manually break the orchestrator
                        system.event_driven_orchestrator = None

                        result = system.execute_trading()

                        # Verify failure result
                        assert result is not None
                        assert result.success is False

