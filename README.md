
# The Alchemiser: Multi-Strategy Trading Bot

The Alchemiser is a Python-based trading bot supporting both single and multi-strategy portfolio management, with automated execution via Alpaca and Telegram integration. It is designed for robust, diversified trading across nuclear energy, technology, and volatility hedges, with full position tracking and reporting.

## 🚀 Quick Start

### Main Entry Point

All bot operations are accessed via:

```bash
python main.py <mode> [options]
```

### Modes

| Mode      | Command                  | Description                                      |
|-----------|--------------------------|--------------------------------------------------|
| bot       | python main.py bot       | Generate multi-strategy signals (no trading)     |
| trade     | python main.py trade     | Execute multi-strategy trading (paper)           |
| trade --live | python main.py trade --live | Execute multi-strategy trading (live) ⚠️      |

#### Example: Live Trading & Telegram

```bash
python main.py trade --live
```

**Requirements:**

- Environment variables: `ALPACA_KEY`, `ALPACA_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

**Telegram Output:**

```text
🚀 Alchemiser Multi-Strategy Execution Report

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

The bot runs automatically via **GitHub Actions**:

- **Command:** `python main.py live`
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
  run: python main.py live
```

## 📁 Project Structure

```text
The-Alchemiser/
├── main.py                     # Unified entry point
├── core/                       # Core trading logic & strategies
│   ├── nuclear_trading_bot.py  # Nuclear strategy
│   ├── tecl_strategy_engine.py # TECL strategy
│   ├── strategy_manager.py     # Multi-strategy coordination
│   └── telegram_utils.py       # Telegram integration
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
# Generate multi-strategy signals (no trading)
python main.py bot

# Run multi-strategy paper trading
python main.py trade

# Run multi-strategy live trading with Telegram
python main.py trade --live
```

### Development & Testing

```bash
python tests/test_multi_strategy.py
```

## 🧠 Advanced Features

- **Multi-Strategy Portfolio:** Allocate between Nuclear, TECL, and others
- **Position Attribution:** Tracks which strategy drives each trade
- **Comprehensive Reporting:** Telegram, logs, and JSON summaries
- **Safe Testing:** Paper trading mode and dry-run capability

## 📋 Quick Reference

| Mode   | Command                    | Purpose                              | Output                |
|--------|----------------------------|--------------------------------------|-----------------------|
| bot    | `python main.py bot`       | Multi-strategy signal generation     | Console + JSON logs   |
| trade  | `python main.py trade`     | Paper trading (multi-strategy)       | Console + Telegram    |
| trade --live | `python main.py trade --live` | Live trading (multi-strategy) ⚠️ | Console + Telegram    |

## 🛠️ Troubleshooting

- Run from project root directory
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check API credentials and network connectivity
- For multi-strategy: check logs for details

## 📚 Documentation

- See `docs/MULTI_STRATEGY.md` for multi-strategy details
- See `execution/README.md` for Alpaca integration

## 🏆 Performance

Performance varies by strategy and market conditions. Example metrics (Nuclear strategy):

- **Total Return:** +54.05% (3 months)
- **Sharpe Ratio:** 2.39
- **Max Drawdown:** -20.15%

## 🤝 Support

- Issues: GitHub Issues
- Telegram: See bot output for contact info
- Test suite: `python tests/test_multi_strategy.py`
