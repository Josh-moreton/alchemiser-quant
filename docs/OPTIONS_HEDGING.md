# Options Hedging Module

## Overview

The Alchemiser options hedging module provides automated downside protection via protective puts on broad market ETFs. It integrates with the existing portfolio rebalancing workflow to automatically evaluate and execute hedge positions.

## Objective

**Reduce equity drawdowns of a 2.0x–2.5x leveraged book by 6–10% NAV under -20% index scenarios, with ≤4% annual premium drag.**

This objective is measurable and locks in the hedging strategy's expectations:
- **Target Protection**: 6–10% NAV payoff when underlying (QQQ/SPY) moves -20%
- **Cost Constraint**: Maximum 4% of NAV spent annually on premiums (≤0.35% per month)
- **Portfolio Profile**: Optimized for 2.0x–2.5x leveraged, tech-heavy portfolios

### What This Is NOT

**This hedging strategy will NOT fully hedge a -20% index move on a 2.5x book.**

With 2.5x leverage and -20% underlying move, the unhedged loss would be -50% NAV. The hedges provide partial mitigation (6–10% NAV), reducing the loss to approximately -40–44% NAV. This is crash insurance, not full portfolio insurance.

The module prioritizes cost-efficiency over complete protection. Full hedging of 2.5x leverage would require prohibitively expensive premiums that would eliminate long-term returns.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAILY WORKFLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     RebalancePlanned      ┌───────────────────┐           │
│  │   Portfolio  │ ─────────────────────────▶│  HedgeEvaluator   │           │
│  │   Lambda     │     (EventBridge)         │     Lambda        │           │
│  └──────────────┘                           └─────────┬─────────┘           │
│         │                                             │                     │
│         │ 3:30 PM ET                                  │                     │
│         ▼                                             ▼                     │
│  ┌──────────────┐                           ┌───────────────────┐           │
│  │  Equity      │                           │   SQS Queue       │           │
│  │  Trades      │                           │  (HedgeEvaluation │           │
│  └──────────────┘                           │   Completed)      │           │
│                                             └─────────┬─────────┘           │
│                                                       │                     │
│                                                       ▼                     │
│                                             ┌───────────────────┐           │
│                                             │  HedgeExecutor    │           │
│                                             │     Lambda        │           │
│                                             └─────────┬─────────┘           │
│                                                       │                     │
│                                      ┌────────────────┼────────────────┐    │
│                                      ▼                ▼                ▼    │
│                               ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│                               │ Alpaca   │    │ DynamoDB │    │EventBridge│ │
│                               │ Options  │    │ Positions│    │  Events   │ │
│                               │   API    │    │  Table   │    │           │ │
│                               └──────────┘    └──────────┘    └──────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ROLL MANAGEMENT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     Scheduled (3:45 PM ET)    ┌───────────────────┐       │
│  │  EventBridge │ ─────────────────────────────▶│  HedgeRollManager │       │
│  │   Schedule   │                               │      Lambda       │       │
│  └──────────────┘                               └─────────┬─────────┘       │
│                                                           │                 │
│                                                           ▼                 │
│                                                 ┌───────────────────┐       │
│                                                 │  Scan DynamoDB    │       │
│                                                 │  for DTE < 45     │       │
│                                                 └─────────┬─────────┘       │
│                                                           │                 │
│                                                           ▼                 │
│                                                 ┌───────────────────┐       │
│                                                 │ HedgeRollTriggered│       │
│                                                 │    (EventBridge)  │       │
│                                                 └───────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Lambda Functions

| Function | Handler | Trigger | Timeout | Memory |
|----------|---------|---------|---------|--------|
| `HedgeEvaluatorFunction` | `hedge_evaluator.lambda_handler` | EventBridge (RebalancePlanned) | 300s | 512 MB |
| `HedgeExecutorFunction` | `hedge_executor.lambda_handler` | SQS Queue | 600s | 1024 MB |
| `HedgeRollManagerFunction` | `hedge_roll_manager.lambda_handler` | EventBridge Schedule | 300s | 512 MB |

### DynamoDB Tables

#### HedgePositionsTable

Stores active and historical hedge positions.

| Attribute | Type | Description |
|-----------|------|-------------|
| `hedge_id` (PK) | String | Unique hedge identifier |
| `underlying_symbol` (GSI) | String | Underlying ETF (QQQ, SPY, etc.) |
| `option_symbol` | String | OCC option symbol |
| `expiration_date` | String | ISO date of expiration |
| `strike_price` | Number | Strike price |
| `contracts` | Number | Number of contracts |
| `entry_price` | Number | Average fill price |
| `entry_date` | String | ISO datetime of entry |
| `state` | String | ACTIVE, CLOSED, ROLLED, EXPIRED |
| `roll_state` | String | HOLDING, PENDING_ROLL, ROLLED |
| `hedge_template` | String | tail_first or smoothing |

#### HedgeHistoryTable

Audit trail for all hedge actions.

| Attribute | Type | Description |
|-----------|------|-------------|
| `account_id` (PK) | String | Account identifier |
| `timestamp` (SK) | String | ISO datetime |
| `action` | String | OPENED, CLOSED, ROLLED, EVALUATION_COMPLETED, etc. |
| `hedge_id` | String | Related hedge ID |
| `correlation_id` | String | Trace ID |
| `details` | Map | Action-specific metadata |

### SQS Queues

#### HedgeExecutionQueue

- **Visibility Timeout**: 900 seconds (15 minutes)
- **Message Retention**: 4 days
- **DLQ**: `HedgeExecutionDLQ` (max 3 retries)

---

## Hedge Strategy

### Tail-Risk Hedge Template (Default)

The tail-risk template uses out-of-the-money puts for crash protection:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Option Type** | Put | Downside protection |
| **Target Delta** | 0.30 | Balance between cost and protection |
| **Target DTE** | 90 days | Time for recovery, avoid rapid theta decay |
| **Strike Range** | 75-95% of underlying | OTM puts |
| **Roll Trigger** | DTE < 45 days | Roll before theta accelerates |
| **Max Concentration** | 2% of NAV per position | Risk management |

### VIX-Adaptive Budget

Premium budget adjusts based on market volatility (VIX):

| VIX Level | Threshold | Target (% NAV) | Rationale |
|-----------|-----------|----------------|-----------|
| Low | < 18 | 0.80% | Protection is cheap, buy more |
| Mid | 18-28 | 0.50% | Standard allocation |
| High | > 28 | 0.30% | Protection expensive, reduce size |

**Important**: VIX-tier rates are *allocation targets*, not guarantees. Actual spend is clamped by the **hard monthly cap (0.35% NAV/month)**. When VIX is low and the tier target is 0.80%, the system will still respect the 0.35% monthly cap—the difference is that low-VIX conditions make it easier to get quality protection within that cap.

**VIX Estimation**: Uses VIXY ETF as proxy (`VIXY price × 10 ≈ VIX index`). The scaling factor is monitored via CloudWatch logs for drift.

### Position Sizing Formula

```
exposure = NAV × net_exposure_ratio × beta_adjustment
premium_budget = NAV × vix_tier_rate × exposure_multiplier
contracts = floor(premium_budget / (contract_price × 100))
```

Where:
- `net_exposure_ratio` = sum of position values / NAV
- `beta_adjustment` = weighted average beta of holdings to underlying
- `exposure_multiplier` = min(1.0, exposure / NAV)
- `contract_price` = ask price (or mid if ask unavailable)

### Sector Mapping

Holdings are mapped to broad market ETFs based on sector:

| Sector | Primary ETF | Fallback |
|--------|-------------|----------|
| Technology | QQQ | SPY |
| Consumer Discretionary | QQQ | SPY |
| Communication Services | QQQ | SPY |
| Healthcare | SPY | IWM |
| Financials | SPY | IWM |
| Industrials | SPY | IWM |
| Consumer Staples | SPY | - |
| Energy | SPY | - |
| Utilities | SPY | - |
| Materials | SPY | IWM |
| Real Estate | IWM | SPY |

The system aggregates to a single hedge underlying using the **80% rule**: if QQQ exposure is within 20% of the maximum, prefer QQQ for its liquidity.

---

## Event Schemas

### HedgeEvaluationCompleted

Published by HedgeEvaluator to SQS:

```json
{
  "event_type": "HedgeEvaluationCompleted",
  "correlation_id": "uuid",
  "plan_id": "rebalance-plan-uuid",
  "portfolio_nav": "150000.00",
  "recommendations": [
    {
      "underlying_symbol": "QQQ",
      "target_delta": "0.30",
      "target_dte": 90,
      "premium_budget": "750.00",
      "contracts_estimated": 3,
      "hedge_template": "tail_first"
    }
  ],
  "total_premium_budget": "750.00",
  "budget_nav_pct": "0.005",
  "vix_tier": "mid",
  "exposure_multiplier": "1.0",
  "skip_reason": null
}
```

### HedgeExecuted

Published per executed hedge order:

```json
{
  "event_type": "HedgeExecuted",
  "correlation_id": "uuid",
  "hedge_id": "hedge-uuid",
  "plan_id": "rebalance-plan-uuid",
  "order_id": "alpaca-order-id",
  "option_symbol": "QQQ260417P00450000",
  "underlying_symbol": "QQQ",
  "quantity": 3,
  "filled_price": "8.50",
  "total_premium": "2550.00",
  "nav_percentage": "0.017",
  "success": true,
  "error_message": null
}
```

### AllHedgesCompleted

Published when all hedges in a cycle complete:

```json
{
  "event_type": "AllHedgesCompleted",
  "correlation_id": "uuid",
  "plan_id": "rebalance-plan-uuid",
  "total_hedges": 1,
  "succeeded_hedges": 1,
  "failed_hedges": 0,
  "total_premium_spent": "2550.00",
  "total_nav_pct": "0.017",
  "hedge_positions": [...],
  "failed_symbols": [],
  "was_skipped": false
}
```

### HedgeRollTriggered

Published when a position needs rolling:

```json
{
  "event_type": "HedgeRollTriggered",
  "correlation_id": "uuid",
  "hedge_id": "hedge-uuid",
  "option_symbol": "QQQ260117P00440000",
  "underlying_symbol": "QQQ",
  "current_dte": 38,
  "current_contracts": 3,
  "roll_reason": "dte_threshold"
}
```

---

## Skip Conditions

Hedging is **automatically skipped** when:

| Condition | Threshold | Reason |
|-----------|-----------|--------|
| Low NAV | < $10,000 | Minimum viable hedge size |
| Low Exposure | < 0.5x | Insufficient equity exposure |
| Existing Hedges | ≥ 3 active | Avoid over-hedging |
| No Positions | 0 equities | Nothing to hedge |

Skip events are logged and a `HedgeEvaluationCompleted` with `skip_reason` is published.

---

## Execution Details

### Contract Selection

The `OptionSelector` finds the optimal contract:

1. Query option chain from Alpaca (strike range: 75-95% of underlying)
2. Filter by target DTE (±15 days from target)
3. Score candidates by delta proximity to target
4. Select contract with best delta match
5. Validate budget allows at least 1 contract

### Order Placement

1. Calculate limit price: `mid_price × 0.98` (2% discount)
2. Place limit order with `time_in_force: day`
3. Poll order status every 2 seconds (up to 5 minutes)
4. Record result to DynamoDB

### Spread Order Retry Logic

For spread orders (long + short leg):

1. Execute long leg first
2. If short leg fails, retry up to 3 times with exponential backoff
3. If all retries fail, attempt compensating close on long leg
4. If compensating close fails, log for manual reconciliation

---

## Configuration

### Environment Variables

| Variable | Function | Description |
|----------|----------|-------------|
| `HEDGE_POSITIONS_TABLE_NAME` | All hedge Lambdas | DynamoDB table for positions |
| `HEDGE_HISTORY_TABLE_NAME` | All hedge Lambdas | DynamoDB table for audit trail |
| `HEDGE_EXECUTION_QUEUE_URL` | Evaluator, Roll Manager | SQS queue URL |
| `HEDGE_ACCOUNT_ID` | Roll Manager | Account ID for audit records |
| `ALPACA__KEY` | Evaluator, Executor | Alpaca API key |
| `ALPACA__SECRET` | Evaluator, Executor | Alpaca API secret |
| `ALPACA__ENDPOINT` | Executor | Alpaca endpoint (paper/live) |

### Constants (hedge_config.py)

```python
# VIX thresholds
VIX_LOW_THRESHOLD = Decimal("18")
VIX_HIGH_THRESHOLD = Decimal("28")

# Budget rates by VIX tier (% NAV per month)
BUDGET_VIX_LOW = Decimal("0.008")   # 0.8% NAV/month
BUDGET_VIX_MID = Decimal("0.005")   # 0.5% NAV/month  
BUDGET_VIX_HIGH = Decimal("0.003")  # 0.3% NAV/month

# Position limits
MIN_NAV_FOR_HEDGING = Decimal("10000")
MIN_EXPOSURE_RATIO = Decimal("0.5")
MAX_EXISTING_HEDGES = 3
MAX_SINGLE_POSITION_PCT = Decimal("0.02")  # 2% NAV

# Roll parameters
ROLL_TRIGGER_DTE = 45
CRITICAL_DTE_THRESHOLD = 14

# ═══════════════════════════════════════════════════════════════
# HARD CONSTRAINTS (Locked Objectives)
# ═══════════════════════════════════════════════════════════════

# Maximum premium spend caps
MAX_PREMIUM_SPEND_ANNUAL_PCT = Decimal("0.04")    # 4% NAV/year maximum
MAX_PREMIUM_SPEND_MONTHLY_PCT = Decimal("0.0035") # 0.35% NAV/month maximum

# Minimum protection floor
MIN_PROTECTION_AT_MINUS_20_PCT = Decimal("0.06")  # 6% NAV minimum payoff at -20% move

# Fallback behavior when minimum protection is unaffordable
PROTECTION_SHORTFALL_FALLBACK = "clip_and_report"
# Options: "clip_and_report" | "switch_template" | "skip"
# - clip_and_report: Buy maximum affordable protection and log shortfall
# - switch_template: Try alternative hedge template (e.g., smoothing)  
# - skip: Do not hedge if minimum protection cannot be met
```

#### Hard Constraints Explained

The hard constraints lock the objectives and prevent the hedging system from drifting:

1. **Annual Premium Cap (4% NAV/year)**: Prevents excessive hedging costs from eroding returns over time. For a $150,000 portfolio, this limits annual premium spend to $6,000.

2. **Monthly Premium Cap (0.35% NAV/month)**: Prevents concentrated hedging in a single period. For a $150,000 portfolio, this limits monthly spend to $525. **This cap overrides VIX-tier targets**—if VIX is low and the tier target is 0.8%, actual spend is clamped to 0.35%.

3. **Protection Floor (6% NAV at -20%)**: Ensures hedges provide meaningful protection in severe drawdowns. For a 2.5x leveraged $150,000 portfolio ($375,000 exposure), a -20% move causes -$75,000 loss. The hedge must pay out at least $9,000 (6% of NAV) to be worthwhile.

4. **Fallback Behavior**: When the system cannot afford to meet the protection floor within budget:
   - **clip_and_report** (default): Buy the maximum affordable protection and log the shortfall for manual review
   - **switch_template**: Attempt to use a lower-cost hedge template (e.g., put spreads)
   - **skip**: Do not hedge at all if minimum protection cannot be met

#### Constraint Hierarchy

```
VIX-Tier Target (0.3%-0.8%)  ←  Soft target based on market conditions
        ↓
Monthly Hard Cap (0.35%)     ←  Clamps VIX target; prevents monthly overspend
        ↓
Annual Hard Cap (4%)         ←  Cumulative limit; rejects orders if exceeded
        ↓
Protection Floor (6% NAV)    ←  Validates payoff quality; triggers fallback if unmet
```

---

## Monitoring & Observability

### CloudWatch Logs

Key log entries to monitor:

| Log Pattern | Meaning |
|-------------|---------|
| `Hedge evaluation completed` | Successful evaluation |
| `Hedge evaluation was skipped` | Skip condition met |
| `Hedge execution completed` | Order filled |
| `No suitable contract found` | Option chain issue |
| `VIX proxy drift monitoring` | Track scaling factor accuracy |
| `manual reconciliation required` | CRITICAL: Failed compensating close |

### Metrics to Track

- Hedge evaluation frequency
- Skip rate by reason
- Fill rate (successful / attempted)
- Average premium as % NAV
- Roll trigger frequency
- DLQ message count

### Alerts

Configure CloudWatch alarms for:

- DLQ messages > 0 (execution failures)
- `manual reconciliation required` log pattern
- Hedge executor Lambda errors

---

## Operational Procedures

### Manual Position Check

Query active positions via AWS Console or CLI:

```bash
aws dynamodb scan \
  --table-name alchemiser-dev-hedge-positions \
  --filter-expression "#s = :active" \
  --expression-attribute-names '{"#s": "state"}' \
  --expression-attribute-values '{":active": {"S": "ACTIVE"}}' \
  --no-cli-pager
```

### Force Roll Check

Manually invoke roll manager:

```bash
aws lambda invoke \
  --function-name alchemiser-dev-hedge-roll-manager \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --no-cli-pager
```

### Disable Hedging Temporarily

1. Disable the EventBridge rule `RebalancePlannedToHedgeRule` in AWS Console
2. Or set `MIN_NAV_FOR_HEDGING` extremely high temporarily

### Manual Hedge Execution

Directly invoke hedge evaluator with test event:

```bash
aws lambda invoke \
  --function-name alchemiser-dev-hedge-evaluator \
  --payload file://test-rebalance-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --no-cli-pager
```

---

## Troubleshooting

### Common Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| No hedges placed | Skip reason logged | Check NAV, exposure, existing hedges |
| Contract not found | "No suitable contract" log | Verify underlying has options, check strike range |
| Order not filling | Order times out | Adjust limit price discount factor |
| VIX tier incorrect | Budget seems wrong | Check VIXY price availability |
| Roll not triggering | Positions not rolling | Verify DynamoDB query, check DTE calculation |

### Alpaca Options API Issues

- **403 Forbidden**: Account not approved for options
- **422 Unprocessable**: Invalid order parameters (check symbol format)
- **429 Rate Limited**: Reduce concurrent executions

---

## Prerequisites

1. **Alpaca Account**: Must have options trading enabled
2. **API Credentials**: Same keys used for equity trading
3. **AWS Resources**: Deployed via SAM (`make deploy-dev` or `make deploy`)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 10.0.0 | 2026-01-26 | Initial options hedging implementation |
