# Staging Environment Setup Guide

## Overview

Staging environment has been added as a long-lived testing environment between dev and prod. This allows for multi-week testing of changes before promoting to production.

## Architecture

The system now supports three environments:

1. **Dev** - Active development and quick iteration (paper trading)
2. **Staging** - Long-lived testing environment (paper trading, production-like)
3. **Prod** - Live trading with real money

## Files Modified

### 1. template.yaml

**Changes:**
- Added `staging` to `Stage` and `Env` parameter allowed values
- Added `StageConfig.staging` mapping: `{ TitleCase: "Staging" }`
- Added `IsStaging` condition
- Added staging-specific parameters:
  - `StagingAlpacaKey`
  - `StagingAlpacaSecret`
  - `StagingAlpacaEndpoint` (defaults to paper trading)
  - `StagingEmailPassword`
  - `StagingEquityDeploymentPct`
- Updated `Globals.Function.Environment.Variables` to use 3-way conditions:
  - `APP__STAGE`: `prod` / `staging` / `dev`
  - `ALPACA__KEY`: Uses `ProdAlpacaKey` / `StagingAlpacaKey` / `AlpacaKey`
  - `ALPACA__SECRET`: Uses `ProdAlpacaSecret` / `StagingAlpacaSecret` / `AlpacaSecret`
  - `ALPACA__ENDPOINT`: Uses `ProdAlpacaEndpoint` / `StagingAlpacaEndpoint` / `AlpacaEndpoint`
  - `EMAIL__PASSWORD`: Uses `ProdEmailPassword` / `StagingEmailPassword` / `EmailPassword`
  - `ALPACA__EQUITY_DEPLOYMENT_PCT`: Uses `ProdEquityDeploymentPct` / `StagingEquityDeploymentPct` / `EquityDeploymentPct`

### 2. samconfig.toml

**Changes:**
- Added `[staging.deploy.parameters]` section:
  - `stack_name = "alchemiser-staging"`
  - `parameter_overrides = ["Stage=staging"]`
- Mirrors dev configuration structure

### 3. Makefile

**Changes:**
- Added `deploy-staging` target
- Creates staging tags: `v{version}-staging.{n}`
- Creates GitHub pre-releases for staging deployments
- Added staging to help text

### 4. .github/workflows/cd.yml

**Changes:**
- Added `staging` to workflow_dispatch environment options
- Added staging tag pattern to push triggers: `v[0-9]+.[0-9]+.[0-9]+-staging.[0-9]+`
- Updated "Decide target environment" step to detect staging tags
- Updated environment selector to handle staging
- Added "Prepare environment variables (staging)" step with staging-specific secrets/vars

## GitHub Setup Required

You need to create a new **staging** environment in your GitHub repository settings:

### How Environment Variables Work

The system uses **GitHub Environments** to manage different values for each deployment target:

1. **Workflow level:** GitHub Actions reads secrets/vars from the selected environment (dev/staging/prod)
2. **Environment variables:** All environments use the **same variable names** (e.g., `ALPACA_KEY`)
3. **Different values:** Each GitHub Environment provides different values for the same variable name
4. **Deploy script:** Maps generic env vars to environment-specific CloudFormation parameters:
   - Dev: `ALPACA_KEY` → `AlpacaKey` parameter
   - Staging: `ALPACA_KEY` → `StagingAlpacaKey` parameter
   - Prod: `ALPACA_KEY` → `ProdAlpacaKey` parameter

This pattern keeps the workflow DRY while allowing CloudFormation to distinguish between environments.

### Steps:

1. Go to your GitHub repository
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name it: `staging`
5. Add the following **Secrets** (same names as dev/prod, different values):
   - `ALPACA_KEY` - Alpaca API key for staging
   - `ALPACA_SECRET` - Alpaca API secret for staging
   - `EMAIL__PASSWORD` - Email SMTP password for staging notifications (optional)
6. Add the following **Variables** (same names as dev/prod, different values):
   - `ALPACA_ENDPOINT` - Typically `https://paper-api.alpaca.markets/v2`
   - `LOGGING__LEVEL` - e.g., `INFO`
   - `EQUITY_DEPLOYMENT_PCT` - e.g., `1.0` (100% of equity)

**Important:** Use the **same environment variable names** as dev/prod. GitHub Environments provide different values automatically based on which environment is deploying.

**Note:** The GitHub environment should already have the `AWS_ROLE_ARN` and `AWS_REGION` secrets configured from dev/prod setup.

## Deployment Workflow

### Deploy to Staging

```bash
make deploy-staging
```

This will:
1. Use current version from `pyproject.toml`
2. Create a staging tag: `v{version}-staging.{n}` (e.g., `v0.4.7-staging.1`)
3. Push the tag to GitHub
4. Create a GitHub pre-release
5. Trigger the CD workflow via tag push

### Deploy Specific Version to Staging

```bash
make deploy-staging v=0.5.0
```

This creates `v0.5.0-staging.1` instead of using the version from `pyproject.toml`.

### Manual Deploy via GitHub Actions

1. Go to **Actions** → **CD** workflow
2. Click **Run workflow**
3. Select **staging** from the environment dropdown
4. Click **Run workflow**

## Staging Tag Format

Staging tags follow the pattern: `v{major}.{minor}.{patch}-staging.{n}`

Examples:
- `v0.4.7-staging.1` - First staging release of version 0.4.7
- `v0.4.7-staging.2` - Second staging release of version 0.4.7
- `v0.5.0-staging.1` - First staging release of version 0.5.0

The staging number auto-increments for each staging deployment of the same version.

## Environment Lifecycle

```
Development → Staging → Production
    ↓           ↓           ↓
  v*-beta.*  v*-staging.*  v*
```

**Typical workflow:**
1. Develop and test in **dev** (rapid iteration, v*-beta.* tags)
2. Promote to **staging** for long-lived testing (v*-staging.* tags)
3. After multi-week testing, promote to **prod** (v* tags)

## CloudFormation Stacks

Each environment has its own CloudFormation stack:

- **Dev:** `alchemiser-dev`
- **Staging:** `alchemiser-staging`
- **Prod:** `alchemiser-prod`

This allows independent infrastructure and complete isolation between environments.

## AWS Resources per Environment

Each environment gets its own set of AWS resources:

- Lambda functions (StrategyOrchestratorFunction, StrategyFunction, etc.)
- DynamoDB tables (AggregationSessionsTable, TradeLedgerTable)
- EventBridge bus (AlchemiserEventBus)
- SQS queues (ExecutionQueue, ExecutionDLQ)
- SNS topics (TradingNotificationsTopic, DLQAlertTopic)
- S3 bucket (PerformanceReportsBucket)

Resource names include environment suffix (e.g., `alchemiser-staging-strategy-orchestrator-function`)

## Cost Considerations

Staging environment will incur additional AWS costs:

- Lambda invocations (minimal, only during scheduled runs)
- DynamoDB storage and requests
- EventBridge events
- SQS messages
- SNS notifications
- S3 storage

**Estimate:** ~$5-20/month depending on usage (Lambda is on-demand, so no cost when not running)

## Testing in Staging

Staging should mirror production as closely as possible:

1. **Use paper trading** (default: `https://paper-api.alpaca.markets/v2`)
2. **Same strategies** as production (but isolated allocation)
3. **Same equity deployment percentage** as production
4. **Run on production schedule** (3:30 PM ET daily)
5. **Test for multiple weeks** before promoting to prod

### Key Differences from Dev:

- **Dev:** Rapid iteration, frequent deployments, may break
- **Staging:** Stable testing, infrequent deployments, production-like
- **Prod:** Live trading, rare deployments, real money

## Monitoring Staging

Use the same observability tools as dev/prod:

```bash
# Fetch logs from staging
make logs stage=staging

# Fetch logs for specific workflow
make logs stage=staging id=workflow-abc123

# Sync strategy ledger to staging
make strategy-sync stage=staging

# List strategies in staging
make strategy-list-dynamo stage=staging
```

## Rollback

If staging deployment fails or needs rollback:

1. **CloudFormation rollback:** AWS automatically rolls back failed deployments
2. **Manual rollback:** Delete the staging stack and redeploy previous version:
   ```bash
   aws cloudformation delete-stack --stack-name alchemiser-staging
   make deploy-staging v=<previous-version>
   ```

## Next Steps

1. ✅ Add staging environment in GitHub repository settings
2. ✅ Configure staging secrets and variables
3. Test deployment: `make deploy-staging`
4. Verify staging stack in AWS CloudFormation console
5. Monitor staging logs and behavior

## Questions?

Refer to:
- [Main README](../README.md) for overall system architecture
- [Template YAML](../template.yaml) for infrastructure details
- [Makefile](../Makefile) for deployment commands
- [CD Workflow](../.github/workflows/cd.yml) for CI/CD logic
