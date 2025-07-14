# Nuclear Trading Bot - Email Setup Guide

## Overview

The Nuclear Trading Bot now supports automatic email notifications when trading signals change. This guide shows how to set up and run the full email-enabled live bot.

## Email Features

### What Gets Emailed:
- **Signal Changes**: Only when the nuclear strategy signal changes (reduces spam)
- **Portfolio Details**: Complete breakdown when nuclear portfolio is active
- **Market Context**: SPY price, RSI levels, market regime analysis
- **Error Notifications**: If the bot encounters issues

### Email Content:
- 📊 Current market conditions (SPY price, RSI, market regime)
- 🎯 Trading signal details (symbol, action, reason)
- 📈 Portfolio allocation (for multi-stock signals)
- ⚠️ Risk disclaimers and educational notices

## Setup Instructions

### 1. Email Configuration

The bot is configured to use **Apple iCloud SMTP** with these settings:
- **SMTP Server**: `smtp.mail.me.com`
- **Port**: `587`
- **From Email**: `joshuamoreton1@icloud.com`
- **To Email**: `josh@rwxt.org`

### 2. Environment Variables

You need to set the `SMTP_PASSWORD` environment variable with your iCloud app password:

```bash
# For local testing
export SMTP_PASSWORD="your-icloud-app-password"

# For GitHub Actions (already configured in secrets)
# SMTP_PASSWORD is set as a repository secret
```

### 3. iCloud App Password Setup

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in and go to "Security" section
3. Generate an App-Specific Password for "Nuclear Trading Bot"
4. Use this password as your `SMTP_PASSWORD`

## Running the Email Bot

### Option 1: Main Launcher (Recommended)
```bash
# Run the full email-enabled nuclear trading bot
python main.py email
```

### Option 2: Direct Email Bot
```bash
# Alternative direct launcher
python run_email_bot.py
```

### Option 3: Test Email Only
```bash
# Test just the email functionality
cd src/core && python nuclear_signal_email.py
```

## Expected Output

### When Signal Changes:
```
🚀 NUCLEAR TRADING BOT - EMAIL MODE
============================================================
Running live trading analysis with email notifications at 2025-07-14 11:21:37

🚀 Nuclear Energy Daily Signal Check (Email Only)
==================================================
✅ Signal fetched successfully: BUY NUCLEAR_PORTFOLIO
   Reason: Bull market - Nuclear portfolio: SMR (31.2%), LEU (39.5%), OKLO (29.3%)
   Signal changed: True
📧 Signal changed - sending email...
Connecting to SMTP server: smtp.mail.me.com:587 as joshuamoreton1@icloud.com
EHLO...
Starting TLS...
EHLO again...
Logging in...
Sending email...
Email sent successfully to josh@rwxt.org
```

### When No Signal Change:
```
✅ Signal fetched successfully: BUY NUCLEAR_PORTFOLIO
   Reason: Bull market - Nuclear portfolio: SMR (31.2%), LEU (39.5%), OKLO (29.3%)
   Signal changed: False
📊 No signal change. No email sent.
```

## GitHub Actions Integration

The GitHub Actions workflow has been updated to use the email mode:

```yaml
- name: Run Nuclear Trading Bot with Email
  env:
    SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
  run: python main.py email
```

### Hourly Execution
- Runs every hour (0 minutes past the hour)
- Only sends email when signals actually change
- Logs errors and uploads artifacts on failure

## Email Content Example

```
Subject: 🔄 SIGNAL CHANGE: Nuclear Energy - BUY Nuclear Portfolio (2025-07-14)

Nuclear Energy Strategy Signal - 2025-07-14

🚨 SIGNAL: BUY Nuclear Portfolio 🔄 SIGNAL CHANGED!

📊 MARKET CONDITIONS:
• SPY Price: $623.62
• SPY 200-MA: $580.82
• SPY vs MA: +7.4%
• SPY RSI(10): 72.1
• Market Regime: Bull

🎯 SIGNAL DETAILS:
• Symbol: NUCLEAR_PORTFOLIO
• Action: BUY
• Reason: Bull market - Nuclear portfolio: SMR (31.2%), LEU (39.5%), OKLO (29.3%)

📈 NUCLEAR PORTFOLIO ALLOCATION:
• SMR: 31.2% at $37.48
• LEU: 39.5% at $206.40  
• OKLO: 29.3% at $56.08

📈 TRADING GUIDANCE:
• This is a deterministic strategy with no confidence scoring
• Signals are based on RSI levels, moving averages, and market regimes
• In bull markets: Focus on nuclear energy portfolio
• In bear markets: Tech shorts and bond/volatility plays
• In overbought conditions: Volatility protection (UVXY)

⚠️ IMPORTANT: This is for educational purposes only. Not financial advice.
Always do your own research before making trading decisions.

Nuclear Energy Strategy | Based on Composer.trade Symphony
```

## Troubleshooting

### Common Issues:

1. **SMTP_PASSWORD not set**:
   ```
   ❌ SMTP_PASSWORD environment variable not set. Email not sent.
   ```
   **Solution**: Set the environment variable with your iCloud app password

2. **SMTP Authentication Error**:
   ```
   Failed to send email: (535, b'5.7.8 Error: authentication failed')
   ```
   **Solution**: Generate a new iCloud app-specific password

3. **Import Errors**:
   ```
   Import "core.nuclear_signal_email" could not be resolved
   ```
   **Solution**: This is a linter warning, the code works at runtime

## Summary

- ✅ **`python main.py email`** - Full email-enabled live bot
- ✅ **`python run_email_bot.py`** - Alternative launcher  
- ✅ **GitHub Actions** - Updated to use email mode
- ✅ **Smart Notifications** - Only emails on signal changes
- ✅ **Rich Content** - Complete market analysis and portfolio details
