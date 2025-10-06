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

from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError
from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators


class IndicatorService:
    """Service for computing technical indicators using real market data.

    Integrates with the existing market data infrastructure to provide
    real-time technical indicator calculations for DSL strategy evaluation.
    """

    def __init__(self, market_data_service: MarketDataPort | None) -> None:
        """Initialize indicator service with market data provider.

        Args:
            market_data_service: MarketDataService instance for real market data (None for fallback)

        """
        self.market_data_service = market_data_service
        # Always initialize indicators; data access is gated separately by market_data_service
        self.technical_indicators: TechnicalIndicators = TechnicalIndicators()

    def _latest_value(self, series: pd.Series, fallback: float) -> float:
        """Safely get the latest value from a pandas series with fallback."""
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

        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            rsi_14=rsi_value if window == 14 else None,
            rsi_10=rsi_value if window == 10 else None,
            rsi_20=rsi_value if window == 20 else None,
            rsi_21=rsi_value if window == 21 else None,
            current_price=(
                Decimal(str(prices.iloc[-1])) if len(prices) > 0 else Decimal("100.0")
            ),
            data_source="real_market_data",
            metadata={"value": rsi_value, "window": window},
        )

    def _compute_current_price(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute current price indicator."""
        last_price = float(prices.iloc[-1]) if len(prices) > 0 else None
        if last_price is None:
            raise DslEvaluationError(f"No last price for symbol {symbol}")

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
            raise DslEvaluationError(
                f"Insufficient data for {symbol}: need {window} bars, have {len(prices)} bars"
            )

        ma_series = self.technical_indicators.moving_average(prices, window=window)

        latest_ma = float(ma_series.iloc[-1]) if len(ma_series) > 0 else None
        if latest_ma is None or pd.isna(latest_ma):
            raise DslEvaluationError(
                f"No moving average available for {symbol} window={window} (need {window} bars, have {len(prices)})"
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
        mar_series = self.technical_indicators.moving_average_return(
            prices, window=window
        )

        latest = float(mar_series.iloc[-1]) if len(mar_series) > 0 else None
        if latest is None or pd.isna(latest):
            raise DslEvaluationError(
                f"No moving average return for {symbol} window={window}"
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
            raise DslEvaluationError(
                f"No cumulative return for {symbol} window={window}"
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
        ema_series = self.technical_indicators.exponential_moving_average(
            prices, window=window
        )

        latest = float(ema_series.iloc[-1]) if len(ema_series) > 0 else None
        if latest is None or pd.isna(latest):
            raise DslEvaluationError(f"No EMA available for {symbol} window={window}")
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
            raise DslEvaluationError(f"No stdev-return for {symbol} window={window}")
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            stdev_return_6=latest if window == 6 else None,
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def _required_bars(
        self, ind_type: str, params: dict[str, int | float | str]
    ) -> int:
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
            # Need at least window plus some extra for pct_change/shift stability
            return max(window + 5, 60)
        if ind_type == "rsi":
            # RSI stabilizes with more data; fetch ~3x window (min 200)
            return max(window * 3 if window > 0 else 200, 200)
        if ind_type == "current_price":
            return 1
        return 252  # sensible default (~1Y)

    def _period_for_bars(self, required_bars: int) -> str:
        """Convert required trading bars to calendar period string."""
        # Use years granularity to avoid weekend/holiday gaps; add 50% safety margin
        # for backtesting to ensure we have sufficient historical data before the backtest period
        bars_with_buffer = math.ceil(required_bars * 1.5)
        years = max(
            2, math.ceil(bars_with_buffer / 252)
        )  # Minimum 2 years for reliable indicators
        return f"{years}Y"

    def _compute_max_drawdown(
        self, symbol: str, prices: pd.Series, parameters: dict[str, int | float | str]
    ) -> TechnicalIndicator:
        """Compute maximum drawdown indicator."""
        window = int(parameters.get("window", 60))
        mdd_series = self.technical_indicators.max_drawdown(prices, window=window)

        latest = float(mdd_series.iloc[-1]) if len(mdd_series) > 0 else None
        if latest is None or pd.isna(latest):
            raise DslEvaluationError(f"No max-drawdown for {symbol} window={window}")
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
            data_source="real_market_data",
            metadata={"value": latest, "window": window},
        )

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Get technical indicator for symbol using real market data.

        Args:
            request: Indicator request

        Returns:
            TechnicalIndicator with real indicator data

        """
        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters

        # Require real market data; no mocks
        if not self.market_data_service:
            raise DslEvaluationError(
                "IndicatorService requires a MarketDataPort; no fallback indicators allowed"
            )

        try:
            # Compute dynamic lookback and fetch market data
            required = self._required_bars(indicator_type, parameters)
            period = self._period_for_bars(required)

            # Fetch bars with computed lookback
            symbol_obj = Symbol(symbol)
            bars = self.market_data_service.get_bars(
                symbol=symbol_obj,
                period=period,
                timeframe="1Day",
            )

            if not bars:
                raise DslEvaluationError(
                    f"No market data available for symbol {symbol}"
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
                return indicator_dispatch[indicator_type](symbol, prices, parameters)

            # Unsupported indicator types
            raise DslEvaluationError(f"Unsupported indicator type: {indicator_type}")

        except Exception as e:
            raise DslEvaluationError(
                f"Error getting indicator {indicator_type} for {symbol}: {e}"
            ) from e
