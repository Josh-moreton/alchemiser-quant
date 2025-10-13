"""Business Unit: shared | Status: current.

Test suite for symbols_config module.

Comprehensive tests for symbol classification, ETF detection, and symbol universe management.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.config.symbols_config import (
    KNOWN_CRYPTO,
    KNOWN_ETFS,
    AssetType,
    add_etf_symbol,
    classify_symbol,
    get_etf_symbols,
    get_symbol_universe,
    is_etf,
)


class TestClassifySymbol:
    """Test classify_symbol function."""

    def test_classify_known_etf_spy(self):
        """Test that SPY is classified as ETF."""
        result = classify_symbol("SPY")
        assert result == "ETF"

    def test_classify_known_etf_qqq(self):
        """Test that QQQ is classified as ETF."""
        result = classify_symbol("QQQ")
        assert result == "ETF"

    def test_classify_known_etf_tqqq(self):
        """Test that TQQQ is classified as ETF."""
        result = classify_symbol("TQQQ")
        assert result == "ETF"

    def test_classify_known_etf_tecl(self):
        """Test that TECL is classified as ETF."""
        result = classify_symbol("TECL")
        assert result == "ETF"

    def test_classify_known_etf_soxl(self):
        """Test that SOXL is classified as ETF."""
        result = classify_symbol("SOXL")
        assert result == "ETF"

    def test_classify_known_crypto_btc(self):
        """Test that BTC is classified as CRYPTO."""
        result = classify_symbol("BTC")
        assert result == "CRYPTO"

    def test_classify_known_crypto_eth(self):
        """Test that ETH is classified as CRYPTO."""
        result = classify_symbol("ETH")
        assert result == "CRYPTO"

    def test_classify_known_crypto_btcusd(self):
        """Test that BTCUSD is classified as CRYPTO."""
        result = classify_symbol("BTCUSD")
        assert result == "CRYPTO"

    def test_classify_known_crypto_ethusd(self):
        """Test that ETHUSD is classified as CRYPTO."""
        result = classify_symbol("ETHUSD")
        assert result == "CRYPTO"

    def test_classify_stock_aapl(self):
        """Test that AAPL is classified as STOCK."""
        result = classify_symbol("AAPL")
        assert result == "STOCK"

    def test_classify_stock_msft(self):
        """Test that MSFT is classified as STOCK."""
        result = classify_symbol("MSFT")
        assert result == "STOCK"

    def test_classify_stock_googl(self):
        """Test that GOOGL is classified as STOCK."""
        result = classify_symbol("GOOGL")
        assert result == "STOCK"

    def test_classify_case_insensitive_lowercase(self):
        """Test that lowercase symbol is normalized and classified."""
        result = classify_symbol("spy")
        assert result == "ETF"

    def test_classify_case_insensitive_mixed(self):
        """Test that mixed case symbol is normalized and classified."""
        result = classify_symbol("SpY")
        assert result == "ETF"

    def test_classify_with_leading_whitespace(self):
        """Test that leading whitespace is stripped."""
        result = classify_symbol("  SPY")
        assert result == "ETF"

    def test_classify_with_trailing_whitespace(self):
        """Test that trailing whitespace is stripped."""
        result = classify_symbol("SPY  ")
        assert result == "ETF"

    def test_classify_with_both_whitespace(self):
        """Test that leading and trailing whitespace is stripped."""
        result = classify_symbol("  SPY  ")
        assert result == "ETF"

    def test_classify_option_ending_with_c(self):
        """Test option detection with C suffix.
        
        Note: Real option symbols like "AAPL240315C00150000" exceed the 10-character
        limit and will raise ValueError during Symbol validation. This is expected
        since the Symbol value object enforces a maximum length of 10 characters.
        
        The simplified option detection logic (checking for C/P suffix) is documented
        as having limitations in the module docstring.
        """
        with pytest.raises(ValueError, match="Symbol cannot exceed 10 characters"):
            classify_symbol("AAPL240315C00150000")

    def test_classify_option_ending_with_p(self):
        """Test option detection with P suffix.
        
        Note: Real option symbols like "AAPL240315P00150000" exceed the 10-character
        limit and will raise ValueError during Symbol validation. This is expected
        since the Symbol value object enforces a maximum length of 10 characters.
        
        The simplified option detection logic (checking for C/P suffix) is documented
        as having limitations in the module docstring.
        """
        with pytest.raises(ValueError, match="Symbol cannot exceed 10 characters"):
            classify_symbol("AAPL240315P00150000")

    def test_classify_future_with_numeric_suffix(self):
        """Test that symbol > 5 chars ending with digits is classified as FUTURE.
        
        Note: This is overly simplistic and causes false positives. Real futures
        symbols have specific month/year codes. This is a known issue documented
        in FILE_REVIEW_symbols_config_2025_10_10.md (HIGH-3).
        
        ESH23 is 5 chars (not > 5), so it's classified as STOCK.
        Using a longer example that meets the > 5 chars condition.
        """
        result = classify_symbol("STOCK12")
        assert result == "FUTURE"

    def test_classify_short_symbol_with_digits_not_future(self):
        """Test that short symbol with digits is not classified as FUTURE."""
        result = classify_symbol("ES1")
        assert result == "STOCK"

    def test_classify_unknown_defaults_to_stock(self):
        """Test that unknown symbol defaults to STOCK."""
        result = classify_symbol("UNKNOWN")
        assert result == "STOCK"

    def test_classify_empty_string_returns_stock(self):
        """Test that empty string raises ValueError after Symbol validation.
        
        Previously returned 'STOCK', but now validates input using Symbol value object.
        """
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            classify_symbol("")

    def test_classify_whitespace_only_returns_stock(self):
        """Test that whitespace-only string raises ValueError after Symbol validation.
        
        Previously returned 'STOCK', but now validates input using Symbol value object.
        """
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            classify_symbol("   ")


class TestIsETF:
    """Test is_etf function."""

    def test_is_etf_spy_returns_true(self):
        """Test that SPY is recognized as ETF."""
        assert is_etf("SPY") is True

    def test_is_etf_qqq_returns_true(self):
        """Test that QQQ is recognized as ETF."""
        assert is_etf("QQQ") is True

    def test_is_etf_tqqq_returns_true(self):
        """Test that TQQQ is recognized as ETF."""
        assert is_etf("TQQQ") is True

    def test_is_etf_aapl_returns_false(self):
        """Test that AAPL is not recognized as ETF."""
        assert is_etf("AAPL") is False

    def test_is_etf_btc_returns_false(self):
        """Test that BTC is not recognized as ETF."""
        assert is_etf("BTC") is False

    def test_is_etf_case_insensitive_lowercase(self):
        """Test that lowercase symbol is normalized."""
        assert is_etf("spy") is True

    def test_is_etf_case_insensitive_mixed(self):
        """Test that mixed case symbol is normalized."""
        assert is_etf("SpY") is True

    def test_is_etf_with_leading_whitespace(self):
        """Test that leading whitespace is stripped."""
        assert is_etf("  SPY") is True

    def test_is_etf_with_trailing_whitespace(self):
        """Test that trailing whitespace is stripped."""
        assert is_etf("SPY  ") is True

    def test_is_etf_empty_string_returns_false(self):
        """Test that empty string raises ValueError after Symbol validation."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            is_etf("")

    def test_is_etf_whitespace_only_returns_false(self):
        """Test that whitespace-only string raises ValueError after Symbol validation."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            is_etf("   ")


class TestGetETFSymbols:
    """Test get_etf_symbols function."""

    def test_get_etf_symbols_returns_frozenset(self):
        """Test that function returns a frozenset (immutable)."""
        result = get_etf_symbols()
        assert isinstance(result, frozenset)

    def test_get_etf_symbols_contains_spy(self):
        """Test that returned set contains SPY."""
        result = get_etf_symbols()
        assert "SPY" in result

    def test_get_etf_symbols_contains_qqq(self):
        """Test that returned set contains QQQ."""
        result = get_etf_symbols()
        assert "QQQ" in result

    def test_get_etf_symbols_contains_tqqq(self):
        """Test that returned set contains TQQQ."""
        result = get_etf_symbols()
        assert "TQQQ" in result

    def test_get_etf_symbols_contains_tecl(self):
        """Test that returned set contains TECL."""
        result = get_etf_symbols()
        assert "TECL" in result

    def test_get_etf_symbols_contains_soxl(self):
        """Test that returned set contains SOXL."""
        result = get_etf_symbols()
        assert "SOXL" in result

    def test_get_etf_symbols_not_empty(self):
        """Test that returned set is not empty."""
        result = get_etf_symbols()
        assert len(result) > 0

    def test_get_etf_symbols_returns_same_reference(self):
        """Test that function returns the same immutable frozenset reference."""
        result1 = get_etf_symbols()
        result2 = get_etf_symbols()
        assert result1 == result2
        assert result1 is result2  # Same object since it's immutable

    def test_get_etf_symbols_matches_known_etfs(self):
        """Test that returned set matches KNOWN_ETFS."""
        result = get_etf_symbols()
        assert result == KNOWN_ETFS


class TestGetSymbolUniverse:
    """Test get_symbol_universe function."""

    def test_get_symbol_universe_returns_dict(self):
        """Test that function returns a dictionary."""
        result = get_symbol_universe()
        assert isinstance(result, dict)

    def test_get_symbol_universe_has_etf_key(self):
        """Test that returned dict has 'ETF' key."""
        result = get_symbol_universe()
        assert "ETF" in result

    def test_get_symbol_universe_has_crypto_key(self):
        """Test that returned dict has 'CRYPTO' key."""
        result = get_symbol_universe()
        assert "CRYPTO" in result

    def test_get_symbol_universe_etf_is_frozenset(self):
        """Test that 'ETF' value is a frozenset (immutable)."""
        result = get_symbol_universe()
        assert isinstance(result["ETF"], frozenset)

    def test_get_symbol_universe_crypto_is_frozenset(self):
        """Test that 'CRYPTO' value is a frozenset (immutable)."""
        result = get_symbol_universe()
        assert isinstance(result["CRYPTO"], frozenset)

    def test_get_symbol_universe_etf_contains_spy(self):
        """Test that ETF set contains SPY."""
        result = get_symbol_universe()
        assert "SPY" in result["ETF"]

    def test_get_symbol_universe_crypto_contains_btc(self):
        """Test that CRYPTO set contains BTC."""
        result = get_symbol_universe()
        assert "BTC" in result["CRYPTO"]

    def test_get_symbol_universe_returns_same_references(self):
        """Test that function returns same immutable frozenset references."""
        result1 = get_symbol_universe()
        result2 = get_symbol_universe()
        assert result1 == result2
        assert result1["ETF"] is result2["ETF"]  # Same immutable object
        assert result1["CRYPTO"] is result2["CRYPTO"]  # Same immutable object

    def test_get_symbol_universe_etf_matches_known_etfs(self):
        """Test that ETF set matches KNOWN_ETFS."""
        result = get_symbol_universe()
        assert result["ETF"] == KNOWN_ETFS

    def test_get_symbol_universe_crypto_matches_known_crypto(self):
        """Test that CRYPTO set matches KNOWN_CRYPTO."""
        result = get_symbol_universe()
        assert result["CRYPTO"] == KNOWN_CRYPTO


class TestAssetType:
    """Test AssetType Literal type."""

    def test_asset_type_stock_is_valid(self):
        """Test that 'STOCK' is a valid AssetType."""
        asset_type: AssetType = "STOCK"
        assert asset_type == "STOCK"

    def test_asset_type_etf_is_valid(self):
        """Test that 'ETF' is a valid AssetType."""
        asset_type: AssetType = "ETF"
        assert asset_type == "ETF"

    def test_asset_type_crypto_is_valid(self):
        """Test that 'CRYPTO' is a valid AssetType."""
        asset_type: AssetType = "CRYPTO"
        assert asset_type == "CRYPTO"

    def test_asset_type_option_is_valid(self):
        """Test that 'OPTION' is a valid AssetType."""
        asset_type: AssetType = "OPTION"
        assert asset_type == "OPTION"

    def test_asset_type_future_is_valid(self):
        """Test that 'FUTURE' is a valid AssetType."""
        asset_type: AssetType = "FUTURE"
        assert asset_type == "FUTURE"


class TestAddETFSymbol:
    """Test add_etf_symbol function (deprecated)."""

    def test_add_etf_symbol_raises_not_implemented_error(self):
        """Test that add_etf_symbol raises NotImplementedError.
        
        This function is deprecated to ensure thread-safety and immutability.
        Symbol universes should be loaded from external configuration, not
        modified at runtime.
        """
        with pytest.raises(NotImplementedError, match="Runtime symbol addition is not supported"):
            add_etf_symbol("TEST")

    def test_add_etf_symbol_provides_clear_error_message(self):
        """Test that error message explains why function is deprecated."""
        try:
            add_etf_symbol("TEST")
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError as e:
            error_msg = str(e)
            assert "immutable" in error_msg.lower()
            assert "thread-safety" in error_msg.lower()
            assert "configuration" in error_msg.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_classify_symbol_with_dots(self):
        """Test symbol with dots (like BRK.B)."""
        result = classify_symbol("BRK.B")
        assert result == "STOCK"

    def test_classify_symbol_with_hyphens(self):
        """Test symbol with hyphens (like BRK-B)."""
        result = classify_symbol("BRK-B")
        assert result == "STOCK"

    def test_classify_single_character_symbol(self):
        """Test single character symbol."""
        result = classify_symbol("F")
        assert result == "STOCK"

    def test_classify_two_character_symbol(self):
        """Test two character symbol."""
        result = classify_symbol("GM")
        assert result == "STOCK"

    def test_is_etf_all_known_etfs(self):
        """Test that all KNOWN_ETFS return True."""
        for etf in KNOWN_ETFS:
            assert is_etf(etf) is True, f"Expected {etf} to be recognized as ETF"

    def test_classify_all_known_etfs(self):
        """Test that all KNOWN_ETFS are classified as ETF."""
        for etf in KNOWN_ETFS:
            result = classify_symbol(etf)
            assert result == "ETF", f"Expected {etf} to be classified as ETF, got {result}"

    def test_classify_all_known_crypto(self):
        """Test that all KNOWN_CRYPTO are classified as CRYPTO."""
        for crypto in KNOWN_CRYPTO:
            result = classify_symbol(crypto)
            assert (
                result == "CRYPTO"
            ), f"Expected {crypto} to be classified as CRYPTO, got {result}"


class TestPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(st.text(min_size=1, max_size=10))
    def test_classify_always_returns_valid_asset_type(self, symbol: str):
        """Test that classify_symbol always returns a valid AssetType or raises ValueError.
        
        Since we now use Symbol value object for validation, invalid symbols
        will raise ValueError instead of being classified.
        """
        try:
            result = classify_symbol(symbol)
            assert result in ["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]
        except ValueError:
            # Invalid symbols raise ValueError, which is expected
            pass

    @given(st.text(min_size=1, max_size=10))
    def test_classify_is_idempotent(self, symbol: str):
        """Test that classify_symbol is idempotent for valid symbols."""
        try:
            result1 = classify_symbol(symbol)
            result2 = classify_symbol(symbol)
            assert result1 == result2
        except ValueError:
            # Invalid symbols consistently raise ValueError, which is idempotent
            pass

    @given(st.text(min_size=1, max_size=10))
    def test_is_etf_returns_boolean(self, symbol: str):
        """Test that is_etf always returns a boolean or raises ValueError for invalid symbols."""
        try:
            result = is_etf(symbol)
            assert isinstance(result, bool)
        except ValueError:
            # Invalid symbols raise ValueError, which is expected
            pass

    @given(st.text(min_size=1, max_size=10))
    def test_is_etf_is_idempotent(self, symbol: str):
        """Test that is_etf is idempotent for valid symbols."""
        try:
            result1 = is_etf(symbol)
            result2 = is_etf(symbol)
            assert result1 == result2
        except ValueError:
            # Invalid symbols consistently raise ValueError, which is idempotent
            pass


class TestBusinessRules:
    """Test business rules and real-world scenarios."""

    def test_major_etfs_recognized(self):
        """Test that major ETFs are recognized."""
        major_etfs = ["SPY", "QQQ", "IWM", "TQQQ", "SOXL", "TECL", "XLK", "SMH"]
        for etf in major_etfs:
            assert is_etf(etf), f"Expected {etf} to be recognized as ETF"
            assert classify_symbol(etf) == "ETF", f"Expected {etf} to classify as ETF"

    def test_leveraged_etfs_recognized(self):
        """Test that leveraged ETFs are recognized."""
        leveraged_etfs = ["TECL", "TQQQ", "SOXL"]
        for etf in leveraged_etfs:
            assert is_etf(etf), f"Expected {etf} to be recognized as leveraged ETF"

    def test_sector_etfs_recognized(self):
        """Test that sector ETFs are recognized."""
        sector_etfs = ["XLK", "SMH", "SOXX"]
        for etf in sector_etfs:
            assert is_etf(etf), f"Expected {etf} to be recognized as sector ETF"

    def test_crypto_symbols_recognized(self):
        """Test that crypto symbols are recognized."""
        crypto_symbols = ["BTC", "ETH", "BTCUSD", "ETHUSD"]
        for crypto in crypto_symbols:
            result = classify_symbol(crypto)
            assert (
                result == "CRYPTO"
            ), f"Expected {crypto} to be classified as CRYPTO, got {result}"

    def test_common_stocks_not_etfs(self):
        """Test that common stocks are not recognized as ETFs."""
        stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        for stock in stocks:
            assert not is_etf(stock), f"Expected {stock} to NOT be recognized as ETF"
            assert classify_symbol(stock) == "STOCK", f"Expected {stock} to classify as STOCK"
