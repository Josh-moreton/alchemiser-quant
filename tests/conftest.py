"""Pytest configuration and shared fixtures for The Alchemiser test suite."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any
from decimal import Decimal

from the_alchemiser.core.types import AccountInfo, PositionInfo, OrderDetails


@pytest.fixture
def mock_account_info() -> AccountInfo:
    """Mock account info for testing."""
    return {
        "account_id": "test_account_123",
        "equity": "100000.00",
        "cash": "50000.00",
        "buying_power": "200000.00",
        "day_trades_remaining": 3,
        "portfolio_value": "100000.00",
        "last_equity": "98000.00",
        "daytrading_buying_power": "400000.00",
        "regt_buying_power": "200000.00",
        "status": "ACTIVE"
    }


@pytest.fixture
def mock_positions() -> Dict[str, PositionInfo]:
    """Mock position data for testing."""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "qty": "100.0",
            "side": "long",
            "market_value": "15000.00",
            "cost_basis": "14000.00",
            "unrealized_pl": "1000.00",
            "unrealized_plpc": "7.14",
            "current_price": "150.00"
        },
        "MSFT": {
            "symbol": "MSFT",
            "qty": "50.0",
            "side": "long",
            "market_value": "12500.00",
            "cost_basis": "12000.00",
            "unrealized_pl": "500.00",
            "unrealized_plpc": "4.17",
            "current_price": "250.00"
        }
    }


@pytest.fixture
def mock_order_details() -> OrderDetails:
    """Mock order details for testing."""
    return {
        "id": "order_123",
        "symbol": "AAPL",
        "qty": "10.0",
        "side": "buy",
        "order_type": "market",
        "time_in_force": "day",
        "status": "filled",
        "filled_qty": "10.0",
        "filled_avg_price": "150.00",
        "created_at": "2025-08-05T10:00:00Z",
        "updated_at": "2025-08-05T10:01:00Z"
    }


@pytest.fixture
def mock_trading_bot():
    """Mock trading bot for portfolio rebalancer testing."""
    bot = Mock()
    
    # Mock account info
    bot.get_account_info.return_value = {
        "portfolio_value": 100000.0,
        "cash": 50000.0,
        "buying_power": 200000.0
    }
    
    # Mock positions
    bot.get_positions_dict.return_value = {
        "AAPL": Mock(market_value=15000.0, qty=100.0),
        "MSFT": Mock(market_value=12500.0, qty=50.0)
    }
    
    # Mock current prices
    def mock_get_current_price(symbol: str) -> float:
        prices = {"AAPL": 150.0, "MSFT": 250.0, "GOOGL": 120.0}
        return prices.get(symbol, 100.0)
    
    bot.get_current_price.side_effect = mock_get_current_price
    
    # Mock order manager
    bot.order_manager = Mock()
    bot.order_manager.place_order.return_value = "mock_order_id_123"
    
    return bot


@pytest.fixture
def sample_target_portfolio() -> Dict[str, float]:
    """Sample target portfolio allocation for testing."""
    return {
        "AAPL": 0.40,  # 40% allocation
        "MSFT": 0.30,  # 30% allocation
        "GOOGL": 0.30  # 30% allocation (new position)
    }


@pytest.fixture
def mock_data_provider():
    """Mock data provider for strategy testing."""
    provider = Mock()
    
    # Mock market data
    import pandas as pd
    sample_data = pd.DataFrame({
        "Open": [100, 101, 102],
        "High": [105, 106, 107],
        "Low": [99, 98, 100],
        "Close": [104, 105, 106],
        "Volume": [1000000, 1100000, 1200000]
    })
    
    provider.get_data.return_value = sample_data
    provider.get_current_price.return_value = 105.0
    
    return provider


@pytest.fixture
def mock_strategy_signals() -> Dict[str, Any]:
    """Mock strategy signals for testing."""
    return {
        "NUCLEAR": {
            "symbol": "AAPL",
            "action": "BUY",
            "reason": "Nuclear strategy signal",
            "allocation_percentage": 0.4
        },
        "TECL": {
            "symbol": "MSFT",
            "action": "BUY", 
            "reason": "TECL strategy signal",
            "allocation_percentage": 0.3
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "strategy: marks tests related to trading strategies")
    config.addinivalue_line("markers", "portfolio: marks tests related to portfolio management")
