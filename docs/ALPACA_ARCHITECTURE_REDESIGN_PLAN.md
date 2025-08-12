# Alpaca Architecture Redesign Plan

## Current Problems

1. **Scattered Alpaca Interactions**: Multiple files directly import and use Alpaca clients
2. **Circular Dependencies**: Services depend on each other in complex ways
3. **Poor Separation of Concerns**: Trading, data, and account logic mixed together
4. **Duplicate Functionality**: Multiple ways to do the same thing
5. **Type Safety Issues**: Inconsistent typing and error handling
6. **Testing Nightmare**: Hard to mock and test due to tight coupling

## New Architecture Design

### Core Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Injection**: Services depend on abstractions, not concrete implementations
3. **Clear Boundaries**: Strict separation between data, trading, and business logic
4. **Centralized Alpaca Access**: All Alpaca interactions go through dedicated adapters
5. **Type Safety**: Strong typing throughout with proper error handling

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  (Business Logic, Trading Strategies, Order Management) │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                    Service Layer                        │
│     (Orchestration, Workflows, Cross-cutting Concerns)  │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   Domain Layer                          │
│        (Models, Types, Business Rules, Interfaces)     │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                Infrastructure Layer                     │
│    (Alpaca Adapters, Database, Logging, Configuration) │
└─────────────────────────────────────────────────────────┘
```

## New Module Structure

### 1. Infrastructure Layer - Alpaca Adapters

These are the ONLY modules that directly interact with Alpaca APIs:

```
the_alchemiser/infrastructure/alpaca/
├── __init__.py
├── adapters/
│   ├── __init__.py
│   ├── trading_adapter.py       # Trading operations (orders, positions)
│   ├── market_data_adapter.py   # Market data (prices, quotes, history)
│   ├── account_adapter.py       # Account info and portfolio
│   └── streaming_adapter.py     # Real-time data streams
├── clients/
│   ├── __init__.py
│   ├── client_factory.py        # Creates and configures Alpaca clients
│   └── client_config.py         # Client configuration and credentials
└── types/
    ├── __init__.py
    ├── alpaca_types.py          # Alpaca-specific type definitions
    └── converters.py            # Convert Alpaca types to domain types
```

### 2. Domain Layer - Core Interfaces and Types

```
the_alchemiser/domain/
├── interfaces/
│   ├── __init__.py
│   ├── trading_repository.py    # Abstract trading operations
│   ├── market_data_repository.py # Abstract market data operations
│   ├── account_repository.py    # Abstract account operations
│   └── streaming_repository.py  # Abstract streaming operations
├── models/
│   ├── __init__.py
│   ├── account.py              # Account and position models
│   ├── orders.py               # Order models and validation
│   ├── market_data.py          # Price, quote, and bar models
│   └── portfolio.py            # Portfolio and performance models
└── types/
    ├── __init__.py
    ├── trading_types.py        # Trading-related types
    ├── market_types.py         # Market data types
    └── common_types.py         # Shared types across domain
```

### 3. Service Layer - Business Logic Orchestration

```
the_alchemiser/services/
├── __init__.py
├── trading/
│   ├── __init__.py
│   ├── order_service.py        # Order placement and management
│   ├── position_service.py     # Position tracking and validation
│   └── portfolio_service.py    # Portfolio management
├── market_data/
│   ├── __init__.py
│   ├── price_service.py        # Current and historical prices
│   ├── quote_service.py        # Bid/ask quotes
│   └── streaming_service.py    # Real-time data management
├── account/
│   ├── __init__.py
│   ├── account_service.py      # Account information
│   └── balance_service.py      # Buying power and balances
└── shared/
    ├── __init__.py
    ├── cache_service.py        # Caching layer
    ├── validation_service.py   # Cross-cutting validation
    └── error_service.py        # Error handling and recovery
```

### 4. Application Layer - High-Level Operations

```
the_alchemiser/application/
├── __init__.py
├── trading/
│   ├── __init__.py
│   ├── trading_engine.py       # Main trading orchestration
│   ├── order_manager.py        # Order lifecycle management
│   └── risk_manager.py         # Risk validation and limits
├── strategies/
│   ├── __init__.py
│   └── strategy_executor.py    # Strategy execution coordination
├── portfolio/
│   ├── __init__.py
│   ├── portfolio_manager.py    # Portfolio state management
│   └── rebalancer.py          # Portfolio rebalancing
└── workflows/
    ├── __init__.py
    ├── trading_workflow.py     # Complete trading workflows
    └── data_workflow.py        # Data collection workflows
```

## Migration Plan

### Phase 1: Create Infrastructure Adapters (Week 1)

1. **Create Alpaca Adapters**
   - `TradingAdapter`: All order and position operations
   - `MarketDataAdapter`: All price and historical data
   - `AccountAdapter`: All account and portfolio info
   - `StreamingAdapter`: All real-time data streams

2. **Create Client Factory**
   - Centralized client creation and configuration
   - Credential management
   - Connection pooling and retry logic

3. **Create Type Converters**
   - Convert Alpaca types to domain types
   - Handle all type mapping in one place

### Phase 2: Define Domain Interfaces (Week 1)

1. **Create Repository Interfaces**
   - Abstract all external dependencies
   - Define clear contracts for each concern
   - Enable easy testing and mocking

2. **Create Domain Models**
   - Clean, typed domain objects
   - Business logic validation
   - Immutable where appropriate

### Phase 3: Implement Services (Week 2)

1. **Create Service Layer**
   - Implement repository interfaces using adapters
   - Add business logic and orchestration
   - Implement caching and error handling

2. **Dependency Injection Setup**
   - Configure service dependencies
   - Enable easy swapping of implementations
   - Support testing with mocks

### Phase 4: Refactor Application Layer (Week 2)

1. **Update High-Level Operations**
   - Use services instead of direct adapters
   - Simplify complex workflows
   - Add proper error handling

2. **Update Strategy Execution**
   - Use new service interfaces
   - Improve testability
   - Add performance monitoring

### Phase 5: Migration and Cleanup (Week 3)

1. **Update All Imports**
   - Run automated import migration script
   - Update all existing code to use new structure
   - Remove deprecated modules

2. **Testing and Validation**
   - Comprehensive testing of new architecture
   - Performance validation
   - Error handling verification

## Implementation Details

### 1. Trading Adapter Example

```python
# the_alchemiser/infrastructure/alpaca/adapters/trading_adapter.py

from typing import Protocol
from alpaca.trading.client import TradingClient
from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.domain.models.orders import Order, OrderRequest
from the_alchemiser.domain.models.positions import Position

class TradingAdapter(TradingRepository):
    """Alpaca implementation of trading operations."""
    
    def __init__(self, client: TradingClient):
        self._client = client
    
    def place_order(self, order_request: OrderRequest) -> Order:
        """Place an order through Alpaca."""
        # Convert domain types to Alpaca types
        alpaca_request = self._convert_order_request(order_request)
        
        # Execute through Alpaca
        alpaca_order = self._client.submit_order(alpaca_request)
        
        # Convert back to domain types
        return self._convert_alpaca_order(alpaca_order)
    
    def get_positions(self) -> list[Position]:
        """Get all positions from Alpaca."""
        alpaca_positions = self._client.get_all_positions()
        return [self._convert_alpaca_position(pos) for pos in alpaca_positions]
```

### 2. Service Layer Example

```python
# the_alchemiser/services/trading/order_service.py

from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.domain.models.orders import OrderRequest, Order
from the_alchemiser.services.shared.validation_service import ValidationService

class OrderService:
    """Service for order placement and management."""
    
    def __init__(
        self, 
        trading_repo: TradingRepository,
        validation_service: ValidationService
    ):
        self._trading_repo = trading_repo
        self._validation = validation_service
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Order:
        """Place a validated market order."""
        # Create order request
        order_request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type="market"
        )
        
        # Validate order
        self._validation.validate_order(order_request)
        
        # Place order through repository
        return self._trading_repo.place_order(order_request)
```

### 3. Dependency Injection Container

```python
# the_alchemiser/container.py

from dependency_injector import containers, providers
from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter import TradingAdapter
from the_alchemiser.infrastructure.alpaca.clients.client_factory import ClientFactory
from the_alchemiser.services.trading.order_service import OrderService

class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure
    client_factory = providers.Singleton(ClientFactory)
    trading_client = providers.Factory(
        client_factory.provided.create_trading_client,
        config.alpaca.api_key,
        config.alpaca.secret_key
    )
    
    # Adapters
    trading_adapter = providers.Factory(
        TradingAdapter,
        trading_client
    )
    
    # Services
    order_service = providers.Factory(
        OrderService,
        trading_adapter
    )
```

## Import Migration Map

### Current → New Mapping

| Current Module | New Module | Notes |
|----------------|------------|-------|
| `services.account_service` | `services.account.account_service` | Split into account/balance services |
| `services.trading_client_service` | `infrastructure.alpaca.adapters.trading_adapter` | Now an adapter |
| `services.market_data_client` | `infrastructure.alpaca.adapters.market_data_adapter` | Now an adapter |
| `services.price_service` | `services.market_data.price_service` | Moved to market_data subdirectory |
| `application.alpaca_client` | `application.trading.trading_engine` | Renamed and restructured |
| `services.position_manager` | `services.trading.position_service` | Moved to trading subdirectory |
| `infrastructure.data_providers.unified_data_provider_facade` | `application.workflows.data_workflow` | Converted to workflow |

### Import Migration Script

```python
# scripts/migrate_imports.py

import os
import re
from pathlib import Path

IMPORT_MIGRATIONS = {
    'from the_alchemiser.services.account_service': 'from the_alchemiser.services.account.account_service',
    'from the_alchemiser.services.trading_client_service': 'from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter',
    'from the_alchemiser.services.market_data_client': 'from the_alchemiser.infrastructure.alpaca.adapters.market_data_adapter',
    'from the_alchemiser.services.price_service': 'from the_alchemiser.services.market_data.price_service',
    'from the_alchemiser.application.alpaca_client': 'from the_alchemiser.application.trading.trading_engine',
    'from the_alchemiser.services.position_manager': 'from the_alchemiser.services.trading.position_service',
    'from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade': 'from the_alchemiser.application.workflows.data_workflow',
}

def migrate_file_imports(file_path: Path):
    """Migrate imports in a single file."""
    content = file_path.read_text()
    
    for old_import, new_import in IMPORT_MIGRATIONS.items():
        content = content.replace(old_import, new_import)
    
    file_path.write_text(content)

def migrate_all_imports():
    """Migrate imports in all Python files."""
    for file_path in Path('.').rglob('*.py'):
        if 'migration' not in str(file_path):  # Skip migration scripts
            migrate_file_imports(file_path)

if __name__ == '__main__':
    migrate_all_imports()
```

## Benefits of New Architecture

1. **Clear Separation of Concerns**: Each module has a single responsibility
2. **Testability**: Easy to mock and test individual components
3. **Maintainability**: Changes to Alpaca API only affect adapter layer
4. **Extensibility**: Easy to add new brokers or data sources
5. **Type Safety**: Strong typing throughout the stack
6. **Performance**: Centralized caching and connection management
7. **Error Handling**: Consistent error handling patterns
8. **Documentation**: Clear interfaces and contracts

## Next Steps

1. **Approve this plan** and get team alignment
2. **Create detailed implementation tickets** for each phase
3. **Set up development branches** for parallel work
4. **Begin Phase 1** with infrastructure adapters
5. **Run continuous integration** to catch breaking changes
6. **Document the migration** for team knowledge sharing

This redesign will take approximately 3 weeks but will result in a much cleaner, more maintainable codebase that's easier to test, debug, and extend.
