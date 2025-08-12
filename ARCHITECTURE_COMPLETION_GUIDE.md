# Architecture Completion Guide

## Completing the Alpaca Architecture Redesign

### Current Status: 65-70% Complete ✅

The Alchemiser project has made significant progress toward the target architecture, with domain interfaces, enhanced services, and application orchestration largely in place. This guide outlines the remaining 30-35% of work needed to fully achieve the clean, maintainable architecture described in the redesign plan.

---

## 📊 Progress Summary

| Layer | Target | Current Status | Completion |
|-------|--------|----------------|------------|
| **Domain Layer** | Clean interfaces & types | ✅ Complete | 95% |
| **Service Layer** | Business logic orchestration | ✅ Mostly complete | 85% |
| **Application Layer** | High-level workflows | ✅ Complete | 90% |
| **Infrastructure Layer** | Dedicated Alpaca adapters | ⚠️ Partial (AlpacaManager exists) | 50% |
| **Migration & Cleanup** | Remove scattered imports | ❌ Not started | 10% |

---

## Phase 1: Infrastructure Layer Completion

**Timeline: Week 1 (5-7 days)**  
**Priority: HIGH - Foundation for all other improvements**

### 1.1 Create Alpaca Adapter Structure

#### Create Directory Structure

```bash
# Create the infrastructure/alpaca structure
mkdir -p the_alchemiser/infrastructure/alpaca/{adapters,clients,types}
touch the_alchemiser/infrastructure/alpaca/__init__.py
touch the_alchemiser/infrastructure/alpaca/adapters/__init__.py
touch the_alchemiser/infrastructure/alpaca/clients/__init__.py
touch the_alchemiser/infrastructure/alpaca/types/__init__.py
```

#### 1.1.1 Client Factory Implementation

**File: `the_alchemiser/infrastructure/alpaca/clients/client_factory.py`**

```python
"""Centralized Alpaca client creation and configuration."""

import logging
from typing import Optional

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream

from the_alchemiser.infrastructure.config import load_settings

logger = logging.getLogger(__name__)


class AlpacaClientFactory:
    """Factory for creating and configuring Alpaca clients."""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._trading_client: Optional[TradingClient] = None
        self._data_client: Optional[StockHistoricalDataClient] = None
        
    def get_trading_client(self) -> TradingClient:
        """Get or create trading client (singleton pattern)."""
        if self._trading_client is None:
            self._trading_client = TradingClient(
                api_key=self._api_key,
                secret_key=self._secret_key,
                paper=self._paper
            )
            logger.info(f"Trading client created - Paper: {self._paper}")
        return self._trading_client
    
    def get_data_client(self) -> StockHistoricalDataClient:
        """Get or create data client (singleton pattern)."""
        if self._data_client is None:
            self._data_client = StockHistoricalDataClient(
                api_key=self._api_key,
                secret_key=self._secret_key
            )
            logger.info("Data client created")
        return self._data_client
    
    def get_trading_stream(self) -> TradingStream:
        """Create new trading stream (always new instance)."""
        return TradingStream(
            api_key=self._api_key,
            secret_key=self._secret_key,
            paper=self._paper
        )
```

#### 1.1.2 Type Converters Implementation  

**File: `the_alchemiser/infrastructure/alpaca/types/converters.py`**

```python
"""Convert between Alpaca types and domain types."""

from typing import Any, Dict
from decimal import Decimal

from alpaca.trading.models import Order as AlpacaOrder
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.models import Account as AlpacaAccount


class AlpacaDomainConverter:
    """Converts Alpaca API types to domain types."""
    
    @staticmethod
    def alpaca_order_to_dict(alpaca_order: AlpacaOrder) -> Dict[str, Any]:
        """Convert Alpaca Order to domain dictionary."""
        return {
            "id": alpaca_order.id,
            "symbol": alpaca_order.symbol,
            "side": alpaca_order.side.value,
            "quantity": float(alpaca_order.qty),
            "order_type": alpaca_order.order_type.value,
            "status": alpaca_order.status.value,
            "filled_qty": float(alpaca_order.filled_qty or 0),
            "filled_avg_price": float(alpaca_order.filled_avg_price or 0),
            "created_at": alpaca_order.created_at,
            "updated_at": alpaca_order.updated_at,
        }
    
    @staticmethod
    def alpaca_position_to_dict(alpaca_position: AlpacaPosition) -> Dict[str, Any]:
        """Convert Alpaca Position to domain dictionary."""
        return {
            "symbol": alpaca_position.symbol,
            "quantity": float(alpaca_position.qty),
            "market_value": float(alpaca_position.market_value),
            "cost_basis": float(alpaca_position.cost_basis),
            "unrealized_pl": float(alpaca_position.unrealized_pl),
            "unrealized_plpc": float(alpaca_position.unrealized_plpc),
            "current_price": float(alpaca_position.current_price or 0),
        }
    
    @staticmethod
    def alpaca_account_to_dict(alpaca_account: AlpacaAccount) -> Dict[str, Any]:
        """Convert Alpaca Account to domain dictionary."""
        return {
            "id": alpaca_account.id,
            "account_number": alpaca_account.account_number,
            "status": alpaca_account.status.value,
            "currency": alpaca_account.currency,
            "buying_power": float(alpaca_account.buying_power),
            "cash": float(alpaca_account.cash),
            "portfolio_value": float(alpaca_account.portfolio_value),
            "equity": float(alpaca_account.equity),
            "last_equity": float(alpaca_account.last_equity),
        }
```

#### 1.1.3 Trading Adapter Implementation

**File: `the_alchemiser/infrastructure/alpaca/adapters/trading_adapter.py`**

```python
"""Alpaca trading operations adapter."""

import logging
from typing import Any, Dict, List, Optional

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest

from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.infrastructure.alpaca.types.converters import AlpacaDomainConverter
from the_alchemiser.services.exceptions import TradingExecutionError

logger = logging.getLogger(__name__)


class AlpacaTradingAdapter(TradingRepository):
    """Alpaca implementation of trading repository interface."""
    
    def __init__(self, trading_client: TradingClient):
        self._client = trading_client
        self._converter = AlpacaDomainConverter()
    
    def get_positions_dict(self) -> Dict[str, float]:
        """Get all current positions as dict."""
        try:
            positions = self._client.get_all_positions()
            return {
                pos.symbol: float(pos.qty) 
                for pos in positions 
                if float(pos.qty) != 0
            }
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise TradingExecutionError(f"Position retrieval failed: {e}") from e
    
    def get_account(self) -> Dict[str, Any] | None:
        """Get account information."""
        try:
            account = self._client.get_account()
            return self._converter.alpaca_account_to_dict(account)
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return None
    
    def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> str | None:
        """Place a market order."""
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            
            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self._client.submit_order(request)
            logger.info(f"Market order placed: {order.id}")
            return order.id
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise TradingExecutionError(f"Order placement failed: {e}") from e
    
    def place_limit_order(
        self, symbol: str, side: str, quantity: float, limit_price: float
    ) -> str | None:
        """Place a limit order."""
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                limit_price=limit_price,
                time_in_force=TimeInForce.DAY
            )
            
            order = self._client.submit_order(request)
            logger.info(f"Limit order placed: {order.id}")
            return order.id
            
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise TradingExecutionError(f"Limit order placement failed: {e}") from e
```

#### 1.1.4 Market Data Adapter Implementation

**File: `the_alchemiser/infrastructure/alpaca/adapters/market_data_adapter.py`**

```python
"""Alpaca market data operations adapter."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.domain.interfaces.market_data_repository import MarketDataRepository
from the_alchemiser.services.exceptions import DataRetrievalError

logger = logging.getLogger(__name__)


class AlpacaMarketDataAdapter(MarketDataRepository):
    """Alpaca implementation of market data repository interface."""
    
    def __init__(self, data_client: StockHistoricalDataClient):
        self._client = data_client
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            response = self._client.get_stock_latest_quote(request)
            
            if symbol in response:
                quote = response[symbol]
                # Use mid-price for current price
                return (float(quote.bid_price) + float(quote.ask_price)) / 2
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
    
    def get_latest_quote(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get latest bid/ask quote for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            response = self._client.get_stock_latest_quote(request)
            
            if symbol in response:
                quote = response[symbol]
                return (float(quote.bid_price), float(quote.ask_price))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None
    
    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical bars for a symbol."""
        try:
            # Default to last 100 days if no start specified
            if start is None:
                start = datetime.now() - timedelta(days=100)
            
            if end is None:
                end = datetime.now()
            
            # Map timeframe string to Alpaca TimeFrame
            tf_map = {
                "1Min": TimeFrame.Minute,
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day,
                "1Week": TimeFrame.Week,
                "1Month": TimeFrame.Month
            }
            
            timeframe_obj = tf_map.get(timeframe, TimeFrame.Day)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_obj,
                start=start,
                end=end,
                limit=limit
            )
            
            response = self._client.get_stock_bars(request)
            
            if symbol in response:
                bars = response[symbol]
                return [
                    {
                        "timestamp": bar.timestamp,
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                    }
                    for bar in bars
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get historical bars for {symbol}: {e}")
            raise DataRetrievalError(f"Historical data retrieval failed: {e}") from e
```

#### 1.1.5 Account Adapter Implementation

**File: `the_alchemiser/infrastructure/alpaca/adapters/account_adapter.py`**

```python
"""Alpaca account operations adapter."""

import logging
from typing import Any, Dict, Optional

from alpaca.trading.client import TradingClient

from the_alchemiser.domain.interfaces.account_repository import AccountRepository
from the_alchemiser.infrastructure.alpaca.types.converters import AlpacaDomainConverter

logger = logging.getLogger(__name__)


class AlpacaAccountAdapter(AccountRepository):
    """Alpaca implementation of account repository interface."""
    
    def __init__(self, trading_client: TradingClient):
        self._client = trading_client
        self._converter = AlpacaDomainConverter()
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive account information."""
        try:
            account = self._client.get_account()
            return self._converter.alpaca_account_to_dict(account)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def get_buying_power(self) -> Optional[float]:
        """Get current buying power."""
        try:
            account = self._client.get_account()
            return float(account.buying_power)
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            return None
    
    def get_portfolio_value(self) -> Optional[float]:
        """Get total portfolio value."""
        try:
            account = self._client.get_account()
            return float(account.portfolio_value)
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            return None
    
    def get_cash_balance(self) -> Optional[float]:
        """Get available cash balance."""
        try:
            account = self._client.get_account()
            return float(account.cash)
        except Exception as e:
            logger.error(f"Failed to get cash balance: {e}")
            return None
```

---

## Phase 2: Service Layer Reorganization

**Timeline: Week 2 (3-5 days)**  
**Priority: MEDIUM - Improves organization and maintainability**

### 2.1 Restructure Services Directory

#### Create New Service Structure

```bash
# Create service subdirectories
mkdir -p the_alchemiser/services/trading
mkdir -p the_alchemiser/services/market_data  
mkdir -p the_alchemiser/services/account
mkdir -p the_alchemiser/services/shared

# Create __init__.py files
touch the_alchemiser/services/trading/__init__.py
touch the_alchemiser/services/market_data/__init__.py
touch the_alchemiser/services/account/__init__.py
touch the_alchemiser/services/shared/__init__.py
```

#### 2.1.1 Move Enhanced Services to Proper Structure

**Move Files:**

```bash
# Trading services
mv the_alchemiser/services/enhanced/order_service.py the_alchemiser/services/trading/
mv the_alchemiser/services/enhanced/position_service.py the_alchemiser/services/trading/

# Market data services  
mv the_alchemiser/services/enhanced/market_data_service.py the_alchemiser/services/market_data/
mv the_alchemiser/services/price_service.py the_alchemiser/services/market_data/

# Account services
mv the_alchemiser/services/enhanced/account_service.py the_alchemiser/services/account/
mv the_alchemiser/services/account_service.py the_alchemiser/services/account/legacy_account_service.py

# Shared services
mv the_alchemiser/services/cache_manager.py the_alchemiser/services/shared/
mv the_alchemiser/services/error_handler.py the_alchemiser/services/shared/
mv the_alchemiser/services/retry_decorator.py the_alchemiser/services/shared/
```

#### 2.1.2 Update Enhanced Service Manager

**File: `the_alchemiser/services/enhanced/trading_service_manager.py`**

Update imports to use new structure:

```python
# Update these imports:
from the_alchemiser.services.trading.account_service import AccountService
from the_alchemiser.services.market_data.market_data_service import MarketDataService  
from the_alchemiser.services.trading.order_service import OrderService
from the_alchemiser.services.trading.position_service import PositionService
```

#### 2.1.3 Create Service Registry

**File: `the_alchemiser/services/service_registry.py`**

```python
"""Service registry for centralized service management."""

from typing import Dict, Any, Optional
import logging

from the_alchemiser.infrastructure.alpaca.clients.client_factory import AlpacaClientFactory
from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter import AlpacaTradingAdapter
from the_alchemiser.infrastructure.alpaca.adapters.market_data_adapter import AlpacaMarketDataAdapter
from the_alchemiser.infrastructure.alpaca.adapters.account_adapter import AlpacaAccountAdapter
from the_alchemiser.services.trading.order_service import OrderService
from the_alchemiser.services.trading.position_service import PositionService
from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.account.account_service import AccountService

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for managing service instances and dependencies."""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all services and dependencies."""
        if self._initialized:
            return
        
        # Create client factory
        client_factory = AlpacaClientFactory(
            self._api_key, self._secret_key, self._paper
        )
        
        # Create adapters
        trading_adapter = AlpacaTradingAdapter(client_factory.get_trading_client())
        market_data_adapter = AlpacaMarketDataAdapter(client_factory.get_data_client())
        account_adapter = AlpacaAccountAdapter(client_factory.get_trading_client())
        
        # Create services
        self._services['orders'] = OrderService(trading_adapter)
        self._services['positions'] = PositionService(trading_adapter)
        self._services['market_data'] = MarketDataService(market_data_adapter)
        self._services['account'] = AccountService(account_adapter)
        
        self._initialized = True
        logger.info("Service registry initialized")
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        if not self._initialized:
            self.initialize()
        
        service = self._services.get(service_name)
        if service is None:
            raise ValueError(f"Service '{service_name}' not found in registry")
        
        return service
    
    @property
    def orders(self) -> OrderService:
        """Get order service."""
        return self.get_service('orders')
    
    @property
    def positions(self) -> PositionService:
        """Get position service."""
        return self.get_service('positions')
    
    @property
    def market_data(self) -> MarketDataService:
        """Get market data service."""
        return self.get_service('market_data')
    
    @property
    def account(self) -> AccountService:
        """Get account service."""
        return self.get_service('account')
```

---

## Phase 3: Application Layer Updates

**Timeline: Week 2 (2-3 days)**  
**Priority: MEDIUM - Modernize high-level orchestration**

### 3.1 Update Application Layer to Use Service Registry

#### 3.1.1 Create Application Subdirectories

```bash
mkdir -p the_alchemiser/application/trading
mkdir -p the_alchemiser/application/strategies  
mkdir -p the_alchemiser/application/portfolio
mkdir -p the_alchemiser/application/workflows

touch the_alchemiser/application/trading/__init__.py
touch the_alchemiser/application/strategies/__init__.py
touch the_alchemiser/application/portfolio/__init__.py
touch the_alchemiser/application/workflows/__init__.py
```

#### 3.1.2 Move and Update Trading Engine

**Move:** `the_alchemiser/application/trading_engine.py` → `the_alchemiser/application/trading/trading_engine.py`

**Update to use Service Registry:**

```python
# Replace AlpacaManager usage with ServiceRegistry
from the_alchemiser.services.service_registry import ServiceRegistry

class TradingEngine:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.services = ServiceRegistry(api_key, secret_key, paper)
        self.services.initialize()
        
        # Use services instead of direct AlpacaManager
        self.orders = self.services.orders
        self.positions = self.services.positions
        self.market_data = self.services.market_data
        self.account = self.services.account
```

#### 3.1.3 Create Trading Workflow

**File: `the_alchemiser/application/workflows/trading_workflow.py`**

```python
"""Complete trading workflow orchestration."""

import logging
from typing import Dict, Any, List

from the_alchemiser.services.service_registry import ServiceRegistry
from the_alchemiser.domain.strategies.strategy_manager import MultiStrategyManager
from the_alchemiser.application.portfolio_rebalancer.portfolio_rebalancer import PortfolioRebalancer

logger = logging.getLogger(__name__)


class TradingWorkflow:
    """Orchestrates complete trading workflows."""
    
    def __init__(self, services: ServiceRegistry):
        self.services = services
        self.strategy_manager = MultiStrategyManager()
        self.rebalancer = PortfolioRebalancer()
    
    def execute_daily_trading(self) -> Dict[str, Any]:
        """Execute complete daily trading workflow."""
        try:
            # 1. Get current portfolio state
            positions = self.services.positions.get_all_positions()
            account_info = self.services.account.get_account_info()
            
            # 2. Generate strategy signals
            signals = self.strategy_manager.generate_combined_signals()
            
            # 3. Calculate target allocations
            target_allocations = self.rebalancer.calculate_target_allocations(
                signals, account_info['portfolio_value']
            )
            
            # 4. Execute rebalancing trades
            trades = self.rebalancer.execute_rebalancing_trades(
                target_allocations, positions
            )
            
            return {
                "success": True,
                "signals": signals,
                "target_allocations": target_allocations,
                "trades_executed": trades,
                "portfolio_value": account_info['portfolio_value']
            }
            
        except Exception as e:
            logger.error(f"Trading workflow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "trades_executed": []
            }
```

---

## Phase 4: Migration and Cleanup

**Timeline: Week 3 (5-7 days)**  
**Priority: HIGH - Critical for achieving target architecture**

### 4.1 Import Migration Script

#### 4.1.1 Create Comprehensive Migration Script

**File: `scripts/complete_import_migration.py`**

```python
#!/usr/bin/env python3
"""Complete import migration script for architecture cleanup."""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Complete mapping of old imports to new imports
IMPORT_MIGRATIONS = {
    # Service reorganization
    'from the_alchemiser.services.enhanced.order_service': 'from the_alchemiser.services.trading.order_service',
    'from the_alchemiser.services.enhanced.position_service': 'from the_alchemiser.services.trading.position_service',
    'from the_alchemiser.services.enhanced.market_data_service': 'from the_alchemiser.services.market_data.market_data_service',
    'from the_alchemiser.services.enhanced.account_service': 'from the_alchemiser.services.account.account_service',
    
    # Legacy service updates
    'from the_alchemiser.services.account_service': 'from the_alchemiser.services.account.legacy_account_service',
    'from the_alchemiser.services.price_service': 'from the_alchemiser.services.market_data.price_service',
    'from the_alchemiser.services.cache_manager': 'from the_alchemiser.services.shared.cache_manager',
    'from the_alchemiser.services.error_handler': 'from the_alchemiser.services.shared.error_handler',
    
    # Application layer updates
    'from the_alchemiser.application.trading_engine': 'from the_alchemiser.application.trading.trading_engine',
    
    # Direct Alpaca imports to adapter imports
    'from alpaca.trading.enums import OrderSide': 'from the_alchemiser.infrastructure.alpaca.types.alpaca_types import OrderSide',
    'from alpaca.trading.requests import MarketOrderRequest': 'from the_alchemiser.infrastructure.alpaca.types.alpaca_types import MarketOrderRequest',
    'from alpaca.trading.requests import LimitOrderRequest': 'from the_alchemiser.infrastructure.alpaca.types.alpaca_types import LimitOrderRequest',
}

# Files that should use ServiceRegistry instead of AlpacaManager
SERVICE_REGISTRY_CANDIDATES = [
    'the_alchemiser/application/',
    'the_alchemiser/interface/',
    'the_alchemiser/main.py',
    'the_alchemiser/lambda_handler.py',
]


def find_files_needing_migration() -> List[Path]:
    """Find all Python files that need import migration."""
    python_files = []
    
    for file_path in Path('.').rglob('*.py'):
        # Skip test files, migration scripts, and __pycache__
        if any(skip in str(file_path) for skip in ['test_', '__pycache__', 'migration', 'scripts/']):
            continue
            
        python_files.append(file_path)
    
    return python_files


def migrate_file_imports(file_path: Path) -> Tuple[bool, List[str]]:
    """Migrate imports in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        changes = []
        
        # Apply import migrations
        for old_import, new_import in IMPORT_MIGRATIONS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  {old_import} → {new_import}")
        
        # Special handling for ServiceRegistry migration
        if any(candidate in str(file_path) for candidate in SERVICE_REGISTRY_CANDIDATES):
            if 'from the_alchemiser.services.alpaca_manager import AlpacaManager' in content:
                content = content.replace(
                    'from the_alchemiser.services.alpaca_manager import AlpacaManager',
                    'from the_alchemiser.services.service_registry import ServiceRegistry'
                )
                changes.append("  AlpacaManager → ServiceRegistry")
        
        # Write changes if any were made
        if content != original_content:
            file_path.write_text(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"Error migrating {file_path}: {e}")
        return False, [f"Error: {e}"]


def analyze_remaining_alpaca_imports() -> Dict[str, List[str]]:
    """Analyze remaining direct Alpaca imports that need manual attention."""
    remaining_imports = {}
    
    for file_path in find_files_needing_migration():
        try:
            content = file_path.read_text()
            alpaca_imports = []
            
            for line_num, line in enumerate(content.split('\n'), 1):
                if re.search(r'from alpaca\.|import alpaca', line):
                    alpaca_imports.append(f"Line {line_num}: {line.strip()}")
            
            if alpaca_imports:
                remaining_imports[str(file_path)] = alpaca_imports
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    return remaining_imports


def main():
    """Run complete import migration."""
    print("🚀 Starting complete import migration...")
    
    # Find files needing migration
    files_to_migrate = find_files_needing_migration()
    print(f"Found {len(files_to_migrate)} Python files to check")
    
    # Migrate imports
    migrated_count = 0
    total_changes = 0
    
    for file_path in files_to_migrate:
        was_migrated, changes = migrate_file_imports(file_path)
        
        if was_migrated:
            migrated_count += 1
            total_changes += len(changes)
            print(f"✅ {file_path}")
            for change in changes:
                print(change)
    
    print(f"\n📊 Migration Summary:")
    print(f"  Files migrated: {migrated_count}")
    print(f"  Total changes: {total_changes}")
    
    # Analyze remaining Alpaca imports
    print(f"\n🔍 Analyzing remaining direct Alpaca imports...")
    remaining = analyze_remaining_alpaca_imports()
    
    if remaining:
        print(f"⚠️  Found {len(remaining)} files with remaining Alpaca imports:")
        for file_path, imports in remaining.items():
            print(f"\n{file_path}:")
            for imp in imports:
                print(f"  {imp}")
    else:
        print("✅ No remaining direct Alpaca imports found!")
    
    print(f"\n🎉 Import migration complete!")


if __name__ == '__main__':
    main()
```

#### 4.1.2 Create Service Usage Migration Script

**File: `scripts/migrate_to_service_registry.py`**

```python
#!/usr/bin/env python3
"""Migrate AlpacaManager usage to ServiceRegistry pattern."""

import re
from pathlib import Path
from typing import List, Tuple


def migrate_alpaca_manager_usage(file_path: Path) -> Tuple[bool, List[str]]:
    """Convert AlpacaManager usage to ServiceRegistry pattern."""
    try:
        content = file_path.read_text()
        original_content = content
        changes = []
        
        # Replace AlpacaManager initialization
        manager_init_pattern = r'(\w+)\s*=\s*AlpacaManager\([^)]+\)'
        if re.search(manager_init_pattern, content):
            content = re.sub(
                manager_init_pattern,
                r'\1 = ServiceRegistry(api_key, secret_key, paper)',
                content
            )
            changes.append("Updated AlpacaManager initialization to ServiceRegistry")
        
        # Replace direct trading_client usage
        if '.trading_client.' in content:
            content = content.replace('.trading_client.', '.orders.')
            changes.append("Replaced .trading_client with .orders service")
        
        # Replace direct data_client usage  
        if '.data_client.' in content:
            content = content.replace('.data_client.', '.market_data.')
            changes.append("Replaced .data_client with .market_data service")
        
        # Replace common method calls
        method_replacements = {
            '.get_positions_dict()': '.positions.get_all_positions()',
            '.get_account()': '.account.get_account_info()',
            '.get_buying_power()': '.account.get_buying_power()',
            '.place_market_order(': '.orders.place_market_order(',
            '.place_limit_order(': '.orders.place_limit_order(',
        }
        
        for old_method, new_method in method_replacements.items():
            if old_method in content:
                content = content.replace(old_method, new_method)
                changes.append(f"Replaced {old_method} with {new_method}")
        
        # Write changes if any were made
        if content != original_content:
            file_path.write_text(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"Error migrating {file_path}: {e}")
        return False, [f"Error: {e}"]


def main():
    """Run AlpacaManager to ServiceRegistry migration."""
    print("🔄 Migrating AlpacaManager usage to ServiceRegistry...")
    
    # Target files that likely use AlpacaManager
    target_patterns = [
        'the_alchemiser/application/**/*.py',
        'the_alchemiser/interface/**/*.py',
        'the_alchemiser/main.py',
        'the_alchemiser/lambda_handler.py',
    ]
    
    files_to_migrate = []
    for pattern in target_patterns:
        files_to_migrate.extend(Path('.').glob(pattern))
    
    migrated_count = 0
    total_changes = 0
    
    for file_path in files_to_migrate:
        if file_path.is_file():
            was_migrated, changes = migrate_alpaca_manager_usage(file_path)
            
            if was_migrated:
                migrated_count += 1
                total_changes += len(changes)
                print(f"✅ {file_path}")
                for change in changes:
                    print(f"  {change}")
    
    print(f"\n📊 ServiceRegistry Migration Summary:")
    print(f"  Files migrated: {migrated_count}")
    print(f"  Total changes: {total_changes}")
    print(f"\n🎉 ServiceRegistry migration complete!")


if __name__ == '__main__':
    main()
```

### 4.2 Cleanup Legacy Files

#### 4.2.1 Remove Deprecated Files

```bash
# Remove enhanced services directory (moved to proper structure)
rm -rf the_alchemiser/services/enhanced/

# Remove legacy service files that have been reorganized
rm the_alchemiser/services/trading_client_service.py
rm the_alchemiser/services/market_data_client.py

# Remove old application files that have been moved
rm the_alchemiser/application/alpaca_client.py  # if exists
```

#### 4.2.2 Update Package Imports

**File: `the_alchemiser/services/__init__.py`**

```python
"""Services package with reorganized structure."""

# Re-export key services for backward compatibility
from the_alchemiser.services.service_registry import ServiceRegistry
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

# Legacy imports for backward compatibility (deprecated)
from the_alchemiser.services.alpaca_manager import AlpacaManager

__all__ = [
    'ServiceRegistry',
    'TradingServiceManager', 
    'AlpacaManager',  # deprecated
]
```

---

## Phase 5: Testing and Validation

**Timeline: Week 3 (2-3 days)**  
**Priority: HIGH - Ensure migration didn't break functionality**

### 5.1 Create Integration Tests

#### 5.1.1 Service Registry Integration Test

**File: `tests/integration/test_service_registry.py`**

```python
"""Integration tests for ServiceRegistry."""

import pytest
from unittest.mock import Mock

from the_alchemiser.services.service_registry import ServiceRegistry


@pytest.fixture
def mock_service_registry():
    """Create a ServiceRegistry with mocked adapters."""
    registry = ServiceRegistry("test_key", "test_secret", paper=True)
    
    # Mock the adapters to avoid real API calls
    registry._services = {
        'orders': Mock(),
        'positions': Mock(),
        'market_data': Mock(),
        'account': Mock(),
    }
    registry._initialized = True
    
    return registry


def test_service_registry_initialization(mock_service_registry):
    """Test that ServiceRegistry initializes properly."""
    assert mock_service_registry._initialized
    assert 'orders' in mock_service_registry._services
    assert 'positions' in mock_service_registry._services
    assert 'market_data' in mock_service_registry._services
    assert 'account' in mock_service_registry._services


def test_service_registry_property_access(mock_service_registry):
    """Test that service properties work correctly."""
    orders_service = mock_service_registry.orders
    positions_service = mock_service_registry.positions
    market_data_service = mock_service_registry.market_data
    account_service = mock_service_registry.account
    
    assert orders_service is not None
    assert positions_service is not None
    assert market_data_service is not None
    assert account_service is not None


def test_service_registry_get_service(mock_service_registry):
    """Test getting services by name."""
    orders_service = mock_service_registry.get_service('orders')
    assert orders_service is not None
    
    with pytest.raises(ValueError):
        mock_service_registry.get_service('nonexistent_service')
```

#### 5.1.2 Adapter Integration Tests

**File: `tests/integration/test_alpaca_adapters.py`**

```python
"""Integration tests for Alpaca adapters."""

import pytest
from unittest.mock import Mock, MagicMock

from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter import AlpacaTradingAdapter
from the_alchemiser.infrastructure.alpaca.adapters.market_data_adapter import AlpacaMarketDataAdapter
from the_alchemiser.infrastructure.alpaca.adapters.account_adapter import AlpacaAccountAdapter


@pytest.fixture
def mock_trading_client():
    """Create a mock trading client."""
    client = Mock()
    
    # Mock account response
    mock_account = Mock()
    mock_account.id = "test-account"
    mock_account.buying_power = 10000.0
    mock_account.cash = 5000.0
    mock_account.portfolio_value = 15000.0
    client.get_account.return_value = mock_account
    
    # Mock positions response
    mock_position = Mock()
    mock_position.symbol = "AAPL"
    mock_position.qty = 10.0
    client.get_all_positions.return_value = [mock_position]
    
    return client


@pytest.fixture
def mock_data_client():
    """Create a mock data client."""
    client = Mock()
    
    # Mock quote response
    mock_quote = Mock()
    mock_quote.bid_price = 100.0
    mock_quote.ask_price = 100.5
    client.get_stock_latest_quote.return_value = {"AAPL": mock_quote}
    
    return client


def test_trading_adapter_get_positions_dict(mock_trading_client):
    """Test trading adapter position retrieval."""
    adapter = AlpacaTradingAdapter(mock_trading_client)
    positions = adapter.get_positions_dict()
    
    assert "AAPL" in positions
    assert positions["AAPL"] == 10.0


def test_trading_adapter_get_account(mock_trading_client):
    """Test trading adapter account retrieval."""
    adapter = AlpacaTradingAdapter(mock_trading_client)
    account = adapter.get_account()
    
    assert account is not None
    assert account["id"] == "test-account"
    assert account["buying_power"] == 10000.0


def test_market_data_adapter_get_current_price(mock_data_client):
    """Test market data adapter price retrieval."""
    adapter = AlpacaMarketDataAdapter(mock_data_client)
    price = adapter.get_current_price("AAPL")
    
    assert price == 100.25  # Mid-price of bid/ask


def test_account_adapter_get_buying_power(mock_trading_client):
    """Test account adapter buying power retrieval."""
    adapter = AlpacaAccountAdapter(mock_trading_client)
    buying_power = adapter.get_buying_power()
    
    assert buying_power == 10000.0
```

### 5.2 Create Migration Validation Script

#### 5.2.1 Architecture Validation Script

**File: `scripts/validate_architecture.py`**

```python
#!/usr/bin/env python3
"""Validate that the architecture migration is complete and correct."""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set


def find_direct_alpaca_imports() -> Dict[str, List[str]]:
    """Find any remaining direct Alpaca imports."""
    direct_imports = {}
    
    for file_path in Path('the_alchemiser').rglob('*.py'):
        try:
            content = file_path.read_text()
            
            # Skip infrastructure/alpaca directory (allowed to have Alpaca imports)
            if 'infrastructure/alpaca' in str(file_path):
                continue
            
            # Look for direct Alpaca imports
            lines_with_alpaca = []
            for line_num, line in enumerate(content.split('\n'), 1):
                if 'from alpaca.' in line or 'import alpaca' in line:
                    lines_with_alpaca.append(f"Line {line_num}: {line.strip()}")
            
            if lines_with_alpaca:
                direct_imports[str(file_path)] = lines_with_alpaca
                
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
    
    return direct_imports


def validate_adapter_structure() -> List[str]:
    """Validate that adapter structure is properly implemented."""
    issues = []
    
    required_adapters = [
        'the_alchemiser/infrastructure/alpaca/adapters/trading_adapter.py',
        'the_alchemiser/infrastructure/alpaca/adapters/market_data_adapter.py',
        'the_alchemiser/infrastructure/alpaca/adapters/account_adapter.py',
        'the_alchemiser/infrastructure/alpaca/clients/client_factory.py',
        'the_alchemiser/infrastructure/alpaca/types/converters.py',
    ]
    
    for adapter_path in required_adapters:
        if not Path(adapter_path).exists():
            issues.append(f"Missing adapter: {adapter_path}")
    
    return issues


def validate_service_structure() -> List[str]:
    """Validate that service structure is properly organized."""
    issues = []
    
    required_service_dirs = [
        'the_alchemiser/services/trading',
        'the_alchemiser/services/market_data',
        'the_alchemiser/services/account',
        'the_alchemiser/services/shared',
    ]
    
    for service_dir in required_service_dirs:
        if not Path(service_dir).exists():
            issues.append(f"Missing service directory: {service_dir}")
    
    # Check that enhanced services have been moved
    if Path('the_alchemiser/services/enhanced').exists():
        enhanced_files = list(Path('the_alchemiser/services/enhanced').glob('*.py'))
        if enhanced_files:
            issues.append("Enhanced services directory still contains files - should be moved to proper structure")
    
    return issues


def validate_import_structure() -> List[str]:
    """Validate that imports follow the new structure."""
    issues = []
    
    # Check for usage of ServiceRegistry in key files
    key_files = [
        'the_alchemiser/main.py',
        'the_alchemiser/lambda_handler.py',
    ]
    
    for file_path in key_files:
        if Path(file_path).exists():
            try:
                content = Path(file_path).read_text()
                if 'AlpacaManager' in content and 'ServiceRegistry' not in content:
                    issues.append(f"{file_path} still uses AlpacaManager instead of ServiceRegistry")
            except Exception as e:
                issues.append(f"Error checking {file_path}: {e}")
    
    return issues


def main():
    """Run complete architecture validation."""
    print("🔍 Validating architecture migration...")
    
    all_issues = []
    
    # Check for direct Alpaca imports
    print("\n1. Checking for direct Alpaca imports...")
    direct_imports = find_direct_alpaca_imports()
    if direct_imports:
        print(f"❌ Found {len(direct_imports)} files with direct Alpaca imports:")
        for file_path, imports in direct_imports.items():
            print(f"  {file_path}:")
            for imp in imports:
                print(f"    {imp}")
        all_issues.extend([f"Direct Alpaca import in {fp}" for fp in direct_imports.keys()])
    else:
        print("✅ No direct Alpaca imports found outside infrastructure layer")
    
    # Check adapter structure
    print("\n2. Validating adapter structure...")
    adapter_issues = validate_adapter_structure()
    if adapter_issues:
        print("❌ Adapter structure issues:")
        for issue in adapter_issues:
            print(f"  {issue}")
        all_issues.extend(adapter_issues)
    else:
        print("✅ Adapter structure is complete")
    
    # Check service structure
    print("\n3. Validating service structure...")
    service_issues = validate_service_structure()
    if service_issues:
        print("❌ Service structure issues:")
        for issue in service_issues:
            print(f"  {issue}")
        all_issues.extend(service_issues)
    else:
        print("✅ Service structure is properly organized")
    
    # Check import structure
    print("\n4. Validating import structure...")
    import_issues = validate_import_structure()
    if import_issues:
        print("❌ Import structure issues:")
        for issue in import_issues:
            print(f"  {issue}")
        all_issues.extend(import_issues)
    else:
        print("✅ Import structure follows new architecture")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    if all_issues:
        print(f"❌ Found {len(all_issues)} issues that need to be addressed")
        print("\nRemaining work:")
        for issue in all_issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("✅ Architecture migration is complete and valid!")
        print("🎉 The target architecture has been successfully achieved!")


if __name__ == '__main__':
    main()
```

---

## Phase 6: Documentation and Final Cleanup

**Timeline: Week 3 (1-2 days)**  
**Priority: LOW - Polish and documentation**

### 6.1 Update Documentation

#### 6.1.1 Create Architecture Documentation

**File: `docs/ARCHITECTURE.md`**

```markdown
# The Alchemiser Architecture

## Overview
The Alchemiser follows a clean layered architecture with Domain-Driven Design (DDD) principles.

## Architecture Layers

### Infrastructure Layer
- **Alpaca Adapters**: `infrastructure/alpaca/adapters/`
  - `TradingAdapter`: Order placement and position management
  - `MarketDataAdapter`: Price data and historical information
  - `AccountAdapter`: Account information and balances
- **Client Factory**: `infrastructure/alpaca/clients/client_factory.py`
- **Type Converters**: `infrastructure/alpaca/types/converters.py`

### Domain Layer  
- **Interfaces**: `domain/interfaces/`
  - Repository protocols for all external dependencies
- **Models**: `domain/models/`
  - Clean domain objects for business logic
- **Types**: `domain/types.py`
  - Shared type definitions

### Service Layer
- **Trading Services**: `services/trading/`
- **Market Data Services**: `services/market_data/`
- **Account Services**: `services/account/`
- **Shared Services**: `services/shared/`
- **Service Registry**: Central service management

### Application Layer
- **Trading Workflows**: `application/trading/`
- **Strategy Execution**: `application/strategies/`  
- **Portfolio Management**: `application/portfolio/`

## Usage

### Basic Service Usage
```python
from the_alchemiser.services.service_registry import ServiceRegistry

# Initialize services
services = ServiceRegistry(api_key, secret_key, paper=True)

# Use services
positions = services.positions.get_all_positions()
account_info = services.account.get_account_info()
order_id = services.orders.place_market_order("AAPL", "buy", 10)
```

### Trading Workflow Usage

```python
from the_alchemiser.application.workflows.trading_workflow import TradingWorkflow

workflow = TradingWorkflow(services)
result = workflow.execute_daily_trading()
```

```

#### 6.1.2 Update README with New Architecture
Update the main README.md to reflect the new architecture and usage patterns.

---

## 🎯 Summary and Next Actions

### Current Architecture Completion: 65-70% ✅

### Remaining Work Breakdown:

| Phase | Work Required | Time Estimate | Priority |
|-------|---------------|---------------|----------|
| **Phase 1: Infrastructure** | Create Alpaca adapters, client factory, type converters | 5-7 days | HIGH |
| **Phase 2: Service Reorganization** | Move services to proper directories, create service registry | 3-5 days | MEDIUM |
| **Phase 3: Application Updates** | Update trading engine and create workflows | 2-3 days | MEDIUM |
| **Phase 4: Migration & Cleanup** | Import migration, remove legacy files | 5-7 days | HIGH |
| **Phase 5: Testing** | Integration tests and validation | 2-3 days | HIGH |
| **Phase 6: Documentation** | Update docs and architecture guide | 1-2 days | LOW |

### **Total Estimated Time: 18-27 days (3.5-5.5 weeks)**

### Critical Success Factors:
1. **Start with Phase 1** - Infrastructure adapters are the foundation
2. **Run migration scripts carefully** - Test each phase before proceeding  
3. **Maintain backward compatibility** - Keep old imports working during transition
4. **Validate at each step** - Use provided validation scripts
5. **Update tests** - Ensure all tests pass after each phase

### Expected Benefits After Completion:
- ✅ **100% separation of concerns** - Each layer has single responsibility
- ✅ **Easy testing** - All external dependencies mocked through interfaces
- ✅ **Maintainable codebase** - Changes isolated to appropriate layers
- ✅ **Extensible architecture** - Easy to add new brokers or data sources
- ✅ **Type safety** - Strong typing throughout the stack
- ✅ **Clean imports** - No scattered Alpaca dependencies

The architecture is already 65-70% complete with the core patterns in place. This guide provides a clear path to finish the remaining 30-35% and achieve the target clean architecture.
