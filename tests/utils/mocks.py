"""
Mock framework for external dependencies in The Alchemiser.

This module provides comprehensive mocking capabilities for all external
services including broker APIs, AWS services, and market data sources.
"""

from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pandas as pd


class AlpacaMocks:
    """Mock implementations for Alpaca Trading API."""

    @staticmethod
    def create_successful_order() -> Mock:
        """Create a mock successful order response."""
        order = Mock()
        order.id = "test_order_123"
        order.status = "ACCEPTED"
        order.symbol = "AAPL"
        order.qty = 100
        order.side = "BUY"
        order.order_type = "MARKET"
        order.filled_at = pd.Timestamp.now()
        order.filled_qty = 100
        order.filled_avg_price = Decimal("150.25")
        return order

    @staticmethod
    def create_failed_order() -> Mock:
        """Create a mock failed order response."""
        order = Mock()
        order.id = "test_order_456"
        order.status = "REJECTED"
        order.symbol = "AAPL"
        order.qty = 100
        order.side = "BUY"
        order.order_type = "MARKET"
        order.reject_reason = "Insufficient buying power"
        return order

    @staticmethod
    def create_account() -> Mock:
        """Create a mock account response."""
        account = Mock()
        account.id = "test_account_123"
        account.buying_power = Decimal("50000.00")
        account.portfolio_value = Decimal("100000.00")
        account.cash = Decimal("25000.00")
        account.equity = Decimal("100000.00")
        account.day_trade_count = 0
        account.pattern_day_trader = False
        return account

    @staticmethod
    def create_position(symbol: str = "AAPL", qty: int = 100) -> Mock:
        """Create a mock position."""
        position = Mock()
        position.symbol = symbol
        position.qty = qty
        position.avg_entry_price = Decimal("150.00")
        position.market_value = Decimal(str(150.00 * qty))
        position.unrealized_pl = Decimal("250.00")
        position.unrealized_plpc = Decimal("0.0167")  # 1.67%
        return position


class AWSMocks:
    """Mock implementations for AWS services."""

    @staticmethod
    def create_s3_client() -> MagicMock:
        """Create a mock S3 client."""
        s3_client = MagicMock()

        # Mock successful operations
        s3_client.put_object.return_value = {"ETag": "test_etag_123"}
        s3_client.get_object.return_value = {
            "Body": MagicMock(),
            "ContentLength": 1024,
            "LastModified": pd.Timestamp.now(),
        }
        s3_client.head_object.return_value = {
            "ContentLength": 1024,
            "LastModified": pd.Timestamp.now(),
        }
        s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "portfolio_state.json", "Size": 1024}]
        }

        return s3_client

    @staticmethod
    def create_secrets_manager_client() -> MagicMock:
        """Create a mock Secrets Manager client."""
        secrets_client = MagicMock()

        secrets_client.get_secret_value.return_value = {
            "SecretString": '{"api_key": "test_key", "secret_key": "test_secret"}'
        }

        return secrets_client

    @staticmethod
    def create_cloudwatch_client() -> MagicMock:
        """Create a mock CloudWatch client."""
        cloudwatch_client = MagicMock()

        cloudwatch_client.put_metric_data.return_value = {}
        cloudwatch_client.get_metric_statistics.return_value = {
            "Datapoints": [{"Timestamp": pd.Timestamp.now(), "Average": 100.0, "Unit": "Count"}]
        }

        return cloudwatch_client


class MarketDataMocks:
    """Mock implementations for market data sources."""

    @staticmethod
    def create_bar_data(
        symbol: str = "AAPL", bars: int = 100, start_price: float = 150.0
    ) -> list[dict[str, Any]]:
        """Create mock historical bar data."""
        import numpy as np

        data = []
        current_price = start_price

        for i in range(bars):
            # Generate realistic price movement
            change = np.random.normal(0, 0.02)  # 2% volatility
            current_price *= 1 + change

            # Ensure realistic OHLC relationships
            open_price = current_price
            high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
            close_price = open_price + np.random.normal(0, open_price * 0.005)

            # Ensure high >= max(open, close) and low <= min(open, close)
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            bar = {
                "timestamp": pd.Timestamp.now() - pd.Timedelta(days=bars - i),
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": int(np.random.uniform(1000000, 10000000)),
            }
            data.append(bar)
            current_price = close_price

        return data

    @staticmethod
    def create_quote_data(symbol: str = "AAPL", price: float = 150.0) -> dict[str, Any]:
        """Create mock real-time quote data."""
        return {
            "symbol": symbol,
            "bid": price - 0.01,
            "ask": price + 0.01,
            "bid_size": 100,
            "ask_size": 200,
            "last": price,
            "last_size": 100,
            "timestamp": pd.Timestamp.now(),
        }


@contextmanager
def mock_alpaca_api(
    orders: list[Mock] | None = None,
    account: Mock | None = None,
    positions: list[Mock] | None = None,
) -> Generator[Mock, None, None]:
    """Context manager to mock the entire Alpaca API client."""
    mock_client = Mock()

    # Setup order responses
    if orders:
        mock_client.submit_order.side_effect = orders
    else:
        mock_client.submit_order.return_value = AlpacaMocks.create_successful_order()

    # Setup account response
    mock_client.get_account.return_value = account or AlpacaMocks.create_account()

    # Setup positions response
    mock_client.get_all_positions.return_value = positions or []

    # Setup market data responses
    mock_client.get_bars.return_value = MarketDataMocks.create_bar_data()
    mock_client.get_latest_quote.return_value = MarketDataMocks.create_quote_data()

    with patch("alpaca.trading.TradingClient", return_value=mock_client):
        yield mock_client


@contextmanager
def mock_aws_clients() -> Generator[dict[str, MagicMock], None, None]:
    """Context manager to mock all AWS service clients."""
    service_mocks = {
        "s3": AWSMocks.create_s3_client(),
        "secretsmanager": AWSMocks.create_secrets_manager_client(),
        "cloudwatch": AWSMocks.create_cloudwatch_client(),
    }

    def get_client(service_name: str, **kwargs: Any) -> MagicMock:
        return service_mocks.get(service_name, MagicMock())

    with patch("boto3.client", side_effect=get_client):
        yield service_mocks


@contextmanager
def chaos_api_failures(failure_rate: float = 0.1):
    """Context manager to inject random API failures for chaos testing."""
    import random

    def random_failure(*args: Any, **kwargs: Any) -> Any:
        if random.random() < failure_rate:
            raise ConnectionError("Simulated API failure")
        return MagicMock()

    # This would need to be applied to specific API calls in actual implementation
    yield random_failure


@contextmanager
def lambda_timeout_simulation(timeout_after_seconds: int = 25):
    """Context manager to simulate Lambda timeouts."""
    import signal

    def timeout_handler(signum: int, frame: Any) -> None:
        raise TimeoutError("Lambda timeout simulation")

    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_after_seconds)

    try:
        yield
    finally:
        signal.alarm(0)  # Cancel the alarm


class TestDataBuilder:
    """Builder pattern for creating complex test data scenarios."""

    def __init__(self) -> None:
        self.portfolio_value = Decimal("100000.00")
        self.positions: dict[str, Any] = {}
        self.cash_ratio = 0.1
        self.symbols: list[str] = []

    def with_portfolio_value(self, value: Decimal) -> "TestDataBuilder":
        """Set the total portfolio value."""
        self.portfolio_value = value
        return self

    def with_position(self, symbol: str, shares: int, avg_price: float) -> "TestDataBuilder":
        """Add a position to the portfolio."""
        self.positions[symbol] = {
            "shares": shares,
            "avg_price": avg_price,
            "market_value": shares * avg_price,
        }
        self.symbols.append(symbol)
        return self

    def with_cash_ratio(self, ratio: float) -> "TestDataBuilder":
        """Set the cash allocation ratio."""
        self.cash_ratio = ratio
        return self

    def build(self) -> dict[str, Any]:
        """Build the final portfolio state."""
        cash_value = float(self.portfolio_value) * self.cash_ratio

        return {
            "portfolio_value": self.portfolio_value,
            "cash": cash_value,
            "positions": self.positions,
            "symbols": self.symbols,
            "timestamp": pd.Timestamp.now(),
        }


def create_test_scenario(scenario_name: str) -> dict[str, Any]:
    """Create predefined test scenarios."""
    scenarios = {
        "normal_portfolio": (
            TestDataBuilder()
            .with_portfolio_value(Decimal("100000.00"))
            .with_position("SPY", 200, 400.0)
            .with_position("QQQ", 100, 350.0)
            .with_position("AAPL", 50, 150.0)
            .with_cash_ratio(0.15)
            .build()
        ),
        "concentrated_portfolio": (
            TestDataBuilder()
            .with_portfolio_value(Decimal("50000.00"))
            .with_position("NVDA", 50, 800.0)
            .with_position("TSLA", 100, 200.0)
            .with_cash_ratio(0.2)
            .build()
        ),
        "cash_heavy_portfolio": (
            TestDataBuilder()
            .with_portfolio_value(Decimal("75000.00"))
            .with_position("SPY", 50, 400.0)
            .with_cash_ratio(0.75)
            .build()
        ),
    }

    return scenarios.get(scenario_name, {})
