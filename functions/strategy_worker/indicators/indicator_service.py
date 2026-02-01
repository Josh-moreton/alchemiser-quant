#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Indicator service for computing technical indicators using real market data.

Integrates with the existing market data infrastructure to provide
real-time technical indicator calculations for DSL strategy evaluation.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from engines.dsl.types import DslEvaluationError
from errors import MarketDataError
from indicators.indicators import TechnicalIndicators

from the_alchemiser.shared.indicators.partial_bar_config import should_use_live_bar
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = get_logger(__name__)

# Module constant for logging context
MODULE_NAME = "strategy_v2.indicators"


class IndicatorService:
    """Service for computing technical indicators using real market data.

    Integrates with the existing market data infrastructure to provide
    real-time technical indicator calculations for DSL strategy evaluation.

    Attributes:
        market_data_service: Market data provider for fetching historical bars
        technical_indicators: Technical indicator computation engine

    """

    def __init__(self, market_data_service: MarketDataPort | None) -> None:
        """Initialize indicator service with market data provider.

        Args:
            market_data_service: MarketDataService instance for real market data.
                None is allowed only for testing; production code must provide a service.

        Raises:
            None. Validation occurs at usage time via get_indicator method.

        """
        self.market_data_service = market_data_service
        # Always initialize indicators; data access is gated separately by market_data_service
        self.technical_indicators: TechnicalIndicators = TechnicalIndicators()
        logger.info(
            "IndicatorService initialized",
            module=MODULE_NAME,
            has_market_data_service=market_data_service is not None,
        )

    def _latest_value(
        self, series: pd.Series, fallback: float | None = None
    ) -> tuple[float | None, bool]:
        """Safely get the latest value from a pandas series with fallback tracking.

        Args:
            series: Pandas series containing computed indicator values
            fallback: Fallback value to return if series is empty or contains NaN.
                      If None, returns None when data is unavailable.

        Returns:
            Tuple of (value, fallback_used) where:
            - value: Latest non-NaN value from series, or fallback if unavailable
            - fallback_used: True if fallback was used instead of real data

        Note:
            REM-005: Now tracks when fallback is used so callers can distinguish
            real data from synthetic values.

        """
        if len(series) > 0 and not pd.isna(series.iloc[-1]):
            return float(series.iloc[-1]), False
        return fallback, True

    def _compute_rsi(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute RSI indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for RSI computation
            parameters: Indicator parameters, including 'window' (default: 14)

        Returns:
            TechnicalIndicator with RSI value in appropriate field based on window.
            RSI value will be None if insufficient data (not neutral 50.0).

        Note:
            REM-005: Changed from returning 50.0 fallback to None when data is
            insufficient. Strategies must handle None RSI explicitly.
            REM-007: Changed from $100.0 price fallback to None.

        """
        window = int(parameters.get("window", 14))
        rsi_series = self.technical_indicators.rsi(prices, window=window)
        rsi_value, fallback_used = self._latest_value(
            rsi_series, None
        )  # REM-005: None instead of 50.0

        if fallback_used:
            logger.warning(
                "RSI using fallback value due to insufficient data",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
                prices_available=len(prices),
                fallback_used=True,
            )
        else:
            # DEBUG: Enhanced logging for signal divergence investigation
            logger.info(
                "RSI_DEBUG: computed value",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
                rsi_value=round(rsi_value, 4) if rsi_value else None,
                last_5_prices=[round(float(p), 2) for p in prices.iloc[-5:].tolist()],
                prices_count=len(prices),
            )

        # REM-007: Return None for price if no data, not $100.0
        current_price = Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            rsi_14=rsi_value if window == 14 else None,
            rsi_10=rsi_value if window == 10 else None,
            rsi_20=rsi_value if window == 20 else None,
            rsi_21=rsi_value if window == 21 else None,
            current_price=current_price,
            data_source="real_market_data" if not fallback_used else "fallback",
            metadata={
                "value": rsi_value if rsi_value is not None else 0.0,
                "window": window,
                "fallback_used": fallback_used,
            },
        )

    def _compute_current_price(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute current price indicator.

        Args:
            symbol: Trading symbol
            prices: Price series (must contain at least one value)
            parameters: Indicator parameters (unused for current_price)

        Returns:
            TechnicalIndicator with current price

        Raises:
            DslEvaluationError: If prices series is empty or contains no valid data

        """
        last_price = float(prices.iloc[-1]) if len(prices) > 0 else None
        if last_price is None:
            logger.error(
                "No last price available",
                module=MODULE_NAME,
                symbol=symbol,
            )
            raise DslEvaluationError(f"No last price for symbol {symbol}")

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
        """Compute moving average indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for moving average computation
            parameters: Indicator parameters, including 'window' (default: 200)

        Returns:
            TechnicalIndicator with moving average value

        Raises:
            DslEvaluationError: If moving average cannot be computed or is NaN

        """
        window = int(parameters.get("window", 200))

        # Validate sufficient data before computation
        if len(prices) < window:
            raise DslEvaluationError(
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
            raise DslEvaluationError(f"No moving average available for {symbol} window={window}")

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
        """Compute moving average return indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for return computation
            parameters: Indicator parameters, including 'window' (default: 21)

        Returns:
            TechnicalIndicator with moving average return value

        Raises:
            DslEvaluationError: If return cannot be computed or is NaN

        """
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
            raise DslEvaluationError(f"No moving average return for {symbol} window={window}")

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
        """Compute cumulative return indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for return computation
            parameters: Indicator parameters, including 'window' (default: 60)

        Returns:
            TechnicalIndicator with cumulative return value

        Raises:
            DslEvaluationError: If return cannot be computed or is NaN

        """
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
            raise DslEvaluationError(f"No cumulative return for {symbol} window={window}")

        # DEBUG: Enhanced logging for signal divergence investigation
        reference_price = float(prices.iloc[-window - 1]) if len(prices) > window else None
        current_price = float(prices.iloc[-1]) if len(prices) > 0 else None
        logger.info(
            "CUMRET_DEBUG: computed value",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            cumulative_return_pct=round(latest, 4),
            current_price=round(current_price, 2) if current_price else None,
            reference_price=round(reference_price, 2) if reference_price else None,
            prices_count=len(prices),
            calculation_method="(current/reference - 1) * 100",
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
        """Compute exponential moving average indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for EMA computation
            parameters: Indicator parameters, including 'window' (default: 12)

        Returns:
            TechnicalIndicator with EMA value

        Raises:
            DslEvaluationError: If EMA cannot be computed or is NaN

        """
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
            raise DslEvaluationError(f"No EMA available for {symbol} window={window}")

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
        """Compute standard deviation return indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for standard deviation computation
            parameters: Indicator parameters, including 'window' (default: 6)

        Returns:
            TechnicalIndicator with standard deviation of returns

        Raises:
            DslEvaluationError: If standard deviation cannot be computed or is NaN

        """
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
            raise DslEvaluationError(f"No stdev-return for {symbol} window={window}")

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

    def _compute_stdev_price(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute standard deviation of raw prices indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for standard deviation computation
            parameters: Indicator parameters, including 'window' (default: 6)

        Returns:
            TechnicalIndicator with standard deviation of prices

        Raises:
            DslEvaluationError: If standard deviation cannot be computed or is NaN

        """
        window = int(parameters.get("window", 6))
        std_series = self.technical_indicators.stdev_price(prices, window=window)

        latest = float(std_series.iloc[-1]) if len(std_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "Standard deviation price computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                window=window,
            )
            raise DslEvaluationError(f"No stdev-price for {symbol} window={window}")

        logger.debug(
            "Standard deviation price computed",
            module=MODULE_NAME,
            symbol=symbol,
            window=window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            stdev_price_6=latest if window == 6 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _required_bars(self, ind_type: str, params: dict[str, int | float | str]) -> int:
        """Compute required bars based on indicator type and parameters.

        Args:
            ind_type: Type of indicator (e.g., 'rsi', 'moving_average')
            params: Indicator parameters dictionary, may contain 'window'

        Returns:
            Number of bars required for stable indicator computation

        Note:
            Returns conservative estimates to ensure sufficient data for reliable
            indicator calculations. Different indicator types have different
            warm-up requirements.

        """
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
            "stdev_price",
            "cumulative_return",
        }:
            # Need at least window plus some extra for pct_change/shift stability
            return max(window + 5, 60)
        if ind_type == "rsi":
            # RSI stabilizes with more data; fetch ~3x window (min 200)
            return max(window * 3 if window > 0 else 200, 200)
        if ind_type == "current_price":
            return 1
        if ind_type in {"percentage_price_oscillator", "percentage_price_oscillator_signal"}:
            # PPO uses EMA(long) + EMA(short) + optional signal smoothing
            long_window = int(params.get("long_window", 26)) if params else 26
            smooth_window = int(params.get("smooth_window", 9)) if params else 9
            # Need at least long_window + smooth_window + buffer for stability
            return max(long_window + smooth_window + 20, 100)
        return 252  # sensible default (~1Y)

    def _period_for_bars(self, required_bars: int) -> str:
        """Convert required trading bars to calendar period string.

        Args:
            required_bars: Number of trading days needed

        Returns:
            Period string in format suitable for market data API (e.g., "1Y", "2Y")

        Note:
            Assumes ~252 trading days per year. Adds 10% safety margin to account
            for weekends, holidays, and market closures.

        """
        # Use years granularity to avoid weekend/holiday gaps; add 10% safety margin
        bars_with_buffer = math.ceil(required_bars * 1.1)
        years = max(1, math.ceil(bars_with_buffer / 252))
        return f"{years}Y"

    def _compute_max_drawdown(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute maximum drawdown indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for drawdown computation
            parameters: Indicator parameters, including 'window' (default: 60)

        Returns:
            TechnicalIndicator with maximum drawdown value

        Raises:
            DslEvaluationError: If drawdown cannot be computed or is NaN

        """
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
            raise DslEvaluationError(f"No max-drawdown for {symbol} window={window}")

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

    def _compute_ppo(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute Percentage Price Oscillator indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for PPO computation
            parameters: Indicator parameters, including 'short_window' (12)
                and 'long_window' (26)

        Returns:
            TechnicalIndicator with PPO value in metadata

        Raises:
            DslEvaluationError: If PPO cannot be computed or is NaN

        """
        short_window = int(parameters.get("short_window", 12))
        long_window = int(parameters.get("long_window", 26))
        ppo_series = self.technical_indicators.percentage_price_oscillator(
            prices, short_window=short_window, long_window=long_window
        )

        latest = float(ppo_series.iloc[-1]) if len(ppo_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "PPO computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                short_window=short_window,
                long_window=long_window,
            )
            raise DslEvaluationError(f"No PPO for {symbol} short={short_window} long={long_window}")

        logger.debug(
            "PPO computed",
            module=MODULE_NAME,
            symbol=symbol,
            short_window=short_window,
            long_window=long_window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            data_source="real_market_data",
            metadata={
                "value": latest,
                "short_window": short_window,
                "long_window": long_window,
            },
        )

    def _compute_ppo_signal(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute PPO Signal Line indicator.

        Args:
            symbol: Trading symbol
            prices: Price series for PPO signal computation
            parameters: Indicator parameters, including 'short_window' (12),
                'long_window' (26), and 'smooth_window' (9)

        Returns:
            TechnicalIndicator with PPO signal value in metadata

        Raises:
            DslEvaluationError: If PPO signal cannot be computed or is NaN

        """
        short_window = int(parameters.get("short_window", 12))
        long_window = int(parameters.get("long_window", 26))
        smooth_window = int(parameters.get("smooth_window", 9))
        ppo_signal_series = self.technical_indicators.percentage_price_oscillator_signal(
            prices,
            short_window=short_window,
            long_window=long_window,
            smooth_window=smooth_window,
        )

        latest = float(ppo_signal_series.iloc[-1]) if len(ppo_signal_series) > 0 else None
        if latest is None or pd.isna(latest):
            logger.error(
                "PPO signal computation failed",
                module=MODULE_NAME,
                symbol=symbol,
                short_window=short_window,
                long_window=long_window,
                smooth_window=smooth_window,
            )
            raise DslEvaluationError(
                f"No PPO signal for {symbol} short={short_window} "
                f"long={long_window} smooth={smooth_window}"
            )

        logger.debug(
            "PPO signal computed",
            module=MODULE_NAME,
            symbol=symbol,
            short_window=short_window,
            long_window=long_window,
            smooth_window=smooth_window,
            value=latest,
        )

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            data_source="real_market_data",
            metadata={
                "value": latest,
                "short_window": short_window,
                "long_window": long_window,
                "smooth_window": smooth_window,
            },
        )

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Get technical indicator for symbol using real market data.

        Args:
            request: Indicator request containing symbol, type, and parameters

        Returns:
            TechnicalIndicator with computed indicator data

        Raises:
            DslEvaluationError: If indicator computation fails or data is unavailable
            MarketDataError: If market data retrieval fails

        Note:
            All market data operations must succeed; no fallback data is provided.
            Correlation IDs from request are propagated to logs for traceability.

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
            raise DslEvaluationError(
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
                indicator_type=indicator_type,
                correlation_id=correlation_id,
            )

            # Fetch bars with computed lookback using standard MarketDataPort interface
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

            # Strip live/partial bar if indicator shouldn't use it
            # This is controlled per-indicator in partial_bar_config.py
            use_live = should_use_live_bar(indicator_type)
            if not use_live and len(bars) > 1 and bars[-1].is_incomplete:
                logger.debug(
                    "Stripping live bar for indicator",
                    module=MODULE_NAME,
                    symbol=symbol,
                    indicator_type=indicator_type,
                    live_bar_close=float(bars[-1].close),
                    correlation_id=correlation_id,
                )
                bars = bars[:-1]

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
                "stdev_price": self._compute_stdev_price,
                "max_drawdown": self._compute_max_drawdown,
                "percentage_price_oscillator": self._compute_ppo,
                "percentage_price_oscillator_signal": self._compute_ppo_signal,
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
            raise DslEvaluationError(f"Unsupported indicator type: {indicator_type}")

        except DslEvaluationError:
            # Re-raise DslEvaluationError without wrapping
            raise
        except MarketDataError:
            # Re-raise MarketDataError without wrapping
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
            raise DslEvaluationError(
                f"Error getting indicator {indicator_type} for {symbol}: {e}"
            ) from e
