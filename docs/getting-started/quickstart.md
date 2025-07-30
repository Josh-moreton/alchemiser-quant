# Quick Start Guide

Get The Alchemiser up and running in under 10 minutes.

## Prerequisites

- Python 3.11 or higher
- Alpaca Markets account (free paper trading)
- macOS, Linux, or Windows with WSL

## 1. Installation

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Using Make (Recommended for macOS)

```bash
make install  # Sets up everything automatically
```

## 2. Configuration

### Get Alpaca API Keys

1. Visit [Alpaca Markets](https://alpaca.markets) and create a free account
2. Go to your dashboard and generate **Paper Trading** API keys
3. Copy your API Key and Secret Key

### Setup Environment

Create a `.env` file in the project root:

```bash
# Paper Trading (Safe for testing)
ALPACA_KEY=your_paper_api_key_here
ALPACA_SECRET=your_paper_secret_here

# Optional: Email notifications
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient@email.com
```

## 3. Your First Run

### Check Installation

```bash
alchemiser version
```

### View Account Status

```bash
alchemiser status
```

Expected output:

```
📊 ACCOUNT OVERVIEW
Portfolio Value: $100,000.00
Cash Available: $100,000.00
Market Status: OPEN
```

### Generate Trading Signals

```bash
alchemiser bot
```

This will:

- Analyze current market conditions
- Generate strategy signals
- Display recommended allocations
- **NOT execute any trades**

### Execute Paper Trades

```bash
alchemiser trade
```

This will:

- Generate signals
- Execute trades in your paper account
- Show execution results
- Update your portfolio

### View Results

```bash
alchemiser status
```

You should now see your portfolio allocated across different assets based on the strategy signals.

## 4. Understanding the Output

### Strategy Signals

```
🎯 NUCLEAR STRATEGY SIGNALS
Current Signal: BEAR_MARKET_DEFENSIVE
Recommended Portfolio:
├── BIL (Treasury Bills): 60.0%
├── UVXY (Volatility): 25.0%
└── PSQ (Tech Short): 15.0%
```

### Execution Results

```
📈 EXECUTION SUMMARY
Orders Placed: 3
├── ✅ BUY BIL: $60,000 (filled)
├── ✅ BUY UVXY: $25,000 (filled)
└── ✅ BUY PSQ: $15,000 (filled)

Total Value: $100,000
Execution Time: 2.3 seconds
```

## 5. Next Steps

### Enable Live Trading (Real Money) ⚠️

**Only after you're comfortable with paper trading:**

```bash
# Add live trading keys to .env
ALPACA_LIVE_KEY=your_live_api_key
ALPACA_LIVE_SECRET=your_live_secret

# Execute live trades
alchemiser trade --live
```

### Setup Email Notifications

See [Email Setup Guide](../user-guide/email-notifications.md) for detailed instructions.

### Explore Strategies

- [Nuclear Strategy](../strategies/nuclear.md) - Market regime detection
- [TECL Strategy](../strategies/tecl.md) - Technology momentum
- [Multi-Strategy](../strategies/multi-strategy.md) - Combined approach

### Deploy to AWS Lambda

```bash
alchemiser deploy
```

See [Lambda Deployment Guide](../deployment/lambda.md) for details.

## Troubleshooting

### Common Issues

**"Command not found: alchemiser"**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -e .
```

**"Invalid API credentials"**

```bash
# Check your .env file format
cat .env

# Verify keys are correct in Alpaca dashboard
```

**"Market is closed"**

```bash
# Paper trading works 24/7, but signals may warn about market hours
alchemiser trade --force  # Override market hours check
```

### Getting Help

- [Full Documentation](../README.md)
- [GitHub Issues](https://github.com/Josh-moreton/the-alchemiser/issues)
- [Debugging Guide](../development/debugging.md)

---

**🎉 Congratulations!** You've successfully set up The Alchemiser and executed your first automated trades.
