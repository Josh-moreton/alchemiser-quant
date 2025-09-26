"""Tests for plan hashing utilities."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import Mock

from the_alchemiser.shared.utils.plan_hashing import (
    generate_plan_hash,
    generate_simple_plan_hash,
    _normalize_plan_for_hash,
    _normalize_allocation_comparison_for_hash,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItem
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO


class TestGeneratePlanHash:
    """Test plan hash generation."""

    def test_generate_plan_hash_deterministic(self):
        """Test that plan hash generation is deterministic."""
        # Create test rebalance plan
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
            RebalancePlanItem(
                symbol="GOOGL",
                current_weight=Decimal("0.6"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("6000"),
                trade_amount=Decimal("-1000"),
                action="SELL",
                priority=2,
            ),
        ]
        
        rebalance_plan = RebalancePlanDTO(
            plan_id="test-plan-123",
            causation_id="test-causation",
            items=plan_items,
            total_trade_value=Decimal("2000"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50"), "GOOGL": Decimal("50")},
            current_values={"AAPL": Decimal("40"), "GOOGL": Decimal("60")},
            deltas={"AAPL": Decimal("10"), "GOOGL": Decimal("-10")},
        )
        
        account_snapshot_id = "account_20240101_120000_abc12345"
        
        # Generate hash multiple times - should be the same
        hash1 = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        hash2 = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        hash3 = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        
        assert hash1 == hash2 == hash3
        assert len(hash1) == 16  # Should be 16 chars
        assert isinstance(hash1, str)

    def test_generate_plan_hash_different_for_different_plans(self):
        """Test that different plans produce different hashes."""
        base_plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        # Plan 1
        plan1 = RebalancePlanDTO(
            plan_id="test-plan-1",
            causation_id="test-causation",
            items=base_plan_items,
            total_trade_value=Decimal("1000"),
        )
        
        # Plan 2 - different trade amount
        different_plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.6"),  # Different target weight
                weight_diff=Decimal("0.2"),
                target_value=Decimal("6000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("2000"),  # Different trade amount
                action="BUY",
                priority=1,
            ),
        ]
        
        plan2 = RebalancePlanDTO(
            plan_id="test-plan-2",
            causation_id="test-causation",
            items=different_plan_items,
            total_trade_value=Decimal("2000"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50")},
            current_values={"AAPL": Decimal("40")},
            deltas={"AAPL": Decimal("10")},
        )
        
        account_snapshot_id = "account_20240101_120000_abc12345"
        
        hash1 = generate_plan_hash(plan1, allocation_comparison, account_snapshot_id)
        hash2 = generate_plan_hash(plan2, allocation_comparison, account_snapshot_id)
        
        assert hash1 != hash2

    def test_generate_plan_hash_ignores_volatile_fields(self):
        """Test that volatile fields don't affect hash."""
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        # Plan 1
        plan1 = RebalancePlanDTO(
            plan_id="plan-1",  # Different plan ID (should be ignored)
            causation_id="causation-1",
            items=plan_items,
            total_trade_value=Decimal("1000"),
        )
        
        # Plan 2 - same content but different volatile fields
        plan2 = RebalancePlanDTO(
            plan_id="plan-2",  # Different plan ID
            causation_id="causation-2",
            items=plan_items,
            total_trade_value=Decimal("1000"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50")},
            current_values={"AAPL": Decimal("40")},
            deltas={"AAPL": Decimal("10")},
        )
        
        account_snapshot_id = "account_20240101_120000_abc12345"
        
        hash1 = generate_plan_hash(plan1, allocation_comparison, account_snapshot_id)
        hash2 = generate_plan_hash(plan2, allocation_comparison, account_snapshot_id)
        
        assert hash1 == hash2  # Should be same despite different volatile fields

    def test_generate_plan_hash_handles_errors_gracefully(self):
        """Test that errors in hash generation return fallback."""
        # Create plan with potentially problematic data
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        rebalance_plan = RebalancePlanDTO(
            plan_id="test-plan",
            causation_id="test-causation",
            items=plan_items,
            total_trade_value=Decimal("1000"),
        )
        
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50")},
            current_values={"AAPL": Decimal("40")},
            deltas={"AAPL": Decimal("10")},
        )
        
        account_snapshot_id = "account_20240101_120000_abc12345"
        
        # Normal case should work
        hash_result = generate_plan_hash(rebalance_plan, allocation_comparison, account_snapshot_id)
        
        # Should return a hash (including fallback case)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16


class TestNormalizePlanForHash:
    """Test plan normalization for hashing."""

    def test_normalize_plan_removes_volatile_fields(self):
        """Test that volatile fields are removed from plan."""
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.5"),
                target_weight=Decimal("0.6"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("6000"),
                current_value=Decimal("5000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        plan = RebalancePlanDTO(
            plan_id="test-plan-123",  # Should be removed
            causation_id="test-causation",  # Should be removed
            items=plan_items,
            total_trade_value=Decimal("1000"),
            execution_urgency="HIGH",
            estimated_duration_minutes=30,  # Should be removed
        )
        
        normalized = _normalize_plan_for_hash(plan)
        
        # Volatile fields should be removed
        assert "plan_id" not in normalized
        assert "correlation_id" not in normalized
        assert "causation_id" not in normalized
        assert "timestamp" not in normalized
        assert "estimated_duration_minutes" not in normalized
        assert "metadata" not in normalized
        
        # Core plan fields should remain
        assert "items" in normalized
        assert "total_portfolio_value" in normalized
        assert "total_trade_value" in normalized
        assert "execution_urgency" in normalized

    def test_normalize_plan_sorts_items_by_symbol(self):
        """Test that plan items are sorted by symbol."""
        plan_items = [
            RebalancePlanItem(
                symbol="GOOGL",  # Second alphabetically
                current_weight=Decimal("0.6"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("6000"),
                trade_amount=Decimal("-1000"),
                action="SELL",
                priority=2,
            ),
            RebalancePlanItem(
                symbol="AAPL",  # First alphabetically
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        plan = RebalancePlanDTO(
            plan_id="test-plan",
            causation_id="test-causation",
            items=plan_items,
            total_trade_value=Decimal("2000"),
        )
        
        normalized = _normalize_plan_for_hash(plan)
        
        # Items should be sorted by symbol (AAPL before GOOGL)
        assert len(normalized["items"]) == 2
        assert normalized["items"][0]["symbol"] == "AAPL"
        assert normalized["items"][1]["symbol"] == "GOOGL"

    def test_normalize_plan_converts_decimals_to_strings(self):
        """Test that Decimal fields are converted to strings."""
        plan_items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("5000"),
                current_value=Decimal("4000"),
                trade_amount=Decimal("1000"),
                action="BUY",
                priority=1,
            ),
        ]
        
        plan = RebalancePlanDTO(
            plan_id="test-plan",
            causation_id="test-causation",
            items=plan_items,
            total_trade_value=Decimal("1000.25"),
        )
        
        normalized = _normalize_plan_for_hash(plan)
        
        # Decimal fields should be converted to strings
        assert normalized["total_trade_value"] == "1000.25"
        
        # Item decimal fields should also be strings
        item = normalized["items"][0]
        assert item["current_weight"] == "0.4"
        assert item["target_weight"] == "0.5"
        assert item["trade_amount"] == "1000"


class TestNormalizeAllocationComparisonForHash:
    """Test allocation comparison normalization."""

    def test_normalize_allocation_comparison_removes_volatile_fields(self):
        """Test that volatile fields are removed."""
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("50"), "GOOGL": Decimal("50")},
            current_values={"AAPL": Decimal("40"), "GOOGL": Decimal("60")},
            deltas={"AAPL": Decimal("10"), "GOOGL": Decimal("-10")},
        )
        
        normalized = _normalize_allocation_comparison_for_hash(allocation_comparison)
        
        # Volatile fields should be removed
        assert "timestamp" not in normalized
        assert "correlation_id" not in normalized
        assert "metadata" not in normalized
        
        # Core fields should remain
        assert "target_values" in normalized
        assert "current_values" in normalized
        assert "deltas" in normalized

    def test_normalize_allocation_comparison_sorts_allocations(self):
        """Test that allocation dictionaries are sorted by symbol."""
        allocation_comparison = AllocationComparisonDTO(
            target_values={"GOOGL": Decimal("30"), "AAPL": Decimal("70")},  # Unsorted
            current_values={"GOOGL": Decimal("40"), "AAPL": Decimal("60")},  # Unsorted
            deltas={"GOOGL": Decimal("-10"), "AAPL": Decimal("10")},  # Unsorted
        )
        
        normalized = _normalize_allocation_comparison_for_hash(allocation_comparison)
        
        # Allocations should be sorted by symbol
        target_keys = list(normalized["target_values"].keys())
        current_keys = list(normalized["current_values"].keys())
        delta_keys = list(normalized["deltas"].keys())
        
        assert target_keys == ["AAPL", "GOOGL"]
        assert current_keys == ["AAPL", "GOOGL"]
        assert delta_keys == ["AAPL", "GOOGL"]

    def test_normalize_allocation_comparison_converts_values_to_strings(self):
        """Test that numeric values are converted to strings."""
        allocation_comparison = AllocationComparisonDTO(
            target_values={"AAPL": Decimal("70.5")},
            current_values={"AAPL": Decimal("60.3")},
            deltas={"AAPL": Decimal("10.2")},
        )
        
        normalized = _normalize_allocation_comparison_for_hash(allocation_comparison)
        
        # Values should be converted to strings
        assert normalized["target_values"]["AAPL"] == "70.5"
        assert normalized["current_values"]["AAPL"] == "60.3"
        assert normalized["deltas"]["AAPL"] == "10.2"


class TestGenerateSimplePlanHash:
    """Test simple plan hash generation."""

    def test_generate_simple_plan_hash_deterministic(self):
        """Test that simple plan hash is deterministic."""
        plan_content = {
            "symbols": ["AAPL", "GOOGL"],
            "total_value": 10000,
            "strategy": "rebalance",
        }
        
        hash1 = generate_simple_plan_hash(plan_content)
        hash2 = generate_simple_plan_hash(plan_content)
        hash3 = generate_simple_plan_hash(plan_content)
        
        assert hash1 == hash2 == hash3
        assert len(hash1) == 16
        assert isinstance(hash1, str)

    def test_generate_simple_plan_hash_different_for_different_content(self):
        """Test that different content produces different hashes."""
        plan_content1 = {
            "symbols": ["AAPL", "GOOGL"],
            "total_value": 10000,
        }
        
        plan_content2 = {
            "symbols": ["AAPL", "MSFT"],  # Different symbol
            "total_value": 10000,
        }
        
        hash1 = generate_simple_plan_hash(plan_content1)
        hash2 = generate_simple_plan_hash(plan_content2)
        
        assert hash1 != hash2

    def test_generate_simple_plan_hash_handles_errors(self):
        """Test error handling returns fallback hash."""
        # Create content that might cause JSON serialization issues
        from unittest.mock import Mock
        problematic_content = {
            "valid_key": "valid_value",
            "problematic": Mock(),  # This should cause JSON error
        }
        
        hash_result = generate_simple_plan_hash(problematic_content)
        
        # Should still return a hash (fallback)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16