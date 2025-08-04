# Enhanced Error Handling and Retry Policy Implementation

## Overview

This document describes the comprehensive error handling and retry policy enhancements implemented for The Alchemiser trading system to enable truly autonomous operation with detailed error reporting.

## Key Improvements

### 1. Enhanced Error Handling System

#### New Error Handler (`core/error_handler.py`)

- **Categorized Error Classification**: Automatically categorizes errors into specific types:
  - `CRITICAL`: System-level failures that stop all operations
  - `TRADING`: Order execution, position validation issues
  - `DATA`: Market data, API connectivity issues  
  - `STRATEGY`: Strategy calculation, signal generation issues
  - `CONFIGURATION`: Config, authentication, setup issues
  - `NOTIFICATION`: Email, alert delivery issues
  - `WARNING`: Non-critical issues that don't stop execution

- **Detailed Error Context**: Captures comprehensive error information:
  - Error type and message
  - Component where error occurred
  - Context of the operation
  - Additional debugging data
  - Suggested remediation actions
  - Full stack trace
  - Timestamp

- **Smart Error Reporting**:
  - Generates structured error reports with specific action recommendations
  - Prioritizes errors by severity for email subject lines
  - Includes all relevant context for debugging

#### Error Integration Points

- **Main Trading Loop** (`main.py`): Catches and categorizes top-level execution errors
- **Lambda Handler** (`lambda_handler.py`): Enhanced AWS Lambda error handling with context
- **Trading Engine** (`execution/trading_engine.py`): Specific trading operation error handling
- **Account Operations**: Detailed error handling for account info and position retrieval

### 2. Reduced EventBridge Retry Policy

#### Template Changes (`template.yaml`)

- **Retry Reduction**: Reduced `MaximumRetryAttempts` from default (185) to 1
- **Dead Letter Queue**: Added SQS Dead Letter Queue for failed executions
- **Fail-Fast Design**: Prevents runaway retry loops that could trigger hundreds of executions
- **Error Visibility**: Failed executions are captured in DLQ for investigation

```yaml
RetryPolicy:
  MaximumRetryAttempts: 1  # Reduced from default (185)
DeadLetterConfig:
  Arn: !GetAtt TradingSystemDLQ.Arn
```

### 3. Enhanced Email Notifications

#### Detailed Error Reports

- **Structured Format**: Comprehensive error reports with categorized sections
- **Action-Oriented**: Each error includes specific suggested actions
- **Priority-Based**: Email subjects indicate severity (CRITICAL, TRADING, SYSTEM)
- **Rich HTML Formatting**: Professional email templates with proper styling

#### Example Error Email Content

```
Subject: [URGENT] The Alchemiser - 🚨 CRITICAL Error Report

# Trading System Error Report

**Execution Time:** 2025-01-04 15:30:00 UTC
**Total Errors:** 2

## 💰 TRADING ERRORS
These errors affected trade execution:

**Component:** AlpacaClient.submit_order
**Context:** order placement  
**Error:** Failed to place order for AAPL
**Action:** Verify trading permissions, account status, and market hours
**Additional Data:** {'symbol': 'AAPL', 'qty': 100, 'side': 'buy'}

## 📊 DATA ERRORS
**Component:** DataProvider.get_current_price
**Context:** price fetching
**Error:** Unable to fetch current price
**Action:** Check market data sources, API limits, and network connectivity
```

### 4. Error Categories and Suggested Actions

| Error Type | Suggested Actions |
|------------|-------------------|
| **InsufficientFundsError** | Check account balance and reduce position sizes or add funds |
| **OrderExecutionError** | Verify market hours, check symbol validity, and ensure order parameters are correct |
| **PositionValidationError** | Check current positions and ensure selling quantities don't exceed holdings |
| **MarketDataError** | Check API connectivity and data provider status |
| **ConfigurationError** | Verify configuration settings and API credentials |
| **StrategyExecutionError** | Review strategy logic and input data for calculation errors |

## Implementation Benefits

### 1. Autonomous Operation

- **Self-Diagnosing**: System provides detailed error analysis without manual log review
- **Actionable Insights**: Each error includes specific steps to resolve the issue
- **Fail-Safe**: Reduced retries prevent cascade failures from single errors

### 2. Operational Reliability  

- **Predictable Behavior**: Known retry limits prevent unexpected behavior
- **Resource Protection**: Prevents excessive API calls or Lambda invocations
- **Quick Recovery**: Specific error guidance enables faster resolution

### 3. Monitoring and Debugging

- **Comprehensive Context**: Full error context captured for each failure
- **Categorized Reporting**: Easy identification of error patterns and root causes
- **Historical Tracking**: Dead letter queue maintains record of failed executions

## Testing Results

The error handling system has been thoroughly tested with:

✅ **Error Categorization**: All exception types correctly classified  
✅ **Structured Reporting**: Detailed reports generated with proper formatting  
✅ **Email Integration**: HTML templates render correctly with structured content  
✅ **Notification Triggering**: Automatic email sending based on error severity  
✅ **Context Preservation**: All error details and debugging data captured  

## Usage

The enhanced error handling is automatically integrated into all trading operations. No manual configuration is required.

### For Developers

```python
from the_alchemiser.core.error_handler import handle_trading_error

# In any trading component
try:
    risky_operation()
except Exception as e:
    handle_trading_error(
        error=e,
        context="specific operation description",
        component="ComponentName.method_name",
        additional_data={"relevant": "debugging_info"}
    )
```

### For Operations

- Monitor email alerts for detailed error reports
- Check Dead Letter Queue in AWS SQS for failed executions  
- Review error patterns to identify systemic issues
- Use suggested actions for quick problem resolution

## AWS Resources Added

1. **SQS Dead Letter Queue**: `the-alchemiser-dlq`
   - 14-day message retention
   - Captures failed Lambda executions

2. **Enhanced IAM Permissions**:
   - Scheduler role can send messages to DLQ
   - Maintains security while enabling error tracking

3. **Reduced Retry Policy**:
   - Maximum 1 retry attempt
   - Prevents runaway executions
   - Fast failure detection

This implementation ensures The Alchemiser can operate autonomously while providing comprehensive error visibility and actionable guidance for any issues that arise.
