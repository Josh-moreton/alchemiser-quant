# Data_v2 Module

**Business Unit: data | Status: current**

## Overview

The Data_v2 module provides market data infrastructure for the trading system, using S3-backed Parquet storage for historical OHLCV bars. Data is refreshed from Alpaca on two schedules: overnight (full backfill) and post-market-close (today's completed daily bar).

## Core Components

### CachedMarketDataAdapter
Primary market data interface for the Strategy Lambda. Reads historical OHLCV bars from S3 Parquet cache.

```python
from the_alchemiser.data_v2.cached_market_data_adapter import CachedMarketDataAdapter

adapter = CachedMarketDataAdapter()
bars = adapter.get_bars(symbol, period="1Y", timeframe="1Day")
# Returns ~250 completed daily bars from S3
```

### MarketDataStore
S3-backed Parquet storage for historical bars. Populated by the Data Lambda on schedule.

### DataRefreshService
Fetches historical bars from Alpaca API and stores in S3.

## Data Flow

```
                    DATA REFRESH (two schedules)
                    ============================

     ┌─────────────────┐         ┌─────────────────┐
     │  Overnight       │         │  Post-Close      │
     │  (4 AM UTC)      │         │  (4:05 PM ET)    │
     │  Full backfill   │         │  Today's bar     │
     └────────┬─────────┘         └────────┬─────────┘
              │                            │
              └──────────┬─────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Alpaca Markets API   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   S3 Parquet Cache    │
              │   (complete daily    │
              │    bars only)        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  CachedMarketData    │
              │  Adapter (read)      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   IndicatorService   │
              │  (SMA, RSI, etc.)    │
              └──────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MARKET_DATA_BUCKET` | (required) | S3 bucket for Parquet cache |

## Schedule

| Schedule | Time | Purpose |
|----------|------|---------|
| Overnight refresh | 4 AM UTC | Full historical backfill to S3 |
| Post-close refresh | 4:05 PM ET | Add today's completed daily bar to S3 |
| Strategy execution | 4:10 PM ET | Run strategies using completed bars |

## File Structure

```
data_v2/
├── __init__.py
├── cached_market_data_adapter.py  # Main adapter (S3 Parquet reader)
├── market_data_store.py           # S3 Parquet read/write
├── data_refresh_service.py        # Data refresh from Alpaca
├── data_freshness_validator.py    # Data staleness checks
├── fetch_request_service.py       # Batch fetch coordination
├── lambda_handler.py              # Data Lambda entry point
├── symbol_extractor.py            # Symbol list extraction
└── README.md                      # This file
```

## Related Documentation

- [Strategy_v2 README](../strategy_v2/README.md) - How strategies consume market data
- [Copilot Instructions](../../.github/copilot-instructions.md) - Development guidelines
