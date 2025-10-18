"""Business Unit: shared | Status: current.

Comprehensive test suite for asset_info.py.

Tests cover:
- AssetType enum
- FractionabilityDetector initialization
- Fractionability detection with caching
- Asset type classification
- Notional order decisions
- Whole share conversion
- Cache statistics
- Provider delegation and fallback behavior
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.math.asset_info import (
    AssetType,
    FractionabilityDetector,
    fractionability_detector,
)


class TestAssetTypeEnum:
    """Test AssetType enum values."""

    def test_enum_has_all_expected_values(self):
        """Test that AssetType enum has all expected values."""
        assert hasattr(AssetType, "STOCK")
        assert hasattr(AssetType, "ETF")
        assert hasattr(AssetType, "ETN")
        assert hasattr(AssetType, "LEVERAGED_ETF")
        assert hasattr(AssetType, "CRYPTO")
        assert hasattr(AssetType, "UNKNOWN")

    def test_enum_values_are_correct(self):
        """Test that enum values have correct string representations."""
        assert AssetType.STOCK.value == "stock"
        assert AssetType.ETF.value == "etf"
        assert AssetType.ETN.value == "etn"
        assert AssetType.LEVERAGED_ETF.value == "leveraged_etf"
        assert AssetType.CRYPTO.value == "crypto"
        assert AssetType.UNKNOWN.value == "unknown"

    def test_enum_values_are_unique(self):
        """Test that all enum values are unique."""
        values = [e.value for e in AssetType]
        assert len(values) == len(set(values))

    def test_enum_can_be_accessed_by_value(self):
        """Test that enum can be accessed by value."""
        assert AssetType("stock") == AssetType.STOCK
        assert AssetType("etf") == AssetType.ETF

    def test_enum_comparison(self):
        """Test enum comparison operations."""
        assert AssetType.STOCK == AssetType.STOCK
        assert AssetType.STOCK != AssetType.ETF


class TestFractionabilityDetectorInitialization:
    """Test FractionabilityDetector initialization."""

    def test_init_without_provider(self):
        """Test initialization without provider."""
        detector = FractionabilityDetector()

        assert detector.asset_metadata_provider is None
        assert isinstance(detector._fractionability_cache, dict)
        assert len(detector._fractionability_cache) == 0
        assert isinstance(detector.backup_known_non_fractionable, frozenset)

    def test_init_with_provider(self):
        """Test initialization with provider."""
        mock_provider = Mock()
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        assert detector.asset_metadata_provider is mock_provider
        assert isinstance(detector._fractionability_cache, dict)

    def test_backup_set_is_immutable(self):
        """Test that backup set is immutable (frozenset)."""
        detector = FractionabilityDetector()

        # Verify it's a frozenset
        assert isinstance(detector.backup_known_non_fractionable, frozenset)

        # Verify we can't add to it
        with pytest.raises(AttributeError):
            detector.backup_known_non_fractionable.add("TEST")  # type: ignore

    def test_backup_set_contains_fngu(self):
        """Test that backup set contains known non-fractionable asset."""
        detector = FractionabilityDetector()
        assert "FNGU" in detector.backup_known_non_fractionable


class TestIsFractionableMethod:
    """Test is_fractionable method."""

    def test_provider_returns_true(self):
        """Test when provider confirms asset is fractionable."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.is_fractionable("AAPL")

        assert result is True
        assert "AAPL" in detector._fractionability_cache
        assert detector._fractionability_cache["AAPL"] is True

    def test_provider_returns_false(self):
        """Test when provider confirms asset is not fractionable."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.is_fractionable("FNGU")

        assert result is False
        assert "FNGU" in detector._fractionability_cache
        assert detector._fractionability_cache["FNGU"] is False

    def test_cache_hit_scenario(self):
        """Test that cache is used on subsequent calls."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # First call - should query provider
        result1 = detector.is_fractionable("AAPL")
        # Second call - should use cache
        result2 = detector.is_fractionable("AAPL")

        assert result1 is True
        assert result2 is True
        # Provider should only be called once
        assert mock_provider.is_fractionable.call_count == 1

    def test_cache_bypass_with_use_cache_false(self):
        """Test that cache can be bypassed."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # First call with cache
        detector.is_fractionable("AAPL", use_cache=True)
        # Second call bypassing cache
        detector.is_fractionable("AAPL", use_cache=False)

        # Provider should be called twice
        assert mock_provider.is_fractionable.call_count == 2

    def test_symbol_normalized_to_uppercase(self):
        """Test that symbol is normalized to uppercase."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        detector.is_fractionable("aapl")

        # Should be cached as uppercase
        assert "AAPL" in detector._fractionability_cache
        assert "aapl" not in detector._fractionability_cache

    def test_provider_exception_handled(self):
        """Test that provider exceptions are handled gracefully."""
        mock_provider = Mock()
        mock_provider.is_fractionable.side_effect = Exception("Provider error")
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Should fall back to prediction, not raise exception
        result = detector.is_fractionable("AAPL")

        assert isinstance(result, bool)
        # Should use fallback (True for unknown symbols)
        assert result is True

    def test_fallback_when_no_provider(self):
        """Test fallback behavior when no provider is configured."""
        detector = FractionabilityDetector()

        # Unknown symbol should default to fractionable
        result = detector.is_fractionable("AAPL")
        assert result is True

        # Known non-fractionable should return False
        result = detector.is_fractionable("FNGU")
        assert result is False

    def test_known_non_fractionable_symbol(self):
        """Test that known non-fractionable symbols are handled."""
        detector = FractionabilityDetector()

        result = detector.is_fractionable("FNGU")

        assert result is False

    def test_fallback_result_is_cached(self):
        """Test that fallback results are also cached."""
        detector = FractionabilityDetector()

        # First call uses fallback
        result1 = detector.is_fractionable("TEST")
        # Second call should use cache
        result2 = detector.is_fractionable("TEST")

        assert result1 == result2
        assert "TEST" in detector._fractionability_cache


class TestGetAssetTypeMethod:
    """Test get_asset_type method."""

    def test_stock_classification_default(self):
        """Test that unknown symbols default to STOCK."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.get_asset_type("UNKNOWN")

        assert result == AssetType.STOCK

    def test_etf_classification_spy(self):
        """Test that SPY is classified as ETF."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.get_asset_type("SPY")

        assert result == AssetType.ETF

    def test_etf_classification_qqq(self):
        """Test that QQQ is classified as ETF."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.get_asset_type("QQQ")

        assert result == AssetType.ETF

    def test_etf_classification_vanguard_prefix(self):
        """Test that Vanguard ETFs are classified correctly."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        assert detector.get_asset_type("VTI") == AssetType.ETF
        assert detector.get_asset_type("VOO") == AssetType.ETF

    def test_leveraged_etf_for_non_fractionable(self):
        """Test that non-fractionable assets are classified as LEVERAGED_ETF."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.get_asset_type("TQQQ")

        assert result == AssetType.LEVERAGED_ETF

    def test_symbol_normalization(self):
        """Test that symbol is normalized in get_asset_type."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.get_asset_type("spy")

        assert result == AssetType.ETF

    def test_all_hardcoded_etfs(self):
        """Test all hardcoded ETF symbols."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        etf_symbols = ["SPY", "QQQ", "IWM", "VTI", "VOO", "VEA", "BIL"]
        for symbol in etf_symbols:
            assert detector.get_asset_type(symbol) == AssetType.ETF


class TestShouldUseNotionalOrderMethod:
    """Test should_use_notional_order method."""

    def test_non_fractionable_returns_true(self):
        """Test that non-fractionable assets always use notional orders."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("FNGU", Decimal("10"))

        assert result is True

    def test_fractional_less_than_one_returns_true(self):
        """Test that quantities < 1.0 use notional orders."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("AAPL", Decimal("0.5"))

        assert result is True

    def test_significant_fractional_part_returns_true(self):
        """Test that significant fractional parts (> 0.1) use notional orders."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("AAPL", Decimal("10.5"))

        assert result is True

    def test_whole_shares_returns_false(self):
        """Test that whole share quantities don't use notional orders."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("AAPL", Decimal("10"))

        assert result is False

    def test_small_fractional_part_returns_false(self):
        """Test that small fractional parts (< 0.1) don't use notional orders."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("AAPL", Decimal("10.05"))

        assert result is False

    def test_exactly_one_share(self):
        """Test edge case of exactly 1.0 share."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result = detector.should_use_notional_order("AAPL", Decimal("1.0"))

        assert result is False

    def test_boundary_at_point_one(self):
        """Test boundary at 0.1 fractional part."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Exactly 0.1 should be False (not >0.1)
        result = detector.should_use_notional_order("AAPL", Decimal("10.1"))
        # Just over 0.1 should be True
        assert result is False  # 0.1 is not > 0.1

        result = detector.should_use_notional_order("AAPL", Decimal("10.11"))
        assert result is True

    def test_accepts_float_input(self):
        """Test that method accepts float input and converts to Decimal."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Should not raise exception with float input
        result = detector.should_use_notional_order("AAPL", 10.5)

        assert result is True


class TestConvertToWholeSharesMethod:
    """Test convert_to_whole_shares method."""

    def test_fractionable_asset_no_conversion(self):
        """Test that fractionable assets are not converted."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, used_rounding = detector.convert_to_whole_shares(
            "AAPL", Decimal("10.5"), Decimal("150.00")
        )

        assert quantity == Decimal("10.5")
        assert used_rounding is False

    def test_non_fractionable_with_fractional_rounds_down(self):
        """Test that non-fractionable assets round down."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("10.75"), Decimal("50.00")
        )

        assert quantity == Decimal("10")
        assert used_rounding is True

    def test_non_fractionable_whole_number_no_change(self):
        """Test that whole numbers don't trigger rounding for non-fractionable."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("10"), Decimal("50.00")
        )

        assert quantity == Decimal("10")
        assert used_rounding is False

    def test_rounding_flag_accuracy(self):
        """Test that rounding flag is set correctly."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # With rounding
        _, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("10.01"), Decimal("50.00")
        )
        assert used_rounding is True

        # Without rounding
        _, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("10.0"), Decimal("50.00")
        )
        assert used_rounding is False

    def test_edge_case_less_than_one_share(self):
        """Test edge case where quantity < 1.0 rounds to 0."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("0.99"), Decimal("50.00")
        )

        assert quantity == Decimal("0")
        assert used_rounding is True

    def test_edge_case_just_over_one_share(self):
        """Test edge case where quantity is just over 1.0."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, used_rounding = detector.convert_to_whole_shares(
            "FNGU", Decimal("1.01"), Decimal("50.00")
        )

        assert quantity == Decimal("1")
        assert used_rounding is True

    def test_return_type_is_decimal(self):
        """Test that return type is Decimal, not float."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        quantity, _ = detector.convert_to_whole_shares("FNGU", Decimal("10.5"), Decimal("50.00"))

        assert isinstance(quantity, Decimal)

    def test_precision_with_various_prices(self):
        """Test precision with different price points."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Test with high price
        quantity, _ = detector.convert_to_whole_shares(
            "FNGU", Decimal("10.9999"), Decimal("500.123456")
        )
        assert quantity == Decimal("10")

        # Test with low price
        quantity, _ = detector.convert_to_whole_shares("FNGU", Decimal("100.5"), Decimal("0.01"))
        assert quantity == Decimal("100")

    def test_accepts_float_inputs(self):
        """Test that method accepts float inputs and converts to Decimal."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Should not raise exception with float inputs
        quantity, used_rounding = detector.convert_to_whole_shares("FNGU", 10.75, 50.00)

        assert quantity == Decimal("10")
        assert used_rounding is True


class TestGetCacheStatsMethod:
    """Test get_cache_stats method."""

    def test_empty_cache(self):
        """Test cache stats with empty cache."""
        detector = FractionabilityDetector()

        stats = detector.get_cache_stats()

        assert stats["cached_symbols"] == 0
        assert stats["fractionable_count"] == 0
        assert stats["non_fractionable_count"] == 0

    def test_cache_with_mixed_results(self):
        """Test cache stats with mixed fractionable/non-fractionable results."""
        mock_provider = Mock()
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Add some cached results
        detector._fractionability_cache["AAPL"] = True
        detector._fractionability_cache["TSLA"] = True
        detector._fractionability_cache["FNGU"] = False

        stats = detector.get_cache_stats()

        assert stats["cached_symbols"] == 3
        assert stats["fractionable_count"] == 2
        assert stats["non_fractionable_count"] == 1

    def test_cache_stats_accuracy(self):
        """Test that cache stats accurately reflect cache state."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Query some symbols
        detector.is_fractionable("AAPL")
        detector.is_fractionable("TSLA")

        stats = detector.get_cache_stats()

        assert stats["cached_symbols"] == 2
        assert stats["fractionable_count"] == 2
        assert stats["non_fractionable_count"] == 0


class TestGlobalInstance:
    """Test global fractionability_detector instance."""

    def test_global_instance_exists(self):
        """Test that global instance is accessible."""
        assert fractionability_detector is not None
        assert isinstance(fractionability_detector, FractionabilityDetector)

    def test_global_instance_has_no_provider(self):
        """Test that global instance starts without provider."""
        # Note: This test may fail if other tests modify the global instance
        # In production, the global instance should be reinitialized with a provider
        assert fractionability_detector.asset_metadata_provider is None


class TestPropertyBasedTests:
    """Property-based tests using Hypothesis."""

    @given(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))
    )
    def test_symbol_normalization_idempotence(self, symbol: str):
        """Test that symbol normalization is idempotent."""
        detector = FractionabilityDetector()

        # Normalize once
        normalized_once = symbol.upper()
        # Normalize twice
        normalized_twice = normalized_once.upper()

        assert normalized_once == normalized_twice

    @given(st.decimals(min_value=0, max_value=1000, places=2))
    def test_convert_to_whole_shares_always_returns_integer_or_unchanged(self, quantity: Decimal):
        """Test that conversion always returns whole number for non-fractionable."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = False
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        result, _ = detector.convert_to_whole_shares("FNGU", quantity, Decimal("50"))

        # Result should be a whole number
        assert result == result.to_integral_value()

    @given(st.decimals(min_value=0, max_value=1000, places=6))
    def test_should_use_notional_order_consistency(self, quantity: Decimal):
        """Test that should_use_notional_order returns consistent results."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # Call twice with same input
        result1 = detector.should_use_notional_order("AAPL", quantity)
        result2 = detector.should_use_notional_order("AAPL", quantity)

        assert result1 == result2

    @given(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu",))))
    def test_cache_consistency(self, symbol: str):
        """Test that cached results are consistent across calls."""
        mock_provider = Mock()
        mock_provider.is_fractionable.return_value = True
        detector = FractionabilityDetector(asset_metadata_provider=mock_provider)

        # First call
        result1 = detector.is_fractionable(symbol)
        # Second call (should use cache)
        result2 = detector.is_fractionable(symbol)

        assert result1 == result2
