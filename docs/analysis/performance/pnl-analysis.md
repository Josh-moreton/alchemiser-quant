# P&L Analysis Feature

The Alchemiser now includes built-in portfolio profit and loss analysis using the Alpaca API. This feature provides weekly and monthly performance reports that can be run from the command line or triggered via AWS Lambda.

## Features

- **Weekly P&L Reports**: Analyze performance over the past N weeks
- **Monthly P&L Reports**: Analyze performance over the past N months
- **Flexible Period Analysis**: Use Alpaca period formats (1W, 1M, 3M, 1A)
- **Detailed Breakdown**: Optional daily-level performance details
- **Multiple Interfaces**: CLI script, main application, and Lambda integration

## Usage

### Main Application Interface

The primary interface for local development uses the main application entry point:

```bash
# Show last week's P&L
poetry run python -m the_alchemiser pnl --weekly

# Show last month's P&L with daily breakdown
poetry run python -m the_alchemiser pnl --monthly --detailed

# Show P&L for last 3 weeks
poetry run python -m the_alchemiser pnl --weekly --periods 3

# Show P&L using Alpaca period format
poetry run python -m the_alchemiser pnl --period 1M
```

### Standalone Script (Alternative)

A standalone script is also available for cases where you need file output:

```bash
# Show last week's P&L
python scripts/pnl_analysis.py --weekly

# Show last month's P&L with daily breakdown
python scripts/pnl_analysis.py --monthly --detailed

# Save report to file
python scripts/pnl_analysis.py --monthly --output /tmp/pnl_report.txt
```

### Makefile Commands

Quick access via Make targets (uses main application interface):

```bash
# Show weekly P&L
make run-pnl-weekly

# Show monthly P&L
make run-pnl-monthly

# Show detailed monthly P&L
make run-pnl-detailed
```

### Main Application Integration

The P&L functionality is integrated into the main application:

```bash
# Via python -m interface (recommended for local dev)
python -m the_alchemiser pnl --weekly
python -m the_alchemiser pnl --monthly --detailed

# Via main function (programmatic usage)
python -c "from the_alchemiser.main import main; main(['pnl', '--monthly', '--detailed'])"
```

### AWS Lambda Integration

P&L analysis can be triggered via Lambda events:

```json
{
  "action": "pnl_analysis",
  "pnl_type": "weekly",
  "pnl_periods": 2,
  "pnl_detailed": true
}
```

```json
{
  "action": "pnl_analysis",
  "pnl_period": "1M"
}
```

## API Reference

### PnLService

The core service class for P&L analysis:

```python
from the_alchemiser.shared.services.pnl_service import PnLService

service = PnLService()

# Get weekly P&L
weekly_data = service.get_weekly_pnl(weeks_back=1)

# Get monthly P&L
monthly_data = service.get_monthly_pnl(months_back=1)

# Get P&L using Alpaca periods
period_data = service.get_period_pnl("3M")

# Format report
report = service.format_pnl_report(weekly_data, detailed=True)
print(report)
```

### PnLData

Container for P&L analysis results:

```python
class PnLData:
    period: str                    # Period description
    start_date: str               # Start date (ISO format)
    end_date: str                 # End date (ISO format)
    start_value: Decimal | None   # Starting portfolio value
    end_value: Decimal | None     # Ending portfolio value
    total_pnl: Decimal | None     # Total profit/loss amount
    total_pnl_pct: Decimal | None # Total profit/loss percentage
    daily_data: list[dict]        # Daily performance data
```

## Configuration

The P&L service uses the same Alpaca API configuration as the main trading system:

- **Environment Variables**: `ALPACA_KEY`, `ALPACA_SECRET`, `ALPACA_ENDPOINT`
- **Lambda Environment**: Credentials passed via Lambda environment variables
- **Paper vs Live**: Determined by endpoint configuration (paper-api.alpaca.markets vs api.alpaca.markets)

## Output Format

Reports include:

- Period summary with start/end dates
- Starting and ending portfolio values
- Total P&L in dollars and percentage
- Performance indicators (📈 for positive, 📉 for negative)
- Optional daily breakdown with per-day P&L

Example output:

```
📊 Portfolio P&L Report - 1 Week
==================================================
Period: 2024-01-01 to 2024-01-07
Starting Value: $10,000.00
Ending Value: $10,300.00
Total P&L: 📈 $+300.00
Total P&L %: +3.00%

Daily Breakdown:
------------------------------
2024-01-01: $10,000.00 | P&L: $+0.00 (+0.00%)
2024-01-02: $10,150.00 | P&L: $+150.00 (+1.50%)
2024-01-03: $10,050.00 | P&L: $-100.00 (-0.99%)
2024-01-04: $10,250.00 | P&L: $+200.00 (+1.99%)
2024-01-07: $10,300.00 | P&L: $+50.00 (+0.49%)
```

## Error Handling

The service gracefully handles:

- Missing Alpaca API credentials
- Network connectivity issues
- Empty or invalid data responses
- Date range validation errors

## Testing

Run the test suite to verify functionality:

```bash
python -m pytest tests/shared/services/test_pnl_service.py -v
```

The tests use mocked Alpaca managers to verify core logic without requiring live API access.
