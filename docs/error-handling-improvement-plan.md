# Error Handling & Exception Hierarchy Improvement Plan

## Current State Analysis

### ✅ What We Have
- **Comprehensive exception hierarchy** in `core/exceptions.py` with 20+ specific exception types
- **Base `AlchemiserError`** class for all custom exceptions
- **Contextual exception classes** with additional attributes (symbol, strategy_name, etc.)
- **Specific exception types** for different domains: Trading, Data, Configuration, etc.

### ❌ What Needs Improvement
- **20+ generic `except Exception` blocks** throughout the codebase
- **Generic `raise Exception()`** calls that should use specific types
- **Limited error context** and error recovery strategies
- **No structured error reporting** for hands-off operation
- **Missing retry logic** with exponential backoff
- **No error aggregation** for batch operations

## Implementation Strategy

### Phase 1: Replace Generic Exception Handling
**Priority: P1 - Critical for production reliability**

1. **Audit and Replace Generic Catches**
2. **Implement Specific Exception Types**
3. **Add Contextual Error Information**
4. **Create Error Recovery Strategies**

### Phase 2: Enhanced Error Reporting
**Priority: P1 - Critical for hands-off operation**

1. **Structured Error Logging**
2. **Error Aggregation and Batching**
3. **Critical Error Notifications**
4. **Error Recovery Dashboards**

### Phase 3: Resilience Patterns
**Priority: P2 - Production hardening**

1. **Retry Logic with Exponential Backoff**
2. **Circuit Breaker Pattern**
3. **Graceful Degradation**
4. **Error Rate Limiting**

## Detailed Implementation Plan

### 1. Exception Replacement Strategy

#### Target Areas (20+ locations identified):

1. **Main Application** (`main.py`): 6 generic exception handlers
2. **Lambda Handler** (`lambda_handler.py`): 2 generic exception handlers  
3. **Execution Manager** (`execution/execution_manager.py`): 2 generic exceptions
4. **Order Tracking** (`tracking/strategy_order_tracker.py`): 4 generic exceptions
5. **Integration** (`tracking/integration.py`): 4 generic exceptions

#### Replacement Pattern:

```python
# BEFORE: Generic exception handling
try:
    result = risky_operation()
except Exception as e:
    logger.error("Something went wrong: %s", e)
    return None

# AFTER: Specific exception handling with context
try:
    result = risky_operation()
except DataProviderError as e:
    logger.error("Data provider failed for %s: %s", e.symbol, e)
    # Specific recovery strategy
    return get_cached_data(e.symbol)
except TradingClientError as e:
    logger.error("Trading operation failed: %s", e)
    # Specific recovery strategy
    notify_critical_error(e)
    raise  # Re-raise for upper layers
except AlchemiserError as e:
    logger.error("Application error: %s", e)
    # Generic recovery for known errors
    return default_safe_value()
```

### 2. Error Context Enhancement

#### Current Exception Classes Enhancement:

```python
# Enhanced exceptions with better context
class OrderExecutionError(TradingClientError):
    """Enhanced order execution error with full context."""
    
    def __init__(
        self, 
        message: str, 
        symbol: str | None = None, 
        order_type: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        account_id: str | None = None,
        timestamp: datetime | None = None,
        retry_count: int = 0
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.order_type = order_type
        self.order_id = order_id
        self.quantity = quantity
        self.price = price
        self.account_id = account_id
        self.timestamp = timestamp or datetime.now()
        self.retry_count = retry_count
        
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "symbol": self.symbol,
            "order_type": self.order_type,
            "order_id": self.order_id,
            "quantity": self.quantity,
            "price": self.price,
            "account_id": self.account_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "retry_count": self.retry_count
        }
```

### 3. Error Recovery Patterns

#### Retry Decorator with Exponential Backoff:

```python
from functools import wraps
import time
import random
from typing import Callable, Type

def retry_with_backoff(
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    """Retry decorator with exponential backoff and jitter."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Add retry context to exception
                        if hasattr(e, 'retry_count'):
                            e.retry_count = attempt
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)  # Add 50% jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

# Usage examples:
@retry_with_backoff(
    exceptions=(DataProviderError, RateLimitError),
    max_retries=3,
    base_delay=1.0
)
def fetch_market_data(symbol: str) -> MarketData:
    # Implementation with specific exception handling
    pass

@retry_with_backoff(
    exceptions=(OrderExecutionError,),
    max_retries=2,
    base_delay=0.5
)
def place_order(symbol: str, quantity: float) -> Order:
    # Implementation with specific exception handling
    pass
```

### 4. Structured Error Reporting

#### Error Reporter for Hands-off Operation:

```python
class ErrorReporter:
    """Centralized error reporting for production monitoring."""
    
    def __init__(self, notification_manager=None):
        self.notification_manager = notification_manager
        self.error_counts = defaultdict(int)
        self.critical_errors = []
        
    def report_error(
        self, 
        error: Exception, 
        context: dict[str, Any] | None = None,
        is_critical: bool = False
    ) -> None:
        """Report an error with context for monitoring."""
        
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "context": context or {},
            "is_critical": is_critical
        }
        
        # Add exception-specific context if available
        if hasattr(error, 'to_dict'):
            error_data.update(error.to_dict())
        
        # Log structured error
        logger.error("Error reported", extra={"error_data": error_data})
        
        # Track error frequency
        error_key = f"{error.__class__.__name__}:{context.get('operation', 'unknown') if context else 'unknown'}"
        self.error_counts[error_key] += 1
        
        # Handle critical errors
        if is_critical or self._is_critical_error(error):
            self.critical_errors.append(error_data)
            self._handle_critical_error(error_data)
        
        # Check for error rate thresholds
        self._check_error_rates()
    
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error is critical based on type."""
        critical_types = (
            InsufficientFundsError,
            SecurityError,
            OrderExecutionError,
            MarketClosedError
        )
        return isinstance(error, critical_types)
    
    def _handle_critical_error(self, error_data: dict[str, Any]) -> None:
        """Handle critical errors with immediate notification."""
        if self.notification_manager:
            self.notification_manager.send_critical_alert(
                f"Critical Error: {error_data['error_type']}",
                error_data
            )
    
    def _check_error_rates(self) -> None:
        """Check for high error rates and alert."""
        # Implementation for error rate monitoring
        pass
        
    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of recent errors for dashboard."""
        return {
            "error_counts": dict(self.error_counts),
            "critical_errors": len(self.critical_errors),
            "last_critical": self.critical_errors[-1] if self.critical_errors else None
        }
```

### 5. Circuit Breaker Pattern

#### For External Service Resilience:

```python
class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time < self.timeout:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN for {func.__name__}"
                    )
                else:
                    self.state = "HALF_OPEN"
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker OPENED for {func.__name__}")
                
                raise
        return wrapper
```

## Implementation Priority

### Week 1: Core Exception Replacement
1. **Replace all generic `except Exception` blocks** in main.py, lambda_handler.py
2. **Add enhanced exception context** to critical paths
3. **Implement ErrorReporter** for centralized error handling
4. **Add retry decorators** to external API calls

### Week 2: Production Hardening  
1. **Implement circuit breaker** for Alpaca API calls
2. **Add error rate monitoring** and alerting
3. **Create error recovery strategies** for each exception type
4. **Add comprehensive error testing** to test suite

### Week 3: Monitoring & Dashboards
1. **Error aggregation** and reporting
2. **Integration with monitoring systems** (CloudWatch, etc.)
3. **Error rate dashboards** for production monitoring
4. **Automated error analysis** and trending

## Success Metrics

- **Zero generic `except Exception` blocks** in production code
- **100% error context** capture for debugging
- **< 30 second** error detection and alerting for critical issues
- **Automated recovery** for 80%+ of transient errors
- **Complete error audit trail** for post-incident analysis

This comprehensive error handling system will make The Alchemiser truly hands-off by ensuring all errors are properly categorized, logged, and either automatically recovered from or escalated appropriately.
