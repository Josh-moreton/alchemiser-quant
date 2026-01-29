# Options Hedging Module

## Overview

The Alchemiser options hedging module provides automated downside protection via protective puts on broad market ETFs. It integrates with the existing portfolio rebalancing workflow to automatically evaluate and execute hedge positions.

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

| VIX Level | Threshold | Budget (% NAV/month) | Annual (×12) | At 1.0x | At 2.0x | At 2.5x |
|-----------|-----------|----------------------|--------------|---------|---------|---------|
| Low | < 18 | 0.80% | 9.6% | 9.6% | 14.4% | 16.8% |
| Mid | 18-28 | 0.50% | 6.0% | 6.0% | 9.0% | 10.5% |
| High | > 28 | 0.30% | 3.6% | 3.6% | 5.4% | 6.3% |
| Rich | > 35 | Reduced intensity | - | - | - | - |

**Notes:**
- Annual drag = monthly rate × 12 months × exposure multiplier
- Exposure multiplier at 1.0x leverage: 1.0
- Exposure multiplier at 2.0x leverage: 1.5 (sublinear scaling)
- Exposure multiplier at 2.5x leverage: 1.75
- **Hard cap: 5% NAV/year** to prevent excessive drag
- **Target band: 2-5% NAV/year** for sustainable protection

**VIX Estimation**: Uses VIXY ETF as proxy (`VIXY price × 10 ≈ VIX index`). The scaling factor is monitored via CloudWatch logs for drift.

### Annual Premium Spend Target

The system enforces an annual premium spend target band to prevent excessive drag:

- **Minimum target**: 2% NAV/year (ensure adequate protection)
- **Maximum target**: 5% NAV/year (prevent excessive cost)
- **Hard cap**: 5% NAV/year (strictly enforced)

Spend tracking:
- Year-to-date premium spend tracked in DynamoDB
- Each hedge evaluation checks against annual cap
- Hedges skipped if cap would be exceeded

### Rich IV Reduction Logic

When implied volatility is rich (VIX > 35), the system automatically reduces hedge intensity to avoid overpaying:

1. **Widen delta target**: Move from 15-delta to 10-delta (further OTM, cheaper)
2. **Extend tenor**: Increase DTE from 90 to 120 days (better theta efficiency)
3. **Reduce target payoff**: Lower payoff target by 25% (less protection needed)

Rationale: When volatility is already elevated, options are expensive and the market has likely already repriced risk. Buying less protection at these times is economically rational.

### Carry Expectation & Trade-offs

**Expected Theta Bleed in Normal Regimes:**

The hedge portfolio exhibits negative carry (theta decay) by design:

| Market Regime | Expected Monthly Bleed | Expected Annual Drag | Trade-off |
|---------------|------------------------|----------------------|-----------|
| Low VIX (<18) | 0.8% NAV/month | 9.6% at 1.0x, 14.4% at 2.0x | Higher cost for cheaper protection |
| Mid VIX (18-28) | 0.5% NAV/month | 6.0% at 1.0x, 9.0% at 2.0x | Balanced cost/protection |
| High VIX (>28) | 0.3% NAV/month | 3.6% at 1.0x, 5.4% at 2.0x | Lower cost but already in stress |
| Rich IV (>35) | Reduced intensity | < 5% at 2.0x | Minimal spend when options expensive |

**Trade-offs Being Accepted:**

1. **Negative carry**: We accept 2-5% NAV/year drag in exchange for:
   - Convex payoff in market crashes (-20% market → +6-10% NAV)
   - Sleep-at-night insurance for leveraged portfolio (2.0x-2.5x)
   - Capital preservation to redeploy at market bottoms

2. **Counter-intuitive timing**: We buy MORE protection when VIX is LOW:
   - Options are cheaper when volatility is compressed
   - Already own protection when volatility expands
   - Avoid panic buying at rich IV levels

3. **Sublinear scaling**: At 2.0x leverage, we only pay 1.5x the base premium:
   - Avoids overpaying at extremes
   - Recognizes diminishing returns of additional protection
   - Balances cost efficiency with risk management

**Acceptable Scenarios:**
- ✅ Portfolio drops 20%, hedge gains 6-10% → Net -10% to -14% (vs -40% unhedged at 2.0x)
- ✅ Portfolio flat for year, lose 2-5% to theta → Insurance premium paid
- ❌ Portfolio up 30%, lose 2-5% to theta → Underperformance vs unhedged

**Unacceptable Scenarios:**
- ❌ Annual drag exceeds 5% NAV (hard cap prevents this)
- ❌ Hedges fail to deliver during actual crash (payoff-based sizing prevents this)

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
| **Annual Cap Exceeded** | **≥ 5% NAV YTD** | **Prevent excessive annual drag** |

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
RICH_IV_THRESHOLD = Decimal("35")  # Reduce hedge intensity above this

# Budget rates by VIX tier
BUDGET_VIX_LOW = Decimal("0.008")   # 0.8% NAV/month
BUDGET_VIX_MID = Decimal("0.005")   # 0.5% NAV/month  
BUDGET_VIX_HIGH = Decimal("0.003")  # 0.3% NAV/month

# Annual spend limits (hard caps to prevent excessive drag)
MAX_ANNUAL_PREMIUM_SPEND_PCT = Decimal("0.05")  # 5% NAV/year hard cap
TARGET_ANNUAL_PREMIUM_SPEND_MIN_PCT = Decimal("0.02")  # 2% NAV/year minimum
TARGET_ANNUAL_PREMIUM_SPEND_MAX_PCT = Decimal("0.05")  # 5% NAV/year maximum

# Position limits
MIN_NAV_FOR_HEDGING = Decimal("10000")
MIN_EXPOSURE_RATIO = Decimal("0.5")
MAX_EXISTING_HEDGES = 3
MAX_SINGLE_POSITION_PCT = Decimal("0.02")  # 2% NAV

# Roll parameters
ROLL_TRIGGER_DTE = 45
CRITICAL_DTE_THRESHOLD = 14
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
- **Year-to-date premium spend as % NAV**
- **Annual drag rate (actual vs target band)**
- Roll trigger frequency
- DLQ message count
- **Rich IV reduction trigger frequency**

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
