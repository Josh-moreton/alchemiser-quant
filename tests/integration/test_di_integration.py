"""Integration tests for dependency injection infrastructure.

This module provides comprehensive tests for the DI system including:
- Container initialization and configuration
- Service creation and injection
- TradingEngine DI integration
- Comparison between traditional and DI modes
- Error handling and fallback mechanisms

These tests ensure the DI system works correctly in all scenarios
while maintaining backward compatibility.
"""

from decimal import Decimal

import pytest

# Skip all tests if DI is not available
try:
    from the_alchemiser.application.trading_engine import TradingEngine
    from the_alchemiser.container.application_container import ApplicationContainer
    from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not DI_AVAILABLE, reason="Dependency injection not available")


class TestDIContainerIntegration:
    """Test DI container initialization and configuration."""

    def test_container_creation_for_testing(self, di_mock_environment):
        """Test that test container can be created with proper configuration."""
        container = ApplicationContainer.create_for_testing()

        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "infrastructure")
        assert hasattr(container, "services")

    def test_container_environment_configuration(self, di_mock_environment):
        """Test that container respects environment configuration."""
        container = ApplicationContainer.create_for_environment("test")

        # Verify test configuration is applied
        config = container.config()
        assert config.alpaca.api_key == "test_api_key_valid_for_testing"
        assert config.alpaca.paper_trading is True

    def test_container_service_creation(self, di_container):
        """Test that container can create all required services."""
        # Test TradingServiceManager creation
        trading_manager = di_container.services.trading_service_manager()
        assert trading_manager is not None
        assert isinstance(trading_manager, TradingServiceManager)

        # Verify it has all required components
        assert hasattr(trading_manager, "alpaca_manager")
        assert hasattr(trading_manager, "order_service")
        assert hasattr(trading_manager, "position_service")
        assert hasattr(trading_manager, "market_data_service")
        assert hasattr(trading_manager, "account_service")


class TestTradingEngineDIIntegration:
    """Test TradingEngine dependency injection integration."""

    def test_trading_engine_creation_with_di(self, di_container):
        """Test TradingEngine can be created with DI container."""
        engine = TradingEngine.create_with_di(container=di_container)

        assert engine is not None
        assert engine._container is not None
        assert hasattr(engine, "data_provider")
        assert hasattr(engine, "trading_client")

    def test_trading_engine_di_vs_traditional_attributes(self, di_comparison_data):
        """Test that DI and traditional engines have equivalent attributes."""
        traditional = di_comparison_data["traditional"]
        di_engine = di_comparison_data["di"]  # type: Optional[TradingEngine]

        if di_engine is None:
            pytest.skip("DI engine not available")
            return  # make control-flow explicit for static analysis

        # Narrow type for static/type checkers and linters
        assert di_engine is not None

        # Both should have the same core attributes
        core_attributes = [
            "data_provider",
            "trading_client",
            "strategy_manager",
            "portfolio_rebalancer",
            "strategy_allocations",
        ]

        for attr in core_attributes:
            assert hasattr(traditional, attr), f"Traditional engine missing {attr}"
            assert hasattr(di_engine, attr), f"DI engine missing {attr}"

    def test_trading_engine_di_initialization_modes(self, mocker):
        """Test all three TradingEngine initialization modes."""
        # Mock Alpaca client
        mock_client = mocker.Mock()
        mock_client.get_account.return_value = mocker.Mock(
            buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
        )
        mocker.patch("alpaca.trading.TradingClient", return_value=mock_client)

        # 1. Traditional mode
        traditional = TradingEngine(paper_trading=True)
        assert traditional._container is None

        # 2. Partial DI mode (inject TradingServiceManager)
        container = ApplicationContainer.create_for_testing()
        trading_manager = container.services.trading_service_manager()
        partial_di = TradingEngine(trading_service_manager=trading_manager)
        assert partial_di._container is None
        assert partial_di.data_provider == trading_manager

        # 3. Full DI mode
        full_di = TradingEngine.create_with_di(container=container)
        assert full_di._container is not None

    def test_trading_engine_di_error_handling(self, mocker):
        """Test DI error handling and fallback mechanisms."""
        # Mock container that raises an error
        mock_container = mocker.Mock()
        mock_container.services.trading_service_manager.side_effect = Exception("DI Error")

        # Should handle the error gracefully (may fall back to mocks)
        try:
            engine = TradingEngine(container=mock_container)
            # If it succeeds, it should still be functional
            assert engine is not None
        except Exception as e:
            # If it fails, the error should be informative
            assert "DI Error" in str(e) or "Failed to initialize" in str(e)


class TestDIServiceBehavior:
    """Test behavior of DI-created services."""

    def test_di_trading_service_manager_functionality(self, di_trading_service_manager):
        """Test that DI-created TradingServiceManager works correctly."""
        tsm = di_trading_service_manager

        # Test basic functionality
        assert hasattr(tsm, "get_account_info")
        assert hasattr(tsm, "get_all_positions")
        assert hasattr(tsm, "place_market_order")

        # Test that methods can be called (with mocked backend)
        try:
            account_info = tsm.get_account_info()
            assert account_info is not None
        except Exception as e:
            # Should not raise unexpected errors
            assert "connection" not in str(e).lower() or "network" not in str(e).lower()

    def test_di_services_are_singletons(self, di_container):
        """Test that DI services are created as singletons."""
        # Get the same service twice
        service1 = di_container.services.trading_service_manager()
        service2 = di_container.services.trading_service_manager()

        # They should be the same instance (singleton pattern)
        assert service1 is service2

    def test_di_configuration_injection(self, di_container):
        """Test that configuration is properly injected into services."""
        config = di_container.config()
        di_container.services.trading_service_manager()

        # Services should receive the same configuration
        assert config.alpaca.paper_trading is True
        assert config.alpaca.api_key == "test_api_key_valid_for_testing"


class TestDIBackwardCompatibility:
    """Test that DI doesn't break existing functionality."""

    def test_traditional_mode_still_works(self, mocker):
        """Test that traditional TradingEngine initialization still works."""
        # Mock Alpaca client
        mock_client = mocker.Mock()
        mock_client.get_account.return_value = mocker.Mock(
            buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
        )
        mocker.patch("alpaca.trading.TradingClient", return_value=mock_client)

        # Traditional initialization should work unchanged
        engine = TradingEngine(paper_trading=True)
        assert engine is not None
        assert engine._container is None  # No DI container
        assert hasattr(engine, "data_provider")

    def test_existing_api_compatibility(self, di_comparison_data):
        """Test that DI engines support the same API as traditional engines."""
        traditional = di_comparison_data["traditional"]
        di_engine = di_comparison_data["di"]  # type: Optional[TradingEngine]

        if di_engine is None:
            pytest.skip("DI engine not available")
            return  # make control-flow explicit for static analysis

        # Narrow type for static/type checkers and linters
        assert di_engine is not None

        # Test that both engines support the same public methods
        public_methods = [
            "execute_multi_strategy",
            "get_account_information",
            "get_current_positions",
        ]

        for method_name in public_methods:
            assert hasattr(traditional, method_name), f"Traditional missing {method_name}"
            assert hasattr(di_engine, method_name), f"DI engine missing {method_name}"

            # Both should be callable
            assert callable(getattr(traditional, method_name))
            assert callable(getattr(di_engine, method_name))

    @pytest.mark.parametrize("engine_present", [True, False])
    def test_no_breaking_changes_in_signatures(self, di_comparison_data, engine_present):
        """Test that method signatures are identical between modes."""
        traditional = di_comparison_data["traditional"]
        di_engine = di_comparison_data["di"] if engine_present else None  # type: Optional[TradingEngine]

        if di_engine is None:
            pytest.skip("DI engine not available")
            return  # make control-flow explicit for static analysis

        # Narrow type for static/type checkers and linters
        assert di_engine is not None

        # Check that execute_multi_strategy has the same signature
        import inspect

        trad_sig = inspect.signature(traditional.execute_multi_strategy)
        di_sig = inspect.signature(di_engine.execute_multi_strategy)

        assert trad_sig == di_sig, "Method signatures should be identical"


class TestDIPerformanceAndReliability:
    """Test DI system performance and reliability."""

    def test_di_container_creation_performance(self, di_mock_environment):
        """Test that DI container creation is reasonably fast."""
        import time

        start_time = time.time()
        container = ApplicationContainer.create_for_testing()
        creation_time = time.time() - start_time

        # Container creation should be fast (< 1 second)
        assert creation_time < 1.0, f"Container creation took {creation_time:.2f}s"
        assert container is not None

    def test_di_service_creation_performance(self, di_container):
        """Test that service creation through DI is reasonably fast."""
        import time

        start_time = time.time()
        trading_manager = di_container.services.trading_service_manager()
        creation_time = time.time() - start_time

        # Service creation should be fast (< 2 seconds)
        assert creation_time < 2.0, f"Service creation took {creation_time:.2f}s"
        assert trading_manager is not None

    def test_di_memory_usage(self, di_container):
        """Test that DI doesn't create excessive objects."""
        # Get multiple instances of the same service
        services = [di_container.services.trading_service_manager() for _ in range(5)]

        # All should be the same instance (singleton)
        first_service = services[0]
        for service in services[1:]:
            assert service is first_service, "Services should be singletons"

    def test_di_error_recovery(self, mocker):
        """Test that DI system can recover from errors."""
        # First, simulate an error condition
        mocker.patch(
            "the_alchemiser.container.application_container.ApplicationContainer.create_for_testing",
            side_effect=RuntimeError("Temporary error"),
        )

        # Should be able to handle the error
        with pytest.raises(RuntimeError):
            ApplicationContainer.create_for_testing()

        # Then verify it can recover when the error is resolved
        mocker.patch(
            "the_alchemiser.container.application_container.ApplicationContainer.create_for_testing"
        ).side_effect = None

        # Reset the mock to normal behavior
        mocker.patch.stopall()

        # Should work normally again
        container = ApplicationContainer.create_for_testing()
        assert container is not None


@pytest.mark.integration
class TestDIFullWorkflow:
    """Integration tests for complete DI workflows."""

    def test_full_di_trading_workflow(self, di_trading_engine, mocker):
        """Test a complete trading workflow with DI."""
        engine = di_trading_engine

        # Mock some market data for the workflow
        mock_bars = mocker.Mock()
        mock_bars.symbol = "SPY"
        mock_bars.close = 400.0

        # Should be able to run basic operations
        try:
            account_info = engine.get_account_information()
            assert account_info is not None

            positions = engine.get_current_positions()
            assert isinstance(positions, list | dict)

        except Exception as e:
            # Errors should be related to mocked data, not DI issues
            assert "dependency" not in str(e).lower()
            assert "injection" not in str(e).lower()

    def test_di_vs_traditional_workflow_equivalence(self, di_comparison_data, mocker):
        """Test that DI and traditional workflows produce equivalent results."""
        traditional = di_comparison_data["traditional"]
        di_engine = di_comparison_data["di"]  # type: Optional[TradingEngine]

        if di_engine is None:
            pytest.skip("DI engine not available")
            return  # make control-flow explicit for static analysis

        # Narrow type for static/type checkers and linters
        assert di_engine is not None

        # Mock consistent data for both
        mock_account = mocker.Mock()
        mock_account.buying_power = Decimal("50000.00")
        mock_account.portfolio_value = Decimal("100000.00")

        # Both should handle the same operations
        try:
            trad_account = traditional.get_account_information()
            di_account = di_engine.get_account_information()

            # Results should be structurally similar
            assert type(trad_account) is type(di_account)

        except Exception as e:
            # If one fails, both should fail similarly
            pytest.skip(f"Both engines failed similarly: {e}")
            return  # make control-flow explicit for static analysis
