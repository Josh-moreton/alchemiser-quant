# Strategies with Filters Applied to Groups

## The Problem

The DSL engine computes indicator values (e.g. `cumulative-return`, `moving-average-return`,
`stdev-return`, `rsi`) by looking up price history for a **single ticker symbol**. When a
`(filter ...)` operator's children are `(asset ...)` nodes this works naturally -- each asset
maps to one ticker.

When a `(filter ...)` operator's children include `(group ...)` nodes, the engine has no
built-in ticker to query. A group is a conditional sub-portfolio that may resolve to
different assets on different days. Without historical context the engine cannot produce a
meaningful time-series for the group, so the indicator value is either missing or
incorrectly computed. This causes the filter to rank groups unreliably.

### Affected Strategies

| Strategy | File | Filter Indicator | What Gets Filtered |
|----------|------|-------------------|--------------------|
| FTL Starburst | `ftl_starburst.clj` | Various (`cumulative-return`, `stdev-return`, etc.) | Groups used as children of filter operators |
| What Have I Done | `what_have_i_done.clj` | `moving-average-return {:window 10}` | Two top-level groups: "Rally Rider + V1a WMDYN" vs "Rally Rider + V1a WAM FTLT" |
| What Have I Done | `what_have_i_done.clj` | `moving-average-return {:window 4}` | Assets mixed with "LAB Check Bull"/"LAB Check Bear" groups (~8 filter instances) |

## The Fix: DynamoDB Group Cache

To support indicators on groups we pre-compute and cache each group's daily portfolio
return in DynamoDB (`GroupHistoricalSelectionsTable`). At evaluation time the engine
looks up the cached return series and computes the requested metric over it, exactly
as it would for a single-ticker price series.

### Architecture

```
backfill_group_cache.py          group_scoring.py (Lambda)
========================         ========================
1. Parse .clj strategy           1. Filter encounters a group child
2. Walk AST to find groups       2. Derive group_id from name
   that are children of filter   3. Query DynamoDB for cached returns
3. For each trading day:         4. If cache has enough data:
   a. Set as_of_date                compute metric from cached series
   b. Evaluate group AST body    5. If cache is insufficient:
   c. Get resulting weights         trigger on-demand backfill
   d. Compute portfolio return      (re-evaluate group AST body for
   e. Write to DynamoDB              each missing day, write to cache)
```

### Key Files

| File | Purpose |
|------|---------|
| `scripts/backfill_group_cache.py` | Offline backfill script -- pre-populates DynamoDB cache |
| `functions/strategy_worker/engines/dsl/operators/group_scoring.py` | Runtime scoring and on-demand backfill within Lambda |
| `functions/strategy_worker/engines/dsl/operators/group_cache_lookup.py` | DynamoDB read/write operations for cached returns |

### Backfill Commands

```bash
# Backfill last 45 days (default) for a strategy
poetry run python scripts/backfill_group_cache.py \
    layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj

# Backfill ALL available history
poetry run python scripts/backfill_group_cache.py \
    layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj --all

# Dry run (compute but don't write)
poetry run python scripts/backfill_group_cache.py \
    layers/shared/the_alchemiser/shared/strategies/what_have_i_done.clj --dry-run

# Filter specific groups by name pattern
poetry run python scripts/backfill_group_cache.py \
    what_have_i_done.clj --group "LAB Check*"
```

### Current Status

- **ftl_starburst.clj**: Cache backfilled. Needs ongoing daily maintenance
  (the Lambda performs on-demand backfill for recent days, but a full historical
  backfill should be run after deploying changes).
- **what_have_i_done.clj**: Needs initial backfill. Has two distinct problem
  patterns:
  1. Top-level filter selecting between two entire strategy sub-trees
  2. Inner filters ranking 6-8 assets alongside a conditional "LAB Check" group

### Remaining Work

- Run full backfill for `what_have_i_done.clj`
- Validate signal output matches expected behaviour after cache is populated
- Consider whether the on-demand backfill path in Lambda is sufficient for
  day-to-day operation, or whether a scheduled backfill job is needed
- Investigate whether any new strategies added in future introduce this pattern
  (the `backfill_group_cache.py` script auto-discovers affected groups)
