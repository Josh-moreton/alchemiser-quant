# Execution Package

This package handles strategy execution and account interactions. The architecture has been modularised to reduce coupling.

```
TradingEngine -> ExecutionManager -> AccountService / SmartExecution
               -> Reporting
```

## Key Modules

- `account_service.py` – account and position utilities
- `execution_manager.py` – orchestrates multi-strategy execution
- `reporting.py` – builds summaries and dashboard data

## Features

- **Paper Trading**: Safe testing environment using Alpaca's paper trading account
- **Automatic Portfolio Rebalancing**: Reads nuclear signals and adjusts portfolio accordingly
- **Position Management**: Handles buying/selling based on nuclear portfolio allocations
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

### Manual Quantitative Trading System

Run the nuclear quantitative trading system with Alpaca execution:

```bash
python main.py alpaca
```

### Standalone Alpaca Trading System

Run just the Alpaca trading component:

```bash
cd src/execution
python alpaca_trader.py
```

## How It Works

1. **Signal Generation**: The nuclear quantitative trading system generates signals and saves them to `/tmp/nuclear_alerts.json`

2. **Signal Reading**: The Alpaca trading system reads the latest signals (within last 5 minutes) to group portfolio signals

3. **Portfolio Parsing**: Extracts allocation percentages from signal reasons (e.g., "31.2%" becomes 0.312 weight)

5. **Trade Execution**:
   - Sells excess positions first
   - Buys new/additional positions
   - Uses market orders with day duration

6. **Logging**: All trades logged to `/tmp/trades_live.json`

### Supported Signals

The bot handles these nuclear strategy signals:

- **NUCLEAR_PORTFOLIO**: Multi-stock allocation (SMR, LEU, OKLO, etc.)
- **UVXY_BTAL_PORTFOLIO**: Volatility hedge (75% UVXY, 25% BTAL)
- **Single stocks**: UVXY, TQQQ, UPRO, etc.

## Example Output

```text
🚀 QUANTITATIVE TRADING SYSTEM WITH ALPACA EXECUTION
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
- **Error Handling**: Comprehensive error catching and logging
- **Dry Run Capability**: Can test without actual execution

## Files

- `alpaca_trader.py`: Main quantitative trading system class
- `/tmp/alpaca_trades.json`: Trade execution log
- `/tmp/alpaca_trader.log`: Error and info logs

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

1. Ensure nuclear system generated recent signals
2. Check `/tmp/nuclear_alerts.json` file exists
3. Verify signal format and timestamps
