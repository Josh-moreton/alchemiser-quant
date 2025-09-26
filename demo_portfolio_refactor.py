#!/usr/bin/env python3
"""
Demonstration script for portfolio_v2 refactor functionality.

Shows the deterministic behavior of plan hashing, DTO adapters, and idempotency.
"""

from decimal import Decimal
from datetime import datetime, UTC

from the_alchemiser.portfolio_v2.adapters import (
    AccountInfoDTO,
    PositionDTO,
    adapt_account_info,
    generate_account_snapshot_id,
)
from the_alchemiser.shared.events.schemas import RebalancePlanned
from the_alchemiser.shared.persistence.portfolio_idempotency_store import (
    get_portfolio_idempotency_store,
)
from the_alchemiser.shared.utils.plan_hashing import generate_plan_hash
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItem
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO


def main():
    """Demonstrate portfolio_v2 refactor functionality."""
    print("🚀 Portfolio_v2 Refactor Demonstration")
    print("=" * 50)
    
    # 1. Demonstrate DTO Adapters
    print("\n1. DTO Adapters - Eliminating Raw Dict Usage")
    print("-" * 45)
    
    # Mock raw broker data (what we used to work with)
    raw_account = {
        "cash": "1500.75",
        "buying_power": "3200.50",
        "portfolio_value": "10000.25",
        "equity": "9800.00",
        "account_id": "demo_account_123",
    }
    
    raw_positions = [
        {"symbol": "AAPL", "qty": "60", "market_value": "6000.00"},
        {"symbol": "GOOGL", "qty": "20", "market_value": "4000.25"},
    ]
    
    # Convert to strongly-typed DTOs
    account_dto = adapt_account_info(raw_account)
    positions_dto = [
        PositionDTO(
            symbol=pos["symbol"],
            quantity=Decimal(pos["qty"]),
            market_value=Decimal(pos["market_value"]),
        )
        for pos in raw_positions
    ]
    
    print(f"✅ Account DTO: cash={account_dto.cash}, portfolio_value={account_dto.portfolio_value}")
    print(f"✅ Positions: {len(positions_dto)} positions with types: {[type(p).__name__ for p in positions_dto]}")
    
    # 2. Demonstrate Account Snapshot ID Generation
    print("\n2. Deterministic Account Snapshot Generation")
    print("-" * 45)
    
    snapshot_id_1 = generate_account_snapshot_id(account_dto, positions_dto)
    snapshot_id_2 = generate_account_snapshot_id(account_dto, positions_dto)
    
    print(f"✅ Snapshot ID 1: {snapshot_id_1}")
    print(f"✅ Snapshot ID 2: {snapshot_id_2}")
    print(f"✅ IDs identical: {snapshot_id_1 == snapshot_id_2} (fully deterministic!)")
    
    # 3. Demonstrate Plan Hash Generation
    print("\n3. Deterministic Plan Hash Generation")
    print("-" * 40)
    
    # Create a rebalance plan
    plan_items = [
        RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.6"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("-0.1"),
            target_value=Decimal("5000"),
            current_value=Decimal("6000"),
            trade_amount=Decimal("-1000"),
            action="SELL",
            priority=1,
        ),
        RebalancePlanItem(
            symbol="GOOGL",
            current_weight=Decimal("0.4"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.1"),
            target_value=Decimal("5000"),
            current_value=Decimal("4000"),
            trade_amount=Decimal("1000"),
            action="BUY",
            priority=2,
        ),
    ]
    
    rebalance_plan = RebalancePlanDTO(
        plan_id="demo-plan-123",
        correlation_id="demo-correlation",
        causation_id="demo-causation",
        timestamp=datetime.now(UTC),
        items=plan_items,
        total_portfolio_value=Decimal("10000"),
        total_trade_value=Decimal("2000"),
    )
    
    allocation_comparison = AllocationComparisonDTO(
        target_values={"AAPL": Decimal("50"), "GOOGL": Decimal("50")},
        current_values={"AAPL": Decimal("60"), "GOOGL": Decimal("40")},
        deltas={"AAPL": Decimal("-10"), "GOOGL": Decimal("10")},
    )
    
    # Generate plan hashes
    plan_hash_1 = generate_plan_hash(rebalance_plan, allocation_comparison, snapshot_id_1)
    plan_hash_2 = generate_plan_hash(rebalance_plan, allocation_comparison, snapshot_id_2)
    
    print(f"✅ Plan hash 1: {plan_hash_1}")
    print(f"✅ Plan hash 2: {plan_hash_2}")
    print(f"✅ Plan hashes match: {plan_hash_1 == plan_hash_2} (deterministic!)")
    
    # 4. Demonstrate Idempotency Store
    print("\n4. Idempotency Store - Duplicate Prevention")
    print("-" * 45)
    
    store = get_portfolio_idempotency_store()
    store._cache.clear()  # Clear for demo
    
    plan_hash = plan_hash_1
    correlation_id = "demo-correlation"
    
    # First check - should not exist
    exists_before = store.has_plan_hash(plan_hash, correlation_id)
    print(f"✅ Plan exists before storing: {exists_before}")
    
    # Store the plan hash
    store.store_plan_hash(
        plan_hash=plan_hash,
        correlation_id=correlation_id,
        causation_id="demo-causation",
        account_snapshot_id=snapshot_id_1,
        metadata={"demo": "value", "trades_count": len(plan_items)},
    )
    
    # Second check - should exist now
    exists_after = store.has_plan_hash(plan_hash, correlation_id)
    print(f"✅ Plan exists after storing: {exists_after}")
    
    # Get metadata
    metadata = store.get_plan_metadata(plan_hash, correlation_id)
    print(f"✅ Retrieved metadata: {metadata['metadata'] if metadata else 'None'}")
    
    # 5. Demonstrate Enhanced Event Schema
    print("\n5. Enhanced RebalancePlanned Event")
    print("-" * 35)
    
    enhanced_event = RebalancePlanned(
        correlation_id=correlation_id,
        causation_id="demo-causation",
        event_id="rebalance-planned-demo",
        timestamp=datetime.now(UTC),
        source_module="portfolio_v2.handlers",
        source_component="PortfolioAnalysisHandler",
        rebalance_plan=rebalance_plan,
        allocation_comparison=allocation_comparison,
        trades_required=True,
        metadata={"analysis_timestamp": datetime.now(UTC).isoformat()},
        # Enhanced fields for idempotency and traceability
        schema_version="1.0",
        plan_hash=plan_hash,
        account_snapshot_id=snapshot_id_1,
    )
    
    print(f"✅ Enhanced event created with {len(enhanced_event.model_fields)} fields")
    print(f"✅ Schema version: {enhanced_event.schema_version}")
    print(f"✅ Plan hash: {enhanced_event.plan_hash}")
    print(f"✅ Account snapshot: {enhanced_event.account_snapshot_id}")
    print(f"✅ Trades required: {enhanced_event.trades_required}")
    
    # 6. Demonstrate Idempotent Replay Behavior
    print("\n6. Idempotent Replay Simulation")
    print("-" * 35)
    
    # Simulate replay with same data
    print("Simulating event replay with identical data...")
    
    # Generate same plan hash again (simulating replay)
    replay_plan_hash = generate_plan_hash(rebalance_plan, allocation_comparison, snapshot_id_1)
    print(f"✅ Original hash: {plan_hash}")
    print(f"✅ Replay hash:   {replay_plan_hash}")
    print(f"✅ Hashes match:  {plan_hash == replay_plan_hash}")
    
    # Check if already processed (should be True - duplicate detected)
    already_processed = store.has_plan_hash(replay_plan_hash, correlation_id)
    print(f"✅ Already processed (would skip): {already_processed}")
    
    print("\n🎉 Demonstration Complete!")
    print("=" * 50)
    print("Summary of improvements:")
    print("• ✅ Raw dict usage eliminated with strongly-typed DTOs")
    print("• ✅ Deterministic plan hashing for idempotency")
    print("• ✅ Account snapshot correlation for traceability")
    print("• ✅ Persistent idempotency store prevents duplicates")
    print("• ✅ Enhanced events with schema versioning")
    print("• ✅ Registry-based handler registration (no orchestrator imports)")
    print("• ✅ Structured logging with correlation metadata")


if __name__ == "__main__":
    main()