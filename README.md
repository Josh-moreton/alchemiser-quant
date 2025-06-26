# LQQ3 Trading Strategy Backtest

This project backtests a trading strategy for the LSE-listed ETF LQQ3 based on signals from the US ETF TQQQ.

## Strategy Description

**Entry Signal**: Buy LQQ3 with 100% of portfolio when TQQQ closes above its 200-day Simple Moving Average (SMA)

**Exit Signal**: Sell 66% of LQQ3 holdings (keep 34%) when TQQQ closes below its 200-day SMA

## Key Features

- ✅ Fetches real-time data from Yahoo Finance
- ✅ Calculates 200-day SMA for TQQQ
- ✅ Simulates trading with realistic position sizing
- ✅ Compares strategy performance vs buy-and-hold
- ✅ Comprehensive performance metrics
- ✅ Interactive visualizations
- ✅ Detailed trade logging

## Quick Start

1. **Install dependencies and run backtest:**

   ```bash
   python run_backtest.py
   ```

2. **Or manually install and run:**

   ```bash
   pip install -r requirements.txt
   python trading_strategy_backtest.py
   ```

## GitHub Actions

This repository includes a workflow to run the daily LQQ3 signal script.
The workflow installs the dependencies and executes `lqq3_daily_signal.py`
every day at 08:00 UTC. You can trigger it manually from the Actions tab
using the **Run workflow** button.

## Files

- `trading_strategy_backtest.py` - Main backtesting engine
- `run_backtest.py` - Quick start script with automatic package installation
- `requirements.txt` - Required Python packages
- `backtest_results.csv` - Detailed results (generated after running)

## Strategy Logic

### Signal Generation

- Uses TQQQ daily closing prices vs 200-day SMA
- Signal = 1 when TQQQ > 200 SMA (bullish)
- Signal = 0 when TQQQ < 200 SMA (bearish)

### Position Management

- **Buy Signal**: Invest 100% of available cash in LQQ3
- **Sell Signal**: Sell 66% of LQQ3 holdings, hold 34% + cash
- **Hold**: No position changes between signals

### Performance Metrics

- Total return vs buy-and-hold benchmark
- Volatility (annualized)
- Sharpe ratio
- Maximum drawdown
- Number of trades
- Trade timing analysis

## Customization

You can modify the strategy parameters in `trading_strategy_backtest.py`:

```python
# Change date range
backtester = TradingStrategyBacktest(
    start_date="2020-01-01",  # Start date
    end_date="2024-12-31",    # End date (optional)
    initial_capital=10000     # Starting capital
)

# Modify sell percentage (currently 66%)
shares_to_sell = shares * 0.66  # Change 0.66 to desired percentage
```

## Output

The backtest generates:

1. **Console Summary**: Key performance metrics and trade summary
2. **Interactive Plots**:
   - Portfolio value vs buy-and-hold
   - TQQQ price vs 200 SMA with signals
   - LQQ3 price movement
   - Portfolio allocation over time
3. **CSV File**: Complete daily portfolio data

## Requirements

- Python 3.7+
- Internet connection (for data fetching)
- See `requirements.txt` for package dependencies

## Risk Disclaimer

This is for educational and research purposes only. Past performance does not guarantee future results. Trading involves risk of loss. Always conduct your own research and consider consulting with a financial advisor before making investment decisions.

## Technical Notes

- Data fetched from Yahoo Finance
- Handles missing data with forward-fill
- Accounts for transaction timing
- Uses adjusted closing prices
- Assumes no transaction costs or slippage

## Troubleshooting

**Data Issues**: If you get data fetching errors, check:

- Internet connection
- Yahoo Finance availability
- Ticker symbols (TQQQ, LQQ3.L)
- Date range validity

**Package Issues**: Run `pip install --upgrade -r requirements.txt`

**Plot Issues**: If plots don't display, try installing: `pip install kaleido`
