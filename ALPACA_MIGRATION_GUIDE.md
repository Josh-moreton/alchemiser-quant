# !/usr/bin/env python3
"""
Migration Guide: From yfinance to Alpaca Market Data API
========================================================

This document outlines the changes made to migrate the nuclear strategy backtest
from yfinance to Alpaca Market Data API.

FILES CREATED/MODIFIED
=======================

1. NEW FILE: src/backtest/alpaca_data_provider.py
   - Drop-in replacement for the yfinance-based BacktestDataProvider
   - Same interface, uses Alpaca Market Data API instead
   - Features:
     - Daily and hourly data downloads
     - Point-in-time data access (prevents look-ahead bias)
     - Retry logic for API reliability
     - Data validation and coverage reporting
     - Progress indicators for large downloads

2. MODIFIED: src/backtest/nuclear_backtest_framework.py
   - Removed old yfinance-based BacktestDataProvider class
   - Added import for AlpacaBacktestDataProvider
   - Created alias: BacktestDataProvider = AlpacaBacktestDataProvider
   - Updated type hints to support both providers
   - All other classes unchanged (BacktestNuclearStrategy, PortfolioBuilder, etc.)

3. MODIFIED: src/backtest/simplified_comprehensive_backtest.py
   - Updated imports to use AlpacaBacktestDataProvider
   - Changed data provider initialization calls
   - Updated display messages to show "Alpaca Data" source
   - All backtest logic remains the same

4. NEW FILE: test_alpaca_backtest.py
   - Test script to verify Alpaca backtest functionality
   - Shows data coverage reporting
   - Tests strategy evaluation and portfolio building

CONFIGURATION REQUIREMENTS
===========================

Your .env file must contain Alpaca API credentials:

```
ALPACA_PAPER_KEY=your_paper_key_here
ALPACA_PAPER_SECRET=your_paper_secret_here
# OR for live data:
ALPACA_KEY=your_live_key_here
ALPACA_SECRET=your_live_secret_here
```

USAGE
======

The backtest interface remains exactly the same:

```python
# Old way (yfinance)
from src.backtest.nuclear_backtest_framework import BacktestDataProvider
data_provider = BacktestDataProvider('2024-01-01', '2024-12-31')

# New way (Alpaca) - same interface!
from src.backtest.nuclear_backtest_framework import BacktestDataProvider
data_provider = BacktestDataProvider('2024-01-01', '2024-12-31')
# BacktestDataProvider is now an alias for AlpacaBacktestDataProvider

# Or be explicit:
from src.backtest.alpaca_data_provider import AlpacaBacktestDataProvider
data_provider = AlpacaBacktestDataProvider('2024-01-01', '2024-12-31')
```

ADVANTAGES OF ALPACA DATA
=========================

1. **More Reliable**: Professional market data API vs free service
2. **Better Coverage**: More symbols and longer history
3. **Real-time Capabilities**: Same API used for live trading
4. **Data Quality**: Professional-grade market data
5. **Rate Limits**: More generous API limits
6. **Consistency**: Same data source for backtest and live trading

TESTING
========

Run the test script to verify everything works:

```bash
python test_alpaca_backtest.py
```

This will:

- Test Alpaca API connection
- Download sample data
- Show data coverage report
- Test strategy evaluation
- Verify portfolio building

BACKWARD COMPATIBILITY
======================

- All existing backtest scripts will work without changes
- The BacktestDataProvider alias maintains compatibility
- Same interface and return formats
- Existing strategy and portfolio logic unchanged

MIGRATION CHECKLIST
===================

✅ Created AlpacaBacktestDataProvider with same interface as yfinance version
✅ Updated nuclear_backtest_framework.py imports
✅ Updated simplified_comprehensive_backtest.py
✅ Added backward compatibility alias
✅ Created test script
✅ Updated display messages to show Alpaca data source
✅ Maintained all existing functionality
✅ Added data validation and coverage reporting
✅ Added retry logic for API reliability

The migration is complete and all existing backtest code should work
without any changes, now using professional Alpaca market data!
"""

if **name** == "**main**":
    print(**doc**)
