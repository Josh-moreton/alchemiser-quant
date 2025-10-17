"""Business Unit: execution | Status: current

Comprehensive unit tests for execution validation utilities.

This test suite provides coverage of execution validation functions including
order validation, quantity checks, and fractional asset handling.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock

from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    OrderValidationResult,
    ExecutionValidationError,
)
from the_alchemiser.shared.schemas.asset_info import AssetInfo


class TestExecutionValidator:
    """Test execution validator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_alpaca_manager = MagicMock()
        self.validator = ExecutionValidator(self.mock_alpaca_manager)

    def test_validate_order_fractionable_asset_valid(self):
        """Test validation of valid order for fractionable asset."""
        # Mock asset info for fractionable asset
        asset_info = AssetInfo(
            symbol="AAPL",
            name="Apple Inc",
            asset_class="us_equity",
            tradable=True,
            fractionable=True
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("AAPL", Decimal("10.5"))
        
        assert result.is_valid is True
        assert result.adjusted_quantity is None
        assert len(result.warnings) == 0

    def test_validate_order_non_fractionable_whole_quantity(self):
        """Test validation of whole quantity for non-fractionable asset."""
        # Mock asset info for non-fractionable asset
        asset_info = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Class A",
            asset_class="us_equity",
            tradable=True,
            fractionable=False
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("BRK.A", Decimal("5"))
        
        assert result.is_valid is True
        assert result.adjusted_quantity is None
        assert len(result.warnings) == 0

    def test_validate_order_non_fractionable_fractional_quantity_auto_adjust(self):
        """Test validation of fractional quantity for non-fractionable asset with auto-adjust."""
        # Mock asset info for non-fractionable asset
        asset_info = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Class A",
            asset_class="us_equity",
            tradable=True,
            fractionable=False
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("BRK.A", Decimal("5.7"), auto_adjust=True)
        
        assert result.is_valid is True
        assert result.adjusted_quantity == Decimal("5")
        assert len(result.warnings) == 1
        assert "adjusted quantity 5.7 → 5 shares" in result.warnings[0]

    def test_validate_order_non_fractionable_fractional_quantity_no_auto_adjust(self):
        """Test validation of fractional quantity for non-fractionable asset without auto-adjust."""
        # Mock asset info for non-fractionable asset
        asset_info = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Class A",
            asset_class="us_equity",
            tradable=True,
            fractionable=False
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("BRK.A", Decimal("5.7"), auto_adjust=False)
        
        assert result.is_valid is False
        assert result.error_code == "40310000"
        assert "not fractionable but quantity 5.7 is fractional" in result.error_message

    def test_validate_order_non_fractionable_rounds_to_zero(self):
        """Test validation when fractional quantity rounds to zero."""
        # Mock asset info for non-fractionable asset
        asset_info = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Class A",
            asset_class="us_equity",
            tradable=True,
            fractionable=False
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("BRK.A", Decimal("0.3"), auto_adjust=True)
        
        assert result.is_valid is False
        assert result.error_code == "ZERO_QUANTITY_AFTER_ROUNDING"
        assert "rounds to zero" in result.error_message

    def test_validate_order_not_tradable_asset(self):
        """Test validation rejects non-tradable assets."""
        # Mock asset info for non-tradable asset
        asset_info = AssetInfo(
            symbol="DELISTED",
            name="Delisted Stock",
            asset_class="us_equity",
            tradable=False,
            fractionable=True
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("DELISTED", Decimal("10"))
        
        assert result.is_valid is False
        assert result.error_code == "NOT_TRADABLE"
        assert "is not tradable" in result.error_message

    def test_validate_order_invalid_quantity(self):
        """Test validation rejects invalid quantities."""
        # Mock asset info for fractionable asset
        asset_info = AssetInfo(
            symbol="AAPL",
            name="Apple Inc",
            asset_class="us_equity",
            tradable=True,
            fractionable=True
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("AAPL", Decimal("0"))
        
        assert result.is_valid is False
        assert result.error_code == "INVALID_QUANTITY"

    def test_validate_order_negative_quantity(self):
        """Test validation rejects negative quantities."""
        # Mock asset info for fractionable asset
        asset_info = AssetInfo(
            symbol="AAPL",
            name="Apple Inc",
            asset_class="us_equity",
            tradable=True,
            fractionable=True
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order("AAPL", Decimal("-5"))
        
        assert result.is_valid is False
        assert result.error_code == "INVALID_QUANTITY"

    def test_validate_order_no_asset_info_allows_order(self):
        """Test validation allows order when asset info is unavailable."""
        # Mock get_asset_info to return None (asset info unavailable)
        self.mock_alpaca_manager.get_asset_info.return_value = None
        
        result = self.validator.validate_order("UNKNOWN", Decimal("10"))
        
        assert result.is_valid is True
        assert result.adjusted_quantity is None

    def test_validate_order_with_correlation_id(self):
        """Test validation includes correlation ID in logging."""
        # Mock asset info for fractionable asset
        asset_info = AssetInfo(
            symbol="AAPL",
            name="Apple Inc",
            asset_class="us_equity",
            tradable=True,
            fractionable=True
        )
        self.mock_alpaca_manager.get_asset_info.return_value = asset_info
        
        result = self.validator.validate_order(
            "AAPL", Decimal("10.5"), correlation_id="test-correlation-123"
        )
        
        assert result.is_valid is True


class TestExecutionValidationError:
    """Test execution validation error class."""

    def test_execution_validation_error_creation(self):
        """Test creation of execution validation errors."""
        error = ExecutionValidationError(
            "Test error message",
            symbol="AAPL",
            code="TEST_ERROR"
        )
        
        assert str(error) == "Test error message"
        assert error.symbol == "AAPL"
        assert error.code == "TEST_ERROR"

    def test_execution_validation_error_without_code(self):
        """Test creation of execution validation error without error code."""
        error = ExecutionValidationError(
            "Test error message",
            symbol="AAPL"
        )
        
        assert str(error) == "Test error message"
        assert error.symbol == "AAPL"
        assert error.code is None


class TestOrderValidationResult:
    """Test order validation result class."""

    def test_order_validation_result_valid(self):
        """Test creation of valid order validation result."""
        result = OrderValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.adjusted_quantity is None
        assert result.warnings == ()
        assert result.error_message is None
        assert result.error_code is None
        assert result.schema_version == "1.0"
        assert result.correlation_id is None

    def test_order_validation_result_invalid_with_error(self):
        """Test creation of invalid order validation result with error."""
        result = OrderValidationResult(
            is_valid=False,
            error_message="Invalid order",
            error_code="INVALID_ORDER"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Invalid order"
        assert result.error_code == "INVALID_ORDER"
        assert result.schema_version == "1.0"

    def test_order_validation_result_with_adjustment(self):
        """Test creation of validation result with quantity adjustment."""
        result = OrderValidationResult(
            is_valid=True,
            adjusted_quantity=Decimal("5"),
            warnings=("Quantity adjusted from 5.7 to 5 shares",)
        )
        
        assert result.is_valid is True
        assert result.adjusted_quantity == Decimal("5")
        assert len(result.warnings) == 1
        assert "adjusted" in result.warnings[0]
        assert result.schema_version == "1.0"

    def test_order_validation_result_is_immutable(self):
        """Test that OrderValidationResult is frozen and immutable."""
        result = OrderValidationResult(is_valid=True)
        
        # Attempt to modify should raise an error
        with pytest.raises(Exception):  # Pydantic raises ValidationError or AttributeError
            result.is_valid = False

    def test_order_validation_result_with_correlation_id(self):
        """Test that correlation_id is captured in result."""
        result = OrderValidationResult(
            is_valid=True,
            correlation_id="test-correlation-123"
        )
        
        assert result.correlation_id == "test-correlation-123"
        assert result.schema_version == "1.0"