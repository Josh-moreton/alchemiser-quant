"""
Telegram Bot for LQQ3 Trading System

- Handles /bot, /email, /alpaca commands
- Runs main.py with the appropriate mode and returns output
- Uses python-telegram-bot library
- Requires TELEGRAM_TOKEN in .env
- Integrates with GitHub Actions workflow
"""
import os
import subprocess
import asyncio
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Import secrets manager
from core.secrets_manager import SecretsManager

# Load environment variables

# Initialize secrets manager
secrets_manager = SecretsManager(region_name="eu-west-2")
TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = secrets_manager.get_telegram_config()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # You'll need to add this to .env
GITHUB_OWNER = "Josh-moreton"
GITHUB_REPO = "LQQ3"
WORKFLOW_FILE = "nuclear_daily_signal.yml"

async def trigger_github_workflow(workflow_file: str, ref: str = "main") -> dict:
    """Trigger GitHub Actions workflow and return response"""
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not set in .env"}
    
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {"ref": ref}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            return {"success": True, "message": "Workflow triggered successfully"}
        else:
            return {"error": f"Failed to trigger workflow: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error triggering workflow: {str(e)}"}

async def get_workflow_runs(workflow_file: str, limit: int = 1) -> dict:
    """Get recent workflow runs for monitoring"""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_file}/runs"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": limit})
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get workflow runs: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error getting workflow runs: {str(e)}"}

async def run_cmd(mode: str) -> str:
    result = subprocess.run(
        ["python", "main.py", mode],
        capture_output=True, text=True
    )
    return result.stdout or result.stderr

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show welcome message with inline keyboard buttons"""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Run Bot (Local)", callback_data="local_bot"),
            InlineKeyboardButton("📧 Email Alert (Local)", callback_data="local_email")
        ],
        [
            InlineKeyboardButton("🏦 Alpaca Trading (Local)", callback_data="local_alpaca")
        ],
        [
            InlineKeyboardButton("☁️ Run via GitHub Actions", callback_data="github_workflow")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🚀 Welcome to the LQQ3 Trading Bot!\n\n"
        "Choose how you want to run the trading bot:\n\n"
        "**Local Commands:**\n"
        "• 🚀 Run Bot - Generate trading signals locally\n"
        "• 📧 Email Alert - Run locally + send email\n"
        "• 🏦 Alpaca Trading - Run locally + execute trades\n\n"
        "**Cloud Commands:**\n"
        "• ☁️ GitHub Actions - Run bot in the cloud\n\n"
        "Use /help to see text commands or click a button below:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "🚀 **LQQ3 Trading Bot Commands**\n\n"
        "**Text Commands:**\n"
        "/start - Show main menu with buttons\n"
        "/help - Show this help message\n"
        "/bot - Run live signal generation (local)\n"
        "/email - Run live signals + email alert (local)\n"
        "/alpaca - Run automated trading (local)\n"
        "/github - Trigger GitHub Actions workflow\n\n"
        "**Button Commands:**\n"
        "Use /start to see interactive buttons for all actions."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def github_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger GitHub Actions workflow directly"""
    await update.message.reply_text("🔄 Triggering GitHub Actions workflow...")
    
    result = await trigger_github_workflow(WORKFLOW_FILE)
    
    if result.get("success"):
        await update.message.reply_text(
            "✅ GitHub Actions workflow triggered successfully!\n\n"
            "The bot is now running in the cloud. You can check the status at:\n"
            f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions"
        )
    else:
        await update.message.reply_text(f"❌ Failed to trigger workflow: {result.get('error')}")

async def button_callback(query_update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = query_update.callback_query
    await query.answer()  # Acknowledge the button click
    
    if query.data == "local_bot":
        await query.edit_message_text("🚀 Running bot locally...")
        output = await run_cmd("bot")
        await query.edit_message_text(f"🚀 **Bot Results:**\n```\n{output}\n```", parse_mode='Markdown')
        
    elif query.data == "local_email":
        await query.edit_message_text("📧 Running bot with email notification...")
        output = await run_cmd("email")
        await query.edit_message_text(f"📧 **Email Results:**\n```\n{output}\n```", parse_mode='Markdown')
        
    elif query.data == "local_alpaca":
        await query.edit_message_text("🏦 Running Alpaca trading bot...")
        output = await run_cmd("alpaca")
        await query.edit_message_text(f"🏦 **Alpaca Results:**\n```\n{output}\n```", parse_mode='Markdown')
        
    elif query.data == "github_workflow":
        await query.edit_message_text("☁️ Triggering GitHub Actions workflow...")
        
        result = await trigger_github_workflow(WORKFLOW_FILE)
        
        if result.get("success"):
            await query.edit_message_text(
                "✅ **GitHub Actions Triggered!**\n\n"
                "The bot is now running in the cloud.\n\n"
                f"🔗 Check status: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions\n\n"
                "The workflow will:\n"
                "• Run the nuclear trading bot\n"
                "• Send email notifications\n"
                "• Log results to GitHub Actions"
            )
        else:
            await query.edit_message_text(f"❌ **Failed to trigger workflow:**\n{result.get('error')}")

# Keep the original command handlers for backward compatibility
async def bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Running bot locally...")
    output = await run_cmd("bot")
    await update.message.reply_text(f"🚀 **Bot Results:**\n```\n{output}\n```", parse_mode='Markdown')

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📧 Running bot with email notification...")
    output = await run_cmd("email")
    await update.message.reply_text(f"📧 **Email Results:**\n```\n{output}\n```", parse_mode='Markdown')

async def alpaca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏦 Running Alpaca trading bot...")
    output = await run_cmd("alpaca")
    await update.message.reply_text(f"🏦 **Alpaca Results:**\n```\n{output}\n```", parse_mode='Markdown')

def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN not set in .env")
        return
    
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set in .env - GitHub Actions features will be disabled")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("bot", bot_command))
    app.add_handler(CommandHandler("email", email_command))
    app.add_handler(CommandHandler("alpaca", alpaca_command))
    app.add_handler(CommandHandler("github", github_command))
    
    # Button callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Telegram bot is running...")
    print(f"GitHub Actions integration: {'✅ Enabled' if GITHUB_TOKEN else '❌ Disabled'}")
    app.run_polling()

if __name__ == "__main__":
    main()
