"""Tests for strategy market data adapter.

Validates that the adapter correctly bridges DataFrame-based strategies
to the canonical domain MarketDataPort.
"""

from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock
import pandas as pd
import pytest

from the_alchemiser.application.mapping.strategy_market_data_adapter import StrategyMarketDataAdapter
from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel
from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol


def test_adapter_get_data_with_bars():
    """Test adapter converts bars to DataFrame correctly."""
    # Mock canonical port
    mock_port = Mock()
    
    # Mock bar data
    mock_bars = [
        BarModel(
            ts=datetime(2023, 1, 1, 9, 30),
            open=Decimal("100.00"),
            high=Decimal("101.00"),
            low=Decimal("99.00"),
            close=Decimal("100.50"),
            volume=Decimal("1000")
        ),
        BarModel(
            ts=datetime(2023, 1, 1, 9, 31),
            open=Decimal("100.50"),
            high=Decimal("102.00"),
            low=Decimal("100.00"),
            close=Decimal("101.25"),
            volume=Decimal("1500")
        )
    ]
    mock_port.get_bars.return_value = mock_bars
    
    # Create adapter
    adapter = StrategyMarketDataAdapter(mock_port)
    
    # Test get_data method
    df = adapter.get_data("AAPL", timeframe="1min", period="1d")
    
    # Verify port was called correctly
    mock_port.get_bars.assert_called_once_with(Symbol("AAPL"), "1d", "1min")
    
    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "timestamp"
    
    # Verify data conversion
    assert df.iloc[0]["open"] == 100.00
    assert df.iloc[0]["close"] == 100.50
    assert df.iloc[1]["high"] == 102.00


def test_adapter_get_data_empty_bars():
    """Test adapter handles empty bars correctly."""
    mock_port = Mock()
    mock_port.get_bars.return_value = []
    
    adapter = StrategyMarketDataAdapter(mock_port)
    df = adapter.get_data("AAPL")
    
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_adapter_get_current_price():
    """Test adapter get_current_price method."""
    mock_port = Mock()
    mock_port.get_mid_price.return_value = 150.75
    
    adapter = StrategyMarketDataAdapter(mock_port)
    price = adapter.get_current_price("MSFT")
    
    mock_port.get_mid_price.assert_called_once_with(Symbol("MSFT"))
    assert price == 150.75


def test_adapter_get_current_price_none():
    """Test adapter handles None price correctly."""
    mock_port = Mock()
    mock_port.get_mid_price.return_value = None
    
    adapter = StrategyMarketDataAdapter(mock_port)
    price = adapter.get_current_price("INVALID")
    
    assert price is None


def test_adapter_get_latest_quote():
    """Test adapter get_latest_quote method."""
    mock_port = Mock()
    mock_quote = QuoteModel(
        ts=datetime.now(),
        bid=Decimal("99.95"),
        ask=Decimal("100.05")
    )
    mock_port.get_latest_quote.return_value = mock_quote
    
    adapter = StrategyMarketDataAdapter(mock_port)
    bid, ask = adapter.get_latest_quote("GOOGL")
    
    mock_port.get_latest_quote.assert_called_once_with(Symbol("GOOGL"))
    assert bid == 99.95
    assert ask == 100.05


def test_adapter_get_latest_quote_none():
    """Test adapter handles None quote correctly."""
    mock_port = Mock()
    mock_port.get_latest_quote.return_value = None
    
    adapter = StrategyMarketDataAdapter(mock_port)
    bid, ask = adapter.get_latest_quote("INVALID")
    
    assert bid is None
    assert ask is None


def test_adapter_symbol_conversion():
    """Test that string symbols are properly converted to Symbol objects."""
    mock_port = Mock()
    mock_port.get_bars.return_value = []
    
    adapter = StrategyMarketDataAdapter(mock_port)
    adapter.get_data("  aapl  ")  # Test with whitespace
    
    # Should be normalized to uppercase Symbol
    mock_port.get_bars.assert_called_with(Symbol("AAPL"), "1y", "1day")