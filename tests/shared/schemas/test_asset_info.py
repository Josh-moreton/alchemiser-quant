"""Business Unit: shared | Status: current.

Comprehensive test suite for AssetInfo DTO.

Tests cover:
- Valid construction with all fields
- Valid construction with minimal required fields
- Symbol normalization validator
- Frozen/immutable behavior
- Invalid inputs (empty symbol, invalid types)
- Field validation and constraints
- Edge cases (special characters, whitespace handling)
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure we can import the module directly without circular imports
# This is necessary because schemas/__init__.py has circular dependencies
if True:  # noqa: SIM108
    # Import the module directly
    import importlib.util

    asset_info_path = (
        Path(__file__).parent.parent.parent.parent
        / "the_alchemiser"
        / "shared"
        / "schemas"
        / "asset_info.py"
    )
    spec = importlib.util.spec_from_file_location("asset_info_module", asset_info_path)
    asset_info_module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(asset_info_module)  # type: ignore
    AssetInfo = asset_info_module.AssetInfo


class TestAssetInfoConstruction:
    """Test AssetInfo construction with various field combinations."""

    def test_construction_with_all_fields(self):
        """Test construction with all fields provided."""
        asset = AssetInfo(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            asset_class="us_equity",
            tradable=True,
            fractionable=True,
            marginable=True,
            shortable=True,
        )

        assert asset.symbol == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.exchange == "NASDAQ"
        assert asset.asset_class == "us_equity"
        assert asset.tradable is True
        assert asset.fractionable is True
        assert asset.marginable is True
        assert asset.shortable is True

    def test_construction_with_minimal_required_fields(self):
        """Test construction with only required fields."""
        asset = AssetInfo(symbol="TSLA", fractionable=True)

        assert asset.symbol == "TSLA"
        assert asset.name is None
        assert asset.exchange is None
        assert asset.asset_class is None
        assert asset.tradable is True  # default value
        assert asset.fractionable is True
        assert asset.marginable is None
        assert asset.shortable is None

    def test_construction_non_fractionable_asset(self):
        """Test construction of non-fractionable asset."""
        asset = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Class A",
            fractionable=False,
            tradable=True,
        )

        assert asset.symbol == "BRK.A"
        assert asset.fractionable is False
        assert asset.tradable is True

    def test_construction_non_tradable_asset(self):
        """Test construction of non-tradable asset."""
        asset = AssetInfo(symbol="SUSPENDED", fractionable=False, tradable=False)

        assert asset.symbol == "SUSPENDED"
        assert asset.tradable is False
        assert asset.fractionable is False

    def test_construction_with_special_chars_in_symbol(self):
        """Test construction with special characters in symbol."""
        # Common valid special characters in symbols
        symbols = ["BRK.B", "BF-B", "SPX-W", "ABC.PR.D"]

        for symbol in symbols:
            asset = AssetInfo(symbol=symbol, fractionable=True)
            assert asset.symbol == symbol.upper()

    def test_construction_with_all_optional_fields_none(self):
        """Test construction with all optional fields explicitly set to None."""
        asset = AssetInfo(
            symbol="TEST",
            name=None,
            exchange=None,
            asset_class=None,
            fractionable=True,
            marginable=None,
            shortable=None,
        )

        assert asset.symbol == "TEST"
        assert asset.name is None
        assert asset.exchange is None
        assert asset.asset_class is None
        assert asset.marginable is None
        assert asset.shortable is None


class TestAssetInfoSymbolNormalization:
    """Test symbol normalization validator."""

    def test_symbol_normalized_to_uppercase(self):
        """Test that symbol is normalized to uppercase."""
        asset = AssetInfo(symbol="aapl", fractionable=True)
        assert asset.symbol == "AAPL"

    def test_symbol_with_whitespace_stripped_and_uppercased(self):
        """Test that symbol whitespace is stripped and uppercased."""
        asset = AssetInfo(symbol="  aapl  ", fractionable=True)
        assert asset.symbol == "AAPL"

    def test_symbol_mixed_case_normalized(self):
        """Test that mixed case symbol is normalized."""
        asset = AssetInfo(symbol="AaPl", fractionable=True)
        assert asset.symbol == "AAPL"

    def test_symbol_with_special_chars_preserved(self):
        """Test that special characters are preserved after normalization."""
        asset = AssetInfo(symbol="brk.b", fractionable=True)
        assert asset.symbol == "BRK.B"

    def test_symbol_with_hyphen_preserved(self):
        """Test that hyphens are preserved after normalization."""
        asset = AssetInfo(symbol="bf-b", fractionable=True)
        assert asset.symbol == "BF-B"


class TestAssetInfoImmutability:
    """Test that AssetInfo is frozen/immutable."""

    def test_cannot_modify_symbol_after_creation(self):
        """Test that symbol cannot be modified after creation."""
        asset = AssetInfo(symbol="AAPL", fractionable=True)

        with pytest.raises((ValidationError, AttributeError)):
            asset.symbol = "TSLA"  # type: ignore

    def test_cannot_modify_fractionable_after_creation(self):
        """Test that fractionable cannot be modified after creation."""
        asset = AssetInfo(symbol="AAPL", fractionable=True)

        with pytest.raises((ValidationError, AttributeError)):
            asset.fractionable = False  # type: ignore

    def test_cannot_modify_optional_field_after_creation(self):
        """Test that optional fields cannot be modified after creation."""
        asset = AssetInfo(symbol="AAPL", fractionable=True, name="Apple Inc.")

        with pytest.raises((ValidationError, AttributeError)):
            asset.name = "Apple Computer"  # type: ignore

    def test_cannot_add_new_field_after_creation(self):
        """Test that new fields cannot be added after creation."""
        asset = AssetInfo(symbol="AAPL", fractionable=True)

        with pytest.raises((ValidationError, AttributeError)):
            asset.new_field = "value"  # type: ignore


class TestAssetInfoValidation:
    """Test validation of AssetInfo fields."""

    def test_missing_required_symbol_raises_error(self):
        """Test that missing symbol raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AssetInfo(fractionable=True)  # type: ignore

        assert "symbol" in str(exc_info.value).lower()

    def test_missing_required_fractionable_raises_error(self):
        """Test that missing fractionable raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AssetInfo(symbol="AAPL")  # type: ignore

        assert "fractionable" in str(exc_info.value).lower()

    def test_empty_symbol_raises_error(self):
        """Test that empty symbol raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AssetInfo(symbol="", fractionable=True)

        error_str = str(exc_info.value).lower()
        assert "symbol" in error_str or "min_length" in error_str

    def test_whitespace_only_symbol_normalized_to_empty_raises_error(self):
        """Test that whitespace-only symbol raises error after normalization."""
        with pytest.raises(ValidationError) as exc_info:
            AssetInfo(symbol="   ", fractionable=True)

        # After stripping, symbol becomes empty which violates min_length=1
        error_str = str(exc_info.value).lower()
        assert "symbol" in error_str or "min_length" in error_str

    def test_invalid_type_for_symbol_raises_error(self):
        """Test that invalid type for symbol raises ValidationError."""
        with pytest.raises(ValidationError):
            AssetInfo(symbol=123, fractionable=True)  # type: ignore

    def test_invalid_type_for_fractionable_raises_error(self):
        """Test that invalid type for fractionable raises ValidationError."""
        with pytest.raises(ValidationError):
            AssetInfo(symbol="AAPL", fractionable="yes")  # type: ignore

    def test_invalid_type_for_tradable_raises_error(self):
        """Test that invalid type for tradable raises ValidationError."""
        with pytest.raises(ValidationError):
            AssetInfo(symbol="AAPL", fractionable=True, tradable="yes")  # type: ignore

    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected due to extra='forbid'."""
        with pytest.raises(ValidationError) as exc_info:
            AssetInfo(
                symbol="AAPL",
                fractionable=True,
                extra_field="should_fail",  # type: ignore
            )

        error_str = str(exc_info.value).lower()
        assert "extra" in error_str or "extra_field" in error_str


class TestAssetInfoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_symbol(self):
        """Test that very long symbol is accepted (no max length constraint currently)."""
        long_symbol = "A" * 100
        asset = AssetInfo(symbol=long_symbol, fractionable=True)
        assert asset.symbol == long_symbol

    def test_very_long_name(self):
        """Test that very long name is accepted (no max length constraint currently)."""
        long_name = "A" * 1000
        asset = AssetInfo(symbol="TEST", fractionable=True, name=long_name)
        assert asset.name == long_name

    def test_symbol_with_numbers(self):
        """Test that symbol with numbers is accepted."""
        asset = AssetInfo(symbol="SPY500", fractionable=True)
        assert asset.symbol == "SPY500"

    def test_all_boolean_combinations(self):
        """Test all combinations of boolean flags."""
        combinations = [
            (True, True, True, True),
            (True, True, True, False),
            (True, True, False, True),
            (True, False, True, True),
            (False, True, True, True),
            (False, False, False, False),
        ]

        for tradable, fractionable, marginable, shortable in combinations:
            asset = AssetInfo(
                symbol="TEST",
                tradable=tradable,
                fractionable=fractionable,
                marginable=marginable,
                shortable=shortable,
            )
            assert asset.tradable == tradable
            assert asset.fractionable == fractionable
            assert asset.marginable == marginable
            assert asset.shortable == shortable

    def test_none_values_for_optional_bool_fields(self):
        """Test that None is valid for optional boolean fields."""
        asset = AssetInfo(
            symbol="TEST",
            fractionable=True,
            marginable=None,
            shortable=None,
        )
        assert asset.marginable is None
        assert asset.shortable is None


class TestAssetInfoEquality:
    """Test equality and hashing behavior."""

    def test_equal_assets_are_equal(self):
        """Test that assets with same values are equal."""
        asset1 = AssetInfo(
            symbol="AAPL",
            name="Apple Inc.",
            fractionable=True,
            tradable=True,
        )
        asset2 = AssetInfo(
            symbol="AAPL",
            name="Apple Inc.",
            fractionable=True,
            tradable=True,
        )
        assert asset1 == asset2

    def test_different_assets_not_equal(self):
        """Test that assets with different values are not equal."""
        asset1 = AssetInfo(symbol="AAPL", fractionable=True)
        asset2 = AssetInfo(symbol="TSLA", fractionable=True)
        assert asset1 != asset2

    def test_asset_with_different_fractionability_not_equal(self):
        """Test that assets with different fractionability are not equal."""
        asset1 = AssetInfo(symbol="AAPL", fractionable=True)
        asset2 = AssetInfo(symbol="AAPL", fractionable=False)
        assert asset1 != asset2

    def test_hashable_for_use_in_sets(self):
        """Test that AssetInfo is hashable and can be used in sets."""
        asset1 = AssetInfo(symbol="AAPL", fractionable=True)
        asset2 = AssetInfo(symbol="TSLA", fractionable=True)
        asset3 = AssetInfo(symbol="AAPL", fractionable=True)  # same as asset1

        asset_set = {asset1, asset2, asset3}
        assert len(asset_set) == 2  # asset1 and asset3 are the same


class TestAssetInfoSerialization:
    """Test serialization and deserialization."""

    def test_model_dump(self):
        """Test that model_dump produces correct dictionary."""
        asset = AssetInfo(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            fractionable=True,
        )

        data = asset.model_dump()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["exchange"] == "NASDAQ"
        assert data["fractionable"] is True
        assert "tradable" in data
        assert "marginable" in data

    def test_model_dump_json(self):
        """Test that model_dump_json produces valid JSON string."""
        asset = AssetInfo(symbol="AAPL", fractionable=True)

        json_str = asset.model_dump_json()
        assert isinstance(json_str, str)
        assert "AAPL" in json_str
        assert "fractionable" in json_str

    def test_model_validate_from_dict(self):
        """Test reconstruction from dictionary."""
        data = {
            "symbol": "aapl",  # lowercase should be normalized
            "name": "Apple Inc.",
            "fractionable": True,
        }

        asset = AssetInfo.model_validate(data)
        assert asset.symbol == "AAPL"  # normalized to uppercase
        assert asset.name == "Apple Inc."
        assert asset.fractionable is True

    def test_model_validate_json(self):
        """Test reconstruction from JSON string."""
        json_str = '{"symbol": "AAPL", "fractionable": true}'

        asset = AssetInfo.model_validate_json(json_str)
        assert asset.symbol == "AAPL"
        assert asset.fractionable is True


class TestAssetInfoRealWorldScenarios:
    """Test real-world scenarios and use cases."""

    def test_leveraged_etf_3x(self):
        """Test leveraged ETF asset (typically non-fractionable)."""
        asset = AssetInfo(
            symbol="TQQQ",
            name="ProShares UltraPro QQQ",
            exchange="NASDAQ",
            asset_class="us_equity",
            tradable=True,
            fractionable=False,  # Many leveraged ETFs are non-fractionable
            marginable=True,
            shortable=True,
        )

        assert asset.symbol == "TQQQ"
        assert asset.fractionable is False
        assert asset.tradable is True

    def test_inverse_etf(self):
        """Test inverse ETF asset."""
        asset = AssetInfo(
            symbol="SQQQ",
            name="ProShares UltraPro Short QQQ",
            exchange="NASDAQ",
            asset_class="us_equity",
            tradable=True,
            fractionable=False,
            marginable=True,
            shortable=False,  # Inverse ETFs typically not shortable
        )

        assert asset.symbol == "SQQQ"
        assert asset.shortable is False

    def test_berkshire_hathaway_class_a(self):
        """Test Berkshire Hathaway Class A (high-priced, non-fractionable)."""
        asset = AssetInfo(
            symbol="BRK.A",
            name="Berkshire Hathaway Inc. Class A",
            exchange="NYSE",
            asset_class="us_equity",
            tradable=True,
            fractionable=False,
            marginable=True,
            shortable=True,
        )

        assert asset.symbol == "BRK.A"
        assert asset.fractionable is False

    def test_standard_tech_stock(self):
        """Test standard tech stock (fractionable)."""
        asset = AssetInfo(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            asset_class="us_equity",
            tradable=True,
            fractionable=True,
            marginable=True,
            shortable=True,
        )

        assert asset.symbol == "AAPL"
        assert asset.fractionable is True
        assert asset.tradable is True

    def test_suspended_trading_asset(self):
        """Test asset with suspended trading."""
        asset = AssetInfo(
            symbol="SUSPENDED",
            name="Suspended Company",
            exchange="NYSE",
            asset_class="us_equity",
            tradable=False,
            fractionable=False,
            marginable=False,
            shortable=False,
        )

        assert asset.tradable is False
        assert all(
            [
                asset.fractionable is False,
                asset.marginable is False,
                asset.shortable is False,
            ]
        )
