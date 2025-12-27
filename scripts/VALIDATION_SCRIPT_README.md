# S3 Data Validation Script

## Overview

`validate_s3_against_yfinance.py` is a **local-only utility** that validates your S3 market data datalake against yfinance. It identifies discrepancies in dates, prices, and volumes across your entire symbol dataset.

**Why local-only?** yfinance blocks Lambda IP ranges, making it impossible to use in AWS Lambda functions. This script runs on your development machine with full access to yfinance.

## Features

- ✅ **Date validation**: Checks for missing dates in S3 or yfinance
- ✅ **Price validation**: Detects mismatches in OHLC prices (with tolerance for float precision)
- ✅ **Volume validation**: Identifies incorrect volume data
- ✅ **Flexible filtering**: Validate all symbols, specific symbols, or a limited batch
- ✅ **Detailed reporting**: CSV summary + optional JSON detailed report
- ✅ **Batch processing**: Handles hundreds of symbols efficiently
- ✅ **Error resilience**: Continues validating even if individual symbols fail

## Installation

The script requires `yfinance` which is in the dev dependencies:

```bash
poetry install --with dev
```

## Quick Start

### Validate a few symbols
```bash
poetry run python scripts/validate_s3_against_yfinance.py \
  --symbols AAPL,MSFT,GOOGL \
  --output my_report.csv
```

### Validate first 50 symbols
```bash
poetry run python scripts/validate_s3_against_yfinance.py \
  --limit 50 \
  --output validation_report.csv
```

### Validate all symbols with detailed report
```bash
poetry run python scripts/validate_s3_against_yfinance.py \
  --output summary.csv \
  --detailed discrepancies.json
```

### Validate custom S3 bucket
```bash
poetry run python scripts/validate_s3_against_yfinance.py \
  --bucket my-custom-bucket \
  --region us-west-2
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--symbols SYMBOLS` | (all) | Comma-separated list of symbols (e.g., `AAPL,MSFT,GOOGL`) |
| `--limit N` | (none) | Maximum number of symbols to validate |
| `--output FILE` | `s3_validation_report.csv` | CSV summary report path |
| `--detailed FILE` | (none) | JSON file for detailed discrepancies |
| `--bucket NAME` | `MARKET_DATA_BUCKET` env var | S3 bucket name |
| `--region REGION` | `us-east-1` | AWS region |

## Output Files

### CSV Summary Report (default: `s3_validation_report.csv`)

```csv
VALIDATION REPORT,2025-12-27T14:23:45.123456+00:00

Total Symbols,150
Valid Symbols,147
Invalid Symbols,3

Symbol,S3 Records,yfinance Records,Missing in S3,Missing in yfinance,Mismatched,Errors,Status
AAPL,7500,7500,0,0,0,,VALID
MSFT,7234,7500,266,0,0,,INVALID
GOOGL,7500,7500,0,0,0,,VALID
AMZN,5678,5678,0,0,3,,INVALID
...
```

### JSON Detailed Report (optional: specify with `--detailed`)

```json
{
  "MSFT": {
    "s3_record_count": 7234,
    "yfinance_record_count": 7500,
    "missing_in_s3": [
      {
        "date": "2024-01-02",
        "close": 375.50,
        "volume": 12345000
      },
      ...
    ],
    "mismatched": [
      {
        "date": "2024-01-15",
        "s3_close": 380.25,
        "yf_close": 380.30,
        "s3_volume": 15000000,
        "yf_volume": 15000000
      },
      ...
    ]
  },
  "AMZN": {
    ...
  }
}
```

## How It Works

1. **List symbols**: Fetches all symbol prefixes from S3 (or uses provided list)
2. **For each symbol**:
   - Downloads Parquet data from S3
   - Fetches historical data from yfinance
   - Normalizes both to a common format (dates, OHLCV)
   - Compares records:
     - Missing dates (in one source but not the other)
     - Mismatched prices or volumes
3. **Reports discrepancies**: Generates CSV summary and optional detailed JSON

## Performance Tips

### Validate in batches
If you have thousands of symbols, validate in batches to avoid timeout:

```bash
# First 100
poetry run python scripts/validate_s3_against_yfinance.py --limit 100 --output batch1.csv

# Next 100
poetry run python scripts/validate_s3_against_yfinance.py --symbols $(poetry run python -c "
import boto3
s3 = boto3.client('s3')
symbols = [p['Prefix'].rstrip('/') for p in s3.get_paginator('list_objects_v2').paginate(Bucket='alchemiser-shared-market-data', Delimiter='/').search('CommonPrefixes[]') or []]
print(','.join(symbols[100:200]))
") --output batch2.csv
```

### Run in background
```bash
nohup poetry run python scripts/validate_s3_against_yfinance.py > validation.log 2>&1 &
```

### Faster: Skip detailed report
The detailed JSON report processes all discrepancies. For large validation runs, skip it:

```bash
poetry run python scripts/validate_s3_against_yfinance.py --output report.csv
# Don't use --detailed flag
```

## Interpreting Results

### Valid Symbol
- **Status**: VALID
- **Meaning**: All S3 data matches yfinance exactly (within float tolerance)
- **Action**: None needed

### Missing in S3
- **Cause**: S3 has fewer records than yfinance
- **Common reason**: Data refresh lag or data truncation
- **Action**: Re-seed from yfinance or check data refresh logs

### Missing in yfinance
- **Cause**: S3 has records yfinance doesn't
- **Common reason**: Weekend/holiday trades, delisted symbols, or yfinance lag
- **Action**: Usually safe to ignore; validate symbol is still trading

### Mismatched Records
- **Cause**: Same date exists in both but price/volume differs
- **Common reason**: Price adjustments (splits, dividends), feed latency, data corruption
- **Action**: Investigate root cause; may need to refresh symbol data

### Errors
- **Cause**: Could not fetch data or comparison failed
- **Common reason**: Symbol no longer exists, network issues, S3 access
- **Action**: Check logs and verify S3 access credentials

## Common Issues

### "Bucket not specified"
**Solution**: Set `MARKET_DATA_BUCKET` env var or use `--bucket` flag:
```bash
export MARKET_DATA_BUCKET=alchemiser-shared-market-data
poetry run python scripts/validate_s3_against_yfinance.py
```

### "No data found in S3 for SYMBOL"
**Cause**: Symbol doesn't exist in S3 datalake
**Solution**: Check if symbol was seeded; verify with:
```bash
aws s3 ls s3://alchemiser-shared-market-data/SYMBOL/
```

### "Failed to fetch yfinance data"
**Cause**: yfinance can't find symbol or network issue
**Solution**: 
- Verify symbol exists: `yfinance.Ticker('AAPL').info`
- Check internet connection
- Try again (has 3 retries built-in)

### High discrepancy counts on new symbols
**Cause**: Newly seeded symbols may have partial historical data
**Action**: Expected; validate after full refresh cycle

## Integration with CI/CD

Add to your CI pipeline to catch data corruption:

```yaml
# .github/workflows/data-validation.yml
name: Data Validation
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install poetry
      - run: poetry install --with dev
      - run: |
          poetry run python scripts/validate_s3_against_yfinance.py \
            --limit 100 \
            --output validation_report.csv \
            --detailed discrepancies.json
        env:
          MARKET_DATA_BUCKET: ${{ secrets.MARKET_DATA_BUCKET }}
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-reports
          path: |
            validation_report.csv
            discrepancies.json
```

## Advanced Usage

### Custom validation logic
Modify `validate_symbol()` to add custom checks (e.g., data gaps, volatility spikes):

```python
def validate_symbol(symbol: str, s3_client, bucket: str) -> SymbolValidationResult:
    result = SymbolValidationResult(...)
    # ... existing code ...
    
    # Add custom validation
    s3_points = normalize_dataframe(s3_df, "S3")
    dates = sorted([p.date for p in s3_points])
    
    # Check for data gaps > 10 days
    for i in range(1, len(dates)):
        gap = (pd.to_datetime(dates[i]) - pd.to_datetime(dates[i-1])).days
        if gap > 10:
            result.errors.append(f"Data gap {gap} days at {dates[i]}")
    
    return result
```

### Process results programmatically
```python
import json
with open('discrepancies.json') as f:
    discrepancies = json.load(f)

# Find symbols with most missing data
sorted_symbols = sorted(
    discrepancies.items(),
    key=lambda x: len(x[1]['missing_in_s3']),
    reverse=True
)

for symbol, issues in sorted_symbols[:10]:
    print(f"{symbol}: {len(issues['missing_in_s3'])} missing dates")
```

## Troubleshooting

Enable debug logging:
```bash
poetry run python scripts/validate_s3_against_yfinance.py --symbols AAPL 2>&1 | grep -E "DEBUG|ERROR"
```

Check S3 connectivity:
```bash
aws s3 ls s3://alchemiser-shared-market-data/ --max-items 5 --region us-east-1
```

Test yfinance directly:
```bash
poetry run python -c "import yfinance; df = yfinance.download('AAPL', period='1mo'); print(len(df))"
```

## FAQ

**Q: Why is price matching lenient (0.01 tolerance)?**
A: Different sources (yfinance, Alpaca, exchanges) may have slight rounding differences due to price adjustments, feeds, and precision. 0.01 catches real errors while ignoring noise.

**Q: Can I validate with a different yfinance source?**
A: Yes, modify `fetch_yfinance_data()` to use AlphaVantage, TwelveData, or other sources.

**Q: Why are some recent symbols slower to validate?**
A: yfinance makes HTTP requests per symbol. Add rate limiting or use `--limit` to test smaller batches.

**Q: How do I handle delisted symbols?**
A: They'll show "Missing in yfinance" errors, which is expected. Filter them out or document them separately.

## Support

For issues or enhancements, check:
- S3 access logs: `aws s3api list-objects-v2 --bucket <bucket> --prefix <symbol>/`
- yfinance documentation: https://github.com/ranaroussi/yfinance
- AWS SDK documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
