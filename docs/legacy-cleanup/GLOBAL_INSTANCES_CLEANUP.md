# Global Instances Cleanup Plan

## Overview

This document outlines the systematic elimination of global instances and singleton patterns throughout The Alchemiser codebase. Global instances create hidden dependencies, make testing difficult, and violate dependency injection principles. This cleanup will replace global patterns with proper dependency injection.

## Global Instance Inventory

### 1. Enhanced Error Reporter Global
**Location**: `core/error_handler.py`
**Pattern**: Global singleton with lazy initialization

```python
# Global enhanced error reporter instance (for backward compatibility)
# Consider using get_enhanced_error_reporter() in new code for better testability
_global_enhanced_error_reporter: EnhancedErrorReporter | None = None

def get_global_error_reporter() -> EnhancedErrorReporter:
    """Get the global error handler instance, creating it if needed."""
    global _global_enhanced_error_reporter
    if _global_enhanced_error_reporter is None:
        _global_enhanced_error_reporter = EnhancedErrorReporter()
    return _global_enhanced_error_reporter
```

**Issues**:
- Hidden dependency for error handling
- Difficult to test with different configurations
- Global state makes testing non-deterministic
- Coupling between modules through global state

**Usage Analysis**: Used throughout codebase for error reporting

### 2. Email Client Global Instance
**Location**: `core/ui/email/client.py`
**Pattern**: Global instance for backward compatibility

```python
# Global instance for backward compatibility
_email_client = EmailClient()

def send_email_notification(
    subject: str,
    html_content: str,
    text_content: str | None = None,
    recipient_email: str | None = None,
) -> bool:
    """Send an email notification (backward compatibility function)."""
    return _email_client.send_notification(...)
```

**Issues**:
- Global email configuration
- Cannot test with different email settings
- Hidden dependency on email configuration
- Single global instance prevents isolation

**Usage Analysis**: Used for all email notifications throughout system

### 3. Email Config Global Instance
**Location**: `core/ui/email/config.py`
**Pattern**: Global configuration singleton

```python
# Global instance for backward compatibility
_email_config = EmailConfig()

def get_email_config() -> tuple[str, int, str, str, str] | None:
    """Get email configuration (backward compatibility function)."""
    config = _email_config.get_config()
    if config:
        return (config.smtp_server, config.smtp_port, config.username, 
                config.password, config.from_email)
    return None
```

**Issues**:
- Global configuration state
- Cannot test with different configurations
- Configuration changes affect entire system
- Caching behavior tied to global state

**Usage Analysis**: Used by email client and configuration systems

### 4. Execution Config Global Instance
**Location**: `config/execution_config.py`
**Pattern**: Global configuration with factory function

```python
# Global config instance
_config_instance: ExecutionConfig | None = None

def get_execution_config() -> ExecutionConfig:
    """Get the global execution configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ExecutionConfig()
    return _config_instance

def reset_execution_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None
```

**Issues**:
- Global execution configuration
- Hidden dependencies throughout execution system
- Reset function indicates testing difficulties
- Configuration changes affect entire system

**Usage Analysis**: Used throughout execution and trading systems

### 5. Strategy Order Tracker Global Instances
**Location**: `tracking/strategy_order_tracker.py`
**Pattern**: Multiple global instances by trading mode

```python
# Global instances for easy access - separate by trading mode
_paper_tracker: StrategyOrderTracker | None = None
_live_tracker: StrategyOrderTracker | None = None

def get_strategy_tracker(paper_trading: bool = True) -> StrategyOrderTracker:
    """Get the global strategy tracker instance."""
    global _paper_tracker, _live_tracker
    
    if paper_trading:
        if _paper_tracker is None:
            _paper_tracker = StrategyOrderTracker(paper_trading=True)
        return _paper_tracker
    else:
        if _live_tracker is None:
            _live_tracker = StrategyOrderTracker(paper_trading=False)
        return _live_tracker
```

**Issues**:
- Multiple global instances
- Hidden dependency on trading mode
- Cannot test with different tracker configurations
- Global state shared across system components

**Usage Analysis**: Used throughout order tracking and strategy systems

### 6. Fractionability Detector Singleton
**Location**: `utils/asset_info.py`
**Pattern**: Singleton with class-level instance management

```python
class FractionabilityDetector:
    _instance: "FractionabilityDetector | None" = None
    
    def __new__(cls, trading_client: TradingClient | None = None) -> "FractionabilityDetector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Issues**:
- Singleton pattern prevents multiple configurations
- Shared cache across all usage
- Cannot test with different trading clients
- Class-level state management

**Usage Analysis**: Used for asset fractionability detection throughout system

### 7. Planned Service Container Global
**Location**: `docs/refactoring/FACADE_TO_SERVICES_MIGRATION_PLAN.md`
**Pattern**: Planned global container for services

```python
# Global container instance
_global_container: ServiceContainer | None = None

def get_service_container(paper_trading: bool = True, config: Settings | None = None) -> ServiceContainer:
    """Get or create the global service container."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer(paper_trading, config)
    return _global_container

def reset_service_container() -> None:
    """Reset the global container (for testing)."""
    global _global_container
    _global_container = None
```

**Issues**:
- Would create global service dependencies
- Single configuration for entire system
- Testing difficulties with global state
- Hidden dependencies between components

**Status**: Planned but not yet implemented

## Dependency Injection Strategy

### 1. Create Service Container
**Objective**: Replace global instances with proper DI container

```python
# New: core/di/container.py
from typing import Protocol, TypeVar, Callable, Any
import threading
from contextlib import contextmanager

T = TypeVar('T')

class DIContainer:
    """Dependency injection container with thread-safe operations."""
    
    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}
        self._lock = threading.Lock()
    
    def register_singleton(self, service_type: type[T], instance: T) -> None:
        """Register a singleton instance."""
        with self._lock:
            self._singletons[service_type] = instance
    
    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for service creation."""
        with self._lock:
            self._factories[service_type] = factory
    
    def get(self, service_type: type[T]) -> T:
        """Get service instance."""
        with self._lock:
            # Check singletons first
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            # Check factories
            if service_type in self._factories:
                return self._factories[service_type]()
            
            raise ValueError(f"Service {service_type} not registered")
    
    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()

# Global container instance (only one global - contains everything else)
_container: DIContainer | None = None
_container_lock = threading.Lock()

def get_container() -> DIContainer:
    """Get the global DI container."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DIContainer()
                _setup_default_services()
    return _container

def setup_container(container: DIContainer) -> None:
    """Set up container for testing or custom configurations."""
    global _container
    with _container_lock:
        _container = container

@contextmanager
def temporary_container(container: DIContainer):
    """Temporarily use a different container (for testing)."""
    old_container = _container
    setup_container(container)
    try:
        yield container
    finally:
        global _container
        _container = old_container

def _setup_default_services() -> None:
    """Set up default service registrations."""
    container = get_container()
    
    # Register factories for services
    container.register_factory(EnhancedErrorReporter, lambda: EnhancedErrorReporter())
    container.register_factory(EmailClient, lambda: EmailClient())
    container.register_factory(EmailConfig, lambda: EmailConfig())
    container.register_factory(ExecutionConfig, lambda: ExecutionConfig())
```

### 2. Service Registration Patterns

```python
# Example service setup
def setup_production_container() -> DIContainer:
    """Set up container for production use."""
    container = DIContainer()
    
    # Error handling
    container.register_singleton(EnhancedErrorReporter, EnhancedErrorReporter())
    
    # Email services
    email_config = EmailConfig()
    container.register_singleton(EmailConfig, email_config)
    container.register_singleton(EmailClient, EmailClient(config=email_config))
    
    # Trading configuration
    container.register_singleton(ExecutionConfig, ExecutionConfig())
    
    # Strategy tracking (paper and live)
    container.register_factory(
        StrategyOrderTracker,
        lambda: StrategyOrderTracker(paper_trading=True)  # Default to paper
    )
    
    return container

def setup_test_container() -> DIContainer:
    """Set up container for testing."""
    container = DIContainer()
    
    # Mock services for testing
    container.register_singleton(EnhancedErrorReporter, Mock(spec=EnhancedErrorReporter))
    container.register_singleton(EmailClient, Mock(spec=EmailClient))
    container.register_singleton(EmailConfig, Mock(spec=EmailConfig))
    container.register_singleton(ExecutionConfig, Mock(spec=ExecutionConfig))
    
    return container
```

## Migration Plan

### Phase 1: Create DI Infrastructure (Week 1)

**Objectives**:
- Implement DI container
- Create service registration system
- Set up testing infrastructure

**Tasks**:
1. **Create DI Container** (1 day)
   - Implement `DIContainer` class
   - Add thread safety
   - Create global container access

2. **Service Registration** (1 day)
   - Create service registration patterns
   - Implement factory and singleton patterns
   - Add container setup functions

3. **Testing Infrastructure** (1 day)
   - Create test container setup
   - Implement temporary container context manager
   - Add container reset capabilities

4. **Documentation** (0.5 day)
   - Document DI patterns
   - Create usage examples
   - Update architecture documentation

### Phase 2: Error Reporter Migration (Week 1)

**Current Usage**: Global error reporter accessed throughout codebase

**Migration Steps**:
1. **Add DI Support** (0.5 day)
   ```python
   # New pattern
   def get_error_reporter(container: DIContainer | None = None) -> EnhancedErrorReporter:
       """Get error reporter from DI container."""
       if container is None:
           container = get_container()
       return container.get(EnhancedErrorReporter)
   ```

2. **Update Usage Sites** (1.5 days)
   - Find all `get_global_error_reporter()` calls
   - Update to use DI pattern
   - Pass container through call chains where needed

3. **Remove Global Instance** (0.5 day)
   - Remove `_global_enhanced_error_reporter`
   - Remove global access functions
   - Update tests

4. **Validation** (0.5 day)
   - Comprehensive testing
   - Verify no global access remains
   - Performance validation

### Phase 3: Email System Migration (Week 1-2)

**Current Usage**: Global email client and config

**Migration Steps**:
1. **Update Email Client** (1 day)
   ```python
   # Remove global instance
   # _email_client = EmailClient()  # REMOVE
   
   # New pattern
   def send_email_notification(
       subject: str,
       html_content: str,
       text_content: str | None = None,
       recipient_email: str | None = None,
       container: DIContainer | None = None,
   ) -> bool:
       """Send email notification using DI."""
       if container is None:
           container = get_container()
       client = container.get(EmailClient)
       return client.send_notification(subject, html_content, text_content, recipient_email)
   ```

2. **Update Email Config** (1 day)
   - Remove global config instance
   - Update config access patterns
   - Use DI for config injection

3. **Update Usage Sites** (1.5 days)
   - Find all email function calls
   - Update to use DI pattern
   - Pass container through call chains

4. **Testing Updates** (0.5 day)
   - Update email tests to use DI
   - Add test container configurations
   - Verify email functionality

### Phase 4: Configuration Migration (Week 2)

**Current Usage**: Global execution configuration

**Migration Steps**:
1. **Update Config Access** (1 day)
   ```python
   # Remove global instance
   # _config_instance: ExecutionConfig | None = None  # REMOVE
   
   # New pattern
   def get_execution_config(container: DIContainer | None = None) -> ExecutionConfig:
       """Get execution config from DI container."""
       if container is None:
           container = get_container()
       return container.get(ExecutionConfig)
   ```

2. **Update Usage Sites** (1.5 days)
   - Find all config access points
   - Update to use DI pattern
   - Remove reset functions

3. **Testing Updates** (0.5 day)
   - Update tests to use DI
   - Remove global reset calls
   - Validate configuration behavior

### Phase 5: Strategy Tracker Migration (Week 2-3)

**Current Usage**: Global tracker instances by trading mode

**Migration Steps**:
1. **Create Tracker Factory** (1 day)
   ```python
   class StrategyTrackerFactory:
       """Factory for creating strategy trackers."""
       
       def __init__(self, container: DIContainer) -> None:
           self.container = container
       
       def create_tracker(self, paper_trading: bool) -> StrategyOrderTracker:
           """Create tracker with proper configuration."""
           return StrategyOrderTracker(
               paper_trading=paper_trading,
               # Inject other dependencies from container
           )
   
   # Register in container
   def setup_strategy_tracking(container: DIContainer) -> None:
       container.register_singleton(StrategyTrackerFactory, 
                                   StrategyTrackerFactory(container))
   ```

2. **Update Usage Sites** (2 days)
   - Replace global tracker access
   - Update to use factory pattern
   - Handle paper/live trading modes properly

3. **Remove Global Instances** (0.5 day)
   - Remove global tracker variables
   - Remove global access functions
   - Clean up imports

### Phase 6: Asset Info Migration (Week 3)

**Current Usage**: Singleton fractionability detector

**Migration Steps**:
1. **Remove Singleton Pattern** (1 day)
   ```python
   # Remove singleton pattern
   class FractionabilityDetector:
       # Remove: _instance: "FractionabilityDetector | None" = None
       
       def __init__(self, trading_client: TradingClient | None = None) -> None:
           # Normal constructor without singleton logic
           self.trading_client = trading_client
           self._cache: dict[str, bool] = {}
   
   # Register in DI container
   def setup_asset_services(container: DIContainer, trading_client: TradingClient) -> None:
       container.register_singleton(
           FractionabilityDetector, 
           FractionabilityDetector(trading_client)
       )
   ```

2. **Update Usage Sites** (1 day)
   - Replace singleton access with DI
   - Update asset checking code
   - Pass detector through dependencies

3. **Testing Updates** (0.5 day)
   - Update tests to create instances directly
   - Remove singleton test patterns
   - Validate asset detection functionality

### Phase 7: Final Cleanup and Validation (Week 3)

**Objectives**:
- Remove all remaining global patterns
- Comprehensive testing
- Performance validation
- Documentation updates

**Tasks**:
1. **Global Pattern Audit** (1 day)
   - Search for remaining global instances
   - Verify all migrations complete
   - Clean up any missed patterns

2. **Comprehensive Testing** (1.5 days)
   - Full test suite with DI patterns
   - Integration testing
   - Performance testing

3. **Documentation Updates** (0.5 day)
   - Update architecture documentation
   - Create DI usage guidelines
   - Update examples and tutorials

## Testing Strategy

### Unit Testing with DI

```python
class TestEmailService:
    def test_email_sending_with_mock(self):
        """Test email sending with mocked dependencies."""
        # Create test container
        container = DIContainer()
        mock_client = Mock(spec=EmailClient)
        container.register_singleton(EmailClient, mock_client)
        
        # Test with DI
        with temporary_container(container):
            result = send_email_notification("Test", "<html>Test</html>")
            mock_client.send_notification.assert_called_once()

class TestErrorHandling:
    def test_error_reporting_with_mock(self):
        """Test error reporting with mocked dependencies."""
        container = DIContainer()
        mock_reporter = Mock(spec=EnhancedErrorReporter)
        container.register_singleton(EnhancedErrorReporter, mock_reporter)
        
        with temporary_container(container):
            reporter = get_error_reporter()
            # Test error reporting behavior
```

### Integration Testing

```python
class TestDIIntegration:
    def test_full_trading_workflow_with_di(self):
        """Test complete trading workflow with DI."""
        # Set up production-like container
        container = setup_test_container()
        
        with temporary_container(container):
            # Run full trading workflow
            # Verify all services work together properly
            pass

    def test_container_isolation(self):
        """Test that containers are properly isolated."""
        container1 = DIContainer()
        container2 = DIContainer()
        
        # Register different services in each container
        # Verify they don't interfere with each other
```

## Risk Management

### High-Risk Areas
1. **Error Reporting**: Used throughout system, critical for debugging
2. **Email Notifications**: Important for monitoring and alerts
3. **Configuration**: Core system behavior depends on configuration

**Mitigation**:
- Gradual migration with extensive testing
- Maintain backward compatibility during transition
- Comprehensive monitoring during rollout
- Quick rollback procedures

### Testing Considerations
1. **Dependency Chains**: Ensure proper dependency injection throughout call chains
2. **Thread Safety**: Verify DI container works correctly in multi-threaded scenarios
3. **Performance**: Ensure DI doesn't introduce significant overhead
4. **Memory**: Verify proper cleanup and no memory leaks

## Expected Benefits

### Testing Benefits
- **Isolated Tests**: Each test can use its own service configuration
- **Mock Injection**: Easy to inject mocks for testing
- **Parallel Testing**: Tests don't interfere through global state
- **Deterministic Tests**: No hidden global state affecting test results

### Code Quality Benefits
- **Explicit Dependencies**: Dependencies clearly declared in function signatures
- **Loose Coupling**: Components depend on abstractions, not concrete instances
- **Single Responsibility**: Each component focused on its specific role
- **Easier Refactoring**: Clear dependency relationships

### Maintainability Benefits
- **Clear Service Boundaries**: Well-defined service interfaces
- **Configuration Management**: Centralized service configuration
- **Easier Debugging**: Clear service dependency chains
- **Better Architecture**: Proper separation of concerns

## Success Criteria

### Functional Criteria
- [ ] All global instances removed
- [ ] No hidden dependencies remain
- [ ] System functionality unchanged
- [ ] Performance maintained or improved

### Code Quality Criteria
- [ ] All services use dependency injection
- [ ] Tests use isolated containers
- [ ] No global variables for service instances
- [ ] Clear dependency relationships

### Testing Criteria
- [ ] 95%+ test coverage maintained
- [ ] Tests run in parallel without interference
- [ ] Easy to mock dependencies in tests
- [ ] Deterministic test results

## Status Tracking

### Phase 1: DI Infrastructure
- [ ] Implement DI container
- [ ] Create service registration system
- [ ] Set up testing infrastructure
- [ ] Document DI patterns

### Phase 2: Error Reporter Migration
- [ ] Add DI support to error reporter
- [ ] Update all usage sites
- [ ] Remove global instance
- [ ] Validate functionality

### Phase 3: Email System Migration
- [ ] Update email client DI
- [ ] Update email config DI
- [ ] Update all usage sites
- [ ] Update tests

### Phase 4: Configuration Migration
- [ ] Update config access patterns
- [ ] Update all usage sites
- [ ] Update tests
- [ ] Remove global config

### Phase 5: Strategy Tracker Migration
- [ ] Create tracker factory
- [ ] Update usage sites
- [ ] Remove global instances
- [ ] Validate tracking functionality

### Phase 6: Asset Info Migration
- [ ] Remove singleton pattern
- [ ] Update usage sites
- [ ] Update tests
- [ ] Validate asset detection

### Phase 7: Final Cleanup
- [ ] Audit for remaining globals
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] Documentation updates

## Conclusion

Eliminating global instances will significantly improve The Alchemiser's testability, maintainability, and architecture. The dependency injection approach provides clear service boundaries while maintaining system functionality and performance.

This migration represents a fundamental improvement in code quality and will make future development and testing much more straightforward and reliable.
