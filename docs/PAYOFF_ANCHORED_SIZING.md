# Payoff-Anchored Options Hedging Implementation

## Summary

This implementation transforms the options hedging system from **budget-first** to **payoff-first** sizing, with explicit budget constraint clipping and rolling 12-month spend tracking.

## Key Changes

### 1. PayoffCalculator (`payoff_calculator.py`)

**Purpose**: Calculate contract sizing to achieve specific payoff targets at scenario moves.

**Key Features**:
- Scenario-based sizing: Given a market move (e.g., -20%), calculate contracts needed to achieve target payoff (e.g., +8% NAV)
- Leverage adjustment: Scales target payoff by portfolio leverage factor
- Strike estimation: Uses delta as proxy for OTM percentage
- Premium estimation: Rule-of-thumb estimates for budget checking

**Example**:
```python
scenario = PayoffScenario(
    scenario_move_pct=Decimal("-0.20"),  # -20% market crash
    target_payoff_pct=Decimal("0.08"),   # +8% NAV target
    description="-20% crash scenario"
)

result = calculator.calculate_contracts_for_scenario(
    underlying_price=Decimal("500"),
    option_delta=Decimal("0.15"),  # 15-delta put
    scenario=scenario,
    nav=Decimal("100000"),
    leverage_factor=Decimal("2.0")
)
# Returns: 7 contracts needed for 16% NAV payoff (8% * 2x leverage)
```

### 2. PremiumTracker (`premium_tracker.py`)

**Purpose**: Track rolling 12-month premium spend and enforce annual caps.

**Key Features**:
- Rolling window tracking: Automatically expires spend records older than 12 months
- Spend cap enforcement: Checks proposed spend against 5% NAV annual cap (configurable)
- Fail-closed behavior: Refuses hedges when cap would be exceeded
- Detailed reporting: Provides transparency on current spend vs capacity

**Example**:
```python
tracker = PremiumTracker()

# Add historical spend
tracker.add_spend(
    amount=Decimal("4000"),
    hedge_id="hedge-001",
    description="Q1 hedges",
    timestamp=datetime.now(UTC) - timedelta(days=90)
)

# Check if new spend is allowed
check_result = tracker.check_spend_within_cap(
    proposed_spend=Decimal("2000"),
    nav=Decimal("100000")
)

if not check_result.is_within_cap:
    # Hedge refused: $6,000 total would exceed $5,000 cap (5% NAV)
    print(f"Remaining capacity: ${check_result.remaining_capacity}")
```

### 3. Updated HedgeSizer (`hedge_sizer.py`)

**Purpose**: Integrate payoff-first sizing with budget constraints.

**New Workflow**:
1. Calculate VIX-adaptive budget cap (as before)
2. **NEW**: Calculate contracts needed for target payoff at scenario move
3. **NEW**: Estimate premium cost for those contracts
4. **NEW**: Clip to budget if needed, emit explicit report
5. **NEW**: Check rolling 12-month spend cap via PremiumTracker

**Example Output**:
```
Target: 8.0% NAV at -20% move (5 contracts).
Affordable: 2.4% NAV at -20% move (1 contracts, clipped by premium cap).
```

### 4. HedgeRecommendation Fields

**New Fields**:
- `target_payoff_pct`: Target payoff as % of NAV
- `scenario_move_pct`: Scenario move used for sizing
- `contracts_for_target`: Contracts needed for target payoff (before clipping)
- `was_clipped_by_budget`: Whether budget cap reduced contracts
- `clip_report`: Human-readable clipping explanation

## Config Integration

The implementation uses existing config parameters:
- `scenario_move`: From TAIL_HEDGE_TEMPLATE (-20%)
- `min_payoff_nav_pct` / `max_payoff_nav_pct`: Target payoff range (6-10% for tail)
- `budget_vix_low/mid/high`: VIX-adaptive budget caps (0.8%, 0.5%, 0.3%)
- `MAX_ANNUAL_PREMIUM_SPEND_PCT`: Annual cap (5% NAV)

## Acceptance Criteria Met

✅ **Sizing starts from payoff targets, not budget**
   - PayoffCalculator calculates contracts for target payoff first
   - Budget is secondary constraint that clips if needed

✅ **Contract count calculated to achieve target payoff at scenario moves**
   - Uses delta-based strike estimation
   - Calculates expected payoff per contract at scenario price
   - Rounds up to ensure target is met or exceeded

✅ **Premium cap clips contracts with explicit reporting**
   - Compares estimated premium to budget cap
   - Clips contracts to affordable amount
   - Emits report: "Target: X% NAV (N contracts). Affordable: Y% NAV (M contracts, clipped by premium cap)."

✅ **Rolling 12-month spend tracker implemented**
   - PremiumTracker maintains rolling window
   - Automatically expires old records
   - Provides detailed reporting

✅ **System refuses hedges when spend cap exceeded**
   - HedgeSizer.should_hedge() checks PremiumTracker
   - Returns (False, reason) when cap would be exceeded
   - Fail-closed behavior: default to safety

## Testing

### Unit Tests (`test_payoff_anchored_sizing.py`)
- ✅ PayoffCalculator basic scenarios
- ✅ PayoffCalculator with leverage
- ✅ Premium cost estimation
- ✅ PremiumTracker basic tracking
- ✅ PremiumTracker cap enforcement (reject over cap)
- ✅ PremiumTracker cap enforcement (accept within cap)
- ✅ PremiumTracker rolling window expiration

### Integration Tests (`test_hedge_sizer_integration.py`)
- ✅ HedgeSizer produces payoff-first recommendations
- ✅ PremiumTracker enforces spend cap in HedgeSizer
- ✅ Budget clipping produces explicit reports

## Example Workflow

```python
# Setup
tracker = PremiumTracker()
tracker.load_history_from_records(historical_spend)  # Load past 12 months

sizer = HedgeSizer(template="tail_first", premium_tracker=tracker)

# Calculate recommendation
recommendation = sizer.calculate_hedge_recommendation(
    exposure=portfolio_exposure,  # 2x leverage, $100k NAV
    current_vix=Decimal("18"),
    underlying_price=Decimal("485")
)

# Result:
# - Scenario: -20% market move
# - Target payoff: 8% NAV (adjusted for leverage → 12%)
# - Contracts for target: 5
# - Estimated premium: $3,637
# - Budget cap: $750 (0.75% NAV)
# - Was clipped: True
# - Contracts affordable: 1
# - Clip report: "Target: 8.0% NAV at -20% move (5 contracts). 
#                 Affordable: 2.4% NAV at -20% move (1 contracts, clipped by premium cap)."

# Check spend cap
should_hedge, reason = sizer.should_hedge(
    exposure=portfolio_exposure,
    proposed_spend=recommendation.premium_budget
)

if should_hedge:
    execute_hedge(recommendation)
else:
    log_rejection(reason)
    # Example reason: "Rolling 12-month spend cap would be exceeded (current: 4.50%, after: 5.25%, cap: 5.0%)"
```

## Migration Notes

**Backward Compatibility**:
- PremiumTracker is optional in HedgeSizer constructor
- If not provided, falls back to check_annual_spend_cap() function
- Existing code continues to work without modification

**Deployment**:
- New classes are in `shared/options/` module
- No database schema changes required
- PremiumTracker state can be loaded from DynamoDB hedge history

**Future Enhancements**:
- Persist PremiumTracker state to DynamoDB
- Add scenario stress tests (multiple moves)
- Support custom scenario definitions per template
- Add payoff optimization (maximize payoff for given budget)
