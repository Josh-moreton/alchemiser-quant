"""Business Unit: shared | Status: current.

Test suite for Symbol value object.

Comprehensive tests for symbol validation, normalization, and edge cases.
"""

from __future__ import annotations

import pytest

from the_alchemiser.shared.value_objects.symbol import Symbol


class TestSymbol:
    """Test Symbol value object."""

    def test_symbol_creation_valid_uppercase(self):
        """Test creating symbol with valid uppercase string."""
        symbol = Symbol("AAPL")
        assert symbol.value == "AAPL"
        assert str(symbol) == "AAPL"

    def test_symbol_creation_valid_lowercase(self):
        """Test creating symbol with valid lowercase string (normalized to uppercase)."""
        symbol = Symbol("aapl")
        assert symbol.value == "AAPL"
        assert str(symbol) == "AAPL"

    def test_symbol_creation_valid_mixed_case(self):
        """Test creating symbol with mixed case (normalized to uppercase)."""
        symbol = Symbol("AaPl")
        assert symbol.value == "AAPL"
        assert str(symbol) == "AAPL"

    def test_symbol_with_dot_valid(self):
        """Test creating symbol with dot (BRK.B is a valid symbol)."""
        symbol = Symbol("BRK.B")
        assert symbol.value == "BRK.B"
        assert str(symbol) == "BRK.B"

    def test_symbol_with_dot_lowercase(self):
        """Test creating symbol with dot in lowercase (normalized to uppercase)."""
        symbol = Symbol("brk.b")
        assert symbol.value == "BRK.B"
        assert str(symbol) == "BRK.B"

    def test_symbol_short_valid(self):
        """Test creating symbol with 1 character."""
        symbol = Symbol("F")
        assert symbol.value == "F"
        assert str(symbol) == "F"

    def test_symbol_two_char_valid(self):
        """Test creating symbol with 2 characters."""
        symbol = Symbol("GM")
        assert symbol.value == "GM"
        assert str(symbol) == "GM"

    def test_symbol_five_char_valid(self):
        """Test creating symbol with 5 characters (at old limit)."""
        symbol = Symbol("GOOGL")
        assert symbol.value == "GOOGL"
        assert str(symbol) == "GOOGL"

    def test_symbol_six_char_valid(self):
        """Test creating symbol with 6 characters (some OTC stocks)."""
        symbol = Symbol("ABCDEF")
        assert symbol.value == "ABCDEF"
        assert str(symbol) == "ABCDEF"

    def test_symbol_crypto_suffix_valid(self):
        """Test creating symbol with crypto suffix (BTCUSD)."""
        symbol = Symbol("BTCUSD")
        assert symbol.value == "BTCUSD"
        assert str(symbol) == "BTCUSD"

    def test_symbol_with_hyphen_valid(self):
        """Test creating symbol with hyphen (some symbols use hyphens)."""
        symbol = Symbol("BRK-B")
        assert symbol.value == "BRK-B"
        assert str(symbol) == "BRK-B"

    def test_symbol_empty_string_invalid(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            Symbol("")

    def test_symbol_whitespace_only_invalid(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            Symbol("   ")

    def test_symbol_with_spaces_invalid(self):
        """Test that symbol with spaces raises ValueError."""
        with pytest.raises(ValueError, match="Symbol must not contain spaces"):
            Symbol("AA PL")

    def test_symbol_with_special_chars_invalid(self):
        """Test that symbol with invalid special characters raises ValueError."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol("AAPL@")

    def test_symbol_with_underscore_invalid(self):
        """Test that symbol with underscore raises ValueError."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol("AAPL_TEST")

    def test_symbol_with_slash_invalid(self):
        """Test that symbol with slash raises ValueError."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol("AAPL/USD")

    def test_symbol_too_long_invalid(self):
        """Test that symbol exceeding max length raises ValueError."""
        with pytest.raises(ValueError, match="Symbol cannot exceed 10 characters"):
            Symbol("ABCDEFGHIJK")

    def test_symbol_immutability(self):
        """Test that Symbol is immutable (frozen dataclass)."""
        symbol = Symbol("AAPL")
        with pytest.raises(AttributeError):
            symbol.value = "MSFT"  # type: ignore

    def test_symbol_equality(self):
        """Test that symbols with same value are equal."""
        symbol1 = Symbol("AAPL")
        symbol2 = Symbol("aapl")  # Normalized to AAPL
        assert symbol1 == symbol2
        assert hash(symbol1) == hash(symbol2)

    def test_symbol_inequality(self):
        """Test that symbols with different values are not equal."""
        symbol1 = Symbol("AAPL")
        symbol2 = Symbol("MSFT")
        assert symbol1 != symbol2

    def test_symbol_str_method(self):
        """Test __str__ method returns the value."""
        symbol = Symbol("TQQQ")
        assert str(symbol) == "TQQQ"
        assert f"{symbol}" == "TQQQ"

    def test_symbol_repr_method(self):
        """Test __repr__ method for debugging."""
        symbol = Symbol("TQQQ")
        # Dataclass provides __repr__ automatically
        assert "Symbol" in repr(symbol)
        assert "TQQQ" in repr(symbol)

    def test_symbol_with_numbers_valid(self):
        """Test symbol with numbers (valid for some instruments)."""
        symbol = Symbol("ES1")
        assert symbol.value == "ES1"

    def test_symbol_all_numbers_valid(self):
        """Test symbol with all numbers (futures contracts)."""
        symbol = Symbol("123")
        assert symbol.value == "123"

    def test_symbol_edge_case_single_dot_invalid(self):
        """Test that single dot is invalid."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            Symbol(".")

    def test_symbol_edge_case_multiple_dots_invalid(self):
        """Test that symbol with multiple dots is invalid."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol("A..B")

    def test_symbol_edge_case_leading_dot_invalid(self):
        """Test that symbol with leading dot is invalid."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol(".AAPL")

    def test_symbol_edge_case_trailing_dot_invalid(self):
        """Test that symbol with trailing dot is invalid."""
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            Symbol("AAPL.")

    def test_symbol_leading_whitespace_trimmed(self):
        """Test that leading whitespace is trimmed."""
        symbol = Symbol("  AAPL")
        assert symbol.value == "AAPL"

    def test_symbol_trailing_whitespace_trimmed(self):
        """Test that trailing whitespace is trimmed."""
        symbol = Symbol("AAPL  ")
        assert symbol.value == "AAPL"

    def test_symbol_both_whitespace_trimmed(self):
        """Test that both leading and trailing whitespace are trimmed."""
        symbol = Symbol("  AAPL  ")
        assert symbol.value == "AAPL"


class TestSymbolEdgeCases:
    """Test Symbol edge cases and boundary conditions."""

    def test_symbol_max_length_boundary(self):
        """Test symbol at maximum allowed length (10 chars)."""
        symbol = Symbol("ABCDEFGHIJ")  # 10 characters
        assert symbol.value == "ABCDEFGHIJ"
        assert len(symbol.value) == 10

    def test_symbol_min_length_boundary(self):
        """Test symbol at minimum allowed length (1 char)."""
        symbol = Symbol("A")
        assert symbol.value == "A"
        assert len(symbol.value) == 1

    def test_symbol_common_etfs(self):
        """Test common ETF symbols."""
        etf_symbols = ["SPY", "QQQ", "IWM", "TQQQ", "SOXL", "TECL"]
        for sym in etf_symbols:
            symbol = Symbol(sym)
            assert symbol.value == sym.upper()

    def test_symbol_common_stocks(self):
        """Test common stock symbols."""
        stock_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        for sym in stock_symbols:
            symbol = Symbol(sym)
            assert symbol.value == sym.upper()

    def test_symbol_crypto_symbols(self):
        """Test cryptocurrency symbols."""
        crypto_symbols = ["BTCUSD", "ETHUSD"]
        for sym in crypto_symbols:
            symbol = Symbol(sym)
            assert symbol.value == sym.upper()


class TestSymbolBusinessRules:
    """Test Symbol business rules and real-world scenarios."""

    def test_symbol_berkshire_hathaway_class_b(self):
        """Test BRK.B symbol (Berkshire Hathaway Class B) from test_trading_business_rules.py."""
        symbol = Symbol("BRK.B")
        assert symbol.value == "BRK.B"

    def test_symbol_berkshire_hathaway_class_a(self):
        """Test BRK.A symbol (Berkshire Hathaway Class A)."""
        symbol = Symbol("BRK.A")
        assert symbol.value == "BRK.A"

    def test_symbol_normalization_matches_business_rules(self):
        """Test symbol normalization matches test_trading_business_rules.py expectations."""
        test_cases = [
            ("aapl", "AAPL"),
            ("msft", "MSFT"),
            ("googl", "GOOGL"),
            ("BRK.B", "BRK.B"),
        ]
        
        for input_sym, expected_sym in test_cases:
            symbol = Symbol(input_sym)
            assert symbol.value == expected_sym
