# Deployment and Incident Response Runbook
**Service**: The Alchemiser Quantitative Trading System  
**Last Updated**: 2024-12-19  
**On-Call Contact**: [Your Team Email/Slack Channel]

---

## Quick Reference

| Scenario | Command | Duration |
|----------|---------|----------|
| Manual deploy (dev) | `gh workflow run cd.yml -f environment=dev` | ~5 min |
| Manual deploy (prod) | `gh workflow run cd.yml -f environment=prod` | ~8 min (with canary) |
| Emergency rollback | See [Rollback Procedure](#rollback-procedure) | ~10 min |
| View logs | `sam logs -n TradingSystemFunction --tail` | Real-time |
| Disable scheduler | See [Emergency Disable](#emergency-disable) | ~30 sec |
| Rotate API keys | See [Key Rotation](#key-rotation) | ~5 min |

---

## Architecture Overview

```
GitHub Actions (CD workflow)
    ↓ (OIDC assume role)
AWS IAM Role (GitHubActions-AlchemiserDeploy)
    ↓ (sam deploy)
CloudFormation Stack (the-alchemiser-v2-{dev|prod})
    ├─ Lambda Function (the-alchemiser-v2-lambda-{stage})
    │   └─ Alias: live (with traffic shifting)
    ├─ Lambda Layer (dependencies-{stage})
    ├─ EventBridge Schedule (daily 9:35 AM ET)
    ├─ SQS Dead Letter Queue (DLQ)
    └─ CloudWatch Alarms (Errors, Duration, Throttles)
        └─ Auto-rollback on alarm breach
```

**Key Concepts**:
- **Alias**: Lambda version pointer (e.g., `live` alias → version 42)
- **Canary Deployment**: 10% traffic to new version for 5 min, then 100% if alarms pass
- **Auto-Rollback**: If CloudWatch alarms trigger during canary, CodeDeploy reverts to previous version

---

## Standard Procedures

### 1. Manual Deployment

#### Dev Environment
```bash
# Trigger CD workflow for dev via GitHub CLI
gh workflow run cd.yml -f environment=dev

# Or via GitHub UI:
# Actions → CD → Run workflow → Select "dev"
```

**Prerequisites**:
- CI workflow passed on main branch (if deploying from main)
- No uncommitted secrets in GitHub Secrets

**Expected Duration**: ~5 minutes  
**Validation**: Check Lambda console shows new version published

#### Prod Environment
```bash
# Trigger CD workflow for prod
gh workflow run cd.yml -f environment=prod

# Or via GitHub UI:
# Actions → CD → Run workflow → Select "prod"
```

**Prerequisites**:
- Code is on `main` branch or has a GitHub release tag
- Manual approval (if GitHub Environment protection rules configured)
- CloudWatch alarms are healthy (no existing incidents)

**Expected Duration**: ~8 minutes (includes 5 min canary period)  
**Validation**: 
1. Check CodeDeploy deployment succeeds
2. Verify alias points to new version: `aws lambda get-alias --function-name the-alchemiser-v2-lambda-prod --name live`
3. Check CloudWatch Logs for new invocations

---

### 2. Rollback Procedure

**When to Rollback**:
- Lambda errors spike after deployment
- Trading logic produces incorrect orders
- CloudWatch alarms fire but auto-rollback failed
- Manual testing reveals critical bug

#### Automatic Rollback (Preferred)
CodeDeploy auto-rollback is enabled for prod deployments. If CloudWatch alarms trigger during canary:
1. CodeDeploy automatically shifts traffic back to previous version
2. Deployment status shows "FAILED" with reason "Alarm triggered"
3. Check CodeDeploy console: https://console.aws.amazon.com/codesuite/codedeploy/deployments

**No manual action required** unless auto-rollback fails.

#### Manual Rollback (If Auto-Rollback Fails)

**Option A: Update Alias** (Fast, but requires knowing previous version)
```bash
# 1. Get current alias version
CURRENT_VERSION=$(aws lambda get-alias \
  --function-name the-alchemiser-v2-lambda-prod \
  --name live \
  --query 'FunctionVersion' \
  --output text)

echo "Current version: $CURRENT_VERSION"

# 2. List recent versions to find previous
aws lambda list-versions-by-function \
  --function-name the-alchemiser-v2-lambda-prod \
  --max-items 10 \
  --query 'Versions[*].[Version,LastModified]' \
  --output table

# 3. Update alias to previous version (e.g., if current is 43, rollback to 42)
PREVIOUS_VERSION=$((CURRENT_VERSION - 1))

aws lambda update-alias \
  --function-name the-alchemiser-v2-lambda-prod \
  --name live \
  --function-version $PREVIOUS_VERSION

echo "Rolled back to version $PREVIOUS_VERSION"
```

**Duration**: ~30 seconds  
**Risk**: LOW (previous version is already deployed and tested)

**Option B: Redeploy Previous Commit** (Slower, but safer)
```bash
# 1. Find the last known good commit
git log --oneline --decorate

# 2. Checkout that commit (e.g., abc1234)
git checkout abc1234

# 3. Trigger manual deploy
gh workflow run cd.yml -f environment=prod

# 4. Wait for deployment to complete (~8 min with canary)

# 5. Return to main branch
git checkout main
```

**Duration**: ~10 minutes (includes canary period)  
**Risk**: LOW (full CI/CD pipeline validation)

#### Post-Rollback Steps
1. **Notify team**: Post in Slack/email with incident summary
2. **Investigate root cause**: Review CloudWatch Logs for errors
3. **Create bug ticket**: Document issue and assign for fix
4. **Update deployment notes**: Add to next release changelog

---

### 3. Emergency Disable

**Scenario**: Critical bug discovered; need to **immediately stop** automated trading until fix is ready.

#### Disable EventBridge Schedule
```bash
# Option 1: Via AWS CLI
aws scheduler update-schedule \
  --name the-alchemiser-daily-trading-prod \
  --state DISABLED

# Option 2: Via AWS Console
# EventBridge → Schedules → the-alchemiser-daily-trading-prod → Actions → Disable
```

**Duration**: ~30 seconds  
**Effect**: Lambda will not be invoked by schedule; manual invocations still work

#### Re-Enable After Fix
```bash
aws scheduler update-schedule \
  --name the-alchemiser-daily-trading-prod \
  --state ENABLED
```

---

### 4. Key Rotation

**When to Rotate**:
- Scheduled quarterly rotation (security best practice)
- Suspected key compromise
- Leaving team member had access to keys

#### Rotate Alpaca API Keys
```bash
# 1. Generate new keys in Alpaca dashboard
# https://app.alpaca.markets/paper/account/keys (for paper trading)
# https://app.alpaca.markets/account/keys (for live trading)

# 2. Update GitHub Secrets (requires GitHub admin access)
gh secret set ALPACA_KEY --body "NEW_KEY_HERE"
gh secret set ALPACA_SECRET --body "NEW_SECRET_HERE"

# 3. Trigger manual deploy to update Lambda env vars
gh workflow run cd.yml -f environment=prod

# 4. Wait for deployment to complete (~8 min)

# 5. Verify Lambda can authenticate with new keys
# Check next scheduled run or trigger manual test:
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-prod \
  --payload '{"mode": "test"}' \
  response.json

# 6. Delete old keys from Alpaca dashboard
```

**Duration**: ~10 minutes (excluding Alpaca dashboard steps)  
**Downtime**: ~5 minutes (during canary deployment)

#### Rotate Email Password
```bash
# 1. Generate new app-specific password from email provider
# (e.g., iCloud Mail: https://appleid.apple.com/account/manage)

# 2. Update GitHub Secret
gh secret set EMAIL__PASSWORD --body "NEW_PASSWORD_HERE"

# 3. Redeploy (same as above)
```

---

## Monitoring & Debugging

### View Real-Time Logs
```bash
# Tail logs (auto-refreshes)
sam logs -n TradingSystemFunction --tail

# Or via AWS CLI
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-prod --follow

# Filter for errors only
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-prod --follow --filter-pattern "ERROR"
```

### Check CloudWatch Alarms
```bash
# List all alarms for the trading system
aws cloudwatch describe-alarms \
  --alarm-name-prefix the-alchemiser \
  --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
  --output table
```

**Expected States**:
- `OK`: Alarm is healthy
- `ALARM`: Threshold breached; check StateReason
- `INSUFFICIENT_DATA`: Not enough data points (normal for new deployments)

### Check Dead Letter Queue
```bash
# Get DLQ message count
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/the-alchemiser-dlq-prod \
  --attribute-names ApproximateNumberOfMessages

# Receive message from DLQ (for debugging)
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/the-alchemiser-dlq-prod \
  --max-number-of-messages 1
```

**Interpretation**:
- `0` messages: All invocations succeeded
- `>0` messages: Lambda failed; check message body for error details

### Manual Lambda Invocation (Testing)
```bash
# Test invocation (paper trading mode)
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-prod \
  --payload '{"mode": "test"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json
```

---

## Disaster Recovery

### Complete Stack Failure
**Scenario**: CloudFormation stack corrupted or deleted.

```bash
# 1. Verify stack state
aws cloudformation describe-stacks \
  --stack-name the-alchemiser-v2

# 2. If stack is in ROLLBACK_COMPLETE or DELETE_FAILED, delete it
aws cloudformation delete-stack --stack-name the-alchemiser-v2

# 3. Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name the-alchemiser-v2

# 4. Redeploy from latest main commit
gh workflow run cd.yml -f environment=prod
```

**Duration**: ~15 minutes (deletion + redeploy)  
**Data Loss**: None (trading state is in Alpaca API, not Lambda)

### Lambda Function Deleted
**Scenario**: Function deleted but stack still exists.

```bash
# CloudFormation will detect drift and recreate on next deploy
gh workflow run cd.yml -f environment=prod
```

---

## Troubleshooting

### Deployment Stuck in "In Progress"
**Cause**: CodeDeploy waiting for canary period (5 minutes) or alarm evaluation.

**Resolution**: Wait for canary period to complete. Check CodeDeploy console for status.

### "Rate Exceeded" Error in CI
**Cause**: GitHub Actions hitting AWS API rate limits.

**Resolution**: Add exponential backoff to `sam deploy` or wait 5 minutes and retry.

### Lambda Timeout (900s)
**Cause**: Trading logic taking longer than 15 minutes (Lambda max timeout).

**Short-term**: Check CloudWatch Logs for slow operations (e.g., DSL parsing, Alpaca API calls).  
**Long-term**: Optimize strategy logic or split into multiple Lambdas.

### "Access Denied" on Secrets
**Cause**: GitHub Secrets not set or CI role lacks permissions.

**Resolution**:
1. Verify secrets exist: `gh secret list`
2. Check IAM role policy includes required actions (see [IAM_POLICIES.md](./IAM_POLICIES.md))

---

## Health Check Script

Save as `scripts/health_check.sh`:

```bash
#!/bin/bash
# Health check for The Alchemiser deployment

set -e

FUNCTION_NAME="the-alchemiser-v2-lambda-prod"
ALARM_PREFIX="the-alchemiser"

echo "🔍 Checking Lambda function..."
aws lambda get-function --function-name $FUNCTION_NAME > /dev/null
echo "✅ Lambda function exists"

echo ""
echo "🔍 Checking alias..."
ALIAS_VERSION=$(aws lambda get-alias --function-name $FUNCTION_NAME --name live --query 'FunctionVersion' --output text)
echo "✅ Alias 'live' points to version $ALIAS_VERSION"

echo ""
echo "🔍 Checking CloudWatch alarms..."
ALARM_COUNT=$(aws cloudwatch describe-alarms --alarm-name-prefix $ALARM_PREFIX --query 'length(MetricAlarms)' --output text)
echo "✅ Found $ALARM_COUNT alarms"

ALARM_STATE=$(aws cloudwatch describe-alarms --alarm-name-prefix $ALARM_PREFIX --state-value ALARM --query 'length(MetricAlarms)' --output text)
if [ "$ALARM_STATE" -gt 0 ]; then
    echo "⚠️  $ALARM_STATE alarms in ALARM state"
    exit 1
else
    echo "✅ All alarms are OK"
fi

echo ""
echo "🔍 Checking EventBridge schedule..."
SCHEDULE_STATE=$(aws scheduler get-schedule --name the-alchemiser-daily-trading-prod --query 'State' --output text)
if [ "$SCHEDULE_STATE" = "ENABLED" ]; then
    echo "✅ Schedule is ENABLED"
else
    echo "⚠️  Schedule is $SCHEDULE_STATE"
fi

echo ""
echo "🔍 Checking DLQ..."
# Note: Replace <ACCOUNT_ID> with actual account ID or use environment variable
# DLQ_URL="https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/the-alchemiser-dlq-prod"
# MSG_COUNT=$(aws sqs get-queue-attributes --queue-url $DLQ_URL --attribute-names ApproximateNumberOfMessages --query 'Attributes.ApproximateNumberOfMessages' --output text)
# if [ "$MSG_COUNT" -gt 0 ]; then
#     echo "⚠️  $MSG_COUNT messages in DLQ"
# else
#     echo "✅ DLQ is empty"
# fi

echo ""
echo "✅ Health check complete!"
```

Run with: `bash scripts/health_check.sh`

---

## Escalation

### On-Call Rotation
- **Primary**: [Your Name] - [Email/Phone]
- **Secondary**: [Backup Name] - [Email/Phone]
- **Escalation**: [Manager Name] - [Email/Phone]

### Severity Levels
- **P0 (Critical)**: Trading system down; money at risk → Escalate immediately
- **P1 (High)**: Deployment failed; rollback required → Notify team
- **P2 (Medium)**: Monitoring alert; investigate within 4 hours
- **P3 (Low)**: Non-urgent issue; address in next sprint

### Communication Channels
- **Incidents**: #alchemiser-incidents (Slack)
- **Deployments**: #alchemiser-deployments (Slack)
- **Alerts**: PagerDuty integration (if configured)

---

## Related Documentation
- [CI/CD Audit Report](./CI_CD_AUDIT_REPORT.md)
- [IAM Policy Documentation](./IAM_POLICIES.md)
- [AWS SAM Template](../template.yaml)
- [Deployment Script](../scripts/deploy.sh)

---

**Document Ownership**: DevOps Team  
**Review Schedule**: Quarterly (or after major incident)  
**Last Reviewed**: 2024-12-19
