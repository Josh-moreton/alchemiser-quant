"""Tests for portfolio sizing with non-fractionable assets."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO


@pytest.fixture
def mock_alpaca_manager():
    """Create a mock AlpacaManager."""
    manager = Mock()
    return manager


@pytest.fixture
def executor(mock_alpaca_manager):
    """Create an Executor with mock AlpacaManager."""
    return Executor(mock_alpaca_manager, enable_smart_execution=False)


def test_adjust_quantity_fractionable_asset(executor, mock_alpaca_manager):
    """Test quantity adjustment for fractionable asset."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test fractional quantity
    result = executor._adjust_quantity_for_fractionability("AAPL", Decimal("1.234567"))
    
    # Should use standard fractional quantization
    expected = Decimal("1.234567")
    assert result == expected


def test_adjust_quantity_non_fractionable_asset(executor, mock_alpaca_manager):
    """Test quantity adjustment for non-fractionable asset."""
    # Setup mock for EDZ (known non-fractionable)
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test fractional quantity
    result = executor._adjust_quantity_for_fractionability("EDZ", Decimal("2.7"))
    
    # Should round down to whole shares
    assert result == Decimal("2")


def test_adjust_quantity_non_fractionable_already_whole(executor, mock_alpaca_manager):
    """Test quantity adjustment for non-fractionable asset that's already whole."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test whole number quantity
    result = executor._adjust_quantity_for_fractionability("EDZ", Decimal("3"))
    
    # Should remain unchanged
    assert result == Decimal("3")


def test_adjust_quantity_non_fractionable_rounds_to_zero(executor, mock_alpaca_manager):
    """Test quantity adjustment when rounding would result in zero."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test small fractional quantity
    result = executor._adjust_quantity_for_fractionability("EDZ", Decimal("0.9"))
    
    # Should round down to zero
    assert result == Decimal("0")


def test_adjust_quantity_asset_info_unavailable(executor, mock_alpaca_manager):
    """Test quantity adjustment when asset info is unavailable."""
    # Setup mock to return None
    mock_alpaca_manager.get_asset_info.return_value = None
    
    # Test should default to fractional behavior
    result = executor._adjust_quantity_for_fractionability("UNKNOWN", Decimal("1.5"))
    
    # Should use standard fractional quantization as fallback
    assert result == Decimal("1.500000")  # quantized to 6 decimal places


def test_adjust_quantity_negative_input(executor, mock_alpaca_manager):
    """Test quantity adjustment with negative input."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test negative quantity (shouldn't happen in practice but test defensive code)
    result = executor._adjust_quantity_for_fractionability("EDZ", Decimal("-1.5"))
    
    # Should return 0 (minimum)
    assert result == Decimal("0")


def test_adjust_quantity_large_fractional(executor, mock_alpaca_manager):
    """Test quantity adjustment for large fractional amounts."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test large fractional quantity
    result = executor._adjust_quantity_for_fractionability("EDZ", Decimal("100.99"))
    
    # Should round down to 100
    assert result == Decimal("100")


def test_portfolio_sizing_integration(executor, mock_alpaca_manager):
    """Test the integration of quantity adjustment in portfolio sizing context."""
    # This test verifies the method exists and can be called
    # In a real integration test, we would test the full flow through execute_rebalance_item
    
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Simulate the calculation that would happen in portfolio sizing
    trade_amount = Decimal("1000.00")  # $1000 trade
    price = Decimal("45.67")  # $45.67 per share
    raw_shares = trade_amount / price  # ~21.895 shares
    
    # Adjust for non-fractionable asset
    adjusted_shares = executor._adjust_quantity_for_fractionability("EDZ", raw_shares)
    
    # Should be rounded down to whole shares
    assert adjusted_shares == Decimal("21")
    
    # Verify the actual dollar amount would be slightly less
    actual_dollar_amount = adjusted_shares * price
    assert actual_dollar_amount < trade_amount
    assert actual_dollar_amount == Decimal("959.07")  # 21 * 45.67