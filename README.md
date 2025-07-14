# Nuclear Trading Strategy

A comprehensive nuclear energy trading strategy with unified entry points, backtesting framework, and automated hourly execution via GitHub Actions.

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

```
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

**Requirements:**

- Environment variable `SMTP_PASSWORD` must be set with iCloud app password
- Configured for: `joshuamoreton1@icloud.com` → `josh@rwxt.org`

**Smart Notifications:**

- Only sends email when signals actually change (reduces spam)
- Includes market analysis, portfolio breakdown, and risk disclaimers
- Sends error notifications if bot encounters issues

**Example Email Content:**

```
🔄 SIGNAL CHANGE: Nuclear Energy - BUY Nuclear Portfolio
📊 Market Conditions: SPY $623.62 (+7.4% vs 200-MA)
🎯 Nuclear Portfolio: SMR (31.2%), LEU (39.5%), OKLO (29.3%)
```

#### 📈 `backtest` - Strategy Backtesting

Test nuclear strategy performance against historical data.

```bash
# Comprehensive backtest (default)
python main.py backtest

# Hourly execution timing analysis
python main.py backtest --backtest-type hourly
```

**Features:**

- Tests multiple execution strategies (open, close, 10AM, 2PM)
- Calculates performance metrics (returns, Sharpe ratio, drawdown)
- Generates detailed reports and CSV files
- Compares strategy vs benchmark performance

**Output Files:**

- `data/backtest_results/nuclear_comprehensive_report_*.json`
- `data/backtest_results/nuclear_trades_*.csv`
- `data/backtest_results/nuclear_portfolio_*.csv`

#### 📊 `dashboard` - Interactive Web Dashboard

Launch Streamlit web dashboard for interactive analysis.

```bash
python main.py dashboard
```

**Features:**

- Real-time trading signal display with portfolio details
- Interactive charts and historical performance analysis
- Signal history timeline and market condition monitoring
- Live backtesting interface
- Access at `http://localhost:8501`

#### ⏰ `hourly-test` - Hourly Execution Testing

Specialized backtest focusing on hourly execution timing optimization.

```bash
python main.py hourly-test
```

**Use Case:** Testing optimal execution times for automated trading with hourly data granularity.

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

```
LQQ3/
├── main.py                     # 🎯 UNIFIED ENTRY POINT (all operations)
├── src/
│   ├── core/                   # Core trading components
│   │   ├── nuclear_trading_bot.py     # Main trading strategy
│   │   ├── signal_analyzer.py         # Signal analysis tools
│   │   ├── nuclear_signal_email.py    # Email notifications
│   │   └── nuclear_dashboard.py       # Trading dashboard
│   ├── backtest/               # Backtesting framework
│   │   ├── nuclear_backtest_framework.py      # Core backtesting
│   │   ├── simplified_comprehensive_backtest.py  # ⭐ Main backtest
│   │   ├── comprehensive_nuclear_backtest.py     # Detailed backtest
│   │   └── nuclear_backtest_complete.py          # Complete suite
│   └── execution/              # Execution timing analysis
│       ├── execution_engine.py         # Trade execution engine
│       └── hourly_execution_engine.py  # Hourly timing optimization
├── tests/                      # Test suite
├── data/                       # Data storage & results
│   ├── logs/                   # Live trading alerts and logs
│   ├── backtest_results/       # Backtest reports and CSV files
│   └── lse_ticker_data/        # Market data cache
├── docs/                       # Documentation
├── .github/workflows/          # 🤖 AUTOMATED EXECUTION
│   └── nuclear_daily_signal.yml       # Hourly GitHub Action
└── requirements.txt            # Python dependencies
```

**Key Files:**

- **`main.py`** - Single entry point for all operations
- **`src/core/nuclear_trading_bot.py`** - Core trading strategy and signal generation
- **`src/core/nuclear_signal_email.py`** - Email notification system
- **`src/backtest/simplified_comprehensive_backtest.py`** - Main backtesting engine
- **`.github/workflows/nuclear_daily_signal.yml`** - Automated hourly execution

## 🤖 Automated Execution

The system runs automatically via **GitHub Actions** every hour:

- **Schedule:** Hourly execution (`0 * * * *`)
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

# Interactive web dashboard
python main.py dashboard
```

### Strategy Analysis

```bash
# Comprehensive backtesting
python main.py backtest

# Hourly execution timing analysis
python main.py hourly-test

# Custom backtest duration
python main.py backtest --backtest-type comprehensive
```

### Development & Testing

```bash
# Test email functionality (requires SMTP_PASSWORD)
python main.py email

# Test specific timeframe
python main.py backtest --backtest-type hourly
```

## Key Features

- **Nuclear Strategy**: Focus on nuclear energy ETFs and leveraged instruments
- **Execution Timing**: Optimized for 9:30 AM market open execution
- **Risk Management**: No leverage (instruments are already leveraged)
- **Comprehensive Backtesting**: Full performance metrics including Sharpe, Sortino, CAGR, max drawdown
- **Data Management**: Organized storage of results, logs, and market data

## Performance Highlights

Recent backtest results (2024-07-01 to 2024-09-30):

- **Total Return**: +54.05%
- **CAGR**: +501.00%
- **Sharpe Ratio**: 2.39
- **Sortino Ratio**: 4.90
- **Max Drawdown**: -20.15%
- **Win Rate**: 60.32%

## File Organization

- **Core Components** (`src/core/`): Main trading logic and strategy
- **Backtesting** (`src/backtest/`): Historical analysis and performance testing
- **Execution** (`src/execution/`): Trade execution and timing optimization
- **Tests** (`tests/`): Unit tests and integration tests
- **Data** (`data/`): Organized storage for results, logs, and market data
- **Documentation** (`docs/`): Strategy guides and implementation notes

## 📋 Quick Reference

### Main.py Modes Summary

| Mode | Command | Purpose | Output |
|------|---------|---------|--------|
| **bot** | `python main.py bot` | Live signal generation | Console + JSON logs |
| **email** | `python main.py email` | Live signals + email alerts | Console + Email |
| **backtest** | `python main.py backtest` | Historical strategy testing | Reports + CSV files |
| **dashboard** | `python main.py dashboard` | Interactive web interface | Web app at :8501 |
| **hourly-test** | `python main.py hourly-test` | Timing optimization | Performance analysis |

### For Production Use

- **Automated Trading**: `python main.py email` (GitHub Actions hourly)
- **Manual Check**: `python main.py bot`
- **Strategy Analysis**: `python main.py backtest`
- **Live Monitoring**: `python main.py dashboard`

### Key Features

- ✅ **Unified Entry Point**: One command for all operations
- ✅ **Smart Email Alerts**: Only sends when signals change
- ✅ **Comprehensive Backtesting**: Multiple execution strategies tested
- ✅ **Automated Execution**: GitHub Actions hourly monitoring
- ✅ **Interactive Dashboard**: Real-time web interface
- ✅ **Organized Data**: All outputs properly structured in `data/` directory
