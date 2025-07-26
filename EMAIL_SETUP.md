# Email Notification Setup Guide

## Overview

The Alchemiser now uses beautiful HTML email notifications instead of Telegram. These emails are built with Maizzle-inspired responsive design and provide comprehensive trading reports.

## Email Configuration Options

### Option 1: Config.yaml + AWS Secrets (Recommended)

1. **Update config.yaml** with your email settings:

```yaml
# Email notification configuration
email:
  smtp_server: "smtp.mail.me.com"
  smtp_port: 587
  from_email: "your-email@icloud.com"    # Your iCloud email
  to_email: "your-email@icloud.com"      # Where to send notifications
  # smtp_password is stored separately in AWS Secrets Manager
```

2. **Store password in AWS Secrets Manager** under your existing `nuclear-secrets`:

```json
{
  "email_password": "your-app-specific-password",
  // ... your other secrets like ALPACA_KEY, etc.
}
```

### Option 2: Environment Variables (Local Development)

Set the following environment variables:

```bash
export SMTP_SERVER="smtp.mail.me.com"
export SMTP_PORT="587"
export EMAIL_ADDRESS="your-email@icloud.com"
export EMAIL_PASSWORD="your-app-specific-password"
export RECIPIENT_EMAIL="your-email@icloud.com"
```

## iCloud Mail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Apple ID account
2. **Generate an App-Specific Password**:
   - Go to [appleid.apple.com](https://appleid.apple.com) and sign in
   - In the Security section, under "App-Specific Passwords", click "Generate Password"
   - Enter a label like "Alchemiser Trading Bot"
   - Copy the generated password (format: xxxx-xxxx-xxxx-xxxx)
   - Use this password in your configuration (not your regular iCloud password)

3. **Configuration Values**:
   - SMTP Server: `smtp.mail.me.com`
   - SMTP Port: `587`
   - Email Address: Your iCloud email address (@icloud.com, @me.com, or @mac.com)
   - Email Password: The app-specific password (16 characters with dashes)
   - Recipient Email: Where you want to receive notifications (can be same as sender)

## Other Email Providers

### Gmail

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Outlook/Hotmail

```
SMTP_SERVER=smtp.live.com
SMTP_PORT=587
```

### Yahoo Mail

```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Custom SMTP Server

Use your hosting provider's SMTP settings.

## Email Templates

The system includes several beautiful HTML email templates:

### 1. Trading Report Email

- **Trigger**: After successful multi-strategy execution (live trading only)
- **Content**:
  - Account summary with portfolio value and cash
  - Strategy signals and allocations
  - Trading activity with buy/sell orders
  - Open positions with P&L
  - Beautiful responsive design with The Alchemiser branding

### 2. Error Alert Email

- **Trigger**: When trading errors occur or market is closed
- **Content**:
  - Error details and timestamps
  - Clear red styling for urgent attention
  - Technical error information for debugging

### 3. Multi-Strategy Email

- **Trigger**: Multi-strategy execution completion
- **Content**:
  - Strategy allocation breakdown
  - Portfolio composition
  - Trading summary
  - Performance metrics

## Features

### Responsive Design

- Mobile-friendly layout
- Professional styling with gradients and shadows
- Clear typography and color coding
- The Alchemiser brand colors (orange/red gradient)

### Rich Content

- 📊 Portfolio allocations with percentages
- ⚡ Trading activity tables
- 💰 P&L calculations with color coding
- 🎯 Strategy signals and reasoning
- 📈 Technical indicator summaries

### Fallback Support

- HTML content with plain text fallback
- MSO/Outlook compatibility
- Robust error handling

## Testing Email Setup

To test your email configuration, you can create a simple test script:

```python
from the_alchemiser.core.ui.email_utils import send_email_notification, build_error_email_html

# Test basic email sending
html_content = build_error_email_html("Test Alert", "This is a test email from The Alchemiser")
success = send_email_notification(
    subject="🧪 The Alchemiser - Email Test",
    html_content=html_content,
    text_content="Test email from The Alchemiser trading bot"
)

if success:
    print("✅ Email sent successfully!")
else:
    print("❌ Email failed to send. Check your configuration.")
```

Or run the provided test script:

```bash
cd /Users/joshua.moreton/Documents/GitHub/The-Alchemiser
python scripts/test_email_setup.py
```

## Migration from Telegram

The following changes have been made:

1. **Removed**: `telegram_utils.py` dependencies
2. **Removed**: `send_telegram_message()` function calls
3. **Added**: `email_utils.py` with comprehensive email functionality
4. **Added**: Beautiful HTML templates inspired by Maizzle framework
5. **Updated**: `main.py` to use email notifications instead of Telegram

### Email vs Telegram Benefits

- ✅ **Rich formatting**: HTML tables, colors, responsive design
- ✅ **No API limits**: No bot token or chat ID required
- ✅ **Better archival**: Emails are automatically stored
- ✅ **Professional appearance**: Beautiful branded templates
- ✅ **Enhanced content**: More detailed trading information
- ✅ **Universal access**: Works with any email provider

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure you're using an app password, not your regular password
   - Check that 2FA is enabled on your account

2. **Connection Refused**
   - Verify SMTP server and port settings
   - Check firewall settings

3. **Emails Not Received**
   - Check spam/junk folder
   - Verify recipient email address
   - Test with a different email provider

4. **HTML Not Rendering**
   - The system includes plain text fallback
   - Most modern email clients support HTML

### Debug Mode

Enable verbose logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- **Never commit email passwords** to version control
- **Use app passwords** instead of account passwords
- **Store credentials securely** in AWS Secrets Manager for production
- **Limit recipient list** to authorized personnel only
- **Regular credential rotation** is recommended

The email notification system provides a more professional and feature-rich alternative to Telegram notifications, with beautiful HTML templates that make monitoring your trading bot a pleasure.
