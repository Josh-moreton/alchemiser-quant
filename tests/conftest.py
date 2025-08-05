"""
Global test configuration and fixtures for The Alchemiser testing framework.

This module provides shared pytest fixtures, configuration, and utilities
used across all test categories.
"""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Return the project root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_path: Path) -> Path:
    """Return the test data directory path."""
    return project_root_path / "tests" / "fixtures"


@pytest.fixture
def sample_portfolio_value() -> Decimal:
    """Standard portfolio value for testing."""
    return Decimal("100000.00")


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
        "TELEGRAM_BOT_TOKEN": "test_token",
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


@contextmanager
def mock_broker_api(responses: list | None = None):
    """Mock all broker API interactions."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_client.submit_order.return_value = Mock(id="test_order_123", status="ACCEPTED")
    mock_client.get_account.return_value = Mock(
        buying_power=Decimal("50000.00"), portfolio_value=Decimal("100000.00")
    )
    mock_client.get_positions.return_value = []

    with patch("alpaca.trading.TradingClient", return_value=mock_client):
        yield mock_client


@contextmanager
def mock_aws_services():
    """Mock all AWS service interactions."""
    with patch("boto3.client") as mock_boto:
        # S3 Mock
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {"ETag": "test_etag"}
        mock_s3.get_object.return_value = {"Body": MagicMock(), "ContentLength": 1024}

        # Secrets Manager Mock
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": '{"api_key": "test_key", "secret_key": "test_secret"}'
        }

        # CloudWatch Mock
        mock_cloudwatch = MagicMock()
        mock_cloudwatch.put_metric_data.return_value = {}

        service_mocks = {
            "s3": mock_s3,
            "secretsmanager": mock_secrets,
            "cloudwatch": mock_cloudwatch,
        }

        mock_boto.side_effect = lambda service_name, **kwargs: service_mocks.get(service_name)
        yield service_mocks


def create_sample_price_data(
    symbols: list[str],
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    frequency: str = "D",
) -> pd.DataFrame:
    """Create sample price data for testing."""
    date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)

    data = []
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
