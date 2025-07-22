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

Generate live nuclear trading signals and log them locally.

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

#### 🚀 `live` - Automated Trading with Telegram Updates

Execute trades via Alpaca and send a Telegram summary after every run.

```bash
python main.py live
```

**Requirements:**

- Environment variables `ALPACA_KEY` and `ALPACA_SECRET`
- Environment variables `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`

**Example Telegram Message:**

```text
🚀 Nuclear Alpaca Bot Execution Report

✅ EXECUTION STATUS: SUCCESS
Portfolio Value: $101,250.00 (+1,250.00 / +1.3%)
Cash: $5,000.00 (4.9% of portfolio)

📊 Positions:
 - SMR: 156 @ $40.00 (P&L +12.0%, 31.2% alloc)
 - LEU: 198 @ $200.00 (P&L +8.5%, 39.5% alloc)
 - OKLO: 487 @ $60.00 (P&L -2.3%, 29.3% alloc)
Top gainer: SMR (+12.0%), Worst: OKLO (-2.3%)

📝 Orders:
 - BUY SMR 50 ($2,000.00)
 - SELL LEU 30 ($6,000.00)
```

### Alpaca & Telegram Setup

Provide your Alpaca API keys and Telegram bot credentials via environment variables before running the bot:

```bash
export ALPACA_KEY="your-alpaca-key"
export ALPACA_SECRET="your-alpaca-secret"
export TELEGRAM_TOKEN="your-telegram-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## 🤖 Automated Execution (GitHub Actions)

## 📁 Project Structure

```text
LQQ3/
├── main.py                     # 🎯 UNIFIED ENTRY POINT (all operations)
├── core/                       # Core trading components
│   ├── nuclear_trading_bot.py  # Main trading strategy
│   ├── telegram_utils.py       # Telegram helpers
│   └── email_utils.py          # Email helper functions
├── execution/                  # Alpaca trading integration
│   └── alpaca_trader.py        # Alpaca trading bot
├── tests/                      # Test suite
├── data/                       # Data storage & results
│   └── logs/                   # Live trading alerts and logs
├── .github/workflows/          # 🤖 AUTOMATED EXECUTION
│   └── nuclear_alpaca_trading.yml     # Daily trading workflow
└── requirements.txt            # Python dependencies
```

**Key Files:**

- **`main.py`** - Single entry point for all operations
- **`core/nuclear_trading_bot.py`** - Core trading strategy and signal generation
- **`core/telegram_utils.py`** - Telegram messaging utilities
- **`execution/alpaca_trader.py`** - Alpaca trading integration
- **`.github/workflows/nuclear_alpaca_trading.yml`** - Daily trading workflow

## 🤖 Automated Execution

The system runs automatically via **GitHub Actions**:

- **Command:** `python main.py live`
- **Functions:** Generates trading signals, executes trades, sends Telegram update
- **Manual Trigger:** Available via GitHub Actions UI
- **Environment:** `ALPACA_KEY`, `ALPACA_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

**GitHub Actions Workflow:**

```yaml
- name: Run Nuclear Trading Bot
  env:
    ALPACA_KEY: ${{ secrets.ALPACA_KEY }}
    ALPACA_SECRET: ${{ secrets.ALPACA_SECRET }}
    TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: python main.py live
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

3. **Set up environment variables:**

```bash
export ALPACA_KEY="your-alpaca-key"
export ALPACA_SECRET="your-alpaca-secret"
export TELEGRAM_TOKEN="your-telegram-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## 📈 Usage Examples

### Daily Operations

```bash
# Generate live trading signal (local use)
python main.py bot

# Run automated trading with Telegram updates
python main.py live
```

### Development & Testing

```bash
# Run the live trading flow with your credentials
python main.py live
```

## Key Features

- **Nuclear Strategy**: Focus on nuclear energy ETFs and leveraged instruments
- **Execution Timing**: Optimized for 9:30 AM market open execution
- **Risk Management**: No leverage (instruments are already leveraged)
- **Data Management**: Organized storage of results, logs, and market data

## File Organization

- **Core Components** (`core/`): Main trading logic and strategy
- **Execution** (`execution/`): Trade execution and timing optimization
- **Tests** (`tests/`): Unit tests and integration tests
- **Data** (`data/`): Organized storage for results, logs, and market data

## 📋 Quick Reference

### Main.py Modes Summary

| Mode   | Command                | Purpose                              | Output                |
|--------|------------------------|--------------------------------------|-----------------------|
| **bot**   | `python main.py bot`    | Live signal generation               | Console + JSON logs   |
| **live**  | `python main.py live`   | Automated trading with Telegram update | Console + Telegram |

### For Production Use

- **Automated Trading**: `python main.py live` (GitHub Actions)
- **Manual Check**: `python main.py bot`

### Other Key Features

- ✅ **Unified Entry Point**: One command for all operations
- ✅ **Automated Execution**: GitHub Actions daily monitoring
- ✅ **Organized Data**: All outputs properly structured in `data/` directory
