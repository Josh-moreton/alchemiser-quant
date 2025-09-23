"""Tests for ExecutionValidator."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    ExecutionValidationError,
    OrderValidationResult,
)
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO


@pytest.fixture
def mock_alpaca_manager():
    """Create a mock AlpacaManager."""
    manager = Mock()
    return manager


@pytest.fixture
def validator(mock_alpaca_manager):
    """Create an ExecutionValidator with mock AlpacaManager."""
    return ExecutionValidator(mock_alpaca_manager)


def test_validate_fractionable_asset(validator, mock_alpaca_manager):
    """Test validation for fractionable asset."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test fractional quantity
    result = validator.validate_order("AAPL", Decimal("1.5"), "buy")
    
    assert result.is_valid
    assert result.adjusted_quantity is None
    assert result.warnings == []
    assert result.error_message is None


def test_validate_non_fractionable_asset_fractional_quantity(validator, mock_alpaca_manager):
    """Test validation for non-fractionable asset with fractional quantity."""
    # Setup mock for EDZ (known non-fractionable)
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test fractional quantity with auto-adjust
    result = validator.validate_order("EDZ", Decimal("2.7"), "buy", auto_adjust=True)
    
    assert result.is_valid
    assert result.adjusted_quantity == Decimal("2")
    assert len(result.warnings) == 1
    assert "adjusted quantity 2.7 → 2 shares" in result.warnings[0]
    assert result.error_message is None


def test_validate_non_fractionable_asset_whole_quantity(validator, mock_alpaca_manager):
    """Test validation for non-fractionable asset with whole quantity."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test whole number quantity
    result = validator.validate_order("EDZ", Decimal("3"), "sell")
    
    assert result.is_valid
    assert result.adjusted_quantity is None
    assert result.warnings == []
    assert result.error_message is None


def test_validate_non_fractionable_asset_no_auto_adjust(validator, mock_alpaca_manager):
    """Test validation for non-fractionable asset without auto-adjust."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test fractional quantity without auto-adjust
    result = validator.validate_order("EDZ", Decimal("2.5"), "buy", auto_adjust=False)
    
    assert not result.is_valid
    assert result.adjusted_quantity is None
    assert result.error_code == "40310000"
    assert "not fractionable" in result.error_message


def test_validate_non_fractionable_asset_rounds_to_zero(validator, mock_alpaca_manager):
    """Test validation when rounding results in zero quantity."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test small fractional quantity that rounds to zero
    result = validator.validate_order("EDZ", Decimal("0.3"), "buy", auto_adjust=True)
    
    assert not result.is_valid
    assert result.error_code == "ZERO_QUANTITY_AFTER_ROUNDING"
    assert "rounds to zero" in result.error_message


def test_validate_non_tradable_asset(validator, mock_alpaca_manager):
    """Test validation for non-tradable asset."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="SUSPEND",
        fractionable=True,
        tradable=False,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test any quantity
    result = validator.validate_order("SUSPEND", Decimal("1"), "buy")
    
    assert not result.is_valid
    assert result.error_code == "NOT_TRADABLE"
    assert "not tradable" in result.error_message


def test_validate_asset_info_unavailable(validator, mock_alpaca_manager):
    """Test validation when asset info is unavailable."""
    # Setup mock to return None
    mock_alpaca_manager.get_asset_info.return_value = None
    
    # Test should allow order to proceed
    result = validator.validate_order("UNKNOWN", Decimal("1"), "buy")
    
    assert result.is_valid
    assert result.adjusted_quantity is None
    assert result.warnings == []


def test_validate_invalid_quantity(validator, mock_alpaca_manager):
    """Test validation with invalid quantity."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test zero quantity
    result = validator.validate_order("AAPL", Decimal("0"), "buy")
    
    assert not result.is_valid
    assert result.error_code == "INVALID_QUANTITY"
    assert "Invalid quantity" in result.error_message
    
    # Test negative quantity
    result = validator.validate_order("AAPL", Decimal("-1"), "sell")
    
    assert not result.is_valid
    assert result.error_code == "INVALID_QUANTITY"
    assert "Invalid quantity" in result.error_message


def test_validate_with_correlation_id(validator, mock_alpaca_manager):
    """Test validation with correlation ID for tracing."""
    # Setup mock
    asset_info = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        tradable=True,
    )
    mock_alpaca_manager.get_asset_info.return_value = asset_info
    
    # Test with correlation ID
    result = validator.validate_order(
        "EDZ", 
        Decimal("2.3"), 
        "buy", 
        correlation_id="test-123",
        auto_adjust=True
    )
    
    assert result.is_valid
    assert result.adjusted_quantity == Decimal("2")
    # Correlation ID should be used in logging (not directly testable without log capture)