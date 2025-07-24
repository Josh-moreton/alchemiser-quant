from __future__ import annotations
from datetime import datetime
from typing import Any


def build_single_strategy_message(result: Any, strategy_name: str, mode: str) -> str:
    if not result.success:
        return f"❌ {mode} {strategy_name} Strategy FAILED\n\nError: {result.execution_summary.get('error', 'Unknown error')}"
    lines = [
        f"🎯 {mode} {strategy_name} STRATEGY",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "🎯 Portfolio Allocation:",
    ]
    for symbol, weight in result.consolidated_portfolio.items():
        lines.append(f"{symbol}: {weight:.1%}")
    trading = result.execution_summary['trading_summary']
    if trading['total_trades'] > 0:
        lines.extend([
            "",
            f"⚡ Trading: {trading['total_trades']} orders",
            f"Buy: ${trading['total_buy_value']:,.0f} | Sell: ${trading['total_sell_value']:,.0f}",
        ])
    else:
        lines.append("\n⚡ No trades needed")
    return "\n".join(lines)


def build_multi_strategy_message(result: Any, mode: str) -> str:
    if not result.success:
        return f"❌ {mode} Multi-Strategy Execution FAILED\n\nError: {result.execution_summary.get('error', 'Unknown error')}"
    lines = [
        f"🎯 {mode} MULTI-STRATEGY EXECUTION",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "📊 Strategy Signals:",
    ]
    for strategy, details in result.execution_summary['strategy_summary'].items():
        lines.append(f"{strategy} ({details['allocation']:.0%}): {details['signal']}")
    lines.extend([
        "",
        "🎯 Portfolio Allocation:",
    ])
    for symbol, weight in result.consolidated_portfolio.items():
        lines.append(f"{symbol}: {weight:.1%}")
    trading = result.execution_summary['trading_summary']
    if trading['total_trades'] > 0:
        lines.extend([
            "",
            f"⚡ Trading: {trading['total_trades']} orders",
            f"Buy: ${trading['total_buy_value']:,.0f} | Sell: ${trading['total_sell_value']:,.0f}",
        ])
    else:
        lines.append("\n⚡ No trades needed")
    return "\n".join(lines)

__all__ = [
    "build_single_strategy_message",
    "build_multi_strategy_message",
]
