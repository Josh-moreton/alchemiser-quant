# Historical Backtesting System

A comprehensive backtesting framework for The Alchemiser trading system that enables testing strategies against historical market data.

## Features

- **Historical Data Management**: Download and store market data from Alpaca
- **Parquet Storage**: Efficient storage organized by symbol and year
- **Order Fill Simulation**: Market orders filled at daily Open prices
- **Portfolio Tracking**: Snapshot-based state management
- **Performance Metrics**: Sharpe ratio, max drawdown, win rate, volatility
- **Full Pipeline Integration**: Uses actual strategy_v2 DSL engine

## Quick Start

### 1. Download Historical Data

```bash
# Download 1 year of data for default symbols (AAPL, GOOGL, MSFT, TSLA, NVDA)
make backtest-download

# Or use the CLI directly
poetry run python scripts/backtest_cli.py download --symbols AAPL GOOGL MSFT --lookback 365
```

### 2. Run a Backtest

```bash
# Run backtest with default settings (1 year)
make backtest

# Run backtest for a specific date range
make backtest-range start=2023-01-01 end=2023-12-31

# Or use the CLI directly
poetry run python scripts/backtest_cli.py run --start 2023-01-01 --end 2023-12-31 --symbols AAPL GOOGL
```

## Architecture

```
scripts/backtest/
├── backtest_runner.py          # Main backtesting engine
├── data_manager.py             # Historical data download coordinator
├── fill_simulator.py           # Order fill simulation at Open prices
├── storage/
│   ├── data_store.py          # Parquet-based storage layer
│   └── providers/
│       └── alpaca_historical.py # Alpaca historical data fetching
├── models/
│   ├── market_data.py         # Historical bar data model
│   ├── portfolio_snapshot.py  # Portfolio state snapshots
│   └── backtest_result.py     # Results and performance metrics
└── analysis/
    ├── performance_metrics.py # Performance calculations
    ├── trade_analysis.py      # Trade statistics
    └── reporting.py           # Report generation
```

## How It Works

### Daily Loop Execution

1. **Load Historical Data**: For each trading day, load OHLCV bars for all symbols
2. **Run Strategy**: Execute DSL strategy engine to generate target allocations
3. **Create Rebalance Plan**: Mock portfolio_v2 to determine required trades
4. **Simulate Execution**: Mock execution_v2 to fill orders at Open prices
5. **Update Portfolio**: Track position changes and portfolio value
6. **Calculate Metrics**: Compute performance statistics

### Fill Simulation

- **Market orders only** (MVP)
- Fills at **Open price** of the trading day
- Configurable commission per trade
- No slippage modeling (MVP)

### Data Storage

Historical data is stored as Parquet files:
```
data/historical/
└── AAPL/
    ├── 2023/
    │   └── daily.parquet
    └── 2024/
        └── daily.parquet
```

## Performance Metrics

The system calculates:

- **Total Return**: Overall percentage return
- **Sharpe Ratio**: Risk-adjusted return (annualized)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable symbols
- **Volatility**: Annualized return volatility
- **Average Trade Return**: Mean return per trade

## Configuration

### Environment Variables

```bash
# Required: Alpaca API credentials
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
```

### Data Manager Options

```python
from scripts.backtest.data_manager import DataManager

manager = DataManager(
    storage_path="data/historical"  # Where to store data
)

# Download with options
manager.download_symbols(
    symbols=["AAPL", "GOOGL"],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    force_refresh=False  # Skip if data exists
)
```

### Backtest Runner Options

```python
from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.storage.data_store import DataStore
from decimal import Decimal

runner = BacktestRunner(
    strategy_config_path="strategies/KLM.clj",
    data_store=DataStore("data/historical"),
    initial_capital=Decimal("100000"),
    commission_per_trade=Decimal("0")  # Zero commission for Alpaca
)

result = runner.run(start_date, end_date, symbols)
```

## Testing

The system includes comprehensive unit tests:

```bash
# Run all backtest tests
poetry run pytest tests/backtest/ -v

# Test coverage
poetry run pytest tests/backtest/ --cov=scripts.backtest
```

## Limitations (MVP)

1. **Market orders only**: No limit order support
2. **No slippage modeling**: Assumes perfect fills at Open
3. **Daily timeframe only**: No intraday backtesting
4. **Simplified strategy**: Uses equal-weight allocation as fallback
5. **Single data provider**: Alpaca only (no Yahoo/TwelveData)

## Future Enhancements

- [ ] Limit order support with realistic fill logic
- [ ] Slippage modeling based on volume and volatility
- [ ] Intraday timeframe support (1min, 5min, 15min)
- [ ] Full DSL strategy integration with indicators
- [ ] Multiple data provider support
- [ ] HTML/interactive reporting with charts
- [ ] Benchmark comparison (SPY, QQQ)
- [ ] Walk-forward optimization
- [ ] Parameter sensitivity analysis

## Integration with Production

The backtesting system uses the **same strategy code** as production:

- ✅ Same DSL engine (`strategy_v2`)
- ✅ Same portfolio logic (mocked at API boundary)
- ✅ Same execution logic (mocked at API boundary)
- ✅ Identical DTOs and data models

This ensures that backtest results reflect actual trading behavior.

## Examples

### Basic Backtest

```python
from datetime import datetime
from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.storage.data_store import DataStore
from scripts.backtest.analysis.reporting import print_report

# Initialize
store = DataStore()
runner = BacktestRunner("strategies/KLM.clj", store)

# Run backtest
result = runner.run(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=["AAPL", "GOOGL", "MSFT"]
)

# Print report
print_report(result)
```

### Download and Backtest

```python
from datetime import datetime, timedelta
from scripts.backtest.data_manager import DataManager
from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.storage.data_store import DataStore

# Download data
manager = DataManager()
manager.download_lookback(
    symbols=["AAPL", "GOOGL"],
    lookback_days=365
)

# Run backtest
store = DataStore()
runner = BacktestRunner("strategies/KLM.clj", store)
result = runner.run(
    start_date=datetime.now() - timedelta(days=365),
    end_date=datetime.now(),
    symbols=["AAPL", "GOOGL"]
)

print(f"Total Return: {result.metrics.total_return:.2f}%")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.metrics.max_drawdown:.2f}%")
```

## Contributing

When adding features:

1. Follow existing code structure and patterns
2. Add unit tests for new functionality
3. Update this README with new features
4. Ensure linting passes: `make lint`
5. Run tests: `poetry run pytest tests/backtest/`

## License

MIT License - See LICENSE file for details
