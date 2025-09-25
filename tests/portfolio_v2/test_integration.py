"""Integration tests for portfolio_v2 refactored functionality."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import Mock, patch

from the_alchemiser.portfolio_v2.adapters import (
    AccountInfoDTO,
    PositionDTO,
    adapt_account_info,
    generate_account_snapshot_id,
)
from the_alchemiser.shared.events.schemas import RebalancePlanned, SignalGenerated
from the_alchemiser.shared.persistence.portfolio_idempotency_store import (
    get_portfolio_idempotency_store,
)
from the_alchemiser.shared.utils.plan_hashing import generate_plan_hash
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItem
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO


class TestPortfolioV2Integration:
    """Test integration of portfolio_v2 refactored components."""
    
    def test_dto_adapters_work_together(self):
        """Test that DTO adapters work together for account snapshot generation."""
        # Mock raw account data
        raw_account = {
            "cash": "1000.50",
            "buying_power": "2500.75",
            "portfolio_value": "5000.25",
            "equity": "4800.00",
            "account_id": "test_account",
        }
        
        # Mock raw positions
        raw_positions = [
            {
                "symbol": "AAPL",
                "qty": "100.5",
                "market_value": "3000.50",
                "avg_entry_price": "150.25",
                "unrealized_pl": "500.25",
            },
            {
                "symbol": "GOOGL", 
                "qty": "25",
                "market_value": "2000.75",
                "avg_entry_price": "80.03",
                "unrealized_pl": "-100.50",
            },
        ]
        
        # Adapt to DTOs
        account_dto = adapt_account_info(raw_account)
        positions_dto = [
            PositionDTO(
                symbol=pos["symbol"],
                quantity=Decimal(str(pos["qty"])),
                market_value=Decimal(str(pos["market_value"])),
                avg_entry_price=Decimal(str(pos["avg_entry_price"])),
                unrealized_pl=Decimal(str(pos["unrealized_pl"])),
            )
            for pos in raw_positions
        ]
        
        # Generate account snapshot ID
        snapshot_id = generate_account_snapshot_id(account_dto, positions_dto)
        
        # Verify results
        assert isinstance(account_dto, AccountInfoDTO)
        assert account_dto.cash == Decimal("1000.50")
        assert account_dto.portfolio_value == Decimal("5000.25")
        
        assert len(positions_dto) == 2
        assert positions_dto[0].symbol == "AAPL"
        assert positions_dto[1].symbol == "GOOGL"
        
        assert snapshot_id.startswith("account_")
        assert len(snapshot_id) > 20  # Should include timestamp and hash
        
        # Test deterministic snapshot ID generation
        snapshot_id2 = generate_account_snapshot_id(account_dto, positions_dto)
        # Content hash should be same (last 8 chars)
        assert snapshot_id.split("_")[-1] == snapshot_id2.split("_")[-1]

    def test_plan_hash_generation_deterministic(self):
        """Test that plan hash generation is deterministic."""
        # Create test rebalance plan
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.6"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("2500"),
                current_value=Decimal("3000"),
                trade_amount=Decimal("-500"),
                action="SELL",
                priority=1,
            ),
            RebalancePlanItem(
                symbol="GOOGL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("2500"),
                current_value=Decimal("2000"),
                trade_amount=Decimal("500"),
                action="BUY",
                priority=2,
            ),
        ]
        
        rebalance_plan = RebalancePlanDTO(
            plan_id="test-plan-123",
            correlation_id="test-correlation",
            causation_id="test-causation",
            timestamp=datetime.now(UTC),
            items=plan_items,
            total_portfolio_value=Decimal("5000"),
            total_trade_value=Decimal("1000"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50"), "GOOGL": Decimal("50")},
            current_values={"AAPL": Decimal("60"), "GOOGL": Decimal("40")},
            deltas={"AAPL": Decimal("-10"), "GOOGL": Decimal("10")},
        )
        
        account_snapshot_id = "account_20240101_120000_abc12345"
        
        # Generate hash multiple times
        hash1 = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        hash2 = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        
        assert hash1 == hash2
        assert len(hash1) == 16
        assert isinstance(hash1, str)
        
        # Different account snapshot should produce different hash
        different_snapshot = "account_20240101_120000_def67890"
        hash3 = generate_plan_hash(rebalance_plan, allocation_comparison, different_snapshot)
        assert hash1 != hash3

    def test_idempotency_store_functionality(self):
        """Test that idempotency store works correctly."""
        store = get_portfolio_idempotency_store()
        
        # Clear any existing cache for clean test
        store._cache.clear()
        
        plan_hash = "test_plan_hash_123"
        correlation_id = "test_correlation_456"
        
        # Initially should not exist
        assert not store.has_plan_hash(plan_hash, correlation_id)
        
        # Store the hash
        store.store_plan_hash(
            plan_hash=plan_hash,
            correlation_id=correlation_id,
            causation_id="test_causation",
            account_snapshot_id="test_snapshot",
            metadata={"test": "value"},
        )
        
        # Now should exist
        assert store.has_plan_hash(plan_hash, correlation_id)
        
        # Should be able to get metadata
        metadata = store.get_plan_metadata(plan_hash, correlation_id)
        assert metadata is not None
        assert metadata["plan_hash"] == plan_hash
        assert metadata["correlation_id"] == correlation_id
        assert metadata["metadata"]["test"] == "value"

    def test_enhanced_rebalance_planned_event_creation(self):
        """Test creation of enhanced RebalancePlanned event."""
        # Create test plan
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.6"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("2500"),
                current_value=Decimal("3000"),
                trade_amount=Decimal("-500"),
                action="SELL",
                priority=1,
            ),
        ]
        
        rebalance_plan = RebalancePlanDTO(
            plan_id="test-plan",
            correlation_id="test-correlation",
            causation_id="test-causation",
            timestamp=datetime.now(UTC),
            items=plan_items,
            total_portfolio_value=Decimal("5000"),
            total_trade_value=Decimal("500"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50")},
            current_values={"AAPL": Decimal("60")},
            deltas={"AAPL": Decimal("-10")},
        )
        
        # Create enhanced event
        event = RebalancePlanned(
            correlation_id="test-correlation",
            causation_id="test-causation",
            event_id="rebalance-planned-123",
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2.handlers",
            source_component="PortfolioAnalysisHandler",
            rebalance_plan=rebalance_plan,
            allocation_comparison=allocation_comparison,
            trades_required=True,
            metadata={"analysis_timestamp": datetime.now(UTC).isoformat()},
            # Enhanced fields
            schema_version="1.0",
            plan_hash="test_plan_hash_123",
            account_snapshot_id="account_20240101_120000_abc12345",
        )
        
        # Verify enhanced fields
        assert event.schema_version == "1.0"
        assert event.plan_hash == "test_plan_hash_123"
        assert event.account_snapshot_id == "account_20240101_120000_abc12345"
        assert event.trades_required is True
        
        # Verify core fields
        assert event.correlation_id == "test-correlation"
        assert event.causation_id == "test-causation"
        assert event.rebalance_plan == rebalance_plan
        assert event.allocation_comparison == allocation_comparison

    def test_portfolio_analysis_idempotency_workflow(self):
        """Test the complete idempotency workflow."""
        # Setup
        store = get_portfolio_idempotency_store()
        store._cache.clear()
        
        # Mock account data
        account_dto = AccountInfoDTO(
            cash=Decimal("1000"),
            buying_power=Decimal("2000"),
            portfolio_value=Decimal("5000"),
        )
        
        positions_dto = [
            PositionDTO(
                symbol="AAPL",
                quantity=Decimal("100"),
                market_value=Decimal("3000"),
            ),
        ]
        
        # Generate snapshot ID
        account_snapshot_id = generate_account_snapshot_id(account_dto, positions_dto)
        
        # Create plan
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.6"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("2500"),
                current_value=Decimal("3000"),
                trade_amount=Decimal("-500"),
                action="SELL",
                priority=1,
            ),
        ]
        
        rebalance_plan = RebalancePlanDTO(
            plan_id="test-plan",
            correlation_id="test-correlation",
            causation_id="test-causation", 
            timestamp=datetime.now(UTC),
            items=plan_items,
            total_portfolio_value=Decimal("5000"),
            total_trade_value=Decimal("500"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50")},
            current_values={"AAPL": Decimal("60")},
            deltas={"AAPL": Decimal("-10")},
        )
        
        # Generate plan hash
        plan_hash = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        
        correlation_id = "test-correlation"
        
        # First time - should not exist
        assert not store.has_plan_hash(plan_hash, correlation_id)
        
        # Store the plan hash (simulating first processing)
        store.store_plan_hash(
            plan_hash=plan_hash,
            correlation_id=correlation_id,
            causation_id="test-causation",
            account_snapshot_id=account_snapshot_id,
        )
        
        # Second time - should exist (simulating replay)
        assert store.has_plan_hash(plan_hash, correlation_id)
        
        # Should be able to retrieve metadata
        metadata = store.get_plan_metadata(plan_hash, correlation_id)
        assert metadata is not None
        assert metadata["account_snapshot_id"] == account_snapshot_id

    def test_dto_immutability_and_validation(self):
        """Test that DTOs are immutable and validate correctly."""
        # Test AccountInfoDTO immutability
        account_dto = AccountInfoDTO(
            cash=Decimal("1000"),
            buying_power=Decimal("2000"),
            portfolio_value=Decimal("5000"),
        )
        
        with pytest.raises(ValueError, match="Instance is frozen"):
            account_dto.cash = Decimal("2000")
        
        # Test PositionDTO validation
        position_dto = PositionDTO(
            symbol="  aapl  ",  # Should be normalized
            quantity=Decimal("100.5"),
            market_value=Decimal("15000"),
        )
        
        assert position_dto.symbol == "AAPL"  # Normalized to uppercase
        
        with pytest.raises(ValueError, match="Instance is frozen"):
            position_dto.symbol = "GOOGL"

    def test_end_to_end_deterministic_behavior(self):
        """Test that the entire workflow produces deterministic results."""
        # Same input data
        raw_account = {
            "cash": "1000.00",
            "buying_power": "2000.00", 
            "portfolio_value": "5000.00",
        }
        
        raw_positions = [
            {"symbol": "AAPL", "qty": "100", "market_value": "3000.00"},
            {"symbol": "GOOGL", "qty": "50", "market_value": "2000.00"},
        ]
        
        # Process twice
        results = []
        for i in range(2):
            account_dto = adapt_account_info(raw_account)
            positions_dto = [
                PositionDTO(
                    symbol=pos["symbol"],
                    quantity=Decimal(pos["qty"]),
                    market_value=Decimal(pos["market_value"]),
                )
                for pos in raw_positions
            ]
            
            snapshot_id = generate_account_snapshot_id(account_dto, positions_dto)
            
            results.append({
                "account_dto": account_dto,
                "positions_dto": positions_dto,
                "snapshot_id": snapshot_id,
            })
        
        # Should produce identical results
        assert results[0]["account_dto"] == results[1]["account_dto"]
        assert results[0]["positions_dto"] == results[1]["positions_dto"]
        
        # Snapshot IDs should have same content hash (last part)
        hash1 = results[0]["snapshot_id"].split("_")[-1]
        hash2 = results[1]["snapshot_id"].split("_")[-1]
        assert hash1 == hash2  # Content hash should be deterministic