from __future__ import annotations
from typing import Dict, Any

"""Console formatting utilities for trading bot output."""

def render_technical_indicators(strategy_signals: Dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("TECHNICAL INDICATORS")
    all_indicators: Dict[str, Dict[str, Any]] = {}
    for _, data in strategy_signals.items():
        if data.get('indicators'):
            all_indicators.update(data['indicators'])
    if not all_indicators:
        lines.append("No indicator data available")
        return "\n".join(lines)
    key_symbols = ["SPY", "TQQQ", "XLK", "KMLM", "UVXY", "SPXL", "TECL", "BIL", "SQQQ", "BSV"]
    shown = 0
    for sym in key_symbols:
        if sym in all_indicators and shown < 8:
            ind = all_indicators[sym]
            price = ind.get('current_price', 0)
            rsi = ind.get('rsi_10', ind.get('rsi_9', 50))
            ma200 = ind.get('ma_200')
            price_str = f"${price:.2f}"
            trend = 'up' if ma200 and price > ma200 else 'down'
            line = f"{sym}: {price_str} RSI:{rsi:.1f} {trend}"
            lines.append(line)
            shown += 1
    return "\n".join(lines)

__all__ = ['render_technical_indicators']
