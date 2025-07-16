# Nuclear Trading Strategy

A comprehensive nuclear energy trading strategy with unified entry points and automated daily execution via GitHub Actions.

## 🚀 Quick Start Guide

### Main Entry Point

All nuclear trading operations are accessed through a single unified entry point:

```bash
python main.py <mode> [options]
```

### Available Modes

#### 🤖 `bot` - Live Trading Signal Generation

Generate live nuclear trading signals without email notifications.

```bash
python main.py bot
```

**What it does:**

- Fetches live market data for all nuclear and market symbols
- Calculates technical indicators (RSI, moving averages, etc.)
- Evaluates nuclear strategy logic and generates trading signals
- Logs alerts to `data/logs/nuclear_alerts.json`
- Displays portfolio allocations for nuclear portfolio signals

**Example Output:**

```text
🚨 NUCLEAR PORTFOLIO SIGNAL: 3 stocks allocated
🎯 NUCLEAR PORTFOLIO ALLOCATION:
   🟢 BUY SMR at $37.48 (31.2%)
   🟢 BUY LEU at $206.40 (39.5%)
   🟢 BUY OKLO at $56.08 (29.3%)
```

#### 📧 `email` - Live Trading with Email Notifications

Generate live trading signals AND send email notifications when signals change.

```bash
python main.py email
```

#### 🦙 `alpaca` - Automated Trading with Alpaca Paper Account

**Requirements:**

- Environment variable `SMTP_PASSWORD` must be set with iCloud app password
- Configured for: `joshuamoreton1@icloud.com` → `josh@rwxt.org`

**Automated Email Alerts:**

- Sends a detailed email notification after every Alpaca bot execution (success or failure)
- Email includes: execution status, account value before/after, cash changes, all positions, and log references
- Uses the same SMTP configuration as the main bot
- No longer requires a signal change to send an email (always notifies)

**Example Email Content:**

```text
Nuclear Alpaca Bot Execution Report - 2025-07-15 13:45:22

✅ EXECUTION STATUS: SUCCESS

📈 ACCOUNT SUMMARY:
   Portfolio Value Before: $100,000.00
   Portfolio Value After:  $101,250.00
   Portfolio Change:       $+1,250.00 (+1.25%)
   
   Cash Before: $10,000.00
   Cash After:  $5,000.00
   Cash Change: $-5,000.00

📊 CURRENT POSITIONS:
   SMR: 156.0 shares @ $40.00 = $31,200.00
   LEU: 197.5 shares @ $200.00 = $39,500.00
   OKLO: 486.67 shares @ $60.00 = $29,200.00

🤖 EXECUTION DETAILS:
   Strategy: Nuclear Energy Portfolio Rebalancing
   Trading Mode: Paper Trading (Alpaca)
   Execution Time: 13:45:22
```

### Alpaca Setup & Environment Variables

### Email & Alpaca Notification Setup

- Set the `SMTP_PASSWORD` environment variable with your iCloud app password for all email features (including Alpaca execution alerts)
- Alpaca mode now always sends a detailed email after every run, regardless of signal change

## 🤖 Automated Execution (GitHub Actions)

### Environment Setup

#### For Email Notifications

```bash
export SMTP_PASSWORD="your-icloud-app-password"
```

**To get iCloud app password:**

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Security → Generate App-Specific Password
3. Name: "Nuclear Trading Bot"
4. Use generated password as `SMTP_PASSWORD`

## 📁 Project Structure

```text
LQQ3/
├── main.py                     # 🎯 UNIFIED ENTRY POINT (all operations)
├── src/
│   ├── core/                   # Core trading components
│   │   ├── nuclear_trading_bot.py     # Main trading strategy
│   │   └── nuclear_signal_email.py    # Email notifications
│   └── execution/              # Alpaca trading integration
│       └── alpaca_trader.py    # Alpaca trading bot
├── tests/                      # Test suite
├── data/                       # Data storage & results
│   └── logs/                   # Live trading alerts and logs
├── .github/workflows/          # 🤖 AUTOMATED EXECUTION
│   └── nuclear_daily_signal.yml       # Hourly GitHub Action
└── requirements.txt            # Python dependencies
```

**Key Files:**

- **`main.py`** - Single entry point for all operations
- **`src/core/nuclear_trading_bot.py`** - Core trading strategy and signal generation
- **`src/core/nuclear_signal_email.py`** - Email notification system
- **`src/execution/alpaca_trader.py`** - Alpaca trading integration
- **`.github/workflows/nuclear_daily_signal.yml`** - Automated hourly execution

## 🤖 Automated Execution

The system runs automatically via **GitHub Actions** every hour:

- **Command:** `python main.py email`
- **Functions:** Generates trading signals, sends email notifications only when signals change
- **Manual Trigger:** Available via GitHub Actions UI
- **Environment:** `SMTP_PASSWORD` configured as repository secret

**GitHub Actions Workflow:**

```yaml
- name: Run Nuclear Trading Bot with Email
  env:
    SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
  run: python main.py email
```

## 📊 Latest Performance

The nuclear strategy has demonstrated exceptional performance:

- **Total Return:** +54.05% (3 months)
- **CAGR:** +501.00% (annualized)
- **Sharpe Ratio:** 2.39
- **Max Drawdown:** -20.15%
- **Win Rate:** 60.32%
- **Optimal Execution:** 9:30 AM (market open)

## 🔧 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Josh-moreton/LQQ3.git
   cd LQQ3
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (for email mode):**

   ```bash
   export SMTP_PASSWORD="your-icloud-app-password"
   ```

## 📈 Usage Examples

### Daily Operations

```bash
# Generate live trading signal (local use)
python main.py bot

# Generate signal + email notifications (production)
python main.py email
```

### Development & Testing

```bash
# Test email functionality (requires SMTP_PASSWORD)
python main.py email
```

## Key Features

- **Nuclear Strategy**: Focus on nuclear energy ETFs and leveraged instruments
- **Execution Timing**: Optimized for 9:30 AM market open execution
- **Risk Management**: No leverage (instruments are already leveraged)
- **Data Management**: Organized storage of results, logs, and market data

## File Organization

- **Core Components** (`src/core/`): Main trading logic and strategy
- **Execution** (`src/execution/`): Trade execution and timing optimization
- **Tests** (`tests/`): Unit tests and integration tests
- **Data** (`data/`): Organized storage for results, logs, and market data

## 📋 Quick Reference

### Main.py Modes Summary

| Mode   | Command                | Purpose                              | Output                |
|--------|------------------------|--------------------------------------|-----------------------|
| **bot**   | `python main.py bot`    | Live signal generation               | Console + JSON logs   |
| **email** | `python main.py email`  | Live signals + email alerts          | Console + Email       |
| **alpaca**| `python main.py alpaca` | Automated trading with Alpaca + email alert | Console + Email |

### For Production Use

- **Automated Trading**: `python main.py email` (GitHub Actions hourly)
- **Manual Check**: `python main.py bot`
- **Alpaca Trading**: `python main.py alpaca`

### Other Key Features

- ✅ **Unified Entry Point**: One command for all operations
- ✅ **Smart Email Alerts**: Only sends when signals change
- ✅ **Automated Execution**: GitHub Actions daily monitoring
- ✅ **Organized Data**: All outputs properly structured in `data/` directory
