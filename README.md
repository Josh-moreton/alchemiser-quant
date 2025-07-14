# Nuclear Trading Strategy

A comprehensive nuclear energy trading strategy with unified entry points, backtesting framework, and automated hourly execution via GitHub Actions.

## 🚀 Quick Start Guide

### Entry Points

The nuclear trading system provides multiple operation modes through a unified entry point:

**Main Entry Point:**

```bash
python main.py [mode] [options]
```

**Available Modes:**

- `bot` - Run live trading bot (generates signals & sends emails)
- `backtest` - Run backtesting analysis
- `dashboard` - Launch web monitoring dashboard  
- `hourly-test` - Test hourly execution timing

**Quick Launchers:**

```bash
python run_bot.py          # Live trading bot
python run_backtest.py     # Comprehensive backtest
python run_dashboard.py    # Web dashboard
```

### Usage Examples

**Live Trading (GitHub Actions runs this hourly):**

```bash
python main.py bot
```

**Comprehensive Backtesting:**

```bash
python main.py backtest --backtest-type comprehensive
```

**Hourly Execution Analysis:**

```bash
python main.py backtest --backtest-type hourly
```

**Web Dashboard:**

```bash
python main.py dashboard
```

## 📁 Project Structure

```
LQQ3/
├── main.py                     # 🎯 UNIFIED ENTRY POINT
├── run_bot.py                  # Quick bot launcher
├── run_backtest.py             # Quick backtest launcher  
├── run_dashboard.py            # Quick dashboard launcher
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
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── .github/workflows/          # 🤖 AUTOMATED EXECUTION
│   └── nuclear_daily_signal.yml       # Hourly GitHub Action
└── requirements.txt            # Python dependencies
```

## 🤖 Automated Execution

The system runs automatically via **GitHub Actions** every hour:

- **Schedule:** Hourly execution (`0 * * * *`)
- **Action:** Runs `python main.py bot`
- **Functions:** Generates trading signals, calculates indicators, sends email alerts
- **Manual Trigger:** Available via GitHub Actions UI

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
   cp .env.example .env
   # Edit .env with your SMTP credentials
   ```

## 📈 Usage Examples

   python main.py

   ```

3. **Run specific components:**
   ```bash
   # Run simplified backtest directly
   python -m src.backtest.simplified_comprehensive_backtest
   
   # Run dashboard
   bash scripts/run_dashboard.sh
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
