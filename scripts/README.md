# Scripts Directory

Utility scripts for testing, deployment, and analysis.

## Backtrader Strategies

### `backtrader_uk_tqqq_sh_strategy.py`

Backtrader implementation of the "TQQQ or SH KMLM Phenomenon" strategy adapted for UK markets.

**Strategy Overview:**
- Switches between leveraged long (LQQ3) and short (XSPS) positions
- Uses RSI indicators across multiple timeframes for decision making
- UK ticker substitutions: TQQQ→LQQ3, SH→XSPS

**Usage:**

```bash
# Default run (last 365 days)
python scripts/backtrader_uk_tqqq_sh_strategy.py

# Custom date range
python scripts/backtrader_uk_tqqq_sh_strategy.py --start 2020-01-01 --end 2023-12-31

# Custom capital and commission
python scripts/backtrader_uk_tqqq_sh_strategy.py --capital 50000 --commission 0.002

# Generate plot with verbose output
python scripts/backtrader_uk_tqqq_sh_strategy.py --plot --verbose
```

**Parameters:**
- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)
- `--capital`: Initial capital (default: 100000)
- `--data-dir`: Path to historical data directory
- `--commission`: Commission rate (default: 0.001 = 0.1%)
- `--plot`: Generate plot of results
- `--verbose`: Enable verbose output

**Required Data:**
IEF, PSQ, XLK, KMLM, LQQ3, XSPS, DBMF

Fetch data with:
```bash
python scripts/fetch_backtest_data.py --symbols IEF PSQ XLK KMLM LQQ3 XSPS DBMF
```

**Documentation:**
See [docs/BACKTRADER_UK_STRATEGY.md](../docs/BACKTRADER_UK_STRATEGY.md) for detailed documentation.

## Signal Comparison

### `compare_strategy_signals.py`

Compare strategy signals between dev and production environments to verify parity during migration periods.

**Usage:**

```bash
# Compare today's signals (all signals from the day)
poetry run python scripts/compare_strategy_signals.py

# Compare today's signals at scheduled time (19:30 UTC = 3:30 PM ET = 7:30 PM UK)
poetry run python scripts/compare_strategy_signals.py --date today --time 19:30 --window 5

# Compare specific date at scheduled time
poetry run python scripts/compare_strategy_signals.py --date 2025-12-09 --time 14:35 --window 10

# Compare last 7 days (all signals)
poetry run python scripts/compare_strategy_signals.py --days-back 7

# Custom output file
poetry run python scripts/compare_strategy_signals.py --date today --time 14:35 --output reports/comparison_2025-12-09.csv
```

**Parameters:**
- `--date`: Date to compare (YYYY-MM-DD or 'today')
- `--days-back`: Number of days to look back from now
- `--time`: Target time in UTC (HH:MM format) to filter around
- `--window`: Time window in minutes around target time (default: 5)
- `--output`: CSV filename for detailed results (default: signal_comparison.csv)

**Output:**
- Console summary showing matching vs divergent signals
- CSV export with all signals and comparison status
- Exit code 0 = perfect parity, 1 = issues detected

**Use Case:**
Run daily during migration to spot any differences in signal generation between old and new indicator calculation methods.

## Hourly Gain/Loss Analysis

### `hourly_gain_analysis.py`

Analyze average hourly gain or loss patterns for stocks using historical data from Alpaca.
This script fetches hourly bar data and calculates statistics showing which hours of the
trading day historically have the best/worst average performance.

**Usage:**

```bash
# Default: Analyze SPY and QQQ over last 10 years
poetry run python scripts/hourly_gain_analysis.py

# Custom lookback period (5 years)
poetry run python scripts/hourly_gain_analysis.py --years 5

# Custom symbols
poetry run python scripts/hourly_gain_analysis.py --symbols SPY QQQ IWM

# Output as CSV
poetry run python scripts/hourly_gain_analysis.py --format csv

# Output both text and CSV
poetry run python scripts/hourly_gain_analysis.py --format both --output-dir reports
```

**Parameters:**
- `--symbols`: Symbols to analyze (default: SPY QQQ)
- `--years`: Number of years to look back (default: 10)
- `--format`: Output format - text, csv, or both (default: text)
- `--output-dir`: Directory for CSV output (default: results)
- `--verbose`: Enable verbose logging

**Environment Variables:**
- `ALPACA_KEY` or `ALPACA__KEY`: Alpaca API key
- `ALPACA_SECRET` or `ALPACA__SECRET`: Alpaca API secret

Set these in `.env.local` file or as environment variables.

**Output:**
- Text report showing average gain/loss for each hour (UTC)
- Statistics including total bars, positive/negative counts
- Key insights: best and worst performing hours
- Optional CSV export for further analysis

**Example Output:**
```
================================================================================
HOURLY GAIN/LOSS ANALYSIS: SPY
Analysis Period: Last 10 years
================================================================================

Hour (UTC)   Avg Gain %   Total Bars   Positive     Negative    
--------------------------------------------------------------------------------
09:00-09:59      0.0523         2520        1340         1180   
10:00-10:59      0.0412         2520        1310         1210   
...
================================================================================

KEY INSIGHTS:
  • Best hour: 14:00-14:59 (avg 0.0823%)
  • Worst hour: 09:00-09:59 (avg -0.0123%)
```

## Other Scripts

### `seed_market_data.py`
Seed historical market data to S3 for local/dev testing.

### `pnl_analysis.py`
Analyze P&L performance by strategy.

### `deploy.sh`
Deployment automation script.
