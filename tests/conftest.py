"""
Global test configuration and fixtures for The Alchemiser testing framework.

This module provides shared pytest fixtures, configuration, and utilities
used across all test categories. Uses pytest-mock for enhanced mocking capabilities.
"""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

# pytest-mock is available as a fixture automatically when installed
# No need to import MockerFixture explicitly

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# DI imports for testing infrastructure
try:
    from the_alchemiser.container.application_container import ApplicationContainer
    from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False

REL_TOL = 1e-6
ABS_TOL = 1e-12


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Return the project root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_path: Path) -> Path:
    """Return the test data directory path."""
    return project_root_path / "tests" / "fixtures"


@pytest.fixture
def sample_portfolio_value():
    """Provides sample portfolio value for testing."""
    return Decimal("1000.00")


@pytest.fixture
def normal_market_conditions():
    """Mock market data for normal trading conditions."""
    return {
        "AAPL": {
            "price": Decimal("150.00"),
            "volume": 1000000,
            "timestamp": "2024-01-01T10:00:00Z",
            "bid": Decimal("149.95"),
            "ask": Decimal("150.05"),
        },
        "TSLA": {
            "price": Decimal("200.00"),
            "volume": 800000,
            "timestamp": "2024-01-01T10:00:00Z",
            "bid": Decimal("199.90"),
            "ask": Decimal("200.10"),
        },
    }


@pytest.fixture
def missing_data_scenario():
    """Mock scenario with missing market data."""
    return {
        "AAPL": {
            "price": None,
            "volume": 0,
            "timestamp": "2024-01-01T10:00:00Z",
            "bid": None,
            "ask": None,
            "error": "Data not available",
        }
    }


@pytest.fixture
def test_symbols() -> list[str]:
    """Standard list of symbols for testing."""
    return ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]


@pytest.fixture
def mock_env_vars() -> dict[str, str]:
    """Standard environment variables for testing."""
    return {
        "AWS_REGION": "us-east-1",
        "ALPACA_API_KEY": "test_key",
        "ALPACA_SECRET_KEY": "test_secret",
        "S3_BUCKET": "test-alchemiser-bucket",
    }


@pytest.fixture(autouse=True)
def setup_test_environment(mock_env_vars: dict[str, str]) -> Generator[None, None, None]:
    """Automatically setup test environment for all tests."""
    original_env = os.environ.copy()

    try:
        # Set test environment variables
        os.environ.update(mock_env_vars)
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def mock_alpaca_client(mocker):
    """Pytest fixture for mocking Alpaca trading client."""
    mock_client = mocker.Mock()
    mock_client.submit_order.return_value = mocker.Mock(id="test_order_123", status="ACCEPTED")
    mock_client.get_account.return_value = mocker.Mock(
        buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
    )
    mock_client.get_positions.return_value = []
    mock_client.get_bars.return_value = []
    mock_client.get_latest_quote.return_value = mocker.Mock(bid=150.0, ask=150.01)

    mocker.patch("alpaca.trading.TradingClient", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_aws_clients(mocker):
    """Pytest fixture for mocking AWS service clients."""
    # S3 Mock
    mock_s3 = mocker.Mock()
    mock_s3.put_object.return_value = {"ETag": "test_etag"}
    mock_s3.get_object.return_value = {"Body": mocker.Mock(), "ContentLength": 1024}
    mock_s3.head_object.return_value = {"ContentLength": 1024}

    # Secrets Manager Mock
    mock_secrets = mocker.Mock()
    mock_secrets.get_secret_value.return_value = {
        "SecretString": '{"api_key": "test_key", "secret_key": "test_secret"}'
    }

    # CloudWatch Mock
    mock_cloudwatch = mocker.Mock()
    mock_cloudwatch.put_metric_data.return_value = {}

    service_mocks = {
        "s3": mock_s3,
        "secretsmanager": mock_secrets,
        "cloudwatch": mock_cloudwatch,
    }

    def get_service(service_name: str, **kwargs) -> Any:
        return service_mocks.get(service_name)

    mocker.patch("boto3.client", side_effect=get_service)
    return service_mocks


@pytest.fixture
def mock_environment_variables(mocker):
    """Pytest fixture for mocking environment variables."""
    env_vars = {
        "AWS_REGION": "us-east-1",
        "ALPACA_API_KEY": "test_key",
        "ALPACA_SECRET_KEY": "test_secret",
        "S3_BUCKET": "test-alchemiser-bucket",
    }

    for key, value in env_vars.items():
        mocker.patch.dict("os.environ", {key: value})

    return env_vars


# Legacy context managers for backward compatibility
@contextmanager
def mock_broker_api(mocker, responses: list[Any] | None = None):
    """Mock all broker API interactions using pytest-mock."""
    mock_client = mocker.Mock()
    mock_client.submit_order.return_value = mocker.Mock(id="test_order_123", status="ACCEPTED")
    mock_client.get_account.return_value = mocker.Mock(
        buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
    )
    mock_client.get_positions.return_value = []

    mocker.patch("alpaca.trading.TradingClient", return_value=mock_client)
    yield mock_client


@contextmanager
def mock_aws_services(mocker):
    """Mock all AWS service interactions using pytest-mock."""
    # S3 Mock
    mock_s3 = mocker.Mock()
    mock_s3.put_object.return_value = {"ETag": "test_etag"}
    mock_s3.get_object.return_value = {"Body": mocker.Mock(), "ContentLength": 1024}

    # Secrets Manager Mock
    mock_secrets = mocker.Mock()
    mock_secrets.get_secret_value.return_value = {
        "SecretString": '{"api_key": "test_key", "secret_key": "test_secret"}'
    }

    # CloudWatch Mock
    mock_cloudwatch = mocker.Mock()
    mock_cloudwatch.put_metric_data.return_value = {}

    service_mocks = {
        "s3": mock_s3,
        "secretsmanager": mock_secrets,
        "cloudwatch": mock_cloudwatch,
    }

    def get_service(service_name: str) -> Any:
        return service_mocks.get(service_name)

    mocker.patch("boto3.client", side_effect=get_service)
    yield service_mocks


# ============================================================================
# DEPENDENCY INJECTION TEST FIXTURES (Phase 3)
# ============================================================================


@pytest.fixture
def di_container(mocker):
    """Pytest fixture for DI container with mocked dependencies."""
    if not DI_AVAILABLE:
        pytest.skip("Dependency injection not available")

    from the_alchemiser.container.application_container import ApplicationContainer

    # Create test container
    container = ApplicationContainer.create_for_testing()

    # Mock the underlying Alpaca client to prevent real API calls
    mock_alpaca_client = mocker.Mock()
    mock_alpaca_client.submit_order.return_value = mocker.Mock(
        id="test_order_123", status="ACCEPTED"
    )
    mock_alpaca_client.get_account.return_value = mocker.Mock(
        buying_power=Decimal("50000.00"),
        portfolio_value=Decimal("100000.00"),
        cash=Decimal("25000.00"),
    )
    mock_alpaca_client.get_positions.return_value = []
    mock_alpaca_client.get_bars.return_value = []
    mock_alpaca_client.get_latest_quote.return_value = mocker.Mock(bid=150.0, ask=150.01)

    # Override the trading client in the container
    mocker.patch("alpaca.trading.TradingClient", return_value=mock_alpaca_client)

    return container


@pytest.fixture
def di_trading_service_manager(di_container):
    """Pytest fixture for DI-created TradingServiceManager."""
    return di_container.services.trading_service_manager()


@pytest.fixture
def di_trading_engine(di_container):
    """Pytest fixture for DI-created TradingEngine."""
    from the_alchemiser.application.trading_engine import TradingEngine

    return TradingEngine.create_with_di(container=di_container)


@pytest.fixture
def di_mock_environment(mocker):
    """Environment setup specifically for DI testing."""
    # Mock environment variables required for DI
    env_vars = {
        "ALPACA_API_KEY": "test_key_for_di",
        "ALPACA_SECRET_KEY": "test_secret_for_di",
        "PAPER_TRADING": "true",
        "AWS_REGION": "us-east-1",
    }

    for key, value in env_vars.items():
        mocker.patch.dict("os.environ", {key: value})

    return env_vars


@pytest.fixture
def di_comparison_data(mocker):
    """Fixture providing both traditional and DI instances for comparison testing."""
    # Traditional instance
    from the_alchemiser.application.trading_engine import TradingEngine

    # Mock Alpaca client for both modes
    mock_alpaca_client = mocker.Mock()
    mock_alpaca_client.submit_order.return_value = mocker.Mock(
        id="test_order_123", status="ACCEPTED"
    )
    mock_alpaca_client.get_account.return_value = mocker.Mock(
        buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
    )
    mock_alpaca_client.get_positions.return_value = []

    mocker.patch("alpaca.trading.TradingClient", return_value=mock_alpaca_client)

    # Create both instances
    traditional_engine = TradingEngine(paper_trading=True)

    if DI_AVAILABLE:
        from the_alchemiser.container.application_container import ApplicationContainer

        di_container = ApplicationContainer.create_for_testing()
        di_engine = TradingEngine.create_with_di(container=di_container)
    else:
        di_engine = None

    return {"traditional": traditional_engine, "di": di_engine, "mock_client": mock_alpaca_client}


# ============================================================================
# END DEPENDENCY INJECTION FIXTURES
# ============================================================================


def create_sample_price_data(
    symbols: list[str],
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    frequency: str = "D",
) -> pd.DataFrame:
    """Create sample price data for testing."""
    date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)

    data: list[dict[str, Any]] = []
    for symbol in symbols:
        # Generate realistic price movements
        base_price = 100.0  # Starting price
        volatility = 0.02  # 2% daily volatility

        prices = [base_price]
        for _ in range(len(date_range) - 1):
            change = np.random.normal(0, volatility)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1.0))  # Prevent negative prices

        for i, date in enumerate(date_range):
            data.append(
                {
                    "timestamp": date,
                    "symbol": symbol,
                    "open": prices[i] * (1 + np.random.normal(0, 0.001)),
                    "high": prices[i] * (1 + abs(np.random.normal(0, 0.005))),
                    "low": prices[i] * (1 - abs(np.random.normal(0, 0.005))),
                    "close": prices[i],
                    "volume": int(np.random.uniform(1000000, 10000000)),
                }
            )

    return pd.DataFrame(data)


def create_portfolio_state(
    symbols: list[str],
    allocations: dict[str, float] | None = None,
    portfolio_value: float = 100000.0,
) -> dict[str, Any]:
    """Create a sample portfolio state for testing."""
    if allocations is None:
        # Equal allocation across symbols
        allocation_per_symbol = 1.0 / len(symbols)
        allocations = dict.fromkeys(symbols, allocation_per_symbol)

    positions = {}
    cash_allocation = allocations.get("CASH", 0.1)  # Default 10% cash

    for symbol, allocation in allocations.items():
        if symbol != "CASH":
            position_value = portfolio_value * allocation
            # Assume $100 per share for simplicity
            shares = int(position_value / 100)
            positions[symbol] = {
                "symbol": symbol,
                "shares": shares,
                "avg_price": 100.0,
                "market_value": shares * 100.0,
                "unrealized_pnl": 0.0,
            }

    return {
        "portfolio_value": portfolio_value,
        "cash": portfolio_value * cash_allocation,
        "positions": positions,
        "allocations": allocations,
        "timestamp": pd.Timestamp.now(),
    }


# Utility functions for test assertions
def assert_decimal_equal(actual: Decimal, expected: Decimal, places: int = 2) -> None:
    """Assert two Decimal values are equal within specified decimal places."""
    tolerance = Decimal(f"1E-{places}")
    assert abs(actual - expected) <= tolerance, f"Expected {expected}, got {actual}"


def assert_allocation_valid(allocations: dict[str, float], tolerance: float = 1e-6) -> None:
    """Assert portfolio allocations sum to 1.0 within tolerance."""
    total = sum(allocations.values())
    assert abs(total - 1.0) <= tolerance, f"Allocations sum to {total}, expected 1.0"


def assert_no_negative_positions(portfolio_state: dict[str, Any]) -> None:
    """Assert no negative positions or cash in portfolio state."""
    assert portfolio_state["cash"] >= 0, "Cash cannot be negative"
    assert portfolio_state["portfolio_value"] >= 0, "Portfolio value cannot be negative"

    for position in portfolio_state["positions"].values():
        assert position["shares"] >= 0, f"Shares cannot be negative for {position['symbol']}"
        assert (
            position["market_value"] >= 0
        ), f"Market value cannot be negative for {position['symbol']}"
