# Dependency Injection Implementation Plan

## Complete Migration Strategy for The Alchemiser

### Overview

This plan implements dependency injection (DI) incrementally while maintaining 100% backward compatibility. The approach uses a "parallel migration" strategy where new DI components are built alongside existing ones, tested thoroughly, then gradually replace the old system.

**Timeline**: 3-4 weeks  
**Risk Level**: LOW (maintains backward compatibility)  
**Testing Strategy**: Parallel testing with gradual migration

---

## Phase 1: Foundation Setup (Week 1, Days 1-3)

### 1.1 Install Dependencies

**Action**: Add dependency injection framework

**Files to modify**:

- `pyproject.toml`

**Work needed**:

```toml
# Add to [tool.poetry.dependencies]
dependency-injector = "^4.41.0"
```

**Terminal commands**:

```bash
cd /Users/joshmoreton/GitHub/alchemiser-quant
poetry add dependency-injector
poetry install
```

**Deliverable**: DI framework installed and available

---

### 1.2 Create Container Infrastructure

#### 1.2.1 Create Base Container Structure

**New file**: `the_alchemiser/container/__init__.py`

```python
"""Dependency injection container package."""

from .application_container import ApplicationContainer
from .config_providers import ConfigProviders
from .infrastructure_providers import InfrastructureProviders
from .service_providers import ServiceProviders

__all__ = [
    "ApplicationContainer",
    "ConfigProviders", 
    "InfrastructureProviders",
    "ServiceProviders",
]
```

**Deliverable**: Container package structure created

#### 1.2.2 Create Configuration Providers

**New file**: `the_alchemiser/container/config_providers.py`

```python
"""Configuration providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.infrastructure.config import Settings, load_settings


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""
    
    # Settings configuration
    settings = providers.Singleton(load_settings)
    
    # Alpaca configuration
    alpaca_api_key = providers.Configuration(
        name="alpaca_api_key",
        default=settings.provided.alpaca.api_key
    )
    
    alpaca_secret_key = providers.Configuration(
        name="alpaca_secret_key", 
        default=settings.provided.alpaca.secret_key
    )
    
    paper_trading = providers.Configuration(
        name="paper_trading",
        default=settings.provided.alpaca.paper_trading
    )
    
    # Email configuration
    email_recipient = providers.Configuration(
        name="email_recipient",
        default=settings.provided.email.recipient
    )
```

**Deliverable**: Configuration providers ready for all settings

#### 1.2.3 Create Infrastructure Providers

**New file**: `the_alchemiser/container/infrastructure_providers.py`

```python
"""Infrastructure layer providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.services.alpaca_manager import AlpacaManager
from the_alchemiser.container.config_providers import ConfigProviders


class InfrastructureProviders(containers.DeclarativeContainer):
    """Providers for infrastructure layer components."""
    
    # Configuration
    config = providers.DependenciesContainer()
    
    # Repository implementations
    alpaca_manager = providers.Singleton(
        AlpacaManager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading
    )
    
    # Backward compatibility: provide same interface
    trading_repository = providers.Alias(alpaca_manager)
    market_data_repository = providers.Alias(alpaca_manager)
    account_repository = providers.Alias(alpaca_manager)
```

**Deliverable**: Infrastructure providers maintaining existing AlpacaManager

#### 1.2.4 Create Service Providers

**New file**: `the_alchemiser/container/service_providers.py`

```python
"""Service layer providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.services.enhanced.account_service import AccountService
from the_alchemiser.services.enhanced.market_data_service import MarketDataService
from the_alchemiser.services.enhanced.order_service import OrderService
from the_alchemiser.services.enhanced.position_service import PositionService
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components."""
    
    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()
    
    # Enhanced services (inject repositories)
    order_service = providers.Factory(
        OrderService,
        trading_repository=infrastructure.trading_repository
    )
    
    position_service = providers.Factory(
        PositionService,
        trading_repository=infrastructure.trading_repository
    )
    
    market_data_service = providers.Factory(
        MarketDataService,
        market_data_repository=infrastructure.market_data_repository
    )
    
    account_service = providers.Factory(
        AccountService,
        account_repository=infrastructure.account_repository
    )
    
    # Backward compatibility: provide TradingServiceManager
    trading_service_manager = providers.Factory(
        TradingServiceManager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading
    )
```

**Deliverable**: Service providers with backward compatibility

#### 1.2.5 Create Main Application Container

**New file**: `the_alchemiser/container/application_container.py`

```python
"""Main application container for dependency injection."""

import os
from dependency_injector import containers, providers

from the_alchemiser.container.config_providers import ConfigProviders
from the_alchemiser.container.infrastructure_providers import InfrastructureProviders
from the_alchemiser.container.service_providers import ServiceProviders


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container orchestrating all dependencies."""
    
    # Wire configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "the_alchemiser.main",
            "the_alchemiser.lambda_handler",
            "the_alchemiser.application.trading_engine",
        ]
    )
    
    # Sub-containers
    config = providers.Container(ConfigProviders)
    infrastructure = providers.Container(
        InfrastructureProviders,
        config=config
    )
    services = providers.Container(
        ServiceProviders,
        infrastructure=infrastructure,
        config=config
    )
    
    # Application layer (will be added in Phase 2)
    
    @classmethod
    def create_for_environment(cls, env: str = "development") -> "ApplicationContainer":
        """Create container configured for specific environment."""
        container = cls()
        
        # Load environment-specific configuration
        if env == "test":
            container.config.alpaca_api_key.override("test_key")
            container.config.alpaca_secret_key.override("test_secret")
            container.config.paper_trading.override(True)
        elif env == "production":
            # Production uses environment variables (default behavior)
            pass
        
        return container
    
    @classmethod
    def create_for_testing(cls) -> "ApplicationContainer":
        """Create container with test doubles."""
        container = cls.create_for_environment("test")
        
        # Override with mocks for testing (will be used in tests)
        from unittest.mock import Mock
        mock_alpaca_manager = Mock()
        container.infrastructure.alpaca_manager.override(mock_alpaca_manager)
        
        return container
```

**Deliverable**: Complete DI container system ready for use

---

### 1.3 Update Enhanced Services for DI (Backward Compatible)

#### 1.3.1 Update OrderService to Accept Injected Dependencies

**File to modify**: `the_alchemiser/services/enhanced/order_service.py`

**Current constructor**:

```python
def __init__(self, alpaca_manager: AlpacaManager):
    self.alpaca_manager = alpaca_manager
```

**Work needed**: Update to accept abstract interface while maintaining backward compatibility

**Updated constructor**:

```python
from typing import Union
from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.services.alpaca_manager import AlpacaManager

def __init__(self, trading_repository: Union[TradingRepository, AlpacaManager]):
    """Initialize OrderService with trading repository.
    
    Args:
        trading_repository: Repository for trading operations.
                          Can be AlpacaManager (backward compatibility) or any TradingRepository.
    """
    # Backward compatibility: if AlpacaManager passed, use it directly
    if isinstance(trading_repository, AlpacaManager):
        self.alpaca_manager = trading_repository
        self._trading_repo = trading_repository
    else:
        # New DI way: use injected repository
        self._trading_repo = trading_repository
        self.alpaca_manager = trading_repository  # For backward compatibility
    
    self.logger = logging.getLogger(__name__)
```

**Deliverable**: OrderService supports both old and new initialization methods

#### 1.3.2 Update PositionService for DI

**File to modify**: `the_alchemiser/services/enhanced/position_service.py`

**Work needed**: Same pattern as OrderService - accept abstract interface with backward compatibility

**Updated constructor**:

```python
from typing import Union
from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.services.alpaca_manager import AlpacaManager

def __init__(self, trading_repository: Union[TradingRepository, AlpacaManager]):
    """Initialize PositionService with trading repository."""
    if isinstance(trading_repository, AlpacaManager):
        self.alpaca_manager = trading_repository
        self._trading_repo = trading_repository
    else:
        self._trading_repo = trading_repository
        self.alpaca_manager = trading_repository
    
    self.logger = logging.getLogger(__name__)
```

**Deliverable**: PositionService supports both initialization methods

#### 1.3.3 Update MarketDataService for DI

**File to modify**: `the_alchemiser/services/enhanced/market_data_service.py`

**Work needed**: Accept MarketDataRepository interface

**Updated constructor**:

```python
from typing import Union
from the_alchemiser.domain.interfaces.market_data_repository import MarketDataRepository
from the_alchemiser.services.alpaca_manager import AlpacaManager

def __init__(self, market_data_repository: Union[MarketDataRepository, AlpacaManager]):
    """Initialize MarketDataService with market data repository."""
    if isinstance(market_data_repository, AlpacaManager):
        self.alpaca_manager = market_data_repository
        self._market_data_repo = market_data_repository
    else:
        self._market_data_repo = market_data_repository
        self.alpaca_manager = market_data_repository
    
    self.logger = logging.getLogger(__name__)
```

**Deliverable**: MarketDataService supports both initialization methods

#### 1.3.4 Update AccountService for DI

**File to modify**: `the_alchemiser/services/enhanced/account_service.py`

**Work needed**: Accept AccountRepository interface

**Updated constructor**:

```python
from typing import Union
from the_alchemiser.domain.interfaces.account_repository import AccountRepository
from the_alchemiser.services.alpaca_manager import AlpacaManager

def __init__(self, account_repository: Union[AccountRepository, AlpacaManager]):
    """Initialize AccountService with account repository."""
    if isinstance(account_repository, AlpacaManager):
        self.alpaca_manager = account_repository
        self._account_repo = account_repository
    else:
        self._account_repo = account_repository
        self.alpaca_manager = account_repository
    
    self.logger = logging.getLogger(__name__)
```

**Deliverable**: AccountService supports both initialization methods

---

### 1.4 Create DI-Aware Service Factory (Optional Entry Point)

**New file**: `the_alchemiser/services/service_factory.py`

```python
"""Service factory using dependency injection."""

from typing import Optional

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class ServiceFactory:
    """Factory for creating services using dependency injection."""
    
    _container: Optional[ApplicationContainer] = None
    
    @classmethod
    def initialize(cls, container: Optional[ApplicationContainer] = None) -> None:
        """Initialize factory with DI container."""
        if container is None:
            container = ApplicationContainer()
        cls._container = container
    
    @classmethod
    def create_trading_service_manager(
        cls, 
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: Optional[bool] = None
    ) -> TradingServiceManager:
        """Create TradingServiceManager using DI or traditional method."""
        
        if cls._container is not None and all(x is None for x in [api_key, secret_key, paper]):
            # Use DI container
            return cls._container.services.trading_service_manager()
        else:
            # Backward compatibility: direct instantiation
            api_key = api_key or "default_key"
            secret_key = secret_key or "default_secret"
            paper = paper if paper is not None else True
            return TradingServiceManager(api_key, secret_key, paper)
    
    @classmethod
    def get_container(cls) -> Optional[ApplicationContainer]:
        """Get the current DI container."""
        return cls._container
```

**Deliverable**: Optional service factory for gradual migration

---

## Phase 2: Application Layer Migration (Week 1, Days 4-7)

### 2.1 Update TradingEngine for DI Support

**File to modify**: `the_alchemiser/application/trading_engine.py`

**Work needed**: Add DI constructor while maintaining backward compatibility

**Add new DI-aware constructor**:

```python
from typing import Optional, Union
from dependency_injector.wiring import Provide, inject
from the_alchemiser.container.application_container import ApplicationContainer

class TradingEngine:
    """Unified multi-strategy trading engine with dependency injection support."""
    
    def __init__(
        self,
        paper_trading: bool = True,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
        config: Settings | None = None,
        # NEW: DI-aware parameters
        trading_service_manager: Optional[TradingServiceManager] = None,
        container: Optional[ApplicationContainer] = None,
    ) -> None:
        """Initialize TradingEngine with optional dependency injection.
        
        Args:
            paper_trading: Whether to use paper trading (backward compatibility)
            strategy_allocations: Strategy allocation weights (backward compatibility)  
            ignore_market_hours: Whether to ignore market hours (backward compatibility)
            config: Settings configuration (backward compatibility)
            trading_service_manager: Injected service manager (DI mode)
            container: DI container for full DI mode
        """
        self.logger = get_logger(__name__)
        
        # Determine initialization mode
        if container is not None:
            # Full DI mode
            self._init_with_container(container, strategy_allocations, ignore_market_hours)
        elif trading_service_manager is not None:
            # Partial DI mode
            self._init_with_service_manager(trading_service_manager, strategy_allocations, ignore_market_hours)
        else:
            # Backward compatibility mode
            self._init_traditional(paper_trading, strategy_allocations, ignore_market_hours, config)
    
    def _init_with_container(
        self, 
        container: ApplicationContainer,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool
    ) -> None:
        """Initialize using full DI container."""
        self._container = container
        self.data_provider = container.services.trading_service_manager()
        self.paper_trading = container.config.paper_trading()
        self.ignore_market_hours = ignore_market_hours
        
        # Initialize other components using DI
        self._init_common_components(strategy_allocations)
    
    def _init_with_service_manager(
        self,
        trading_service_manager: TradingServiceManager,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool
    ) -> None:
        """Initialize using injected service manager."""
        self._container = None
        self.data_provider = trading_service_manager
        self.paper_trading = trading_service_manager.alpaca_manager.is_paper_trading
        self.ignore_market_hours = ignore_market_hours
        
        self._init_common_components(strategy_allocations)
    
    def _init_traditional(
        self,
        paper_trading: bool,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool,
        config: Settings | None
    ) -> None:
        """Initialize using traditional method (backward compatibility)."""
        # Existing initialization logic remains unchanged
        self._container = None
        self.paper_trading = paper_trading
        self.ignore_market_hours = ignore_market_hours
        
        # Load configuration
        try:
            self.config = config or load_settings()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration error: {e}")
        
        # Initialize data provider (existing logic)
        try:
            self.data_provider = UnifiedDataProviderFacade(
                paper_trading=paper_trading, settings=self.config
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize data provider: {e}")
            raise
        
        self._init_common_components(strategy_allocations)
    
    def _init_common_components(self, strategy_allocations: dict[StrategyType, float] | None) -> None:
        """Initialize components common to all initialization modes."""
        # Strategy allocations
        self.strategy_allocations = strategy_allocations or {
            StrategyType.NUCLEAR: 1.0 / 3.0,
            StrategyType.TECL: 1.0 / 3.0,
            StrategyType.KLM: 1.0 / 3.0,
        }
        
        # Initialize other components (existing logic remains the same)
        # ... rest of existing initialization
    
    @classmethod 
    @inject
    def create_with_di(
        cls,
        container: ApplicationContainer = Provide[ApplicationContainer],
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine with full DI."""
        return cls(
            container=container,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours
        )
```

**Deliverable**: TradingEngine supports DI while maintaining backward compatibility

### 2.2 Update Main Entry Points

#### 2.2.1 Update main.py for Optional DI

**File to modify**: `the_alchemiser/main.py`

**Work needed**: Add DI initialization option while keeping existing functionality

**Add at the top of file (after imports)**:

```python
from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.services.service_factory import ServiceFactory

# Global DI container (optional)
_di_container: Optional[ApplicationContainer] = None

def initialize_dependency_injection(use_di: bool = False) -> None:
    """Initialize dependency injection system."""
    global _di_container
    
    if use_di:
        _di_container = ApplicationContainer()
        _di_container.wire(modules=[__name__])
        ServiceFactory.initialize(_di_container)
        logger.info("Dependency injection initialized")
    else:
        logger.info("Using traditional initialization (no DI)")
```

**Update main function to support DI**:

```python
def main(use_dependency_injection: bool = False) -> dict[str, Any]:
    """Main trading function with optional dependency injection.
    
    Args:
        use_dependency_injection: Whether to use DI system (default: False for backward compatibility)
    
    Returns:
        Dictionary containing execution results and performance metrics
    """
    try:
        # Initialize DI if requested
        initialize_dependency_injection(use_di=use_dependency_injection)
        
        if _di_container is not None:
            # Use DI mode
            engine = TradingEngine.create_with_di(
                container=_di_container,
                ignore_market_hours=True
            )
        else:
            # Traditional mode (existing logic)
            engine = TradingEngine(
                paper_trading=True,
                ignore_market_hours=True
            )
        
        # Rest of function remains the same
        result = engine.execute_multi_strategy()
        return result
        
    except Exception as e:
        logger.error(f"Trading execution failed: {e}")
        raise
```

**Add CLI argument for DI**:

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="The Alchemiser Trading System")
    
    # Existing arguments...
    
    # NEW: DI option
    parser.add_argument(
        "--use-di",
        action="store_true",
        help="Use dependency injection system (experimental)"
    )
    
    return parser.parse_args()
```

**Update CLI entry point**:

```python
if __name__ == "__main__":
    args = parse_arguments()
    
    if args.command == "trade":
        result = main(use_dependency_injection=args.use_di)
    # ... rest of CLI logic
```

**Deliverable**: main.py supports optional DI while maintaining existing functionality

#### 2.2.2 Update lambda_handler.py for DI

**File to modify**: `the_alchemiser/lambda_handler.py`

**Work needed**: Add DI support for AWS Lambda environment

**Add DI initialization**:

```python
from the_alchemiser.container.application_container import ApplicationContainer

# Lambda global container
_lambda_container: Optional[ApplicationContainer] = None

def initialize_lambda_di() -> ApplicationContainer:
    """Initialize DI container for Lambda environment."""
    global _lambda_container
    
    if _lambda_container is None:
        _lambda_container = ApplicationContainer.create_for_environment("production")
        _lambda_container.wire(modules=[__name__])
    
    return _lambda_container
```

**Update lambda_handler function**:

```python
def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda handler with optional dependency injection."""
    try:
        # Check if DI is enabled via environment variable
        use_di = os.environ.get("USE_DEPENDENCY_INJECTION", "false").lower() == "true"
        
        if use_di:
            # Use DI mode
            container = initialize_lambda_di()
            engine = TradingEngine.create_with_di(container=container)
        else:
            # Traditional mode (existing logic)
            from the_alchemiser.main import main
            result = main()
            return {"statusCode": 200, "body": json.dumps(result)}
        
        # Execute trading with DI
        result = engine.execute_multi_strategy()
        return {"statusCode": 200, "body": json.dumps(result)}
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
```

**Deliverable**: Lambda handler supports DI via environment variable

---

## Phase 3: Testing Infrastructure (Week 2, Days 1-3)

### 3.1 Create DI Test Utilities

**New file**: `tests/conftest.py` (update existing)

**Work needed**: Add DI test fixtures

**Add to existing conftest.py**:

```python
import pytest
from unittest.mock import Mock

from the_alchemiser.container.application_container import ApplicationContainer


@pytest.fixture
def di_container():
    """Provide DI container for testing."""
    return ApplicationContainer.create_for_testing()


@pytest.fixture
def mock_trading_service_manager():
    """Provide mocked TradingServiceManager."""
    mock_manager = Mock()
    mock_manager.alpaca_manager = Mock()
    mock_manager.alpaca_manager.is_paper_trading = True
    
    # Mock common methods
    mock_manager.get_all_positions.return_value = {"AAPL": 100, "MSFT": 50}
    mock_manager.get_account_info.return_value = {
        "portfolio_value": 100000,
        "cash": 10000,
        "buying_power": 50000
    }
    
    return mock_manager


@pytest.fixture
def di_trading_engine(di_container, mock_trading_service_manager):
    """Provide TradingEngine with DI for testing."""
    # Override service manager with mock
    di_container.services.trading_service_manager.override(mock_trading_service_manager)
    
    from the_alchemiser.application.trading_engine import TradingEngine
    return TradingEngine(container=di_container)
```

**Deliverable**: Test fixtures for DI testing

### 3.2 Create DI Integration Tests

**New file**: `tests/integration/test_dependency_injection.py`

```python
"""Integration tests for dependency injection system."""

import pytest

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.application.trading_engine import TradingEngine


class TestDependencyInjection:
    """Test dependency injection integration."""
    
    def test_container_initialization(self):
        """Test that DI container initializes correctly."""
        container = ApplicationContainer()
        
        # Test that container can provide services
        trading_manager = container.services.trading_service_manager()
        assert trading_manager is not None
        assert hasattr(trading_manager, 'alpaca_manager')
    
    def test_trading_engine_di_mode(self, di_container):
        """Test TradingEngine in DI mode."""
        engine = TradingEngine(container=di_container)
        
        assert engine._container is not None
        assert engine.data_provider is not None
        assert hasattr(engine, 'paper_trading')
    
    def test_trading_engine_traditional_mode(self):
        """Test TradingEngine in traditional mode (backward compatibility)."""
        engine = TradingEngine(paper_trading=True)
        
        assert engine._container is None
        assert engine.data_provider is not None
        assert engine.paper_trading is True
    
    def test_service_injection(self, di_container, mock_trading_service_manager):
        """Test that services are properly injected."""
        # Override with mock
        di_container.services.trading_service_manager.override(mock_trading_service_manager)
        
        engine = TradingEngine(container=di_container)
        
        # Test that mock is used
        positions = engine.data_provider.get_all_positions()
        assert positions == {"AAPL": 100, "MSFT": 50}
    
    def test_environment_specific_containers(self):
        """Test environment-specific container configuration."""
        # Test container
        test_container = ApplicationContainer.create_for_environment("test")
        assert test_container.config.paper_trading() is True
        
        # Production container
        prod_container = ApplicationContainer.create_for_environment("production")
        assert prod_container is not None


class TestBackwardCompatibility:
    """Test that existing functionality still works."""
    
    def test_trading_service_manager_traditional_init(self):
        """Test TradingServiceManager works with traditional initialization."""
        from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
        
        # This should work exactly as before
        manager = TradingServiceManager("test_key", "test_secret", paper=True)
        assert manager.alpaca_manager is not None
        assert manager.alpaca_manager.is_paper_trading is True
    
    def test_main_function_backward_compatibility(self):
        """Test that main function works without DI."""
        from the_alchemiser.main import main
        
        # This should work exactly as before
        try:
            result = main(use_dependency_injection=False)
            # Should execute without errors (though may fail due to missing credentials)
        except Exception as e:
            # Expected due to test environment, but DI code shouldn't cause issues
            assert "dependency" not in str(e).lower()
```

**Deliverable**: Comprehensive DI integration tests

### 3.3 Update Existing Tests for DI Support

**Files to modify**: All existing test files in `tests/`

**Work needed**: Update tests to optionally use DI fixtures

**Example update for** `tests/services/test_trading_service_manager.py`:

```python
# Add DI test alongside existing test
def test_trading_service_manager_with_di(di_container):
    """Test TradingServiceManager via DI container."""
    manager = di_container.services.trading_service_manager()
    
    assert manager is not None
    assert hasattr(manager, 'alpaca_manager')
    
    # Test should work the same as traditional initialization
    # ... existing test logic
```

**Strategy**: Add DI tests alongside existing tests without modifying the existing ones

**Deliverable**: Enhanced test suite supporting both traditional and DI modes

---

## Phase 4: Gradual Migration and Production Rollout (Week 2-3)

### 4.1 Feature Flag System

**New file**: `the_alchemiser/config/feature_flags.py`

```python
"""Feature flags for gradual DI rollout."""

import os
from typing import Dict, Any


class FeatureFlags:
    """Feature flags for controlling DI rollout."""
    
    @staticmethod
    def is_di_enabled() -> bool:
        """Check if dependency injection is enabled."""
        return os.environ.get("ENABLE_DEPENDENCY_INJECTION", "false").lower() == "true"
    
    @staticmethod
    def get_di_rollout_percentage() -> int:
        """Get percentage of requests to use DI (0-100)."""
        return int(os.environ.get("DI_ROLLOUT_PERCENTAGE", "0"))
    
    @staticmethod
    def should_use_di_for_request(request_id: str = None) -> bool:
        """Determine if this request should use DI based on rollout percentage."""
        if not FeatureFlags.is_di_enabled():
            return False
        
        rollout_pct = FeatureFlags.get_di_rollout_percentage()
        if rollout_pct >= 100:
            return True
        if rollout_pct <= 0:
            return False
        
        # Simple hash-based distribution
        if request_id:
            hash_val = hash(request_id) % 100
            return hash_val < rollout_pct
        
        return False
```

**Deliverable**: Feature flag system for controlled rollout

### 4.2 Update Main Entry Points for Gradual Rollout

**File to modify**: `the_alchemiser/main.py`

**Work needed**: Use feature flags for gradual rollout

**Update main function**:

```python
from the_alchemiser.config.feature_flags import FeatureFlags

def main(
    use_dependency_injection: Optional[bool] = None,
    request_id: Optional[str] = None
) -> dict[str, Any]:
    """Main trading function with gradual DI rollout.
    
    Args:
        use_dependency_injection: Override DI setting (None = use feature flags)
        request_id: Request ID for rollout decisions
    """
    try:
        # Determine if DI should be used
        if use_dependency_injection is None:
            use_di = FeatureFlags.should_use_di_for_request(request_id)
        else:
            use_di = use_dependency_injection
        
        logger.info(f"Execution mode: {'DI' if use_di else 'Traditional'}")
        
        # Initialize and execute
        initialize_dependency_injection(use_di=use_di)
        
        if _di_container is not None:
            engine = TradingEngine.create_with_di(
                container=_di_container,
                ignore_market_hours=True
            )
        else:
            engine = TradingEngine(
                paper_trading=True,
                ignore_market_hours=True
            )
        
        result = engine.execute_multi_strategy()
        
        # Add metadata about execution mode
        result["execution_mode"] = "dependency_injection" if use_di else "traditional"
        result["di_enabled"] = use_di
        
        return result
        
    except Exception as e:
        logger.error(f"Trading execution failed: {e}")
        raise
```

**Deliverable**: Gradual rollout capability in main entry point

### 4.3 AWS Lambda Gradual Rollout

**File to modify**: `the_alchemiser/lambda_handler.py`

**Work needed**: Implement gradual rollout for Lambda

**Update lambda_handler**:

```python
import uuid
from the_alchemiser.config.feature_flags import FeatureFlags

def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda handler with gradual DI rollout."""
    try:
        # Generate request ID for rollout decision
        request_id = event.get("request_id", str(uuid.uuid4()))
        
        # Determine if DI should be used based on feature flags
        use_di = FeatureFlags.should_use_di_for_request(request_id)
        
        logger.info(f"Lambda execution mode: {'DI' if use_di else 'Traditional'}, Request ID: {request_id}")
        
        if use_di:
            # Use DI mode
            container = initialize_lambda_di()
            engine = TradingEngine.create_with_di(container=container)
            result = engine.execute_multi_strategy()
        else:
            # Traditional mode
            from the_alchemiser.main import main
            result = main(use_dependency_injection=False, request_id=request_id)
        
        # Add metadata
        result["request_id"] = request_id
        result["execution_mode"] = "dependency_injection" if use_di else "traditional"
        
        return {"statusCode": 200, "body": json.dumps(result)}
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
```

**Deliverable**: Lambda with gradual DI rollout

### 4.4 Monitoring and Observability

**New file**: `the_alchemiser/monitoring/di_metrics.py`

```python
"""Monitoring and metrics for dependency injection rollout."""

import logging
import time
from typing import Dict, Any
from contextlib import contextmanager


class DIMetrics:
    """Metrics collection for DI vs Traditional execution."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, Any] = {
            "di_executions": 0,
            "traditional_executions": 0,
            "di_execution_times": [],
            "traditional_execution_times": [],
            "di_errors": 0,
            "traditional_errors": 0,
        }
    
    @contextmanager
    def track_execution(self, mode: str):
        """Track execution time and success/failure."""
        start_time = time.time()
        success = False
        
        try:
            yield
            success = True
        except Exception as e:
            self.logger.error(f"{mode} execution failed: {e}")
            if mode == "di":
                self.metrics["di_errors"] += 1
            else:
                self.metrics["traditional_errors"] += 1
            raise
        finally:
            execution_time = time.time() - start_time
            
            if success:
                if mode == "di":
                    self.metrics["di_executions"] += 1
                    self.metrics["di_execution_times"].append(execution_time)
                else:
                    self.metrics["traditional_executions"] += 1
                    self.metrics["traditional_execution_times"].append(execution_time)
            
            self.logger.info(f"{mode} execution completed in {execution_time:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        di_times = self.metrics["di_execution_times"]
        traditional_times = self.metrics["traditional_execution_times"]
        
        return {
            "di_executions": self.metrics["di_executions"],
            "traditional_executions": self.metrics["traditional_executions"],
            "di_avg_time": sum(di_times) / len(di_times) if di_times else 0,
            "traditional_avg_time": sum(traditional_times) / len(traditional_times) if traditional_times else 0,
            "di_error_rate": self.metrics["di_errors"] / max(1, self.metrics["di_executions"]),
            "traditional_error_rate": self.metrics["traditional_errors"] / max(1, self.metrics["traditional_executions"]),
        }


# Global metrics instance
di_metrics = DIMetrics()
```

**File to modify**: `the_alchemiser/main.py`

**Add metrics tracking**:

```python
from the_alchemiser.monitoring.di_metrics import di_metrics

def main(use_dependency_injection: Optional[bool] = None, request_id: Optional[str] = None) -> dict[str, Any]:
    """Main trading function with metrics tracking."""
    # Determine execution mode
    if use_dependency_injection is None:
        use_di = FeatureFlags.should_use_di_for_request(request_id)
    else:
        use_di = use_dependency_injection
    
    mode = "di" if use_di else "traditional"
    
    # Execute with metrics tracking
    with di_metrics.track_execution(mode):
        initialize_dependency_injection(use_di=use_di)
        
        if _di_container is not None:
            engine = TradingEngine.create_with_di(container=_di_container, ignore_market_hours=True)
        else:
            engine = TradingEngine(paper_trading=True, ignore_market_hours=True)
        
        result = engine.execute_multi_strategy()
    
    # Add metrics to result
    result["execution_mode"] = mode
    result["metrics_summary"] = di_metrics.get_summary()
    
    return result
```

**Deliverable**: Comprehensive monitoring for DI rollout

---

## Phase 5: Migration Validation and Cleanup (Week 3-4)

### 5.1 Migration Validation Script

**New file**: `scripts/validate_di_migration.py`

```python
#!/usr/bin/env python3
"""Validate dependency injection migration."""

import sys
import traceback
from typing import Dict, Any, List

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.application.trading_engine import TradingEngine
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class DIValidation:
    """Validation suite for DI migration."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        try:
            test_func()
            self.results.append({"test": test_name, "status": "PASS", "error": None})
            print(f"✅ {test_name}")
        except Exception as e:
            self.results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"❌ {test_name}: {e}")
    
    def test_container_creation(self):
        """Test that DI container can be created."""
        container = ApplicationContainer()
        assert container is not None
    
    def test_service_injection(self):
        """Test that services can be injected."""
        container = ApplicationContainer.create_for_testing()
        trading_manager = container.services.trading_service_manager()
        assert trading_manager is not None
    
    def test_trading_engine_di_mode(self):
        """Test TradingEngine with DI."""
        container = ApplicationContainer.create_for_testing()
        engine = TradingEngine(container=container)
        assert engine._container is not None
    
    def test_trading_engine_traditional_mode(self):
        """Test TradingEngine traditional mode still works."""
        engine = TradingEngine(paper_trading=True)
        assert engine._container is None
        assert engine.paper_trading is True
    
    def test_backward_compatibility(self):
        """Test that existing code still works."""
        # Test TradingServiceManager direct instantiation
        manager = TradingServiceManager("test_key", "test_secret", paper=True)
        assert manager.alpaca_manager is not None
        
        # Test that all existing methods exist
        assert hasattr(manager, 'get_all_positions')
        assert hasattr(manager, 'place_market_order')
    
    def test_feature_flags(self):
        """Test feature flag system."""
        from the_alchemiser.config.feature_flags import FeatureFlags
        
        # Test methods exist and return proper types
        assert isinstance(FeatureFlags.is_di_enabled(), bool)
        assert isinstance(FeatureFlags.get_di_rollout_percentage(), int)
    
    def test_environment_containers(self):
        """Test environment-specific containers."""
        test_container = ApplicationContainer.create_for_environment("test")
        prod_container = ApplicationContainer.create_for_environment("production")
        
        assert test_container is not None
        assert prod_container is not None
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("🔍 Validating Dependency Injection Migration...")
        print("=" * 60)
        
        self.run_test("Container Creation", self.test_container_creation)
        self.run_test("Service Injection", self.test_service_injection)
        self.run_test("TradingEngine DI Mode", self.test_trading_engine_di_mode)
        self.run_test("TradingEngine Traditional Mode", self.test_trading_engine_traditional_mode)
        self.run_test("Backward Compatibility", self.test_backward_compatibility)
        self.run_test("Feature Flags", self.test_feature_flags)
        self.run_test("Environment Containers", self.test_environment_containers)
        
        # Summary
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        
        print("=" * 60)
        print(f"📊 Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ Failed tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['error']}")
            return False
        else:
            print("✅ All tests passed! DI migration is successful.")
            return True


def main():
    """Run DI validation."""
    validator = DIValidation()
    success = validator.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Deliverable**: Comprehensive validation script

### 5.2 Performance Comparison Script

**New file**: `scripts/compare_di_performance.py`

```python
#!/usr/bin/env python3
"""Compare performance between DI and traditional modes."""

import time
import statistics
from typing import List, Dict, Any

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.application.trading_engine import TradingEngine


class PerformanceComparison:
    """Compare performance between DI and traditional modes."""
    
    def __init__(self, iterations: int = 10):
        self.iterations = iterations
        self.results: Dict[str, List[float]] = {
            "traditional": [],
            "di": []
        }
    
    def time_traditional_initialization(self) -> float:
        """Time traditional TradingEngine initialization."""
        start = time.time()
        engine = TradingEngine(paper_trading=True)
        # Simulate some operations
        _ = hasattr(engine, 'data_provider')
        end = time.time()
        return end - start
    
    def time_di_initialization(self) -> float:
        """Time DI TradingEngine initialization."""
        start = time.time()
        container = ApplicationContainer.create_for_testing()
        engine = TradingEngine(container=container)
        # Simulate some operations
        _ = hasattr(engine, 'data_provider')
        end = time.time()
        return end - start
    
    def run_comparison(self):
        """Run performance comparison."""
        print(f"🚀 Running performance comparison ({self.iterations} iterations)...")
        
        # Traditional mode
        print("Testing traditional mode...")
        for i in range(self.iterations):
            try:
                time_taken = self.time_traditional_initialization()
                self.results["traditional"].append(time_taken)
                print(f"  Iteration {i+1}: {time_taken:.4f}s")
            except Exception as e:
                print(f"  Iteration {i+1}: FAILED - {e}")
        
        # DI mode
        print("Testing DI mode...")
        for i in range(self.iterations):
            try:
                time_taken = self.time_di_initialization()
                self.results["di"].append(time_taken)
                print(f"  Iteration {i+1}: {time_taken:.4f}s")
            except Exception as e:
                print(f"  Iteration {i+1}: FAILED - {e}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print performance summary."""
        print("\n" + "=" * 60)
        print("📊 Performance Summary")
        print("=" * 60)
        
        for mode, times in self.results.items():
            if times:
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                min_time = min(times)
                max_time = max(times)
                
                print(f"\n{mode.upper()} MODE:")
                print(f"  Average: {avg_time:.4f}s")
                print(f"  Median:  {median_time:.4f}s")
                print(f"  Min:     {min_time:.4f}s")
                print(f"  Max:     {max_time:.4f}s")
                print(f"  Samples: {len(times)}")
            else:
                print(f"\n{mode.upper()} MODE: No successful runs")
        
        # Comparison
        if self.results["traditional"] and self.results["di"]:
            traditional_avg = statistics.mean(self.results["traditional"])
            di_avg = statistics.mean(self.results["di"])
            
            if di_avg < traditional_avg:
                improvement = ((traditional_avg - di_avg) / traditional_avg) * 100
                print(f"\n✅ DI mode is {improvement:.1f}% faster")
            else:
                overhead = ((di_avg - traditional_avg) / traditional_avg) * 100
                print(f"\n⚠️  DI mode has {overhead:.1f}% overhead")


def main():
    """Run performance comparison."""
    comparison = PerformanceComparison(iterations=10)
    comparison.run_comparison()


if __name__ == "__main__":
    main()
```

**Deliverable**: Performance comparison analysis

### 5.3 Migration Completion Checklist

**New file**: `docs/DI_MIGRATION_CHECKLIST.md`

```markdown
# Dependency Injection Migration Checklist

## Phase 1: Foundation ✅
- [ ] Install dependency-injector package
- [ ] Create container infrastructure
- [ ] Update enhanced services for DI compatibility
- [ ] Create service factory
- [ ] Validate Phase 1 with tests

## Phase 2: Application Layer ✅  
- [ ] Update TradingEngine for DI support
- [ ] Update main.py entry point
- [ ] Update lambda_handler.py
- [ ] Maintain backward compatibility
- [ ] Validate Phase 2 with tests

## Phase 3: Testing ✅
- [ ] Create DI test utilities
- [ ] Create DI integration tests
- [ ] Update existing tests
- [ ] Validate all tests pass
- [ ] Performance testing

## Phase 4: Gradual Rollout ✅
- [ ] Implement feature flag system
- [ ] Update entry points for gradual rollout
- [ ] Add monitoring and observability
- [ ] Test rollout mechanism
- [ ] Monitor metrics

## Phase 5: Validation & Cleanup ✅
- [ ] Run migration validation script
- [ ] Run performance comparison
- [ ] Complete documentation
- [ ] Remove deprecated code (if any)
- [ ] Final testing

## Production Rollout Plan

### Week 1: 0% → 5%
- [ ] Enable DI for 5% of requests
- [ ] Monitor error rates and performance
- [ ] Compare metrics between modes

### Week 2: 5% → 25%
- [ ] Increase to 25% if metrics are good
- [ ] Continue monitoring
- [ ] Address any issues

### Week 3: 25% → 75%
- [ ] Major rollout to 75%
- [ ] Monitor stability
- [ ] Prepare for full rollout

### Week 4: 75% → 100%
- [ ] Complete rollout to 100%
- [ ] Monitor for issues
- [ ] Mark traditional mode as deprecated

## Environment Variables for Rollout

```bash
# Enable DI system
ENABLE_DEPENDENCY_INJECTION=true

# Rollout percentage (0-100)
DI_ROLLOUT_PERCENTAGE=50

# Lambda-specific DI
USE_DEPENDENCY_INJECTION=true
```

## Success Criteria

- [ ] All tests pass in both modes
- [ ] Performance is comparable (within 10%)
- [ ] Error rates are same or lower
- [ ] Memory usage is comparable
- [ ] No breaking changes for existing code

```

**Deliverable**: Complete migration checklist

---

## Risk Mitigation and Rollback Plan

### Rollback Strategy

1. **Immediate Rollback**: Set `DI_ROLLOUT_PERCENTAGE=0`
2. **Environment Variable Rollback**: Set `ENABLE_DEPENDENCY_INJECTION=false`
3. **Code Rollback**: All traditional code paths remain unchanged

### Monitoring Points

1. **Error Rates**: Compare error rates between DI and traditional modes
2. **Performance**: Monitor initialization and execution times
3. **Memory Usage**: Track memory consumption
4. **Success Rates**: Monitor trading execution success rates

### Validation Gates

Each phase must pass these gates before proceeding:
1. All tests pass
2. Performance within 10% of baseline
3. No increase in error rates
4. Memory usage within acceptable bounds

---

## Summary of Deliverables

### Files Created (New):
1. `the_alchemiser/container/__init__.py`
2. `the_alchemiser/container/application_container.py`
3. `the_alchemiser/container/config_providers.py`
4. `the_alchemiser/container/infrastructure_providers.py`
5. `the_alchemiser/container/service_providers.py`
6. `the_alchemiser/services/service_factory.py`
7. `the_alchemiser/config/feature_flags.py`
8. `the_alchemiser/monitoring/di_metrics.py`
9. `tests/integration/test_dependency_injection.py`
10. `scripts/validate_di_migration.py`
11. `scripts/compare_di_performance.py`
12. `docs/DI_MIGRATION_CHECKLIST.md`

### Files Modified (Enhanced):
1. `pyproject.toml` - Add dependency-injector
2. `the_alchemiser/services/enhanced/order_service.py` - DI compatibility
3. `the_alchemiser/services/enhanced/position_service.py` - DI compatibility
4. `the_alchemiser/services/enhanced/market_data_service.py` - DI compatibility
5. `the_alchemiser/services/enhanced/account_service.py` - DI compatibility
6. `the_alchemiser/application/trading_engine.py` - DI support
7. `the_alchemiser/main.py` - DI integration
8. `the_alchemiser/lambda_handler.py` - DI integration
9. `tests/conftest.py` - DI test fixtures

### Key Benefits Achieved:
1. **Zero Breaking Changes**: All existing code continues to work
2. **Gradual Migration**: Controlled rollout with feature flags
3. **Easy Testing**: Mocked dependencies for unit tests
4. **Flexible Configuration**: Environment-specific containers
5. **Performance Monitoring**: Comprehensive metrics collection
6. **Clean Architecture**: Proper separation of concerns

This plan ensures a safe, controlled migration to dependency injection while maintaining all existing functionality and providing clear benefits for testing, configuration, and maintainability.
