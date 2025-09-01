"""Business Unit: shared | Status: current.

Signal DTOs for inter-module communication in The Alchemiser trading system.

This module provides typed DTOs for strategy signals, replacing loose dicts
and enabling type-safe communication between strategy and portfolio modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class StrategySignalDTO(BaseModel):
    """DTO for strategy signals passed between modules.
    
    Provides immutable, validated container for strategy signals with
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
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Signal data
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    action: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trading action")
    confidence: Decimal = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    
    # Optional signal metadata
    reasoning: str | None = Field(None, description="Human-readable signal reasoning")
    allocation_percentage: Decimal | None = Field(
        None, ge=0, le=100, description="Recommended allocation percentage"
    )
    target_price: Decimal | None = Field(None, gt=0, description="Target execution price")
    
    # Portfolio context (for multi-symbol strategies)
    portfolio_weights: dict[str, Decimal] | None = Field(
        None, description="Full portfolio weights if signal affects multiple symbols"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategySignalDTO:
        """Create DTO from dictionary with validation and type conversion.
        
        Args:
            data: Dictionary containing signal data
            
        Returns:
            Validated StrategySignalDTO instance
            
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
        for field in ["confidence", "allocation_percentage", "target_price"]:
            if field in processed_data and processed_data[field] is not None:
                processed_data[field] = Decimal(str(processed_data[field]))
                
        # Convert portfolio weights to Decimal if present
        if processed_data.get("portfolio_weights"):
            processed_data["portfolio_weights"] = {
                symbol: Decimal(str(weight))
                for symbol, weight in processed_data["portfolio_weights"].items()
            }
        
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
            elif field_name == "portfolio_weights" and field_value is not None:
                result[field_name] = {
                    symbol: str(weight) for symbol, weight in field_value.items()
                }
            else:
                result[field_name] = field_value
                
        return result