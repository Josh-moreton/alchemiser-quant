# Nuclear Energy Trading Strategy Backtester

## Overview

This backtesting framework tests the Nuclear Energy trading strategy against historical data with multiple execution timing strategies to determine optimal trade execution.

## Features

### Execution Strategies Tested

1. **Open Execution**: Trades executed at market open
2. **Close Execution**: Trades executed at market close  
3. **Hour-specific Execution**: Trades at specific hours (10AM, 2PM)
4. **Signal Timing**: Trades executed when signals are generated (simulated random intraday timing)

### Strategy Components Tested

- **Nuclear Portfolio Allocation**: Dynamic allocation to top 3 nuclear stocks with inverse volatility weighting
- **Market Regime Detection**: RSI-based overbought/oversold conditions
- **Volatility Protection**: UVXY/BTAL allocation during market stress
- **Bear Market Logic**: Tech/bond dynamics with inverse volatility weighting

### Data Handling

- **Multi-timeframe**: Daily data for strategy calculations, hourly data for precise execution timing
- **Multi-level DataFrame Support**: Handles yfinance's multi-level column structure
- **Robust Error Handling**: Graceful handling of missing data and API failures
- **Intelligent Caching**: Avoids redundant API calls

## Usage

### Basic Usage

```bash
# Run comprehensive backtest with default settings
python nuclear_backtest_simple.py

# Custom date range and capital
python nuclear_backtest_simple.py --start-date 2020-01-01 --end-date 2024-12-31 --capital 250000

# Save results to specific path
python nuclear_backtest_simple.py --save-path my_backtest_results
```

### Command Line Arguments

- `--start-date`: Start date (YYYY-MM-DD), default: 2020-01-01
- `--end-date`: End date (YYYY-MM-DD), default: 2024-12-31  
- `--capital`: Initial capital, default: 100,000
- `--save-path`: Path prefix for saving results, default: nuclear_backtest_results

### Quick Test

```bash
# Test backtester functionality
python test_backtest.py
```

## Output

### Console Report

The backtester generates a comprehensive console report including:

- Summary table of all execution strategies
- Performance metrics (returns, Sharpe ratio, max drawdown, win rate)
- Best strategy identification
- Timing impact analysis
- Key insights and recommendations

### Files Generated

- `{save_path}_summary.csv`: Performance summary table
- `{save_path}_charts.png`: Visualization charts
- Console output with detailed analysis

### Visualizations

1. **Normalized Portfolio Value**: Performance over time for all strategies
2. **Total Returns Comparison**: Bar chart with benchmark comparison
3. **Risk-Return Scatter**: Annual return vs Sharpe ratio
4. **Maximum Drawdown**: Risk comparison across strategies

## Performance Metrics

### Returns

- **Total Return**: Cumulative return over backtest period
- **Annual Return**: Annualized return rate
- **vs Benchmark**: Outperformance vs SPY

### Risk Metrics

- **Sharpe Ratio**: Risk-adjusted return (assuming 2% risk-free rate)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades

### Trading Metrics

- **Total Trades**: Number of portfolio rebalancing events
- **Trade Frequency**: Based on daily rebalancing

## Technical Implementation

### Data Sources

- **yfinance**: Historical price data for all securities
- **Multi-timeframe**: 1-day and 1-hour intervals
- **Date Range**: Flexible start/end dates

### Strategy Engine Integration

- Uses existing `NuclearStrategyEngine` from main trading bot
- Identical signal generation logic for consistent backtesting
- Portfolio allocation matching live trading implementation

### Execution Timing

- **Open**: Uses opening price of target day
- **Close**: Uses closing price of target day
- **Hour-specific**: Uses hourly data for precise timing
- **Signal**: Simulates random intraday signal generation

## Key Insights from Backtesting

### Timing Impact Analysis

The backtester automatically analyzes whether execution timing significantly impacts returns:

- **High Impact (>5% difference)**: Timing optimization recommended
- **Low Impact (<5% difference)**: Timing has minimal effect

### Strategy Robustness

Tests multiple execution scenarios to validate strategy effectiveness across different market conditions and timing constraints.

### Real-world Applicability

Results help determine:

- Whether sophisticated intraday timing is worth the complexity
- Optimal hours for trade execution if timing matters
- Robustness of strategy to execution delays

## Requirements

```
yfinance>=0.2.18
pandas>=1.5.0
numpy>=1.24.0
matplotlib>=3.5.0
seaborn>=0.11.0
python-dateutil>=2.8.0
```

## Error Handling

- **Missing Data**: Graceful handling of symbols with insufficient data
- **API Failures**: Retry logic and fallback mechanisms
- **Date Mismatches**: Automatic adjustment to available trading days
- **Calculation Errors**: Safe indicator calculations with fallback values

## Limitations

1. **Transaction Costs**: Not modeled (assumes zero-cost trading)
2. **Slippage**: Market impact not considered
3. **Liquidity**: Assumes perfect liquidity for all symbols
4. **Survivorship Bias**: Uses current symbol list (delisted stocks not included)
5. **API Limits**: yfinance rate limiting may affect large backtests

## Future Enhancements

- Transaction cost modeling
- Slippage simulation
- Volume-based liquidity constraints
- Walk-forward optimization
- Monte Carlo simulation
- Multiple timeframe strategy testing
- Options and derivatives support

## Example Output

```
================================================================================
NUCLEAR ENERGY STRATEGY BACKTEST RESULTS
================================================================================
Backtest Period: 2020-01-01 to 2024-12-31
Initial Capital: $100,000

SUMMARY BY EXECUTION STRATEGY:
      Strategy Total Return Annual Return Sharpe Ratio Max Drawdown Win Rate  Total Trades vs Benchmark
 Open Execution       25.43%        4.72%         0.89      -12.34%    67.2%          156       5.12%
Close Execution       27.89%        5.14%         0.95      -11.78%    68.9%          156       7.58%
 10AM Execution       26.12%        4.84%         0.91      -12.01%    67.8%          156       5.81%
  2PM Execution       28.45%        5.24%         0.98      -11.23%    69.5%          156       8.14%
Signal Timing         27.23%        5.03%         0.93      -11.89%    68.1%          156       6.92%

BEST STRATEGY (by Sharpe Ratio): 2PM Execution
  Sharpe Ratio: 0.98
  Total Return: 28.45%
  Max Drawdown: -11.23%

================================================================================
KEY INSIGHTS:
================================================================================
📊 Best Performing Strategy: 2PM Execution (28.45%)
📊 Worst Performing Strategy: Open Execution (25.43%)
📊 Timing Impact: 3.02% difference between best and worst timing
✅ Timing has minimal impact on this strategy.

✅ Backtest complete! Results saved with prefix: nuclear_backtest_results
```
