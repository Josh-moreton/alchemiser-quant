# Scripts Directory

Utility scripts for testing, deployment, and analysis.

## Signal Comparison

### `compare_strategy_signals.py`

Compare strategy signals between dev and production environments to verify parity during migration periods.

**Usage:**

```bash
# Compare today's signals (all signals from the day)
poetry run python scripts/compare_strategy_signals.py

# Compare today's signals at scheduled time (14:35 UTC = 9:35 AM ET = 2:35 PM UK)
poetry run python scripts/compare_strategy_signals.py --date today --time 14:35 --window 5

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

## Other Scripts

### `seed_market_data.py`
Seed historical market data to S3 for local/dev testing.

### `pnl_analysis.py`
Analyze P&L performance by strategy.

### `deploy.sh`
Deployment automation script.
