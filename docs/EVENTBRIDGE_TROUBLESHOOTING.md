# EventBridge Troubleshooting Guide

## Overview

This guide provides troubleshooting procedures for common issues with the EventBridge-based event-driven architecture.

**Target Audience:** DevOps, SRE, Platform Engineers, Developers  
**Last Updated:** 2025-10-14  
**Version:** 1.0

---

## Quick Diagnostics

### Check System Health

```bash
# Check EventBridge rule states
aws events list-rules \
  --event-bus-name alchemiser-trading-events-dev \
  --query "Rules[?starts_with(Name, 'alchemiser-')].{Name:Name,State:State}"

# Check DLQ depth
aws sqs get-queue-attributes \
  --queue-url $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='EventDLQUrl'].OutputValue" \
    --output text) \
  --attribute-names ApproximateNumberOfMessages

# Check Lambda errors (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Check recent Lambda invocations
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --since 10m
```

---

## Common Issues

### 1. Events Not Being Processed

**Symptoms:**
- No Lambda invocations despite events being published
- CloudWatch Logs show no recent activity

**Diagnosis:**

```bash
# Check if rules are enabled
aws events describe-rule \
  --event-bus-name alchemiser-trading-events-dev \
  --name alchemiser-signal-generated-dev \
  --query "State"

# Check if rule has targets
aws events list-targets-by-rule \
  --event-bus-name alchemiser-trading-events-dev \
  --rule alchemiser-signal-generated-dev

# Check Lambda permissions
aws lambda get-policy \
  --function-name the-alchemiser-v2-lambda-dev \
  --query "Policy" | jq '.Statement[] | select(.Principal.Service == "events.amazonaws.com")'
```

**Resolution:**

```bash
# Enable the rule
aws events enable-rule --name alchemiser-signal-generated-dev

# Add target if missing
aws events put-targets \
  --rule alchemiser-signal-generated-dev \
  --event-bus-name alchemiser-trading-events-dev \
  --targets Id=1,Arn=$(aws lambda get-function \
    --function-name the-alchemiser-v2-lambda-dev \
    --query "Configuration.FunctionArn" --output text)

# Add Lambda permission
aws lambda add-permission \
  --function-name the-alchemiser-v2-lambda-dev \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn $(aws events describe-rule \
    --event-bus-name alchemiser-trading-events-dev \
    --name alchemiser-signal-generated-dev \
    --query "Arn" --output text)
```

---

### 2. Events Going to DLQ

**Symptoms:**
- DLQ alarm triggered
- `ApproximateNumberOfMessages` > 0 in DLQ

**Diagnosis:**

```bash
# View messages in DLQ
aws sqs receive-message \
  --queue-url $(aws cloudformation describe-stacks \
    --stack-name alchemiser-trading-dev \
    --query "Stacks[0].Outputs[?OutputKey=='EventDLQUrl'].OutputValue" \
    --output text) \
  --max-number-of-messages 10 \
  --attribute-names All

# Check Lambda error logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev \
  --filter-pattern "ERROR" \
  --since 1h
```

**Common Causes:**

1. **Lambda Timeout**
   ```bash
   # Check timeout configuration
   aws lambda get-function-configuration \
     --function-name the-alchemiser-v2-lambda-dev \
     --query "Timeout"
   
   # Increase timeout if needed (max 900 seconds)
   aws lambda update-function-configuration \
     --function-name the-alchemiser-v2-lambda-dev \
     --timeout 600
   ```

2. **Lambda Error/Exception**
   - Check CloudWatch Logs for stack traces
   - Look for validation errors, missing environment variables
   - Review recent code changes

3. **Event Payload Issues**
   ```bash
   # Validate event payload from DLQ
   aws sqs receive-message \
     --queue-url DLQ_URL \
     --max-number-of-messages 1 | jq '.Messages[0].Body | fromjson'
   
   # Check for missing required fields
   # Verify timestamp format
   # Ensure causation_id is present
   ```

**Resolution:**

```bash
# Drain DLQ after fixing issue (redrive to source)
# Note: This will replay events - ensure idempotency is working!

# 1. Configure redrive policy
aws sqs set-queue-attributes \
  --queue-url SOURCE_QUEUE_URL \
  --attributes RedrivePolicy='{"deadLetterTargetArn":"DLQ_ARN","maxReceiveCount":"3"}'

# 2. Start redrive (via AWS Console or custom script)
# OR manually process and delete messages
```

---

### 3. Duplicate Event Processing

**Symptoms:**
- Same event processed multiple times
- Duplicate trades executed
- Logs show "Duplicate event detected" warnings

**Diagnosis:**

```bash
# Check idempotency table
aws dynamodb scan \
  --table-name alchemiser-event-dedup-dev \
  --limit 10

# Check for specific event
aws dynamodb get-item \
  --table-name alchemiser-event-dedup-dev \
  --key '{"event_id": {"S": "evt-123"}}'

# Check TTL configuration
aws dynamodb describe-table \
  --table-name alchemiser-event-dedup-dev \
  --query "Table.TimeToLiveDescription"
```

**Common Causes:**

1. **DynamoDB Table Not Created**
   ```bash
   # Verify table exists
   aws dynamodb describe-table --table-name alchemiser-event-dedup-dev
   
   # Create if missing (via CloudFormation)
   sam deploy --config-env dev
   ```

2. **Lambda Missing DynamoDB Permissions**
   ```bash
   # Check IAM policy
   aws iam get-policy-version \
     --policy-arn $(aws iam list-policies \
       --query "Policies[?PolicyName=='TradingSystemPolicy'].Arn" \
       --output text) \
     --version-id $(aws iam get-policy \
       --policy-arn POLICY_ARN \
       --query "Policy.DefaultVersionId" --output text) \
     --query "PolicyVersion.Document.Statement[?Action contains 'dynamodb']"
   ```

3. **Idempotency Check Failing Open**
   - Check CloudWatch Logs for "Failed to check idempotency" warnings
   - Verify DynamoDB is accessible (not throttled)

**Resolution:**

```bash
# Add DynamoDB permissions to Lambda role
aws iam put-role-policy \
  --role-name TradingSystemExecutionRole \
  --policy-name DynamoDBIdempotency \
  --policy-document file://dynamodb-policy.json

# Enable TTL if not enabled
aws dynamodb update-time-to-live \
  --table-name alchemiser-event-dedup-dev \
  --time-to-live-specification Enabled=true,AttributeName=ttl

# Clean up stale idempotency records (manual)
aws dynamodb scan \
  --table-name alchemiser-event-dedup-dev \
  --filter-expression "attribute_exists(event_id)"
```

---

### 4. EventBridge Publish Failures

**Symptoms:**
- `EventPublishError` exceptions in logs
- Events not appearing in archive
- Failed invocations metric increasing

**Diagnosis:**

```bash
# Check EventBridge metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=alchemiser-signal-generated-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Check Lambda CloudWatch Logs for publish errors
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev \
  --filter-pattern "EventPublishError" \
  --since 1h
```

**Common Causes:**

1. **IAM Permissions Missing**
   ```bash
   # Check Lambda role has events:PutEvents permission
   aws iam simulate-principal-policy \
     --policy-source-arn $(aws lambda get-function \
       --function-name the-alchemiser-v2-lambda-dev \
       --query "Configuration.Role" --output text) \
     --action-names events:PutEvents \
     --resource-arns $(aws events describe-event-bus \
       --name alchemiser-trading-events-dev \
       --query "Arn" --output text)
   ```

2. **Event Bus Not Found**
   ```bash
   # Verify event bus exists
   aws events describe-event-bus \
     --name alchemiser-trading-events-dev
   ```

3. **EventBridge Service Issues**
   - Check AWS Service Health Dashboard
   - Review EventBridge service limits

**Resolution:**

```bash
# Add EventBridge publish permission
aws iam put-role-policy \
  --role-name TradingSystemExecutionRole \
  --policy-name EventBridgePublish \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "events:PutEvents",
      "Resource": "arn:aws:events:REGION:ACCOUNT:event-bus/alchemiser-trading-events-dev"
    }]
  }'

# Retry failed events (manual)
# Extract failed events from logs and republish
```

---

### 5. Lambda Throttling

**Symptoms:**
- `TooManyRequestsException` errors
- Throttles alarm triggered
- High latency in event processing

**Diagnosis:**

```bash
# Check throttles metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Check concurrent executions
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum

# Check account limits
aws lambda get-account-settings
```

**Resolution:**

```bash
# Request concurrency limit increase
# AWS Support ticket with business justification

# Add reserved concurrency (if needed)
aws lambda put-function-concurrency \
  --function-name the-alchemiser-v2-lambda-dev \
  --reserved-concurrent-executions 50

# Reduce event rate at source
# Implement exponential backoff in publishers
```

---

### 6. High Lambda Duration

**Symptoms:**
- Duration p95 alarm triggered
- Slow event processing
- Near-timeout warnings in logs

**Diagnosis:**

```bash
# Check duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,p95

# Analyze slow invocations
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev \
  --filter-pattern "Duration" \
  --since 1h | grep "REPORT"
```

**Common Causes:**

1. **Cold Start Overhead**
   - Large dependencies
   - Slow initialization

2. **Inefficient Code**
   - N+1 queries to external services
   - Lack of caching
   - Excessive logging

3. **External Service Latency**
   - Alpaca API slow
   - DynamoDB throttling

**Resolution:**

```bash
# Increase memory (also increases CPU)
aws lambda update-function-configuration \
  --function-name the-alchemiser-v2-lambda-dev \
  --memory-size 1024

# Enable Provisioned Concurrency (reduces cold starts)
aws lambda put-provisioned-concurrency-config \
  --function-name the-alchemiser-v2-lambda-dev \
  --provisioned-concurrent-executions 5 \
  --qualifier "$LATEST"

# Optimize code (profile locally)
# Add caching for repeated calls
# Reduce package size
```

---

## Monitoring Dashboards

### CloudWatch Dashboard

Access pre-built dashboard:
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name AlchemiserEventBridge \
  --dashboard-body file://cloudwatch-dashboard.json
```

Key metrics to monitor:
- **EventBridge Invocations** (should be > 0 during trading hours)
- **Failed Invocations** (should be 0)
- **DLQ Depth** (should be 0)
- **Lambda Errors** (should be < 1%)
- **Lambda Duration p95** (should be < 5 minutes)
- **Lambda Throttles** (should be 0)

---

## Escalation Procedures

### Severity Levels

**P1 (Critical):**
- Trading halted due to system failure
- Data loss detected
- Security breach suspected

**P2 (High):**
- Degraded performance affecting trading
- DLQ filling up rapidly
- Persistent Lambda errors

**P3 (Medium):**
- Intermittent errors
- Non-critical alarms triggered
- Performance degradation

**P4 (Low):**
- Informational issues
- Feature requests
- Documentation updates

### Escalation Path

1. **First Response:** Platform Team (#alchemiser-platform)
2. **Escalation (P1/P2):** SRE On-Call
3. **Escalation (P1):** Engineering Manager
4. **Executive Escalation:** VP Engineering

---

## Useful Commands Reference

```bash
# View event archive
aws events describe-archive \
  --archive-name alchemiser-event-archive-dev

# List recent events (via CloudWatch Logs Insights)
aws logs start-query \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, correlation_id, event_id | filter @message like /Event handled successfully/'

# Purge DLQ
aws sqs purge-queue --queue-url DLQ_URL

# Export metrics to CSV
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time START \
  --end-time END \
  --period 300 \
  --statistics Sum \
  --output table > metrics.csv
```

---

## Contact Information

- **Platform Team:** platform@example.com / #alchemiser-platform
- **SRE On-Call:** sre-oncall@example.com
- **AWS Support:** Use AWS Console or CLI to create support cases

---

## Version History

| Version | Date       | Author | Changes                        |
|---------|------------|--------|--------------------------------|
| 1.0     | 2025-10-14 | Copilot | Initial troubleshooting guide |
