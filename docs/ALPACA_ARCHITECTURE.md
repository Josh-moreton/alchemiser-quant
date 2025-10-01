# Alpaca Integration Architecture

**Business Unit:** shared | **Status:** current

## Purpose

This document explains how The Alchemiser integrates with the Alpaca broker API, following clean architecture principles to maintain separation between domain logic and broker mechanics.

## Architecture Principles

The Alpaca integration follows these key principles:

1. **Single Responsibility:** All Alpaca API interactions are centralized in `shared/brokers/`
2. **Domain Ownership:** Business modules (Execution, Portfolio) own their logic
3. **Clean Separation:** Adapter handles "how to call API", domain handles "when and why"
4. **DRY:** No duplication of authentication, error handling, or retry logic
5. **Practical:** No over-abstraction—one well-structured adapter, not a generic broker interface

## Layer Structure

```
┌─────────────────────────────────────────────────────┐
│       Business Modules (Domain Logic)               │
│  execution_v2/ - Order orchestration & timing       │
│  portfolio_v2/ - Rebalance planning & allocation    │
│  strategy_v2/  - Signal generation                  │
└─────────────────────────────────────────────────────┘
                        ↓
                    uses via
                        ↓
┌─────────────────────────────────────────────────────┐
│         shared/brokers/AlpacaManager                 │
│  Thin wrapper - API mechanics only                  │
│  - Authentication                                   │
│  - Order placement                                  │
│  - Position queries                                 │
│  - Error handling & retries                         │
│  - Rate limiting                                    │
└─────────────────────────────────────────────────────┘
                        ↓
                     wraps
                        ↓
┌─────────────────────────────────────────────────────┐
│              Alpaca SDK (alpaca-py)                  │
│  Raw API - TradingClient, DataClient                │
└─────────────────────────────────────────────────────┘
```

## Core Components

### AlpacaManager (`shared/brokers/alpaca_manager.py`)

The single entry point for all Alpaca API interactions.

**Responsibilities:**
- Initialize Alpaca clients (TradingClient, StockHistoricalDataClient)
- Implement domain interfaces (TradingRepository, MarketDataRepository, AccountRepository)
- Delegate to specialized services
- Manage singleton instances per credentials
- Coordinate WebSocket connections

**Key Features:**
```python
class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Centralized Alpaca client management implementing domain interfaces."""
    
    def __init__(self, api_key: str, secret_key: str, *, paper: bool = True):
        # Initialize clients
        self._trading_client = TradingClient(api_key, secret_key, paper)
        self._data_client = StockHistoricalDataClient(api_key, secret_key)
        
        # Delegate to specialized services
        self._account_service = AlpacaAccountService(self._trading_client)
        self._trading_service = AlpacaTradingService(self._trading_client, ...)
        self._asset_metadata_service = AssetMetadataService(self._trading_client)
```

**Public API:**
- `place_order(order_request)` - Place market or limit orders
- `get_positions()` - Query current positions
- `get_account()` - Get account information
- `get_quote(symbol)` - Fetch current quote
- `cancel_order(order_id)` - Cancel pending order

### AlpacaTradingService (`shared/services/alpaca_trading_service.py`)

Handles all trading operations with proper error handling and retry logic.

**Responsibilities:**
- Order placement (market, limit)
- Order status monitoring
- Order cancellation
- Smart execution coordination
- WebSocket integration for real-time updates

**Key Methods:**
- `place_order(order_request)` - Execute order with validation
- `get_order_execution_result(order_id)` - Check order status
- `cancel_order(order_id)` - Cancel pending order
- `replace_order(order_id, new_request)` - Modify existing order

### AlpacaAccountService (`shared/services/alpaca_account_service.py`)

Manages account and position queries.

**Responsibilities:**
- Account information retrieval
- Position queries and aggregation
- Buying power calculations
- Portfolio history

**Key Methods:**
- `get_account_object()` - Fetch account details
- `get_positions()` - List all positions
- `get_position(symbol)` - Get specific position
- `get_buying_power()` - Calculate available buying power

### AlpacaErrorHandler (`shared/utils/alpaca_error_handler.py`)

Centralized error handling with intelligent retry logic.

**Features:**
- Transient vs permanent error detection
- Exponential backoff with jitter
- API rate limit handling
- Error message sanitization (removes sensitive data)

**Usage:**
```python
from the_alchemiser.shared.utils.alpaca_error_handler import alpaca_retry_context

with alpaca_retry_context(max_retries=3, operation_name="Fetch positions"):
    positions = trading_client.get_all_positions()
```

## Domain Module Usage

### Execution Module (`execution_v2/`)

**Domain Logic (what Execution owns):**
- Deciding WHEN to place an order
- Order timing and orchestration
- Smart execution strategies
- Rebalance plan execution
- Position validation

**Example:**
```python
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

class Executor:
    def __init__(self, alpaca_manager: AlpacaManager):
        self.alpaca_manager = alpaca_manager  # Inject adapter
        
    async def execute_order(self, symbol: str, side: str, quantity: Decimal):
        # Domain logic: Validation & decision-making
        validation_result = self.validator.validate_order(symbol, quantity, side)
        
        if not validation_result.is_valid:
            return self._build_validation_failure_result(...)
        
        # Broker mechanics: Delegated to AlpacaManager
        order_request = MarketOrderRequest(symbol=symbol, qty=float(quantity), side=side)
        broker_result = self.alpaca_manager.place_order(order_request)
        
        return self._build_execution_result(broker_result)
```

### Portfolio Module (`portfolio_v2/`)

**Domain Logic (what Portfolio owns):**
- Rebalance plan calculation
- Allocation decisions
- Portfolio state analysis

**Adapter Pattern:**
```python
from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import AlpacaDataAdapter

class PortfolioService:
    def __init__(self, alpaca_manager: AlpacaManager):
        # Use thin adapter for domain-specific conveniences
        self._data_adapter = AlpacaDataAdapter(alpaca_manager)
    
    def build_rebalance_plan(self, signals):
        # Domain logic: Get current state via adapter
        positions = self._data_adapter.get_positions()  # Returns Dict[str, Decimal]
        prices = self._data_adapter.get_current_prices(symbols)
        cash = self._data_adapter.get_account_cash()
        
        # Domain logic: Calculate rebalance trades
        return self._calculate_trades(positions, prices, cash, signals)
```

The `AlpacaDataAdapter` adds domain-specific conveniences:
- Converts to `Decimal` for monetary precision
- Provides clean error messages
- Adds portfolio-specific logging
- Still delegates actual API calls to `AlpacaManager`

## Error Handling Strategy

### Transient Errors (retry automatically)

- Network timeouts
- API rate limits (429)
- Server errors (500, 502, 503)
- Connection errors

**Retry Logic:**
- Max 3 retries by default
- Exponential backoff: 1s, 2s, 4s
- Jitter added to prevent thundering herd

### Permanent Errors (fail immediately)

- Invalid credentials (401, 403)
- Invalid symbols (404)
- Insufficient funds
- Market closed

**Handling:**
- No retries
- Clear error messages
- Logged with context

## Extending the Integration

### Adding New Functionality

**To add a new Alpaca feature:**

1. **Add to appropriate service** (trading, account, or market data)
2. **Add method to AlpacaManager** that delegates to the service
3. **Use error handling wrapper** (`alpaca_retry_context`)
4. **Add tests** in `tests/shared/`

**Example: Adding order history**

```python
# Step 1: Add to AlpacaAccountService
class AlpacaAccountService:
    def get_order_history(self, days: int = 30) -> list[Order]:
        """Fetch order history for last N days."""
        end = datetime.now(UTC)
        start = end - timedelta(days=days)
        
        with alpaca_retry_context(operation_name="Fetch order history"):
            return self._trading_client.get_orders(
                GetOrdersRequest(after=start, until=end)
            )

# Step 2: Add to AlpacaManager
class AlpacaManager:
    def get_order_history(self, days: int = 30) -> list[Order]:
        """Get order history."""
        return self._account_service.get_order_history(days)

# Step 3: Use in domain module
class ExecutionAnalyzer:
    def analyze_recent_trades(self):
        orders = self.alpaca_manager.get_order_history(days=7)
        # Domain logic here
```

### Adding New Error Handling

Add error detection to `AlpacaErrorHandler.is_transient_error()`:

```python
@staticmethod
def is_transient_error(error: Exception) -> tuple[bool, str]:
    """Determine if error is transient (should retry)."""
    
    # Add new transient error type
    if "new transient condition" in str(error):
        return True, "New transient error detected"
    
    # Existing logic...
```

## Testing Strategy

### Unit Tests

- **Mock AlpacaManager** in business module tests
- **Test error scenarios** with synthetic errors
- **Verify retry logic** with controlled failures

**Example:**
```python
def test_executor_handles_transient_error(mock_alpaca_manager):
    mock_alpaca_manager.place_order.side_effect = [
        HTTPError("429 Rate Limit"),  # First attempt fails
        ExecutedOrder(...),            # Second attempt succeeds
    ]
    
    executor = Executor(mock_alpaca_manager)
    result = executor.execute_order("AAPL", "buy", Decimal("10"))
    
    assert result.success
    assert mock_alpaca_manager.place_order.call_count == 2
```

### Integration Tests

- **Use paper trading credentials** for real API tests
- **Test actual order placement** in test environment
- **Verify error handling** with invalid requests

## Best Practices

### DO ✅

- **Inject AlpacaManager** into domain modules via constructor
- **Use the adapter** for all Alpaca interactions
- **Add retries** for transient errors via `alpaca_retry_context`
- **Log operations** with correlation IDs for traceability
- **Convert to Decimal** for all monetary values
- **Validate inputs** in domain layer before calling adapter

### DON'T ❌

- **Don't import Alpaca SDK** directly in business modules
- **Don't duplicate** error handling or retry logic
- **Don't mix** domain logic with API calls
- **Don't use floats** for money (use Decimal)
- **Don't catch all exceptions** without re-raising typed errors
- **Don't create multiple** AlpacaManager instances for same credentials

## Module Import Rules

**Enforcement via import-linter:**

```toml
[[tool.importlinter.contracts]]
name = "Execution module cannot import from Portfolio"
type = "forbidden"
source_modules = ["the_alchemiser.execution_v2"]
forbidden_modules = ["the_alchemiser.portfolio_v2"]

[[tool.importlinter.contracts]]
name = "Business modules use shared adapter only"
type = "layers"
layers = [
    "the_alchemiser.execution_v2",
    "the_alchemiser.portfolio_v2", 
    "the_alchemiser.shared",
]
```

## Configuration

### Environment Variables

```bash
# Alpaca credentials
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here

# Trading mode
STAGE=paper  # or 'live'

# Optional: Custom base URL
ALPACA_BASE_URL=https://api.alpaca.markets
```

### Code Configuration

```python
from the_alchemiser.shared.brokers import create_alpaca_manager

# Factory function handles configuration
alpaca_manager = create_alpaca_manager(
    api_key=settings.alpaca_api_key,
    secret_key=settings.alpaca_secret_key,
    paper=settings.is_paper_trading
)
```

## Performance Considerations

### WebSocket Management

- **Singleton pattern** prevents duplicate connections
- **Shared WebSocket** across all operations
- **Automatic reconnection** on connection loss

### Rate Limiting

- **Alpaca limits:** 200 requests/minute
- **Built-in throttling** in WebSocket manager
- **Exponential backoff** on rate limit errors

### Caching

- **Position data** cached briefly to reduce API calls
- **Account info** cached with TTL
- **Market data** fetched in batch where possible

## Observability

### Logging

All operations logged with structured context:

```python
log_with_context(
    logger,
    logging.INFO,
    "Order placed successfully",
    module="execution_v2",
    symbol=symbol,
    order_id=order_id,
    correlation_id=correlation_id,
)
```

### Metrics

- Order placement latency
- API call success/failure rates
- Retry counts
- WebSocket connection status

## Troubleshooting

### Common Issues

**Issue:** "Insufficient buying power"
- **Cause:** Account doesn't have enough cash
- **Solution:** Check `get_buying_power()` before placing buy orders

**Issue:** "429 Rate Limit Exceeded"
- **Cause:** Too many API calls in short period
- **Solution:** Automatic retry with backoff; reduce query frequency

**Issue:** "Order rejected: market closed"
- **Cause:** Attempting to trade outside market hours
- **Solution:** Check market status before placing orders

**Issue:** "Authentication failed"
- **Cause:** Invalid API credentials
- **Solution:** Verify `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`

## References

### Internal Documentation

- [WebSocket Architecture](./WEBSOCKET_ARCHITECTURE.md)
- [Limit Order Pricing](./limit-order-pricing.md)
- [README - System Architecture](../README.md#system-architecture)

### External Documentation

- [Alpaca API Documentation](https://docs.alpaca.markets/)
- [alpaca-py SDK Documentation](https://alpaca.markets/docs/python-sdk/)

## Changelog

### 2025-01 - Current Architecture

- AlpacaManager moved to `shared/brokers/` from `execution/`
- Extracted specialized services (Trading, Account, MarketData)
- Implemented domain interfaces (TradingRepository, etc.)
- Added comprehensive error handling with retry logic
- Centralized WebSocket management

### Legacy (pre-2025)

- Direct Alpaca SDK usage in multiple modules
- Scattered error handling
- No retry logic
- Multiple WebSocket connections

---

**Last Updated:** January 2025  
**Maintained By:** Architecture Team  
**Status:** Current - Production Ready
