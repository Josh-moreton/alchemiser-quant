# P&L Workflow Environment Variable Fix

## Problem
The P&L Analysis workflow was failing with "Missing required Alpaca credentials" error despite having `environment: production` set and secrets being passed in the `env:` block.

## Root Cause
Environment variables in GitHub Actions step-level `env:` blocks are only available **within that specific step**. They don't persist to subsequent steps unless explicitly exported to `$GITHUB_ENV`.

## Solution
Added a "Prepare environment variables" step that explicitly exports all required variables to `$GITHUB_ENV`, making them available to the subsequent "Run P&L Analysis" step.

### Changes Made

**Before:**
```yaml
- name: Run P&L Analysis
  id: run_pnl
  env:
    ALPACA_KEY: ${{ secrets.ALPACA_KEY }}
    ALPACA_SECRET: ${{ secrets.ALPACA_SECRET }}
    # ... other vars
  run: |
    poetry run python -m the_alchemiser pnl --monthly
```

**After:**
```yaml
- name: Prepare environment variables
  env:
    ALPACA_KEY: ${{ secrets.ALPACA_KEY }}
    ALPACA_SECRET: ${{ secrets.ALPACA_SECRET }}
    # ... other vars
  run: |
    echo "ALPACA_KEY=$ALPACA_KEY" >> $GITHUB_ENV
    echo "ALPACA_SECRET=$ALPACA_SECRET" >> $GITHUB_ENV
    # ... export all vars

- name: Run P&L Analysis
  id: run_pnl
  run: |
    poetry run python -m the_alchemiser pnl --monthly
```

## Why This Works
1. The "Prepare" step receives variables from GitHub Secrets/Vars
2. It exports them to `$GITHUB_ENV` (a special GitHub Actions file)
3. All subsequent steps in the job automatically inherit these environment variables
4. The Python application can now access them via `os.getenv()`

## Pattern Consistency
This matches the pattern used in the CD workflow (`cd.yml`):
- Dev environment: Lines 87-102
- Prod environment: Lines 104-119

Both deployment environments use the same export pattern, ensuring consistency across all workflows.

## Testing
Run the workflow manually via GitHub Actions UI:
1. Go to Actions → PnL Analysis
2. Click "Run workflow"
3. Select analysis type and options
4. Verify credentials are found in logs

## Related Files
- `.github/workflows/pnl-analysis.yml` - Fixed workflow
- `.github/workflows/cd.yml` - Reference pattern
- `the_alchemiser/shared/config/secrets_adapter.py` - Credential loading logic
