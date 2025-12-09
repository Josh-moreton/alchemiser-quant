"""Business Unit: indicators | Status: current.

Indicator service for computing technical indicators using real market data.

This service integrates with the S3-based market data infrastructure to provide
real-time technical indicator calculations. It is designed to be invoked as a
Lambda function by the Strategy Lambda.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd

from the_alchemiser.indicators.indicators import TechnicalIndicators
from the_alchemiser.shared.errors.exceptions import MarketDataError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = get_logger(__name__)

# Module constant for logging context
MODULE_NAME = "indicators"


class IndicatorComputationError(Exception):
    """Error during indicator computation."""


class IndicatorService:
    """Service for computing technical indicators using real market data.

    Integrates with the S3-based market data infrastructure to provide
    real-time technical indicator calculations.

    Attributes:
        market_data_service: Market data provider for fetching historical bars
        technical_indicators: Technical indicator computation engine

    """

    def __init__(self, market_data_service: MarketDataPort | None) -> None:
        """Initialize indicator service with market data provider.

        Args:
            market_data_service: MarketDataService instance for real market data.
                None is allowed only for testing; production code must provide a service.

        """
        self.market_data_service = market_data_service
        self.technical_indicators: TechnicalIndicators = TechnicalIndicators()
        logger.info(
            "IndicatorService initialized",
            module=MODULE_NAME,
            has_market_data_service=market_data_service is not None,
        )

    def _latest_value(self, series: pd.Series, fallback: float) -> float:
        """Safely get the latest value from a pandas series with fallback.

        Args:
            series: Pandas series containing computed indicator values
            fallback: Fallback value to return if series is empty or contains NaN

        Returns:
            Latest non-NaN value from series, or fallback if unavailable

        """
        if len(series) > 0 and not pd.isna(series.iloc[-1]):
            return float(series.iloc[-1])
        return fallback

    def _compute_rsi(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute RSI indicator."""
        window = int(parameters.get("window", 14))
        rsi_series = self.technical_indicators.rsi(prices, window=window)
        rsi_value = self._latest_value(rsi_series, 50.0)  # Neutral fallback

        logger.debug(
            "RSI computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            rsi_value=rsi_value,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            rsi_14=rsi_value if window == 14 else None,
            rsi_10=rsi_value if window == 10 else None,
            rsi_20=rsi_value if window == 20 else None,
            rsi_21=rsi_value if window == 21 else None,
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else Decimal("100.0")),
            data_source="real_market_data",
            metadata={"value": rsi_value, "window": window},
        )

    def _compute_current_price(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute current price indicator."""
        last_price = float(prices.iloc[-1]) if len(prices) > 0 else None
        if last_price is None:
            logger.error(
                "No last price available",
                module=MODULE_NAME,
                symbol=symbol,
            )
            raise IndicatorComputationError(f"No last price for symbol {symbol}")

        logger.debug(
            "Current price retrieved",
            module=MODULE_NAME,
            symbol=symbol,
            price=last_price,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            rsi_14=None,
            rsi_10=None,
            rsi_21=None,
            current_price=Decimal(str(last_price)),
            data_source="real_market_data",
            metadata={"value": last_price},
        )

    def _compute_moving_average(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute moving average indicator."""
        window = int(parameters.get("window", 200))

        # Validate sufficient data before computation
        if len(prices) < window:
            raise IndicatorComputationError(
                f"Insufficient data for {symbol}: need {window} bars, have {len(prices)} bars"
            )

        ma_series = self.technical_indicators.moving_average(prices, window=window)

        latest_ma = float(ma_series.iloc[-1]) if len(ma_series) > 0 else None
        if latest_ma is None or pd.isna(latest_ma):
            logger.error(
                "Moving average computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(
                f"No moving average available for {symbol} window={window}"
            )

        logger.debug(
            "Moving average computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            ma_value=latest_ma,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            ma_20=latest_ma if window == 20 else None,
            ma_50=latest_ma if window == 50 else None,
            ma_200=latest_ma if window == 200 else None,
            data_source="real_market_data",
            metadata={"value": latest_ma, "window": window},
        )

    def _compute_moving_average_return(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute moving average return indicator."""
        window = int(parameters.get("window", 21))
        mar_series = self.technical_indicators.moving_average_return(prices, window=window)

        latest = float(mar_series.iloc[-1]) if len(mar_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "Moving average return computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(
                f"No moving average return for {symbol} window={window}"
            )

        logger.debug(
            "Moving average return computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            ma_return_90=latest if window == 90 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _compute_cumulative_return(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute cumulative return indicator."""
        window = int(parameters.get("window", 60))
        cum_series = self.technical_indicators.cumulative_return(prices, window=window)

        latest = float(cum_series.iloc[-1]) if len(cum_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "Cumulative return computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(f"No cumulative return for {symbol} window={window}")

        logger.debug(
            "Cumulative return computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            cum_return_60=latest if window == 60 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _compute_ema(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute exponential moving average indicator."""
        window = int(parameters.get("window", 12))
        ema_series = self.technical_indicators.exponential_moving_average(prices, window=window)

        latest = float(ema_series.iloc[-1]) if len(ema_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "EMA computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(f"No EMA available for {symbol} window={window}")

        logger.debug(
            "EMA computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            ema_12=latest if window == 12 else None,
            ema_26=latest if window == 26 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _compute_stdev_return(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute standard deviation return indicator."""
        window = int(parameters.get("window", 6))
        std_series = self.technical_indicators.stdev_return(prices, window=window)

        latest = float(std_series.iloc[-1]) if len(std_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "Standard deviation return computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(f"No stdev-return for {symbol} window={window}")

        logger.debug(
            "Standard deviation return computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            stdev_return_6=latest if window == 6 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _compute_max_drawdown(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute maximum drawdown indicator."""
        window = int(parameters.get("window", 60))
        mdd_series = self.technical_indicators.max_drawdown(prices, window=window)

        latest = float(mdd_series.iloc[-1]) if len(mdd_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "Max drawdown computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise IndicatorComputationError(f"No max-drawdown for {symbol} window={window}")

        logger.debug(
            "Max drawdown computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _required_bars(self, ind_type: str, params: dict[str, int | float | str]) -> int:
        """Compute required bars based on indicator type and parameters."""
        window = int(params.get("window", 0)) if params else 0
        if ind_type in {
            "moving_average",
            "exponential_moving_average_price",
            "max_drawdown",
        }:
            return max(window, 200)
        if ind_type in {
            "moving_average_return",
            "stdev_return",
            "cumulative_return",
        }:
            return max(window + 5, 60)
        if ind_type == "rsi":
            return max(window * 3 if window > 0 else 200, 200)
        if ind_type == "current_price":
            return 1
        return 252  # sensible default (~1Y)

    def _period_for_bars(self, required_bars: int) -> str:
        """Convert required trading bars to calendar period string."""
        bars_with_buffer = math.ceil(required_bars * 1.1)
        years = max(1, math.ceil(bars_with_buffer / 252))
        return f"{years}Y"

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Get technical indicator for symbol using real market data.

        Args:
            request: Indicator request containing symbol, type, and parameters

        Returns:
            TechnicalIndicator with computed indicator data

        Raises:
            IndicatorComputationError: If indicator computation fails
            MarketDataError: If market data retrieval fails

        """
        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters
        correlation_id = request.correlation_id

        logger.info(
            "Indicator request received",
            module=MODULE_NAME,
            symbol=symbol,
            indicator_type=indicator_type,
            correlation_id=correlation_id,
        )

        # Require real market data; no mocks
        if not self.market_data_service:
            logger.error(
                "No market data service configured",
                module=MODULE_NAME,
                symbol=symbol,
                indicator_type=indicator_type,
                correlation_id=correlation_id,
            )
            raise IndicatorComputationError(
                "IndicatorService requires a MarketDataPort; no fallback indicators allowed"
            )

        try:
            # Compute dynamic lookback and fetch market data
            required = self._required_bars(indicator_type, parameters)
            period = self._period_for_bars(required)

            logger.debug(
                "Fetching market data",
                module=MODULE_NAME,
                symbol=symbol,
                required_bars=required,
                period=period,
                correlation_id=correlation_id,
            )

            # Fetch bars with computed lookback
            symbol_obj = Symbol(symbol)
            bars = self.market_data_service.get_bars(
                symbol=symbol_obj,
                period=period,
                timeframe="1Day",
            )

            if not bars:
                logger.error(
                    "No market data available",
                    module=MODULE_NAME,
                    symbol=symbol,
                    period=period,
                    correlation_id=correlation_id,
                )
                raise MarketDataError(
                    f"No market data available for symbol {symbol}",
                    symbol=symbol,
                )

            logger.debug(
                "Market data fetched",
                module=MODULE_NAME,
                symbol=symbol,
                bars_count=len(bars),
                correlation_id=correlation_id,
            )

            # Convert bars to pandas Series for technical indicators
            prices = pd.Series([float(bar.close) for bar in bars])

            # Dispatch to appropriate indicator computation method
            indicator_dispatch = {
                "rsi": self._compute_rsi,
                "current_price": self._compute_current_price,
                "moving_average": self._compute_moving_average,
                "moving_average_return": self._compute_moving_average_return,
                "cumulative_return": self._compute_cumulative_return,
                "exponential_moving_average_price": self._compute_ema,
                "stdev_return": self._compute_stdev_return,
                "max_drawdown": self._compute_max_drawdown,
            }

            if indicator_type in indicator_dispatch:
                result = indicator_dispatch[indicator_type](symbol, prices, parameters)
                logger.info(
                    "Indicator computed successfully",
                    module=MODULE_NAME,
                    symbol=symbol,
                    indicator_type=indicator_type,
                    correlation_id=correlation_id,
                )
                return result

            # Unsupported indicator types
            logger.error(
                "Unsupported indicator type",
                module=MODULE_NAME,
                symbol=symbol,
                indicator_type=indicator_type,
                correlation_id=correlation_id,
            )
            raise IndicatorComputationError(f"Unsupported indicator type: {indicator_type}")

        except IndicatorComputationError:
            raise
        except MarketDataError:
            raise
        except Exception as e:
            logger.error(
                "Indicator computation error",
                module=MODULE_NAME,
                symbol=symbol,
                indicator_type=indicator_type,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            raise IndicatorComputationError(
                f"Error getting indicator {indicator_type} for {symbol}: {e}"
            ) from e
