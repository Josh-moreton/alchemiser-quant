import os
import requests
from datetime import datetime
from the_alchemiser.core.secrets.secrets_manager import SecretsManager

# Initialize secrets manager - region will be loaded from config
secrets_manager = SecretsManager()
TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = secrets_manager.get_telegram_config()


def send_telegram_message(text, chat_id=None, parse_mode=None):
    """
    Send a message to a Telegram chat using the Bot API.
    Args:
        text (str): The message to send
        chat_id (str, optional): Telegram chat ID. If not provided, uses TELEGRAM_CHAT_ID from env
        parse_mode (str, optional): 'Markdown' or 'HTML' for formatting
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN not set in environment.")
        return False
    if not chat_id:
        chat_id = TELEGRAM_CHAT_ID
    if not chat_id:
        print("TELEGRAM_CHAT_ID not set in environment or not provided.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"Failed to send Telegram message: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def build_execution_report(
    *,
    mode: str,
    success: bool,
    account_before: dict,
    account_after: dict,
    positions: dict,
    orders: list | None = None,
    signal=None,
    portfolio_state: dict | None = None,
    portfolio_history: dict | None = None,
    open_positions: list | None = None,
) -> str:
    """Build an objective Telegram report focused on signals and trades.

    Parameters
    ----------
    mode: str
        Execution mode label (e.g. "LIVE" or "PAPER").
    success: bool
        Whether trading finished successfully.
    account_before: dict
        Account stats before trading.
    account_after: dict
        Account stats after trading.
    positions: dict
        Current positions keyed by symbol.
    orders: list | None
        Orders executed during the run.
    signal: optional
        The primary trading signal/alert object for context.
    portfolio_state: dict | None
        Final portfolio allocation state with target vs current data.
    portfolio_history: dict | None
        Portfolio history data from Alpaca API.
    open_positions: list | None
        Open positions data from Alpaca API.
    """

    lines = [f"🤖 Nuclear {mode} Bot Report"]
    
    # Status
    status_emoji = "✅" if success else "❌"
    lines.append(f"{status_emoji} Status: {'Success' if success else 'Failed'}")
    lines.append(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    lines.append("")
    
    # Account summary with P&L
    if account_after:
        equity = float(account_after.get('equity', 0))
        cash = float(account_after.get('cash', 0))
        
        lines.append("💰 Account Summary:")
        lines.append(f"Portfolio: ${equity:,.2f}")
        lines.append(f"Cash: ${cash:,.2f}")
        
        # Add P&L from portfolio history if available
        if portfolio_history and 'profit_loss' in portfolio_history:
            profit_loss = portfolio_history['profit_loss']
            profit_loss_pct = portfolio_history['profit_loss_pct']
            
            if profit_loss and len(profit_loss) > 0:
                latest_pl = profit_loss[-1]
                latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                
                pl_emoji = "📈" if latest_pl >= 0 else "📉"
                pl_sign = "+" if latest_pl >= 0 else ""
                
                lines.append(f"{pl_emoji} Total P&L: {pl_sign}${latest_pl:,.2f} ({pl_sign}{latest_pl_pct:.2%})")
        
        lines.append("")
    
    # Open positions summary
    if open_positions:
        lines.append("📊 Open Positions:")
        total_unrealized_pl = 0
        
        for position in open_positions[:5]:  # Limit to top 5 for Telegram
            symbol = position.get('symbol', 'N/A')
            market_value = float(position.get('market_value', 0))
            unrealized_pl = float(position.get('unrealized_pl', 0))
            unrealized_plpc = float(position.get('unrealized_plpc', 0))
            
            total_unrealized_pl += unrealized_pl
            
            pl_emoji = "🟢" if unrealized_pl >= 0 else "🔴"
            pl_sign = "+" if unrealized_pl >= 0 else ""
            
            lines.append(f"{symbol}: ${market_value:,.0f} {pl_emoji}{pl_sign}${unrealized_pl:.0f} ({pl_sign}{unrealized_plpc:.1%})")
        
        if len(open_positions) > 5:
            lines.append(f"... and {len(open_positions) - 5} more positions")
        
        # Total unrealized P&L
        if len(open_positions) > 1:
            total_pl_emoji = "🟢" if total_unrealized_pl >= 0 else "🔴"
            total_pl_sign = "+" if total_unrealized_pl >= 0 else ""
            lines.append(f"Total Unrealized: {total_pl_emoji}{total_pl_sign}${total_unrealized_pl:.2f}")
        
        lines.append("")
    
    # Signal information if available
    if signal:
        lines.append("📈 Signal:")
        try:
            sig_line = f"{signal.action} {signal.symbol}"
            if hasattr(signal, "reason") and signal.reason:
                sig_line += f" - {signal.reason}"
            lines.append(f"  {sig_line}")
        except Exception:
            lines.append("  Error reading signal data")
        lines.append("")
    
    # Trading activity
    if orders:
        lines.append(f"⚡ Orders: {len(orders)}")
        buy_count = sum(1 for o in orders if 'buy' in str(o.get('side', '')).lower())
        sell_count = len(orders) - buy_count
        if buy_count > 0:
            lines.append(f"🟢 Buys: {buy_count}")
        if sell_count > 0:
            lines.append(f"🔴 Sells: {sell_count}")
        lines.append("")
    else:
        lines.append("⚡ No trades executed")
        lines.append("")
    
    # Final portfolio state
    if portfolio_state and "allocations" in portfolio_state:
        lines.append("🏁 Portfolio State:")
        
        total_value = portfolio_state.get("total_value", 0)
        if total_value > 0:
            lines.append(f"💰 Value: ${total_value:,.2f}")
        
        allocations = portfolio_state["allocations"]
        if allocations:
            lines.append("🎯 Allocations:")
            for symbol, data in allocations.items():
                target_pct = data.get("target_percent", 0)
                current_pct = data.get("current_percent", 0) 
                current_value = data.get("current_value", 0)
                
                lines.append(f"  {symbol}: {current_pct:.1f}% (${current_value:,.0f})")
    
    # Errors if any
    if not success:
        lines.append("")
        lines.append("⚠️ Check logs for details")

    return "\n".join(lines)