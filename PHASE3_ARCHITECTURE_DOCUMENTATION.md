# Phase 3 Enhanced Services Architecture Documentation

## Overview

The Alchemiser trading system has been successfully refactored into a clean, layered architecture that provides logical separation of concerns, type safety, and testability. This document outlines the new architecture and how to use it.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  TradingServiceManager (Unified Facade)                    │
│  ├── High-level trading operations                         │
│  ├── Smart order execution                                 │
│  └── Trading dashboard aggregation                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  OrderService        │  PositionService                    │
│  ├── Order validation│  ├── Position analysis             │
│  ├── Order placement │  ├── Risk calculations             │
│  └── Order tracking  │  └── Portfolio metrics             │
│                      │                                     │
│  MarketDataService   │  AccountService                     │
│  ├── Price validation│  ├── Account metrics               │
│  ├── Data caching    │  ├── Risk assessment               │
│  └── Spread analysis │  └── Trade eligibility             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  TradingRepository   │  AccountRepository                  │
│  ├── get_positions_dict()  ├── get_positions()            │
│  ├── place_market_order()  ├── get_account()              │
│  ├── liquidate_position()  ├── get_buying_power()         │
│  └── cancel_order()        └── get_portfolio_value()      │
│                      │                                     │
│  MarketDataRepository                                      │
│  ├── get_current_price()                                  │
│  ├── get_quote()                                          │
│  └── validate_symbol()                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│                   AlpacaManager                            │
│  ├── Implements all repository interfaces                  │
│  ├── Manages Alpaca API clients                           │
│  ├── Provides consistent error handling                    │
│  ├── Handles connection management                         │
│  └── Centralizes all external API interactions             │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Infrastructure Layer

#### AlpacaManager
**Location**: `the_alchemiser/services/alpaca_manager.py`

**Purpose**: Single point of integration with Alpaca API, implementing all domain interfaces.

**Key Features**:
- Implements `TradingRepository`, `AccountRepository`, and `MarketDataRepository`
- Centralized error handling and logging
- Connection management for trading and market data clients
- Type-safe wrapper methods around Alpaca SDK

**Example Usage**:
```python
from the_alchemiser.services.alpaca_manager import AlpacaManager

# Initialize
alpaca = AlpacaManager(api_key, secret_key, paper=True)

# Direct repository interface usage
positions = alpaca.get_positions()  # Returns list[Any] for AccountRepository
position_dict = alpaca.get_positions_dict()  # Returns dict[str, float] for TradingRepository
order_id = alpaca.place_market_order("AAPL", "buy", qty=1.0)
```

### 2. Domain Layer

#### Repository Interfaces
**Location**: `the_alchemiser/domain/interfaces/`

**Purpose**: Define contracts for data access and external service interactions.

##### TradingRepository
```python
class TradingRepository(Protocol):
    def get_positions_dict(self) -> dict[str, float]: ...
    def place_market_order(self, symbol: str, side: str, qty: float | None = None, notional: float | None = None) -> str | None: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def liquidate_position(self, symbol: str) -> str | None: ...
```

##### AccountRepository
```python
class AccountRepository(Protocol):
    def get_account(self) -> dict[str, Any] | None: ...
    def get_positions(self) -> list[Any]: ...
    def get_buying_power(self) -> float | None: ...
    def get_portfolio_value(self) -> float | None: ...
```

##### MarketDataRepository
```python
class MarketDataRepository(Protocol):
    def get_current_price(self, symbol: str) -> float | None: ...
    def get_quote(self, symbol: str) -> dict[str, Any] | None: ...
    def validate_symbol(self, symbol: str) -> bool: ...
```

### 3. Service Layer

#### OrderService
**Location**: `the_alchemiser/services/enhanced/order_service.py`

**Purpose**: Type-safe order management with comprehensive validation.

**Key Features**:
- Parameter validation and normalization
- Market price validation before order placement
- Support for market and limit orders
- Position validation for sell orders
- Enhanced error handling with domain-specific exceptions

**Example Usage**:
```python
from the_alchemiser.services.enhanced.order_service import OrderService

order_service = OrderService(alpaca_manager)

# Place validated market order
order_id = order_service.place_market_order(
    symbol="AAPL",
    side="buy",
    quantity=1.0,
    validate_price=True
)

# Place validated limit order
order_id = order_service.place_limit_order(
    symbol="AAPL",
    side="sell",
    quantity=1.0,
    limit_price=150.00,
    time_in_force="day"
)
```

#### PositionService
**Location**: `the_alchemiser/services/enhanced/position_service.py`

**Purpose**: Position analysis, risk management, and portfolio metrics.

**Key Features**:
- Enhanced position information with analysis
- Portfolio-level risk calculations
- Position weight and diversification metrics
- Risk limit validation
- Portfolio summary with unrealized P&L

**Example Usage**:
```python
from the_alchemiser.services.enhanced.position_service import PositionService

position_service = PositionService(alpaca_manager, alpaca_manager, alpaca_manager)

# Get positions with enhanced analysis
positions = position_service.get_positions_with_analysis()
for symbol, position_info in positions.items():
    print(f"{symbol}: {position_info.quantity} shares, ${position_info.market_value:.2f}")

# Get portfolio summary
portfolio = position_service.get_portfolio_summary()
print(f"Total Value: ${portfolio.total_market_value:.2f}")
print(f"Unrealized P&L: ${portfolio.total_unrealized_pnl:.2f}")

# Check position limits before trading
can_buy = position_service.check_position_limits("AAPL", 10.0)
```

#### MarketDataService
**Location**: `the_alchemiser/services/enhanced/market_data_service.py`

**Purpose**: Enhanced market data operations with caching and validation.

**Key Features**:
- Price validation with staleness checks
- Intelligent caching to reduce API calls
- Batch price retrieval for multiple symbols
- Spread analysis for bid-ask spreads
- Market hours detection

**Example Usage**:
```python
from the_alchemiser.services.enhanced.market_data_service import MarketDataService

market_data = MarketDataService(alpaca_manager)

# Get validated current price
price = market_data.get_validated_price("AAPL", max_age_seconds=30)

# Get multiple prices efficiently
symbols = ["AAPL", "GOOGL", "MSFT"]
prices = market_data.get_batch_prices(symbols)

# Analyze bid-ask spread
spread_info = market_data.get_spread_analysis("AAPL")
if spread_info:
    print(f"Spread: ${spread_info['spread']:.4f} ({spread_info['spread_percent']:.2f}%)")
```

#### AccountService
**Location**: `the_alchemiser/services/enhanced/account_service.py`

**Purpose**: Account management, risk assessment, and trade eligibility validation.

**Key Features**:
- Comprehensive risk metrics calculation
- Trade eligibility validation
- Portfolio allocation analysis
- Safe attribute access with helper methods
- Buying power validation

**Example Usage**:
```python
from the_alchemiser.services.enhanced.account_service import AccountService

account_service = AccountService(alpaca_manager)

# Get comprehensive risk metrics
risk_metrics = account_service.get_risk_metrics()
print(f"Portfolio Beta: {risk_metrics['portfolio_beta']:.2f}")
print(f"Max Drawdown: {risk_metrics['max_drawdown_percent']:.2f}%")

# Validate trade eligibility
eligibility = account_service.validate_trade_eligibility(
    symbol="AAPL",
    quantity=10,
    side="buy",
    estimated_cost=1500.00
)
if eligibility["eligible"]:
    print("Trade approved")
else:
    print(f"Trade rejected: {eligibility['reason']}")

# Get portfolio allocation
allocation = account_service.get_portfolio_allocation()
for symbol, weight in allocation["allocations"].items():
    print(f"{symbol}: {weight:.2f}%")
```

### 4. Application Layer

#### TradingServiceManager
**Location**: `the_alchemiser/services/enhanced/trading_service_manager.py`

**Purpose**: Unified facade providing high-level trading operations and dashboard functionality.

**Key Features**:
- Single entry point for all trading operations
- Smart order execution with pre-trade validation
- Comprehensive trading dashboard
- Consistent error handling and response formatting
- Integration of all enhanced services

**Example Usage**:
```python
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

# Initialize with credentials
trading_manager = TradingServiceManager(api_key, secret_key, paper=True)

# Place orders with automatic validation
result = trading_manager.place_market_order("AAPL", 1.0, "buy", validate=True)
if result["success"]:
    print(f"Order placed: {result['order_id']}")

# Execute smart orders with comprehensive validation
smart_result = trading_manager.execute_smart_order(
    symbol="AAPL",
    quantity=10,
    side="buy",
    order_type="market"
)

# Get comprehensive trading dashboard
dashboard = trading_manager.get_trading_dashboard()
print(f"Account Value: ${dashboard['account']['total_value']:.2f}")
print(f"Buying Power: ${dashboard['account']['buying_power']:.2f}")
print(f"Open Positions: {len(dashboard['position_summary']['positions'])}")

# Clean up when done
trading_manager.close()
```

## Data Models

### PositionInfo
```python
@dataclass
class PositionInfo:
    symbol: str
    quantity: float
    market_value: float
    unrealized_pnl: float
    weight: float
    last_updated: datetime
```

### PortfolioSummary
```python
@dataclass
class PortfolioSummary:
    total_market_value: float
    cash_balance: float
    total_unrealized_pnl: float
    day_change: float
    day_change_percent: float
    positions_count: int
    last_updated: datetime
```

## Type Safety

The entire architecture is fully type-safe with mypy compliance:

```bash
$ python -m mypy the_alchemiser/services/enhanced/ --show-error-codes
Success: no issues found in 6 source files
```

## Error Handling

### Exception Hierarchy
```python
class OrderValidationError(Exception):
    """Raised when order parameters are invalid."""
    pass

class InsufficientFundsError(OrderValidationError):
    """Raised when insufficient buying power for order."""
    pass

class PositionNotFoundError(Exception):
    """Raised when attempting to operate on non-existent position."""
    pass
```

### Consistent Error Responses
All service methods return consistent error responses:
```python
# Success response
{
    "success": True,
    "result": {...},
    "timestamp": "2025-08-08T10:30:00Z"
}

# Error response
{
    "success": False,
    "error": "Detailed error message",
    "error_code": "VALIDATION_FAILED",
    "timestamp": "2025-08-08T10:30:00Z"
}
```

## Migration Guide

### From Direct Alpaca Usage
```python
# Before
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest

client = TradingClient(api_key, secret_key)
order_request = MarketOrderRequest(
    symbol="AAPL",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)
order = client.submit_order(order_request)

# After
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

trading = TradingServiceManager(api_key, secret_key)
result = trading.place_market_order("AAPL", 1.0, "buy")
if result["success"]:
    order_id = result["order_id"]
```

### Gradual Migration Strategy
1. **Start with TradingServiceManager** for new code
2. **Use individual services** for specific functionality
3. **Keep existing code** working during transition
4. **Migrate incrementally** as features are updated

## Testing

### Integration Tests
Run the comprehensive integration test suite:
```bash
python scripts/test_phase3_integration.py
```

Expected output:
```
✅ All imports successful
📋 Running Phase 3 Enhanced Services Integration Tests
📋 Running Import Test... ✅ PASS
📋 Running Service Instantiation... ✅ PASS
📋 Running Interface Compliance... ✅ PASS
📋 Running Type Annotations... ✅ PASS
📊 Test Summary: Passed: 4/4, Success Rate: 100.0%
🎉 All integration tests passed!
```

### Unit Testing Example
```python
import pytest
from unittest.mock import Mock
from the_alchemiser.services.enhanced.order_service import OrderService

def test_order_service_validation():
    # Create mock repository
    mock_trading = Mock()
    mock_trading.place_market_order.return_value = "ORDER123"
    
    # Test service
    order_service = OrderService(mock_trading)
    
    # Test validation
    with pytest.raises(ValueError, match="Quantity must be positive"):
        order_service.place_market_order("AAPL", "buy", -1.0)
    
    # Test successful order
    order_id = order_service.place_market_order("AAPL", "buy", 1.0)
    assert order_id == "ORDER123"
    mock_trading.place_market_order.assert_called_once()
```

## Configuration

### Environment Variables
```bash
# Required
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key

# Optional
ALPACA_PAPER_TRADING=true
ALPACA_MAX_POSITION_WEIGHT=0.10
ALPACA_CACHE_TTL_SECONDS=30
```

### Programmatic Configuration
```python
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

# Basic configuration
trading = TradingServiceManager(
    api_key="your_key",
    secret_key="your_secret",
    paper=True
)

# Advanced service configuration
from the_alchemiser.services.enhanced.position_service import PositionService

position_service = PositionService(
    trading_repo=alpaca_manager,
    market_data_repo=alpaca_manager,
    account_repo=alpaca_manager,
    max_position_weight=0.15  # 15% max position size
)
```

## Performance Considerations

### Caching
- **Market Data**: Automatic caching with configurable TTL
- **Account Data**: Cached for short periods to reduce API calls
- **Position Data**: Real-time with smart refresh logic

### API Rate Limiting
- Built-in respect for Alpaca rate limits
- Automatic retry with exponential backoff
- Batch operations where possible

### Memory Usage
- Efficient data structures for large portfolios
- Lazy loading of historical data
- Configurable cache sizes

## Future Enhancements

### Planned Improvements
1. **Enhanced Testing Infrastructure**
   - Mock repository implementations
   - Test data fixtures
   - Performance benchmarks

2. **Advanced Risk Management**
   - Real-time risk monitoring
   - Position size optimization
   - Portfolio rebalancing

3. **Performance Monitoring**
   - API latency tracking
   - Order execution metrics
   - System health monitoring

4. **Configuration Management**
   - Centralized configuration system
   - Environment-specific settings
   - Runtime configuration updates

## Best Practices

### Service Usage
1. **Use TradingServiceManager** for most operations
2. **Inject dependencies** through interfaces for testing
3. **Handle errors gracefully** with try-catch blocks
4. **Validate inputs** before making API calls
5. **Log operations** for debugging and monitoring

### Code Organization
1. **Keep business logic** in service layer
2. **Use type hints** consistently
3. **Document public interfaces** with docstrings
4. **Follow single responsibility principle**
5. **Test at appropriate levels** (unit, integration, system)

## Conclusion

The Phase 3 enhanced services architecture provides:

- ✅ **Clean separation of concerns** with layered architecture
- ✅ **Type safety** with 100% mypy compliance
- ✅ **Testability** through interface-based design
- ✅ **Extensibility** for future enhancements
- ✅ **Maintainability** with clear patterns and documentation
- ✅ **Production readiness** with comprehensive error handling

This architecture successfully abstracts Alpaca API interactions while providing enhanced functionality, type safety, and maintainability for the trading system.
