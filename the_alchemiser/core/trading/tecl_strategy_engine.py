#!/usr/bin/env python3
"""
TECL Strategy Engine

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

import logging
import warnings

from the_alchemiser.core.indicators.indicators import TechnicalIndicators
from the_alchemiser.core.utils.common import ActionType
from the_alchemiser.utils.indicator_utils import safe_get_indicator

warnings.filterwarnings("ignore")


class TECLStrategyEngine:
    """TECL Strategy Engine - Long-term technology leverage with volatility protection"""

    def __init__(self, data_provider=None):
        if data_provider is None:
            raise ValueError("data_provider is required for TECLStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()

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

    def get_market_data(self):
        """Fetch data for all symbols"""
        market_data = {}
        for symbol in self.all_symbols:
            data = self.data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        return market_data

    def calculate_indicators(self, market_data):
        """Calculate all technical indicators needed for TECL strategy"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df["Close"]
            indicators[symbol] = {
                "rsi_9": safe_get_indicator(close, self.indicators.rsi, 9),
                "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                "current_price": float(close.iloc[-1]),
            }
        return indicators

    def evaluate_tecl_strategy(self, indicators, market_data=None):
        """
        Evaluate the TECL (Technology) strategy with detailed reasoning.

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
        else:
            # BEAR MARKET PATH
            market_analysis += "• Regime: BEAR MARKET (SPY below 200MA)\n"
            return self._evaluate_bear_market_path(indicators, market_analysis)

    def _evaluate_bull_market_path(self, indicators, market_analysis):
        """Evaluate strategy when SPY is above 200-day MA (bull market)"""

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

    def _evaluate_bear_market_path(self, indicators, market_analysis):
        """Evaluate strategy when SPY is below 200-day MA (bear market)"""

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
            elif uvxy_rsi > 74:
                # High UVXY - defensive
                reasoning = f"{market_analysis}\n\nHigh Volatility Environment:\n"
                reasoning += f"• UVXY RSI(10): {uvxy_rsi:.1f} > 74 (elevated)\n"
                reasoning += "• Strategy: Full defensive positioning\n"
                reasoning += "• Target: BIL (cash equivalent) for capital preservation\n"
                reasoning += "• Rationale: High volatility suggests more downside risk"

                return "BIL", ActionType.BUY.value, reasoning

        # Fourth check: KMLM Switcher for bear market
        return self._evaluate_kmlm_switcher(indicators, market_analysis, "Bear market")

    def _evaluate_kmlm_switcher(self, indicators, market_analysis, market_regime):
        """
        KMLM Switcher logic: Compare XLK vs KMLM RSI to determine technology timing

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
            else:
                # XLK strong but not extreme - buy technology
                reasoning = f"{switcher_analysis}• XLK Status: Strong but sustainable (<81)\n"
                reasoning += "• Strategy: Technology momentum play\n"
                reasoning += "• Target: TECL (3x leveraged tech) for sector strength\n"
                reasoning += "• Rationale: Tech outperforming materials, trend continuation"

                logging.debug(f"XLK stronger than KMLM: {xlk_rsi:.2f} > {kmlm_rsi:.2f}")
                return "TECL", ActionType.BUY.value, reasoning

        else:
            # Materials (KMLM) is stronger than technology (XLK)
            switcher_analysis += "• Sector Comparison: Materials STRONGER than Technology\n"

            if xlk_rsi < 29:
                # XLK oversold - buy the dip
                reasoning = f"{switcher_analysis}• XLK Status: Oversold (<29) despite weakness\n"
                reasoning += "• Strategy: Counter-trend tech dip buying\n"
                reasoning += "• Target: TECL (3x leveraged tech) for oversold bounce\n"
                reasoning += (
                    "• Rationale: Tech oversold creates opportunity despite sector weakness"
                )

                logging.debug(f"XLK oversold: {xlk_rsi:.2f} < 29")
                return "TECL", ActionType.BUY.value, reasoning
            else:
                # XLK weak - return BIL directly in bull market, use selection in bear market
                logging.debug(f"KMLM stronger than XLK: {kmlm_rsi:.2f} > {xlk_rsi:.2f}")
                if market_regime == "Bull market":
                    reasoning = f"{switcher_analysis}• Tech Status: Weak relative to materials\n"
                    reasoning += "• Strategy: Defensive positioning in bull market\n"
                    reasoning += "• Target: BIL (cash) - avoid weak tech sector\n"
                    reasoning += "• Rationale: Materials strength suggests rotation away from tech"

                    return "BIL", ActionType.BUY.value, reasoning
                else:
                    # Bear market - use bond vs short selection
                    return self._evaluate_bond_vs_short_selection(
                        indicators, switcher_analysis, market_regime
                    )

    def _evaluate_bond_vs_short_selection(self, indicators, switcher_analysis, market_regime):
        """
        Final selection between bonds and short positions using RSI filter mechanism.
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

    def get_strategy_summary(self) -> str:
        """Get a summary description of the TECL strategy"""
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


def main():
    """Test the TECL strategy engine"""

    print("🚀 TECL Strategy Engine Test")
    print("=" * 50)

    # Initialize engine
    engine = TECLStrategyEngine()

    # Get market data
    print("📊 Fetching market data...")
    market_data = engine.get_market_data()
    print(f"✅ Fetched data for {len(market_data)} symbols")

    # Calculate indicators
    print("🔬 Calculating technical indicators...")
    indicators = engine.calculate_indicators(market_data)
    print(f"✅ Calculated indicators for {len(indicators)} symbols")

    # Evaluate strategy
    print("⚡ Evaluating TECL strategy...")
    symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)

    print("\n🎯 TECL STRATEGY RESULT:")
    print(f"   Action: {action}")
    if isinstance(symbol_or_allocation, dict):
        print(f"   Allocation: {symbol_or_allocation}")
    else:
        print(f"   Symbol: {symbol_or_allocation}")
    print(f"   Reason: {reason}")

    # Print key indicators
    print("\n🔬 Key Technical Indicators:")
    key_symbols = ["SPY", "XLK", "KMLM", "TQQQ", "UVXY"]
    for sym in key_symbols:
        if sym in indicators:
            print(f"   {sym}: RSI(10)={indicators[sym]['rsi_10']:.1f}")

    print("\n📈 Strategy Summary:")
    print(engine.get_strategy_summary())


if __name__ == "__main__":
    main()
