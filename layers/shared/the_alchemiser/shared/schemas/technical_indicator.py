#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Technical indicator data transfer objects for strategy engines.

Provides typed DTOs for technical indicators with standardized field names
and validation to ensure consistent indicator data across strategy engines.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..constants import CONTRACT_VERSION
from ..utils.timezone_utils import ensure_timezone_aware


class TechnicalIndicator(BaseModel):
    """DTO for technical indicator data used by strategy engines.

    Provides a standardized structure for technical indicators computed
    from market data, with proper validation and type safety.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Identification
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    timestamp: datetime = Field(..., description="Indicator calculation timestamp")
    data_source: str | None = Field(default=None, description="Data source identifier")

    # Price indicators
    current_price: Decimal | None = Field(default=None, gt=0, description="Current/last price")

    # RSI indicators (common windows)
    rsi_10: float | None = Field(
        default=None, ge=0, le=100, description="RSI with 10-period window"
    )
    rsi_14: float | None = Field(
        default=None, ge=0, le=100, description="RSI with 14-period window"
    )
    rsi_20: float | None = Field(
        default=None, ge=0, le=100, description="RSI with 20-period window"
    )
    rsi_21: float | None = Field(
        default=None, ge=0, le=100, description="RSI with 21-period window"
    )

    # Moving Average indicators
    ma_20: float | None = Field(default=None, gt=0, description="20-period simple moving average")
    ma_50: float | None = Field(default=None, gt=0, description="50-period simple moving average")
    ma_200: float | None = Field(default=None, gt=0, description="200-period simple moving average")

    # Exponential Moving Averages
    ema_12: float | None = Field(
        default=None, gt=0, description="12-period exponential moving average"
    )
    ema_26: float | None = Field(
        default=None, gt=0, description="26-period exponential moving average"
    )

    # Return indicators
    ma_return_90: float | None = Field(default=None, description="90-period moving average return")
    cum_return_60: float | None = Field(default=None, description="60-period cumulative return")
    stdev_return_6: float | None = Field(
        default=None, ge=0, description="6-period return standard deviation"
    )
    stdev_price_6: float | None = Field(
        default=None, ge=0, description="6-period price standard deviation"
    )

    # Volatility indicators
    volatility_14: float | None = Field(default=None, ge=0, description="14-period volatility")
    volatility_20: float | None = Field(default=None, ge=0, description="20-period volatility")
    atr_14: float | None = Field(default=None, ge=0, description="14-period Average True Range")

    # MACD indicators
    macd_line: float | None = Field(default=None, description="MACD line (12-26 EMA difference)")
    macd_signal: float | None = Field(
        default=None, description="MACD signal line (9-period EMA of MACD)"
    )
    macd_histogram: float | None = Field(default=None, description="MACD histogram (MACD - Signal)")

    # Bollinger Bands
    bb_upper: float | None = Field(default=None, gt=0, description="Bollinger Band upper bound")
    bb_middle: float | None = Field(default=None, gt=0, description="Bollinger Band middle (SMA)")
    bb_lower: float | None = Field(default=None, gt=0, description="Bollinger Band lower bound")
    bb_width: float | None = Field(default=None, ge=0, description="Bollinger Band width")

    # Volume indicators
    volume_sma_20: float | None = Field(default=None, ge=0, description="20-period volume SMA")
    volume_ratio: float | None = Field(
        default=None, ge=0, description="Current volume / average volume"
    )

    # Custom indicators
    nuclear_strength: float | None = Field(
        default=None, description="Nuclear strategy specific indicator"
    )
    klm_score: float | None = Field(default=None, description="KLM strategy specific score")
    tecl_regime: str | None = Field(default=None, description="TECL strategy market regime")

    # Data quality
    calculation_window: int | None = Field(
        default=None, ge=1, description="Minimum window used for calculations"
    )
    completeness_score: float | None = Field(
        default=None, ge=0, le=1, description="Data completeness (0-1)"
    )

    # Optional metadata
    metadata: dict[str, str | int | float | bool] | None = Field(
        default=None, description="Additional indicator metadata"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @field_validator("tecl_regime")
    @classmethod
    def validate_tecl_regime(cls, v: str | None) -> str | None:
        """Validate TECL regime values."""
        if v is None:
            return v
        valid_regimes = {"BULL", "BEAR", "NEUTRAL", "TRANSITION"}
        regime_upper = v.strip().upper()
        if regime_upper not in valid_regimes:
            raise ValueError(f"TECL regime must be one of {valid_regimes}, got {regime_upper}")
        return regime_upper

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation optimized for JSON serialization.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        if self.current_price is not None:
            data["current_price"] = str(self.current_price)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TechnicalIndicator:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing indicator data

        Returns:
            TechnicalIndicator instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

        # Convert string current_price back to Decimal
        if (
            "current_price" in data
            and data["current_price"] is not None
            and isinstance(data["current_price"], str)
        ):
            try:
                data["current_price"] = Decimal(data["current_price"])
            except (ValueError, TypeError, InvalidOperation) as e:
                raise ValueError(f"Invalid current_price value: {data['current_price']}") from e

        return cls(**data)

    @classmethod
    def from_legacy_dict(cls, symbol: str, legacy_indicators: dict[str, Any]) -> TechnicalIndicator:
        """Create TechnicalIndicator from legacy indicator dictionary.

        Args:
            symbol: Trading symbol
            legacy_indicators: Dictionary with legacy indicator structure

        Returns:
            TechnicalIndicator instance

        Note:
            Handles conversion from existing strategy engine indicator formats
            to the new typed DTO structure.

        """
        try:
            base_data = cls._build_base_data(symbol, legacy_indicators)
            cls._map_price_indicators(legacy_indicators, base_data)
            cls._map_rsi_indicators(legacy_indicators, base_data)
            cls._map_moving_averages(legacy_indicators, base_data)
            cls._map_return_indicators(legacy_indicators, base_data)
            cls._map_volatility_indicators(legacy_indicators, base_data)
            cls._map_remaining_to_metadata(legacy_indicators, base_data)

            return cls(**base_data)

        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid legacy indicator data for {symbol}: {e}") from e

    @classmethod
    def _build_base_data(cls, symbol: str, legacy_indicators: dict[str, Any]) -> dict[str, Any]:
        """Build base DTO data with symbol, timestamp, and data source."""
        timestamp = legacy_indicators.get("timestamp", datetime.now(UTC))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        return {
            "symbol": symbol,
            "timestamp": ensure_timezone_aware(timestamp),
            "data_source": legacy_indicators.get("data_source", "legacy"),
        }

    @classmethod
    def _map_price_indicators(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map price indicators from legacy format."""
        if "current_price" in legacy_indicators:
            base_data["current_price"] = Decimal(str(legacy_indicators["current_price"]))

    @classmethod
    def _map_rsi_indicators(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map RSI indicators from legacy format."""
        for period in [10, 14, 20, 21]:
            key = f"rsi_{period}"
            if key in legacy_indicators:
                base_data[key] = float(legacy_indicators[key])

    @classmethod
    def _map_moving_averages(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map moving average indicators from legacy format."""
        for period in [20, 50, 200]:
            key = f"ma_{period}"
            if key in legacy_indicators:
                base_data[key] = float(legacy_indicators[key])

    @classmethod
    def _map_return_indicators(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map return indicators from legacy format."""
        return_keys = ["ma_return_90", "cum_return_60", "stdev_return_6"]
        for key in return_keys:
            if key in legacy_indicators:
                base_data[key] = float(legacy_indicators[key])

    @classmethod
    def _map_volatility_indicators(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map volatility indicators from legacy format."""
        volatility_keys = ["volatility_14", "volatility_20", "atr_14"]
        for key in volatility_keys:
            if key in legacy_indicators:
                base_data[key] = float(legacy_indicators[key])

    @classmethod
    def _map_remaining_to_metadata(
        cls, legacy_indicators: dict[str, Any], base_data: dict[str, Any]
    ) -> None:
        """Map any remaining indicators to metadata."""
        mapped_keys = set(base_data.keys()) | {"timestamp", "data_source"}
        remaining = {k: v for k, v in legacy_indicators.items() if k not in mapped_keys}
        if remaining:
            base_data["metadata"] = remaining

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility.

        Returns:
            Dictionary in the format expected by existing strategy engines.

        """
        result: dict[str, Any] = {}

        self._add_price_indicators_to_dict(result)
        self._add_rsi_indicators_to_dict(result)
        self._add_moving_averages_to_dict(result)
        self._add_return_indicators_to_dict(result)
        self._add_volatility_indicators_to_dict(result)
        self._add_metadata_to_dict(result)

        return result

    def _add_price_indicators_to_dict(self, result: dict[str, Any]) -> None:
        """Add price indicators to legacy dictionary."""
        if self.current_price is not None:
            result["current_price"] = float(self.current_price)

    def _add_rsi_indicators_to_dict(self, result: dict[str, Any]) -> None:
        """Add RSI indicators to legacy dictionary."""
        for period in [10, 14, 20, 21]:
            value = getattr(self, f"rsi_{period}")
            if value is not None:
                result[f"rsi_{period}"] = value

    def _add_moving_averages_to_dict(self, result: dict[str, Any]) -> None:
        """Add moving average indicators to legacy dictionary."""
        for period in [20, 50, 200]:
            value = getattr(self, f"ma_{period}")
            if value is not None:
                result[f"ma_{period}"] = value

    def _add_return_indicators_to_dict(self, result: dict[str, Any]) -> None:
        """Add return indicators to legacy dictionary."""
        for key in ["ma_return_90", "cum_return_60", "stdev_return_6"]:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

    def _add_volatility_indicators_to_dict(self, result: dict[str, Any]) -> None:
        """Add volatility indicators to legacy dictionary."""
        for key in ["volatility_14", "volatility_20", "atr_14"]:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

    def _add_metadata_to_dict(self, result: dict[str, Any]) -> None:
        """Add metadata to legacy dictionary."""
        if self.metadata:
            result.update(self.metadata)

    def get_rsi_by_period(self, period: int) -> float | None:
        """Get RSI value for a specific period.

        Args:
            period: RSI period (10, 14, 20, or 21)

        Returns:
            RSI value or None if not available

        """
        field_name = f"rsi_{period}"
        return getattr(self, field_name, None)

    def get_ma_by_period(self, period: int) -> float | None:
        """Get moving average value for a specific period.

        Args:
            period: MA period (20, 50, or 200)

        Returns:
            Moving average value or None if not available

        """
        field_name = f"ma_{period}"
        return getattr(self, field_name, None)
