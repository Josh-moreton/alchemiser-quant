# Migration Plan: From Facade to Native Individual Services

## 🎯 Overview

This document provides a comprehensive plan to migrate from the `UnifiedDataProviderFacade` to direct usage of individual services. This migration will unlock the full benefits of the refactored architecture including better testability, performance, and maintainability.

## 📊 Current State Analysis

### Files Using UnifiedDataProvider (From Inventory)

**Core Strategy Modules:**
- `the_alchemiser/core/trading/klm_ensemble_engine.py` (Line 444, 446)
- `the_alchemiser/core/trading/klm_trading_bot.py` (Line 27, 131)
- `the_alchemiser/core/trading/strategy_manager.py` (Line 120, 122)
- `the_alchemiser/core/trading/tecl_signals.py` (Line 39)
- `the_alchemiser/core/trading/nuclear_signals.py`
- `the_alchemiser/core/trading/tecl_strategy_engine.py`

**Execution Modules:**
- `the_alchemiser/execution/smart_execution.py` (Line 23, 77)
- `the_alchemiser/execution/trading_engine.py` (Line 172, 174)
- `the_alchemiser/execution/alpaca_client.py` (Line 52, 85)
- `the_alchemiser/execution/account_service.py`
- `the_alchemiser/execution/portfolio_rebalancer.py`

**Main Entry Point:**
- `the_alchemiser/main.py` (Line 108, 113)

**Utility Modules:**
- `the_alchemiser/utils/account_utils.py`
- `the_alchemiser/utils/asset_order_handler.py`
- `the_alchemiser/utils/position_manager.py`
- `the_alchemiser/utils/price_fetching_utils.py`
- `the_alchemiser/utils/smart_pricing_handler.py`
- `the_alchemiser/utils/spread_assessment.py`

**Test Files:**
- `tests/test_unified_data_provider_baseline.py`
- `tests/simulation/test_chaos_engineering.py`

**Alert Services:**
- `the_alchemiser/core/alerts/alert_service.py`

## 🏗️ Migration Strategy Overview

### Phase 1: Infrastructure Setup (Week 1)
- Create service factory pattern
- Implement dependency injection container
- Set up configuration management
- Create migration utilities

### Phase 2: Core Services Migration (Week 2)
- Migrate main.py and strategy_manager.py
- Update trading engines (klm_ensemble_engine, klm_trading_bot)
- Migrate execution modules (trading_engine, smart_execution)

### Phase 3: Utility Services Migration (Week 3)  
- Migrate utility modules
- Update alert services
- Migrate execution support modules

### Phase 4: Testing and Validation (Week 4)
- Update all test files
- Performance validation
- Integration testing
- Documentation updates

## 📋 Detailed Migration Plan

### Phase 1: Infrastructure Setup

#### 1.1 Create Service Factory Pattern

**File**: `/the_alchemiser/core/services/service_factory.py`

```python
"""
Service Factory for creating and managing service instances.

Provides a centralized way to create and configure services with proper
dependency injection and shared resources.
"""

from typing import Any, Optional
from the_alchemiser.core.config import Settings
from the_alchemiser.core.services import (
    ConfigService,
    SecretsService,
    MarketDataClient,
    TradingClientService,
    CacheManager,
)
from the_alchemiser.core.services.account_service import AccountService
from the_alchemiser.core.services.price_service import ModernPriceFetchingService
from the_alchemiser.core.services.error_handling import ErrorHandler


class ServiceFactory:
    """Factory for creating configured service instances."""
    
    def __init__(self, paper_trading: bool = True, config: Settings | None = None):
        self.paper_trading = paper_trading
        self.config_service = ConfigService(config)
        self.secrets_service = SecretsService()
        
        # Get credentials once
        self.api_key, self.secret_key = self.secrets_service.get_alpaca_credentials(paper_trading)
        
        # Shared cache
        self.cache = CacheManager[Any](
            maxsize=1000, 
            default_ttl=self.config_service.cache_duration
        )
        
        # Error handler
        self.error_handler = ErrorHandler()
    
    def create_market_data_client(self) -> MarketDataClient:
        """Create market data client."""
        return MarketDataClient(self.api_key, self.secret_key)
    
    def create_trading_client_service(self) -> TradingClientService:
        """Create trading client service."""
        return TradingClientService(self.api_key, self.secret_key, self.paper_trading)
    
    def create_account_service(self) -> AccountService:
        """Create account service."""
        trading_service = self.create_trading_client_service()
        return AccountService(
            trading_service,
            self.api_key,
            self.secret_key,
            self.config_service.get_endpoint(self.paper_trading)
        )
    
    def create_price_service(self) -> ModernPriceFetchingService:
        """Create modern price fetching service."""
        market_data = self.create_market_data_client()
        return ModernPriceFetchingService(market_data, None, self.cache)
    
    def create_all_services(self) -> dict[str, Any]:
        """Create all services in one call."""
        return {
            'config': self.config_service,
            'secrets': self.secrets_service,
            'market_data': self.create_market_data_client(),
            'trading': self.create_trading_client_service(),
            'account': self.create_account_service(),
            'price': self.create_price_service(),
            'cache': self.cache,
            'error_handler': self.error_handler,
        }
```

#### 1.2 Create Service Container

**File**: `/the_alchemiser/core/services/service_container.py`

```python
"""
Dependency Injection Container for service management.

Provides singleton service instances and handles service lifecycle.
"""

from typing import Any, Dict, Type, TypeVar
from the_alchemiser.core.services.service_factory import ServiceFactory

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for services."""
    
    def __init__(self, paper_trading: bool = True, config: Any = None):
        self._factory = ServiceFactory(paper_trading, config)
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def get_service(self, service_name: str) -> Any:
        """Get a service instance, creating it if necessary."""
        if not self._initialized:
            self._services = self._factory.create_all_services()
            self._initialized = True
        
        if service_name not in self._services:
            raise ValueError(f"Unknown service: {service_name}")
        
        return self._services[service_name]
    
    def get_market_data_client(self):
        """Get market data client."""
        return self.get_service('market_data')
    
    def get_trading_client_service(self):
        """Get trading client service."""
        return self.get_service('trading')
    
    def get_account_service(self):
        """Get account service."""
        return self.get_service('account')
    
    def get_price_service(self):
        """Get price service."""
        return self.get_service('price')
    
    def get_cache_manager(self):
        """Get cache manager."""
        return self.get_service('cache')
    
    def get_config_service(self):
        """Get config service."""
        return self.get_service('config')


# Global container instance
_global_container: ServiceContainer | None = None


def get_service_container(paper_trading: bool = True, config: Any = None) -> ServiceContainer:
    """Get the global service container."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer(paper_trading, config)
    return _global_container


def reset_service_container():
    """Reset the global container (useful for testing)."""
    global _global_container
    _global_container = None
```

#### 1.3 Create Migration Utilities

**File**: `/the_alchemiser/core/services/migration_utils.py`

```python
"""
Migration utilities for converting from facade to services.

Provides helper functions and patterns for migrating existing code.
"""

from typing import Any, Protocol
from the_alchemiser.core.services.service_container import ServiceContainer


class LegacyDataProvider(Protocol):
    """Protocol defining the legacy data provider interface."""
    
    def get_data(self, symbol: str, **kwargs) -> Any: ...
    def get_current_price(self, symbol: str) -> float | None: ...
    def get_account_info(self) -> dict[str, Any]: ...
    def get_positions(self) -> list[dict[str, Any]]: ...
    def get_latest_quote(self, symbol: str) -> tuple[float | None, float | None]: ...


class ServiceAdapter:
    """
    Adapter that converts service calls to match legacy interface.
    
    This helps during migration by providing the same interface while
    using individual services underneath.
    """
    
    def __init__(self, services: ServiceContainer):
        self.services = services
    
    def get_data(self, symbol: str, period: str = "1y", interval: str = "1d", **kwargs) -> Any:
        """Get historical data using market data service."""
        market_data = self.services.get_market_data_client()
        return market_data.get_historical_bars(symbol, period, interval)
    
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price using price service."""
        price_service = self.services.get_price_service()
        # Use async price service with fallback
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(price_service.get_current_price_async(symbol))
        except Exception:
            # Fall back to market data client
            market_data = self.services.get_market_data_client()
            bid, ask = market_data.get_latest_quote(symbol)
            return (bid + ask) / 2 if bid and ask else None
    
    def get_account_info(self) -> dict[str, Any]:
        """Get account info using account service."""
        account_service = self.services.get_account_service()
        account_model = account_service.get_account_info()
        return account_model.to_dict()
    
    def get_positions(self) -> list[dict[str, Any]]:
        """Get positions using account service."""
        account_service = self.services.get_account_service()
        positions = account_service.get_positions()
        return [pos.to_dict() for pos in positions]
    
    def get_latest_quote(self, symbol: str) -> tuple[float | None, float | None]:
        """Get latest quote using market data service."""
        market_data = self.services.get_market_data_client()
        return market_data.get_latest_quote(symbol)


def create_service_adapter(paper_trading: bool = True, config: Any = None) -> ServiceAdapter:
    """Create a service adapter for migration purposes."""
    container = ServiceContainer(paper_trading, config)
    return ServiceAdapter(container)


def migrate_data_provider_usage(
    existing_provider: Any,
    service_container: ServiceContainer,
    preserve_cache: bool = True
) -> ServiceAdapter:
    """
    Migrate from existing data provider to service adapter.
    
    Args:
        existing_provider: The current data provider instance
        service_container: The service container to use
        preserve_cache: Whether to preserve existing cache if possible
    
    Returns:
        ServiceAdapter that can replace the existing provider
    """
    adapter = ServiceAdapter(service_container)
    
    # If preserve_cache is True and existing provider has cache, try to migrate it
    if preserve_cache and hasattr(existing_provider, '_cache'):
        try:
            cache_manager = service_container.get_cache_manager()
            # Migration logic would go here
            # This is a placeholder for cache migration
        except Exception:
            pass  # Ignore cache migration errors
    
    return adapter
```

### Phase 2: Core Services Migration

#### 2.1 Migrate main.py

**Current Pattern in main.py:**
```python
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

shared_data_provider = UnifiedDataProvider(paper_trading=True)
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import get_service_container

# Get service container
services = get_service_container(paper_trading=True)

# Use specific services as needed
market_data = services.get_market_data_client()
account_service = services.get_account_service()
```

#### 2.2 Migrate Strategy Manager

**File**: `the_alchemiser/core/trading/strategy_manager.py`

**Current Pattern:**
```python
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

shared_data_provider = UnifiedDataProvider(paper_trading=True)
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

class MultiStrategyManager:
    def __init__(
        self,
        strategy_allocations: dict[StrategyType, float] | None = None,
        service_container: ServiceContainer | None = None,
        config: Any = None,
    ):
        if service_container is None:
            service_container = ServiceContainer(paper_trading=True, config=config)
        
        self.services = service_container
        
        # Pass services to strategy engines instead of data provider
        self.strategy_engines = {}
        for strategy_type in self.strategy_allocations.keys():
            strategy_class = STRATEGY_REGISTRY[strategy_type]
            # Pass service container to strategies
            self.strategy_engines[strategy_type] = strategy_class(
                services=self.services
            )
```

#### 2.3 Migrate Trading Engines

**For klm_ensemble_engine.py and klm_trading_bot.py:**

**Current Pattern:**
```python
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

class KLMStrategyEnsemble:
    def __init__(self, data_provider: Any = None) -> None:
        if data_provider is None:
            data_provider = UnifiedDataProvider(paper_trading=True)
        self.data_provider = data_provider
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

class KLMStrategyEnsemble:
    def __init__(self, services: ServiceContainer | None = None) -> None:
        if services is None:
            services = ServiceContainer(paper_trading=True)
        
        self.services = services
        self.market_data = services.get_market_data_client()
        self.price_service = services.get_price_service()
        self.cache = services.get_cache_manager()
    
    def get_market_data(self) -> dict[str, pd.DataFrame]:
        """Fetch data for all symbols needed by the ensemble"""
        market_data = {}
        for symbol in self.all_symbols:
            try:
                # Use cache first
                cache_key = f"{symbol}:1y:1d"
                cached_data = self.cache.get(cache_key, "historical_data")
                
                if cached_data is not None:
                    data = cached_data
                else:
                    data = self.market_data.get_historical_bars(symbol, "1y", "1d")
                    if not data.empty:
                        self.cache.set(cache_key, data, "historical_data")
                
                if not data.empty:
                    market_data[symbol] = data
                else:
                    self.logger.warning(f"Empty data for {symbol}")
            except Exception as e:
                self.logger.warning(f"Could not fetch data for {symbol}: {e}")
        
        return market_data
```

#### 2.4 Migrate Execution Modules

**For trading_engine.py:**

**Current Pattern:**
```python
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

self.data_provider = UnifiedDataProvider(paper_trading=self.paper_trading, config=config)
self.trading_client = self.data_provider.trading_client
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

class TradingEngine:
    def __init__(self, paper_trading: bool = True, config: Settings | None = None):
        self.services = ServiceContainer(paper_trading, config)
        
        # Get specific services
        self.market_data = self.services.get_market_data_client()
        self.trading_service = self.services.get_trading_client_service()
        self.account_service = self.services.get_account_service()
        self.price_service = self.services.get_price_service()
        
        # Get raw trading client if needed for legacy compatibility
        self.trading_client = self.trading_service.get_client()
```

### Phase 3: Utility Services Migration

#### 3.1 Migrate Price Fetching Utils

**File**: `the_alchemiser/utils/price_fetching_utils.py`

**Current Pattern:**
```python
def get_price_from_historical_fallback(data_provider: Any, symbol: str) -> float | None:
    df = data_provider.get_data(symbol, period="1d", interval="1m")
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

def get_price_from_historical_fallback(
    services: ServiceContainer, 
    symbol: str
) -> float | None:
    market_data = services.get_market_data_client()
    df = market_data.get_historical_bars(symbol, "1d", "1m")
```

#### 3.2 Migrate Account Utils

**File**: `the_alchemiser/utils/account_utils.py`

**Current Pattern:**
```python
def extract_comprehensive_account_data(data_provider: Any) -> AccountInfo:
    account = data_provider.get_account_info()
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

def extract_comprehensive_account_data(services: ServiceContainer) -> AccountInfo:
    account_service = services.get_account_service()
    account_model = account_service.get_account_info()
    return account_model.to_dict()  # Convert to legacy format if needed
```

#### 3.3 Migrate Alert Services

**File**: `the_alchemiser/core/alerts/alert_service.py`

**Current Pattern:**
```python
def create_alerts_from_signal(
    symbol: str,
    action: str,
    reason: str,
    indicators: dict[str, Any],
    market_data: dict[str, Any],
    data_provider: Any,
    ensure_scalar_price: Any,
    strategy_engine: Any = None,
) -> list[Alert]:
    current_price = data_provider.get_current_price(stock_symbol)
```

**New Pattern:**
```python
from the_alchemiser.core.services.service_container import ServiceContainer

def create_alerts_from_signal(
    symbol: str,
    action: str,
    reason: str,
    indicators: dict[str, Any],
    market_data: dict[str, Any],
    services: ServiceContainer,
    ensure_scalar_price: Any,
    strategy_engine: Any = None,
) -> list[Alert]:
    price_service = services.get_price_service()
    
    # Use async price service for better performance
    import asyncio
    current_price = asyncio.run(price_service.get_current_price_async(stock_symbol))
```

### Phase 4: Testing and Validation

#### 4.1 Update Test Files

**For test_unified_data_provider_baseline.py:**

```python
# Instead of testing the facade, test individual services
from the_alchemiser.core.services import MarketDataClient, TradingClientService
from the_alchemiser.core.services.account_service import AccountService

class TestServicesBaseline:
    def test_market_data_client_initialization(self):
        client = MarketDataClient("test_key", "test_secret")
        assert client.api_key == "test_key"
    
    def test_account_service_integration(self):
        # Test that services work together correctly
        pass
```

#### 4.2 Performance Validation Tests

**File**: `/tests/performance/test_service_performance.py`

```python
"""
Performance tests comparing facade vs native services.
"""

import time
import pytest
from the_alchemiser.core.data.unified_data_provider_facade import UnifiedDataProvider
from the_alchemiser.core.services.service_container import ServiceContainer


class TestServicePerformance:
    
    def test_data_fetching_performance(self):
        """Compare facade vs native service performance."""
        
        # Test facade
        facade = UnifiedDataProvider(paper_trading=True)
        start_time = time.time()
        for _ in range(10):
            facade.get_data("AAPL", "1y", "1d")
        facade_time = time.time() - start_time
        
        # Test native services
        services = ServiceContainer(paper_trading=True)
        market_data = services.get_market_data_client()
        cache = services.get_cache_manager()
        
        start_time = time.time()
        for _ in range(10):
            cache_key = "AAPL:1y:1d"
            cached = cache.get(cache_key, "historical_data")
            if cached is None:
                data = market_data.get_historical_bars("AAPL", "1y", "1d")
                cache.set(cache_key, data, "historical_data")
        native_time = time.time() - start_time
        
        # Native services should be faster due to direct cache access
        assert native_time <= facade_time * 1.1  # Allow 10% margin
```

## 📋 Migration Checklist

### Pre-Migration Setup
- [ ] Create ServiceFactory class
- [ ] Create ServiceContainer class  
- [ ] Create migration utilities and adapters
- [ ] Set up performance benchmarking
- [ ] Create backup branches for rollback

### Phase 1: Core Infrastructure
- [ ] Implement service factory pattern
- [ ] Implement dependency injection container
- [ ] Create migration utilities
- [ ] Test service creation and injection

### Phase 2: Core Services
- [ ] Migrate main.py to use service container
- [ ] Update MultiStrategyManager to use services
- [ ] Migrate KLM strategy engines
- [ ] Migrate TECL strategy engines
- [ ] Update trading engine to use services
- [ ] Migrate execution modules

### Phase 3: Supporting Services  
- [ ] Migrate utility modules (price_fetching_utils, account_utils, etc.)
- [ ] Update alert services
- [ ] Migrate execution support modules (portfolio_rebalancer, etc.)
- [ ] Update remaining strategy modules

### Phase 4: Testing and Validation
- [ ] Update all test files to use services
- [ ] Run performance comparison tests
- [ ] Execute full integration test suite
- [ ] Validate error handling and logging
- [ ] Update documentation

### Post-Migration Cleanup
- [ ] Remove facade usage (optional - can be kept for compatibility)
- [ ] Clean up legacy imports
- [ ] Update type hints and protocols
- [ ] Performance optimization based on metrics
- [ ] Final documentation updates

## 🚀 Expected Benefits After Migration

### Performance Improvements
- **Direct Cache Access**: No facade overhead for cache operations
- **Async Operations**: Full async/await support for price fetching
- **Connection Pooling**: Better resource management for API calls
- **Selective Service Loading**: Only load services actually needed

### Architectural Benefits
- **Better Testability**: Mock individual services instead of entire facade
- **Clearer Dependencies**: Explicit service dependencies in constructors
- **Single Responsibility**: Each service has a focused purpose
- **Easier Maintenance**: Changes isolated to specific services

### Developer Experience
- **Type Safety**: Full type hints for all service methods
- **IDE Support**: Better autocomplete and error detection
- **Debugging**: Clearer call stacks and error traces
- **Extensibility**: Easy to add new services or modify existing ones

## ⚠️ Migration Risks and Mitigation

### Risks
1. **Breaking Changes**: Existing code may break during migration
2. **Performance Regression**: If not done carefully, could be slower
3. **Increased Complexity**: More moving parts to manage
4. **Integration Issues**: Services may not work together correctly

### Mitigation Strategies
1. **Gradual Migration**: Migrate one module at a time
2. **Comprehensive Testing**: Test each migration step thoroughly
3. **Performance Monitoring**: Benchmark before and after each phase
4. **Rollback Plan**: Keep facade available as fallback
5. **Documentation**: Clear migration guides for each pattern

## 📅 Timeline Estimate

**Total Duration**: 4 weeks

- **Week 1**: Infrastructure setup and core framework
- **Week 2**: Core services migration (main.py, strategy managers, trading engines)
- **Week 3**: Utility services and supporting modules
- **Week 4**: Testing, validation, and performance optimization

**Effort**: ~40-60 hours total
- Setup: 10-15 hours
- Core migration: 15-20 hours  
- Supporting migration: 10-15 hours
- Testing and validation: 5-10 hours

## 🎯 Success Criteria

1. **Functionality**: All existing functionality works with native services
2. **Performance**: Equal or better performance compared to facade
3. **Tests**: All tests pass with updated service usage
4. **Documentation**: Complete migration documentation
5. **Type Safety**: Full type coverage for all service interactions
6. **Error Handling**: Proper error handling and logging throughout

This migration plan provides a structured approach to transition from the facade pattern to direct service usage, unlocking the full benefits of the refactored architecture while minimizing risks and maintaining system stability.
