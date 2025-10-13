# Deployment Environments - Quick Reference

## When to Use Each Environment

### 🧪 Test Environment (`test`)
**Use for**: Feature development, Copilot changes, experimental work

**Characteristics**:
- ✅ Isolated Lambda deployment
- ✅ No automatic schedules
- ✅ Manual invocation only
- ✅ Optional credentials
- ✅ Separate stack (`the-alchemiser-v2-test`)
- ⚠️ No EventBridge triggers
- 💰 Pay per manual invocation only

**Triggers**: Automatic on `feat/*` or `copilot/*` branch push

**Best for**:
- Testing Lambda code changes
- Validating build process
- Checking environment configuration
- Isolated feature testing

### 🔧 Dev Environment (`dev`)
**Use for**: Stable development, integration testing

**Characteristics**:
- ✅ Full deployment with schedules
- ✅ Daily trading at 9:35 AM ET (Mon-Fri)
- ✅ Monthly summary reports
- ✅ Paper trading (Alpaca paper API)
- ✅ Separate stack (`the-alchemiser-v2-dev`)
- 🔒 Required credentials
- 💰 Runs automatically on schedule

**Triggers**: Automatic on `main` branch push

**Best for**:
- Integration testing
- End-to-end validation
- Pre-production verification
- Scheduled execution testing

### 🚀 Production Environment (`prod`)
**Use for**: Live trading

**Characteristics**:
- ✅ Full deployment with schedules
- ✅ Daily trading at 9:35 AM ET (Mon-Fri)
- ✅ Monthly summary reports
- ✅ Live trading (Alpaca live API)
- ✅ Main stack (`the-alchemiser-v2`)
- 🔒 Required credentials
- 💰 Runs automatically on schedule + real money

**Triggers**: Manual release publish only

**Best for**:
- Live trading with real capital
- Production workloads

## Comparison Matrix

| Feature | Test | Dev | Prod |
|---------|------|-----|------|
| **Stack Name** | `the-alchemiser-v2-test` | `the-alchemiser-v2-dev` | `the-alchemiser-v2` |
| **Lambda Name** | `...-lambda-test` | `...-lambda-dev` | `...-lambda-prod` |
| **Daily Schedule** | ❌ | ✅ 9:35 AM ET | ✅ 9:35 AM ET |
| **Monthly Summary** | ❌ | ✅ 1st at 00:05 UTC | ✅ 1st at 00:05 UTC |
| **Alpaca API** | Paper (optional) | Paper (required) | Live (required) |
| **Credentials** | Optional | Required | Required |
| **Auto Deploy** | feat/*, copilot/* | main push | Release only |
| **Invocation** | Manual only | Manual + Schedule | Manual + Schedule |
| **Cost** | Minimal (manual) | Low (scheduled) | Low (scheduled) |
| **Purpose** | Feature testing | Integration | Production |

## Decision Tree

```
Need to test a feature?
│
├─ Does it need scheduled execution?
│  ├─ YES → Use Dev (main branch)
│  └─ NO → Use Test (feat/* or copilot/* branch)
│
├─ Is it ready for real money?
│  └─ YES → Use Prod (create release)
│
└─ Just validating code/config?
   └─ Use Test (no credentials needed)
```

## Deployment Commands

### Test
```bash
# Automatic (push to feat/* or copilot/*)
git push origin feat/my-feature

# Manual
./scripts/deploy.sh test
```

### Dev
```bash
# Automatic (push to main)
git push origin main

# Manual
./scripts/deploy.sh dev
```

### Prod
```bash
# Automatic (via release)
gh release create v2.23.0 --title "Release v2.23.0" --notes "..."

# Manual
./scripts/deploy.sh prod
```

## Lambda Invocation

### Test (manual only)
```bash
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-test \
  --payload '{"mode": "trade"}' \
  response.json
```

### Dev (manual or automatic)
```bash
# Manual invocation
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-dev \
  --payload '{"mode": "trade"}' \
  response.json

# Automatic via EventBridge
# Runs daily at 9:35 AM ET (Mon-Fri)
```

### Prod (manual or automatic)
```bash
# Manual invocation
aws lambda invoke \
  --function-name the-alchemiser-v2-lambda-prod \
  --payload '{"mode": "trade"}' \
  response.json

# Automatic via EventBridge
# Runs daily at 9:35 AM ET (Mon-Fri)
```

## Cleanup

### Test
```bash
# Recommended: Delete after feature merge
sam delete --stack-name the-alchemiser-v2-test --no-prompts
```

### Dev
```bash
# Rarely needed (persistent environment)
sam delete --stack-name the-alchemiser-v2-dev --no-prompts
```

### Prod
```bash
# ⚠️ DANGER: Only in emergency
sam delete --stack-name the-alchemiser-v2 --no-prompts
```

## Cost Optimization

**Test Environment**:
- Delete after feature is merged
- No ongoing costs if deleted
- Only pay for manual invocations while active

**Dev Environment**:
- Persistent (don't delete)
- Low ongoing cost (scheduled invocations)
- Shared across all developers

**Prod Environment**:
- Persistent (don't delete)
- Low ongoing cost (scheduled invocations)
- Real trading operations

## Environment Variables

All environments support the same variables:

```bash
# Required for dev/prod, optional for test
ALPACA_KEY=your_key
ALPACA_SECRET=your_secret

# Optional for all
ALPACA_ENDPOINT=https://paper-api.alpaca.markets/v2  # or live
EMAIL__PASSWORD=your_smtp_password
LOGGING__LEVEL=INFO
ALCHEMISER_DSL_MAX_WORKERS=7
```

## Workflow Files

- **Test**: `.github/workflows/test-deploy.yml`
- **Dev**: `.github/workflows/cd.yml` (dev environment)
- **Prod**: `.github/workflows/cd.yml` (prod environment)

## Logs

View logs for any environment:

```bash
# Test
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-test --follow

# Dev
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow

# Prod
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-prod --follow
```

## Support

For detailed information, see:
- **Test Environment**: [docs/TEST_DEPLOYMENT_GUIDE.md](./TEST_DEPLOYMENT_GUIDE.md)
- **Implementation**: [docs/TEST_DEPLOYMENT_SUMMARY.md](./TEST_DEPLOYMENT_SUMMARY.md)
- **SAM Architecture**: [docs/SAM_BUILD_ARCHITECTURE.md](./SAM_BUILD_ARCHITECTURE.md)

---

**Last Updated**: 2025-10-13  
**Version**: 2.23.0
