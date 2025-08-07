# UnifiedDataProvider Usage Inventory

## Current Call Sites

Based on codebase analysis, the following modules import and use `UnifiedDataProvider`:

### Core Strategy Modules
1. **the_alchemiser/core/trading/klm_ensemble_engine.py**: 
   - Line 444: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 446: `data_provider = UnifiedDataProvider(paper_trading=True)`

2. **the_alchemiser/core/trading/klm_trading_bot.py**:
   - Line 27: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 131: `data_provider = UnifiedDataProvider(paper_trading=True)`

3. **the_alchemiser/core/trading/strategy_manager.py**:
   - Line 87: Type annotation in docstring
   - Line 120: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 122: `shared_data_provider = UnifiedDataProvider(paper_trading=True)`

4. **the_alchemiser/core/trading/tecl_signals.py**:
   - Line 39: Comment indicating import location

### Execution Modules
5. **the_alchemiser/execution/smart_execution.py**:
   - Line 23: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 77: Return type annotation

6. **the_alchemiser/execution/trading_engine.py**:
   - Line 172: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 174: `self.data_provider = UnifiedDataProvider(paper_trading=self.paper_trading, config=config)`

7. **the_alchemiser/execution/alpaca_client.py**:
   - Line 52: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 85: Type annotation in constructor

### Main Entry Point
8. **the_alchemiser/main.py**:
   - Line 108: `from the_alchemiser.core.data.data_provider import UnifiedDataProvider`
   - Line 113: `shared_data_provider = UnifiedDataProvider(paper_trading=True)`

### Utility Modules
9. **the_alchemiser/utils/account_utils.py**:
   - Line 20: Type annotation in docstring

## Key Usage Patterns

### Initialization Patterns
- Most common: `UnifiedDataProvider(paper_trading=True)`
- With config: `UnifiedDataProvider(paper_trading=self.paper_trading, config=config)`
- Shared instance pattern in strategy manager

### Primary Methods Used
- `get_data()` - Historical market data
- `get_current_price()` - Real-time pricing
- `get_account_info()` - Account information
- `get_positions()` - Current positions
- `get_latest_quote()` - Bid/ask quotes
- `trading_client` - Access to trading client

### Dependencies
- Alpaca API credentials management
- Real-time pricing service integration
- Caching functionality
- Trading client access

## Migration Considerations

### High Impact Changes
1. Strategy engines rely heavily on data provider for market data
2. Trading engine uses it for both market data and trading operations
3. Main entry point creates shared instances

### Low Risk Areas
1. Type annotations and docstrings
2. Comment references

### Key Interfaces to Maintain
1. Constructor signature compatibility
2. Core method signatures for data access
3. Trading client access pattern
