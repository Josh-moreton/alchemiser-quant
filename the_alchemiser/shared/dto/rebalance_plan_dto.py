"""Business Unit: shared | Status: current.

Rebalance plan DTOs for inter-module communication in The Alchemiser trading system.

This module provides typed DTOs for portfolio rebalancing plans, enabling type-safe
communication between portfolio and execution modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class RebalancePlanDTO(BaseModel):
    """DTO for portfolio rebalancing plans passed between modules.
    
    Provides immutable, validated container for rebalancing instructions with
    required correlation tracking fields and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(..., min_length=1, description="Causation chain identifier")
    timestamp: datetime = Field(..., description="Plan generation timestamp")

    # Rebalancing instruction data
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    trade_direction: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trade direction")
    trade_amount: Decimal = Field(..., description="Trade amount (signed, negative for sells)")
    trade_amount_abs: Decimal = Field(..., ge=0, description="Absolute trade amount")
    
    # Portfolio context
    current_weight: Decimal = Field(..., ge=0, le=1, description="Current portfolio weight")
    target_weight: Decimal = Field(..., ge=0, le=1, description="Target portfolio weight")
    weight_diff: Decimal = Field(..., description="Weight difference (target - current)")
    weight_change_bps: int = Field(..., description="Weight change in basis points")
    
    # Valuation context
    current_value: Decimal = Field(..., ge=0, description="Current position value")
    target_value: Decimal = Field(..., ge=0, description="Target position value")
    
    # Plan metadata
    needs_rebalance: bool = Field(..., description="Whether rebalancing is needed")
    priority: int = Field(default=0, description="Execution priority (higher = more urgent)")
    estimated_cost: Decimal | None = Field(None, ge=0, description="Estimated transaction cost")
    
    # Risk and constraints
    max_order_size: Decimal | None = Field(None, gt=0, description="Maximum single order size")
    min_order_size: Decimal | None = Field(None, gt=0, description="Minimum order size threshold")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RebalancePlanDTO:
        """Create DTO from dictionary with validation and type conversion.
        
        Args:
            data: Dictionary containing rebalance plan data
            
        Returns:
            Validated RebalancePlanDTO instance
            
        Raises:
            ValueError: If required fields missing or invalid

        """
        # Ensure required correlation fields with defaults if not provided
        processed_data = data.copy()
        
        if "correlation_id" not in processed_data:
            processed_data["correlation_id"] = str(uuid4())
            
        if "causation_id" not in processed_data:
            processed_data["causation_id"] = processed_data["correlation_id"]
            
        if "timestamp" not in processed_data:
            processed_data["timestamp"] = datetime.now(UTC)
        elif isinstance(processed_data["timestamp"], str):
            processed_data["timestamp"] = datetime.fromisoformat(processed_data["timestamp"])
            
        # Convert numeric fields to Decimal
        decimal_fields = [
            "trade_amount", "trade_amount_abs", "current_weight", "target_weight",
            "weight_diff", "current_value", "target_value", "estimated_cost",
            "max_order_size", "min_order_size"
        ]
        
        for field in decimal_fields:
            if field in processed_data and processed_data[field] is not None:
                processed_data[field] = Decimal(str(processed_data[field]))
        
        return cls(**processed_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.
        
        Returns:
            Dictionary representation with Decimals converted to strings

        """
        result: dict[str, Any] = {}
        
        for field_name, field_value in self.model_dump().items():
            if isinstance(field_value, Decimal):
                result[field_name] = str(field_value)
            elif field_name == "timestamp" and isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat()
            else:
                result[field_name] = field_value
                
        return result

    @property
    def requires_execution(self) -> bool:
        """Check if this plan requires actual execution."""
        return self.needs_rebalance and self.trade_direction != "HOLD"

    @property
    def is_buy_order(self) -> bool:
        """Check if this plan represents a buy order."""
        return self.trade_direction == "BUY"

    @property
    def is_sell_order(self) -> bool:
        """Check if this plan represents a sell order."""
        return self.trade_direction == "SELL"