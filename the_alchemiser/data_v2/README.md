# Data_v2 Module

**Business Unit: data | Status: current**

## Overview

The Data_v2 module provides market data infrastructure for the trading system, including S3-backed caching of historical bars and real-time price injection for up-to-date indicator computation.

## Core Components

### CachedMarketDataAdapter
Primary market data interface for the Strategy Lambda. Reads historical OHLCV bars from S3 Parquet cache and optionally injects today's live bar.

```python
from the_alchemiser.data_v2.cached_market_data_adapter import CachedMarketDataAdapter

adapter = CachedMarketDataAdapter(
    append_live_bar=True,  # Enable live bar injection
)
bars = adapter.get_bars(symbol, period="1Y", timeframe="1Day")
# Returns 250 bars: 249 historical + 1 live (today)
```

### LiveBarProvider
Fetches today's OHLCV bar from Alpaca Snapshot API. Caches results per-symbol for Lambda duration.

```python
from the_alchemiser.data_v2.live_bar_provider import LiveBarProvider

provider = LiveBarProvider()
bar = provider.get_todays_bar("SPY")
# Returns BarModel with today's open, high, low, close, volume
```

### MarketDataStore
S3-backed Parquet storage for historical bars. Populated nightly by Data Lambda.

### DataRefreshService
Fetches historical bars from Alpaca API and stores in S3. Runs on schedule (overnight).

## Live Bar Injection

The CachedMarketDataAdapter automatically:

1. **Reads historical bars** from S3 Parquet cache (nightly-refreshed)
2. **Fetches today's bar** from Alpaca Snapshot API via LiveBarProvider
3. **Appends today's bar** to the historical series
4. **Returns combined series** for indicator computation

Live bar injection is enabled by default (`append_live_bar=True`).

### Data Flow

```
┌─────────────────────┐     ┌──────────────────────┐
│   S3 Parquet Cache  │     │  Alpaca Snapshot API │
│   (historical bars) │     │   (today's bar)      │
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          │  249 bars                  │  1 bar
          │  (through yesterday)       │  (OHLCV today)
          └──────────┬─────────────────┘
                     │
                     ▼
          ┌──────────────────────────┐
          │  CachedMarketDataAdapter │
          │   append_live_bar=True   │
          └──────────┬───────────────┘
                     │
                     │  250 bars total
                     ▼
          ┌──────────────────────────┐
          │    IndicatorService      │
          │  (200-day SMA, RSI, etc) │
          └──────────────────────────┘
```

### Today's Bar Contents

The live bar from Alpaca Snapshot includes:

| Field | Description |
|-------|-------------|
| `open` | Today's opening price |
| `high` | Today's high (updated throughout day) |
| `low` | Today's low (updated throughout day) |
| `close` | Current/latest price |
| `volume` | Today's cumulative volume |

### Caching

Live bars are cached per-symbol for the Lambda invocation:
- First request: API call to Alpaca
- Subsequent requests: Returns cached bar
- Cache cleared: Next Lambda cold start

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MARKET_DATA_BUCKET` | (required) | S3 bucket for Parquet cache |
| `ALPACA__KEY` | (required) | Alpaca API key |
| `ALPACA__SECRET` | (required) | Alpaca secret key |

### Programmatic Configuration

```python
# Live bar injection is enabled by default
adapter = CachedMarketDataAdapter()

# Or explicitly with custom provider
adapter = CachedMarketDataAdapter(
    append_live_bar=True,
    live_bar_provider=LiveBarProvider(),
)
```

## Schedule

| Lambda | Time | Purpose |
|--------|------|---------|
| Data Lambda (Refresh) | Overnight (4 AM UTC) | Refresh historical bars in S3 |
| Data Lambda (Validation) | 3 PM EST / 4 PM EDT (8 PM UTC) Weekdays | Validate data quality against Yahoo Finance |
| Strategy Lambda | 3:30 PM ET | Run strategies with live bar injection |

## Data Quality Validation

The Data Lambda runs daily data quality validation at 8 PM UTC on weekdays (3 PM Eastern Standard Time / 4 PM Eastern Daylight Time). This validates S3 cached data against Yahoo Finance to detect discrepancies.
1. **Fetch data from yfinance**: Downloads recent bars for comparison
2. **Compare OHLCV fields**: Validates close, open, high, low, and volume
3. **Apply tolerances**: 
   - Price fields: 0.5% tolerance
   - Volume: 5% tolerance
4. **Generate report**: Creates CSV with all discrepancies
5. **Upload to S3**: Stores report in `data-quality-reports/` prefix
6. **Publish event**: Emits `DataValidationCompleted` event

### Manual Validation

```python
# Trigger validation via Lambda invocation
{
    "validation_trigger": true,
    "symbols": ["AAPL", "MSFT"],  # Optional: specific symbols
    "lookback_days": 5             # Optional: days to validate
}
```

### Validation Reports

Reports are stored in S3:
```
s3://alchemiser-shared-market-data/data-quality-reports/
├── 2025-01-01_validation_report.csv
├── 2025-01-02_validation_report.csv
└── ...
```

Report format:
```csv
Symbol,Date,Field,Alpaca Value,YFinance Value,Diff %
AAPL,2025-01-01,close,150.00,151.00,0.67
```

## File Structure

```
data_v2/
├── __init__.py
├── cached_market_data_adapter.py  # Main adapter with live bar injection
├── live_bar_provider.py           # Alpaca Snapshot API client
├── market_data_store.py           # S3 Parquet read/write
├── data_refresh_service.py        # Nightly data refresh
├── data_freshness_validator.py    # Data staleness checks
├── data_quality_validator.py      # External validation against yfinance
├── fetch_request_service.py       # Batch fetch coordination
├── lambda_handler.py              # Data Lambda entry point
├── symbol_extractor.py            # Symbol list extraction
└── README.md                      # This file
```

## Testing

```bash
# Run data module tests
poetry run pytest tests/data_v2/ -v

# Test live bar provider manually
python -c "
from the_alchemiser.data_v2.live_bar_provider import LiveBarProvider
bar = LiveBarProvider().get_todays_bar('SPY')
print(f'SPY: ${float(bar.close):.2f}, vol={bar.volume:,}')
"
```

## Related Documentation

- [Strategy_v2 README](../strategy_v2/README.md) - How strategies consume market data
- [Architecture Docs](../../docs/architecture/) - System design
- [Copilot Instructions](../../.github/copilot-instructions.md) - Development guidelines
