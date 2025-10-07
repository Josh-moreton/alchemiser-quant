#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for TickSizeService.

Tests tick size calculation for various price ranges and edge cases,
ensuring correctness of limit price calculations in execution flow.
"""

from __future__ import annotations

import math
import pytest
from decimal import Decimal, InvalidOperation
from hypothesis import given, strategies as st, assume

from the_alchemiser.shared.services.tick_size_service import (
    TickSizeService,
    DynamicTickSizeService,
)


class TestTickSizeService:
    """Test cases for TickSizeService."""

    @pytest.mark.unit
    def test_tick_size_for_regular_stock(self):
        """Test tick size for regular stock prices (>= $1.00)."""
        service = TickSizeService()
        tick_size = service.get_tick_size("AAPL", Decimal("150.00"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_tick_size_for_sub_dollar_stock(self):
        """Test tick size for sub-dollar stock prices (< $1.00)."""
        service = TickSizeService()
        tick_size = service.get_tick_size("PENNY", Decimal("0.50"))
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit
    def test_tick_size_at_one_dollar_boundary(self):
        """Test tick size exactly at $1.00 boundary."""
        service = TickSizeService()
        # At exactly $1.00, should use penny increment
        tick_size = service.get_tick_size("TEST", Decimal("1.00"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_tick_size_just_below_one_dollar(self):
        """Test tick size just below $1.00 boundary."""
        service = TickSizeService()
        # At $0.9999, should use sub-dollar increment
        tick_size = service.get_tick_size("TEST", Decimal("0.9999"))
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit
    def test_tick_size_just_above_one_dollar(self):
        """Test tick size just above $1.00 boundary."""
        service = TickSizeService()
        # At $1.01, should use penny increment
        tick_size = service.get_tick_size("TEST", Decimal("1.01"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_tick_size_for_high_price_stock(self):
        """Test tick size for high price stock."""
        service = TickSizeService()
        # Even at $1000+, still uses penny increment
        tick_size = service.get_tick_size("BRK.A", Decimal("500000.00"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_tick_size_for_very_low_price(self):
        """Test tick size for very low price stock."""
        service = TickSizeService()
        # Very low prices use sub-dollar increment
        tick_size = service.get_tick_size("MICRO", Decimal("0.0001"))
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit
    def test_tick_size_return_type_is_decimal(self):
        """Test that returned tick size is always a Decimal."""
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", Decimal("100.00"))
        assert isinstance(tick_size, Decimal)

    @pytest.mark.unit
    def test_tick_size_is_positive(self):
        """Test that returned tick size is always positive."""
        service = TickSizeService()
        tick_size_high = service.get_tick_size("TEST", Decimal("100.00"))
        tick_size_low = service.get_tick_size("TEST", Decimal("0.50"))
        assert tick_size_high > Decimal("0")
        assert tick_size_low > Decimal("0")

    @pytest.mark.unit
    def test_symbol_parameter_unused_but_required(self):
        """Test that symbol parameter is required but currently unused."""
        service = TickSizeService()
        # Different symbols should give same result for same price
        tick_size_aapl = service.get_tick_size("AAPL", Decimal("100.00"))
        tick_size_tsla = service.get_tick_size("TSLA", Decimal("100.00"))
        tick_size_any = service.get_tick_size("ANY_SYMBOL", Decimal("100.00"))
        assert tick_size_aapl == tick_size_tsla == tick_size_any

    @pytest.mark.unit
    def test_dynamic_tick_size_service_alias(self):
        """Test that DynamicTickSizeService is an alias for TickSizeService."""
        assert DynamicTickSizeService is TickSizeService
        
        # Should work identically
        service1 = TickSizeService()
        service2 = DynamicTickSizeService()
        
        tick1 = service1.get_tick_size("TEST", Decimal("100.00"))
        tick2 = service2.get_tick_size("TEST", Decimal("100.00"))
        assert tick1 == tick2

    @pytest.mark.unit
    def test_tick_size_deterministic(self):
        """Test that tick size calculation is deterministic."""
        service = TickSizeService()
        price = Decimal("123.45")
        
        # Call multiple times, should always get same result
        results = [service.get_tick_size("TEST", price) for _ in range(10)]
        assert all(r == results[0] for r in results)

    @pytest.mark.unit
    def test_tick_size_with_high_precision_price(self):
        """Test tick size with high precision price input."""
        service = TickSizeService()
        # Price with many decimal places
        tick_size = service.get_tick_size("TEST", Decimal("123.456789012345"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_tick_size_preserves_decimal_precision(self):
        """Test that returned Decimal maintains proper precision."""
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", Decimal("100.00"))
        
        # Check Decimal properties
        assert tick_size.as_tuple().exponent == -2  # 0.01 has exponent -2
        
        tick_size_sub = service.get_tick_size("TEST", Decimal("0.50"))
        assert tick_size_sub.as_tuple().exponent == -4  # 0.0001 has exponent -4


class TestTickSizeServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_zero_price(self):
        """Test behavior with zero price.
        
        Note: Current implementation doesn't validate, but zero price
        would use sub-dollar tick size (< 1.00 condition).
        """
        service = TickSizeService()
        # Zero is less than 1.00, so should return sub-dollar tick
        tick_size = service.get_tick_size("TEST", Decimal("0"))
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit 
    def test_negative_price(self):
        """Test behavior with negative price.
        
        Note: Current implementation doesn't validate, but negative price
        would use sub-dollar tick size (< 1.00 condition).
        """
        service = TickSizeService()
        # Negative is less than 1.00, so should return sub-dollar tick
        tick_size = service.get_tick_size("TEST", Decimal("-10.00"))
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit
    def test_very_large_price(self):
        """Test behavior with very large price."""
        service = TickSizeService()
        # Even extremely large prices use penny increment
        tick_size = service.get_tick_size("TEST", Decimal("999999999.99"))
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_price_with_many_decimal_places(self):
        """Test price with excessive decimal precision."""
        service = TickSizeService()
        # Should handle arbitrary precision without error
        tick_size = service.get_tick_size(
            "TEST", 
            Decimal("100.123456789012345678901234567890")
        )
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    def test_empty_symbol_string(self):
        """Test with empty symbol string (parameter is unused)."""
        service = TickSizeService()
        # Empty string should work fine since symbol is unused
        tick_size = service.get_tick_size("", Decimal("100.00"))
        assert tick_size == Decimal("0.01")


# Property-based tests using Hypothesis
class TestTickSizeServiceProperties:
    """Property-based tests for TickSizeService."""

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("0.0001"),
            max_value=Decimal("100000.00"),
            places=4,
        )
    )
    def test_tick_size_always_positive(self, price: Decimal):
        """Property: Tick size should always be positive."""
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", price)
        assert tick_size > Decimal("0")

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("0.0001"),
            max_value=Decimal("100000.00"),
            places=4,
        )
    )
    def test_tick_size_returns_decimal(self, price: Decimal):
        """Property: Tick size should always return a Decimal."""
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", price)
        assert isinstance(tick_size, Decimal)

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("1.00"),
            max_value=Decimal("10000.00"),
            places=2,
        )
    )
    def test_prices_above_dollar_use_penny_tick(self, price: Decimal):
        """Property: Prices >= $1.00 should use penny tick size."""
        assume(price >= Decimal("1.00"))
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", price)
        assert tick_size == Decimal("0.01")

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("0.0001"),
            max_value=Decimal("0.9999"),
            places=4,
        )
    )
    def test_prices_below_dollar_use_sub_penny_tick(self, price: Decimal):
        """Property: Prices < $1.00 should use sub-penny tick size."""
        assume(price < Decimal("1.00") and price > Decimal("0"))
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", price)
        assert tick_size == Decimal("0.0001")

    @pytest.mark.unit
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters()),
        price=st.decimals(
            min_value=Decimal("1.00"),
            max_value=Decimal("1000.00"),
            places=2,
        ),
    )
    def test_symbol_does_not_affect_result(self, symbol: str, price: Decimal):
        """Property: Different symbols should give same tick size for same price."""
        service = TickSizeService()
        tick_size1 = service.get_tick_size(symbol, price)
        tick_size2 = service.get_tick_size("DIFFERENT", price)
        assert tick_size1 == tick_size2

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("0.0001"),
            max_value=Decimal("10000.00"),
            places=4,
        )
    )
    def test_tick_size_is_deterministic(self, price: Decimal):
        """Property: Same price should always return same tick size."""
        service = TickSizeService()
        tick_size1 = service.get_tick_size("TEST", price)
        tick_size2 = service.get_tick_size("TEST", price)
        tick_size3 = service.get_tick_size("TEST", price)
        assert tick_size1 == tick_size2 == tick_size3

    @pytest.mark.unit
    @given(
        price=st.decimals(
            min_value=Decimal("0.0001"),
            max_value=Decimal("10000.00"),
            places=4,
        )
    )
    def test_tick_size_in_valid_set(self, price: Decimal):
        """Property: Tick size should be one of known valid values."""
        service = TickSizeService()
        tick_size = service.get_tick_size("TEST", price)
        valid_tick_sizes = {Decimal("0.01"), Decimal("0.0001")}
        assert tick_size in valid_tick_sizes


class TestTickSizeServiceIntegration:
    """Integration tests with trading_math module."""

    @pytest.mark.unit
    def test_compatible_with_tick_size_provider_protocol(self):
        """Test that TickSizeService implements TickSizeProvider protocol."""
        from the_alchemiser.shared.math.trading_math import TickSizeProvider
        
        service = TickSizeService()
        
        # Should have the required method
        assert hasattr(service, "get_tick_size")
        assert callable(service.get_tick_size)
        
        # Should work as a TickSizeProvider
        tick_size = service.get_tick_size("TEST", Decimal("100.00"))
        assert isinstance(tick_size, Decimal)

    @pytest.mark.unit
    def test_usage_in_calculate_dynamic_limit_price_with_symbol(self):
        """Test integration with calculate_dynamic_limit_price_with_symbol."""
        from the_alchemiser.shared.math.trading_math import (
            calculate_dynamic_limit_price_with_symbol
        )
        
        service = TickSizeService()
        
        # Use service as tick_size_provider
        price = calculate_dynamic_limit_price_with_symbol(
            side_is_buy=True,
            bid=100.00,
            ask=100.10,
            symbol="AAPL",
            step=0,
            tick_size_provider=service,
        )
        
        # Should return a float price
        assert isinstance(price, float)
        assert price > 0


class TestTickSizeServiceDocumentation:
    """Tests to validate documentation and docstrings."""

    @pytest.mark.unit
    def test_class_has_docstring(self):
        """Test that TickSizeService has a docstring."""
        assert TickSizeService.__doc__ is not None
        assert len(TickSizeService.__doc__) > 0

    @pytest.mark.unit
    def test_method_has_docstring(self):
        """Test that get_tick_size method has a docstring."""
        assert TickSizeService.get_tick_size.__doc__ is not None
        assert len(TickSizeService.get_tick_size.__doc__) > 0

    @pytest.mark.unit
    def test_docstring_documents_parameters(self):
        """Test that docstring documents parameters."""
        docstring = TickSizeService.get_tick_size.__doc__
        assert "Args:" in docstring or "args:" in docstring.lower()
        assert "symbol" in docstring.lower()
        assert "price" in docstring.lower()

    @pytest.mark.unit
    def test_docstring_documents_return_value(self):
        """Test that docstring documents return value."""
        docstring = TickSizeService.get_tick_size.__doc__
        assert "Returns:" in docstring or "returns:" in docstring.lower()
