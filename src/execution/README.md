# Alpaca Trading Integration

This module integrates the Nuclear Trading Strategy with Alpaca Markets for automated trade execution using paper trading.

## Features

- **Paper Trading**: Safe testing environment using Alpaca's paper trading account
- **Automatic Portfolio Rebalancing**: Reads nuclear signals and adjusts portfolio accordingly
- **Position Management**: Handles buying/selling based on nuclear portfolio allocations
- **Risk Management**: Built-in position size limits and cash reserves
- **Comprehensive Logging**: All trades and errors logged for analysis

## Setup

### 1. Alpaca Account Setup

1. Create a free Alpaca account at [alpaca.markets](https://alpaca.markets)
2. Get your Paper Trading API keys from the dashboard
3. Add credentials to your `.env` file (already configured in this project)

### 2. Environment Variables

The following variables should be in your `.env` file:

```bash
# Paper Trading (recommended for testing)
ALPACA_PAPER_ENDPOINT=https://paper-api.alpaca.markets/v2
ALPACA_PAPER_KEY=your_paper_key_here
ALPACA_PAPER_SECRET=your_paper_secret_here

# Live Trading (use with caution)
ALPACA_ENDPOINT=https://api.alpaca.markets
ALPACA_KEY=your_live_key_here
ALPACA_SECRET=your_live_secret_here
```

## Usage

### Basic Test

Test your Alpaca connection:

```bash
cd src/execution
python test_alpaca.py
```

### Manual Trading Bot

Run the nuclear bot with Alpaca execution:

```bash
python main.py alpaca
```

### Standalone Alpaca Bot

Run just the Alpaca trading component:

```bash
cd src/execution
python alpaca_trader.py
```

### Continuous Monitoring

Run continuous monitoring with hourly execution:

```bash
cd src/execution
python nuclear_alpaca_bot.py --continuous --interval 60
```

## How It Works

1. **Signal Generation**: The nuclear trading bot generates signals and saves them to `data/logs/nuclear_alerts.json`

2. **Signal Reading**: The Alpaca bot reads the latest signals (within last 5 minutes) to group portfolio signals

3. **Portfolio Parsing**: Extracts allocation percentages from signal reasons (e.g., "31.2%" becomes 0.312 weight)

4. **Risk Management**:
   - Maximum 10% per position
   - 5% cash reserve maintained
   - Position sizing based on portfolio value

5. **Trade Execution**:
   - Sells excess positions first
   - Buys new/additional positions
   - Uses market orders with day duration

6. **Logging**: All trades logged to `data/logs/alpaca_trades.json`

## Configuration

### Position Limits

Edit `AlpacaTradingBot` class parameters:

```python
self.max_position_size = 0.10  # Max 10% per position
self.min_cash_reserve = 0.05   # Keep 5% cash
```

### Supported Signals

The bot handles these nuclear strategy signals:

- **NUCLEAR_PORTFOLIO**: Multi-stock allocation (SMR, LEU, OKLO, etc.)
- **UVXY_BTAL_PORTFOLIO**: Volatility hedge (75% UVXY, 25% BTAL)
- **Single stocks**: UVXY, TQQQ, UPRO, etc.

## Example Output

```text
🚀 NUCLEAR TRADING BOT WITH ALPACA EXECUTION
======================================================================
📊 STEP 1: Generating Nuclear Trading Signals...
✅ Nuclear trading signals generated successfully!

🏦 STEP 2: Connecting to Alpaca Paper Trading...
============================================================
🏦 ALPACA ACCOUNT SUMMARY
============================================================
Portfolio Value: $100,000.00
Buying Power: $200,000.00
Cash: $100,000.00
Status: ACTIVE

⚡ STEP 3: Executing Trades Based on Nuclear Signals...
Target Portfolio: {'SMR': 0.312, 'LEU': 0.395, 'OKLO': 0.293}
✅ Portfolio rebalanced - 3 orders executed
   SMR_BUY: Order abc123
   LEU_BUY: Order def456
   OKLO_BUY: Order ghi789
```

## Safety Features

- **Paper Trading Only**: Default configuration uses paper trading
- **Position Limits**: Prevents over-concentration in single positions
- **Error Handling**: Comprehensive error catching and logging
- **Dry Run Capability**: Can test without actual execution

## Files

- `alpaca_trader.py`: Main trading bot class
- `test_alpaca.py`: Connection testing script
- `nuclear_alpaca_bot.py`: Integrated nuclear + Alpaca execution
- `../logs/alpaca_trades.json`: Trade execution log
- `../logs/alpaca_trader.log`: Error and info logs

## Troubleshooting

### Connection Issues

1. Verify API keys in `.env` file
2. Check Alpaca account status
3. Ensure paper trading is enabled

### Position Issues

1. Check account buying power
2. Verify stock symbols are valid
3. Review position size calculations

### Signal Issues

1. Ensure nuclear bot generated recent signals
2. Check `nuclear_alerts.json` file exists
3. Verify signal format and timestamps
