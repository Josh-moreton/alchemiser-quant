# Filterable Groups Cache System

This directory contains extracted group strategies that are evaluated daily by the Group Cache Lambda. The cache enables accurate historical portfolio scoring for filter operators like `select-top`, `select-bottom`, etc.

## Problem This Solves

When a strategy uses a filter operator on groups:

```clojure
(filter (moving-average-return {:window 10}) (select-bottom 1)
  [(group "Strategy A" [...])
   (group "Strategy B" [...])
   (group "Strategy C" [...])])
```

The filter needs to score each group's **actual portfolio performance** over the last 10 days. Without caching, the system would need to:
1. Evaluate each group's DSL for each of the last 10 days
2. Determine what portfolio each group would have held
3. Fetch price data and compute returns

This is computationally expensive and introduces timing issues (evaluating historical DSL with current market data).

## Solution: Pre-computed Portfolio Returns

The Group Cache Lambda runs daily at **4:00 AM ET** and:
1. Evaluates each `.clj` file in this directory
2. Determines the portfolio (symbols + weights) each group would select
3. Fetches price data and computes the weighted daily return
4. Stores the result in DynamoDB

At strategy runtime (3:30 PM ET), filter operators query the cache to get historical portfolio returns, enabling accurate scoring.

## Directory Structure

```
filterable_groups/
    README.md                    # This file
    ftl_starburst/              # Parent strategy name
        _manifest.json           # Required: defines groups and metadata
        drv_drn_mean_reversion.clj
        labu_labd_mean_reversion.clj
        yinn_yang_mean_reversion.clj
    another_strategy/           # Add more strategies here
        _manifest.json
        group_a.clj
        group_b.clj
```

## How to Add a New Strategy

### Step 1: Create the Strategy Directory

Create a subdirectory named after the parent strategy:

```bash
mkdir -p layers/shared/the_alchemiser/shared/strategies/filterable_groups/my_strategy
```

### Step 2: Identify Groups to Extract

Look at your parent strategy file and find the groups being filtered. For example, in `ftl_starburst.clj`:

```clojure
(filter (moving-average-return {:window 10}) (select-bottom 1)
  [(group "DRV DRN Mean Reversion [FTL Copy] w/ WAM Updated Package" [...])
   (group "LABU LABD Mean Reversion [FTL Copy] w/ WAM Updated Package" [...])
   (group "YINN YANG Mean Reversion [FTL Copy] w/ WAM Updated Package" [...])])
```

Each of these groups needs to be extracted as a standalone `.clj` file.

### Step 3: Extract Each Group to a Standalone File

For each group, create a `.clj` file that wraps it in a `defsymphony`:

```clojure
;; Filterable Group: My Group Name
;; Extracted from: my_strategy.clj
;; Parent Filter: (moving-average-return {:window 10}) (select-bottom 1)
;; Required lookback: 10 days for filter scoring
(defsymphony
 "My Group Name"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "My Group Name"
    [(weight-equal
      ;; ... paste the group's content here ...
    )])]))
```

**Important**: The extracted file must be a valid, self-contained strategy that:
- Starts with `(defsymphony ...)`
- Has balanced brackets (use `scripts/check_balance.py` to verify)
- Contains the complete group definition

### Step 4: Create the Manifest File

Create `_manifest.json` in your strategy directory:

```json
{
  "strategy_name": "my_strategy",
  "description": "Filterable groups for My Strategy",
  "parent_strategy": "my_strategy.clj",
  "filter_config": {
    "metric": "moving-average-return",
    "window": 10,
    "selector": "select-bottom",
    "count": 1
  },
  "groups": [
    {
      "id": "my_strategy__group_a",
      "name": "Group A Name",
      "file": "group_a.clj",
      "description": "Description of what this group does"
    },
    {
      "id": "my_strategy__group_b",
      "name": "Group B Name",
      "file": "group_b.clj",
      "description": "Description of what this group does"
    }
  ],
  "created_at": "2026-02-06",
  "version": "1.0.0"
}
```

**Group ID Convention**: Use `{strategy_name}__{group_name_snake_case}` format. The double underscore separates strategy from group name.

### Step 5: Validate Bracket Balance

Run the balance checker on all your files:

```bash
for f in layers/shared/the_alchemiser/shared/strategies/filterable_groups/my_strategy/*.clj; do
  echo "=== $(basename $f) ==="
  python3 scripts/check_balance.py "$f"
done
```

All files must show "Balanced!" before proceeding.

### Step 6: Deploy and Backfill

1. **Commit and deploy**:
   ```bash
   git add layers/shared/the_alchemiser/shared/strategies/filterable_groups/my_strategy/
   make bump-patch
   make deploy-dev  # or deploy-prod
   ```

2. **Backfill historical data** (one-time):
   ```bash
   poetry run python scripts/backfill_sub_strategy_data.py --stage dev --days 30
   ```

   Adjust `--days` based on the longest lookback window your filter uses. Add a buffer (e.g., if filter uses 10-day window, backfill 30 days).

3. **Verify the cache is populated**:
   ```bash
   aws logs tail /aws/lambda/alchemiser-dev-sub-strategy-data --since 5m --format short --no-cli-pager | grep -E "(cache|groups)"
   ```

## DynamoDB Schema

Table: `GroupHistoricalSelectionsTable`

| Field | Type | Description |
|-------|------|-------------|
| `group_id` | String (HASH) | e.g., `ftl_starburst__drv_drn_mean_reversion` |
| `record_date` | String (RANGE) | ISO date, e.g., `2026-02-06` |
| `selected_portfolio` | Map | `{symbols: [...], weights: {...}}` |
| `portfolio_daily_return` | String | Decimal as string, e.g., `"0.0234"` (2.34%) |
| `evaluation_timestamp` | String | ISO timestamp of when evaluated |
| `strategy_file` | String | Path to the `.clj` file |

## Supported Filter Metrics

The cache system supports these metrics for portfolio scoring:

| DSL Metric | Description | Cached Field Used |
|------------|-------------|-------------------|
| `moving-average-return` | Average daily return over window | `portfolio_daily_return` |
| `cumulative-return` | Compound return over window | `portfolio_daily_return` |
| `stdev-return` | Volatility (annualized) | `portfolio_daily_return` |
| `max-drawdown` | Maximum peak-to-trough decline | `portfolio_daily_return` |

## Fail-Closed Behavior

If the cache has insufficient data (fewer days than the filter window requires), the scoring function returns `None` and the group is **excluded** from the filter selection. This prevents incorrect rankings based on incomplete data.

Minimum returns required: 3 days (hardcoded in `_MIN_RETURNS_FOR_METRIC`).

## Troubleshooting

### Groups not being cached (0 groups cached)

1. Check the manifest exists: `_manifest.json` must be present
2. Check file paths in manifest match actual `.clj` files
3. Check CloudWatch logs for parsing errors:
   ```bash
   aws logs tail /aws/lambda/alchemiser-dev-sub-strategy-data --since 10m --format short --no-cli-pager
   ```

### Parse errors (Missing closing RBRACKET)

Run the balance checker:
```bash
python3 scripts/check_balance.py path/to/file.clj
```

Common issues:
- Missing closing `)` or `]` at end of file
- Mismatched brackets from copy-paste errors

### MultiplexedPath errors

This is a Lambda packaging issue. The fix is in `lambda_handler.py` line ~430 which extracts the actual filesystem path from `MultiplexedPath._paths[0]`.

## Files Reference

| File | Purpose |
|------|---------|
| `functions/sub_strategy_data/lambda_handler.py` | Daily cache population Lambda |
| `functions/strategy_worker/engines/dsl/operators/group_cache_lookup.py` | Cache query utilities |
| `functions/strategy_worker/engines/dsl/operators/portfolio.py` | Portfolio scoring with cache |
| `scripts/backfill_sub_strategy_data.py` | Historical data backfill script |
| `scripts/check_balance.py` | Bracket balance validator |

## Example: ftl_starburst

The `ftl_starburst/` directory contains three groups extracted from `ftl_starburst.clj`:

1. **drv_drn_mean_reversion.clj** - DRV/DRN real estate mean reversion
2. **labu_labd_mean_reversion.clj** - LABU/LABD biotech mean reversion  
3. **yinn_yang_mean_reversion.clj** - YINN/YANG China mean reversion

These groups are filtered by `(moving-average-return {:window 10}) (select-bottom 1)` in the parent strategy, selecting the group with the lowest 10-day average return.
