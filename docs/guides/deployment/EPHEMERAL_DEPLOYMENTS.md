# Ephemeral Deployments Guide

## Overview

Ephemeral deployments allow you to deploy any feature branch to AWS as a fully isolated stack for realistic testing. These stacks are temporary, automatically cleaned up after a configurable TTL, and completely isolated from dev/prod environments.

## Features

- **Full AWS Deployment**: Deploy complete infrastructure (Lambda, S3, EventBridge, IAM, CloudWatch) for any branch
- **Automatic Isolation**: All resources are namespaced by stack name to prevent conflicts
- **TTL-based Cleanup**: Stacks are automatically deleted after expiration
- **Manual Control**: Deploy and destroy stacks on-demand via GitHub Actions or CLI
- **Safety Guardrails**: Protection against accidental deployment/deletion of dev/prod stacks

## Quick Start

### Deploy an Ephemeral Stack

**Option 1: GitHub Actions UI**
1. Go to [Actions > Manual Deploy Ephemeral](https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/manual-deploy-ephemeral.yml)
2. Click "Run workflow"
3. **Select the branch you want to deploy** from the "Use workflow from" dropdown
4. Set TTL hours (default: 24)
5. Click "Run workflow"

**Option 2: GitHub CLI**
```bash
# Deploy current branch
gh workflow run manual-deploy-ephemeral.yml \
  -f ttl_hours="24"

# Deploy specific branch
gh workflow run manual-deploy-ephemeral.yml \
  --ref "feature/my-feature" \
  -f ttl_hours="24"
```

**Option 3: Makefile**
```bash
# Deploy current branch with default TTL (24 hours)
make deploy-ephemeral

# Deploy current branch with custom TTL
make deploy-ephemeral TTL_HOURS=48

# Deploy specific branch
make deploy-ephemeral BRANCH=feature/my-feature TTL_HOURS=24
```

### List Ephemeral Stacks

```bash
# Using Makefile (requires AWS CLI configured)
make list-ephemeral

# Using AWS CLI directly
aws cloudformation describe-stacks \
  --query "Stacks[?Tags[?Key=='Ephemeral' && Value=='true']]"
```

### Destroy an Ephemeral Stack

**Option 1: GitHub Actions UI**
1. Go to [Actions > Manual Destroy Ephemeral](https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/manual-destroy-ephemeral.yml)
2. Click "Run workflow"
3. Enter the stack name (e.g., `alchemiser-ephem-feature-my-feature-a1b2c3d`)
4. Click "Run workflow"

**Option 2: Makefile**
```bash
make destroy-ephemeral STACK=alchemiser-ephem-feature-my-feature-a1b2c3d
```

## Stack Naming Convention

Ephemeral stacks follow this naming pattern:
```
alchemiser-ephem-{sanitized-branch}-{short-sha}
```

**Examples:**
- Branch: `feature/my-feature` → Stack: `alchemiser-ephem-feature-my-feature-a1b2c3d`
- Branch: `bugfix/fix_123` → Stack: `alchemiser-ephem-bugfix-fix-123-b4e5f6a`
- Branch: `FEAT/New.Feature` → Stack: `alchemiser-ephem-feat-new-feature-c7d8e9f`

**Sanitization Rules:**
- Convert to lowercase
- Replace `/`, `.`, `_`, `@` with `-`
- Remove all other special characters
- Truncate to 40 characters (if needed)
- Remove leading/trailing dashes

**Long Branch Names:**
If your branch name is too long, use the `stack_suffix` parameter:
```bash
# Via GitHub UI: enter value in "Optional stack suffix override" field
# Via GitHub CLI:
gh workflow run manual-deploy-ephemeral.yml \
  --ref "feature/very-long-branch-name-that-exceeds-limits" \
  -f stack_suffix="my-short-name"
```

## Resource Naming

All AWS resources created by ephemeral stacks are namespaced by the stack name:

| Resource Type | Naming Pattern |
|--------------|----------------|
| Lambda Function | `{stack-name}-lambda` |
| S3 Bucket | `{stack-name}-trade-ledger` |
| DLQ | `{stack-name}-dlq` |
| EventBridge Schedule | `{stack-name}-daily-trading` |
| Monthly Schedule | `{stack-name}-monthly-summary` |
| Log Group | `/aws/lambda/{stack-name}-lambda` |
| Layer | `{stack-name}-dependencies` |

**Example for stack `alchemiser-ephem-feature-foo-a1b2c3d`:**
- Lambda: `alchemiser-ephem-feature-foo-a1b2c3d-lambda`
- S3: `alchemiser-ephem-feature-foo-a1b2c3d-trade-ledger`
- Logs: `/aws/lambda/alchemiser-ephem-feature-foo-a1b2c3d-lambda`

## Isolation Features

### 1. Separate Stacks
Each ephemeral deployment creates a completely separate CloudFormation stack.

### 2. Namespaced Resources
All resources include the stack name in their identifier, preventing conflicts with dev/prod or other ephemeral stacks.

### 3. Disabled Schedules
EventBridge schedules are automatically disabled for ephemeral stacks to prevent:
- Unexpected trading activity
- Resource consumption
- Conflicts with dev/prod schedules

### 4. Short Log Retention
Ephemeral stacks use 3-day log retention (vs 30 days for dev/prod) to minimize costs.

### 5. Same IAM Path
Ephemeral stacks use the same IAM role and credentials as dev deployments (not prod).

## Automatic Cleanup

### TTL-Based Deletion

The [scheduled cleanup workflow](https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/scheduled-ephemeral-cleanup.yml) runs every 30 minutes and:

1. Lists all stacks tagged with `Ephemeral=true`
2. Checks the `CreationTime` and `TTLHours` tag
3. Deletes stacks that have exceeded their TTL
4. Cleans up orphaned S3 artifacts

**Example:**
- Stack created: 2024-01-15 10:00 AM
- TTL: 24 hours
- Expiration: 2024-01-16 10:00 AM
- Deletion: Within 30 minutes after 10:00 AM on Jan 16

### Manual Dry Run

Test what would be deleted without actually deleting:

```bash
gh workflow run scheduled-ephemeral-cleanup.yml -f dry_run=true
```

## Stack Tags

Every ephemeral stack is tagged with:

| Tag | Description | Example |
|-----|-------------|---------|
| `Ephemeral` | Identifies ephemeral stacks | `true` |
| `Branch` | Original branch name | `feature/my-feature` |
| `SafeBranch` | Sanitized branch name | `feature-my-feature` |
| `ShortSHA` | Git commit SHA (7 chars) | `a1b2c3d` |
| `TTLHours` | TTL in hours | `24` |
| `CreatedBy` | Creator | `GitHubActions` |
| `WorkflowRun` | GitHub Actions run ID | `12345678` |

## Safety Guardrails

### Deploy Protection

The deploy workflow **blocks** deployment if:
- Branch name is `main`, `prod`, or `production`
- Stack name exceeds 128 characters

### Destroy Protection

The destroy workflow **blocks** deletion if:
- Stack name doesn't start with `alchemiser-ephem-`
- Stack name matches protected patterns: `the-alchemiser-v2`, `the-alchemiser-v2-dev`, `the-alchemiser-v2-prod`
- Stack is not tagged with `Ephemeral=true`

### Makefile Protection

Makefile targets validate:
- Required parameters are provided
- Stack names follow ephemeral naming pattern
- AWS/GitHub CLI are authenticated

## Workflow Details

### Manual Deploy Ephemeral

**File:** `.github/workflows/manual-deploy-ephemeral.yml`

**Triggers:**
- Manual via GitHub Actions UI (select branch from dropdown)
- GitHub CLI (`gh workflow run --ref <branch>`)
- Makefile (`make deploy-ephemeral`)

**Steps:**
1. Validate branch name (reject main/prod/production)
2. Checkout the selected branch
3. Generate sanitized stack name with short SHA
4. Configure AWS credentials (OIDC)
5. Set up Python and Poetry
6. Install SAM CLI
7. Build with `sam build --use-container --config-env ephemeral`
8. Deploy with stack-specific parameters and tags
9. Display stack outputs

**Environment:**
- Uses `dev` environment in GitHub Actions
- Same AWS role as dev deployments
- Same secrets/variables as dev

### Manual Destroy Ephemeral

**File:** `.github/workflows/manual-destroy-ephemeral.yml`

**Triggers:**
- Manual via GitHub Actions UI
- GitHub CLI (`gh workflow run`)
- Makefile (`make destroy-ephemeral`)

**Steps:**
1. Validate stack name (must be ephemeral)
2. Verify stack exists and is tagged as ephemeral
3. Empty S3 bucket (including versions)
4. Delete CloudFormation stack with `sam delete`
5. Wait for deletion to complete
6. Clean up orphaned resources (log groups, SAM artifacts)

### Scheduled Ephemeral Cleanup

**File:** `.github/workflows/scheduled-ephemeral-cleanup.yml`

**Triggers:**
- Scheduled: Every 30 minutes (`*/30 * * * *`)
- Manual via GitHub Actions UI (with dry_run option)

**Steps:**
1. List all ephemeral stacks
2. Calculate age and expiration for each stack
3. Delete expired stacks:
   - Empty S3 bucket
   - Delete stack
   - Clean up log groups
4. Clean up orphaned SAM deployment artifacts
5. Report summary

## Cost Considerations

### Per-Stack Costs
- Lambda: $0 (within free tier for most ephemeral testing)
- S3: ~$0.02/month for minimal data
- CloudWatch Logs: ~$0.50/GB ingested
- EventBridge: $0 (schedules disabled)
- **Estimated:** $0-2 per stack per day

### Optimization Tips
1. Use shorter TTLs for quick tests (2-4 hours)
2. Destroy stacks manually when done testing
3. Monitor with `make list-ephemeral`
4. Let automatic cleanup handle forgotten stacks

## Troubleshooting

### Deployment Failed

**Symptom:** Workflow fails during `sam deploy`

**Possible Causes:**
1. Stack name too long → Use `stack_suffix` parameter
2. Resource conflicts → Check for existing resources with same names
3. IAM permissions → Verify AWS role has necessary permissions
4. CloudFormation limits → You may have too many stacks

**Solution:**
```bash
# Check existing stacks
make list-ephemeral

# Try with a shorter suffix via GitHub UI or:
gh workflow run manual-deploy-ephemeral.yml \
  --ref "my-branch" \
  -f stack_suffix="short"
```

### Deletion Failed

**Symptom:** Stack deletion hangs or fails

**Possible Causes:**
1. S3 bucket not empty → Manual intervention needed
2. Lambda still has log streams → Wait and retry
3. Stack in `UPDATE_ROLLBACK_FAILED` state

**Solution:**
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name <stack-name>

# Force delete resources via AWS Console if needed
# Then re-run destroy workflow
```

### Stack Not Found in List

**Symptom:** Deployed stack doesn't appear in `make list-ephemeral`

**Possible Causes:**
1. Not tagged correctly
2. Different AWS region
3. Different AWS account

**Solution:**
```bash
# Check all stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE

# Check stack tags
aws cloudformation describe-stacks --stack-name <stack-name> \
  --query 'Stacks[0].Tags'
```

## Advanced Usage

### Custom TTL

Set a longer TTL for extended testing:
```bash
# Current branch with 1 week TTL
make deploy-ephemeral TTL_HOURS=168

# Specific branch with custom TTL
make deploy-ephemeral BRANCH=feature/long-test TTL_HOURS=168
```

### Testing Specific Commits

Deploy a specific commit by specifying its branch or SHA:
```bash
# Via GitHub CLI with a specific ref
gh workflow run manual-deploy-ephemeral.yml \
  --ref abc123def \
  -f ttl_hours=24
```

### Parallel Ephemeral Stacks

Deploy multiple branches simultaneously for comparison:
```bash
make deploy-ephemeral BRANCH=feature/approach-a TTL_HOURS=12
make deploy-ephemeral BRANCH=feature/approach-b TTL_HOURS=12
```

Each gets a unique stack name due to different branch names.

### Monitoring Ephemeral Stacks

```bash
# Watch logs in real-time
aws logs tail /aws/lambda/alchemiser-ephem-feature-foo-a1b2c3d-lambda --follow

# Check stack status
aws cloudformation describe-stacks \
  --stack-name alchemiser-ephem-feature-foo-a1b2c3d \
  --query 'Stacks[0].StackStatus'

# List all resources in stack
aws cloudformation list-stack-resources \
  --stack-name alchemiser-ephem-feature-foo-a1b2c3d
```

## Best Practices

1. **Short TTLs for Quick Tests**: Use 2-4 hours for rapid iteration
2. **Manual Cleanup**: Destroy stacks when done testing (don't wait for TTL)
3. **Descriptive Branch Names**: Use clear branch names for easy identification
4. **Monitor Costs**: Periodically check for forgotten stacks
5. **Test in Isolation**: Each feature gets its own ephemeral stack
6. **Document Test Plans**: Note what you're testing in PR descriptions

## Comparison with Dev/Prod

| Feature | Dev/Prod | Ephemeral |
|---------|----------|-----------|
| Stack Name | Fixed | Dynamic (per-branch) |
| Schedules | Enabled | Disabled |
| Log Retention | 30 days | 3 days |
| TTL | None | Configurable |
| Auto-Cleanup | No | Yes |
| Isolation | Per-environment | Per-branch |
| Use Case | Long-lived | Temporary testing |

## References

- [Manual Deploy Workflow](../.github/workflows/manual-deploy-ephemeral.yml)
- [Manual Destroy Workflow](../.github/workflows/manual-destroy-ephemeral.yml)
- [Scheduled Cleanup Workflow](../.github/workflows/scheduled-ephemeral-cleanup.yml)
- [CloudFormation Template](../template.yaml)
- [SAM Configuration](../samconfig.toml)
- [Makefile Targets](../Makefile)

## Support

For issues or questions:
1. Check [GitHub Actions logs](https://github.com/Josh-moreton/alchemiser-quant/actions)
2. Review stack events in AWS CloudFormation Console
3. Check CloudWatch Logs for Lambda errors
4. Open an issue on GitHub
