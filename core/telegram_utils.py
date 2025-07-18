import os
import requests
from .secrets_manager import SecretsManager

# Initialize secrets manager
secrets_manager = SecretsManager(region_name="eu-west-2")
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
) -> str:
    """Build a rich Telegram report for trade execution.

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
    """

    lines = [f"\U0001F680 Nuclear {mode} Execution Report", ""]
    lines.append(f"Status: {'✅ Success' if success else '❌ Failed'}")

    pv_before = float(account_before.get("portfolio_value", 0))
    pv_after = float(account_after.get("portfolio_value", 0))
    cash_after = float(account_after.get("cash", 0))

    change = pv_after - pv_before
    change_pct = (change / pv_before * 100) if pv_before else 0

    lines.append(
        f"Portfolio Value: ${pv_after:,.2f} ({change:+.2f} / {change_pct:+.2f}%)"
    )
    cash_pct = (cash_after / pv_after * 100) if pv_after else 0
    lines.append(f"Cash: ${cash_after:,.2f} ({cash_pct:.1f}% of portfolio)")

    if signal is not None:
        try:
            sig_line = f"{signal.action} {signal.symbol}"
            if hasattr(signal, "reason") and signal.reason:
                sig_line += f" – {signal.reason}"
            lines.append("")
            lines.append(f"🔔 Signal: {sig_line}")
        except Exception:
            pass

    if positions:
        lines.append("\n📊 Positions:")
        # Sort by allocation size
        pv = pv_after or 1.0
        sorted_pos = sorted(
            positions.items(), key=lambda kv: kv[1].get("market_value", 0), reverse=True
        )
        top_gainer = None
        worst = None
        for symbol, pos in sorted_pos:
            qty = pos.get("qty", 0)
            price = pos.get("current_price", 0)
            mv = pos.get("market_value", 0)
            pnl_pct = pos.get("unrealized_plpc", 0) * 100
            allocation = mv / pv * 100
            lines.append(
                f"- {symbol}: {qty} @ ${price:.2f} "
                f"(P&L {pnl_pct:+.1f}%, {allocation:.1f}% alloc)"
            )
            if top_gainer is None or pnl_pct > top_gainer[1]:
                top_gainer = (symbol, pnl_pct)
            if worst is None or pnl_pct < worst[1]:
                worst = (symbol, pnl_pct)
        if top_gainer and worst:
            lines.append(
                f"Top gainer: {top_gainer[0]} ({top_gainer[1]:+.1f}%), "
                f"Worst: {worst[0]} ({worst[1]:+.1f}%)"
            )

    if orders:
        lines.append("\n📝 Orders:")
        for order in orders:
            side = order.get("side")
            side = side.value if hasattr(side, "value") else str(side)
            lines.append(
                f"- {side.upper()} {order.get('qty')} {order.get('symbol')} "
                f"(${order.get('estimated_value', 0):.2f})"
            )

    if cash_pct < 5:
        lines.append(f"\n⚠️ Cash buffer low at {cash_pct:.1f}%")

    return "\n".join(lines)
