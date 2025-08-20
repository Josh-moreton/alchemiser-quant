# Observability Guide

This comprehensive guide covers all aspects of observability in The Alchemiser quantitative trading system, including logging, error handling, monitoring, and debugging.

## Table of Contents

1. [Overview](#overview)
2. [Logging Architecture](#logging-architecture)
3. [Error Categories and Handling](#error-categories-and-handling)
4. [Request Tracking and Correlation](#request-tracking-and-correlation)
5. [Environment-Specific Behavior](#environment-specific-behavior)
6. [CloudWatch Integration](#cloudwatch-integration)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Best Practices](#best-practices)
10. [Development Workflow](#development-workflow)

## Overview

The Alchemiser implements a comprehensive observability strategy designed for production-grade quantitative trading operations. The system provides:

- **Structured logging** with JSON format for production environments
- **Comprehensive error categorization** with automatic classification
- **Request correlation** across all system boundaries
- **CloudWatch-first** logging approach for AWS Lambda deployments
- **Environment-aware** configuration for development vs production

## Logging Architecture

### Logging Formats

The system supports two primary logging formats based on the environment:

#### Production Format (Structured JSON)
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "the_alchemiser.services.trading",
  "message": "Order executed successfully",
  "module": "trading_service_manager",
  "function": "execute_smart_order",
  "line": 156,
  "request_id": "abc123-def456",
  "error_id": "err789-xyz012",
  "symbol": "AAPL",
  "quantity": 100,
  "order_type": "market"
}
```

#### Development Format (Human-readable)
```
2024-01-15 10:30:45,123 - INFO - the_alchemiser.services.trading - [ALCHEMISER] [req_id=abc123-def456] Order executed successfully
```

### Logging Components

#### Core Logging Utilities
- **StructuredFormatter**: Converts log records to JSON with context variables
- **AlchemiserLoggerAdapter**: Adds system prefixes and correlation IDs
- **Context Variables**: Thread-safe storage for request_id and error_id

#### Logger Configuration Functions
```python
# Production logging with CloudWatch-first approach
configure_production_logging(log_level=logging.INFO)

# Test environment with human-readable format
configure_test_logging(log_level=logging.WARNING)

# Development with custom configuration
setup_logging(
    log_level=logging.DEBUG,
    structured_format=False,
    console_level=logging.INFO
)
```

### Environment Detection

The logging system automatically detects the environment and configures appropriately:

```python
# Lambda detection
is_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

# S3 logging control
s3_logging_enabled = os.environ.get("ENABLE_S3_LOGGING", "").lower() in ("1", "true", "yes", "on")
```

## Error Categories and Handling

### Error Categories

The system classifies errors into the following categories for monitoring and alerting:

| Category | Description | Examples | Severity |
|----------|-------------|----------|----------|
| `CRITICAL` | System-level failures that stop all operations | Configuration errors, AWS permission issues | High |
| `TRADING` | Order execution and position validation issues | Insufficient funds, order rejection | High |
| `DATA` | Market data and API connectivity issues | Data provider timeout, invalid prices | Medium |
| `STRATEGY` | Strategy calculation and signal generation issues | Invalid indicators, calculation errors | Medium |
| `CONFIGURATION` | Config, authentication, and setup issues | Missing API keys, invalid settings | High |
| `NOTIFICATION` | Email and alert delivery issues | SMTP errors, template issues | Low |
| `WARNING` | Non-critical issues that don't stop execution | Rate limiting, minor data inconsistencies | Low |

### Error Severity Levels

```python
class ErrorSeverity:
    LOW = "low"       # Minor issues, system continues normally
    MEDIUM = "medium" # Noticeable issues, may impact performance
    HIGH = "high"     # Significant issues, may impact functionality
    CRITICAL = "critical" # Severe issues, system may be unable to operate
```

### Error Handler Usage

```python
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

def risky_trading_operation():
    try:
        # Your trading logic
        return execute_trade()
    except Exception as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            component="OrderService.execute_market_order",
            context="AAPL market order execution",
            additional_data={"symbol": "AAPL", "qty": 100}
        )
        raise StrategyExecutionError(f"Trading operation failed: {e}") from e
```

## Request Tracking and Correlation

### Request ID Management

Request IDs enable end-to-end tracking of operations across all system components:

#### Setting Request IDs at System Boundaries

**1. Lambda Handler (AWS Entry Point)**
```python
def lambda_handler(event, context):
    # Generate correlation ID for the entire request
    correlation_id = generate_request_id()
    set_request_id(correlation_id)
    
    # Extract AWS request ID for additional tracking
    aws_request_id = getattr(context, "aws_request_id", "unknown") if context else "local"
```

**2. CLI Entry Point (Local Development)**
```python
def main(args=None):
    # Set request ID for local CLI sessions
    request_id = generate_request_id()
    set_request_id(request_id)
    logger.info(f"Starting CLI session with request_id: {request_id}")
```

**3. Web/API Endpoints (Future)**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = generate_request_id()
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Context Propagation

Request IDs automatically propagate through:
- All log messages via `StructuredFormatter`
- Error handling via `TradingSystemErrorHandler`
- Nested function calls via thread-local context variables

#### Example Context Usage
```python
from the_alchemiser.infrastructure.logging.logging_utils import set_request_id, set_error_id

# At boundary component
set_request_id("req-trading-session-123")

# In error handling
try:
    execute_trade()
except Exception as e:
    error_id = generate_error_id()
    set_error_id(error_id)
    logger.error(f"Trade execution failed: {e}")
    # Both request_id and error_id will appear in logs
```

## Environment-Specific Behavior

### Production Environment (AWS Lambda)

**Characteristics:**
- JSON structured logging to CloudWatch Logs
- S3 logging disabled by default (opt-in only)
- Reduced console verbosity
- Automatic correlation ID generation

**Configuration:**
```bash
# Required for Lambda detection
AWS_LAMBDA_FUNCTION_NAME=the-alchemiser-v2-lambda

# Optional: Enable S3 logging
ENABLE_S3_LOGGING=true

# Optional: Adjust log level
LOGGING__LEVEL=INFO
```

**Log Output:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "the_alchemiser.services.trading",
  "message": "Market order executed",
  "request_id": "lambda-req-abc123",
  "symbol": "AAPL",
  "quantity": 100
}
```

### Development Environment (Local)

**Characteristics:**
- Human-readable console logging
- Full debug information available
- File logging optional
- Manual request ID management

**Configuration:**
```bash
# Development mode (no Lambda function name)
# AWS_LAMBDA_FUNCTION_NAME not set

# Optional: Enable debug logging
LOGGING__LEVEL=DEBUG
```

**Log Output:**
```
2024-01-15 10:30:45,123 - INFO - the_alchemiser.services.trading - [ALCHEMISER] [req_id=dev-abc123] Market order executed
```

### Test Environment

**Characteristics:**
- Minimal logging (WARNING level)
- Human-readable format
- Suppressed third-party noise
- No file output

**Usage:**
```python
from the_alchemiser.infrastructure.logging.logging_utils import configure_test_logging

# In test setup
configure_test_logging(log_level=logging.WARNING)
```

## CloudWatch Integration

### Log Groups and Retention

The Alchemiser Lambda function logs to:
- **Log Group**: `/aws/lambda/the-alchemiser-v2-lambda`
- **Retention**: 14 days (configurable)
- **Format**: JSON (structured)

### CloudWatch Insights Queries

#### Error Analysis

**1. Error Rate by Category**
```sql
fields @timestamp, level, error_type, message
| filter level = "ERROR"
| stats count() by error_type
| sort count desc
```

**2. Recent Critical Errors**
```sql
fields @timestamp, level, message, component, error_type, request_id
| filter level = "ERROR" and (component like /trading/ or component like /order/)
| sort @timestamp desc
| limit 25
```

**3. Error Correlation by Request ID**
```sql
fields @timestamp, level, message, component, error_id
| filter request_id = "your-request-id-here"
| sort @timestamp asc
```

#### Performance Monitoring

**4. Request Duration Analysis**
```sql
fields @timestamp, @duration, request_id, component
| filter @duration > 5000  # Requests taking more than 5 seconds
| sort @duration desc
| limit 20
```

**5. Trading Operations Timeline**
```sql
fields @timestamp, message, symbol, quantity, order_type
| filter message like /order/ or message like /trade/
| sort @timestamp desc
| limit 100
```

#### Strategy Monitoring

**6. Strategy Signal Analysis**
```sql
fields @timestamp, strategy_type, signal, confidence, target_allocation
| filter strategy_type exists
| stats count() by strategy_type, signal
| sort count desc
```

**7. Portfolio Performance Tracking**
```sql
fields @timestamp, portfolio_value, cash_balance, total_equity
| filter portfolio_value exists
| sort @timestamp desc
| limit 20
```

#### System Health

**8. Lambda Cold Starts**
```sql
fields @timestamp, @duration, @initDuration
| filter @initDuration > 1000  # Cold starts taking more than 1 second
| sort @timestamp desc
| limit 20
```

**9. Memory Usage Warnings**
```sql
fields @timestamp, @maxMemoryUsed, @memorySize, level, message
| filter @maxMemoryUsed / @memorySize > 0.8  # Using more than 80% memory
| sort @timestamp desc
```

**10. High Error Rate Detection**
```sql
fields @timestamp, level
| filter level = "ERROR"
| stats count() by bin(1m)
| sort @timestamp desc
| limit 60  # Last hour in 1-minute bins
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Error Rates**
   - Total errors per hour
   - Errors by category
   - Critical error frequency

2. **Performance Metrics**
   - Request duration trends
   - Lambda cold start frequency
   - Memory usage patterns

3. **Trading Metrics**
   - Order execution success rate
   - Strategy signal generation frequency
   - Portfolio value changes

4. **System Health**
   - Lambda function invocations
   - Log volume and patterns
   - Configuration error frequency

### CloudWatch Alarms

**High Error Rate Alarm**
```yaml
MetricName: ErrorCount
Namespace: AWS/Logs
Dimensions:
  - Name: LogGroupName
    Value: /aws/lambda/the-alchemiser-v2-lambda
Statistic: Sum
Period: 300
EvaluationPeriods: 2
Threshold: 5
ComparisonOperator: GreaterThanThreshold
```

**Lambda Duration Alarm**
```yaml
MetricName: Duration
Namespace: AWS/Lambda
Dimensions:
  - Name: FunctionName
    Value: the-alchemiser-v2-lambda
Statistic: Average
Period: 300
EvaluationPeriods: 3
Threshold: 30000  # 30 seconds
ComparisonOperator: GreaterThanThreshold
```

### Custom Metrics from Logs

Use CloudWatch Metric Filters to extract custom metrics:

**Trading Error Rate Filter**
```json
{
  "filterPattern": "[timestamp, level=\"ERROR\", logger, message, module, function, line, request_id, error_type=\"trading\"]",
  "metricTransformation": {
    "metricName": "TradingErrors",
    "metricNamespace": "Alchemiser/Trading",
    "metricValue": "1"
  }
}
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Missing Logs in CloudWatch

**Symptoms:**
- No logs appearing in CloudWatch
- Empty log streams

**Diagnosis:**
```sql
# Check for any logs from the function
fields @timestamp, @message
| sort @timestamp desc
| limit 10
```

**Solutions:**
- Verify Lambda execution role has CloudWatch permissions
- Check log group exists: `/aws/lambda/the-alchemiser-v2-lambda`
- Ensure Lambda function is being invoked

#### 2. Unstructured Logs in Production

**Symptoms:**
- Logs appear as plain text instead of JSON
- Missing request_id or error_id fields

**Diagnosis:**
```python
# Check logging configuration
import os
print(f"Lambda function: {os.environ.get('AWS_LAMBDA_FUNCTION_NAME')}")
print(f"S3 logging: {os.environ.get('ENABLE_S3_LOGGING')}")
```

**Solutions:**
- Verify `AWS_LAMBDA_FUNCTION_NAME` environment variable is set
- Check `structured_format=True` in production logging config
- Ensure `configure_production_logging()` is called

#### 3. Missing Request Correlation

**Symptoms:**
- request_id missing from logs
- Unable to trace requests end-to-end

**Diagnosis:**
```sql
# Check for logs without request_id
fields @timestamp, @message, request_id
| filter ispresent(request_id) = 0
| sort @timestamp desc
```

**Solutions:**
- Ensure `set_request_id()` is called at entry points
- Verify context variables are properly propagated
- Check for request_id clearing in exception handlers

#### 4. S3 Logging Blocked

**Symptoms:**
- S3 logs not being written despite configuration
- Warning messages about S3 logging blocked

**Diagnosis:**
```sql
# Look for S3 logging warnings
fields @timestamp, @message
| filter @message like /S3 logging blocked/
| sort @timestamp desc
```

**Solutions:**
- Set `ENABLE_S3_LOGGING=true` environment variable
- Verify S3 bucket permissions and credentials
- Check CloudWatch logs for detailed error messages

### Debug Logging

Enable debug logging for detailed troubleshooting:

```python
# Temporary debug configuration
from the_alchemiser.infrastructure.logging.logging_utils import setup_logging
import logging

setup_logging(
    log_level=logging.DEBUG,
    structured_format=True,
    console_level=logging.DEBUG
)
```

## Best Practices

### Logging Best Practices

1. **Use Structured Logging in Production**
   ```python
   # Good: Include context
   logger.info("Order executed", extra={"symbol": "AAPL", "quantity": 100})
   
   # Avoid: Plain text only
   logger.info("Order executed for AAPL")
   ```

2. **Always Set Request IDs at Boundaries**
   ```python
   # At every entry point
   request_id = generate_request_id()
   set_request_id(request_id)
   ```

3. **Include Relevant Context**
   ```python
   # Trading operations
   log_with_context(logger, logging.INFO, "Trade executed", 
                    symbol="AAPL", quantity=100, order_type="market")
   ```

4. **Use Appropriate Log Levels**
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: Normal operation confirmation
   - `WARNING`: Something unexpected but system continues
   - `ERROR`: Serious problem that caused operation to fail
   - `CRITICAL`: System-level failure

### Error Handling Best Practices

1. **Categorize Errors Consistently**
   ```python
   try:
       execute_order()
   except InsufficientFundsError as e:
       # Will be automatically categorized as TRADING
       error_handler.handle_error(e, "OrderService.execute", "Market order")
   ```

2. **Include Error Context**
   ```python
   error_handler.handle_error(
       error=e,
       component="TradingService.execute_order",
       context="AAPL market order execution",
       additional_data={
           "symbol": "AAPL",
           "quantity": 100,
           "account_balance": account.cash
       }
   )
   ```

3. **Set Error IDs for Complex Flows**
   ```python
   try:
       complex_operation()
   except Exception as e:
       error_id = str(uuid.uuid4())
       set_error_id(error_id)
       logger.error(f"Complex operation failed: {e}")
       # Error ID will be included in all subsequent logs
   ```

### Monitoring Best Practices

1. **Monitor Key Business Metrics**
   - Order success rates
   - Strategy performance
   - Portfolio value changes

2. **Set Up Proactive Alerts**
   - Error rate thresholds
   - Performance degradation
   - System health indicators

3. **Use Correlation IDs for Debugging**
   - Always include request_id in error reports
   - Use CloudWatch Insights to trace request flows

4. **Regular Log Analysis**
   - Weekly error pattern reviews
   - Performance trend analysis
   - Capacity planning based on usage patterns

### Security Considerations

1. **Never Log Sensitive Data**
   ```python
   # Good: Log trade details without sensitive info
   logger.info("Order placed", extra={"symbol": "AAPL", "side": "buy"})
   
   # Bad: Never log API keys or account numbers
   # logger.info(f"Using API key: {api_key}")  # DON'T DO THIS
   ```

2. **Sanitize User Inputs**
   ```python
   # Ensure user inputs don't contain sensitive data before logging
   safe_symbol = sanitize_symbol_input(user_symbol)
   logger.info("Processing symbol", extra={"symbol": safe_symbol})
   ```

3. **Use Appropriate Log Retention**
   - Production logs: 30-90 days
   - Debug logs: 7-14 days
   - Security logs: 1+ year

## Development Workflow

### Local Development Setup

1. **Environment Configuration**
   ```bash
   # .env file for local development
   LOGGING__LEVEL=DEBUG
   ALPACA_API_KEY=your_paper_key
   ALPACA_SECRET_KEY=your_paper_secret
   PAPER_TRADING=true
   ```

2. **Initialize Logging**
   ```python
   # In your development script
   from the_alchemiser.infrastructure.logging.logging_utils import setup_logging, set_request_id, generate_request_id
   
   # Set up development logging
   setup_logging(
       log_level=logging.DEBUG,
       structured_format=False,  # Human-readable for development
       console_level=logging.INFO
   )
   
   # Set request ID for session tracking
   request_id = generate_request_id()
   set_request_id(request_id)
   print(f"Development session: {request_id}")
   ```

### Testing Observability

1. **Test Log Output**
   ```python
   def test_logging_includes_context():
       set_request_id("test-req-123")
       logger = get_logger(__name__)
       
       with caplog.record_tuples() as log_capture:
           logger.info("Test message")
           
       # Verify request_id is included
       assert "test-req-123" in log_capture[0].message
   ```

2. **Test Error Categorization**
   ```python
   def test_error_categorization():
       handler = TradingSystemErrorHandler()
       
       # Test trading error classification
       trading_error = InsufficientFundsError("Not enough cash")
       category = handler.categorize_error(trading_error)
       assert category == ErrorCategory.TRADING
   ```

### Debugging Production Issues

1. **Find Related Logs**
   ```sql
   # Use request_id to find all related logs
   fields @timestamp, level, message, component
   | filter request_id = "problematic-request-id"
   | sort @timestamp asc
   ```

2. **Analyze Error Patterns**
   ```sql
   # Look for recurring errors
   fields @timestamp, error_type, message
   | filter level = "ERROR"
   | stats count() by error_type, message
   | sort count desc
   ```

3. **Performance Analysis**
   ```sql
   # Identify slow operations
   fields @timestamp, @duration, component, message
   | filter @duration > 10000
   | sort @duration desc
   ```

This comprehensive observability guide provides all the tools and knowledge needed to effectively monitor, debug, and maintain The Alchemiser trading system across all environments.