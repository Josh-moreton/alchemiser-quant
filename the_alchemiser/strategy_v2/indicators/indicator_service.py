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

from the_alchemiser.shared.dto.indicator_request_dto import IndicatorRequestDTO
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
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
        self.technical_indicators = TechnicalIndicators() if market_data_service else None

    def get_indicator(self, request: IndicatorRequestDTO) -> TechnicalIndicatorDTO:
        """Get technical indicator for symbol using real market data.

        Args:
            request: Indicator request

        Returns:
            TechnicalIndicatorDTO with real indicator data

        """
        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters

        # Require real market data; no mocks
        if not self.market_data_service or not self.technical_indicators:
            raise DslEvaluationError(
                "IndicatorService requires a MarketDataPort; no fallback indicators allowed"
            )

        try:
            # Compute dynamic lookback based on indicator/window to ensure enough bars
            def _required_bars(ind_type: str, params: dict[str, int | float | str]) -> int:
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

            def _period_for_bars(required_bars: int) -> str:
                # Convert required trading bars to calendar period string understood by MarketDataService
                # Use years granularity to avoid weekend/holiday gaps; add 10% safety margin
                bars_with_buffer = math.ceil(required_bars * 1.1)
                years = max(1, math.ceil(bars_with_buffer / 252))
                return f"{years}Y"

            required = _required_bars(indicator_type, parameters)
            period = _period_for_bars(required)

            # Fetch bars with computed lookback
            symbol_obj = Symbol(symbol)
            bars = self.market_data_service.get_bars(
                symbol=symbol_obj,
                period=period,
                timeframe="1Day",
            )

            if not bars:
                raise DslEvaluationError(f"No market data available for symbol {symbol}")

            # Convert bars to pandas Series for technical indicators
            import pandas as pd

            prices = pd.Series([float(bar.close) for bar in bars])

            if indicator_type == "rsi":
                window = parameters.get("window", 14)
                rsi_series = self.technical_indicators.rsi(prices, window=window)

                # Get the most recent RSI value
                if len(rsi_series) > 0 and not pd.isna(rsi_series.iloc[-1]):
                    rsi_value = float(rsi_series.iloc[-1])
                else:
                    rsi_value = 50.0  # Neutral fallback

                return TechnicalIndicatorDTO(
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
            if indicator_type == "current_price":
                last_price = float(prices.iloc[-1]) if len(prices) > 0 else None
                if last_price is None:
                    raise DslEvaluationError(f"No last price for symbol {symbol}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    rsi_14=None,
                    rsi_10=None,
                    rsi_21=None,
                    current_price=Decimal(str(last_price)),
                    data_source="real_market_data",
                    metadata={"value": last_price},
                )

            if indicator_type == "moving_average":
                window = int(parameters.get("window", 200))
                ma_series = self.technical_indicators.moving_average(prices, window=window)
                import pandas as pd

                latest_ma = float(ma_series.iloc[-1]) if len(ma_series) > 0 else None
                if latest_ma is None or pd.isna(latest_ma):
                    raise DslEvaluationError(
                        f"No moving average available for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    ma_20=latest_ma if window == 20 else None,
                    ma_50=latest_ma if window == 50 else None,
                    ma_200=latest_ma if window == 200 else None,
                    data_source="real_market_data",
                    metadata={"value": latest_ma, "window": window},
                )

            if indicator_type == "moving_average_return":
                window = int(parameters.get("window", 21))
                mar_series = self.technical_indicators.moving_average_return(prices, window=window)
                import pandas as pd

                latest = float(mar_series.iloc[-1]) if len(mar_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No moving average return for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    ma_return_90=latest if window == 90 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "cumulative_return":
                window = int(parameters.get("window", 60))
                cum_series = self.technical_indicators.cumulative_return(prices, window=window)
                import pandas as pd

                latest = float(cum_series.iloc[-1]) if len(cum_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(f"No cumulative return for {symbol} window={window}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    cum_return_60=latest if window == 60 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "exponential_moving_average_price":
                window = int(parameters.get("window", 12))
                ema_series = self.technical_indicators.exponential_moving_average(
                    prices, window=window
                )
                import pandas as pd

                latest = float(ema_series.iloc[-1]) if len(ema_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(f"No EMA available for {symbol} window={window}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    ema_12=latest if window == 12 else None,
                    ema_26=latest if window == 26 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "stdev_return":
                window = int(parameters.get("window", 6))
                std_series = self.technical_indicators.stdev_return(prices, window=window)
                import pandas as pd

                latest = float(std_series.iloc[-1]) if len(std_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(f"No stdev-return for {symbol} window={window}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    stdev_return_6=latest if window == 6 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "max_drawdown":
                window = int(parameters.get("window", 60))
                mdd_series = self.technical_indicators.max_drawdown(prices, window=window)
                import pandas as pd

                latest = float(mdd_series.iloc[-1]) if len(mdd_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(f"No max-drawdown for {symbol} window={window}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None),
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            # Unsupported indicator types
            raise DslEvaluationError(f"Unsupported indicator type: {indicator_type}")

        except Exception as e:
            raise DslEvaluationError(
                f"Error getting indicator {indicator_type} for {symbol}: {e}"
            ) from e