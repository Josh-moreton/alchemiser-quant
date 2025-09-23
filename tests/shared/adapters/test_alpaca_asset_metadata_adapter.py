"""Tests for AlpacaAssetMetadataAdapter."""

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import AlpacaAssetMetadataAdapter
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO
from the_alchemiser.shared.value_objects.symbol import Symbol


@pytest.fixture
def mock_alpaca_manager():
    """Create a mock AlpacaManager."""
    manager = Mock()
    return manager


@pytest.fixture
def adapter(mock_alpaca_manager):
    """Create an AlpacaAssetMetadataAdapter with mock AlpacaManager."""
    return AlpacaAssetMetadataAdapter(mock_alpaca_manager)


def test_is_fractionable_true(adapter, mock_alpaca_manager):
    """Test is_fractionable for fractionable asset."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    result = adapter.is_fractionable(symbol)
    
    assert result is True
    mock_alpaca_manager.is_fractionable.assert_called_once_with("AAPL")


def test_is_fractionable_false(adapter, mock_alpaca_manager):
    """Test is_fractionable for non-fractionable asset."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = False
    
    symbol = Symbol("EDZ")
    result = adapter.is_fractionable(symbol)
    
    assert result is False
    mock_alpaca_manager.is_fractionable.assert_called_once_with("EDZ")


def test_get_asset_class_with_info(adapter, mock_alpaca_manager):
    """Test get_asset_class when asset info is available."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        asset_class="us_equity",
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    symbol = Symbol("AAPL")
    result = adapter.get_asset_class(symbol)
    
    assert result == "us_equity"
    mock_alpaca_manager.get_asset_info.assert_called_once_with("AAPL")


def test_get_asset_class_no_info(adapter, mock_alpaca_manager):
    """Test get_asset_class when asset info is unavailable."""
    # Setup mock to return None
    mock_alpaca_manager.get_asset_info.return_value = None
    
    symbol = Symbol("XYZ")
    result = adapter.get_asset_class(symbol)
    
    assert result == "unknown"
    mock_alpaca_manager.get_asset_info.assert_called_once_with("XYZ")


def test_get_asset_class_no_asset_class_field(adapter, mock_alpaca_manager):
    """Test get_asset_class when asset info has no asset_class."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        asset_class=None,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    symbol = Symbol("AAPL")
    result = adapter.get_asset_class(symbol)
    
    assert result == "unknown"


def test_should_use_notional_order_non_fractionable(adapter, mock_alpaca_manager):
    """Test should_use_notional_order for non-fractionable asset."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = False
    
    symbol = Symbol("EDZ")
    result = adapter.should_use_notional_order(symbol, 1.5)
    
    # Should use notional for non-fractionable assets
    assert result is True


def test_should_use_notional_order_small_quantity(adapter, mock_alpaca_manager):
    """Test should_use_notional_order for small fractional amounts."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    result = adapter.should_use_notional_order(symbol, 0.5)
    
    # Should use notional for quantities < 1
    assert result is True


def test_should_use_notional_order_large_fractional(adapter, mock_alpaca_manager):
    """Test should_use_notional_order for large fractional part."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    result = adapter.should_use_notional_order(symbol, 5.8)
    
    # Should use notional for fractional part > 0.1
    assert result is True


def test_should_use_notional_order_small_fractional_part(adapter, mock_alpaca_manager):
    """Test should_use_notional_order for small fractional part."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    result = adapter.should_use_notional_order(symbol, 5.05)
    
    # Should not use notional for small fractional part
    assert result is False


def test_should_use_notional_order_whole_number(adapter, mock_alpaca_manager):
    """Test should_use_notional_order for whole number quantities."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    result = adapter.should_use_notional_order(symbol, 10.0)
    
    # Should not use notional for whole numbers
    assert result is False


def test_adapter_implements_protocol(adapter):
    """Test that adapter properly implements AssetMetadataProvider protocol."""
    # This test verifies that the adapter has all required methods
    assert hasattr(adapter, 'is_fractionable')
    assert hasattr(adapter, 'get_asset_class')
    assert hasattr(adapter, 'should_use_notional_order')
    
    # Test that methods are callable
    assert callable(adapter.is_fractionable)
    assert callable(adapter.get_asset_class)
    assert callable(adapter.should_use_notional_order)


def test_symbol_conversion(adapter, mock_alpaca_manager):
    """Test that Symbol objects are properly converted to strings."""
    # Setup mock
    mock_alpaca_manager.is_fractionable.return_value = True
    
    symbol = Symbol("AAPL")
    adapter.is_fractionable(symbol)
    
    # Verify that string representation of symbol was used
    mock_alpaca_manager.is_fractionable.assert_called_once_with("AAPL")