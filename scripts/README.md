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

## Data Validation

### `validate_s3_against_yfinance.py`

Validate your entire S3 market data datalake against yfinance for data integrity issues.

**Why local-only?** yfinance blocks Lambda IP ranges, so validation must run on your development machine.

**Features:**
- ✅ Date validation (missing dates in S3 or yfinance)
- ✅ Price validation (OHLC mismatches with float tolerance)
- ✅ Volume validation (incorrect volume data)
- ✅ Flexible filtering (all symbols, specific list, or limited batch)
- ✅ Dual reporting (CSV summary + optional JSON detailed report)
- ✅ Batch processing (handles hundreds of symbols efficiently)
- ✅ Error resilience (continues despite individual symbol failures)

**Usage:**

```bash
# Validate specific symbols
poetry run python scripts/validate_s3_against_yfinance.py \
  --symbols AAPL,MSFT,GOOGL \
  --output report.csv

# Validate first 50 symbols
poetry run python scripts/validate_s3_against_yfinance.py \
  --limit 50 \
  --output validation_report.csv

# Validate all with detailed discrepancies
poetry run python scripts/validate_s3_against_yfinance.py \
  --output summary.csv \
  --detailed discrepancies.json

# Custom S3 bucket and region
poetry run python scripts/validate_s3_against_yfinance.py \
  --bucket my-bucket \
  --region us-west-2
```

**Parameters:**
- `--symbols`: Comma-separated list (e.g., `AAPL,MSFT,GOOGL`)
- `--limit`: Maximum number of symbols to validate
- `--output`: CSV summary report (default: `s3_validation_report.csv`)
- `--detailed`: JSON file with detailed discrepancies
- `--bucket`: S3 bucket name (default: `MARKET_DATA_BUCKET` env var)
- `--region`: AWS region (default: `us-east-1`)

**Output:**
- **CSV Report**: Summary of valid/invalid symbols with discrepancy counts
- **JSON Report** (optional): Detailed list of missing dates, mismatched prices, etc.

**Full Documentation:**
See [VALIDATION_SCRIPT_README.md](./VALIDATION_SCRIPT_README.md) for comprehensive guide, performance tips, troubleshooting, and advanced usage.

## Other Scripts

### `backfill_group_cache.py`

Backfill group history cache for DSL strategy groups. Evaluates each named group in a strategy file over a historical window, computes weighted portfolio daily returns, and writes the results to both DynamoDB (legacy) and S3 Parquet files (new).

**Purpose:**
Group history is used by filter operators (e.g., moving-average-return, max-drawdown) to score and rank portfolios. Pre-computing this history allows strategies to run efficiently without re-evaluating groups on every bar.

**Storage:**
- **S3 (new)**: `s3://{bucket}/groups/{group_id}/history.parquet` + metadata.json
- **DynamoDB (legacy)**: GroupHistoricalSelectionsTable (for backward compatibility)

**Usage:**

```bash
# Backfill all groups in a strategy (default 45 calendar days)
poetry run python scripts/backfill_group_cache.py \
  shared_layer/python/the_alchemiser/shared/strategies/ftl_starburst.clj

# Custom lookback period
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --days 60

# Backfill ALL available history (as far back as data exists)
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --all

# Dry-run (compute but do not write)
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --dry-run

# Target specific groups with pattern matching
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj \
  --group "WYLD Mean Reversion*"

# Parallel processing (4 workers per depth level)
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --parallel 4

# Specific deployment stage (dev/prod resources)
poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --stage dev
```

**Parameters:**
- `--days`: Calendar days to look back (default: 45)
- `--all`: Backfill all available history (ignores --days)
- `--dry-run`: Compute without writing to DynamoDB or S3
- `--group`: Pattern to match specific groups (supports wildcards)
- `--parallel`: Number of parallel workers per depth level (default: 1)
- `--stage`: Deployment stage (dev/prod) for resource selection
- `--level`: Target specific nesting depth only

**Output:**
- Console report showing per-group statistics
- S3 Parquet files for each group with metadata
- DynamoDB records (legacy, for transition period)

**Environment Variables:**
- `MARKET_DATA_BUCKET`: S3 bucket for market data and group history
- `GROUP_HISTORY_TABLE`: DynamoDB table name (legacy)
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)

**Performance Optimizations:**
- Pre-loads all market data into memory (eliminates S3 round-trips)
- Batch writes (25 items per DynamoDB request, single Parquet per group)
- Parallel group evaluation at each nesting depth
- Processes deepest groups first (outer groups can use inner caches)

**Migration Note:**
The script now writes to both DynamoDB and S3 simultaneously. Once all production workflows are verified to read from S3, the DynamoDB table can be deprecated.

### `seed_market_data.py`
Seed historical market data to S3 for local/dev testing.

### `pnl_analysis.py`
Analyze P&L performance by strategy.

### `deploy.sh`
Deployment automation script.
