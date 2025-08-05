"""Test configuration and shared utilities."""

import logging
import os
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import pytest

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test constants
TEST_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "SPY", "QQQ"]
TEST_PORTFOLIO_VALUE = Decimal("100000.00")
MIN_COLD_START_TIME = 5.0  # seconds
MAX_COLD_START_TIME = 30.0  # seconds


# Mock data generators
def create_test_account_info() -> dict[str, Any]:
    """Create realistic test account information."""
    return {
        "account_id": "test_account_123",
        "equity": "105000.50",
        "cash": "25000.00",
        "buying_power": "50000.00",
        "day_trades_remaining": 3,
        "portfolio_value": "105000.50",
        "last_equity": "104500.25",
        "daytrading_buying_power": "50000.00",
        "regt_buying_power": "50000.00",
        "status": "ACTIVE",
    }


def create_test_position(symbol: str, qty: float = 100.0, price: float = 150.0) -> dict[str, Any]:
    """Create realistic test position data."""
    market_value = qty * price
    cost_basis = market_value * 0.95  # Slight profit

    return {
        "symbol": symbol,
        "qty": str(qty),
        "side": "long",
        "market_value": str(market_value),
        "cost_basis": str(cost_basis),
        "unrealized_pl": str(market_value - cost_basis),
        "unrealized_plpc": str((market_value - cost_basis) / cost_basis),
        "current_price": str(price),
    }


def create_test_order(symbol: str, qty: float = 100.0, side: str = "buy") -> dict[str, Any]:
    """Create realistic test order data."""
    return {
        "id": f"test_order_{symbol}_{side}",
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "order_type": "market",
        "time_in_force": "day",
        "status": "filled",
        "filled_qty": str(qty),
        "filled_avg_price": "150.00",
        "created_at": "2024-01-15T09:30:00Z",
        "updated_at": "2024-01-15T09:30:05Z",
    }


# Test fixtures
@pytest.fixture
def test_account():
    """Provide test account information."""
    return create_test_account_info()


@pytest.fixture
def test_positions():
    """Provide test position data."""
    return {symbol: create_test_position(symbol) for symbol in TEST_SYMBOLS[:3]}


@pytest.fixture
def test_portfolio_value():
    """Provide standard test portfolio value."""
    return TEST_PORTFOLIO_VALUE


@pytest.fixture
def mock_data_provider():
    """Mock data provider with realistic responses."""
    mock = Mock()

    # Mock price data
    mock.get_current_price.return_value = 150.0
    mock.get_data.return_value = create_sample_price_data()

    return mock


@pytest.fixture
def mock_alpaca_client():
    """Mock Alpaca trading client."""
    mock = Mock()

    # Mock order submission
    mock.submit_order.return_value = Mock(id="test_order_123")
    mock.get_account.return_value = Mock(**create_test_account_info())
    mock.list_positions.return_value = [
        Mock(**create_test_position(symbol)) for symbol in TEST_SYMBOLS[:2]
    ]

    return mock


def create_sample_price_data(days: int = 100):
    """Create sample price data for testing."""
    from datetime import datetime, timedelta

    import numpy as np
    import pandas as pd

    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    dates.reverse()

    # Generate realistic price movement
    np.random.seed(42)  # Reproducible
    returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
    prices = [100.0]  # Starting price

    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": prices,
            "High": [p * 1.02 for p in prices],
            "Low": [p * 0.98 for p in prices],
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, days),
        }
    ).set_index("Date")


# Test utilities
class TestingUtilities:
    """Shared testing utilities."""

    @staticmethod
    def assert_decimal_equal(actual: Decimal, expected: Decimal, places: int = 2):
        """Assert decimal equality within specified decimal places."""
        tolerance = Decimal(10) ** -places
        assert abs(actual - expected) <= tolerance, f"Expected {expected}, got {actual}"

    @staticmethod
    def assert_portfolio_balanced(allocations: dict[str, float], tolerance: float = 1e-6):
        """Assert portfolio allocations sum to 1.0."""
        total = sum(allocations.values())
        assert abs(total - 1.0) <= tolerance, f"Portfolio not balanced: {total}"

    @staticmethod
    def create_price_gap(data: pd.DataFrame, gap_size: float = 0.1) -> pd.DataFrame:
        """Inject price gap into market data."""
        data_copy = data.copy()
        mid_point = len(data_copy) // 2
        gap_multiplier = 1 + gap_size

        # Apply gap to second half of data
        data_copy.iloc[mid_point:] *= gap_multiplier
        return data_copy


# Test environment setup
def setup_test_environment():
    """Setup test environment variables."""
    os.environ.update(
        {
            "AWS_DEFAULT_REGION": "us-east-1",
            "ALPACA_API_KEY": "test_key",
            "ALPACA_SECRET_KEY": "test_secret",
            "S3_BUCKET": "test-bucket",
            "PAPER_TRADING": "true",
            "LOG_LEVEL": "DEBUG",
        }
    )


# Call setup when module is imported
setup_test_environment()
