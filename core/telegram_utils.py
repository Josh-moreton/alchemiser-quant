import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Set this in your .env


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
        resp = requests.post(url, data=payload)
        if resp.status_code == 200:
            return True
        else:
            print(f"Failed to send Telegram message: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False
