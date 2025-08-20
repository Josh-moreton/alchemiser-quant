"""
Shared Nuclear Strategy Logic

This module contains the core decision logic for the Nuclear energy trading strategy
that is shared between the typed and legacy implementations to eliminate code duplication.

The logic implements the canonical hierarchical decision tree from the original
Clojure implementation, ensuring both implementations use identical strategy logic.
"""

from typing import Any

from the_alchemiser.domain.strategies.strategy_engine import (
    BearMarketStrategy,
    BullMarketStrategy,
    VoxOverboughtStrategy,
)
from the_alchemiser.domain.strategies.strategy_engine import (
    NuclearStrategyEngine as PureNuclearEngine,
)


def evaluate_nuclear_strategy_logic(
    indicators: dict[str, Any],
    market_data: dict[str, Any] | None = None,
    pure_strategy: PureNuclearEngine | None = None,
) -> tuple[str, str, str]:
    """
    Core Nuclear Energy strategy evaluation logic.

    This function implements the canonical hierarchical decision tree that both
    typed and legacy implementations use, eliminating code duplication.

    Args:
        indicators: Technical indicators for all symbols
        market_data: Raw market data (optional, used by some sub-strategies)
        pure_strategy: Pure strategy engine instance (created if not provided)

    Returns:
        Tuple of (recommended_symbol, action, detailed_reason)
    """
    if pure_strategy is None:
        pure_strategy = PureNuclearEngine()

    if "SPY" not in indicators:
        return "SPY", "HOLD", "Missing SPY data - cannot evaluate market conditions"

    # Get key market indicators for detailed reasoning
    spy_rsi_10 = indicators["SPY"]["rsi_10"]
    spy_price = indicators["SPY"]["current_price"]
    spy_ma_200 = indicators["SPY"]["ma_200"]
    market_trend = "Bull Market" if spy_price > spy_ma_200 else "Bear Market"

    # PRIMARY BRANCH: SPY RSI > 79 (ALL nested overbought checks happen HERE)
    if spy_rsi_10 > 79:
        base_explanation = (
            f"Market Analysis: {market_trend} (SPY ${spy_price:.2f} vs 200MA ${spy_ma_200:.2f})\n"
            f"SPY RSI(10): {spy_rsi_10:.1f} - Primary overbought condition triggered (>79)"
        )

        # First: SPY extremely overbought (> 81)
        if spy_rsi_10 > 81:
            explanation = (
                f"{base_explanation}\n\n"
                f"Signal: SPY extremely overbought (RSI {spy_rsi_10:.1f} > 81)\n"
                f"Action: Buy UVXY volatility hedge - expect major market correction"
            )
            return "UVXY", "BUY", explanation

        # Then: Nested checks for IOO, TQQQ, VTV, XLF (RSI > 81) - IN ORDER
        for symbol in ["IOO", "TQQQ", "VTV", "XLF"]:
            if symbol in indicators and indicators[symbol]["rsi_10"] > 81:
                symbol_rsi = indicators[symbol]["rsi_10"]
                explanation = (
                    f"{base_explanation}\n\n"
                    f"Secondary Check: {symbol} RSI(10): {symbol_rsi:.1f} - Extremely overbought (>81)\n"
                    f"Action: Buy UVXY volatility hedge - sector rotation imminent"
                )
                return "UVXY", "BUY", explanation

        # Finally: SPY moderately overbought (79-81) - hedge portfolio
        explanation = (
            f"{base_explanation}\n\n"
            f"Signal: SPY moderately overbought (79 < RSI {spy_rsi_10:.1f} < 81)\n"
            f"Action: Defensive hedged position - UVXY 75% + BTAL 25%\n"
            f"Rationale: Partial volatility hedge while maintaining some upside exposure"
        )
        return "UVXY_BTAL_PORTFOLIO", "BUY", explanation

    # PRIMARY BRANCH: SPY RSI <= 79 - Continue with VOX, oversold checks, bull/bear logic
    base_explanation = (
        f"Market Analysis: {market_trend} (SPY ${spy_price:.2f} vs 200MA ${spy_ma_200:.2f})\n"
        f"SPY RSI(10): {spy_rsi_10:.1f} - Not overbought, checking secondary conditions"
    )

    # VOX overbought check
    if "VOX" in indicators and indicators["VOX"]["rsi_10"] > 79:
        vox_rsi = indicators["VOX"]["rsi_10"]
        result = VoxOverboughtStrategy().recommend(indicators)
        if result:
            symbol, action, basic_reason = result
            explanation = (
                f"{base_explanation}\n\n"
                f"VOX Telecom Analysis: RSI(10) {vox_rsi:.1f} > 79 (overbought)\n"
                f"{basic_reason}"
            )
            return symbol, action, explanation

    # Oversold conditions (TQQQ first, then SPY)
    if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
        tqqq_rsi = indicators["TQQQ"]["rsi_10"]
        explanation = (
            f"{base_explanation}\n\n"
            f"Oversold Opportunity: TQQQ RSI(10) {tqqq_rsi:.1f} < 30\n"
            f"Action: Buy the dip in leveraged tech - oversold bounce expected"
        )
        return "TQQQ", "BUY", explanation

    if indicators["SPY"]["rsi_10"] < 30:
        explanation = (
            f"{base_explanation}\n\n"
            f"Oversold Opportunity: SPY RSI(10) {spy_rsi_10:.1f} < 30\n"
            f"Action: Buy UPRO (3x leveraged SPY) - market oversold, strong bounce expected"
        )
        return "UPRO", "BUY", explanation

    # Bull vs Bear market determination (SPY above/below 200 MA)
    if "SPY" in indicators and spy_price > spy_ma_200:
        result = BullMarketStrategy(pure_strategy).recommend(indicators, market_data)
        if result:
            symbol, action, basic_reason = result
            explanation = (
                f"{base_explanation}\n\n"
                f"Bull Market Strategy: SPY above 200MA (${spy_price:.2f} > ${spy_ma_200:.2f})\n"
                f"{basic_reason}"
            )
            return symbol, action, explanation
    else:
        result = BearMarketStrategy(pure_strategy).recommend(indicators)
        if result:
            symbol, action, basic_reason = result
            explanation = (
                f"{base_explanation}\n\n"
                f"Bear Market Strategy: SPY below 200MA (${spy_price:.2f} < ${spy_ma_200:.2f})\n"
                f"{basic_reason}"
            )
            return symbol, action, explanation

    # Fallback - no clear signal
    explanation = (
        f"{base_explanation}\n\n"
        f"No Clear Signal: Market conditions neutral\n"
        f"RSI not overbought/oversold, no strong trend signals\n"
        f"Action: Hold current positions, wait for clearer market direction"
    )
    return "SPY", "HOLD", explanation
