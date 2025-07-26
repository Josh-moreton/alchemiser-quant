
# The Alchemiser: Multi-Strategy Trading Bot

The Alchemiser is a Python-based trading bot supporting both single and multi-strategy portfolio management, with automated execution via Alpaca and beautiful HTML email notifications. It is designed for robust, diversified trading across nuclear energy, technology, and volatility hedges, with full position tracking and reporting.

## 🚀 Quick Start

### Modern CLI Entry Point

All bot operations are now accessed via the [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) CLI:

```bash
alchemiser <command> [options]
```

Or, using the Makefile (recommended for MacOS/venv users):

```bash
make run-bot           # Show signals only
make run-trade         # Paper trading
make run-trade-live    # Live trading (⚠️ real money)
make status            # Account info
make deploy            # Deploy to AWS Lambda
```

### CLI Commands

| Command         | Purpose                                 | Output                |
|-----------------|-----------------------------------------|-----------------------|
| `alchemiser bot`| Multi-strategy signal generation        | Console + JSON logs   |
| `alchemiser trade` | Paper trading (multi-strategy)       | Console only          |
| `alchemiser trade --live` | Live trading (multi-strategy) ⚠️ | Console + Email       |
| `alchemiser status` | Show account status and positions   | Console               |
| `alchemiser deploy` | Build & deploy Lambda Docker image  | Console               |
| `alchemiser version`| Show version info                   | Console               |

#### Example: Live Trading & Email Notifications

```bash
alchemiser trade --live
```

**Requirements:**

- Environment variables: `ALPACA_KEY`, `ALPACA_SECRET`
- Email configuration: See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed setup

**Email Output:**

- Beautiful HTML emails with responsive design
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

The bot can run automatically via **GitHub Actions** or AWS Lambda:

- **GitHub Actions:**
  - **Command:** `alchemiser trade --live`
  - **Functions:** Multi-strategy signal generation, trade execution, Telegram update
  - **Manual Trigger:** Available via GitHub Actions UI
  - **Environment:** `ALPACA_KEY`, `ALPACA_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

**GitHub Actions Workflow:**

```yaml
- name: Run Alchemiser Bot
  env:
    ALPACA_KEY: ${{ secrets.ALPACA_KEY }}
    ALPACA_SECRET: ${{ secrets.ALPACA_SECRET }}
    TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: alchemiser trade --live
```

- **AWS Lambda:**
  - Use the CLI command `alchemiser deploy` (or `make deploy`) to build and push the Docker image and update the Lambda function.
  - Lambda will run the container as configured (see `scripts/build_and_push_lambda.sh`).

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
│   ├── alpaca_trader.py        # Alpaca trading bot
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
- Use Makefile targets for common tasks: `make run-bot`, `make deploy`, etc.
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
