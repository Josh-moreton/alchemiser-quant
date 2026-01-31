# Daily P&L Capture Lambda

This Lambda function runs daily to capture the previous day's portfolio P&L data from Alpaca and store it in DynamoDB.

## Purpose

Provides a canonical source of truth for historical daily P&L that:
- Tracks equity levels
- Records P&L adjusted for deposits/withdrawals  
- Enables fast queries of historical performance
- Serves as single data source for notifications and reports

## Trigger

EventBridge schedule: Daily at 9:00 PM ET (after market close + 4 hour buffer)

## Configuration

Environment variables:
- `DAILY_PNL_TABLE_NAME`: DynamoDB table for storing daily PnL records
- `ENVIRONMENT`: Current environment (dev/staging/prod)
- Alpaca credentials (from Secrets Manager)

## Backfilling

To backfill historical data, invoke with:
```json
{
  "target_date": "2025-01-15"
}
```
