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
    
    # Show final portfolio state if available
    if hasattr(result, 'final_portfolio_state') and result.final_portfolio_state:
        portfolio_state = result.final_portfolio_state
        lines.extend([
            "",
            "🏁 FINAL PORTFOLIO STATE:",
        ])
        
        total_value = portfolio_state.get('total_value', 0)
        if total_value > 0:
            lines.append(f"💰 Portfolio Value: ${total_value:,.2f}")
        
        allocations = portfolio_state.get('allocations', {})
        if allocations:
            lines.append("🎯 Target vs Current:")
            for symbol, data in allocations.items():
                target_pct = data.get('target_percent', 0)
                current_pct = data.get('current_percent', 0) 
                target_value = data.get('target_value', 0)
                current_value = data.get('current_value', 0)
                
                lines.append(f"  {symbol}: Target {target_pct:.1f}% (${target_value:,.2f}) | Current {current_pct:.1f}% (${current_value:,.2f})")
    else:
        # Fallback to simple portfolio allocation
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
