# CloudWatch Logging and Insights Guide

This guide covers how to monitor and analyze The Alchemiser's production logs using AWS CloudWatch Logs and CloudWatch Insights.

## Production Logging Architecture

The Alchemiser uses a **CloudWatch-first** logging approach in production (Lambda environments):

### Default Behavior
- **Lambda**: JSON-structured logs sent to CloudWatch Logs by default
- **Development**: Human-readable logs to console
- **S3 Logging**: Explicit opt-in only with `ENABLE_S3_LOGGING=true`

### Log Format (Production)
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

## CloudWatch Log Groups

The Alchemiser Lambda function logs to:
- **Log Group**: `/aws/lambda/the-alchemiser-v2-lambda`
- **Retention**: 14 days (configurable)
- **Format**: JSON (structured)

## CloudWatch Insights Queries

### Error Analysis

#### 1. Error Rate by Category
```sql
fields @timestamp, level, error_type, message
| filter level = "ERROR"
| stats count() by error_type
| sort count desc
```

#### 2. Recent Errors with Context
```sql
fields @timestamp, level, message, component, error_type, request_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 50
```

#### 3. Critical Trading Errors
```sql
fields @timestamp, message, component, symbol, quantity, error_type
| filter level = "ERROR" and (component like /trading/ or component like /order/)
| sort @timestamp desc
| limit 25
```

### Performance Monitoring

#### 4. Request Duration Analysis
```sql
fields @timestamp, @duration, request_id, component
| filter @duration > 5000  # Requests taking more than 5 seconds
| sort @duration desc
| limit 20
```

#### 5. Trading Operations Timeline
```sql
fields @timestamp, message, symbol, quantity, order_type
| filter message like /order/ or message like /trade/
| sort @timestamp desc
| limit 100
```

### Strategy Monitoring

#### 6. Strategy Signal Analysis
```sql
fields @timestamp, strategy_type, signal, confidence, target_allocation
| filter strategy_type exists
| stats count() by strategy_type, signal
| sort count desc
```

#### 7. Portfolio Performance Tracking
```sql
fields @timestamp, portfolio_value, cash_balance, total_equity
| filter portfolio_value exists
| sort @timestamp desc
| limit 20
```

### Error Correlation

#### 8. Error Correlation by Request ID
```sql
# Find all log entries for a specific request
fields @timestamp, level, message, component, error_id
| filter request_id = "your-request-id-here"
| sort @timestamp asc
```

#### 9. Error Patterns by Time
```sql
fields @timestamp, level, error_type, component
| filter level = "ERROR"
| stats count() by bin(5m), error_type
| sort @timestamp desc
```

### Market Data Issues

#### 10. Data Provider Errors
```sql
fields @timestamp, level, message, symbol, error_type
| filter component like /market_data/ and level = "ERROR"
| stats count() by error_type, symbol
| sort count desc
```

#### 11. WebSocket Connection Issues
```sql
fields @timestamp, level, message, component
| filter component like /streaming/ or message like /websocket/
| filter level in ["ERROR", "WARNING"]
| sort @timestamp desc
```

### Alert-Worthy Queries

#### 12. High Error Rate Detection
```sql
fields @timestamp, level
| filter level = "ERROR"
| stats count() by bin(1m)
| sort @timestamp desc
| limit 60  # Last hour in 1-minute bins
```

#### 13. Lambda Cold Starts
```sql
fields @timestamp, @duration, @initDuration
| filter @initDuration > 1000  # Cold starts taking more than 1 second
| sort @timestamp desc
| limit 20
```

#### 14. Memory Usage Warnings
```sql
fields @timestamp, @maxMemoryUsed, @memorySize, level, message
| filter @maxMemoryUsed / @memorySize > 0.8  # Using more than 80% memory
| sort @timestamp desc
```

## Setting Up Alerts

### CloudWatch Alarms

Create CloudWatch Alarms for:

1. **High Error Rate**
   - Metric: Error log entries
   - Threshold: > 5 errors in 5 minutes
   - Action: SNS notification

2. **Lambda Failures**
   - Metric: Lambda errors
   - Threshold: > 1 failure in 1 minute
   - Action: SNS + SQS DLQ investigation

3. **Long Execution Times**
   - Metric: Lambda duration
   - Threshold: > 30 seconds
   - Action: Performance investigation

### Log-based Metrics

Create custom metrics from logs:

```sql
# Error rate metric filter
[timestamp, request_id, level="ERROR"]
```

```sql
# Trading volume metric filter
[timestamp, symbol, quantity, order_type="market"]
```

## Log Retention and Costs

### Retention Policy
- **Development**: 7 days
- **Production**: 14 days
- **Critical Events**: Export to S3 for long-term storage

### Cost Optimization
- Use log retention policies
- Archive old logs to S3 (when S3 logging is enabled)
- Filter noisy debug logs in production

## Troubleshooting Common Issues

### 1. Missing Logs
**Symptom**: No logs appearing in CloudWatch
**Solution**: 
- Check Lambda execution role permissions
- Verify log group exists: `/aws/lambda/the-alchemiser-v2-lambda`
- Check Lambda function configuration

### 2. Structured Logging Not Working
**Symptom**: Logs appear as plain text instead of JSON
**Solution**:
- Verify `structured_format=True` in production logging config
- Check `AWS_LAMBDA_FUNCTION_NAME` environment variable is set

### 3. S3 Logging Unexpectedly Disabled
**Symptom**: S3 logs not being written despite configuration
**Solution**:
- Ensure `ENABLE_S3_LOGGING=true` environment variable is set
- Check CloudWatch logs for S3 logging warning messages
- Verify S3 bucket permissions and credentials

### 4. High Log Volume
**Symptom**: Excessive logging costs
**Solution**:
- Adjust log levels in production (`LOGGING__LEVEL=WARNING`)
- Review and suppress noisy third-party loggers
- Implement log sampling for high-frequency events

## Best Practices

1. **Use Structured Logging**: Always include relevant context (request_id, symbol, etc.)
2. **Correlation IDs**: Track request flows with request_id
3. **Error Context**: Include error_id for detailed error investigation
4. **Performance Metrics**: Log execution times and memory usage
5. **Security**: Never log sensitive data (API keys, account numbers)
6. **Cost Control**: Set appropriate log retention and levels

## Environment Variables

### Production Logging Control
```bash
# Required in Lambda
AWS_LAMBDA_FUNCTION_NAME=the-alchemiser-v2-lambda

# Optional: Enable S3 logging
ENABLE_S3_LOGGING=true

# Optional: Adjust log level
LOGGING__LEVEL=INFO

# Optional: S3 logging configuration (via config)
LOGGING__S3_LOG_URI=s3://your-bucket/logs/alchemiser/
```

## Example Monitoring Dashboard

Create a CloudWatch Dashboard with:

1. **Lambda Metrics**: Duration, Errors, Invocations
2. **Error Rate**: Custom metric from log filters
3. **Trading Volume**: Custom metric from trading logs  
4. **Recent Errors**: Log insights widget with error query
5. **Performance**: Duration and memory usage trends

This provides comprehensive monitoring of The Alchemiser's production environment with CloudWatch-native tools.