# Test Deployment Environment Guide

## Overview

The **test** deployment environment provides an isolated AWS environment for validating feature branches and Copilot-generated changes before merging to main. This environment is designed to be ephemeral and allows developers to deploy Lambda functions independently for testing.

## Key Characteristics

### What's Different in Test Environment

1. **No EventBridge Schedules**: Test deployments do NOT include automatic trading schedules
2. **Separate Stack**: Uses `the-alchemiser-v2-test` stack name to avoid conflicts
3. **Optional Credentials**: Can deploy without real Alpaca credentials for structure validation
4. **Manual Invocation**: Lambda must be invoked manually (no automatic triggers)
5. **Isolated Resources**: Separate S3 bucket, Lambda function, and IAM roles

### What's The Same

- Same runtime configuration (Python 3.12, timeout, memory)
- Same build process (SAM with container builds)
- Same code packaging and dependencies
- Same environment variable structure

## Automatic Deployment

Test deployments are automatically triggered by:

- **Pushes to `feat/*` branches**: All feature branches
- **Pushes to `copilot/*` branches**: All Copilot-generated branches

The deployment workflow (`.github/workflows/test-deploy.yml`) runs automatically on push.

## Manual Deployment

### Via GitHub Actions (Recommended)

1. Go to **Actions** → **Test Environment Deployment**
2. Click **Run workflow**
3. Select the branch to deploy (or leave empty for current branch)
4. Click **Run workflow**

### Via Command Line

```bash
# Ensure you have AWS credentials configured
export AWS_PROFILE=your-profile

# Optional: Set Alpaca credentials (can be empty for validation)
export ALPACA_KEY="your-key"
export ALPACA_SECRET="your-secret"
export ALPACA_ENDPOINT="https://paper-api.alpaca.markets/v2"

# Deploy to test environment
./scripts/deploy.sh test
```

## Testing Deployed Lambda

Since the test environment has no EventBridge schedule, you must invoke the Lambda manually:

### Manual Invocation (AWS CLI)

```bash
# Basic invocation (health check mode)
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-test \
  --payload '{}' \
  response.json

# Trade mode invocation
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-test \
  --payload '{"mode": "trade"}' \
  response.json

# Monthly summary mode
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-test \
  --payload '{"action": "monthly_summary"}' \
  response.json

# View response
cat response.json
```

### Using SAM CLI (Local)

```bash
# Local invocation with test event
sam local invoke TradingSystemFunction \
  --config-env test \
  --event test-events/trade-event.json

# Interactive local testing
sam local start-lambda --config-env test
```

## Viewing Logs

### Via AWS CLI

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-test --follow

# View recent logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-test --since 1h

# Filter for errors
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-test --filter-pattern "ERROR"
```

### Via SAM CLI

```bash
sam logs --name TradingSystemFunction --stack-name the-alchemiser-v2-test --tail
```

### Via AWS Console

1. Go to **CloudWatch** → **Log groups**
2. Find `/aws/lambda/the-alchemiser-v2-lambda-test`
3. Browse log streams

## Cleanup

### Via SAM CLI (Recommended)

```bash
# Delete the entire test stack and all resources
sam delete --stack-name the-alchemiser-v2-test --region us-east-1 --no-prompts
```

### Via AWS CLI

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name the-alchemiser-v2-test

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name the-alchemiser-v2-test
```

### Manual Cleanup (if automated deletion fails)

1. **S3 Bucket**: Empty and delete `the-alchemiser-v2-trade-ledger-test`
2. **Lambda**: Delete function `the-alchemiser-v2-lambda-test`
3. **IAM Roles**: Delete test-specific execution roles
4. **CloudWatch Logs**: Delete log group `/aws/lambda/the-alchemiser-v2-lambda-test`
5. **CloudFormation**: Delete stack `the-alchemiser-v2-test`

## Environment Variables

Test environment supports all the same environment variables as dev/prod:

### Required for Real API Calls
- `ALPACA_KEY`: Alpaca API key (optional for structure validation)
- `ALPACA_SECRET`: Alpaca API secret (optional)

### Optional Configuration
- `ALPACA_ENDPOINT`: API endpoint (defaults to paper trading)
- `EMAIL__PASSWORD`: SMTP password for notifications
- `LOGGING__LEVEL`: Log level (default: INFO)
- `ALCHEMISER_DSL_MAX_WORKERS`: DSL worker threads (default: 7)

## Stack Resources

A test deployment creates:

1. **Lambda Function**: `the-alchemiser-v2-lambda-test`
2. **Lambda Layer**: `the-alchemiser-dependencies-test`
3. **S3 Bucket**: `the-alchemiser-v2-trade-ledger-test`
4. **IAM Roles**: 
   - `TradingSystemExecutionRole` (for Lambda)
   - **NO** SchedulerExecutionRole (schedules not created)
5. **SQS Queue**: `the-alchemiser-dlq-test` (dead letter queue)
6. **CloudWatch Log Group**: `/aws/lambda/the-alchemiser-v2-lambda-test`

**Note**: No EventBridge Scheduler resources are created in test environment.

## Cost Considerations

Test deployments have minimal costs:

- **Lambda**: Pay per invocation (only when manually invoked)
- **S3**: Minimal storage for trade ledger
- **CloudWatch Logs**: 30-day retention
- **No EventBridge costs**: Since no schedules are created

**Recommendation**: Delete test stacks when no longer needed to avoid accumulating storage costs.

## Best Practices

### 1. Use Descriptive Branch Names
```bash
# Good examples
feat/add-new-strategy
copilot/improve-portfolio-rebalancing
feat/fix-alpaca-authentication

# Avoid
test-branch
my-changes
```

### 2. Test Before Merging
- Deploy to test environment
- Manually invoke Lambda with various payloads
- Check CloudWatch logs for errors
- Verify expected behavior

### 3. Clean Up Regularly
- Delete test stacks after feature is merged
- Don't accumulate multiple test deployments
- Use `sam delete` for complete cleanup

### 4. Monitor Costs
- Check AWS Cost Explorer for test environment spending
- Set up billing alarms if needed
- Remember: test has no automatic schedules (lower cost)

### 5. Credentials Management
- Test environment can share dev credentials (paper trading)
- Or use separate test credentials if preferred
- Can deploy without credentials for structure validation only

## Troubleshooting

### Build Fails

```bash
# Clean build artifacts and retry
rm -rf .aws-sam
sam build --use-container --parallel --config-env test
```

### Deployment Fails

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name the-alchemiser-v2-test \
  --max-items 20

# Validate template
sam validate --region us-east-1 --lint
```

### Lambda Invocation Fails

```bash
# Check function exists
aws lambda get-function --function-name the-alchemiser-v2-lambda-test

# Check recent error logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-test --since 1h --filter-pattern "ERROR"
```

### Stack Deletion Fails

```bash
# Check what's blocking deletion
aws cloudformation describe-stack-events \
  --stack-name the-alchemiser-v2-test \
  | grep -i "DELETE_FAILED"

# Common fix: Empty S3 bucket first
aws s3 rm s3://the-alchemiser-v2-trade-ledger-test --recursive
```

## Comparison: Dev vs Test vs Prod

| Feature | Dev | Test | Prod |
|---------|-----|------|------|
| Stack Name | `the-alchemiser-v2-dev` | `the-alchemiser-v2-test` | `the-alchemiser-v2` |
| EventBridge Schedule | ✅ Daily 9:35 AM ET | ❌ None | ✅ Daily 9:35 AM ET |
| Monthly Summary | ✅ Monthly | ❌ None | ✅ Monthly |
| Alpaca API | Paper trading | Paper trading (optional) | Live trading |
| Auto Deploy | On main push | On feat/copilot push | On release |
| Manual Invoke | ✅ Supported | ✅ Required | ✅ Supported |
| Credentials | Required | Optional | Required |
| Purpose | Stable testing | Feature validation | Production trading |

## Security Notes

- Test environment uses same IAM role requirements as dev/prod
- Credentials are stored in GitHub Secrets (not in code)
- Test Lambda has same IAM permissions (S3, CloudWatch, etc.)
- No public access to any resources
- All resources are within VPC (if configured)

## Integration with CI/CD

The test deployment workflow is separate from main CI/CD:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs on all branches
- **Test Deploy** (`.github/workflows/test-deploy.yml`): Runs on feat/* and copilot/* only
- **CD Workflow** (`.github/workflows/cd.yml`): Runs on main and releases only

This ensures test deployments don't interfere with stable dev/prod pipelines.

## Related Documentation

- [SAM Build Architecture](./SAM_BUILD_ARCHITECTURE.md)
- [SAM Build Testing Guide](./SAM_BUILD_TESTING_GUIDE.md)
- [CI/CD Configuration](./CI_NON_BLOCKING_TESTS.md)
- [Deployment Script](../scripts/deploy.sh)

---

**Last Updated**: 2025-10-13  
**Version**: 1.0.0
