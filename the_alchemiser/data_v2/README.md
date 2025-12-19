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

When `STRATEGY_APPEND_LIVE_BAR=true`, the CachedMarketDataAdapter:

1. **Reads historical bars** from S3 Parquet cache (nightly-refreshed)
2. **Fetches today's bar** from Alpaca Snapshot API via LiveBarProvider
3. **Appends today's bar** to the historical series
4. **Returns combined series** for indicator computation

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
| `STRATEGY_APPEND_LIVE_BAR` | `false` | Enable live bar injection |
| `MARKET_DATA_BUCKET` | (required) | S3 bucket for Parquet cache |
| `ALPACA__KEY` | (required) | Alpaca API key |
| `ALPACA__SECRET` | (required) | Alpaca secret key |

### Enable Live Bar Injection

Set in `template.yaml` for Strategy Lambda:
```yaml
Environment:
  Variables:
    STRATEGY_APPEND_LIVE_BAR: "true"
```

Or programmatically:
```python
adapter = CachedMarketDataAdapter(
    append_live_bar=True,
    live_bar_provider=LiveBarProvider(),
)
```

## Schedule

| Lambda | Time | Purpose |
|--------|------|---------|
| Data Lambda | Overnight (4 AM UTC) | Refresh historical bars in S3 |
| Strategy Lambda | 3:30 PM ET | Run strategies with live bar injection |

## File Structure

```
data_v2/
├── __init__.py
├── cached_market_data_adapter.py  # Main adapter with live bar injection
├── live_bar_provider.py           # Alpaca Snapshot API client
├── market_data_store.py           # S3 Parquet read/write
├── data_refresh_service.py        # Nightly data refresh
├── data_freshness_validator.py    # Data staleness checks
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
