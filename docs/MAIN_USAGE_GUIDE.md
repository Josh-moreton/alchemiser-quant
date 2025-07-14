# Nuclear Trading Strategy - Main.py Usage Guide

## Overview

`main.py` is the unified entry point for all Nuclear Trading Strategy operations. It provides a single command-line interface to access all functionality including live trading, email notifications, backtesting, and dashboard.

## Basic Usage

```bash
python main.py <mode> [options]
```

## Available Modes

### 🚀 `bot` - Live Trading Signal Generation

**Purpose**: Generate live nuclear trading signals without email notifications

**Usage**:
```bash
python main.py bot
```

**What it does**:
- Fetches live market data for all nuclear and market symbols
- Calculates technical indicators (RSI, moving averages, etc.)
- Evaluates nuclear strategy logic
- Generates trading signals (BUY/SELL/HOLD)
- Logs alerts to `data/logs/nuclear_alerts.json`
- Displays portfolio allocations for nuclear portfolio signals

**Output Files**:
- `data/logs/nuclear_alerts.json` - JSON log of all alerts
- `data/logs/nuclear_alerts.log` - Detailed logging

**Example Output**:
```
🚀 NUCLEAR TRADING BOT - LIVE MODE
============================================================
🚨 NUCLEAR PORTFOLIO SIGNAL: 3 stocks allocated

🎯 NUCLEAR PORTFOLIO ALLOCATION:
   🟢 BUY SMR at $37.48
      Reason: Nuclear portfolio allocation: 31.2%
   🟢 BUY LEU at $206.40
      Reason: Nuclear portfolio allocation: 39.5%
   🟢 BUY OKLO at $56.08
      Reason: Nuclear portfolio allocation: 29.3%

✅ Signal generated successfully!
📁 Alert logged to: data/logs/nuclear_alerts.json
```

---

### 📧 `email` - Live Trading with Email Notifications

**Purpose**: Generate live nuclear trading signals AND send email notifications when signals change

**Usage**:
```bash
python main.py email
```

**Requirements**:
- Environment variable `SMTP_PASSWORD` must be set with iCloud app password
- Configured for: `joshuamoreton1@icloud.com` → `josh@rwxt.org`

**What it does**:
- Everything that `bot` mode does
- Compares current signal with previous signal
- **Only sends email if signal has changed** (smart notifications)
- Sends detailed email with market analysis and portfolio breakdown
- Handles error notifications via email

**Email Content Includes**:
- 📊 Market conditions (SPY price, RSI, market regime)
- 🎯 Signal details (symbol, action, reason)
- 📈 Portfolio allocations (for multi-stock signals)
- ⚠️ Risk disclaimers and educational notices

**Example Output**:
```
🚀 NUCLEAR TRADING BOT - EMAIL MODE
============================================================
📧 Starting email-enabled nuclear trading bot...
✅ Signal fetched successfully: BUY NUCLEAR_PORTFOLIO
   Signal changed: True
📧 Signal changed - sending email...
Email sent successfully to josh@rwxt.org
```

---

### 📈 `backtest` - Strategy Backtesting

**Purpose**: Test nuclear strategy performance against historical data

**Usage**:
```bash
# Comprehensive backtest (default)
python main.py backtest

# Hourly execution backtest
python main.py backtest --backtest-type hourly
```

**Options**:
- `--backtest-type comprehensive` - Tests multiple execution strategies
- `--backtest-type hourly` - Tests hourly execution timing

**What it does**:
- Downloads historical market data
- Simulates nuclear strategy over specified time period
- Tests different execution timings (open, close, 10AM, 2PM)
- Calculates performance metrics (returns, Sharpe ratio, drawdown)
- Generates comparative analysis

**Output Files**:
- `data/backtest_results/nuclear_comprehensive_report_YYYYMMDD_HHMMSS.json`
- `data/backtest_results/nuclear_trades_YYYYMMDD_HHMMSS.csv`
- `data/backtest_results/nuclear_portfolio_YYYYMMDD_HHMMSS.csv`

**Example Output**:
```
📈 NUCLEAR STRATEGY BACKTEST
============================================================
🚀 COMPREHENSIVE NUCLEAR STRATEGY BACKTEST
============================================================
Period: 2024-07-01 to 2024-09-30
Initial Capital: $100,000.00

EXECUTION STRATEGY COMPARISON:
Strategy               Total Return  Sharpe Ratio  Max Drawdown
Open Execution         +15.2%        1.85          -8.3%
Close Execution        +18.7%        2.12          -7.1%
2PM Execution          +19.1%        2.18          -6.9%

BEST STRATEGY: 2PM Execution (19.1% return, 2.18 Sharpe)
```

---

### 📊 `dashboard` - Interactive Web Dashboard

**Purpose**: Launch Streamlit web dashboard for interactive analysis

**Usage**:
```bash
python main.py dashboard
```

**What it provides**:
- Real-time trading signal display
- Interactive charts and visualizations
- Historical signal analysis
- Portfolio allocation breakdown
- Market condition monitoring
- Live backtesting interface

**Access**: Opens browser at `http://localhost:8501`

**Features**:
- 📊 Current market signal with portfolio details
- 📈 Historical performance charts
- 🎯 Signal history timeline
- 📋 Interactive backtesting controls
- 💹 Real-time market data display

---

### ⏰ `hourly-test` - Hourly Execution Testing

**Purpose**: Specialized backtest focusing on hourly execution timing

**Usage**:
```bash
python main.py hourly-test
```

**What it does**:
- Runs backtest with hourly data granularity
- Tests precise timing of trade execution
- Optimizes for intraday signal generation
- Measures timing impact on performance

**Use Case**: Testing optimal execution times for automated trading

---

## Environment Variables

### Required for Email Mode

```bash
# iCloud App-Specific Password
export SMTP_PASSWORD="your-icloud-app-password"
```

**To get iCloud app password**:
1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Security → Generate App-Specific Password
3. Name: "Nuclear Trading Bot"
4. Use generated password as `SMTP_PASSWORD`

## File Structure

### Input Requirements
- `requirements.txt` - Python dependencies
- `src/` - Source code directory with organized modules

### Output Locations
- `data/logs/` - Live trading alerts and logs
- `data/backtest_results/` - Backtest reports and CSV files
- Console output for immediate feedback

## Usage Examples

### Daily Live Signal Check
```bash
# Just generate signal (no email)
python main.py bot

# Generate signal + email if changed
python main.py email
```

### Strategy Analysis
```bash
# Full backtest analysis
python main.py backtest

# Test hourly execution timing
python main.py hourly-test

# Interactive analysis
python main.py dashboard
```

### GitHub Actions / Automation
```bash
# Recommended for automated hourly execution
python main.py email
```

## Error Handling

- All modes include comprehensive error handling
- Failed operations exit with code 1
- Successful operations exit with code 0
- Errors logged to console and log files
- Email mode sends error notifications

## Performance Notes

- **Bot mode**: ~30-60 seconds (live data fetch + analysis)
- **Email mode**: +5-10 seconds (email sending)
- **Backtest mode**: 2-5 minutes (historical data processing)
- **Dashboard mode**: Immediate startup, continuous running
- **Hourly-test**: 1-3 minutes (focused backtest)

## Tips

1. **For development**: Use `bot` mode for quick signal testing
2. **For production**: Use `email` mode for automated monitoring
3. **For analysis**: Use `backtest` mode for strategy validation
4. **For presentation**: Use `dashboard` mode for interactive demos
5. **For optimization**: Use `hourly-test` mode for timing analysis

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in the project root directory
cd /path/to/LQQ3
python main.py <mode>
```

**Email Not Sending**:
```bash
# Check environment variable
echo $SMTP_PASSWORD

# Test with local signal generation first
python main.py bot
```

**Backtest Errors**:
```bash
# Check internet connection (needs Yahoo Finance data)
# Verify date ranges in backtest configuration
```

## Summary

`main.py` is your one-stop command center for:
- ✅ **Live Trading**: Real-time signal generation
- ✅ **Email Alerts**: Smart notifications on signal changes  
- ✅ **Backtesting**: Historical strategy validation
- ✅ **Dashboard**: Interactive web interface
- ✅ **Analysis**: Performance optimization tools

Use `python main.py <mode>` for all nuclear trading operations!
