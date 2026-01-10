# Deployment Checklist for Dynamic Strategy Weighting

## Pre-Deployment Verification

### Code Quality
- [x] All files pass linting (ruff)
- [x] SAM template validates successfully
- [x] Documentation complete (README, examples, summary)
- [x] No hardcoded secrets or sensitive data

### Infrastructure Requirements
- [ ] Verify `TRADE_LEDGER__TABLE_NAME` environment variable is set
- [ ] Verify sufficient trade history exists (90+ days recommended)
- [ ] Confirm at least 5 closed lots per strategy for valid Sharpe calculation

## Deployment Steps

### 1. Deploy to Dev Environment
```bash
# From repository root
make deploy-dev
```

Expected outputs:
- `StrategyWeightsTable` DynamoDB table created
- `StrategyWeightingFunction` Lambda deployed
- `StrategyWeightingSchedule` EventBridge schedule created (Sundays 6 PM ET)

### 2. Manual Testing

#### Test 1: Manual Lambda Invocation
```bash
aws lambda invoke \
  --function-name alchemiser-dev-strategy-weighting \
  --payload '{"source": "manual_test"}' \
  /tmp/weighting-response.json

cat /tmp/weighting-response.json
```

Expected response:
```json
{
  "statusCode": 200,
  "body": "Dynamic weights updated for N strategies",
  "correlation_id": "..."
}
```

#### Test 2: Verify DynamoDB Storage
```bash
aws dynamodb query \
  --table-name alchemiser-dev-strategy-weights \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"WEIGHTS#CURRENT"}}' \
  --scan-index-forward false \
  --limit 1
```

Expected: Most recent weight record with metadata

#### Test 3: Check CloudWatch Logs
```bash
aws logs tail /aws/lambda/alchemiser-dev-strategy-weighting --follow
```

Look for:
- "Strategy weighting Lambda invoked"
- "Calculated Sharpe ratios for N strategies"
- "Dynamic weights updated successfully"

#### Test 4: Verify Strategy Config Integration
```python
# In Python shell with PYTHONPATH set to layers/shared
from the_alchemiser.shared.config.strategy_profiles import get_strategy_profile

profile = get_strategy_profile(stage="dev", use_dynamic=True)
print(f"Dynamic weights active: {profile.is_dynamic}")
print(f"Allocations: {profile.allocations}")
```

Expected: `is_dynamic=True` if weights were successfully loaded

### 3. Monitor First Scheduled Execution

Wait for first Sunday 6 PM ET execution:
- Check CloudWatch Logs for successful execution
- Verify new weights stored in DynamoDB
- Confirm no errors in Lambda metrics

### 4. Validation Checks

#### Strategy Orchestrator Integration
Monitor next trading execution (Monday morning) to verify:
- [ ] Orchestrator uses dynamic weights if available
- [ ] Falls back to baseline if dynamic weights unavailable
- [ ] No errors in strategy execution flow

#### Weight Adjustment Sanity Checks
```bash
# Query most recent weights
aws dynamodb get-item \
  --table-name alchemiser-dev-strategy-weights \
  --key '{"PK":{"S":"WEIGHTS#CURRENT"},"SK":{"S":"<latest-timestamp>"}}' \
  --query 'Item.weights'
```

Verify:
- [ ] All weights sum to ~1.0 (100%)
- [ ] No weight < 0.5x or > 2.0x of baseline
- [ ] Highest Sharpe strategy has highest weight
- [ ] Lowest Sharpe strategy has lowest weight

## Production Deployment (After Dev Validation)

### Prerequisites
- [ ] Dev deployment successful and stable for 1+ week
- [ ] No errors in dev CloudWatch logs
- [ ] Weight adjustments align with expectations
- [ ] Strategy orchestrator confirmed working with dynamic weights

### Deploy to Production
```bash
make deploy  # or make deploy v=x.y.z for versioned release
```

### Post-Production Monitoring

Week 1:
- [ ] Daily check of CloudWatch logs for errors
- [ ] Verify weekly weight adjustments occur as scheduled
- [ ] Monitor trading performance for anomalies
- [ ] Compare dynamic vs baseline allocations

Week 2-4:
- [ ] Weekly review of Sharpe ratios and weight adjustments
- [ ] Validate weight constraints are working as intended
- [ ] Check for any edge cases or unexpected behavior

## Rollback Procedure

If issues arise, dynamic weighting can be disabled without code changes:

### Option 1: Disable Lambda Schedule (Temporary)
```bash
aws scheduler update-schedule \
  --name alchemiser-prod-strategy-weighting \
  --state DISABLED
```

### Option 2: Delete Dynamic Weights (Immediate Fallback)
```bash
aws dynamodb delete-item \
  --table-name alchemiser-prod-strategy-weights \
  --key '{"PK":{"S":"WEIGHTS#CURRENT"},"SK":{"S":"<timestamp>"}}'
```

System will automatically fall back to baseline allocations.

### Option 3: Redeploy Without Changes (Full Rollback)
```bash
# Revert to previous commit
git revert <commit-hash>
make deploy
```

## Success Criteria

✅ Lambda executes successfully on schedule  
✅ Sharpe ratios calculated for all active strategies  
✅ Weights adjusted within constraints (0.5x-2.0x)  
✅ Dynamic weights stored in DynamoDB with metadata  
✅ Strategy orchestrator integrates dynamic weights  
✅ Graceful fallback to baseline on errors  
✅ No impact to existing trading operations  
✅ CloudWatch logs show clear audit trail  

## Support & Troubleshooting

### Common Issues

**Issue**: "No Sharpe ratios calculated - insufficient trade history"
- **Cause**: Strategies have <5 closed lots in lookback period
- **Solution**: Wait for more trade history to accumulate, or reduce LOOKBACK_DAYS

**Issue**: Lambda timeout (>300s)
- **Cause**: Large number of closed lots to process
- **Solution**: Increase Lambda timeout or optimize Sharpe calculation

**Issue**: Dynamic weights not loaded by strategy orchestrator
- **Cause**: STRATEGY_WEIGHTS__TABLE_NAME not set or DynamoDB permissions missing
- **Solution**: Verify environment variable and IAM role permissions

### Monitoring Queries

CloudWatch Logs Insights:
```
# Recent weight adjustments
fields @timestamp, correlation_id, event, message
| filter event = "Dynamic weights updated successfully"
| sort @timestamp desc
| limit 10

# Sharpe calculation errors
fields @timestamp, strategy_name, error_type, message
| filter level = "error" and module = "sharpe_calculator"
| sort @timestamp desc

# Weight adjustment history
fields @timestamp, correlation_id, message
| filter message like /Weight adjustments applied/
| sort @timestamp desc
```

### Contact
For issues or questions, check:
- CloudWatch Logs: `/aws/lambda/alchemiser-{stage}-strategy-weighting`
- DynamoDB Table: `alchemiser-{stage}-strategy-weights`
- Lambda Function: `alchemiser-{stage}-strategy-weighting`
