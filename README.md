
# The Alchemiser: Multi-Strategy Trading Engine

> **Sophisticated automated trading system with real-time execution, WebSocket integration, and multi-strategy portfolio management**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The Alchemiser is a production-ready trading system that combines multiple quantitative strategies with intelligent order execution, real-time market data, and comprehensive risk management.

## 🚀 Quick Start

```bash
# Install and setup
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
make install

# Configure API keys
cp .env.example .env
# Edit .env with your Alpaca API keys

# Start trading (paper mode)
alchemiser trade

# View account status
alchemiser status
```

**🎯 [Complete Quick Start Guide →](./docs/getting-started/quickstart.md)**

## ✨ Key Features

### 🧠 **Multi-Strategy Intelligence**

- **Nuclear Strategy**: Market regime detection with volatility hedging
- **TECL Strategy**: Technology sector momentum and rotation
- **Dynamic Allocation**: Intelligent portfolio weighting and risk management

### ⚡ **Smart Order Execution**

- **Progressive Limit Orders**: Start at mid-price, step toward market price
- **WebSocket Integration**: Real-time pricing and order monitoring
- **Sub-100ms Latency**: Instant fill notifications vs 2-second polling

### 🛡️ **Risk Management**

- **Paper Trading First**: Safe testing with $100K virtual portfolio
- **Position Limits**: Configurable maximum allocations by asset type
- **Spread Protection**: Reject orders with excessive bid-ask spreads

### 📊 **Professional Reporting**

- **Rich CLI Output**: Beautiful terminal interface with live updates
- **Email Notifications**: HTML reports with P&L tracking and charts
- **Portfolio Analytics**: Detailed performance metrics and attribution

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Strategy      │    │   Execution     │    │   Integration   │
│   Layer         │    │   Layer         │    │   Layer         │
│                 │    │                 │    │                 │
│ • Nuclear       │───▶│ • Smart Orders  │───▶│ • Alpaca API    │
│ • TECL          │    │ • Portfolio     │    │ • WebSocket     │
│ • Multi-Strat   │    │ • Risk Mgmt     │    │ • Email/Alerts  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**📖 [Detailed Architecture Guide →](./docs/architecture/overview.md)**

## 💹 Trading Performance

### Smart Execution Benefits

| Feature | Traditional Bots | The Alchemiser |
|---------|------------------|----------------|
| **Order Type** | Market orders only | Progressive limit orders |
| **Price Improvement** | None | 0.3-2.0% vs market |
| **Fill Rate** | 100% at poor prices | 85%+ before market fallback |
| **Latency** | N/A | <100ms WebSocket notifications |

### Strategy Performance (Backtesting)

```
Nuclear Strategy (2020-2024):
├── Total Return: +127.3%
├── Sharpe Ratio: 1.34
├── Max Drawdown: -18.7%
└── Win Rate: 68.2%

TECL Strategy (2020-2024):
├── Total Return: +89.4%
├── Sharpe Ratio: 1.12
└── Max Drawdown: -23.1%
```

## 🛠️ CLI Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `alchemiser bot` | Generate signals only | `alchemiser bot --output-format json` |
| `alchemiser trade` | Execute trades | `alchemiser trade --live` |
| `alchemiser status` | Account overview | `alchemiser status --detailed` |
| `alchemiser deploy` | AWS Lambda deployment | `alchemiser deploy --environment production` |

**📚 [Complete CLI Reference →](./docs/user-guide/cli-commands.md)**

## 📈 Strategy Examples

### Nuclear Strategy Output

```
🎯 NUCLEAR STRATEGY SIGNALS
Current Signal: BEAR_MARKET_DEFENSIVE
Market Regime: High Volatility (VIX: 28.4)

Recommended Portfolio:
├── BIL (Treasury Bills): 60.0%
├── UVXY (Volatility): 25.0%
└── PSQ (Tech Short): 15.0%

📊 Technical Indicators:
├── RSI(14): 28.5 (Oversold)
├── RSI(2): 15.2 (Extreme Oversold)
└── 14-Day Volatility: 31.2% (High)
```

### Execution Summary

```
📈 EXECUTION RESULTS
Orders Placed: 3 | Filled: 3 | Failed: 0

├── ✅ SELL SPY: 150 shares → $67,425.00 (Limit: $449.50)
├── ✅ BUY BIL: 825 shares → $40,000.00 (Limit: $48.49)
└── ✅ BUY UVXY: 1,250 shares → $25,000.00 (Limit: $20.01)

💰 Portfolio Summary:
├── Total Value: $132,425.00
├── Cash Available: $0.00
└── Execution Time: 3.7 seconds
```

**🎯 [Strategy Deep Dive →](./docs/strategies/)**

## 🚀 Deployment to AWS Lambda

### Prerequisites

1. Install Node.js 18+ and AWS CLI
2. Configure AWS credentials: `aws configure`
3. Ensure your `.env` file has required variables:
   - `AWS__ACCOUNT_ID`
   - `SECRETS_MANAGER__SECRET_NAME`
   - `TRACKING__S3_BUCKET`

### Simple Deployment

```bash
# One-time setup
npm install

# Deploy to AWS Lambda
./deploy.sh

# Or use npm scripts
npm run deploy
```

### Useful Commands

```bash
# View live logs
npm run logs

# Invoke function manually
npm run invoke

# Get deployment info
npm run info

# Remove everything
npm run remove
```

### Scheduling

- The Lambda function has a schedule trigger (disabled by default)
- Enable it in the AWS Console when ready for automatic trading
- Default schedule: every 15 minutes during market hours

### Local Development

```bash
# Development mode with auto-reload
make run-signals    # Signals only
make run-trade      # Paper trading
make run-trade-live # Live trading ⚠️
```

## 📊 Monitoring & Alerts

### Email Notifications

Professional HTML email reports with:

- 📈 Portfolio performance and P&L tracking
- 🎯 Strategy allocation breakdowns
- 📋 Detailed trade execution summaries
- ⚠️ Error alerts and system notifications

### CLI Monitoring

```bash
# Real-time portfolio tracking
alchemiser status

# Recent P&L analysis
alchemiser status --history 30 --detailed

# Export data for analysis
alchemiser status --format json > portfolio.json
```

**📧 [Email Setup Guide →](./docs/user-guide/email-notifications.md)**

## 🔧 Configuration

### Environment Setup

```bash
# Paper Trading (Safe)
ALPACA_KEY=your_paper_api_key
ALPACA_SECRET=your_paper_secret

# Live Trading (Real Money) ⚠️
ALPACA_LIVE_KEY=your_live_api_key
ALPACA_LIVE_SECRET=your_live_secret

# Email Notifications
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient@email.com
```

### Strategy Configuration

```yaml
# config.yaml
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

execution:
  progressive_orders: true
  websocket_enabled: true
  max_position_size: 0.25
```

**⚙️ [Configuration Guide →](./docs/getting-started/configuration.md)**

## 🧪 Testing & Quality

### Comprehensive Test Suite

- **232+ Tests** across 12 test files
- **93% Code Coverage** with unit and integration tests
- **Market Scenario Testing** for various conditions
- **Error Handling Validation** for robust operation

```bash
# Run test suite
make test

# Generate coverage report
make test-coverage

# Run specific test category
pytest tests/test_strategy_engines.py -v
```

**🔬 [Testing Guide →](./docs/development/testing.md)**

## 📚 Documentation

### Complete Documentation Framework

- **📖 [User Guide](./docs/user-guide/)** - CLI commands, trading modes, monitoring
- **🏗️ [Architecture](./docs/architecture/)** - System design and data flow
- **📈 [Strategies](./docs/strategies/)** - Nuclear, TECL, and custom strategies
- **💹 [Trading Features](./docs/trading/)** - Smart orders, risk management
- **🛠️ [Development](./docs/development/)** - Contributing, testing, debugging
- **🚀 [Deployment](./docs/deployment/)** - AWS Lambda, Docker, monitoring

**📖 [Browse All Documentation →](./docs/README.md)**

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./docs/development/contributing.md) for details.

### Development Setup

```bash
# Setup development environment
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
make install-dev

# Run tests
make test

# Code formatting
make format

# Submit changes
git checkout -b feature/your-feature
# Make changes and test
git commit -m "Add your feature"
git push origin feature/your-feature
```

### Code Quality

The Alchemiser enforces high code quality standards through automated tooling:

- **🎨 Black**: Consistent code formatting
- **🔍 Ruff**: Fast linting and import sorting (replaces Flake8 + isort)
- **🔒 MyPy**: Static type checking
- **🎣 Pre-commit hooks**: Automatic code quality checks

```bash
# Install pre-commit hooks (one-time setup)
poetry run pre-commit install

# Run quality checks manually
poetry run black .                    # Format code
poetry run ruff check . --fix         # Fix linting issues
poetry run mypy the_alchemiser/       # Type checking
poetry run pre-commit run --all-files # Run all hooks

# Quality checks run automatically on:
# ✅ Every commit (pre-commit hooks)
# ✅ Every pull request (GitHub Actions)
```

**📝 [Contributing Guide →](./CONTRIBUTING.md)**

## ⚠️ Risk Disclosure

**Important**: This software is for educational and research purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results.

- ✅ Always start with **paper trading**
- ✅ Never risk more than you can afford to lose
- ✅ Understand the strategies before using live funds
- ✅ Monitor your positions and set appropriate limits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **📊 [Live Demo](https://demo.alchemiser.trading)** *(Coming Soon)*
- **📖 [Documentation](./docs/README.md)**
- **🐛 [Issues](https://github.com/Josh-moreton/the-alchemiser/issues)**
- **💬 [Discussions](https://github.com/Josh-moreton/the-alchemiser/discussions)**

---

**Built with ❤️ for systematic trading**

- Real-time portfolio and P&L reporting
- Strategy allocation breakdowns
- Trading activity summaries
- Error alerts and market status notifications

✅ EXECUTION STATUS: SUCCESS
Portfolio Value: $101,250.00 (+1,250.00 / +1.3%)
Cash: $5,000.00 (4.9% of portfolio)

📊 Positions:

- SMR: 156 @ $40.00 (P&L +12.0%, 31.2% alloc)
- LEU: 198 @ $200.00 (P&L +8.5%, 39.5% alloc)
- OKLO: 487 @ $60.00 (P&L -2.3%, 29.3% alloc)
- TECL: 100 @ $60.00 (P&L +5.0%, 20% alloc)
Top gainer: SMR (+12.0%), Worst: OKLO (-2.3%)

📝 Orders:

- BUY SMR 50 ($2,000.00)
- SELL LEU 30 ($6,000.00)

```

### Alpaca & Telegram Setup

Set your credentials before running:

```bash
export ALPACA_KEY="your-alpaca-key"
export ALPACA_SECRET="your-alpaca-secret"
export TELEGRAM_TOKEN="your-telegram-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## 🤖 Automated Execution

The bot can run automatically via **GitHub Actions** or **AWS Lambda**:

### GitHub Actions

- **Command:** `alchemiser trade --live`
- **Functions:** Multi-strategy signal generation, trade execution, Telegram update
- **Manual Trigger:** Available via GitHub Actions UI
- **Environment:** `ALPACA_KEY`, `ALPACA_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

**GitHub Actions Workflow:**

```yaml
- name: Run Alchemiser System
  env:
    ALPACA_KEY: ${{ secrets.ALPACA_KEY }}
    ALPACA_SECRET: ${{ secrets.ALPACA_SECRET }}
    TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: alchemiser trade --live
```

### AWS Lambda (Enhanced Event-Driven)

The Lambda handler now supports **multiple trading modes** triggered by different event configurations:

#### 🎯 Supported Modes

- **Paper Trading**: Safe testing with simulated trades
- **Live Trading**: Real money trading with actual positions
- **Signal Analysis**: Display signals without executing trades

#### 📋 Event Configuration

```json
{
    "mode": "trade" | "bot",           // Required: Operation mode
    "trading_mode": "paper" | "live",  // Optional: Trading mode (default: live)
    "ignore_market_hours": boolean     // Optional: Override market hours (default: false)
}
```

#### 📚 Event Examples

```json
// Paper Trading
{"mode": "trade", "trading_mode": "paper"}

// Live Trading
{"mode": "trade", "trading_mode": "live"}

// Signal Analysis
{"mode": "bot"}

// Testing Mode (ignore market hours)
{"mode": "trade", "trading_mode": "paper", "ignore_market_hours": true}

// Empty Event (Backward Compatibility - defaults to live trading)
{}
```

#### 🕐 CloudWatch Schedules

```bash
# Paper Trading (Daily at 9:45 AM EST)
aws events put-rule --name "AlchemiserPaper" \
  --schedule-expression "cron(45 14 ? * MON-FRI *)"
aws events put-targets --rule "AlchemiserPaper" \
  --targets Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:the-alchemiser,Input='{"mode":"trade","trading_mode":"paper"}'

# Live Trading (Daily at 9:45 AM EST)
aws events put-rule --name "AlchemiserLive" \
  --schedule-expression "cron(45 14 ? * MON-FRI *)"
aws events put-targets --rule "AlchemiserLive" \
  --targets Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:the-alchemiser,Input='{"mode":"trade","trading_mode":"live"}'
```

#### 🚀 Deployment

- Use the CLI command `alchemiser deploy` (or `make deploy`) to build and push the Docker image and update the Lambda function.
- Lambda will run the container as configured (see `scripts/build_and_push_lambda.sh`).
- **📖 Detailed Documentation**: See [`docs/lambda_event_configuration.md`](docs/lambda_event_configuration.md) for comprehensive setup guide.

## 📁 Project Structure

```text
The-Alchemiser/
├── main.py                     # Unified entry point
├── core/                       # Core trading logic & strategies
│   ├── data/                   # Data access & providers
│   ├── indicators/             # Technical indicators
│   ├── secrets/                # Secrets management
│   ├── logging/                # Logging helpers
│   ├── trading/                # Bots and strategy engines
│   ├── ui/                     # CLI & Telegram utilities
│   ├── utils/                  # Common utilities (S3, helpers)
│   └── alerts/                 # Alerting services
├── execution/                  # Trading integration
│   ├── alpaca_trader.py        # Alpaca trading system
│   └── multi_strategy_trader.py# Multi-strategy trading
├── tests/                      # Test suite
├── data/                       # Data storage & logs
│   └── logs/                   # Trading logs
├── .github/workflows/          # Automated execution
│   └── nuclear_alpaca_trading.yml
└── requirements.txt            # Python dependencies
```

## 📊 Features & Strategies

- **Multi-Strategy Support:** Nuclear, TECL, volatility hedges, and more
- **Automated Trading:** Executes trades via Alpaca (paper/live)
- **Post-Trade Validation:** Validates technical indicators against TwelveData API (live mode only)
- **Telegram Integration:** Sends execution summaries and signals
- **Position Tracking:** Tracks allocations and performance per strategy
- **Risk Management:** No leverage (uses leveraged ETFs only)
- **Data Management:** Logs, results, and signals organized in `data/`

### Post-Trade Technical Indicator Validation 🔍

When running in **live mode** (`--live` flag), the bot automatically validates technical indicators used in signal evaluation against external TwelveData API after trades are executed:

- **Non-blocking:** Validation happens in background thread, doesn't delay trades
- **Targeted:** Only validates indicators actually used in signal generation
- **Rate-limited:** Respects TwelveData API limits (7 requests/minute)
- **Strategy-aware:** Nuclear strategy (RSI 10/20, MA 20/200) vs TECL strategy (RSI 9/10, MA 200)

```bash
# Live trading with automatic post-trade validation
python main.py trade --live

# Example validation output in logs:
# 🔍 Triggering post-trade validation for Nuclear: ['SPY', 'SMR'], TECL: ['XLK']
# ✅ Post-trade validation Nuclear: 2/2 successful
# ✅ Post-trade validation TECL: 1/1 successful
```

**Demo the validation system:**

```bash
python demo_post_trade_validation.py
```

See [docs/POST_TRADE_VALIDATION.md](docs/POST_TRADE_VALIDATION.md) for detailed documentation.

### Example Supported Strategies

- Nuclear Portfolio: SMR, LEU, OKLO
- TECL For The Long Term: TECL, XLK, KMLM, UVXY, BIL
- Volatility Hedge: UVXY, BTAL

## 🔧 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Josh-moreton/The-Alchemiser.git
   cd The-Alchemiser
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

4. **Set up environment variables:**

```bash
export ALPACA_KEY="your-alpaca-key"
export ALPACA_SECRET="your-alpaca-secret"
export TELEGRAM_TOKEN="your-telegram-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## 📈 Usage Examples

### Daily Operations

```bash
# Show multi-strategy signals (no trading)
alchemiser bot

# Run multi-strategy paper trading
alchemiser trade

# Run multi-strategy live trading with Telegram
alchemiser trade --live

# Show account status
alchemiser status

# Deploy to AWS Lambda
alchemiser deploy
```

### Development & Testing

```bash
pytest tests/ -v
```

## 🧠 Advanced Features

- **Multi-Strategy Portfolio:** Allocate between Nuclear, TECL, and others
- **Position Attribution:** Tracks which strategy drives each trade
- **Comprehensive Reporting:** Telegram, logs, and JSON summaries
- **Safe Testing:** Paper trading mode and dry-run capability

## 📋 Quick Reference

| Command                | Purpose                              | Output                |
|------------------------|--------------------------------------|-----------------------|
| `alchemiser bot`       | Multi-strategy signal generation     | Console + JSON logs   |
| `alchemiser trade`     | Paper trading (multi-strategy)       | Console + Telegram    |
| `alchemiser trade --live` | Live trading (multi-strategy) ⚠️ | Console + Telegram    |
| `alchemiser status`    | Show account status and positions    | Console               |
| `alchemiser deploy`    | Build & deploy Lambda Docker image   | Console               |
| `alchemiser version`   | Show version info                    | Console               |

## 🛠️ Troubleshooting

- Run from project root directory
- Ensure all dependencies installed: `pip install -e .` (for CLI) or `pip install -r requirements.txt`
- Activate your venv: `source .venv/bin/activate` (macOS recommended)
- Use Makefile targets for common tasks: `make run-signals`, `make deploy`, etc.
- Check API credentials and network connectivity
- For multi-strategy: check logs for details

## 📚 Documentation

- See `docs/MULTI_STRATEGY.md` for multi-strategy details
- See `execution/README.md` for Alpaca integration
- See `the_alchemiser/cli.py` for CLI source and available commands

## 🏆 Performance

Performance varies by strategy and market conditions. Example metrics (Nuclear strategy):

- **Total Return:** +54.05% (3 months)
- **Sharpe Ratio:** 2.39
- **Max Drawdown:** -20.15%

## 🤝 Support

- Issues: GitHub Issues
- Telegram: See bot output for contact info
- Test suite: `pytest tests/ -v`
