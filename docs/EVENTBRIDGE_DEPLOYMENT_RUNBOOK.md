# EventBridge Deployment Runbook

## Overview

This runbook provides step-by-step procedures for deploying and managing the EventBridge-based event-driven architecture for The Alchemiser trading system.

**Target Audience:** DevOps, SRE, Platform Engineers  
**Last Updated:** 2025-10-14  
**Version:** 1.0

---

## Prerequisites

- AWS CLI configured with appropriate credentials
- SAM CLI installed
- Access to dev/prod AWS accounts
- EventBridge bus and DynamoDB table deployed

---

## Deployment Procedure

### Phase 1: Infrastructure Deployment

```bash
# 1. Build the Lambda function
sam build

# 2. Deploy to dev environment
sam deploy --config-env dev

# 3. Verify infrastructure resources
aws events list-event-buses --query "EventBuses[?Name=='alchemiser-trading-events-dev']"
aws dynamodb describe-table --table-name alchemiser-event-dedup-dev
aws sqs get-queue-attributes --queue-url $(aws cloudformation describe-stacks \
  --stack-name alchemiser-trading-dev \
  --query "Stacks[0].Outputs[?OutputKey=='EventDLQUrl'].OutputValue" \
  --output text) \
  --attribute-names All
```

### Phase 2: Enable EventBridge Rules (Progressive)

**Important:** Enable rules one at a time and verify after each enable.

```bash
# Enable SignalGenerated rule first
aws events enable-rule --name alchemiser-signal-generated-dev

# Wait 2 minutes, then check for errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=alchemiser-signal-generated-dev \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# If no failures, enable next rule
aws events enable-rule --name alchemiser-rebalance-planned-dev

# Wait 2 minutes, verify again
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=alchemiser-rebalance-planned-dev \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Enable monitoring rules
aws events enable-rule --name alchemiser-trade-executed-dev
aws events enable-rule --name alchemiser-all-events-monitor-dev
```

### Phase 3: Smoke Tests

Run smoke tests to verify end-to-end functionality:

```bash
# 1. Trigger a test trading workflow (paper mode)
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-dev \
  --payload '{"mode": "trade", "trading_mode": "paper"}' \
  response.json

# 2. Check response
cat response.json

# 3. Verify events were published
aws events list-archives --event-source-arn $(aws cloudformation describe-stacks \
  --stack-name alchemiser-trading-dev \
  --query "Stacks[0].Outputs[?OutputKey=='EventBusArn'].OutputValue" \
  --output text)

# 4. Check DLQ is empty
aws sqs get-queue-attributes \
  --queue-url $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='EventDLQUrl'].OutputValue" \
    --output text) \
  --attribute-names ApproximateNumberOfMessages

# Expected: ApproximateNumberOfMessages = 0
```

### Phase 4: Monitoring Setup

```bash
# Subscribe to alarm notifications (replace EMAIL with your email)
aws sns subscribe \
  --topic-arn $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='AlarmTopicArn'].OutputValue" \
    --output text) \
  --protocol email \
  --notification-endpoint YOUR_EMAIL@example.com

# Confirm subscription via email link

# Test alarm notification (optional)
aws sns publish \
  --topic-arn $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='AlarmTopicArn'].OutputValue" \
    --output text) \
  --message "Test alarm notification"
```

---

## Rollback Procedure

### Emergency Rollback (Disable All Rules)

```bash
# Disable all EventBridge rules immediately
for rule in signal-generated rebalance-planned trade-executed all-events-monitor; do
  aws events disable-rule --name alchemiser-${rule}-dev
  echo "Disabled alchemiser-${rule}-dev"
done

# Verify all rules are disabled
aws events list-rules \
  --event-bus-name alchemiser-trading-events-dev \
  --query "Rules[?starts_with(Name, 'alchemiser-')].{Name:Name,State:State}"
```

### Code Rollback

```bash
# Revert to previous stack version
sam deploy --config-env dev --parameter-overrides Stage=dev

# Or rollback Lambda function only
aws lambda update-function-code \
  --function-name the-alchemiser-v2-lambda-dev \
  --s3-bucket YOUR_DEPLOYMENT_BUCKET \
  --s3-key previous-version.zip
```

---

## Event Replay

Replay events from the archive for recovery or testing:

```bash
# 1. Create replay configuration
aws events start-replay \
  --replay-name "replay-$(date +%Y%m%d-%H%M%S)" \
  --event-source-arn $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='EventBusArn'].OutputValue" \
    --output text) \
  --event-start-time "2025-10-14T00:00:00Z" \
  --event-end-time "2025-10-14T23:59:59Z" \
  --destination EventBusArn=$(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='EventBusArn'].OutputValue" \
    --output text)

# 2. Monitor replay progress
aws events describe-replay --replay-name "replay-TIMESTAMP"

# 3. Cancel replay if needed
aws events cancel-replay --replay-name "replay-TIMESTAMP"
```

**⚠️ Warning:** Replay will re-invoke handlers. Ensure idempotency is working before replaying!

---

## Verification Checklist

After deployment, verify:

- [ ] All EventBridge rules are in desired state (enabled/disabled)
- [ ] DLQ has 0 messages
- [ ] CloudWatch alarms are in OK state
- [ ] SNS subscription confirmed
- [ ] Idempotency table created with TTL enabled
- [ ] Lambda has DynamoDB permissions
- [ ] Lambda has EventBridge publish permissions
- [ ] Recent Lambda invocations succeeded (check CloudWatch Logs)
- [ ] No throttling errors in last 15 minutes

```bash
# Quick verification script
./scripts/verify-eventbridge-deployment.sh dev
```

---

## Production Deployment

Production deployment follows the same procedure with additional safeguards:

1. **Deploy to dev first**, verify for 24 hours
2. **Enable rules progressively** (one per hour)
3. **Monitor dashboards continuously** during rollout
4. **Have rollback plan ready** (pre-tested in dev)
5. **Deploy during off-peak hours** (weekends preferred)
6. **Notify stakeholders** before and after deployment

```bash
# Production deployment
sam deploy --config-env prod

# Enable rules with extended monitoring periods
for rule in signal-generated rebalance-planned trade-executed all-events-monitor; do
  aws events enable-rule --name alchemiser-${rule}-prod
  echo "Enabled alchemiser-${rule}-prod - monitoring for 1 hour..."
  sleep 3600
  # Check for failures before proceeding
  aws cloudwatch get-metric-statistics \
    --namespace AWS/Events \
    --metric-name FailedInvocations \
    --dimensions Name=RuleName,Value=alchemiser-${rule}-prod \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum
done
```

---

## Helper Scripts Location

- Verify deployment: `scripts/verify-eventbridge-deployment.sh`
- Enable rules: `scripts/enable-eventbridge-rules.sh`
- Disable rules: `scripts/disable-eventbridge-rules.sh`
- Monitor health: `scripts/monitor-eventbridge-health.sh`

---

## Contact Information

- **Primary Contact:** Platform Team (platform@example.com)
- **Escalation:** SRE On-Call (sre-oncall@example.com)
- **Slack Channel:** #alchemiser-platform

---

## Version History

| Version | Date       | Author | Changes                     |
|---------|------------|--------|-----------------------------|
| 1.0     | 2025-10-14 | Copilot | Initial deployment runbook |
