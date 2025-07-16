# Telegram Bot Setup Guide

## 1. GitHub Personal Access Token

To enable GitHub Actions integration, you need to create a GitHub Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "LQQ3 Telegram Bot"
4. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
5. Click "Generate token"
6. Copy the token and add it to your `.env` file:

```bash
GITHUB_TOKEN=your_github_token_here
```

## 2. Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python telegram_bot.py
```

## 3. Using the Bot

1. Start a chat with your bot on Telegram
2. Send `/start` to see the interactive menu
3. Use buttons or text commands:
   - 🚀 Local execution (runs on your machine)
   - ☁️ GitHub Actions (runs in the cloud)

## 4. Features

- **Interactive Buttons**: Easy-to-use interface
- **Local Execution**: Run commands directly on your machine
- **GitHub Actions**: Trigger cloud workflows
- **Real-time Results**: Get immediate feedback
- **Backward Compatible**: Text commands still work

## 5. Commands

- `/start` - Show main menu with buttons
- `/help` - Show help message
- `/bot` - Run trading bot locally
- `/email` - Run with email notifications
- `/alpaca` - Run with Alpaca trading
- `/github` - Trigger GitHub Actions workflow

## 6. Security Notes

- Keep your `TELEGRAM_TOKEN` and `GITHUB_TOKEN` secure
- Never commit these tokens to version control
- Use environment variables only
