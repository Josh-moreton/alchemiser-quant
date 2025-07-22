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
    """Build an objective Telegram report focused on signals and trades.

    Parameters
    ----------
    mode: str
        Execution mode label (e.g. "LIVE" or "PAPER").
    success: bool
        Whether trading finished successfully.
    account_before: dict
        Account stats before trading (unused in objective mode).
    account_after: dict
        Account stats after trading (unused in objective mode).
    positions: dict
        Current positions keyed by symbol (unused in objective mode).
    orders: list | None
        Orders executed during the run.
    signal: optional
        The primary trading signal/alert object for context.
    """

    lines = [f"Nuclear {mode} Bot Report"]
    
    # Status
    if success:
        lines.append("Status: Completed")
    else:
        lines.append("Status: Failed")
    
    # Signal detected
    if signal is not None:
        try:
            sig_line = f"{signal.action} {signal.symbol}"
            if hasattr(signal, "reason") and signal.reason:
                sig_line += f" - {signal.reason}"
            lines.append(f"Signal: {sig_line}")
        except Exception:
            lines.append("Signal: Error reading signal data")
    else:
        lines.append("Signal: None detected")

    # Orders executed
    if orders and len(orders) > 0:
        lines.append(f"Orders: {len(orders)} executed")
        for order in orders:
            side = order.get("side")
            side = side.value if hasattr(side, "value") else str(side)
            symbol = order.get("symbol", "N/A")
            qty = order.get("qty", 0)
            value = order.get("estimated_value", 0)
            lines.append(f"- {side.upper()} {qty:.6f} {symbol} (${value:.2f})")
    else:
        lines.append("Orders: None executed")
    
    # Errors if any
    if not success:
        lines.append("Note: Check logs for error details")

    return "\n".join(lines)
