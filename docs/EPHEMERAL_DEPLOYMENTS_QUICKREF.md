# Ephemeral Deployments - Quick Reference

## One-Line Commands

### Deploy
```bash
# Via Makefile
make deploy-ephemeral BRANCH=feature/my-feature TTL_HOURS=24

# Via GitHub CLI
gh workflow run manual-deploy-ephemeral.yml -f branch=feature/my-feature -f ttl_hours=24
```

### Destroy
```bash
# Via Makefile
make destroy-ephemeral STACK=alchemiser-ephem-feature-my-feature-a1b2c3d

# Via GitHub CLI
gh workflow run manual-destroy-ephemeral.yml -f stack_name=alchemiser-ephem-feature-my-feature-a1b2c3d
```

### List
```bash
make list-ephemeral
```

## Stack Naming

Pattern: `alchemiser-ephem-{branch}-{sha}`

Branch Sanitization:
- Lowercase
- `/._@` → `-`
- Max 40 chars
- Example: `feature/My_Test.Branch` → `feature-my-test-branch`

## Resource Naming

| Resource | Pattern |
|----------|---------|
| Lambda | `{stack}-lambda` |
| S3 | `{stack}-trade-ledger` |
| DLQ | `{stack}-dlq` |
| Schedule | `{stack}-daily-trading` |
| Logs | `/aws/lambda/{stack}-lambda` |

## Stack Tags

| Tag | Purpose |
|-----|---------|
| `Ephemeral=true` | Identifies ephemeral stacks |
| `Branch` | Original branch name |
| `ShortSHA` | 7-char commit SHA |
| `TTLHours` | Auto-cleanup TTL |
| `CreatedBy=GitHubActions` | Creator |

## Key Differences from Dev/Prod

| Feature | Dev/Prod | Ephemeral |
|---------|----------|-----------|
| Schedules | Enabled | **Disabled** |
| Log Retention | 30 days | **3 days** |
| TTL | None | **Configurable** |
| Auto-Cleanup | No | **Yes (30min checks)** |

## Safety Guardrails

### Deploy: Blocked If
- Branch = `main`, `prod`, `production`
- Stack name > 128 chars

### Destroy: Blocked If
- Stack name ≠ `alchemiser-ephem-*`
- Stack tag `Ephemeral` ≠ `true`
- Stack = dev/prod stack

## Cleanup Schedule

- **Frequency:** Every 30 minutes
- **Logic:** Delete if `CurrentTime > CreationTime + TTLHours`
- **Dry Run:** `gh workflow run scheduled-ephemeral-cleanup.yml -f dry_run=true`

## Common Workflows

### Quick Test (2 hours)
```bash
make deploy-ephemeral BRANCH=$(git branch --show-current) TTL_HOURS=2
# ... test ...
make destroy-ephemeral STACK=<generated-stack-name>
```

### Extended Test (1 week)
```bash
make deploy-ephemeral BRANCH=feature/big-change TTL_HOURS=168
```

### Parallel Testing
```bash
make deploy-ephemeral BRANCH=feature/approach-a TTL_HOURS=12
make deploy-ephemeral BRANCH=feature/approach-b TTL_HOURS=12
```

## Monitoring

```bash
# List stacks
make list-ephemeral

# Watch logs
aws logs tail /aws/lambda/{stack}-lambda --follow

# Stack status
aws cloudformation describe-stacks --stack-name {stack} \
  --query 'Stacks[0].StackStatus'
```

## Cost Estimate

- **Per stack:** $0-2/day
- **Mostly free tier:** Lambda, EventBridge
- **Small costs:** S3 (~$0.02/mo), Logs (~$0.50/GB)

## Troubleshooting

### Stack name too long
```bash
gh workflow run manual-deploy-ephemeral.yml \
  -f branch=feature/my-branch \
  -f stack_suffix=short-name
```

### Deletion stuck
```bash
# Check status
aws cloudformation describe-stacks --stack-name {stack}

# If failed, empty S3 manually then retry destroy
```

### Stack not in list
```bash
# Check tags
aws cloudformation describe-stacks --stack-name {stack} \
  --query 'Stacks[0].Tags'
```

## Links

- [Full Documentation](EPHEMERAL_DEPLOYMENTS.md)
- [Deploy Workflow](../.github/workflows/manual-deploy-ephemeral.yml)
- [Destroy Workflow](../.github/workflows/manual-destroy-ephemeral.yml)
- [Cleanup Workflow](../.github/workflows/scheduled-ephemeral-cleanup.yml)
