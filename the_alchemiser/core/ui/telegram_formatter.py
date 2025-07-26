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
    
    # Show portfolio P&L if available in account info
    account_info = result.execution_summary.get('account_info_after', {})
    portfolio_history = account_info.get('portfolio_history', {})
    open_positions = account_info.get('open_positions', [])
    
    if portfolio_history and 'profit_loss' in portfolio_history:
        profit_loss = portfolio_history['profit_loss']
        profit_loss_pct = portfolio_history['profit_loss_pct']
        
        if profit_loss and len(profit_loss) > 0:
            latest_pl = profit_loss[-1]
            latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
            
            pl_emoji = "📈" if latest_pl >= 0 else "📉"
            pl_sign = "+" if latest_pl >= 0 else ""
            
            lines.extend([
                "",
                "💰 Portfolio Performance:",
                f"{pl_emoji} Total P&L: {pl_sign}${latest_pl:,.2f} ({pl_sign}{latest_pl_pct:.2%})"
            ])
    
    # Show current positions summary
    if open_positions:
        lines.extend([
            "",
            "📊 Open Positions:",
        ])
        
        total_unrealized_pl = 0
        for position in open_positions[:3]:  # Show top 3 for brevity
            symbol = position.get('symbol', 'N/A')
            market_value = float(position.get('market_value', 0))
            unrealized_pl = float(position.get('unrealized_pl', 0))
            unrealized_plpc = float(position.get('unrealized_plpc', 0))
            
            total_unrealized_pl += unrealized_pl
            
            pl_emoji = "🟢" if unrealized_pl >= 0 else "🔴"
            pl_sign = "+" if unrealized_pl >= 0 else ""
            
            lines.append(f"{symbol}: ${market_value:,.0f} {pl_emoji}{pl_sign}${unrealized_pl:.0f}")
        
        if len(open_positions) > 3:
            lines.append(f"... and {len(open_positions) - 3} more")
        
        if len(open_positions) > 1:
            total_pl_emoji = "🟢" if total_unrealized_pl >= 0 else "🔴"
            total_pl_sign = "+" if total_unrealized_pl >= 0 else ""
            lines.append(f"Total Unrealized: {total_pl_emoji}{total_pl_sign}${total_unrealized_pl:.0f}")
    
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
            for symbol, data in list(allocations.items())[:5]:  # Limit to top 5
                target_pct = data.get('target_percent', 0)
                current_pct = data.get('current_percent', 0) 
                target_value = data.get('target_value', 0)
                current_value = data.get('current_value', 0)
                
                lines.append(f"  {symbol}: Target {target_pct:.1f}% (${target_value:,.0f}) | Current {current_pct:.1f}% (${current_value:,.0f})")
    else:
        # Fallback to simple portfolio allocation
        lines.extend([
            "",
            "🎯 Portfolio Allocation:",
        ])
        for symbol, weight in list(result.consolidated_portfolio.items())[:5]:  # Top 5
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
