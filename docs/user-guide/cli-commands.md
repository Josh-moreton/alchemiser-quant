# CLI Commands Reference

Complete reference for all Alchemiser command-line interface commands.

## Overview

The Alchemiser CLI is built with [Typer](https://typer.tiangolo.com/) and provides rich, colorful output via the [Rich](https://rich.readthedocs.io/) library.

## Installation

After installing The Alchemiser, the CLI is available as:

```bash
alchemiser <command> [options]
```

## Core Commands

### `alchemiser bot`

Generate trading signals without executing trades.

```bash
alchemiser bot [OPTIONS]
```

**Purpose**: Analyze market conditions and generate strategy signals for review.

**Options**:
- `--output-format [console|json]` - Output format (default: console)
- `--save-signals / --no-save-signals` - Save signals to file (default: true)
- `--config FILE` - Custom configuration file path

**Examples**:

```bash
# Basic signal generation
alchemiser bot

# Generate signals with JSON output
alchemiser bot --output-format json

# Generate without saving to file
alchemiser bot --no-save-signals
```

**Output**:

```
🎯 NUCLEAR STRATEGY SIGNALS
Current Signal: BEAR_MARKET_DEFENSIVE
Recommended Portfolio:
├── BIL (Treasury Bills): 60.0%
├── UVXY (Volatility): 25.0%
└── PSQ (Tech Short): 15.0%

📊 TECL STRATEGY SIGNALS  
Current Signal: BULL_MARKET_MOMENTUM
Recommended Portfolio:
├── TECL (3x Tech): 70.0%
└── BIL (Cash): 30.0%
```

### `alchemiser trade`

Execute paper or live trades based on strategy signals.

```bash
alchemiser trade [OPTIONS]
```

**Purpose**: Execute automated trading based on generated signals.

**Options**:
- `--live / --paper` - Live trading vs paper trading (default: paper)
- `--email / --no-email` - Send email notifications (default: true for live)
- `--dry-run` - Show what would be traded without executing
- `--force` - Override market hours check
- `--config FILE` - Custom configuration file path

**Examples**:

```bash
# Paper trading (safe)
alchemiser trade

# Live trading with real money ⚠️
alchemiser trade --live

# Dry run - see what would happen
alchemiser trade --dry-run

# Force trading outside market hours
alchemiser trade --force
```

**Output**:

```
📈 EXECUTION SUMMARY
Strategy: Multi-Strategy (Nuclear + TECL)
Execution Mode: Paper Trading

Orders Placed: 3
├── ✅ SELL SPY: 150 shares → $67,425.00
├── ✅ BUY BIL: 825 shares → $40,000.00  
└── ✅ BUY UVXY: 1,250 shares → $25,000.00

Portfolio Value: $132,425.00
Cash Available: $0.00
Execution Time: 3.7 seconds
```

### `alchemiser status`

Display current account status and portfolio information.

```bash
alchemiser status [OPTIONS]
```

**Purpose**: View account overview, positions, and recent performance.

**Options**:
- `--detailed` - Show detailed position information
- `--history [1|7|30]` - Days of history to include (default: 7)
- `--format [table|json]` - Output format (default: table)

**Examples**:

```bash
# Basic status
alchemiser status

# Detailed status with 30 days history
alchemiser status --detailed --history 30

# JSON output for parsing
alchemiser status --format json
```

**Output**:

```
📊 ACCOUNT OVERVIEW
Portfolio Value: $132,425.00
Cash Available: $12,425.00
Day Change: +$2,341.50 (+1.80%)
Market Status: OPEN

🎯 CURRENT POSITIONS
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Symbol      ┃ Shares        ┃ Market Value  ┃ Day Change    ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ BIL         │ 825           │ $40,125.00    │ +$25.00       │
│ UVXY        │ 1,250         │ $27,500.00    │ +$1,250.00    │
│ TECL        │ 500           │ $52,375.00    │ +$1,375.00    │
└─────────────┴───────────────┴───────────────┴───────────────┘
```

### `alchemiser deploy`

Deploy The Alchemiser to AWS Lambda for automated execution.

```bash
alchemiser deploy [OPTIONS]
```

**Purpose**: Build and deploy containerized Lambda function for scheduled trading.

**Options**:
- `--environment [staging|production]` - Deployment environment
- `--schedule TEXT` - Cron schedule (default: daily at 9:35 AM ET)
- `--timeout INTEGER` - Lambda timeout in seconds (default: 300)
- `--memory INTEGER` - Lambda memory in MB (default: 512)

**Examples**:

```bash
# Deploy to staging
alchemiser deploy --environment staging

# Deploy with custom schedule (twice daily)
alchemiser deploy --schedule "0 9,15 * * MON-FRI"

# Deploy with more memory for complex strategies  
alchemiser deploy --memory 1024
```

**Output**:

```
🚀 DEPLOYING TO AWS LAMBDA

Building Docker image...
├── ✅ Base image: python:3.11-slim
├── ✅ Dependencies installed
├── ✅ Code copied
└── ✅ Image built: the-alchemiser:latest

Pushing to ECR...
├── ✅ Repository created: the-alchemiser
├── ✅ Image tagged: latest
└── ✅ Push complete

Creating Lambda function...
├── ✅ Function: the-alchemiser-production
├── ✅ Memory: 512 MB
├── ✅ Timeout: 300 seconds
└── ✅ Schedule: cron(35 9 * * MON-FRI)

🎉 Deployment complete!
Function ARN: arn:aws:lambda:us-east-1:123456789012:function:the-alchemiser-production
```

### `alchemiser version`

Display version and system information.

```bash
alchemiser version [OPTIONS]
```

**Purpose**: Show version, dependencies, and system information for debugging.

**Options**:
- `--check-updates` - Check for available updates
- `--dependencies` - Show all dependency versions

**Examples**:

```bash
# Basic version info
alchemiser version

# Check for updates
alchemiser version --check-updates

# Show all dependencies
alchemiser version --dependencies
```

**Output**:

```
🔧 THE ALCHEMISER VERSION INFORMATION

Version: 2.1.0
Python: 3.11.7
Platform: macOS-14.2.1-arm64
Installation: Development (/Users/joshua/the-alchemiser)

📦 KEY DEPENDENCIES
├── alpaca-py: 0.42.0
├── typer: 0.12.3
├── rich: 13.7.1
├── pandas: 2.1.4
└── requests: 2.31.0

🌐 API CONNECTIVITY
├── ✅ Alpaca Paper API: Connected
├── ✅ TwelveData API: Connected  
└── ✅ WebSocket: Available
```

## Configuration Commands

### Global Options

All commands support these global options:

```bash
--help              # Show command help
--config FILE       # Use custom config file
--verbose          # Enable verbose logging
--quiet            # Suppress output except errors
--log-level LEVEL  # Set logging level (DEBUG|INFO|WARNING|ERROR)
```

### Environment Variables

```bash
# API Configuration
ALPACA_KEY=your_paper_api_key
ALPACA_SECRET=your_paper_secret
ALPACA_LIVE_KEY=your_live_api_key  
ALPACA_LIVE_SECRET=your_live_secret

# Email Configuration  
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com

# Optional Configuration
TWELVE_DATA_API_KEY=your_twelve_data_key
LOG_LEVEL=INFO
```

## Advanced Usage

### Makefile Shortcuts

For convenient development and operation:

```bash
# Development
make install       # Install dependencies and setup
make test         # Run test suite
make lint         # Run code linting

# Trading Operations  
make run-bot      # Generate signals only
make run-trade    # Paper trading
make run-trade-live  # Live trading ⚠️
make status       # Account status

# Deployment
make deploy       # Deploy to AWS Lambda
make logs         # View Lambda logs
```

### Configuration File

Create `config.yaml` for custom settings:

```yaml
# Trading Configuration
trading:
  paper_trading: true
  email_notifications: true
  max_position_size: 0.25
  rebalance_threshold: 0.05

# Strategy Configuration
strategies:
  nuclear:
    enabled: true
    weight: 0.6
    rsi_overbought: 70
    rsi_oversold: 30
    
  tecl:
    enabled: true  
    weight: 0.4
    momentum_threshold: 0.15

# Execution Configuration
execution:
  progressive_orders: true
  websocket_enabled: true
  order_timeout: 300
  max_retries: 3
```

### Output Formats

#### JSON Output

Use `--output-format json` for programmatic consumption:

```json
{
  "timestamp": "2024-01-15T09:35:00Z",
  "strategies": {
    "nuclear": {
      "signal": "BEAR_MARKET_DEFENSIVE",
      "portfolio": {"BIL": 0.6, "UVXY": 0.25, "PSQ": 0.15}
    },
    "tecl": {
      "signal": "NEUTRAL", 
      "portfolio": {"BIL": 1.0}
    }
  },
  "consolidated_portfolio": {"BIL": 0.76, "UVXY": 0.15, "PSQ": 0.09}
}
```

#### CSV Export

Export position data for analysis:

```bash
alchemiser status --format csv > positions.csv
```

## Error Handling

### Common Error Messages

**"Invalid API credentials"**

```bash
# Check credentials
alchemiser status
# Expected: Account info displayed
# Actual: API authentication error

# Solution: Verify .env file configuration
```

**"Market is closed"**

```bash
# Override with --force flag
alchemiser trade --force

# Or wait for market hours (9:30 AM - 4:00 PM ET)
```

**"Insufficient buying power"**

```bash
# Check account status
alchemiser status

# Reduce position sizes in config.yaml
# Or add more funds to account
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Maximum verbosity
alchemiser --log-level DEBUG --verbose trade

# Save logs to file
alchemiser trade 2>&1 | tee trading.log
```

## Integration Examples

### Cron Job Setup

Schedule automated trading:

```bash
# Edit crontab
crontab -e

# Add entry for daily trading at 9:35 AM ET
35 9 * * MON-FRI cd /path/to/alchemiser && alchemiser trade --live
```

### Shell Scripting

```bash
#!/bin/bash
# trading_script.sh

set -e  # Exit on error

echo "Starting Alchemiser trading session..."

# Generate signals first
alchemiser bot --output-format json > signals.json

# Check if signals are bullish
if grep -q "BULL_MARKET" signals.json; then
    echo "Bullish signals detected, executing trades..."
    alchemiser trade --live --email
else
    echo "Defensive signals, using paper trading..."
    alchemiser trade --paper
fi

# Send status update
alchemiser status --detailed | mail -s "Trading Update" user@email.com
```

### Docker Usage

```bash
# Build container
docker build -t alchemiser .

# Run trading session
docker run --env-file .env alchemiser trade

# Interactive session
docker run -it --env-file .env alchemiser bash
```

## Next Steps

- [Trading Modes Guide](../user-guide/trading-modes.md)
- [Configuration Guide](../getting-started/configuration.md)
- [Email Notifications Setup](../user-guide/email-notifications.md)
