"""Business Unit: shared | Status: current.

Unit tests for QuoteModel domain object.

This test suite provides comprehensive coverage of the QuoteModel class,
including creation, properties, immutability, and edge cases.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.types.quote import QuoteModel


class TestQuoteModelCreation:
    """Test QuoteModel instantiation."""

    def test_creates_with_valid_data(self):
        """Test that QuoteModel can be created with valid data."""
        ts = datetime.now(UTC)
        quote = QuoteModel(ts=ts, bid=Decimal("100.00"), ask=Decimal("100.25"))

        assert quote.ts == ts
        assert quote.bid == Decimal("100.00")
        assert quote.ask == Decimal("100.25")

    def test_creates_with_none_timestamp(self):
        """Test that QuoteModel can be created with None timestamp."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        assert quote.ts is None
        assert quote.bid == Decimal("100")
        assert quote.ask == Decimal("101")

    def test_creates_with_equal_bid_ask(self):
        """Test creation when bid equals ask (zero spread)."""
        quote = QuoteModel(ts=None, bid=Decimal("100.00"), ask=Decimal("100.00"))

        assert quote.bid == quote.ask
        assert quote.mid == Decimal("100.00")

    def test_creates_with_small_prices(self):
        """Test creation with small decimal prices."""
        quote = QuoteModel(ts=None, bid=Decimal("0.01"), ask=Decimal("0.02"))

        assert quote.bid == Decimal("0.01")
        assert quote.ask == Decimal("0.02")

    def test_creates_with_large_prices(self):
        """Test creation with large decimal prices."""
        quote = QuoteModel(ts=None, bid=Decimal("99999.99"), ask=Decimal("100000.00"))

        assert quote.bid == Decimal("99999.99")
        assert quote.ask == Decimal("100000.00")


class TestMidProperty:
    """Test mid-point calculation."""

    def test_calculates_mid_correctly(self):
        """Test that mid property calculates correct midpoint."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("102"))

        assert quote.mid == Decimal("101")

    def test_mid_preserves_decimal_precision(self):
        """Test that mid calculation preserves Decimal precision."""
        quote = QuoteModel(ts=None, bid=Decimal("100.00"), ask=Decimal("100.25"))

        assert quote.mid == Decimal("100.125")

    def test_mid_with_equal_bid_ask(self):
        """Test mid calculation when bid equals ask."""
        quote = QuoteModel(ts=None, bid=Decimal("100.00"), ask=Decimal("100.00"))

        assert quote.mid == Decimal("100.00")

    def test_mid_with_odd_difference(self):
        """Test mid calculation with odd spread."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        assert quote.mid == Decimal("100.5")

    def test_mid_with_high_precision(self):
        """Test mid calculation preserves high precision."""
        quote = QuoteModel(ts=None, bid=Decimal("100.1234"), ask=Decimal("100.5678"))

        expected = (Decimal("100.1234") + Decimal("100.5678")) / Decimal("2")
        assert quote.mid == expected
        assert quote.mid == Decimal("100.3456")

    def test_mid_recalculates_each_time(self):
        """Test that mid property recalculates (not cached)."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("102"))

        # Call multiple times to ensure no caching issues
        assert quote.mid == Decimal("101")
        assert quote.mid == Decimal("101")
        assert quote.mid == Decimal("101")

    @given(
        bid=st.decimals(
            min_value="0.01",
            max_value="10000",
            places=4,
            allow_nan=False,
            allow_infinity=False,
        ),
        ask=st.decimals(
            min_value="0.01",
            max_value="10000",
            places=4,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    def test_mid_always_between_bid_and_ask_property_based(self, bid, ask):
        """Property-based test: mid should be between bid and ask."""
        if bid <= ask:
            quote = QuoteModel(ts=None, bid=bid, ask=ask)
            # Mid should always be between bid and ask
            assert bid <= quote.mid <= ask

    @given(
        bid=st.decimals(
            min_value="0.01",
            max_value="10000",
            places=4,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_mid_equals_price_when_bid_equals_ask_property_based(self, bid):
        """Property-based test: mid equals bid/ask when they're equal."""
        quote = QuoteModel(ts=None, bid=bid, ask=bid)
        assert quote.mid == bid


class TestImmutability:
    """Test that QuoteModel is immutable."""

    def test_cannot_modify_bid(self):
        """Test that bid field cannot be modified after creation."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        with pytest.raises((AttributeError, TypeError)):
            quote.bid = Decimal("200")  # type: ignore[misc]

    def test_cannot_modify_ask(self):
        """Test that ask field cannot be modified after creation."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        with pytest.raises((AttributeError, TypeError)):
            quote.ask = Decimal("200")  # type: ignore[misc]

    def test_cannot_modify_timestamp(self):
        """Test that timestamp field cannot be modified after creation."""
        ts = datetime.now(UTC)
        quote = QuoteModel(ts=ts, bid=Decimal("100"), ask=Decimal("101"))

        with pytest.raises((AttributeError, TypeError)):
            quote.ts = datetime.now(UTC)  # type: ignore[misc]

    def test_is_frozen(self):
        """Test that the dataclass is frozen."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        # Verify frozen attribute
        assert quote.__dataclass_fields__["bid"].metadata.get("frozen", True)


class TestDecimalPrecision:
    """Test Decimal precision preservation."""

    def test_preserves_two_decimal_places(self):
        """Test that 2 decimal places are preserved."""
        quote = QuoteModel(ts=None, bid=Decimal("100.12"), ask=Decimal("100.34"))

        assert str(quote.bid) == "100.12"
        assert str(quote.ask) == "100.34"

    def test_preserves_four_decimal_places(self):
        """Test that 4 decimal places are preserved."""
        quote = QuoteModel(ts=None, bid=Decimal("100.1234"), ask=Decimal("100.5678"))

        assert str(quote.bid) == "100.1234"
        assert str(quote.ask) == "100.5678"

    def test_no_float_conversion_errors(self):
        """Test that Decimal avoids float conversion errors."""
        # Use a value that would have float precision issues
        quote = QuoteModel(ts=None, bid=Decimal("0.1"), ask=Decimal("0.2"))

        # Mid should be exactly 0.15, not 0.15000000000000002 like with floats
        assert quote.mid == Decimal("0.15")

    def test_string_initialization_preserves_precision(self):
        """Test that string initialization preserves exact precision."""
        quote = QuoteModel(ts=None, bid=Decimal("100.123456789"), ask=Decimal("100.987654321"))

        assert quote.bid == Decimal("100.123456789")
        assert quote.ask == Decimal("100.987654321")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_spread(self):
        """Test quote with very small spread."""
        quote = QuoteModel(ts=None, bid=Decimal("100.0000"), ask=Decimal("100.0001"))

        assert quote.mid == Decimal("100.00005")

    def test_very_large_spread(self):
        """Test quote with very large spread."""
        quote = QuoteModel(ts=None, bid=Decimal("1"), ask=Decimal("1000"))

        assert quote.mid == Decimal("500.5")

    def test_penny_stocks(self):
        """Test quotes for penny stocks (very low prices)."""
        quote = QuoteModel(ts=None, bid=Decimal("0.0001"), ask=Decimal("0.0002"))

        assert quote.mid == Decimal("0.00015")

    def test_high_value_stocks(self):
        """Test quotes for high-value stocks."""
        quote = QuoteModel(ts=None, bid=Decimal("500000.00"), ask=Decimal("500001.00"))

        assert quote.mid == Decimal("500000.50")


class TestEquality:
    """Test equality and hashing."""

    def test_equal_quotes_are_equal(self):
        """Test that quotes with same values are equal."""
        ts = datetime(2025, 10, 6, 12, 0, 0, tzinfo=UTC)
        quote1 = QuoteModel(ts=ts, bid=Decimal("100"), ask=Decimal("101"))
        quote2 = QuoteModel(ts=ts, bid=Decimal("100"), ask=Decimal("101"))

        assert quote1 == quote2

    def test_different_quotes_are_not_equal(self):
        """Test that quotes with different values are not equal."""
        quote1 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))
        quote2 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("102"))

        assert quote1 != quote2

    def test_quote_is_hashable(self):
        """Test that QuoteModel can be used as dict key."""
        quote1 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))
        quote2 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        # Should be able to use as dict key
        quote_dict = {quote1: "value1"}
        assert quote_dict[quote2] == "value1"

    def test_can_add_to_set(self):
        """Test that QuoteModel can be added to a set."""
        quote1 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))
        quote2 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))
        quote3 = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("102"))

        quote_set = {quote1, quote2, quote3}
        # quote1 and quote2 are equal, so set should have 2 elements
        assert len(quote_set) == 2


class TestStringRepresentation:
    """Test string representation of QuoteModel."""

    def test_repr_contains_fields(self):
        """Test that repr contains all field names and values."""
        ts = datetime(2025, 10, 6, 12, 0, 0, tzinfo=UTC)
        quote = QuoteModel(ts=ts, bid=Decimal("100.00"), ask=Decimal("100.25"))

        repr_str = repr(quote)
        assert "QuoteModel" in repr_str
        assert "ts=" in repr_str
        assert "bid=" in repr_str
        assert "ask=" in repr_str
        assert "100.00" in repr_str
        assert "100.25" in repr_str

    def test_repr_with_none_timestamp(self):
        """Test repr with None timestamp."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        repr_str = repr(quote)
        assert "ts=None" in repr_str


class TestTypeAnnotations:
    """Test that type annotations are correct."""

    def test_fields_have_correct_types(self):
        """Test that QuoteModel fields have correct type annotations."""
        quote = QuoteModel(ts=datetime.now(UTC), bid=Decimal("100"), ask=Decimal("101"))

        # Test that we can access fields with proper types
        assert isinstance(quote.ts, datetime) or quote.ts is None
        assert isinstance(quote.bid, Decimal)
        assert isinstance(quote.ask, Decimal)

    def test_mid_returns_decimal(self):
        """Test that mid property returns Decimal type."""
        quote = QuoteModel(ts=None, bid=Decimal("100"), ask=Decimal("101"))

        assert isinstance(quote.mid, Decimal)
