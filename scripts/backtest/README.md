# Backtesting System

Historical backtesting system for validating trading strategies against past market data.

## Overview

The backtesting system runs the full trading pipeline (strategy → portfolio → execution) using historical market data with mocked portfolio and execution layers. It provides realistic performance metrics and trade analysis.

## Architecture

```
scripts/backtest/
├── data_manager.py           # Historical data download coordinator
├── backtest_runner.py        # Main backtesting engine
├── fill_simulator.py         # Order fill simulation at Open prices
├── storage/
│   ├── data_store.py         # Parquet-based data persistence
│   └── providers/
│       └── alpaca_historical.py  # Alpaca historical data fetcher
├── models/
│   ├── market_data.py        # Market data DTOs
│   ├── portfolio_snapshot.py # Portfolio state tracking
│   └── backtest_result.py    # Backtest result DTOs
└── analysis/
    └── performance_metrics.py # Performance calculation (Sharpe, drawdown, etc.)
```

## Data Storage

- **Provider**: Alpaca historical API only
- **Format**: Parquet files organized by symbol and year
- **Path**: `data/historical/{symbol}/{year}/daily.parquet`
- **Schema**: Date (index), Open, High, Low, Close, Volume, Adjusted_Close
- **Auto-download**: Missing data is automatically downloaded from Alpaca when needed

### Auto-Download Behavior

When `DataStore.load_bars()` is called for a symbol/date range:

1. **Check Local Cache**: Looks for required year files in `data/historical/{symbol}/{year}/`
2. **Auto-Download Missing Data**: If files are missing and `data_provider` is configured:
   - Downloads missing data from Alpaca API
   - Caches it locally for future use
   - Proceeds with loading the data
3. **Fail Fast on Unavailable Data**: If data cannot be downloaded:
   - Raises `DataUnavailableError` with clear error message
   - Includes required date range and symbol information
   - Never proceeds with incomplete data

**Example error message:**
```
DataUnavailableError: Symbol 'GE' has no data available from provider for the requested date range.
Required: 2023-01-01 to 2025-10-06.
```

This ensures backtests never run with incomplete data and provides clear feedback when symbols are unavailable.

## Usage

### Download Historical Data

```bash
# Download default symbols (SPY, QQQ, TECL, TQQQ) for 1 year
make backtest-download

# Download specific symbols
poetry run python scripts/backtest_download.py --symbols AAPL MSFT GOOGL --days 365

# Force re-download
poetry run python scripts/backtest_download.py --force
```

### Run Backtest

```bash
# Run backtest with defaults (90 days, $100k capital)
make backtest

# Run backtest with custom date range
make backtest-range ARGS='--start-date 2023-01-01 --end-date 2023-12-31'

# Run backtest with specific parameters
poetry run python scripts/backtest_run.py \
  --strategy KLM.clj \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --capital 100000 \
  --commission 1.0 \
  --symbols SPY QQQ
```

## Features

### MVP Implementation

- **Market orders only**: Fills at daily Open price
- **No slippage modeling**: Deterministic fills
- **Simple commission**: Flat rate per trade
- **Full pipeline**: Runs actual strategy code with mocked portfolio/execution

### Performance Metrics

- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Max Drawdown**: Largest peak-to-trough decline (%)
- **Total Return**: Overall gain/loss (%)
- **Win Rate**: Percentage of profitable trades
- **Trade Count**: Total number of trades executed

### Portfolio Tracking

- Daily portfolio snapshots with positions and cash
- Trade history with execution prices and commissions
- Position tracking with unrealized P&L
- Day-over-day P&L calculation

## Implementation Details

### Strategy Integration

The backtesting system runs the **real Strategy_v2 DSL engine** with historical data. The DSL strategies are evaluated using a `HistoricalMarketDataPort` that provides bars and quotes from stored Parquet files.

**Key features:**
- Real DSL strategy evaluation (not mocked)
- Historical market data port implementation
- Full indicator calculation with historical bars
- Multiple strategy file support

### Portfolio Mocking

The portfolio module is mocked to:
1. Start with empty portfolio on day 1
2. Generate rebalance plans to transition from yesterday's state to today's signal
3. Calculate target positions based on signal weights and portfolio value
4. Generate BUY/SELL orders to reach target positions

### Execution Mocking

The execution module is mocked to:
1. Fill all orders at the day's Open price
2. Apply commission to each trade
3. Update portfolio cash and positions
4. Track all trades with timestamps and prices

## Testing

```bash
# Run all backtest tests
poetry run pytest tests/backtest/ -v

# Run specific test categories
poetry run pytest tests/backtest/test_data_store.py -v
poetry run pytest tests/backtest/test_fill_simulator.py -v
poetry run pytest tests/backtest/test_backtest_integration.py -v
```

Test coverage:
- **Data storage**: 6 tests for Parquet persistence
- **Fill simulation**: 9 tests for order fills at Open price
- **Integration**: 7 tests for full pipeline execution

## Future Enhancements

### Phase 5 (Future)
- Real DSL strategy evaluation during backtest
- Multiple strategy testing in parallel
- Limit order support with fill logic
- Slippage modeling (percentage-based)
- Market impact modeling for large orders
- Intraday bar support (hourly, minute)

### Phase 6 (Future)
- Advanced metrics: Sortino ratio, Calmar ratio, win/loss streaks
- Trade analysis: holding periods, trade sizes, entry/exit timing
- HTML report generation with charts
- Benchmark comparison (SPY, QQQ)
- Walk-forward analysis
- Parameter optimization

## Known Limitations

1. **MVP scope**: Only market orders, no limit orders
2. **No slippage**: Assumes perfect fills at Open price
3. **Simple rebalancing**: Equal-weight mock strategy
4. **Daily bars only**: No intraday data support
5. **Cash constraints**: Must have sufficient cash for all trades
6. **Commission model**: Flat rate only, no tiered/percentage commission

## Recent Improvements

### v2.10.0 - Auto-Download Missing Historical Data
- **Automatic data fetching**: Missing historical data is now automatically downloaded from Alpaca when needed
- **Fail-fast error handling**: Clear `DataUnavailableError` messages when data is unavailable
- **No silent failures**: Backtests no longer proceed with incomplete data
- **Local caching**: Downloaded data is cached for future runs
- **Test-friendly**: Gracefully handles missing API credentials in test environments

## Dependencies

- **pyarrow**: Parquet file format support
- **pandas**: Data manipulation
- **alpaca-py**: Historical data API access
- **pydantic**: Data validation and modeling

## Contributing

When adding features:
1. Follow existing module structure
2. Add tests for all new functionality
3. Update this README with usage examples
4. Maintain type safety with mypy
5. Keep functions under 50 lines
6. Document all public APIs
