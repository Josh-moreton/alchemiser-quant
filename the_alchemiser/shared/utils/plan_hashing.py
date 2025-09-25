#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Plan hashing utilities for deterministic rebalance plan identification.

Provides deterministic hash generation for rebalance plans to support
idempotent event processing and replay detection in portfolio workflows.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO

logger = get_logger(__name__)


def generate_plan_hash(
    rebalance_plan: RebalancePlanDTO,
    allocation_comparison: AllocationComparisonDTO,
    account_snapshot_id: str,
) -> str:
    """Generate deterministic hash for rebalance plan.
    
    Creates a stable hash from rebalance plan, allocation comparison, and account
    state that remains consistent across multiple invocations with the same data.
    
    Args:
        rebalance_plan: The rebalance plan to hash
        allocation_comparison: Allocation comparison data
        account_snapshot_id: Account state snapshot identifier
        
    Returns:
        Hexadecimal hash string for idempotency checking
    """
    try:
        # Create normalized data structure for hashing
        hash_data = {
            "plan": _normalize_plan_for_hash(rebalance_plan),
            "allocation": _normalize_allocation_comparison_for_hash(allocation_comparison),
            "account_snapshot": account_snapshot_id,
        }
        
        # Convert to deterministic JSON (sorted keys)
        json_data = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(json_data.encode("utf-8"))
        plan_hash = hash_obj.hexdigest()[:16]  # Use first 16 chars for readability
        
        logger.debug(
            f"Generated plan hash: {plan_hash} from {len(json_data)} bytes"
        )
        return plan_hash
        
    except Exception as e:
        logger.error(f"Failed to generate plan hash: {e}")
        # Return a fallback hash based on plan ID to avoid blocking
        fallback_data = f"{rebalance_plan.plan_id}_{account_snapshot_id}"
        fallback = hashlib.sha256(fallback_data.encode()).hexdigest()[:16]
        logger.warning(f"Using fallback plan hash: {fallback}")
        return fallback


def _normalize_plan_for_hash(plan: RebalancePlanDTO) -> dict[str, Any]:
    """Normalize rebalance plan for consistent hashing.
    
    Removes volatile fields and ensures stable ordering for deterministic hashing.
    """
    # Convert plan to dict and normalize
    plan_dict = plan.model_dump()
    
    # Remove volatile fields that shouldn't affect plan hash
    volatile_fields = {
        "plan_id",  # Generated UUID, not part of plan content
        "correlation_id",  # Event correlation, not plan content  
        "causation_id",  # Event causation, not plan content
        "timestamp",  # Time of creation, not plan content
        "estimated_duration_minutes",  # Estimate, not plan content
        "metadata",  # Additional metadata, not core plan
    }
    
    stable_plan = {
        key: value for key, value in plan_dict.items() 
        if key not in volatile_fields
    }
    
    # Sort items by symbol for consistent ordering
    if "items" in stable_plan and isinstance(stable_plan["items"], list):
        stable_plan["items"] = sorted(
            stable_plan["items"], 
            key=lambda x: x.get("symbol", "") if isinstance(x, dict) else ""
        )
        
        # Normalize item fields to ensure consistent hashing
        normalized_items = []
        for item in stable_plan["items"]:
            if isinstance(item, dict):
                normalized_item = {
                    "symbol": item.get("symbol", ""),
                    "action": item.get("action", ""),
                    "current_weight": str(item.get("current_weight", 0)),
                    "target_weight": str(item.get("target_weight", 0)),
                    "weight_diff": str(item.get("weight_diff", 0)),
                    "target_value": str(item.get("target_value", 0)),
                    "current_value": str(item.get("current_value", 0)),
                    "trade_amount": str(item.get("trade_amount", 0)),
                    "priority": item.get("priority", 1),
                }
                normalized_items.append(normalized_item)
            else:
                normalized_items.append(item)
        stable_plan["items"] = normalized_items
    
    # Convert Decimal fields to strings for consistent representation
    decimal_fields = ["total_portfolio_value", "total_trade_value", "max_drift_tolerance"]
    for field in decimal_fields:
        if field in stable_plan and stable_plan[field] is not None:
            stable_plan[field] = str(stable_plan[field])
    
    return stable_plan


def _normalize_allocation_comparison_for_hash(
    allocation_comparison: AllocationComparisonDTO,
) -> dict[str, Any]:
    """Normalize allocation comparison for consistent hashing."""
    comp_dict = allocation_comparison.model_dump()
    
    # Remove any volatile fields (AllocationComparison has minimal fields)
    # The AllocationComparison DTO only has target_values, current_values, deltas
    stable_comparison = comp_dict.copy()
    
    # Normalize allocation dictionaries (sort by symbol)
    allocation_fields = ["target_values", "current_values", "deltas"]
    for field in allocation_fields:
        if field in stable_comparison and isinstance(stable_comparison[field], dict):
            # Sort by symbol and convert values to strings
            stable_comparison[field] = {
                symbol: str(value)
                for symbol, value in sorted(stable_comparison[field].items())
            }
    
    return stable_comparison


def generate_simple_plan_hash(plan_content: dict[str, Any]) -> str:
    """Generate simple hash from arbitrary plan content.
    
    Utility function for hashing plan-like structures when full DTOs aren't available.
    
    Args:
        plan_content: Dictionary containing plan data
        
    Returns:
        Hexadecimal hash string
    """
    try:
        # Sort keys and create deterministic JSON
        json_data = json.dumps(plan_content, sort_keys=True, separators=(",", ":"))
        hash_obj = hashlib.sha256(json_data.encode("utf-8"))
        return hash_obj.hexdigest()[:16]
    except Exception as e:
        logger.error(f"Failed to generate simple plan hash: {e}")
        # Return timestamp-based fallback
        import time
        fallback_data = f"{time.time()}_{len(str(plan_content))}"
        return hashlib.sha256(fallback_data.encode()).hexdigest()[:16]