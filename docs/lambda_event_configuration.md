# Lambda Event-Driven Trading Modes

The Alchemiser Lambda handler now supports multiple trading modes triggered by different event configurations. This allows you to run paper trading, live trading, or signal analysis using a single Lambda function with different event payloads.

## 🎯 Overview

The enhanced Lambda handler can execute different modes based on the event payload:

- **Paper Trading**: Safe testing mode with simulated trades
- **Live Trading**: Real money trading with actual positions
- **Signal Analysis**: Display signals without executing any trades

## 📋 Event Structure

```json
{
    "mode": "trade" | "bot",           // Required: Operation mode
    "trading_mode": "paper" | "live",  // Optional: Trading mode (default: live for backward compatibility)
    "ignore_market_hours": boolean     // Optional: Override market hours check (default: false)
}
```

## 📚 Event Examples

### Paper Trading Event

```json
{
    "mode": "trade",
    "trading_mode": "paper"
}
```

### Live Trading Event

```json
{
    "mode": "trade", 
    "trading_mode": "live"
}
```

### Signal Analysis Event

```json
{
    "mode": "bot"
}
```

### Testing Event (Ignore Market Hours)

```json
{
    "mode": "trade",
    "trading_mode": "paper",
    "ignore_market_hours": true
}
```

### Empty Event (Backward Compatibility)

```json
{}
```

*Defaults to live trading mode for existing deployments*

## 🛠️ CloudWatch Events Configuration

### 1. Paper Trading Schedule (Daily at 9:45 AM EST)

```json
{
    "Rules": [
        {
            "Name": "AlchemiserPaperTradingDaily",
            "ScheduleExpression": "cron(45 14 ? * MON-FRI *)",
            "State": "ENABLED",
            "Targets": [
                {
                    "Id": "AlchemiserPaperTarget",
                    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser",
                    "Input": "{\"mode\": \"trade\", \"trading_mode\": \"paper\"}"
                }
            ]
        }
    ]
}
```

### 2. Live Trading Schedule (Daily at 9:45 AM EST)

```json
{
    "Rules": [
        {
            "Name": "AlchemiserLiveTradingDaily", 
            "ScheduleExpression": "cron(45 14 ? * MON-FRI *)",
            "State": "ENABLED",
            "Targets": [
                {
                    "Id": "AlchemiserLiveTarget",
                    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser",
                    "Input": "{\"mode\": \"trade\", \"trading_mode\": \"live\"}"
                }
            ]
        }
    ]
}
```

### 3. Signal Analysis Schedule (Multiple times daily)

```json
{
    "Rules": [
        {
            "Name": "AlchemiserSignalAnalysis",
            "ScheduleExpression": "cron(0 9,12,15 ? * MON-FRI *)",
            "State": "ENABLED", 
            "Targets": [
                {
                    "Id": "AlchemiserSignalTarget",
                    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser",
                    "Input": "{\"mode\": \"bot\"}"
                }
            ]
        }
    ]
}
```

## 🔧 AWS CLI Configuration Commands

### Create Paper Trading Rule

```bash
aws events put-rule \
    --name "AlchemiserPaperTradingDaily" \
    --schedule-expression "cron(45 14 ? * MON-FRI *)" \
    --description "Daily paper trading at 9:45 AM EST"

aws events put-targets \
    --rule "AlchemiserPaperTradingDaily" \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser","Input"='{"mode": "trade", "trading_mode": "paper"}'
```

### Create Live Trading Rule

```bash
aws events put-rule \
    --name "AlchemiserLiveTradingDaily" \
    --schedule-expression "cron(45 14 ? * MON-FRI *)" \
    --description "Daily live trading at 9:45 AM EST"

aws events put-targets \
    --rule "AlchemiserLiveTradingDaily" \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser","Input"='{"mode": "trade", "trading_mode": "live"}'
```

### Create Signal Analysis Rule

```bash
aws events put-rule \
    --name "AlchemiserSignalAnalysis" \
    --schedule-expression "cron(0 9,12,15 ? * MON-FRI *)" \
    --description "Signal analysis at 9 AM, 12 PM, and 3 PM EST"

aws events put-targets \
    --rule "AlchemiserSignalAnalysis" \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT:function:the-alchemiser","Input"='{"mode": "bot"}'
```

## 🔍 Lambda Response Format

The enhanced handler returns detailed status information:

```json
{
    "status": "success" | "failed",
    "mode": "trade" | "bot",
    "trading_mode": "paper" | "live" | "n/a", 
    "message": "Human-readable status message",
    "request_id": "Lambda request ID"
}
```

### Example Responses

**Successful Paper Trading:**

```json
{
    "status": "success",
    "mode": "trade", 
    "trading_mode": "paper",
    "message": "Paper trading completed successfully",
    "request_id": "12345-abcde-67890"
}
```

**Failed Live Trading:**

```json
{
    "status": "failed",
    "mode": "trade",
    "trading_mode": "live", 
    "message": "Live trading failed",
    "request_id": "12345-abcde-67890"
}
```

**Successful Signal Analysis:**

```json
{
    "status": "success",
    "mode": "bot",
    "trading_mode": "n/a",
    "message": "Signal analysis completed successfully", 
    "request_id": "12345-abcde-67890"
}
```

## 🔒 Security Considerations

1. **Environment Variables**: Ensure all required secrets are configured:
   - `ALPACA_KEY` and `ALPACA_SECRET` for trading
   - `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` for notifications
   - Other configuration as needed

2. **IAM Permissions**: Lambda execution role needs:
   - CloudWatch Logs permissions for logging
   - S3 permissions if using S3 for data storage
   - Any other AWS services your trading bot uses

3. **Event Validation**: The handler validates all event parameters and defaults to safe values

## 🧪 Testing

### Local Testing

```python
from the_alchemiser.lambda_handler import lambda_handler

# Test paper trading
paper_event = {"mode": "trade", "trading_mode": "paper"}
result = lambda_handler(paper_event)
print(result)

# Test signal analysis
signal_event = {"mode": "bot"}  
result = lambda_handler(signal_event)
print(result)
```

### Lambda Console Testing

Use the AWS Lambda console test feature with the event examples above.

## 🔄 Migration from Old Handler

The new handler is backward compatible:

- Empty events default to live trading (existing behavior)
- All existing CloudWatch triggers continue to work
- New event-driven functionality can be added incrementally

## 📖 Command Line Equivalents

| Event | Command Line Equivalent |
|-------|------------------------|
| `{"mode": "trade", "trading_mode": "paper"}` | `python main.py trade` |
| `{"mode": "trade", "trading_mode": "live"}` | `python main.py trade --live` |
| `{"mode": "bot"}` | `python main.py bot` |
| `{"mode": "trade", "trading_mode": "paper", "ignore_market_hours": true}` | `python main.py trade --ignore-market-hours` |

## 🚀 Next Steps

1. **Deploy the updated Lambda function**
2. **Configure CloudWatch Events** for your desired trading schedule
3. **Test with paper trading** before enabling live trading
4. **Monitor CloudWatch Logs** for execution details
5. **Set up CloudWatch Alarms** for failure notifications
