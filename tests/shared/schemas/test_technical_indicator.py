"""Business Unit: shared | Status: current

Unit tests for TechnicalIndicator DTO.

Tests DTO validation, immutability, serialization, and legacy format conversion.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator


class TestTechnicalIndicatorCreation:
    """Test TechnicalIndicator DTO creation and validation."""

    def test_valid_technical_indicator_minimal(self):
        """Test creation with only required fields."""
        now = datetime.now(UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=now,
        )
        assert indicator.symbol == "AAPL"
        assert indicator.timestamp == now
        assert indicator.current_price is None
        assert indicator.rsi_14 is None

    def test_valid_technical_indicator_full(self):
        """Test creation with all fields."""
        now = datetime.now(UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=now,
            data_source="alpaca",
            current_price=Decimal("150.50"),
            rsi_10=45.2,
            rsi_14=52.3,
            rsi_20=48.1,
            rsi_21=49.0,
            ma_20=148.0,
            ma_50=145.5,
            ma_200=140.0,
            ema_12=149.0,
            ema_26=147.0,
            ma_return_90=0.15,
            cum_return_60=0.10,
            stdev_return_6=0.02,
            volatility_14=0.25,
            volatility_20=0.22,
            atr_14=3.5,
            macd_line=2.1,
            macd_signal=1.8,
            macd_histogram=0.3,
            bb_upper=155.0,
            bb_middle=150.0,
            bb_lower=145.0,
            bb_width=10.0,
            volume_sma_20=1000000.0,
            volume_ratio=1.2,
            nuclear_strength=0.75,
            klm_score=85.5,
            tecl_regime="BULL",
            calculation_window=200,
            completeness_score=0.95,
            metadata={"source": "live", "latency_ms": 15},
        )
        assert indicator.symbol == "AAPL"
        assert indicator.current_price == Decimal("150.50")
        assert indicator.rsi_14 == 52.3
        assert indicator.tecl_regime == "BULL"

    def test_immutability(self):
        """Test that TechnicalIndicator is frozen."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            indicator.symbol = "GOOGL"  # type: ignore

    def test_symbol_normalization_to_uppercase(self):
        """Test that symbol is normalized to uppercase."""
        indicator = TechnicalIndicator(
            symbol="aapl",
            timestamp=datetime.now(UTC),
        )
        assert indicator.symbol == "AAPL"

    def test_symbol_whitespace_stripped(self):
        """Test that symbol whitespace is stripped."""
        indicator = TechnicalIndicator(
            symbol="  AAPL  ",
            timestamp=datetime.now(UTC),
        )
        assert indicator.symbol == "AAPL"

    def test_naive_timestamp_converted_to_utc(self):
        """Test that naive datetime is converted to UTC."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=naive_dt,
        )
        assert indicator.timestamp.tzinfo is UTC

    def test_aware_timestamp_preserved(self):
        """Test that timezone-aware datetime is preserved."""
        aware_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=aware_dt,
        )
        assert indicator.timestamp == aware_dt
        assert indicator.timestamp.tzinfo is UTC


class TestTechnicalIndicatorValidation:
    """Test field validation rules."""

    def test_empty_symbol_rejected(self):
        """Test that empty symbol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="",
                timestamp=datetime.now(UTC),
            )
        assert "symbol" in str(exc_info.value)

    def test_symbol_too_long_rejected(self):
        """Test that symbol exceeding max length is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="VERYLONGSYM",  # 11 chars
                timestamp=datetime.now(UTC),
            )
        assert "symbol" in str(exc_info.value)

    def test_negative_current_price_rejected(self):
        """Test that negative price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                current_price=Decimal("-10.0"),
            )
        assert "current_price" in str(exc_info.value)

    def test_zero_current_price_rejected(self):
        """Test that zero price is rejected (gt=0)."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                current_price=Decimal("0.0"),
            )
        assert "current_price" in str(exc_info.value)

    def test_rsi_below_zero_rejected(self):
        """Test that RSI below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                rsi_14=-5.0,
            )
        assert "rsi_14" in str(exc_info.value)

    def test_rsi_above_100_rejected(self):
        """Test that RSI above 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                rsi_14=105.0,
            )
        assert "rsi_14" in str(exc_info.value)

    def test_rsi_boundary_values_accepted(self):
        """Test that RSI boundary values 0 and 100 are accepted."""
        indicator_zero = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            rsi_14=0.0,
        )
        assert indicator_zero.rsi_14 == 0.0

        indicator_hundred = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            rsi_14=100.0,
        )
        assert indicator_hundred.rsi_14 == 100.0

    def test_negative_moving_average_rejected(self):
        """Test that negative moving average is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                ma_20=-10.0,
            )
        assert "ma_20" in str(exc_info.value)

    def test_negative_volatility_rejected(self):
        """Test that negative volatility is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                volatility_14=-0.1,
            )
        assert "volatility_14" in str(exc_info.value)

    def test_negative_volume_ratio_rejected(self):
        """Test that negative volume ratio is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                volume_ratio=-0.5,
            )
        assert "volume_ratio" in str(exc_info.value)

    def test_completeness_score_below_zero_rejected(self):
        """Test that completeness score below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                completeness_score=-0.1,
            )
        assert "completeness_score" in str(exc_info.value)

    def test_completeness_score_above_one_rejected(self):
        """Test that completeness score above 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                completeness_score=1.5,
            )
        assert "completeness_score" in str(exc_info.value)

    def test_calculation_window_zero_rejected(self):
        """Test that zero calculation window is rejected (ge=1)."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                calculation_window=0,
            )
        assert "calculation_window" in str(exc_info.value)

    def test_invalid_tecl_regime_rejected(self):
        """Test that invalid TECL regime is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                tecl_regime="INVALID",
            )
        assert "TECL regime must be one of" in str(exc_info.value)

    def test_valid_tecl_regimes_accepted(self):
        """Test that all valid TECL regimes are accepted."""
        valid_regimes = ["BULL", "BEAR", "NEUTRAL", "TRANSITION"]
        for regime in valid_regimes:
            indicator = TechnicalIndicator(
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                tecl_regime=regime,
            )
            assert indicator.tecl_regime == regime

    def test_tecl_regime_normalized_to_uppercase(self):
        """Test that TECL regime is normalized to uppercase."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            tecl_regime="bull",
        )
        assert indicator.tecl_regime == "BULL"


class TestTechnicalIndicatorSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        now = datetime.now(UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=now,
            current_price=Decimal("150.50"),
        )
        data = indicator.to_dict()
        
        assert data["symbol"] == "AAPL"
        assert data["timestamp"] == now.isoformat()
        assert data["current_price"] == "150.50"

    def test_to_dict_converts_decimal_to_string(self):
        """Test that Decimal price is converted to string."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("123.456"),
        )
        data = indicator.to_dict()
        
        assert isinstance(data["current_price"], str)
        assert data["current_price"] == "123.456"

    def test_to_dict_converts_timestamp_to_iso(self):
        """Test that timestamp is converted to ISO string."""
        now = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=now,
        )
        data = indicator.to_dict()
        
        assert isinstance(data["timestamp"], str)
        assert now.isoformat() in data["timestamp"]

    def test_from_dict_basic(self):
        """Test basic from_dict conversion."""
        data = {
            "symbol": "AAPL",
            "timestamp": "2025-01-15T10:30:00+00:00",
            "current_price": "150.50",
        }
        indicator = TechnicalIndicator.from_dict(data)
        
        assert indicator.symbol == "AAPL"
        assert indicator.current_price == Decimal("150.50")
        assert indicator.timestamp.year == 2025

    def test_from_dict_with_z_suffix_timestamp(self):
        """Test from_dict with Z suffix timestamp."""
        data = {
            "symbol": "AAPL",
            "timestamp": "2025-01-15T10:30:00Z",
        }
        indicator = TechnicalIndicator.from_dict(data)
        
        assert indicator.timestamp.year == 2025
        assert indicator.timestamp.tzinfo is not None

    def test_from_dict_invalid_timestamp_raises_error(self):
        """Test that invalid timestamp format raises ValueError."""
        data = {
            "symbol": "AAPL",
            "timestamp": "not-a-timestamp",
        }
        with pytest.raises(ValueError) as exc_info:
            TechnicalIndicator.from_dict(data)
        assert "Invalid timestamp format" in str(exc_info.value)

    def test_from_dict_invalid_price_raises_error(self):
        """Test that invalid price raises ValueError."""
        data = {
            "symbol": "AAPL",
            "timestamp": "2025-01-15T10:30:00+00:00",
            "current_price": "not-a-number",
        }
        with pytest.raises(ValueError) as exc_info:
            TechnicalIndicator.from_dict(data)
        assert "Invalid current_price value" in str(exc_info.value)

    def test_roundtrip_serialization(self):
        """Test that serialization roundtrip preserves data."""
        now = datetime.now(UTC)
        original = TechnicalIndicator(
            symbol="AAPL",
            timestamp=now,
            current_price=Decimal("150.50"),
            rsi_14=52.3,
            ma_20=148.0,
        )
        
        data = original.to_dict()
        reconstructed = TechnicalIndicator.from_dict(data)
        
        assert reconstructed.symbol == original.symbol
        assert reconstructed.current_price == original.current_price
        assert reconstructed.rsi_14 == original.rsi_14
        assert reconstructed.ma_20 == original.ma_20


class TestTechnicalIndicatorLegacyConversion:
    """Test legacy format conversion."""

    def test_from_legacy_dict_basic(self):
        """Test basic legacy dict conversion."""
        legacy_data = {
            "current_price": 150.50,
            "rsi_14": 52.3,
            "ma_20": 148.0,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.symbol == "AAPL"
        assert indicator.current_price == Decimal("150.50")
        assert indicator.rsi_14 == 52.3
        assert indicator.ma_20 == 148.0

    def test_from_legacy_dict_with_timestamp(self):
        """Test legacy conversion with explicit timestamp."""
        timestamp_str = "2025-01-15T10:30:00+00:00"
        legacy_data = {
            "timestamp": timestamp_str,
            "current_price": 150.50,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.timestamp.year == 2025
        assert indicator.timestamp.month == 1

    def test_from_legacy_dict_maps_rsi_indicators(self):
        """Test that RSI indicators are mapped correctly."""
        legacy_data = {
            "rsi_10": 45.0,
            "rsi_14": 50.0,
            "rsi_20": 55.0,
            "rsi_21": 56.0,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.rsi_10 == 45.0
        assert indicator.rsi_14 == 50.0
        assert indicator.rsi_20 == 55.0
        assert indicator.rsi_21 == 56.0

    def test_from_legacy_dict_maps_moving_averages(self):
        """Test that moving averages are mapped correctly."""
        legacy_data = {
            "ma_20": 148.0,
            "ma_50": 145.0,
            "ma_200": 140.0,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.ma_20 == 148.0
        assert indicator.ma_50 == 145.0
        assert indicator.ma_200 == 140.0

    def test_from_legacy_dict_maps_return_indicators(self):
        """Test that return indicators are mapped correctly."""
        legacy_data = {
            "ma_return_90": 0.15,
            "cum_return_60": 0.10,
            "stdev_return_6": 0.02,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.ma_return_90 == 0.15
        assert indicator.cum_return_60 == 0.10
        assert indicator.stdev_return_6 == 0.02

    def test_from_legacy_dict_maps_volatility_indicators(self):
        """Test that volatility indicators are mapped correctly."""
        legacy_data = {
            "volatility_14": 0.25,
            "volatility_20": 0.22,
            "atr_14": 3.5,
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.volatility_14 == 0.25
        assert indicator.volatility_20 == 0.22
        assert indicator.atr_14 == 3.5

    def test_from_legacy_dict_maps_unknown_to_metadata(self):
        """Test that unknown fields are mapped to metadata."""
        legacy_data = {
            "current_price": 150.50,
            "custom_indicator_1": 42,
            "custom_indicator_2": "value",
        }
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", legacy_data)
        
        assert indicator.metadata is not None
        assert "custom_indicator_1" in indicator.metadata
        assert "custom_indicator_2" in indicator.metadata

    def test_to_legacy_dict_basic(self):
        """Test basic to_legacy_dict conversion."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.50"),
            rsi_14=52.3,
            ma_20=148.0,
        )
        legacy_data = indicator.to_legacy_dict()
        
        assert legacy_data["current_price"] == 150.50
        assert legacy_data["rsi_14"] == 52.3
        assert legacy_data["ma_20"] == 148.0

    def test_to_legacy_dict_includes_metadata(self):
        """Test that metadata is included in legacy dict."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            metadata={"custom_field": "value"},
        )
        legacy_data = indicator.to_legacy_dict()
        
        assert "custom_field" in legacy_data
        assert legacy_data["custom_field"] == "value"

    def test_legacy_roundtrip_preserves_data(self):
        """Test that legacy conversion roundtrip preserves data."""
        original_legacy = {
            "current_price": 150.50,
            "rsi_14": 52.3,
            "ma_20": 148.0,
            "volatility_14": 0.25,
        }
        
        indicator = TechnicalIndicator.from_legacy_dict("AAPL", original_legacy)
        reconstructed_legacy = indicator.to_legacy_dict()
        
        assert reconstructed_legacy["current_price"] == original_legacy["current_price"]
        assert reconstructed_legacy["rsi_14"] == original_legacy["rsi_14"]
        assert reconstructed_legacy["ma_20"] == original_legacy["ma_20"]
        assert reconstructed_legacy["volatility_14"] == original_legacy["volatility_14"]


class TestTechnicalIndicatorGetters:
    """Test convenience getter methods."""

    def test_get_rsi_by_period(self):
        """Test getting RSI by period."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            rsi_10=45.0,
            rsi_14=50.0,
            rsi_20=55.0,
        )
        
        assert indicator.get_rsi_by_period(10) == 45.0
        assert indicator.get_rsi_by_period(14) == 50.0
        assert indicator.get_rsi_by_period(20) == 55.0

    def test_get_rsi_by_period_returns_none_if_not_set(self):
        """Test that get_rsi_by_period returns None if not set."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
        )
        
        assert indicator.get_rsi_by_period(14) is None

    def test_get_ma_by_period(self):
        """Test getting MA by period."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            ma_20=148.0,
            ma_50=145.0,
            ma_200=140.0,
        )
        
        assert indicator.get_ma_by_period(20) == 148.0
        assert indicator.get_ma_by_period(50) == 145.0
        assert indicator.get_ma_by_period(200) == 140.0

    def test_get_ma_by_period_returns_none_if_not_set(self):
        """Test that get_ma_by_period returns None if not set."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
        )
        
        assert indicator.get_ma_by_period(20) is None


class TestTechnicalIndicatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_optional_fields_none(self):
        """Test that all optional fields can be None."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
        )
        
        # Verify all optional fields are None
        assert indicator.data_source is None
        assert indicator.current_price is None
        assert indicator.rsi_10 is None
        assert indicator.ma_20 is None
        assert indicator.volatility_14 is None
        assert indicator.metadata is None

    def test_metadata_with_various_types(self):
        """Test metadata with various allowed types."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            metadata={
                "string_val": "test",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": True,
            },
        )
        
        assert indicator.metadata["string_val"] == "test"
        assert indicator.metadata["int_val"] == 42
        assert indicator.metadata["float_val"] == 3.14
        assert indicator.metadata["bool_val"] is True

    def test_decimal_precision_preserved(self):
        """Test that Decimal precision is preserved."""
        price = Decimal("150.123456789")
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=price,
        )
        
        assert indicator.current_price == price
        assert str(indicator.current_price) == "150.123456789"

    def test_very_small_positive_price(self):
        """Test very small positive price (penny stocks)."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("0.0001"),
        )
        
        assert indicator.current_price == Decimal("0.0001")

    def test_negative_returns_allowed(self):
        """Test that negative returns are allowed (losses)."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            ma_return_90=-0.15,
            cum_return_60=-0.10,
        )
        
        assert indicator.ma_return_90 == -0.15
        assert indicator.cum_return_60 == -0.10

    def test_negative_macd_values_allowed(self):
        """Test that negative MACD values are allowed."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            macd_line=-2.1,
            macd_signal=-1.8,
            macd_histogram=-0.3,
        )
        
        assert indicator.macd_line == -2.1
        assert indicator.macd_signal == -1.8
        assert indicator.macd_histogram == -0.3
