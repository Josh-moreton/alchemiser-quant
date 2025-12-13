# Order Attribution Implementation Checklist

**Based on**: [ORDER_ATTRIBUTION_ANALYSIS.md](ORDER_ATTRIBUTION_ANALYSIS.md)  
**Quick Reference**: [ORDER_ATTRIBUTION_SUMMARY.md](ORDER_ATTRIBUTION_SUMMARY.md)

This checklist breaks down the recommendations into actionable implementation tasks.

---

## ✅ Phase 0: Accept Current State (Complete)

- [x] Understand system is rebalance-plan-driven, not intent-aggregated
- [x] Document that only single-strategy execution is supported
- [x] Identify that client_order_id + broker data is insufficient for full attribution
- [x] Catalog reconstruction gaps and time-windows

---

## 🔴 Phase 1: Critical Auditability (P0)

### Task 1.1: Persist RebalancePlan to DynamoDB

**Objective**: Enable reconstruction of decisions beyond 24h EventBridge retention.

#### Implementation Steps:

- [ ] Create DynamoDB table or extend existing TradeLedgerTable
  - Option A: Create new `RebalancePlanTable` with dedicated schema
  - Option B: Add to existing `TradeLedgerTable` with PK pattern `PLAN#{plan_id}`
  - Recommended: Option A for cleaner separation
  - TTL: 90-day retention (automatically delete old plans)

- [ ] Add DynamoDB persistence to `portfolio_v2/core/planner.py`
  ```python
  # After line 195: logger.info("Rebalance plan built successfully", ...)
  
  # NEW CODE:
  if settings.persist_rebalance_plans:
      from datetime import timedelta
      
      ttl_timestamp = int((datetime.now(UTC) + timedelta(days=90)).timestamp())
      
      dynamodb.put_item(
          TableName=settings.rebalance_plans_table,
          Item={
              'PK': {'S': f'PLAN#{plan.plan_id}'},
              'SK': {'S': f'CORRELATION#{plan.correlation_id}'},
              'plan_data': {'S': json.dumps(plan.to_dict())},
              'created_at': {'S': plan.timestamp.isoformat()},
              'correlation_id': {'S': plan.correlation_id},
              'causation_id': {'S': plan.causation_id},
              'item_count': {'N': str(len(plan.items))},
              'total_trade_value': {'S': str(plan.total_trade_value)},
              'ttl': {'N': str(ttl_timestamp)}  # Auto-delete after 90 days
          }
      )
  ```

- [ ] Add DynamoDB table definition in `template.yaml`
  ```yaml
  RebalancePlanTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !If 
        - UseStackNameForResources
        - !Sub "${StackName}-rebalance-plans"
        - !Sub "alchemiser-${Stage}-rebalance-plans"
      BillingMode: PAY_PER_REQUEST
      
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: correlation_id
          AttributeType: S
        - AttributeName: created_at
          AttributeType: S
      
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      
      GlobalSecondaryIndexes:
        - IndexName: CorrelationIdIndex
          KeySchema:
            - AttributeName: correlation_id
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true
      
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      
      Tags:
        - Key: Purpose
          Value: RebalancePlanArchive
        - Key: Retention
          Value: 90-days
  ```

- [ ] Add configuration in `shared/config/config.py`
  ```python
  class AlpacaConfig:
      ...
      persist_rebalance_plans: bool = True
      rebalance_plans_table: str = "alchemiser-prod-rebalance-plans"
  ```

- [ ] Update IAM role in `template.yaml`
  ```yaml
  Policies:
    - DynamoDBCrudPolicy:
        TableName: !Ref RebalancePlanTable
  ```

- [ ] Create reconstruction utility
  ```python
  # New file: scripts/reconstruct_decision.py
  def reconstruct_decision(correlation_id: str) -> RebalancePlan:
      """Fetch plan from DynamoDB for historical analysis."""
      response = dynamodb.query(
          TableName='RebalancePlanTable',
          IndexName='CorrelationIdIndex',
          KeyConditionExpression='correlation_id = :cid',
          ExpressionAttributeValues={':cid': {'S': correlation_id}}
      )
      
      if not response['Items']:
          raise ValueError(f"No plan found for correlation_id: {correlation_id}")
      
      plan_data = json.loads(response['Items'][0]['plan_data']['S'])
      return RebalancePlan.from_dict(plan_data)
  ```

**Testing**:
- [ ] Unit test: Plan serialization/deserialization
- [ ] Integration test: DynamoDB write and read
- [ ] Test TTL expiration (with short TTL in test environment)
- [ ] Test reconstruction script with historical data
- [ ] Test GSI query performance

**Success Criteria**:
- ✅ Plans persist for 90 days
- ✅ Can answer "why no trade" beyond 24h window
- ✅ Audit trail for compliance
- ✅ Auto-cleanup via TTL after 90 days

---

## 🟡 Phase 2: Multi-Strategy Support (P1)

### Task 2.1: Encode Strategy ID in client_order_id

**Objective**: Enable per-strategy order attribution.

#### Implementation Steps:

- [ ] Update `generate_client_order_id()` signature
  ```python
  # File: shared/utils/order_id_utils.py
  
  def generate_client_order_id(
      symbol: str,
      strategy_id: str,  # CHANGED: was default "alch"
      *,
      prefix: str | None = None,
      signal_version: str | None = None,  # NEW
  ) -> str:
      """
      Format: {strategy_id}-{symbol}-{timestamp}-{uuid}[-v{version}]
      Example: nuclear-AAPL-20231201T093000-a1b2c3d4-v1
      """
  ```

- [ ] Update all call sites to pass strategy_id
  - [ ] `execution_v2/unified/placement_service.py:163`
  - [ ] `execution_v2/handlers/trading_execution_handler.py` (needs strategy context)
  - [ ] Any other locations found by grep

- [ ] Add strategy_id to RebalancePlan metadata
  ```python
  # File: shared/schemas/rebalance_plan.py
  
  class RebalancePlan(BaseModel):
      ...
      strategy_id: str | None = Field(default=None)  # NEW FIELD
  ```

- [ ] Thread strategy_id through event chain
  - [ ] `SignalGenerated.metadata["strategy_id"]`
  - [ ] `RebalancePlanned.rebalance_plan.strategy_id`
  - [ ] `OrderIntent.strategy_id` (new field)

- [ ] Update parsing function
  ```python
  def parse_client_order_id(client_order_id: str) -> dict[str, str] | None:
      """Parse enhanced format: strategy-symbol-timestamp-uuid[-version]"""
  ```

**Testing**:
- [ ] Unit test: ID generation with strategy_id
- [ ] Unit test: ID parsing with new format
- [ ] Integration test: Full order flow with attribution
- [ ] Backward compatibility test (old format still parseable)

**Success Criteria**:
- ✅ Can identify originating strategy from order ID
- ✅ Backward compatible with existing "alch" prefix orders
- ✅ Signal version tracking enabled

---

### Task 2.2: Add Per-Strategy Contributions Tracking

**Objective**: Enable multi-strategy P&L attribution.

#### Implementation Steps:

- [ ] Update `ConsolidatedPortfolio` schema
  ```python
  # File: shared/schemas/consolidated_portfolio.py
  
  class ConsolidatedPortfolio(BaseModel):
      ...
      # NEW FIELD:
      strategy_contributions: dict[str, dict[str, Decimal]] = Field(
          default_factory=dict,
          description="Per-strategy allocation breakdown: {strategy_id: {symbol: weight}}"
      )
  ```

- [ ] Update consolidation logic
  ```python
  # File: strategy_v2/handlers/signal_generation_handler.py
  
  def _build_consolidated_portfolio(...) -> tuple[...]:
      """Track which strategy contributed what."""
      consolidated_portfolio: dict[str, Decimal] = {}
      strategy_contributions: dict[str, dict[str, Decimal]] = {}  # NEW
      
      for signal in signals:
          strategy_id = signal.metadata.get("strategy_id", "unknown")
          symbol = signal.symbol.value
          allocation = self._extract_signal_allocation(signal)
          
          # Existing consolidation
          if symbol in consolidated_portfolio:
              consolidated_portfolio[symbol] += allocation
          else:
              consolidated_portfolio[symbol] = allocation
          
          # NEW: Track contribution
          if strategy_id not in strategy_contributions:
              strategy_contributions[strategy_id] = {}
          strategy_contributions[strategy_id][symbol] = allocation
      
      return consolidated_portfolio, strategy_contributions, contributing_strategies
  ```

- [ ] Update P&L calculation in Trade Ledger
  ```python
  # New method: Calculate per-strategy P&L from fills
  def calculate_strategy_pnl(
      fill: ExecutedOrder,
      strategy_contributions: dict[str, dict[str, Decimal]]
  ) -> dict[str, Decimal]:
      """Decompose fill P&L to contributing strategies."""
  ```

**Testing**:
- [ ] Unit test: Contribution tracking with multiple strategies
- [ ] Unit test: P&L decomposition algorithm
- [ ] Integration test: End-to-end multi-strategy flow
- [ ] Property test: Sum of strategy P&L equals total P&L

**Success Criteria**:
- ✅ Can answer "which strategy made/lost money on this symbol?"
- ✅ Contribution weights sum correctly
- ✅ Handles partial fills correctly

---

### Task 2.3: Implement Multi-Strategy Aggregation

**Objective**: Support concurrent signal emission from multiple strategies.

#### Design Decisions Required:

- [ ] **Conflict Resolution Strategy**:
  - Option A: Simple sum (current within-strategy behavior)
  - Option B: Weighted average by strategy priority
  - Option C: Last-writer-wins with timestamp ordering
  - Option D: Explicit conflict flagging, require manual resolution

- [ ] **Synchronization Mechanism**:
  - Option A: Collect all strategy signals before portfolio planning
  - Option B: Real-time aggregation with eventual consistency
  - Option C: Coordinator Lambda that waits for N strategies

#### Implementation Steps:

- [ ] Choose aggregation pattern (requires architecture discussion)

- [ ] If choosing "Collector Pattern" (recommended):
  ```python
  # New Lambda: strategy_aggregator
  
  def aggregate_signals(signals: list[SignalGenerated]) -> ConsolidatedPortfolio:
      """
      Collect signals from multiple strategies.
      Wait for timeout or N strategies, then consolidate.
      """
  ```

- [ ] Update event routing in `template.yaml`
  ```yaml
  # NEW: Aggregator queue for multi-strategy
  StrategyAggregatorQueue:
    Type: AWS::SQS::Queue
  
  # Route SignalGenerated to aggregator instead of directly to portfolio
  SignalGeneratedRule:
    Properties:
      Targets:
        - Arn: !GetAtt StrategyAggregatorQueue.Arn
  ```

- [ ] Implement conflict resolution logic

**Testing**:
- [ ] Unit test: Aggregation with 0, 1, 2, N strategies
- [ ] Integration test: Concurrent strategy executions
- [ ] Chaos test: Strategy failures during aggregation
- [ ] Performance test: Latency with N strategies

**Success Criteria**:
- ✅ Supports 2+ concurrent strategies
- ✅ Handles conflicts according to chosen strategy
- ✅ Degrades gracefully if strategies timeout

---

## 🟢 Phase 3: Enhanced Observability (P2)

### Task 3.1: Log Suppression Decisions to Trade Ledger

**Objective**: Permanent audit trail of "why no trade" decisions.

#### Implementation Steps:

- [ ] Extend `TradeLedgerEntry` schema
  ```python
  # File: shared/schemas/trade_ledger.py
  
  class TradeLedgerEntry(BaseModel):
      ...
      action: Literal["BUY", "SELL", "SUPPRESSED"] = "BUY"  # CHANGED: add SUPPRESSED
      suppression_reason: str | None = None  # NEW
      intended_trade_amount: Decimal | None = None  # NEW
  ```

- [ ] Log suppressions in planner
  ```python
  # File: portfolio_v2/core/planner.py
  # In _suppress_small_trades() method
  
  for item in items:
      if item.action in ("BUY", "SELL") and abs(item.trade_amount) < min_threshold:
          # Existing logging
          logger.debug("Suppressing micro trade", ...)
          
          # NEW: Write to ledger
          suppressed_entry = TradeLedgerEntry(
              trade_id=f"suppressed_{item.symbol}_{correlation_id}",
              symbol=item.symbol,
              quantity=Decimal("0"),
              action="SUPPRESSED",
              suppression_reason=f"below_threshold_{min_threshold}",
              intended_trade_amount=item.trade_amount,
              correlation_id=correlation_id,
          )
          trade_ledger_service.write_entry(suppressed_entry)
  ```

- [ ] Add DynamoDB write permission

**Testing**:
- [ ] Unit test: Suppression ledger entry creation
- [ ] Integration test: Query suppressed trades
- [ ] Verify no PII in suppression_reason field

**Success Criteria**:
- ✅ Can query "all suppressed trades for correlation_id"
- ✅ Answer "why no trade" from ledger, not ephemeral plan

---

### Task 3.2: Link Fills to Plans via plan_id

**Objective**: Enable plan-level P&L rollup.

#### Implementation Steps:

- [ ] Add `plan_id` to `TradeLedgerEntry`
  ```python
  class TradeLedgerEntry(BaseModel):
      ...
      plan_id: str | None = None  # NEW: links to RebalancePlan
  ```

- [ ] Thread plan_id through execution flow
  ```python
  # execution_v2/handlers/trading_execution_handler.py
  
  for item in rebalance_plan_data.items:
      intent = OrderIntent(
          ...
          plan_id=rebalance_plan_data.plan_id,  # NEW
      )
  ```

- [ ] Create plan-level P&L query
  ```python
  # New utility: scripts/plan_pnl.py
  
  def calculate_plan_pnl(plan_id: str) -> Decimal:
      """Sum all fills linked to this plan."""
      ledger_entries = query_ledger(plan_id=plan_id)
      return sum(entry.realized_pnl for entry in ledger_entries)
  ```

**Testing**:
- [ ] Unit test: plan_id propagation
- [ ] Integration test: Plan-level P&L calculation
- [ ] Test with partial fills

**Success Criteria**:
- ✅ Can answer "total P&L for plan X"
- ✅ Can trace all fills back to originating plan

---

## 📊 Phase 4: Validation & Monitoring

### Task 4.1: Reconstruction Validation Tests

**Objective**: Prove reconstruction works end-to-end.

- [ ] Create test suite: `tests/reconstruction/`
  - [ ] `test_reconstruct_from_broker.py`
  - [ ] `test_reconstruct_from_dynamodb_plans.py`
  - [ ] `test_reconstruct_multi_strategy_pnl.py`

- [ ] Implement historical replay script
  ```python
  # scripts/replay_decision.py
  
  def replay_decision(correlation_id: str) -> ReconstructionResult:
      """
      Given correlation_id:
      1. Fetch SignalGenerated from logs
      2. Fetch RebalancePlan from DynamoDB
      3. Fetch fills from Alpaca
      4. Verify: plan matches actual execution
      """
  ```

- [ ] Run against production data (last 90 days)

**Success Criteria**:
- ✅ 100% of recent plans reconstructable from DynamoDB
- ✅ <1% discrepancy in P&L reconstruction
- ✅ Automated test runs nightly

---

### Task 4.2: Attribution Monitoring Dashboard

**Objective**: Real-time visibility into attribution health.

- [ ] Create CloudWatch dashboard with:
  - [ ] Metric: `OrdersWithStrategyID` (should be 100%)
  - [ ] Metric: `PlansPersisstedToDynamoDB` (should match plans created)
  - [ ] Metric: `AttributionReconstructionTime` (latency for lookups)
  - [ ] Alarm: Plan persistence failures

- [ ] Add CloudWatch Insights queries
  ```sql
  # Query: Orders without strategy attribution
  fields @timestamp, client_order_id
  | filter client_order_id like /^alch-/
  | stats count() by bin(5m)
  ```

**Success Criteria**:
- ✅ Dashboard shows attribution coverage > 99%
- ✅ Alerts trigger if plan persistence fails

---

## 🔒 Phase 5: Security & Compliance

### Task 5.1: Audit Trail Validation

- [ ] Verify all plan writes are encrypted (DynamoDB encryption at rest enabled)
- [ ] Implement CloudTrail logging for DynamoDB table access
- [ ] Create compliance report script
  ```python
  # scripts/compliance_report.py
  
  def generate_audit_trail(start_date: date, end_date: date) -> Report:
      """Generate regulatory-compliant trade decision audit."""
      # Query DynamoDB for plans in date range
      # Include suppression decisions from Trade Ledger
      # Generate timestamped audit report
  ```

- [ ] Test data retention policy (90 days via TTL)

**Success Criteria**:
- ✅ All plans encrypted at rest (DynamoDB default encryption)
- ✅ Access audit trail via CloudTrail for forensics
- ✅ Meets regulatory requirements

---

## ✅ Definition of Done

For each phase, consider complete when:

1. **Code**:
   - [ ] Implementation merged to main
   - [ ] All tests passing (unit + integration)
   - [ ] Code review approved
   - [ ] Documentation updated

2. **Observability**:
   - [ ] Metrics tracked in CloudWatch
   - [ ] Alarms configured
   - [ ] Runbook created for alerts

3. **Validation**:
   - [ ] Tested in dev environment
   - [ ] Load tested in staging
   - [ ] Validated with production replay

4. **Rollout**:
   - [ ] Feature flag controlled (if applicable)
   - [ ] Rollback plan documented
   - [ ] Post-deployment verification complete

---

## 🎯 Success Metrics

Track these KPIs after implementation:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Attribution Coverage | >99% | Orders with valid strategy_id |
| Plan Persistence Rate | 100% | Plans in DynamoDB / Plans created |
| Reconstruction Success Rate | >99.9% | Historical replays matching broker |
| Suppressed Trade Visibility | 100% | Suppressions logged to ledger |
| Multi-Strategy P&L Accuracy | <0.1% error | Decomposed P&L vs total |

---

## 🚀 Rollout Strategy

Suggested phased rollout:

1. **Week 1-2**: Phase 1 (Plan Persistence)
   - Low risk, high value
   - Deploy to dev, then prod

2. **Week 3-4**: Phase 2.1 (Strategy ID)
   - Medium risk, requires coordination
   - Deploy with feature flag

3. **Week 5-8**: Phase 2.2-2.3 (Multi-Strategy)
   - High complexity, requires design decisions
   - POC in dev first

4. **Week 9-10**: Phase 3 (Observability)
   - Low risk, incremental value

5. **Ongoing**: Phase 4-5 (Validation & Compliance)
   - Continuous monitoring

---

## 📚 Related Documents

- [ORDER_ATTRIBUTION_ANALYSIS.md](ORDER_ATTRIBUTION_ANALYSIS.md) - Detailed analysis
- [ORDER_ATTRIBUTION_SUMMARY.md](ORDER_ATTRIBUTION_SUMMARY.md) - Executive summary
- Architecture diagrams (to be created)
- ADRs for design decisions (to be created)

---

**Checklist Version**: 1.0  
**Last Updated**: 2025-12-13  
**Maintainer**: Platform Team
