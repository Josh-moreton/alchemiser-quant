"""Business Unit: execution | Status: current

Unit tests for execution_v2/core/smart_execution_strategy/__init__.py.

Tests module structure, documentation, imports, and accessibility patterns
for the smart execution strategy package public API.

Note: SmartExecutionStrategy has been replaced by UnifiedOrderPlacementService.
This module now only exports configuration and data models.
"""

import pytest


class TestSmartExecutionStrategyInit:
    """Test smart_execution_strategy __init__.py module structure."""

    def test_module_docstring_exists(self):
        """Test that the module has proper docstring with Business Unit marker."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert smart_execution_strategy.__doc__ is not None
        assert "Business Unit: execution" in smart_execution_strategy.__doc__
        assert "Status: current" in smart_execution_strategy.__doc__

    def test_module_describes_purpose(self):
        """Test that docstring describes the module's purpose."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert "execution" in smart_execution_strategy.__doc__.lower()

    def test_all_exports_defined(self):
        """Test that __all__ is defined with expected exports."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert hasattr(smart_execution_strategy, "__all__")
        expected_exports = {
            "ExecutionConfig",
            "LiquidityMetadata",
            "SmartOrderRequest",
            "SmartOrderResult",
        }
        assert set(smart_execution_strategy.__all__) == expected_exports

    def test_all_exports_count(self):
        """Test that __all__ has exactly 4 exports."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert len(smart_execution_strategy.__all__) == 4

    def test_all_is_alphabetically_sorted(self):
        """Test that __all__ is alphabetically sorted for maintainability."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        sorted_all = sorted(smart_execution_strategy.__all__)
        assert smart_execution_strategy.__all__ == sorted_all

    def test_execution_config_importable(self):
        """Test that ExecutionConfig can be imported."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

        assert ExecutionConfig is not None
        assert hasattr(ExecutionConfig, "__dataclass_fields__")

    def test_liquidity_metadata_importable(self):
        """Test that LiquidityMetadata can be imported."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import LiquidityMetadata

        assert LiquidityMetadata is not None
        # TypedDict doesn't have __dict__ but has __annotations__
        assert hasattr(LiquidityMetadata, "__annotations__")

    def test_smart_order_request_importable(self):
        """Test that SmartOrderRequest can be imported."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderRequest

        assert SmartOrderRequest is not None
        assert hasattr(SmartOrderRequest, "__dataclass_fields__")

    def test_smart_order_result_importable(self):
        """Test that SmartOrderResult can be imported."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult

        assert SmartOrderResult is not None
        assert hasattr(SmartOrderResult, "__dataclass_fields__")

    def test_all_classes_importable_together(self):
        """Test that all exported components can be imported together."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import (
            ExecutionConfig,
            LiquidityMetadata,
            SmartOrderRequest,
            SmartOrderResult,
        )

        # Verify they are all valid
        assert ExecutionConfig is not None
        assert LiquidityMetadata is not None
        assert SmartOrderRequest is not None
        assert SmartOrderResult is not None

    def test_execution_config_repeated_import(self):
        """Test that ExecutionConfig repeated imports are identical."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import (
            ExecutionConfig as EC1,
        )
        from the_alchemiser.execution_v2.core.smart_execution_strategy import (
            ExecutionConfig as EC2,
        )

        assert EC1 is EC2

    def test_invalid_attribute_raises_attribute_error(self):
        """Test that accessing invalid attributes raises AttributeError."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        with pytest.raises(AttributeError):
            _ = smart_execution_strategy.NonExistentClass

    def test_module_is_a_package(self):
        """Test that smart_execution_strategy is a package (has __path__)."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert hasattr(smart_execution_strategy, "__path__")
        assert smart_execution_strategy.__path__ is not None

    def test_module_has_correct_name(self):
        """Test that module has correct __name__."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert (
            smart_execution_strategy.__name__
            == "the_alchemiser.execution_v2.core.smart_execution_strategy"
        )

    def test_module_file_location(self):
        """Test that module __file__ points to correct location."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert smart_execution_strategy.__file__ is not None
        assert "__init__.py" in smart_execution_strategy.__file__
        assert "smart_execution_strategy" in smart_execution_strategy.__file__

    def test_all_exports_are_actually_exported(self):
        """Test that all items in __all__ are actually accessible."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        for export_name in smart_execution_strategy.__all__:
            assert hasattr(smart_execution_strategy, export_name), (
                f"{export_name} not found in module"
            )
            exported_item = getattr(smart_execution_strategy, export_name)
            assert exported_item is not None

    def test_no_unintended_exports(self):
        """Test that module doesn't export unintended symbols."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        # These should not be exported
        internal_symbols = ["models", "strategy"]

        for symbol in internal_symbols:
            # Symbol may exist but should not be in __all__
            if hasattr(smart_execution_strategy, symbol):
                assert symbol not in smart_execution_strategy.__all__, (
                    f"{symbol} should not be in __all__"
                )

    def test_execution_config_has_decimal_fields(self):
        """Test that ExecutionConfig uses Decimal for monetary/percentage values."""
        from decimal import Decimal

        from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

        config = ExecutionConfig()

        # Verify key fields use Decimal
        assert isinstance(config.max_spread_percent, Decimal)
        assert isinstance(config.repeg_threshold_percent, Decimal)
        assert isinstance(config.min_bid_ask_size, Decimal)

    def test_smart_order_request_has_required_fields(self):
        """Test that SmartOrderRequest has required fields."""
        from decimal import Decimal

        from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderRequest

        # Create instance with required fields
        request = SmartOrderRequest(
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test-123",
        )

        assert request.symbol == "AAPL"
        assert request.side == "BUY"
        assert request.quantity == Decimal("10")
        assert request.correlation_id == "test-123"
        assert request.urgency == "NORMAL"  # default
        assert request.is_complete_exit is False  # default

    def test_smart_order_result_success_case(self):
        """Test SmartOrderResult can represent successful execution."""
        from decimal import Decimal

        from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult

        result = SmartOrderResult(success=True, order_id="order-123", final_price=Decimal("150.50"))

        assert result.success is True
        assert result.order_id == "order-123"
        assert result.final_price == Decimal("150.50")

    def test_smart_order_result_failure_case(self):
        """Test SmartOrderResult can represent failed execution."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult

        result = SmartOrderResult(success=False, error_message="Liquidity too low")

        assert result.success is False
        assert result.error_message == "Liquidity too low"
        assert result.order_id is None

    def test_liquidity_metadata_structure(self):
        """Test that LiquidityMetadata is a TypedDict with expected fields."""
        from the_alchemiser.execution_v2.core.smart_execution_strategy import LiquidityMetadata

        # TypedDict should have __annotations__
        assert hasattr(LiquidityMetadata, "__annotations__")

        # Check for key fields
        annotations = LiquidityMetadata.__annotations__
        assert "liquidity_score" in annotations
        assert "volume_imbalance" in annotations
        assert "confidence" in annotations
        assert "bid_volume" in annotations
        assert "ask_volume" in annotations

    def test_smart_execution_strategy_not_exported(self):
        """Test that SmartExecutionStrategy is no longer exported (replaced by unified service)."""
        from the_alchemiser.execution_v2.core import smart_execution_strategy

        assert "SmartExecutionStrategy" not in smart_execution_strategy.__all__
