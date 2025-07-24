from __future__ import annotations
from typing import Dict, Any

"""Console formatting utilities for trading bot output."""

def render_technical_indicators(strategy_signals: Dict[Any, Any]) -> str:
    lines: list[str] = []
    lines.append("\n📊 TECHNICAL INDICATORS:")
    lines.append("┌─" + "─" * 58 + "─┐")
    lines.append("│ Key Market & Technical Indicators                        │")
    lines.append("├─" + "─" * 58 + "─┤")

    all_indicators: Dict[str, Dict[str, Any]] = {}
    for _, data in strategy_signals.items():
        if 'indicators' in data and data['indicators']:
            all_indicators.update(data['indicators'])

    if not all_indicators:
        lines.append("│ No indicator data available                              │")
        lines.append("└─" + "─" * 58 + "─┘")
        return "\n".join(lines)

    # Show all symbols for which we have indicator data, sorted for consistency
    for symbol in sorted(all_indicators.keys()):
        ind = all_indicators[symbol]
        price = ind.get('current_price', 0)
        # Format price nicely
        if price < 10:
            price_str = f"${price:.3f}"
        elif price < 100:
            price_str = f"${price:.2f}"
        else:
            price_str = f"${price:.1f}"

        # Collect all RSI and MA values
        rsi_parts = []
        ma_parts = []
        for k, v in ind.items():
            if k.startswith('rsi_'):
                rsi_parts.append(f"{k.upper()}:{v:.1f}")
            if k.startswith('ma_'):
                ma_parts.append(f"{k.upper()}:{v:.1f}")
        # Add other indicators if present
        other_parts = []
        for k, v in ind.items():
            if k not in ('current_price',) and not k.startswith('rsi_') and not k.startswith('ma_'):
                other_parts.append(f"{k}:{v:.2f}")

        # RSI color/emoji for rsi_10 if present
        rsi_10 = ind.get('rsi_10', ind.get('rsi_9', 50))
        rsi_level = ""
        if rsi_10 > 80:
            rsi_level = "🔴"
        elif rsi_10 < 30:
            rsi_level = "🟢"
        else:
            rsi_level = "⚪"

        # Trend indicator for ma_200 if present
        ma_200 = ind.get('ma_200')
        trend_indicator = ""
        if ma_200 and price > 0:
            if price > ma_200:
                trend_indicator = " ↗"
            else:
                trend_indicator = " ↘"

        # Compose the line
        line = f"│ {symbol:>4}: {price_str:<8} {rsi_level}{trend_indicator} "
        if rsi_parts:
            line += "| " + ", ".join(rsi_parts) + " "
        if ma_parts:
            line += "| " + ", ".join(ma_parts) + " "
        if other_parts:
            line += "| " + ", ".join(other_parts) + " "
        # Pad to exact width
        line = line[:59] + "│" if len(line) > 60 else line.ljust(61) + "│"
        lines.append(line)

    # Add market regime summary
    if 'SPY' in all_indicators:
        spy_data = all_indicators['SPY']
        spy_price = spy_data.get('current_price', 0)
        spy_ma200 = spy_data.get('ma_200', 0)

        if spy_price > 0 and spy_ma200 > 0:
            lines.append("├─" + "─" * 58 + "─┤")
            regime = "BULL MARKET" if spy_price > spy_ma200 else "BEAR MARKET"
            regime_line = f"│ Market Regime: {regime} (SPY {spy_price:.1f} vs 200MA {spy_ma200:.1f})"
            regime_line = regime_line.ljust(61) + "│"
            lines.append(regime_line)

    lines.append("└─" + "─" * 58 + "─┘")
    return "\n".join(lines)

__all__ = ['render_technical_indicators']
