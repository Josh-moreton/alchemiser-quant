# Persistence Architecture for Paper vs Live Trading

## Overview

The Alchemiser trading system now uses different persistence backends based on the trading mode to avoid S3 dependency issues in paper trading environments.

## Architecture

### Storage Abstraction
- `PersistenceHandler` protocol defines the interface for all storage operations
- Factory pattern automatically selects the appropriate implementation based on trading mode
- Same API for all persistence operations regardless of backend

### Trading Mode Detection
Trading mode is automatically detected from the `ALPACA_ENDPOINT` environment variable:
- Paper trading: endpoints containing "paper" (e.g., `https://paper-api.alpaca.markets/v2`)
- Live trading: other endpoints (e.g., `https://api.alpaca.markets`)
- Default: Paper trading (for safety when endpoint is not set)

### Persistence Implementations

#### Paper Trading Mode
- **Handler**: `LocalFileHandler`
- **Storage**: Secure temporary directory on local filesystem
- **Benefits**: No AWS credentials required, works in CI/CD environments
- **Use case**: Development, testing, paper trading

#### Live Trading Mode  
- **Handler**: `S3Handler`
- **Storage**: AWS S3 buckets
- **Benefits**: Persistent, scalable cloud storage
- **Use case**: Production deployments, live trading

## Usage

### Automatic (Recommended)
```python
from the_alchemiser.shared.persistence import create_persistence_handler

# Automatically detects trading mode from environment
handler = create_persistence_handler(paper_trading=detect_paper_trading_from_environment())
```

### Manual
```python
from the_alchemiser.shared.persistence import create_persistence_handler

# Force paper trading mode (local storage)
handler = create_persistence_handler(paper_trading=True)

# Force live trading mode (S3 storage)  
handler = create_persistence_handler(paper_trading=False)
```

### Integration
The `StrategyOrderTracker` and dashboard reporting automatically use the factory pattern:
```python
# This will use LocalFileHandler for paper trading, S3Handler for live trading
tracker = StrategyOrderTracker(paper_trading=True)
```

## Environment Variables

| Variable | Purpose | Paper Trading Value | Live Trading Value |
|----------|---------|-------------------|------------------|
| `ALPACA_ENDPOINT` | Trading mode detection | `https://paper-api.alpaca.markets/v2` | `https://api.alpaca.markets` |
| `ALPACA_PAPER_TRADING` | Explicit override | `true`/`1`/`yes` | `false`/`0`/`no` |

## File Storage Paths

### Paper Trading (Local)
- Base directory: Secure temporary directory (e.g., `/tmp/alchemiser_paper_XXXXXX`)
- S3 URIs are converted to local paths: `s3://bucket/path/file.json` → `{base_dir}/bucket/path/file.json`

### Live Trading (S3)
- Uses actual S3 buckets and keys as specified in URIs
- Requires AWS credentials (IAM role, environment variables, or AWS CLI)

## Migration

Existing code automatically benefits from this change with no modifications required:
- `StrategyOrderTracker` instances automatically use the correct backend
- Dashboard data saving uses the correct backend
- All S3 URIs work the same way regardless of backend

## Benefits

1. **No CI/CD failures**: Paper trading no longer requires AWS credentials
2. **Seamless development**: Local development works without S3 setup
3. **Production ready**: Live trading continues to use S3 for persistence
4. **Backward compatible**: Existing code works without changes
5. **Secure**: Uses proper temporary directories, not hardcoded paths