"""End-to-end integration test for non-fractionable asset support."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.utils.execution_validator import ExecutionValidator
from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import AlpacaAssetMetadataAdapter
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO
from the_alchemiser.shared.value_objects.symbol import Symbol


@pytest.fixture
def mock_alpaca_manager():
    """Create a comprehensive mock AlpacaManager for integration testing."""
    manager = Mock()
    
    # Setup asset info for EDZ (non-fractionable)
    edz_asset_info = AssetInfoDTO(
        symbol="EDZ",
        name="Direxion Daily MSCI Emerging Markets Bear 3X Shares",
        exchange="NASDAQ",
        asset_class="us_equity",
        tradable=True,
        fractionable=False,  # Key: non-fractionable
        marginable=True,
        shortable=True,
    )
    
    # Setup asset info for AAPL (fractionable)
    aapl_asset_info = AssetInfoDTO(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        asset_class="us_equity",
        tradable=True,
        fractionable=True,  # Key: fractionable
        marginable=True,
        shortable=True,
    )
    
    # Configure mock responses
    def get_asset_info_side_effect(symbol):
        if symbol.upper() == "EDZ":
            return edz_asset_info
        elif symbol.upper() == "AAPL":
            return aapl_asset_info
        return None
    
    def is_fractionable_side_effect(symbol):
        if symbol.upper() == "EDZ":
            return False
        elif symbol.upper() == "AAPL":
            return True
        return True  # Default to fractionable for unknown assets
    
    manager.get_asset_info.side_effect = get_asset_info_side_effect
    manager.is_fractionable.side_effect = is_fractionable_side_effect
    
    return manager


def test_end_to_end_non_fractionable_edz(mock_alpaca_manager):
    """Test end-to-end flow for EDZ (non-fractionable asset)."""
    # Create components
    validator = ExecutionValidator(mock_alpaca_manager)
    adapter = AlpacaAssetMetadataAdapter(mock_alpaca_manager)
    executor = Executor(mock_alpaca_manager, enable_smart_execution=False)
    
    # Test 1: Asset metadata retrieval
    edz_symbol = Symbol("EDZ")
    assert not adapter.is_fractionable(edz_symbol)
    assert adapter.get_asset_class(edz_symbol) == "us_equity"
    assert adapter.should_use_notional_order(edz_symbol, 1.5)  # Always notional for non-fractionable
    
    # Test 2: Execution validation with fractional quantity
    validation_result = validator.validate_order("EDZ", Decimal("2.7"), "buy", auto_adjust=True)
    assert validation_result.is_valid
    assert validation_result.adjusted_quantity == Decimal("2")
    assert len(validation_result.warnings) == 1
    assert "adjusted quantity 2.7 → 2 shares" in validation_result.warnings[0]
    
    # Test 3: Portfolio sizing adjustment
    # Simulate portfolio sizing calculation: $1000 trade at $45.67/share = ~21.895 shares
    trade_amount = Decimal("1000.00")
    price = Decimal("45.67")
    raw_shares = trade_amount / price  # ~21.895 shares
    
    adjusted_shares = executor._adjust_quantity_for_fractionability("EDZ", raw_shares)
    assert adjusted_shares == Decimal("21")  # Rounded down to whole shares
    
    # Verify the actual investment amount is slightly less due to rounding
    actual_investment = adjusted_shares * price
    assert actual_investment == Decimal("959.07")  # 21 * 45.67
    assert actual_investment < trade_amount  # Less than intended due to rounding
    
    # Test 4: Validation would reject without auto-adjust
    validation_result_strict = validator.validate_order("EDZ", Decimal("2.5"), "buy", auto_adjust=False)
    assert not validation_result_strict.is_valid
    assert validation_result_strict.error_code == "40310000"  # Alpaca non-fractionable error
    assert "not fractionable" in validation_result_strict.error_message


def test_end_to_end_fractionable_aapl(mock_alpaca_manager):
    """Test end-to-end flow for AAPL (fractionable asset) as comparison."""
    # Create components
    validator = ExecutionValidator(mock_alpaca_manager)
    adapter = AlpacaAssetMetadataAdapter(mock_alpaca_manager)
    executor = Executor(mock_alpaca_manager, enable_smart_execution=False)
    
    # Test 1: Asset metadata retrieval
    aapl_symbol = Symbol("AAPL")
    assert adapter.is_fractionable(aapl_symbol)
    assert adapter.get_asset_class(aapl_symbol) == "us_equity"
    assert not adapter.should_use_notional_order(aapl_symbol, 5.05)  # Small fractional part
    assert adapter.should_use_notional_order(aapl_symbol, 5.8)  # Large fractional part
    
    # Test 2: Execution validation with fractional quantity
    validation_result = validator.validate_order("AAPL", Decimal("2.7"), "buy")
    assert validation_result.is_valid
    assert validation_result.adjusted_quantity is None  # No adjustment needed
    assert validation_result.warnings == []
    
    # Test 3: Portfolio sizing - no adjustment needed
    raw_shares = Decimal("21.895")
    adjusted_shares = executor._adjust_quantity_for_fractionability("AAPL", raw_shares)
    assert adjusted_shares == Decimal("21.895000")  # Standard fractional quantization
    
    # Test 4: Fractional quantities are allowed
    validation_result_fractional = validator.validate_order("AAPL", Decimal("2.123456"), "buy")
    assert validation_result_fractional.is_valid
    assert validation_result_fractional.adjusted_quantity is None


def test_integration_zero_quantity_after_rounding(mock_alpaca_manager):
    """Test integration when rounding results in zero quantity."""
    validator = ExecutionValidator(mock_alpaca_manager)
    executor = Executor(mock_alpaca_manager, enable_smart_execution=False)
    
    # Small fractional quantity that rounds to zero
    small_quantity = Decimal("0.3")
    
    # Test validation catches this
    validation_result = validator.validate_order("EDZ", small_quantity, "buy", auto_adjust=True)
    assert not validation_result.is_valid
    assert validation_result.error_code == "ZERO_QUANTITY_AFTER_ROUNDING"
    
    # Test portfolio sizing also handles this
    adjusted = executor._adjust_quantity_for_fractionability("EDZ", small_quantity)
    assert adjusted == Decimal("0")


def test_integration_unknown_asset_fallback(mock_alpaca_manager):
    """Test integration behavior for unknown assets."""
    # Mock will return None for unknown assets
    validator = ExecutionValidator(mock_alpaca_manager)
    executor = Executor(mock_alpaca_manager, enable_smart_execution=False)
    
    # Test validation allows unknown assets to proceed
    validation_result = validator.validate_order("UNKN", Decimal("1.5"), "buy")
    assert validation_result.is_valid
    assert validation_result.adjusted_quantity is None
    
    # Test portfolio sizing defaults to fractional for unknown assets
    adjusted = executor._adjust_quantity_for_fractionability("UNKN", Decimal("1.234567"))
    assert adjusted == Decimal("1.234567")  # Should use fractional as fallback


def test_alpaca_error_code_mapping():
    """Test that we properly map to Alpaca's 40310000 error code."""
    mock_manager = Mock()
    mock_manager.get_asset_info.return_value = AssetInfoDTO(
        symbol="EDZ", fractionable=False, tradable=True
    )
    
    validator = ExecutionValidator(mock_manager)
    
    # Test that we use the correct Alpaca error code
    result = validator.validate_order("EDZ", Decimal("1.5"), "buy", auto_adjust=False)
    assert not result.is_valid
    assert result.error_code == "40310000"  # Alpaca's actual error code for non-fractionable assets