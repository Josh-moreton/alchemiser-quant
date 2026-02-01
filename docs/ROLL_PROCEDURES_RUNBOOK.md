# Roll Procedures Runbook

## Overview

This document provides comprehensive operational procedures for rolling options hedge positions in the Alchemiser hedging system. Rolling involves closing an expiring or suboptimal position and opening a replacement position with a later expiration date or more appropriate strikes.

## Objective

Execute timely and cost-efficient roll operations to:
1. Maintain continuous downside protection
2. Optimize time decay and carry costs
3. Adapt to changing market regimes (volatility, skew, delta drift)
4. Minimize transaction costs and slippage

## Roll Strategy by Template

### Template 1: Tail Hedge (15-Delta OTM Puts)

**Primary Strategy**: DTE-based rolling with regime adjustments

**Configuration**:
- Target DTE: 90 days
- Roll trigger DTE: 45 days
- Target delta: 0.15 (15-delta OTM puts)
- Underlying: QQQ (tech-heavy portfolio correlation)

#### Roll Triggers - Tail Template

| Trigger Type | Threshold | Action | Priority |
|--------------|-----------|--------|----------|
| **DTE Threshold** | DTE < 45 | Mandatory roll | **High** |
| **DTE Critical** | DTE < 14 | Urgent roll | **Critical** |
| **Delta Drift** | Δ moves > 10 delta points | Roll to restore target delta | **Medium** |
| **Extrinsic Value Decay** | Extrinsic < 20% of entry premium | Consider profit-taking roll | **Medium** |
| **Skew Regime Change** | IV skew > +2 std dev | Adjust strikes or widen spreads | **Low** |
| **Rich IV** | VIX > 35 | Widen delta, extend tenor, or skip | **Medium** |

#### Delta Drift Roll Trigger

**Configuration**: `TAIL_DELTA_DRIFT_THRESHOLD = 0.10` (10 delta points)

**Logic**:
- Entry delta: 0.15 (15-delta put)
- Current delta: Monitor daily
- Trigger: If `abs(current_delta - entry_delta) > 0.10`
- Example: 15-delta put moves to 28-delta (ITM drift) → Roll to restore OTM structure

**Rationale**: Hedge should remain OTM for optimal gamma/vega exposure. If delta drifts significantly ITM or OTM, roll to restore target profile.

**Action**:
```python
# Pseudo-code
if abs(current_delta - entry_delta) > TAIL_DELTA_DRIFT_THRESHOLD:
    if current_delta > entry_delta:
        # Position moved ITM - take profit and re-establish OTM
        roll_reason = "delta_drift_itm"
    else:
        # Position moved further OTM - rebalance to target delta
        roll_reason = "delta_drift_otm"
    trigger_roll(hedge_id, roll_reason)
```

#### Extrinsic Value Roll Trigger

**Configuration**: `TAIL_EXTRINSIC_DECAY_THRESHOLD = 0.20` (20% of entry premium)

**Logic**:
- Entry extrinsic value: `entry_price` (all extrinsic for OTM options)
- Current extrinsic value: `current_price - intrinsic_value`
- Trigger: If `extrinsic_value < (entry_price * 0.20)`

**Rationale**: When extrinsic value decays below 20% of entry premium, most time value is gone. Rolling captures remaining value before full decay.

**Action**:
```python
# Calculate intrinsic value
intrinsic_value = max(strike_price - underlying_price, 0)  # For puts
extrinsic_value = current_price - intrinsic_value

if extrinsic_value < (entry_price * TAIL_EXTRINSIC_DECAY_THRESHOLD):
    roll_reason = "extrinsic_decay"
    trigger_roll(hedge_id, roll_reason)
```

#### Skew Regime Change Roll Trigger

**Configuration**: 
- `SKEW_BASELINE_WINDOW = 252` (1 year lookback)
- `SKEW_CHANGE_THRESHOLD = 2.0` (standard deviations)

**Metrics**:
- **Put skew**: 25-delta put IV - ATM IV
- **Historical skew**: Rolling 252-day average and std dev
- **Current z-score**: `(current_skew - mean_skew) / std_skew`

**Logic**:
```python
# Pseudo-code
skew_zscore = calculate_skew_zscore(underlying="QQQ", window=252)

if skew_zscore > SKEW_CHANGE_THRESHOLD:
    # Skew is abnormally steep - puts are expensive relative to history
    # Consider: 1) Widen to spreads, 2) Reduce size, 3) Skip roll
    roll_reason = "skew_regime_rich"
    adaptive_action = "consider_spread_or_reduce_size"
    
elif skew_zscore < -SKEW_CHANGE_THRESHOLD:
    # Skew is abnormally flat - puts are cheap relative to history
    # Consider: 1) Add size, 2) Tighten spreads to naked puts
    roll_reason = "skew_regime_cheap"
    adaptive_action = "consider_increased_size"
```

**Data Source** (if implemented):
- ATM IV: Options chain data for near-money strikes
- 25-delta IV: Interpolated from options chain
- Historical IV: 252-day rolling window stored in S3/DynamoDB

**Fallback** (current implementation):
- Use VIX as proxy for overall IV regime
- Skew not yet implemented - placeholder for future enhancement

### Template 2: Smoothing Hedge (Put Spreads)

**Primary Strategy**: Fixed 21-day cadence with dynamic adjustments

**Configuration**:
- Target DTE: 60 days
- Roll cadence: 21 days (fixed)
- Long delta: 0.30 (30-delta put)
- Short delta: 0.10 (10-delta put)
- Underlying: QQQ

#### Roll Triggers - Spread Template

| Trigger Type | Threshold | Action | Priority |
|--------------|-----------|--------|----------|
| **Time-Based Cadence** | 21 days since entry | Mandatory roll | **High** |
| **Remaining Width Value** | Spread value < 30% of max width | Roll to capture value | **Medium** |
| **Long Leg Delta Drift** | Long Δ > 0.50 | Roll to restore OTM profile | **Medium** |
| **Short Leg Assignment Risk** | Short Δ > 0.80 | Immediate roll or close | **Critical** |
| **Spread Convergence** | Width < 50% of entry width | Roll to wider strikes | **Low** |

#### Time-Based Cadence (21 Days)

**Configuration**: `SMOOTHING_HEDGE_TEMPLATE.roll_cadence_days = 21`

**Logic**:
```python
# Calculate days held
days_held = (today - entry_date).days

# Trigger roll if held >= 21 days
if days_held >= SMOOTHING_HEDGE_TEMPLATE.roll_cadence_days:
    roll_reason = "cadence_due"
    trigger_roll(hedge_id, roll_reason)
```

**Rationale**: Fixed cadence provides predictable roll schedule and captures theta decay before acceleration near expiry.

#### Remaining Width Value Roll Trigger

**Configuration**: `SPREAD_WIDTH_VALUE_THRESHOLD = 0.30` (30% of max width)

**Logic**:
```python
# Calculate spread metrics
max_width = long_strike - short_strike  # e.g., $470 - $450 = $20
current_spread_value = long_price - short_price  # e.g., $15 - $2 = $13
intrinsic_width = max(long_strike - underlying_price, 0) - max(short_strike - underlying_price, 0)

# Trigger if spread value decayed significantly
if current_spread_value < (max_width * SPREAD_WIDTH_VALUE_THRESHOLD):
    roll_reason = "width_value_decay"
    trigger_roll(hedge_id, roll_reason)
```

**Rationale**: When spread value decays to < 30% of max width, most protection value is lost. Roll to restore defined-risk protection.

**Example**:
```
Entry: Long $470 Put @ $12, Short $450 Put @ $4 → Spread value $8, Max width $20
After 3 weeks: Long $470 Put @ $7, Short $450 Put @ $1 → Spread value $6 (30% of $20 = $6)
Trigger: Roll to new strikes to restore protection
```

#### Delta Drift on Both Legs

**Configuration**:
- Long leg drift threshold: `SPREAD_LONG_DELTA_THRESHOLD = 0.50`
- Short leg drift threshold: `SPREAD_SHORT_DELTA_THRESHOLD = 0.20`

**Long Leg Delta Drift**:
```python
# Long leg target: 0.30 delta
# Alert if moves > 0.50 (deep ITM)
if abs(long_leg_current_delta) > SPREAD_LONG_DELTA_THRESHOLD:
    roll_reason = "long_leg_delta_drift"
    urgency = "medium"
    trigger_roll(hedge_id, roll_reason)
```

**Short Leg Delta Drift**:
```python
# Short leg target: 0.10 delta
# Critical alert if moves > 0.20 (assignment risk zone)
if abs(short_leg_current_delta) > SPREAD_SHORT_DELTA_THRESHOLD:
    if abs(short_leg_current_delta) > 0.80:
        # Critical assignment risk - see ASSIGNMENT_HANDLING_RUNBOOK.md
        roll_reason = "short_leg_assignment_risk"
        urgency = "critical"
    else:
        roll_reason = "short_leg_delta_drift"
        urgency = "medium"
    trigger_roll(hedge_id, roll_reason)
```

**Rationale**: Delta drift indicates changed market conditions. Long leg drift reduces convexity; short leg drift increases assignment risk.

## Roll Execution Procedures

### Step-by-Step Roll Process

#### Phase 1: Pre-Roll Evaluation

1. **Identify Eligible Positions**:
   - Query `HedgePositionsTable` for positions with `state=active`
   - Filter by roll trigger criteria (DTE, delta, cadence, etc.)
   - Prioritize by urgency (critical → high → medium → low)

2. **Check Market Conditions**:
   - Verify market is open (9:30 AM - 4:00 PM ET)
   - Check VIX level and IV regime
   - Confirm liquidity on target contracts (OI, volume, spread)

3. **Calculate Replacement Parameters**:
   - Target DTE: 90 days (tail) or 60 days (spread)
   - Target delta: 0.15 (tail) or 0.30/0.10 (spread)
   - Strike selection: Within liquidity bands
   - Quantity: Match existing position size (or adjust based on budget)

4. **Budget Verification**:
   ```python
   # Check remaining monthly budget
   ytd_spend = query_ytd_premium_spend()
   monthly_spend = query_monthly_premium_spend()
   
   if monthly_spend > MAX_PREMIUM_SPEND_MONTHLY_PCT * current_nav:
       # Skip roll if budget exceeded
       skip_reason = "monthly_budget_exceeded"
       return skip_roll(hedge_id, skip_reason)
   ```

#### Phase 2: Close Existing Position

1. **Market Order vs Limit Order**:
   - **Limit order** (preferred): Midpoint or midpoint + slippage tolerance
   - **Market order** (fallback): If limit not filled within 5 minutes

2. **Close Long Leg First** (for spreads):
   ```python
   # Sell to close long leg
   order = {
       "symbol": long_leg_symbol,
       "qty": contracts,
       "side": "sell",
       "type": "limit",
       "limit_price": long_leg_mid * 1.02,  # Slight premium above mid
       "time_in_force": "day",
       "order_class": "simple"
   }
   ```

3. **Close Short Leg Second** (for spreads):
   ```python
   # Buy to close short leg
   order = {
       "symbol": short_leg_symbol,
       "qty": contracts,
       "side": "buy",
       "type": "limit",
       "limit_price": short_leg_mid * 0.98,  # Slight discount below mid
       "time_in_force": "day",
       "order_class": "simple"
   }
   ```

4. **Record Close**:
   ```python
   # Update position state
   update_position(
       hedge_id=hedge_id,
       state=HedgePositionState.ROLLING,
       roll_state=RollState.ROLLING
   )
   
   # Record to audit trail
   record_action(
       action=HedgeAction.HEDGE_CLOSED,
       hedge_id=hedge_id,
       reason="roll_close_leg"
   )
   ```

#### Phase 3: Open Replacement Position

1. **Contract Selection**:
   - Query options chain for target DTE range (±7 days)
   - Filter by liquidity (min OI, max spread %)
   - Select strike nearest to target delta

2. **Open New Long Leg** (for spreads):
   ```python
   # Buy to open long leg
   order = {
       "symbol": new_long_symbol,
       "qty": contracts,
       "side": "buy",
       "type": "limit",
       "limit_price": new_long_mid * 0.98,  # Discount below mid
       "time_in_force": "day",
       "order_class": "simple"
   }
   ```

3. **Open New Short Leg** (for spreads):
   ```python
   # Sell to open short leg
   order = {
       "symbol": new_short_symbol,
       "qty": contracts,
       "side": "sell",
       "type": "limit",
       "limit_price": new_short_mid * 1.02,  # Premium above mid
       "time_in_force": "day",
       "order_class": "simple"
   }
   ```

4. **Record Open**:
   ```python
   # Create new position record
   create_position(
       hedge_id=f"hedge-{uuid.uuid4()}",
       option_symbol=new_long_symbol,
       short_leg_symbol=new_short_symbol,  # If spread
       contracts=contracts,
       entry_price=fill_price,
       entry_delta=calculated_delta,
       state=HedgePositionState.ACTIVE,
       roll_state=RollState.HOLDING,
       hedge_template=template
   )
   
   # Record to audit trail
   record_action(
       action=HedgeAction.HEDGE_ROLLED,
       hedge_id=old_hedge_id,
       new_hedge_id=new_hedge_id,
       roll_cost=net_debit_or_credit
   )
   ```

#### Phase 4: Post-Roll Verification

1. **Verify Fills**:
   - Confirm all legs filled
   - Check fill prices vs expected (slippage)
   - Verify position reflected in broker account

2. **Update Position State**:
   ```python
   # Old position: mark as closed
   update_position(
       hedge_id=old_hedge_id,
       state=HedgePositionState.CLOSED,
       roll_state=RollState.CLOSED
   )
   
   # New position: mark as active
   update_position(
       hedge_id=new_hedge_id,
       state=HedgePositionState.ACTIVE,
       roll_state=RollState.HOLDING
   )
   ```

3. **Calculate Roll Cost**:
   ```python
   # Net roll cost
   close_proceeds = long_leg_close_price - short_leg_close_price  # For spreads
   open_cost = new_long_price - new_short_price  # For spreads
   roll_cost = open_cost - close_proceeds
   
   # Update YTD spend
   update_ytd_premium_spend(roll_cost)
   ```

4. **Notification**:
   ```python
   # Log success
   logger.info(
       "Hedge roll completed successfully",
       old_hedge_id=old_hedge_id,
       new_hedge_id=new_hedge_id,
       roll_cost=str(roll_cost),
       roll_reason=roll_reason
   )
   
   # Send notification (if configured)
   publish_notification(
       subject="Hedge Roll Completed",
       message=f"Rolled {old_symbol} → {new_symbol}, Cost: ${roll_cost}"
   )
   ```

## Adaptive Roll Strategies

### Rich IV Regime Adaptations

When VIX > 35 (rich IV), apply these adjustments:

1. **Widen Delta**:
   - Target delta: 0.15 → 0.10 (move further OTM)
   - Rationale: Cheaper protection, accept lower probability of payoff

2. **Extend Tenor**:
   - Target DTE: 90 → 120 days
   - Rationale: Longer tenor has less theta decay per day

3. **Reduce Size**:
   - Contracts: Reduce by 25%
   - Rationale: Lower premium spend in expensive market

4. **Switch to Spreads**:
   - Template: tail → smoothing
   - Rationale: Spreads cap cost by selling OTM leg

**Configuration**:
```python
RICH_IV_THRESHOLD = Decimal("35")
RICH_IV_DELTA_REDUCTION = Decimal("0.05")  # Widen by 5 delta
RICH_IV_DTE_EXTENSION = 30  # Add 30 days
RICH_IV_PAYOFF_MULTIPLIER = Decimal("0.75")  # Reduce payoff target by 25%
```

### Cheap IV Regime Opportunities

When VIX < 15 (cheap IV), consider:

1. **Tighten Delta**:
   - Target delta: 0.15 → 0.20 (move closer to ATM)
   - Rationale: More protection per dollar spent

2. **Increase Size**:
   - Contracts: Increase by 25-50% (within budget)
   - Rationale: Lock in cheap protection before volatility rises

3. **Shorten Tenor**:
   - Target DTE: 90 → 60 days
   - Rationale: Roll more frequently to continuously buy cheap vol

## Failure Handling

### Partial Fill Scenarios

**Scenario 1: Close Leg Filled, Open Leg Not Filled**

```python
# Risk: Temporarily unhedged
# Action:
if close_filled and not open_filled:
    # Retry open order with wider limit (increase slippage tolerance)
    retry_open_order(limit_price=mid * 0.95)  # More aggressive
    
    # If still no fill after 3 attempts:
    if retry_count > 3:
        # Log warning and wait for next evaluation cycle
        logger.warning(
            "Roll incomplete - open leg not filled",
            hedge_id=hedge_id,
            manual_intervention_required=True
        )
        # Send alert to operations team
```

**Scenario 2: One Spread Leg Filled, Other Not Filled**

```python
# Risk: Undefined risk (naked long or short)
# Action: URGENT - complete the spread immediately
if long_filled and not short_filled:
    # Naked long put - no immediate risk, but not a spread
    # Aggressively fill short leg at market if necessary
    market_order_short_leg()
    
elif short_filled and not long_filled:
    # Naked short put - CRITICAL RISK
    # Must complete spread immediately
    market_order_long_leg()  # Use market order
    # Set kill switch if fill fails
    if not long_filled_after_market_order:
        set_kill_switch(reason="naked_short_position_unfilled")
```

### Roll Rejection Scenarios

**Budget Exceeded**:
```python
if roll_cost > remaining_monthly_budget:
    skip_roll(reason="budget_exceeded", wait_until_next_month=True)
```

**No Liquid Contracts Available**:
```python
if not find_suitable_contract(target_dte, target_delta, liquidity_filters):
    skip_roll(reason="no_liquid_contracts", retry_next_evaluation=True)
```

**Market Closed**:
```python
if not is_market_open():
    defer_roll(reason="market_closed", retry_at_market_open=True)
```

## Monitoring and Metrics

### Roll Performance Metrics

- **Roll frequency**: Count of rolls per position lifetime
- **Average roll cost**: Net debit/credit per roll transaction
- **Roll slippage**: Actual fill vs expected mid price
- **Time to complete roll**: Duration from close to open completion
- **Failed roll rate**: Percentage of roll attempts that fail or timeout

### CloudWatch Dashboards

**Roll Activity Dashboard**:
- Daily roll count by template (tail vs spread)
- Roll trigger breakdown (DTE vs delta vs cadence vs extrinsic)
- Cumulative roll costs YTD
- Average days between rolls

**Roll Health Dashboard**:
- Positions due for roll (DTE < 45)
- Positions overdue for roll (DTE < 14)
- Partial fills awaiting completion
- Failed rolls requiring manual intervention

## Emergency Roll Procedures

See [Emergency Unwind Runbook](EMERGENCY_UNWIND_RUNBOOK.md) for:
- Forced close of all positions (market crash scenario)
- Liquidity crisis handling (wide spreads, no fills)
- System failure recovery (Lambda timeout, DynamoDB unavailable)

## Testing and Validation

### Pre-Production Roll Tests

1. **Simulated DTE Roll**:
   - Set position DTE to 44 days
   - Verify roll triggered correctly
   - Confirm new position has 90 DTE

2. **Simulated Delta Drift**:
   - Mock position with current delta = 0.28 (entry 0.15)
   - Verify delta drift roll triggered
   - Confirm new position restores target delta

3. **Simulated Cadence Roll**:
   - Set position entry_date to 22 days ago
   - Verify smoothing template cadence roll triggered
   - Confirm 21-day interval logic

4. **Simulated Budget Limit**:
   - Set monthly spend to 99% of cap
   - Attempt roll
   - Verify roll skipped due to budget

### Production Monitoring

- **Daily**: Review roll execution logs for errors
- **Weekly**: Audit roll costs vs budget
- **Monthly**: Review roll trigger distribution (which triggers most common)
- **Quarterly**: Backtest roll strategy effectiveness

## Related Documentation

- [Assignment Handling Runbook](ASSIGNMENT_HANDLING_RUNBOOK.md)
- [Emergency Unwind Runbook](EMERGENCY_UNWIND_RUNBOOK.md)
- [Options Hedging Module Documentation](OPTIONS_HEDGING.md)
- [Options Hedging Strategy Review](OPTIONS_HEDGING_STRATEGY_REVIEW.md)

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-30 | 1.0.0 | Copilot | Initial creation with enhanced roll triggers |

## Appendix: Configuration Constants

### Tail Template Roll Configuration

```python
# In hedge_config.py
TAIL_HEDGE_TEMPLATE.roll_trigger_dte = 45  # DTE threshold
TAIL_DELTA_DRIFT_THRESHOLD = Decimal("0.10")  # 10 delta points
TAIL_EXTRINSIC_DECAY_THRESHOLD = Decimal("0.20")  # 20% of entry premium
SKEW_BASELINE_WINDOW = 252  # Trading days (1 year)
SKEW_CHANGE_THRESHOLD = Decimal("2.0")  # Standard deviations
```

### Smoothing Template Roll Configuration

```python
# In hedge_config.py
SMOOTHING_HEDGE_TEMPLATE.roll_cadence_days = 21  # Fixed cadence
SPREAD_WIDTH_VALUE_THRESHOLD = Decimal("0.30")  # 30% of max width
SPREAD_LONG_DELTA_THRESHOLD = Decimal("0.50")  # Long leg alert
SPREAD_SHORT_DELTA_THRESHOLD = Decimal("0.20")  # Short leg warning
# assignment_risk_delta_threshold = 0.80 already defined
```

### Execution Parameters

```python
# In hedge_config.py
ROLL_LIMIT_SLIPPAGE_TOLERANCE = Decimal("0.02")  # 2% slippage
ROLL_RETRY_ATTEMPTS = 3  # Max retry attempts
ROLL_TIMEOUT_MINUTES = 15  # Max time to complete roll
ROLL_MARKET_ORDER_FALLBACK = True  # Use market order if limit fails
```
