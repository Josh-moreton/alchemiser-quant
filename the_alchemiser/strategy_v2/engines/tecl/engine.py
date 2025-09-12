#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

TECL Strategy Engine.

Implements the "TECL For The Long Term (v7)" strategy from Composer.trade.
This strategy is designed for long-term technology leverage (TECL) with volatility protection.

Strategy Logic (translated from Clojure):
1. Market Regime Detection: SPY vs 200-day MA (bull vs bear market)
2. Volatility Protection: Multiple RSI-based triggers for defensive positions
3. Technology Focus: TECL as primary growth vehicle in appropriate conditions
4. Bond Hedge: BIL as defensive cash equivalent
5. Sector Rotation: XLK vs KMLM comparison for technology timing

Key Symbols:
- TECL: 3x leveraged technology ETF (primary growth vehicle)
- BIL: Short-term treasury bills (defensive cash equivalent)
- UVXY: Volatility hedge for extreme overbought conditions
- XLK: Technology sector ETF (timing signal)
- KMLM: Materials sector ETF (comparative signal)
- TQQQ, SPXL, SPY: Market timing indicators
- SQQQ: Inverse NASDAQ for bear market conditions
- BSV: Short-term bond ETF alternative
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.shared.config.confidence_config import ConfidenceConfig, TECLConfidenceConfig
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.shared.types import StrategyEngine, StrategySignal, Confidence
from the_alchemiser.strategy_v2.indicators.indicator_utils import safe_get_indicator
from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators
from the_alchemiser.strategy_v2.indicators.indicator_utils import safe_get_indicator
from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators

warnings.filterwarnings("ignore")


class TECLEngine(StrategyEngine):
    """TECL Strategy Engine - Long-term technology leverage with volatility protection."""

    def __init__(self, data_provider: MarketDataPort) -> None:
        """Initialize TECL strategy with typed MarketDataPort.

        Args:
            data_provider: Market data provider implementing MarketDataPort protocol

        """
        super().__init__("TECL", data_provider)
        self.data_provider = data_provider  # Keep for backward compatibility with existing methods
        self.indicators = TechnicalIndicators()
        self.confidence_config = ConfidenceConfig.default()

        # Core symbols used in TECL strategy
        self.market_symbols = ["SPY", "TQQQ", "SPXL"]
        self.tech_symbols = ["TECL", "XLK", "KMLM"]
        self.volatility_symbols = ["UVXY"]
        self.bond_symbols = ["BIL", "BSV"]
        self.inverse_symbols = ["SQQQ"]

        # All symbols needed for the strategy
        self.all_symbols = (
            self.market_symbols
            + self.tech_symbols
            + self.volatility_symbols
            + self.bond_symbols
            + self.inverse_symbols
        )

        logging.debug("TECLStrategyEngine initialized")

    def get_required_symbols(self) -> list[str]:
        """Return all symbols required by the TECL strategy."""
        return self.all_symbols

    def get_market_data(self) -> dict[str, Any]:
        """Fetch data for all symbols."""
        # TODO: Remove this deprecated mapping dependency
        # This should be replaced with direct DTO construction  
        # For now, we'll implement the required functionality directly
        def symbol_str_to_symbol(symbol_str: str):
            from the_alchemiser.shared.value_objects.symbol import Symbol
            return Symbol(symbol_str)
        
        def bars_to_dataframe(bars):
            # Simplified conversion - replace with proper implementation
            return pd.DataFrame(bars) if bars else pd.DataFrame()

        market_data = {}
        for symbol in self.all_symbols:
            try:
                symbol_obj = symbol_str_to_symbol(symbol)
                bars = self.data_provider.get_bars(symbol_obj, period="1y", timeframe="1day")
                data = bars_to_dataframe(bars)
                if not data.empty:
                    market_data[symbol] = data
                else:
                    logging.warning(f"Could not fetch data for {symbol}")
            except Exception as e:
                logging.warning(f"Failed to fetch data for {symbol}: {e}")
        return market_data

    def calculate_indicators(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate all technical indicators needed for TECL strategy."""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df["Close"]
            indicators[symbol] = {
                "rsi_9": safe_get_indicator(close, self.indicators.rsi, 9),
                "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                "rsi_20": safe_get_indicator(close, self.indicators.rsi, 20),
                "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                "ma_20": safe_get_indicator(close, self.indicators.moving_average, 20),
                "current_price": float(close.iloc[-1]),
            }
        return indicators

    def evaluate_tecl_strategy(
        self, indicators: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate the TECL (Technology) strategy with detailed reasoning.

        Returns: (recommended_symbol_or_allocation, action, detailed_reason)
        - For single symbols: returns symbol string
        - For multi-asset allocations: returns dict with symbol:weight pairs
        """
        if "SPY" not in indicators:
            return (
                "BIL",
                ActionType.HOLD.value,
                "Missing SPY data for market regime detection - cannot determine bull/bear market",
            )

        # Primary market regime detection: SPY vs 200 MA
        spy_price = indicators["SPY"]["current_price"]
        spy_ma_200 = indicators["SPY"]["ma_200"]
        spy_rsi = indicators["SPY"]["rsi_10"]

        market_analysis = "Market Regime Analysis:\n"
        market_analysis += f"• SPY Price: ${spy_price:.2f} vs 200MA: ${spy_ma_200:.2f}\n"
        market_analysis += f"• SPY RSI(10): {spy_rsi:.1f}\n"

        if spy_price > spy_ma_200:
            # BULL MARKET PATH
            market_analysis += "• Regime: BULL MARKET (SPY above 200MA)\n"
            return self._evaluate_bull_market_path(indicators, market_analysis)
        # BEAR MARKET PATH
        market_analysis += "• Regime: BEAR MARKET (SPY below 200MA)\n"
        return self._evaluate_bear_market_path(indicators, market_analysis)

    def _evaluate_bull_market_path(
        self, indicators: dict[str, Any], market_analysis: str
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate strategy when SPY is above 200-day MA (bull market)."""
        # First check: TQQQ overbought > 79 - Mixed allocation (25% UVXY + 75% BIL)
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] > 79:
            tqqq_rsi = indicators["TQQQ"]["rsi_10"]
            reasoning = f"{market_analysis}\n\nTechnology Overbought Signal:\n"
            reasoning += f"• TQQQ RSI(10): {tqqq_rsi:.1f} > 79 (overbought threshold)\n"
            reasoning += "• Strategy: Defensive hedge against tech weakness\n"
            reasoning += "• Allocation: UVXY 25% (volatility) + BIL 75% (cash)\n"
            reasoning += "• Rationale: Tech strength may reverse, partial protection needed"

            return {"UVXY": 0.25, "BIL": 0.75}, ActionType.BUY.value, reasoning

        # Second check: SPY overbought > 80 - Mixed allocation (25% UVXY + 75% BIL)
        if indicators["SPY"]["rsi_10"] > 80:
            spy_rsi = indicators["SPY"]["rsi_10"]
            reasoning = f"{market_analysis}\n\nMarket Overbought Signal:\n"
            reasoning += f"• SPY RSI(10): {spy_rsi:.1f} > 80 (high overbought threshold)\n"
            reasoning += "• Strategy: Broad market protection in bull market\n"
            reasoning += "• Allocation: UVXY 25% (volatility) + BIL 75% (cash)\n"
            reasoning += "• Rationale: Market stretched, preparing for pullback"

            return {"UVXY": 0.25, "BIL": 0.75}, ActionType.BUY.value, reasoning

        # Third check: KMLM Switcher logic
        return self._evaluate_kmlm_switcher(indicators, market_analysis, "Bull market")

    def _evaluate_bear_market_path(
        self, indicators: dict[str, Any], market_analysis: str
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate strategy when SPY is below 200-day MA (bear market)."""
        # First check: TQQQ oversold < 31 (buy the dip even in bear market)
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 31:
            tqqq_rsi = indicators["TQQQ"]["rsi_10"]
            reasoning = f"{market_analysis}\n\nOversold Dip-Buying Signal:\n"
            reasoning += f"• TQQQ RSI(10): {tqqq_rsi:.1f} < 31 (oversold)\n"
            reasoning += "• Strategy: Counter-trend tech dip buying in bear market\n"
            reasoning += "• Target: TECL (3x leveraged tech) for maximum bounce\n"
            reasoning += "• Rationale: Tech oversold provides opportunity even in bear market"

            return "TECL", ActionType.BUY.value, reasoning

        # Second check: SPXL oversold < 29
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 29:
            spxl_rsi = indicators["SPXL"]["rsi_10"]
            reasoning = f"{market_analysis}\n\nBroad Market Oversold Signal:\n"
            reasoning += f"• SPXL RSI(10): {spxl_rsi:.1f} < 29 (extremely oversold)\n"
            reasoning += "• Strategy: Leveraged S&P dip buying\n"
            reasoning += "• Target: SPXL (3x S&P 500) for oversold bounce\n"
            reasoning += "• Rationale: Extreme oversold conditions create opportunity"

            return "SPXL", ActionType.BUY.value, reasoning

        # Third check: UVXY volatility conditions
        if "UVXY" in indicators:
            uvxy_rsi = indicators["UVXY"]["rsi_10"]

            if uvxy_rsi > 84:
                # Extreme UVXY spike - mixed position (15% UVXY + 85% BIL)
                reasoning = f"{market_analysis}\n\nExtreme Volatility Spike:\n"
                reasoning += f"• UVXY RSI(10): {uvxy_rsi:.1f} > 84 (extreme spike)\n"
                reasoning += "• Strategy: Volatility momentum + defensive cash\n"
                reasoning += "• Allocation: UVXY 15% (volatility) + BIL 85% (cash)\n"
                reasoning += "• Rationale: Ride volatility spike while staying defensive"

                return {"UVXY": 0.15, "BIL": 0.85}, ActionType.BUY.value, reasoning
            if uvxy_rsi > 74:
                # High UVXY - defensive
                reasoning = f"{market_analysis}\n\nHigh Volatility Environment:\n"
                reasoning += f"• UVXY RSI(10): {uvxy_rsi:.1f} > 74 (elevated)\n"
                reasoning += "• Strategy: Full defensive positioning\n"
                reasoning += "• Target: BIL (cash equivalent) for capital preservation\n"
                reasoning += "• Rationale: High volatility suggests more downside risk"

                return "BIL", ActionType.BUY.value, reasoning

        # Fourth check: KMLM Switcher for bear market
        return self._evaluate_kmlm_switcher(indicators, market_analysis, "Bear market")

    def _evaluate_kmlm_switcher(
        self, indicators: dict[str, Any], market_analysis: str, market_regime: str
    ) -> tuple[str | dict[str, float], str, str]:
        """KMLM Switcher logic: Compare XLK vs KMLM RSI to determine technology timing.

        This is the core technology timing mechanism of the strategy.
        """
        if "XLK" not in indicators or "KMLM" not in indicators:
            reasoning = f"{market_analysis}\n\nKMLM Switcher - Data Missing:\n"
            reasoning += "• Missing XLK and/or KMLM technical data\n"
            reasoning += "• Cannot perform technology vs materials comparison\n"
            reasoning += "• Strategy: Full defensive cash position\n"
            reasoning += "• Target: BIL (cash equivalent) for capital preservation"

            return "BIL", ActionType.BUY.value, reasoning

        xlk_rsi = indicators["XLK"]["rsi_10"]
        kmlm_rsi = indicators["KMLM"]["rsi_10"]

        # Debug logging for RSI comparison
        logging.debug(f"KMLM Switcher - XLK RSI(10) = {xlk_rsi:.2f}, KMLM RSI(10) = {kmlm_rsi:.2f}")

        switcher_analysis = f"{market_analysis}\n\nKMLM Switcher Analysis:\n"
        switcher_analysis += f"• XLK (Technology) RSI(10): {xlk_rsi:.1f}\n"
        switcher_analysis += f"• KMLM (Materials) RSI(10): {kmlm_rsi:.1f}\n"

        if xlk_rsi > kmlm_rsi:
            # Technology (XLK) is stronger than materials (KMLM)
            switcher_analysis += "• Sector Comparison: Technology STRONGER than Materials\n"

            if xlk_rsi > 81:
                # XLK extremely overbought - defensive
                reasoning = f"{switcher_analysis}• XLK Status: Extremely overbought (>81)\n"
                reasoning += "• Strategy: Defensive despite tech strength\n"
                reasoning += "• Target: BIL (cash) - tech too extended for entry\n"
                reasoning += "• Rationale: Tech leadership unsustainable at extreme levels"

                logging.debug(f"XLK extremely overbought: {xlk_rsi:.2f} > 81")
                return "BIL", ActionType.BUY.value, reasoning
            # XLK strong but not extreme - buy technology
            reasoning = f"{switcher_analysis}• XLK Status: Strong but sustainable (<81)\n"
            reasoning += "• Strategy: Technology momentum play\n"
            reasoning += "• Target: TECL (3x leveraged tech) for sector strength\n"
            reasoning += "• Rationale: Tech outperforming materials, trend continuation"

            logging.debug(f"XLK stronger than KMLM: {xlk_rsi:.2f} > {kmlm_rsi:.2f}")
            return "TECL", ActionType.BUY.value, reasoning

        # Materials (KMLM) is stronger than technology (XLK)
        switcher_analysis += "• Sector Comparison: Materials STRONGER than Technology\n"

        if xlk_rsi < 29:
            # XLK oversold - buy the dip
            reasoning = f"{switcher_analysis}• XLK Status: Oversold (<29) despite weakness\n"
            reasoning += "• Strategy: Counter-trend tech dip buying\n"
            reasoning += "• Target: TECL (3x leveraged tech) for oversold bounce\n"
            reasoning += "• Rationale: Tech oversold creates opportunity despite sector weakness"

            logging.debug(f"XLK oversold: {xlk_rsi:.2f} < 29")
            return "TECL", ActionType.BUY.value, reasoning
        # XLK weak - return BIL directly in bull market, use selection in bear market
        logging.debug(f"KMLM stronger than XLK: {kmlm_rsi:.2f} > {xlk_rsi:.2f}")
        if market_regime == "Bull market":
            reasoning = f"{switcher_analysis}• Tech Status: Weak relative to materials\n"
            reasoning += "• Strategy: Defensive positioning in bull market\n"
            reasoning += "• Target: BIL (cash) - avoid weak tech sector\n"
            reasoning += "• Rationale: Materials strength suggests rotation away from tech"

            return "BIL", ActionType.BUY.value, reasoning
        # Bear market - use bond vs short selection
        return self._evaluate_bond_vs_short_selection(indicators, switcher_analysis, market_regime)

    def _evaluate_bond_vs_short_selection(
        self, indicators: dict[str, Any], switcher_analysis: str, market_regime: str
    ) -> tuple[str | dict[str, float], str, str]:
        """Final selection between bonds and short positions using RSI filter mechanism.
        This implements the filter/select-top logic from the Clojure version.
        """
        # Create candidate list with their RSI(9) values
        candidates = []

        if "SQQQ" in indicators:
            candidates.append(("SQQQ", indicators["SQQQ"]["rsi_9"]))

        if "BSV" in indicators:
            candidates.append(("BSV", indicators["BSV"]["rsi_9"]))

        if not candidates:
            reasoning = f"{switcher_analysis}• Final Selection: No SQQQ/BSV data available\n"
            reasoning += "• Strategy: Default to cash position\n"
            reasoning += "• Target: BIL (cash equivalent)\n"
            reasoning += "• Rationale: Cannot execute bond vs short selection without data"

            return "BIL", ActionType.BUY.value, reasoning

        # Select the candidate with the highest RSI(9) - "select-top 1" from Clojure
        best_candidate = max(candidates, key=lambda x: x[1])
        symbol, rsi_value = best_candidate

        candidate_desc = ", ".join([f"{sym} (RSI9: {rsi:.1f})" for sym, rsi in candidates])

        reasoning = f"{switcher_analysis}• Final Selection Process: Bond vs Short Selection\n"
        reasoning += f"• Candidates: {candidate_desc}\n"
        reasoning += "• Selection Rule: Highest RSI(9) value\n"
        reasoning += f"• Winner: {symbol} with RSI(9) {rsi_value:.1f}\n"
        reasoning += "• Rationale: Mean reversion play - buy strength in bear market"

        return symbol, ActionType.BUY.value, reasoning

    def _calculate_confidence(
        self, symbol: str, action: str, indicators: dict[str, Any], reasoning: str
    ) -> Confidence:
        """Calculate confidence based on market indicators and signal strength.

        Replaces the fixed 0.8 confidence with indicator-driven calculation.

        Args:
            symbol: Target symbol for the signal
            action: Action type (BUY/SELL/HOLD)
            indicators: Dictionary of calculated indicators
            reasoning: Signal reasoning for additional context

        Returns:
            Confidence object with calculated value

        """
        config = self.confidence_config.tecl
        confidence = config.base_confidence

        # Check for defensive/hold positions (lower confidence)
        is_defensive = symbol in ["BIL", "BSV"] or "defensive" in reasoning.lower()
        if is_defensive or action == "HOLD":
            confidence -= config.defensive_penalty

        # RSI-based confidence adjustments
        rsi_boost = self._calculate_rsi_confidence_boost(indicators, config)
        confidence += rsi_boost

        # Moving average distance boost
        ma_boost = self._calculate_ma_confidence_boost(indicators, config)
        confidence += ma_boost

        # Clamp to valid range
        confidence = max(config.min_confidence, min(config.max_confidence, confidence))

        return Confidence(confidence)

    def _calculate_rsi_confidence_boost(
        self, indicators: dict[str, Any], config: TECLConfidenceConfig
    ) -> Decimal:
        """Calculate confidence boost based on RSI extremes across key symbols."""
        max_boost = Decimal("0")

        # Check RSI for key symbols
        key_symbols = ["SPY", "TQQQ", "XLK", "TECL"]

        for symbol in key_symbols:
            if symbol not in indicators:
                continue

            symbol_indicators = indicators[symbol]
            rsi_10 = symbol_indicators.get("rsi_10")

            if rsi_10 is None:
                continue

            rsi_val = Decimal(str(rsi_10))

            # Extreme RSI conditions (> 80 or < 20)
            extreme_low = Decimal("100") - config.rsi_extreme_threshold
            if rsi_val > config.rsi_extreme_threshold or rsi_val < extreme_low:
                max_boost = max(max_boost, config.rsi_extreme_boost)
            else:
                # Moderate RSI conditions (> 70 or < 30)
                moderate_low = Decimal("100") - config.rsi_moderate_threshold
                if rsi_val > config.rsi_moderate_threshold or rsi_val < moderate_low:
                    max_boost = max(max_boost, config.rsi_moderate_boost)

        return max_boost

    def _calculate_ma_confidence_boost(
        self, indicators: dict[str, Any], config: TECLConfidenceConfig
    ) -> Decimal:
        """Calculate confidence boost based on distance from moving averages."""
        max_boost = Decimal("0")

        # Check MA distance for market timing symbols
        key_symbols = ["SPY", "TQQQ"]

        for symbol in key_symbols:
            if symbol not in indicators:
                continue

            symbol_indicators = indicators[symbol]
            current_price = symbol_indicators.get("current_price")
            ma_200 = symbol_indicators.get("ma_200")

            if current_price is None or ma_200 is None:
                continue

            # Calculate percentage distance from MA
            price_decimal = Decimal(str(current_price))
            ma_decimal = Decimal(str(ma_200))

            if ma_decimal > 0:
                distance = abs(price_decimal - ma_decimal) / ma_decimal
                if distance > config.ma_distance_threshold:
                    max_boost = max(max_boost, config.ma_distance_boost)

        return max_boost

    def generate_signals(self, now: datetime) -> list[StrategySignal]:
        """Generate typed strategy signals (new typed interface).

        Args:
            now: Current timestamp for signal generation

        Returns:
            List of StrategySignal objects with typed domain values

        """
        try:
            # Get market data and indicators
            market_data = self.get_market_data()
            if not market_data:
                return []

            indicators = self.calculate_indicators(market_data)
            if not indicators:
                return []

            # Get strategy recommendation
            symbol_or_allocation, action, reasoning = self.evaluate_tecl_strategy(
                indicators, market_data
            )

            # Convert to typed signals
            signals = []

            if isinstance(symbol_or_allocation, dict):
                # Portfolio allocation - create a single signal representing the portfolio
                # Use the largest allocation as the primary symbol
                primary_symbol = max(
                    symbol_or_allocation.keys(), key=lambda s: symbol_or_allocation[s]
                )
                total_allocation = sum(symbol_or_allocation.values())

                signal = StrategySignal(
                    symbol=Symbol(primary_symbol),
                    action=action,  # type: ignore  # action comes from ActionType.value
                    confidence=self._calculate_confidence(
                        primary_symbol, action, indicators, reasoning
                    ),
                    target_allocation=Percentage(Decimal(str(total_allocation))),
                    reasoning=reasoning,
                )
                signals.append(signal)
            else:
                # Single symbol recommendation
                signal = StrategySignal(
                    symbol=Symbol(symbol_or_allocation),
                    action=action,  # type: ignore  # action comes from ActionType.value
                    confidence=self._calculate_confidence(
                        symbol_or_allocation, action, indicators, reasoning
                    ),
                    target_allocation=Percentage(Decimal("1.0")),  # 100% allocation
                    reasoning=reasoning,
                )
                signals.append(signal)

            return signals

        except Exception as e:
            logging.error(f"Error generating TECL signals: {e}")
            return []

    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate generated signal (StrategyEngine protocol)."""
        try:
            # Basic validation
            if not signal.symbol.value:
                return False
            if signal.action not in ("BUY", "SELL", "HOLD"):
                return False
            if signal.confidence.value < 0 or signal.confidence.value > 1:
                return False
            return not (signal.target_allocation.value < 0 or signal.target_allocation.value > 1)

        except Exception:
            return False

    def get_strategy_summary(self) -> str:
        """Get a summary description of the TECL strategy."""
        return """
        TECL Strategy Summary:

        Bull Market (SPY > 200 MA):
        1. If TQQQ RSI > 79 → 25% UVXY + 75% BIL (volatility hedge)
        2. If SPY RSI > 80 → 25% UVXY + 75% BIL (volatility hedge)
        3. KMLM Switcher:
           - If XLK RSI > KMLM RSI:
             * XLK RSI > 81 → BIL (defensive)
             * Else → TECL (technology growth)
           - If KMLM RSI > XLK RSI:
             * XLK RSI < 29 → TECL (buy dip)
             * Else → BIL (defensive cash)

        Bear Market (SPY < 200 MA):
        1. If TQQQ RSI < 31 → TECL (buy tech dip)
        2. If SPXL RSI < 29 → SPXL (buy S&P dip)
        3. If UVXY RSI > 84 → 15% UVXY + 85% BIL (volatility spike)
        4. If UVXY RSI > 74 → BIL (defensive)
        5. KMLM Switcher:
           - If XLK RSI > KMLM RSI:
             * XLK RSI > 81 → BIL (defensive)
             * Else → TECL (technology growth)
           - If KMLM RSI > XLK RSI:
             * XLK RSI < 29 → TECL (buy dip)
             * Else → Bond/Short selection

        Bond/Short Selection (Bear Market Only):
        - Compare SQQQ vs BSV using RSI(9)
        - Select highest RSI candidate
        """


def main() -> None:
    """Test the TECL strategy engine."""
    logger = logging.getLogger(__name__)
    logger.info("🚀 TECL Strategy Engine Test")
    logger.info("=" * 50)
    logger.info("Note: This test requires a configured data provider")
    logger.info("Use the strategy through the signal generator for full functionality")


if __name__ == "__main__":
    main()
