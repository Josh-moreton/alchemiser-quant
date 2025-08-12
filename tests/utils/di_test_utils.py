"""DI testing utilities and helpers.

This module provides utilities for testing with dependency injection,
including test builders, assertion helpers, and common testing patterns.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
import pytest

# Conditional imports for DI
try:
    from the_alchemiser.container.application_container import ApplicationContainer
    from the_alchemiser.application.trading_engine import TradingEngine
    from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False


class DITestBuilder:
    """Builder for creating DI test scenarios."""

    def __init__(self, mocker=None):
        """Initialize the DI test builder."""
        self.mocker = mocker
        self._mock_client = None
        self._container = None
        self._env_vars = {}

    def with_mock_alpaca_client(self, **client_config) -> "DITestBuilder":
        """Configure mock Alpaca client with custom behavior."""
        if not self.mocker:
            raise ValueError("Mocker required for mock client configuration")

        self._mock_client = self.mocker.Mock()

        # Default mock behavior
        defaults = {
            "buying_power": Decimal("50000.00"),
            "portfolio_value": Decimal("100000.00"),
            "cash": Decimal("25000.00"),
            "order_id": "test_order_123",
            "order_status": "ACCEPTED",
        }
        defaults.update(client_config)

        # Configure mock methods
        self._mock_client.submit_order.return_value = self.mocker.Mock(
            id=defaults["order_id"], status=defaults["order_status"]
        )
        self._mock_client.get_account.return_value = self.mocker.Mock(
            buying_power=defaults["buying_power"],
            portfolio_value=defaults["portfolio_value"],
            cash=defaults["cash"],
        )
        self._mock_client.get_positions.return_value = []
        self._mock_client.get_bars.return_value = []
        self._mock_client.get_latest_quote.return_value = self.mocker.Mock(bid=150.0, ask=150.01)

        # Patch the Alpaca client
        self.mocker.patch("alpaca.trading.TradingClient", return_value=self._mock_client)
        return self

    def with_environment_variables(self, **env_vars) -> "DITestBuilder":
        """Configure environment variables for testing."""
        defaults = {
            "ALPACA_API_KEY": "test_key_for_di",
            "ALPACA_SECRET_KEY": "test_secret_for_di",
            "PAPER_TRADING": "true",
            "AWS_REGION": "us-east-1",
        }
        defaults.update(env_vars)
        self._env_vars = defaults

        if self.mocker:
            for key, value in defaults.items():
                self.mocker.patch.dict("os.environ", {key: value})

        return self

    def build_container(self) -> ApplicationContainer:
        """Build and configure DI container."""
        if not DI_AVAILABLE:
            pytest.skip("Dependency injection not available")

        self._container = ApplicationContainer.create_for_testing()
        return self._container

    def build_trading_engine(self) -> TradingEngine:
        """Build TradingEngine with DI."""
        if not self._container:
            self.build_container()

        return TradingEngine.create_with_di(container=self._container)

    def build_trading_service_manager(self) -> TradingServiceManager:
        """Build TradingServiceManager with DI."""
        if not self._container:
            self.build_container()

        return self._container.services.trading_service_manager()

    def build_comparison_set(self) -> Dict[str, Any]:
        """Build both traditional and DI instances for comparison."""
        # Traditional instance
        traditional_engine = TradingEngine(paper_trading=True)

        # DI instance
        if DI_AVAILABLE:
            di_engine = self.build_trading_engine()
        else:
            di_engine = None

        return {
            "traditional": traditional_engine,
            "di": di_engine,
            "mock_client": self._mock_client,
            "container": self._container,
        }


class DIAssertionHelper:
    """Helper class for DI-specific assertions."""

    @staticmethod
    def assert_di_available():
        """Assert that DI is available for testing."""
        if not DI_AVAILABLE:
            pytest.skip("Dependency injection not available")

    @staticmethod
    def assert_container_valid(container: ApplicationContainer):
        """Assert that a DI container is properly configured."""
        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "infrastructure")
        assert hasattr(container, "services")

    @staticmethod
    def assert_trading_engine_di_ready(engine: TradingEngine):
        """Assert that a TradingEngine is properly configured with DI."""
        assert engine is not None
        assert engine._container is not None
        assert hasattr(engine, "data_provider")
        assert hasattr(engine, "trading_client")

    @staticmethod
    def assert_engines_equivalent(traditional: TradingEngine, di_engine: TradingEngine):
        """Assert that traditional and DI engines have equivalent capabilities."""
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

    @staticmethod
    def assert_service_is_singleton(container: ApplicationContainer, service_name: str):
        """Assert that a service is created as singleton."""
        service_provider = getattr(container.services, service_name)
        service1 = service_provider()
        service2 = service_provider()
        assert service1 is service2, f"Service {service_name} should be singleton"

    @staticmethod
    def assert_no_di_leakage(engine: TradingEngine):
        """Assert that traditional engine has no DI dependencies."""
        assert engine._container is None, "Traditional engine should not have DI container"


class DIPerformanceProfiler:
    """Profiler for DI performance testing."""

    def __init__(self):
        """Initialize the profiler."""
        self.measurements = {}

    def time_container_creation(self) -> float:
        """Time container creation and return duration."""
        import time

        start_time = time.time()
        container = ApplicationContainer.create_for_testing()
        duration = time.time() - start_time

        self.measurements["container_creation"] = duration
        assert container is not None
        return duration

    def time_service_creation(self, container: ApplicationContainer) -> float:
        """Time service creation and return duration."""
        import time

        start_time = time.time()
        trading_manager = container.services.trading_service_manager()
        duration = time.time() - start_time

        self.measurements["service_creation"] = duration
        assert trading_manager is not None
        return duration

    def assert_performance_acceptable(
        self, max_container_time: float = 1.0, max_service_time: float = 2.0
    ):
        """Assert that performance measurements are within acceptable limits."""
        if "container_creation" in self.measurements:
            assert (
                self.measurements["container_creation"] < max_container_time
            ), f"Container creation took {self.measurements['container_creation']:.2f}s"

        if "service_creation" in self.measurements:
            assert (
                self.measurements["service_creation"] < max_service_time
            ), f"Service creation took {self.measurements['service_creation']:.2f}s"


def create_di_test_scenario(mocker, scenario_name: str = "default") -> Dict[str, Any]:
    """Factory function for creating common DI test scenarios."""
    builder = DITestBuilder(mocker)

    if scenario_name == "default":
        return builder.with_mock_alpaca_client().with_environment_variables().build_comparison_set()

    elif scenario_name == "high_portfolio_value":
        return (
            builder.with_mock_alpaca_client(
                portfolio_value=Decimal("1000000.00"), buying_power=Decimal("500000.00")
            )
            .with_environment_variables()
            .build_comparison_set()
        )

    elif scenario_name == "error_prone":
        # Configure mock to simulate errors
        builder.with_environment_variables()
        if mocker:
            mock_client = mocker.Mock()
            mock_client.get_account.side_effect = Exception("Simulated API error")
            mocker.patch("alpaca.trading.TradingClient", return_value=mock_client)

        return builder.build_comparison_set()

    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")


def skip_if_di_unavailable(func):
    """Decorator to skip tests if DI is not available."""

    def wrapper(*args, **kwargs):
        if not DI_AVAILABLE:
            pytest.skip("Dependency injection not available")
        return func(*args, **kwargs)

    return wrapper


# Pytest marks for DI testing
requires_di = pytest.mark.skipif(not DI_AVAILABLE, reason="Dependency injection not available")
di_integration = pytest.mark.integration
di_performance = pytest.mark.performance
