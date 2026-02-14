# Assignment Handling Runbook

## Overview

This document provides step-by-step operational procedures for handling option assignment events on short option positions within the Alchemiser options hedging system. Assignment risk occurs primarily on short legs of put spread structures when the short position moves deep in-the-money (ITM).

## Objective

Ensure that assignment events are detected promptly and remediated to:
1. Restore defined-risk structure by closing/exercising paired legs
2. Flatten any accidental underlying exposure created by assignment
3. Prevent capital lock-up and margin violations
4. Maintain audit trail of all remediation actions

## Assignment Risk Detection

### Automated Detection Criteria

The system monitors for assignment risk on short option legs using the following thresholds:

| Risk Level | Delta Threshold | Action Required |
|------------|----------------|-----------------|
| **Warning** | \|Δ\| > 0.60 | Alert logged, monitoring increased |
| **High Risk** | \|Δ\| > 0.80 | Critical alert, prepare for assignment |
| **Critical** | \|Δ\| > 0.90 | Immediate remediation recommended |

**Configuration**: `SMOOTHING_HEDGE_TEMPLATE.assignment_risk_delta_threshold = 0.80`

### Detection Frequency

- **Primary**: Daily roll schedule check (3:45 PM ET via `HedgeRollManagerFunction`)
- **Secondary**: Real-time delta monitoring during market hours (if implemented)
- **Manual**: On-demand position review via DynamoDB query

### Detection Location

**Handler**: `functions/hedge_roll_manager/handlers/roll_schedule_handler.py`
**Method**: `_check_assignment_risk()`
**Log Pattern**: `"Assignment risk detected on short leg"`

## Assignment Detection Procedure

### Step 1: Identify Assigned Positions

#### Automated Detection

The system logs assignment risk when short leg delta exceeds threshold:

```
[WARNING] Assignment risk detected on short leg
hedge_id: hedge-abc123
short_leg_symbol: QQQ241215P00450000
short_delta: -0.85
threshold: 0.80
```

#### Manual Detection (DynamoDB Query)

Query `HedgePositionsTable` for positions with assignment risk:

```bash
aws dynamodb scan \
  --table-name HedgePositionsTable \
  --filter-expression "is_spread = :true AND attribute_exists(short_leg_current_delta)" \
  --expression-attribute-values '{":true": {"BOOL": true}}' \
  --region us-east-1
```

Look for positions where `abs(short_leg_current_delta) > 0.80`.

#### Broker Notification Check

Check Alpaca account for assignment notifications:

```bash
# Via Alpaca API (if implemented)
# Check account activities for OPTION_ASSIGNMENT events
curl -X GET "https://paper-api.alpaca.markets/v2/account/activities/OPTION_ASSIGNMENT" \
  -H "APCA-API-KEY-ID: {API_KEY}" \
  -H "APCA-API-SECRET-KEY: {SECRET_KEY}"
```

### Step 2: Assess Assignment Impact

For each assigned position, determine:

1. **Assigned Quantity**: Number of contracts assigned (typically 100 shares per contract)
2. **Underlying Position**: Stock position created by assignment
3. **Paired Long Leg**: Corresponding long option that must be exercised/closed
4. **Net Exposure**: Calculate unintended market exposure
5. **Capital Requirements**: Margin impact and buying power reduction

**Example Calculation**:
```
Short 5x QQQ $450 Puts (assigned)
→ Long 500 shares QQQ @ $450 = $225,000 position
→ Must close/exercise 5x QQQ $470 Puts (long leg)
→ Net exposure: $225,000 until remediated
```

## Remediation Procedures

### Procedure A: Immediate Paired Leg Exercise (Preferred)

**When to Use**: If long leg is ITM and assignment has occurred

**Steps**:

1. **Verify Assignment**:
   ```bash
   # Check Alpaca positions for unexpected stock holdings
   curl -X GET "https://paper-api.alpaca.markets/v2/positions" \
     -H "APCA-API-KEY-ID: {API_KEY}" \
     -H "APCA-API-SECRET-KEY: {SECRET_KEY}"
   ```

2. **Exercise Long Leg**:
   - Submit exercise request to broker for long put option
   - This offsets the assigned stock position
   - **Alpaca API**: Use options exercise endpoint (if available)
   - **Manual**: Contact broker support if API not available

3. **Verify Offset**:
   - Confirm stock position is flat (zero shares)
   - Confirm both option legs are closed
   - Document in `HedgeHistoryTable`

4. **Record Action**:
   ```python
   # Record ASSIGNMENT_EXERCISED action
   HedgeAction.ASSIGNMENT_EXERCISED
   details = {
       "assigned_leg": "QQQ241215P00450000",
       "exercised_leg": "QQQ241215P00470000",
       "contracts": 5,
       "stock_position_flattened": True,
       "remediation_timestamp": datetime.now(UTC).isoformat()
   }
   ```

### Procedure B: Close Both Legs at Market (Fallback)

**When to Use**: If immediate exercise is not available or long leg is OTM

**Steps**:

1. **Sell Assigned Stock**:
   ```bash
   # Market order to sell assigned shares immediately
   # This flattens unintended stock exposure
   curl -X POST "https://paper-api.alpaca.markets/v2/orders" \
     -H "APCA-API-KEY-ID: {API_KEY}" \
     -H "APCA-API-SECRET-KEY: {SECRET_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "QQQ",
       "qty": 500,
       "side": "sell",
       "type": "market",
       "time_in_force": "day"
     }'
   ```

2. **Close Long Leg**:
   - Sell long put option at market
   - Accept current market price to exit quickly
   - Record execution price and slippage

3. **Verify Positions Flat**:
   ```bash
   # Verify no residual positions
   # NOTE: HedgePositionsTable uses PK/SK single-table design.
   # Derive keys from hedge_id: PK="HEDGE#<hedge_id>", SK="POSITION#LIVE"
   aws dynamodb update-item \
     --no-cli-pager \
     --table-name HedgePositionsTable \
     --key '{
       "PK": {"S": "HEDGE#hedge-abc123"},
       "SK": {"S": "POSITION#LIVE"}
     }' \
     --update-expression "SET #state = :closed, roll_state = :closed_state" \
     --expression-attribute-names '{"#state": "state"}' \
     --expression-attribute-values '{":closed": {"S": "closed"}, ":closed_state": {"S": "closed"}}' \
     --region us-east-1
   ```

4. **Calculate P&L**:
   - Net premium paid/received on spread
   - Assignment execution price vs strike
   - Stock sale proceeds
   - Long leg exit proceeds
   - Document total realized P&L

### Procedure C: Roll to New Position (Proactive)

**When to Use**: Assignment risk detected (delta > 0.80) but not yet assigned

**Steps**:

1. **Close Existing Spread**:
   - Sell to close long leg (buy put)
   - Buy to close short leg (sold put)
   - Use limit orders with reasonable slippage tolerance

2. **Open Replacement Position**:
   - Follow standard hedge evaluation logic
   - Select new strikes with wider spread (reduce assignment risk)
   - Consider reducing position size if budget constrained

3. **Update Position State**:
   ```python
   # Update hedge_position in DynamoDB
   state = HedgePositionState.ROLLING
   roll_state = RollState.ROLLING
   roll_reason = "assignment_risk_preemptive"
   ```

## Halt Trading Mechanism

### Trigger Conditions

Halt all hedging operations if:

1. **Unresolved Assignment**: Assignment detected but not remediated within 1 trading day
2. **Multiple Assignments**: More than 1 position assigned simultaneously
3. **Capital Shortage**: Insufficient buying power to remediate
4. **API Failures**: Unable to execute remediation orders due to broker API errors

### Halt Implementation

**Location**: `shared_layer/python/the_alchemiser/shared/options/kill_switch_service.py`

**Steps**:

1. **Set Kill Switch**:
   ```python
   # Using KillSwitchService
   from the_alchemiser.shared.options.kill_switch_service import KillSwitchService
   
   service = KillSwitchService()
   service.activate(
       reason="unresolved_assignment_detected",
       triggered_by="manual"
   )
   ```

2. **Notification**:
   - Send critical alert via SNS
   - Email notification to operations team
   - CloudWatch alarm triggered

3. **Bypass Logic**:
   - `HedgeEvaluatorFunction` checks kill switch before evaluation
   - `HedgeExecutorFunction` refuses new orders if kill switch active
   - Manual override required to resume operations

4. **Clear Kill Switch** (after remediation):
   ```python
   service.deactivate()
   ```

## Forced Actions Configuration

### Assignment Action Types

New action types added to `HedgeAction` enum:

- `ASSIGNMENT_DETECTED`: Logged when delta > 0.80 on short leg
- `ASSIGNMENT_EXERCISED`: Long leg exercised to offset assigned stock
- `ASSIGNMENT_CLOSED`: Both legs closed at market to remediate
- `ASSIGNMENT_UNRESOLVED`: Flagged when remediation fails or delayed

### Forced Remediation Logic

**Configuration**: `hedge_config.py`

```python
# Assignment handling configuration (PLANNED - not yet implemented)
# These constants are placeholders for future automated remediation.
# When implemented, define them in hedge_config.py and wire into runtime.
# ASSIGNMENT_AUTO_REMEDIATE: bool = True  # Enable automatic remediation
# ASSIGNMENT_REMEDIATION_TIMEOUT_HOURS: int = 4  # Max time to remediate
# ASSIGNMENT_HALT_ON_UNRESOLVED: bool = True  # Halt trading if not resolved
```

**Handler**: `functions/hedge_roll_manager/handlers/assignment_handler.py` (to be created)

## Monitoring and Alerts

### CloudWatch Metrics

- `assignment_risk_detected_count`: Daily count of positions with delta > 0.80
- `assignment_remediation_success`: Count of successfully remediated assignments
- `assignment_remediation_failure`: Count of failed remediation attempts
- `days_since_last_assignment`: Days since last assignment event

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| `HighAssignmentRisk` | delta > 0.80 on any short leg | Warning email |
| `CriticalAssignmentRisk` | delta > 0.90 on any short leg | Urgent pager notification |
| `UnresolvedAssignment` | Assignment unresolved > 4 hours | Halt trading + escalate |
| `MultipleAssignments` | 2+ assignments in same day | Halt trading + escalate |

### Log Patterns to Monitor

```
[WARNING] Assignment risk detected on short leg
[CRITICAL] Assignment detected - remediation required
[SUCCESS] Assignment remediated - position closed
[ERROR] Assignment remediation failed - manual intervention required
[ALERT] Kill switch activated - assignment unresolved
```

## Escalation Procedures

### Level 1: Automated Remediation (0-4 hours)

- System attempts automatic remediation via Procedures A or B
- Logs all actions to `HedgeHistoryTable`
- Sends status updates via CloudWatch

### Level 2: Operations Review (4-24 hours)

- If automatic remediation fails, notify operations team
- Manual review of position and market conditions
- Execute Procedure B or C with manual oversight
- Document lessons learned

### Level 3: Emergency Escalation (24+ hours)

- If assignment unresolved after 1 trading day:
  - Halt all hedging operations (kill switch)
  - Contact broker support for assistance
  - Executive team notification
  - Post-mortem required

## Audit Trail Requirements

### Required Documentation

For each assignment event, record:

1. **Detection**:
   - Timestamp of detection
   - Hedge ID and option symbols
   - Delta at detection
   - Detection method (automated vs manual)

2. **Remediation**:
   - Remediation procedure used (A, B, or C)
   - Execution timestamps
   - Order details (prices, quantities)
   - P&L impact

3. **Verification**:
   - Final position status (flat/closed)
   - Residual exposure (if any)
   - Lessons learned
   - Process improvements identified

### Storage

- **Primary**: DynamoDB `HedgeHistoryTable` with action type `ASSIGNMENT_*`
- **Secondary**: CloudWatch Logs with structured JSON
- **Backup**: S3 bucket for audit archives

## Testing and Validation

### Pre-Production Testing

1. **Simulated Assignment**:
   - Create mock position with delta > 0.80
   - Verify detection logic triggers correctly
   - Test remediation procedures in paper trading

2. **Kill Switch Test**:
   - Manually trigger kill switch
   - Verify all hedging operations halt
   - Test manual override and clear procedures

3. **Notification Test**:
   - Trigger assignment risk alert
   - Verify SNS/email notifications delivered
   - Verify CloudWatch alarms fire correctly

### Production Monitoring

- **Daily**: Review assignment risk detection logs
- **Weekly**: Audit trail review of all assignment events
- **Monthly**: Test kill switch activation/deactivation
- **Quarterly**: Full disaster recovery drill

## Related Documentation

- [Roll Procedures Runbook](ROLL_PROCEDURES_RUNBOOK.md)
- [Emergency Unwind Runbook](EMERGENCY_UNWIND_RUNBOOK.md)
- [Options Hedging Module Documentation](OPTIONS_HEDGING.md)
- [Fail-Closed Safety Rails](FAIL_CLOSED_SAFETY_RAILS.md)

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-30 | 1.0.0 | Copilot | Initial creation |

## Appendix A: Example Assignment Scenarios

### Scenario 1: QQQ Put Spread - Normal Assignment

**Position**: 
- Long 5x QQQ $470 Put @ $8.00
- Short 5x QQQ $450 Put @ $3.00
- Net debit: $5.00 per spread = $2,500 total

**Assignment Event**:
- QQQ drops to $445 (5 delta points below short strike)
- Short $450 put delta moves to -0.88
- Assignment occurs overnight (after-hours)

**Remediation**:
- Exercise long $470 puts (offsetting short stock from assignment)
- Net P&L: Max profit of $20 per spread = $10,000 gain
- Position closed successfully

### Scenario 2: Early Assignment Risk - Proactive Roll

**Position**:
- Long 10x SPY $580 Put @ $12.00
- Short 10x SPY $560 Put @ $5.00
- Net debit: $7.00 per spread = $7,000 total

**Risk Detection**:
- SPY drops to $565 (5 delta points below long strike)
- Short $560 put delta moves to -0.82
- System detects assignment risk (above 0.80 threshold)

**Proactive Action**:
- Close existing spread at $14.00 credit (net $7,000 profit)
- Open new spread with wider strikes ($590/$570)
- Assignment avoided, profits captured early

### Scenario 3: Multiple Assignment Failure - Kill Switch

**Position**:
- 3 separate spread positions all showing delta > 0.85
- Attempted remediation via Procedure A fails (API error)
- Attempted remediation via Procedure B partially succeeds

**Escalation**:
- Kill switch activated after 4 hours
- All hedging operations halted
- Manual broker contact initiated
- Positions manually closed by end of trading day
- Post-mortem identifies API reliability issue

## Appendix B: Command Reference

### Query Assignment Risk Positions

```bash
# DynamoDB scan for at-risk positions
aws dynamodb scan \
  --table-name HedgePositionsTable \
  --filter-expression "is_spread = :true AND short_leg_current_delta > :threshold" \
  --expression-attribute-values '{
    ":true": {"BOOL": true},
    ":threshold": {"N": "0.80"}
  }' \
  --projection-expression "hedge_id,short_leg_symbol,short_leg_current_delta,short_leg_strike" \
  --region us-east-1
```

### Manually Trigger Roll Check

```bash
# Invoke HedgeRollManagerFunction
aws lambda invoke \
  --function-name HedgeRollManagerFunction \
  --payload '{"detail-type": "ManualRollCheck"}' \
  --region us-east-1 \
  response.json
```

### Check Kill Switch Status

```bash
# Query kill switch state (HedgeKillSwitchTable uses switch_id as PK)
aws dynamodb get-item \
  --no-cli-pager \
  --table-name HedgeKillSwitchTable \
  --key '{"switch_id": {"S": "HEDGE_KILL_SWITCH"}}' \
  --region us-east-1
```

### Manual Position Close

```bash
# Update position state to closed
# NOTE: HedgePositionsTable uses PK/SK single-table design.
# Derive keys from hedge_id: PK="HEDGE#<hedge_id>", SK="POSITION#LIVE"
aws dynamodb update-item \
  --no-cli-pager \
  --table-name HedgePositionsTable \
  --key '{
    "PK": {"S": "HEDGE#hedge-abc123"},
    "SK": {"S": "POSITION#LIVE"}
  }' \
  --update-expression "SET #state = :closed, roll_state = :closed_state, last_updated = :now" \
  --expression-attribute-names '{"#state": "state"}' \
  --expression-attribute-values '{
    ":closed": {"S": "closed"},
    ":closed_state": {"S": "closed"},
    ":now": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
  }' \
  --region us-east-1
```
