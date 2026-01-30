# Emergency Unwind Runbook

## Overview

This document provides critical procedures for emergency unwinding of options hedge positions in the Alchemiser hedging system. Emergency unwind procedures are invoked during system failures, market disruptions, or risk management escalations requiring immediate position liquidation.

## Objective

Execute safe and controlled position liquidation during emergency scenarios to:
1. Minimize capital loss during forced liquidation
2. Maintain audit trail for regulatory compliance
3. Restore system to safe operating state
4. Enable post-mortem analysis and process improvement

## Emergency Scenario Classifications

### Level 1: Operational Emergency (Moderate Urgency)

**Triggers**:
- Lambda function timeout or repeated failures
- DynamoDB table unavailable or throttling
- Alpaca API outage or degraded performance
- Data feed disruption (VIX proxy, market data)

**Response Time**: Within 1-4 hours
**Authority**: Automated system + Operations team

### Level 2: Market Emergency (High Urgency)

**Triggers**:
- VIX spike > 50 (extreme volatility)
- Circuit breaker triggered (market halt)
- Flash crash or rapid drawdown (-10% in single day)
- Liquidity crisis (bid-ask spreads > 20%)

**Response Time**: Within 30-60 minutes
**Authority**: Operations team + Risk manager

### Level 3: Risk Emergency (Critical Urgency)

**Triggers**:
- Margin call or account restriction
- Multiple assignment events simultaneously
- Unhedged naked options position detected
- Broker account suspension or technical issue

**Response Time**: Immediate (< 15 minutes)
**Authority**: Risk manager + Executive team

## Emergency Unwind Procedures

### Procedure 1: Controlled Full Unwind

**When to Use**: Level 1-2 emergencies with time to execute systematically

#### Step 1: Activate Emergency Mode

```bash
# Set kill switch to halt new hedging operations
aws dynamodb update-item \
  --table-name HedgeConfigTable \
  --key '{"config_key": {"S": "kill_switch_status"}}' \
  --update-expression "SET #status = :active, reason = :reason, timestamp = :now" \
  --expression-attribute-names '{"#status": "status"}' \
  --expression-attribute-values '{
    ":active": {"S": "active"},
    ":reason": {"S": "emergency_unwind_initiated"},
    ":now": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
  }' \
  --region us-east-1
```

```python
# In code
from the_alchemiser.shared.options.kill_switch_service import set_kill_switch

set_kill_switch(
    reason="emergency_unwind_initiated",
    details={"scenario": "lambda_repeated_failures", "initiated_by": "ops_team"}
)
```

#### Step 2: Query All Active Positions

```bash
# Get complete position inventory
aws dynamodb scan \
  --table-name HedgePositionsTable \
  --filter-expression "#state = :active" \
  --expression-attribute-names '{"#state": "state"}' \
  --expression-attribute-values '{":active": {"S": "active"}}' \
  --region us-east-1 \
  > active_positions_$(date +%Y%m%d_%H%M%S).json
```

```python
# In code
from the_alchemiser.shared.options.adapters import HedgePositionsRepository

positions_repo = HedgePositionsRepository(table_name=HEDGE_POSITIONS_TABLE_NAME)
active_positions = positions_repo.query_active_positions()

logger.info(
    "Emergency unwind - active positions queried",
    position_count=len(active_positions),
    emergency_correlation_id=correlation_id
)
```

#### Step 3: Prioritize Liquidation Order

**Priority 1 (Immediate)**: Naked short positions or high assignment risk
```python
critical_positions = [
    pos for pos in active_positions
    if pos.get("is_spread") and abs(Decimal(pos.get("short_leg_current_delta", "0"))) > 0.80
]
```

**Priority 2 (High)**: Large positions or concentrated risk
```python
large_positions = [
    pos for pos in active_positions
    if pos.get("contracts", 0) > 10 or Decimal(pos.get("total_premium_paid", "0")) > 5000
]
```

**Priority 3 (Medium)**: Standard positions
```python
standard_positions = [
    pos for pos in active_positions
    if pos not in critical_positions and pos not in large_positions
]
```

#### Step 4: Execute Liquidation by Priority

**For Each Position in Priority Order**:

1. **Spread Positions** - Close both legs simultaneously if possible:
   ```python
   # Attempt multi-leg close (if broker supports)
   try:
       close_spread_order = {
           "symbol": long_leg_symbol,
           "qty": contracts,
           "side": "sell",
           "type": "market",  # Use market orders in emergency
           "time_in_force": "day"
       }
       # Submit both legs
       long_order_id = alpaca.submit_order(**close_spread_order)
       
       close_short_order = {
           "symbol": short_leg_symbol,
           "qty": contracts,
           "side": "buy",
           "type": "market",
           "time_in_force": "day"
       }
       short_order_id = alpaca.submit_order(**close_short_order)
       
   except Exception as e:
       logger.error("Spread close failed - attempting leg by leg", error=str(e))
       # Fall back to sequential close
   ```

2. **Single Leg Positions** - Market order close:
   ```python
   close_order = {
       "symbol": option_symbol,
       "qty": contracts,
       "side": "sell",  # Selling long puts
       "type": "market",
       "time_in_force": "day"
   }
   order_id = alpaca.submit_order(**close_order)
   ```

3. **Monitor Fill Status**:
   ```python
   import time
   
   max_wait = 60  # seconds
   start = time.time()
   
   while time.time() - start < max_wait:
       order_status = alpaca.get_order(order_id)
       if order_status.status == "filled":
           logger.info("Position closed", hedge_id=hedge_id, fill_price=order_status.filled_avg_price)
           break
       elif order_status.status in ["canceled", "rejected"]:
           logger.error("Close order failed", hedge_id=hedge_id, status=order_status.status)
           # Retry with different parameters or escalate
           break
       time.sleep(2)
   ```

4. **Update Position State**:
   ```python
   positions_repo.update_position(
       hedge_id=hedge_id,
       updates={
           "state": "closed",
           "roll_state": "closed",
           "last_updated": datetime.now(UTC).isoformat()
       }
   )
   ```

5. **Record to Audit Trail**:
   ```python
   from the_alchemiser.shared.options.adapters import HedgeHistoryRepository
   from the_alchemiser.shared.options.schemas.hedge_history_record import HedgeAction
   
   history_repo = HedgeHistoryRepository(table_name=HEDGE_HISTORY_TABLE_NAME)
   history_repo.record_action(
       account_id=HEDGE_ACCOUNT_ID,
       action=HedgeAction.HEDGE_CLOSED,
       hedge_id=hedge_id,
       option_symbol=option_symbol,
       underlying_symbol=underlying_symbol,
       contracts=contracts,
       premium=Decimal(str(close_proceeds)),
       correlation_id=emergency_correlation_id,
       details={
           "close_reason": "emergency_unwind",
           "emergency_level": "level_1",
           "fill_price": str(fill_price),
           "slippage": str(fill_price - expected_mid)
       }
   )
   ```

#### Step 5: Verify All Positions Closed

```bash
# Query for remaining active positions
aws dynamodb scan \
  --table-name HedgePositionsTable \
  --filter-expression "#state = :active" \
  --expression-attribute-names '{"#state": "state"}' \
  --expression-attribute-values '{":active": {"S": "active"}}' \
  --region us-east-1
```

```python
# Verify closure
remaining_active = positions_repo.query_active_positions()
if remaining_active:
    logger.error(
        "Emergency unwind incomplete - positions remain active",
        remaining_count=len(remaining_active),
        hedge_ids=[pos["hedge_id"] for pos in remaining_active]
    )
    # Escalate to manual intervention
else:
    logger.info("Emergency unwind complete - all positions closed")
```

#### Step 6: Financial Reconciliation

```python
# Calculate total liquidation P&L
total_proceeds = sum(Decimal(pos.get("close_proceeds", "0")) for pos in closed_positions)
total_cost_basis = sum(Decimal(pos.get("total_premium_paid", "0")) for pos in closed_positions)
net_pnl = total_proceeds - total_cost_basis

logger.info(
    "Emergency unwind P&L summary",
    positions_closed=len(closed_positions),
    total_proceeds=str(total_proceeds),
    total_cost_basis=str(total_cost_basis),
    net_pnl=str(net_pnl),
    emergency_correlation_id=emergency_correlation_id
)

# Update YTD tracking
update_ytd_premium_spend(additional_spend=Decimal("0"))  # No new spend, just close
```

### Procedure 2: Rapid Market Order Unwind

**When to Use**: Level 2-3 emergencies requiring immediate action

#### Simplified Steps

1. **Get All Active Positions** (as above)

2. **Submit Market Orders for All Positions Immediately**:
   ```python
   # No prioritization - close everything now
   for position in active_positions:
       try:
           # Long leg
           alpaca.submit_order(
               symbol=position["option_symbol"],
               qty=position["contracts"],
               side="sell",
               type="market",
               time_in_force="day"
           )
           
           # Short leg (if spread)
           if position.get("is_spread"):
               alpaca.submit_order(
                   symbol=position["short_leg_symbol"],
                   qty=position["contracts"],
                   side="buy",
                   type="market",
                   time_in_force="day"
               )
       except Exception as e:
           logger.error(f"Failed to close {position['hedge_id']}: {e}")
           # Continue with other positions
   ```

3. **Monitor Fills** (timeout after 5 minutes)

4. **Manual Follow-up** for unfilled orders

### Procedure 3: Broker-Assisted Emergency Close

**When to Use**: Level 3 emergencies or when automated systems fail

#### Steps

1. **Contact Broker Support**:
   - Alpaca support phone/email
   - Provide account ID and urgency level
   - Request immediate liquidation of all option positions

2. **Provide Position Details**:
   ```bash
   # Generate position summary for broker
   echo "EMERGENCY POSITION LIQUIDATION REQUEST" > emergency_request.txt
   echo "Account: HEDGE_ACCOUNT_ID" >> emergency_request.txt
   echo "Timestamp: $(date -u)" >> emergency_request.txt
   echo "" >> emergency_request.txt
   echo "Positions to close:" >> emergency_request.txt
   
   aws dynamodb scan \
     --table-name HedgePositionsTable \
     --filter-expression "#state = :active" \
     --expression-attribute-names '{"#state": "state"}' \
     --expression-attribute-values '{":active": {"S": "active"}}' \
     --query 'Items[*].[hedge_id.S, option_symbol.S, contracts.N]' \
     --output text >> emergency_request.txt
   ```

3. **Document Broker Actions**:
   - Record broker confirmation number
   - Note executed prices and timestamps
   - Update DynamoDB manually if system unavailable

4. **Post-Emergency Reconciliation**:
   - Compare broker statements to system records
   - Update HedgeHistoryTable with manual entries
   - Document discrepancies for post-mortem

## Emergency Unwind Triggers

### Automated Trigger Conditions

**Lambda Function Failures**:
```python
# In Lambda error handler
lambda_error_threshold = 3  # consecutive failures
if consecutive_failures >= lambda_error_threshold:
    logger.critical("Lambda failure threshold exceeded - consider emergency unwind")
    send_alert(
        severity="critical",
        message="Lambda failures may require emergency unwind",
        action_required="Evaluate system health and position risk"
    )
```

**Assignment Crisis**:
```python
# In roll_schedule_handler.py
if assignment_risks >= 3:  # Multiple assignments simultaneously
    logger.critical("Multiple assignment risks detected - emergency unwind may be required")
    set_kill_switch(reason="multiple_assignment_crisis")
    # Trigger emergency unwind procedure
```

**VIX Extreme Spike**:
```python
# In hedge_evaluator
if vix > 60:  # Historical panic levels (2008, 2020)
    logger.critical("VIX extreme spike detected", vix=str(vix))
    # Consider emergency unwind if liquidity deteriorates
    # Check bid-ask spreads on existing positions
```

### Manual Trigger Process

**Command Line**:
```bash
# Manually trigger emergency unwind Lambda
aws lambda invoke \
  --function-name EmergencyUnwindFunction \
  --payload '{
    "emergency_level": "level_2",
    "reason": "market_disruption",
    "initiated_by": "risk_manager",
    "authorization_code": "EMERGENCY_AUTH_CODE"
  }' \
  --region us-east-1 \
  response.json
```

**Operations Console** (if implemented):
- Navigate to Emergency Controls panel
- Select "Initiate Emergency Unwind"
- Confirm emergency level and reason
- Provide authorization credentials
- Monitor real-time unwind progress

## Post-Emergency Procedures

### Step 1: System Health Verification

```bash
# Check all Lambda functions operational
aws lambda list-functions --region us-east-1 | jq '.Functions[].FunctionName'

# Check DynamoDB tables accessible
aws dynamodb list-tables --region us-east-1

# Check EventBridge rules active
aws events list-rules --region us-east-1

# Verify Alpaca API connectivity
curl -X GET "https://paper-api.alpaca.markets/v2/account" \
  -H "APCA-API-KEY-ID: {API_KEY}" \
  -H "APCA-API-SECRET-KEY: {SECRET_KEY}"
```

### Step 2: Data Reconciliation

1. **Compare System Records to Broker**:
   ```python
   # Get broker positions
   alpaca_positions = alpaca.list_positions()
   
   # Get system positions
   system_positions = positions_repo.query_active_positions()
   
   # Identify discrepancies
   discrepancies = []
   for sys_pos in system_positions:
       if not any(alp_pos.symbol == sys_pos["option_symbol"] for alp_pos in alpaca_positions):
           discrepancies.append(sys_pos)
   ```

2. **Update System State**:
   ```python
   # Mark positions as closed if confirmed closed at broker
   for hedge_id in confirmed_closed:
       positions_repo.update_position(
           hedge_id=hedge_id,
           updates={"state": "closed", "roll_state": "closed"}
       )
   ```

3. **Generate Reconciliation Report**:
   ```python
   report = {
       "emergency_timestamp": emergency_timestamp,
       "positions_closed": len(closed_positions),
       "total_proceeds": str(total_proceeds),
       "net_pnl": str(net_pnl),
       "discrepancies": discrepancies,
       "manual_actions_required": manual_actions
   }
   
   # Save to S3
   s3_client.put_object(
       Bucket=reports_bucket,
       Key=f"emergency_unwind/{emergency_timestamp}/reconciliation.json",
       Body=json.dumps(report, indent=2)
   )
   ```

### Step 3: Root Cause Analysis

**Immediate Questions**:
1. What triggered the emergency?
2. Was automated unwind successful?
3. Were all positions closed?
4. What was the financial impact?
5. What manual interventions were required?

**Post-Mortem Template**:
```markdown
# Emergency Unwind Post-Mortem

## Incident Summary
- **Date/Time**: YYYY-MM-DD HH:MM:SS UTC
- **Emergency Level**: Level 1/2/3
- **Trigger**: [Description]
- **Duration**: [Time from trigger to resolution]

## Timeline
- HH:MM - Initial trigger detected
- HH:MM - Kill switch activated
- HH:MM - Unwind procedure initiated
- HH:MM - First position closed
- HH:MM - Last position closed
- HH:MM - System restored

## Impact Assessment
- **Positions Closed**: X positions
- **Total P&L**: $X (gain/loss)
- **Slippage Cost**: $X (compared to mid prices)
- **Positions Requiring Manual Intervention**: Y

## Root Cause
[Detailed analysis of what caused the emergency]

## What Went Well
- [Successes during emergency response]

## What Went Wrong
- [Failures or issues during emergency response]

## Action Items
- [ ] [Specific improvement #1]
- [ ] [Specific improvement #2]
- [ ] [Code/process changes needed]

## Preventive Measures
- [How to prevent similar emergencies in future]
```

### Step 4: System Restoration

**Clear Kill Switch**:
```bash
aws dynamodb update-item \
  --table-name HedgeConfigTable \
  --key '{"config_key": {"S": "kill_switch_status"}}' \
  --update-expression "SET #status = :inactive, cleared_timestamp = :now" \
  --expression-attribute-names '{"#status": "status"}' \
  --expression-attribute-values '{
    ":inactive": {"S": "inactive"},
    ":now": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
  }' \
  --region us-east-1
```

```python
from the_alchemiser.shared.options.kill_switch_service import clear_kill_switch

clear_kill_switch(
    cleared_by="ops_manager",
    post_mortem_completed=True
)
```

**Resume Normal Operations**:
1. Verify all systems operational
2. Run test hedge evaluation (paper trading mode)
3. Verify test completes successfully
4. Monitor first live evaluation closely
5. Gradual ramp-up of position sizes

## Monitoring and Alerts

### Emergency Detection Alerts

**CloudWatch Alarms**:
- `EmergencyTriggerDetected`: Any emergency trigger condition met
- `MultiplePositionFailures`: 3+ positions failed to close
- `EmergencyUnwindTimeout`: Unwind exceeds expected duration
- `PostEmergencyDiscrepancy`: System vs broker position mismatch

**SNS Notifications**:
```python
# Critical severity - page on-call engineer
publish_notification(
    topic_arn=CRITICAL_ALERTS_TOPIC,
    subject="EMERGENCY: Hedge Unwind Initiated",
    message=f"""
    Emergency unwind triggered: {emergency_reason}
    Level: {emergency_level}
    Active positions: {len(active_positions)}
    Expected completion: {estimated_completion_time}
    
    Monitor real-time progress in CloudWatch Logs.
    """,
    priority="critical"
)
```

### Real-Time Monitoring During Unwind

```python
# Emit progress metrics
cloudwatch.put_metric_data(
    Namespace="AlchemiserHedging/Emergency",
    MetricData=[
        {
            "MetricName": "PositionsClosing",
            "Value": len(active_positions),
            "Unit": "Count",
            "Timestamp": datetime.now(UTC)
        },
        {
            "MetricName": "PositionsClosed",
            "Value": len(closed_positions),
            "Unit": "Count",
            "Timestamp": datetime.now(UTC)
        },
        {
            "MetricName": "EmergencyUnwindProgress",
            "Value": len(closed_positions) / len(active_positions) * 100,
            "Unit": "Percent",
            "Timestamp": datetime.now(UTC)
        }
    ]
)
```

## Testing Emergency Procedures

### Quarterly Drill Requirements

1. **Simulated Emergency Drill** (paper trading):
   - Trigger emergency unwind in test environment
   - Verify all steps execute correctly
   - Measure time to complete
   - Document lessons learned

2. **Kill Switch Test**:
   - Activate kill switch manually
   - Verify hedging operations halt
   - Clear kill switch and verify resume
   - Test notification delivery

3. **Data Reconciliation Drill**:
   - Manually create position discrepancy
   - Run reconciliation procedures
   - Verify discrepancy detection and correction

4. **Broker Communication Drill**:
   - Contact broker support (non-emergency)
   - Verify contact procedures current
   - Test information handoff procedures

## Related Documentation

- [Assignment Handling Runbook](ASSIGNMENT_HANDLING_RUNBOOK.md)
- [Roll Procedures Runbook](ROLL_PROCEDURES_RUNBOOK.md)
- [Options Hedging Module Documentation](OPTIONS_HEDGING.md)
- [Fail-Closed Safety Rails](FAIL_CLOSED_SAFETY_RAILS.md)

## Contacts and Escalation

### Primary Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Operations Manager | ops@alchemiser.com | 24/7 on-call |
| Risk Manager | risk@alchemiser.com | Business hours + emergency escalation |
| Executive Team | exec@alchemiser.com | Critical escalations only |

### Broker Contacts

| Broker | Support | Emergency Line | Account Manager |
|--------|---------|----------------|-----------------|
| Alpaca Markets | support@alpaca.markets | [Emergency Phone] | [Account Manager] |

### External Resources

- AWS Support: Premium support for Lambda/DynamoDB issues
- Cloud monitoring: 24/7 infrastructure monitoring
- Legal/Compliance: For regulatory reporting of significant events

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-30 | 1.0.0 | Copilot | Initial creation |

## Appendix: Emergency Authorization

### Authorization Levels

| Emergency Level | Required Authorization | Override Available |
|-----------------|------------------------|-------------------|
| Level 1 | Operations team | No |
| Level 2 | Operations + Risk manager | Yes (Executive) |
| Level 3 | Risk manager + Executive team | No |

### Authorization Codes

Emergency authorization codes are stored securely in AWS Secrets Manager:

```bash
# Retrieve emergency authorization code
aws secretsmanager get-secret-value \
  --secret-id AlchemiserEmergencyAuthCodes \
  --region us-east-1 \
  --query SecretString \
  --output text
```

Authorization codes must be rotated monthly and after each use.
