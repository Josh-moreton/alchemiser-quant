# Validation Scripts

This directory contains validation scripts for data quality verification.

## Scripts

### Data Lake Validation (`validate_data_lake.py`)

Comprehensive validation of S3 market data against yfinance as the source of truth.

**Validates:**
1. **Completeness** - All symbols from strategy DSL configs exist in S3
2. **Freshness** - S3 data has the latest complete bar available on yfinance
3. **Integrity** - Close prices match yfinance Adj Close within 2% tolerance
4. **Gaps** - No missing trading days in the data series

**Usage:**
```bash
# Validate all configured symbols
make validate-data-lake

# Validate specific symbols
make validate-data-lake symbols=SPY,QQQ

# Show detailed debug output
make validate-data-lake debug=1

# Mark failed symbols for automatic refetch
make validate-data-lake mark-bad=1
```

### Signal Validation (`validate_signals.py`)

Interactive validation of strategy signals against Composer.trade.

**Usage:**
```bash
# Validate latest dev session
make validate-signals

# Validate prod signals
make validate-signals stage=prod

# Start fresh validation
make validate-signals fresh=1
```

### DynamoDB Data Validation (`validate_dynamo_data.py`)

Validates DynamoDB trade ledger data for per-strategy performance metrics.

**Validates:**
1. Entity completeness (TRADE, STRATEGY_LOT, SIGNAL, STRATEGY_METADATA)
2. Strategy attribution on trades
3. Lot data quality (entry/exit records, P&L calculations)
4. Data linkage (correlation_id chains)

**Usage:**
```bash
# Validate prod data
make validate-dynamo

# Validate dev data
make validate-dynamo stage=dev

# Verbose output
make validate-dynamo verbose=1

# JSON output
make validate-dynamo json=1
```

### Legacy S3 Validation (`validate_s3_against_yfinance.py`)

Original S3 vs yfinance validation script. Use `validate_data_lake.py` for enhanced validation.

## Configuration

### Price Tolerance

The price tolerance for data lake validation is set in `validate_data_lake.py`:

```python
PRICE_TOLERANCE_PCT = 0.02  # 2%
```

This allows for minor rounding differences between Alpaca and yfinance data.

### Output

Validation reports are saved to `validation_results/`:
- `data_lake_validation_YYYY-MM-DD.csv`
- `signal_validation_YYYY-MM-DD.csv`
