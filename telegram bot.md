# Plan for Building a Telegram Bot

The project’s main entry point is main.py, which takes a single argument called mode with the choices “bot”, “email”, or “alpaca”:

parser.add_argument('mode', choices=['bot', 'email', 'alpaca'],
                   help='Operation mode to run')

The README also summarizes these three modes in a table of commands:

| **bot**   | `python main.py bot`    | Live signal generation      | Console + JSON logs   |
| **email** | `python main.py email`  | Live signals + email alerts | Console + Email       |
| **alpaca**| `python main.py alpaca` | Automated trading with Alpaca + email alert | Console + Email |

To build a basic Telegram Bot that can trigger these commands and return the output:

Create a Telegram Bot

Use BotFather on Telegram to generate an API token as described in Telegram’s bot API docs.

Choose a Python Telegram library

Libraries such as python-telegram-bot or telebot (PyTelegramBotAPI) simplify message handling and command routing.

Set up command handlers

Implement handlers for /bot, /email, and /alpaca. Each handler runs python main.py <mode> using a subprocess call and captures the output.

Example pseudocode (using python-telegram-bot):

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess

async def run_cmd(mode: str) -> str:
    result = subprocess.run(
        ["python", "main.py", mode],
        capture_output=True, text=True
    )
    return result.stdout or result.stderr

async def bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    output = await run_cmd("bot")
    await update.message.reply_text(output)

# Repeat for email and alpaca

Send email content back to Telegram

The email and alpaca modes rely on core/email_utils.py to send emails. Modify send_signal_notification and send_alpaca_notification to return the formatted email body as a string after sending. The Telegram handler can then reply with that body.

Optional: Provide a help/start command

Implement /start or /help to list the available commands and brief descriptions.

Deploy and run

The bot process must have access to Python dependencies (see requirements.txt) and environment variables (e.g., SMTP_PASSWORD for email mode). Run the bot on a server or a cloud instance so it stays online.

When users send /bot, /email, or /alpaca in Telegram, the bot will execute the corresponding mode of main.py and respond with either the trading signal result or the email content that would have been sent. This allows quick interaction with the trading strategy directly from Telegram.
