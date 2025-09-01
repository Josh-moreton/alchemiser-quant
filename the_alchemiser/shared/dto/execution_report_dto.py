"""Business Unit: shared | Status: current.

Execution report DTOs for inter-module communication in The Alchemiser trading system.

This module provides typed DTOs for trade execution reports, enabling type-safe
communication from execution module back to portfolio and strategy modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionReportDTO(BaseModel):
    """DTO for trade execution reports passed between modules.
    
    Provides immutable, validated container for execution results with
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
    timestamp: datetime = Field(..., description="Execution completion timestamp")

    # Execution identification
    execution_id: str = Field(..., min_length=1, description="Unique execution identifier")
    order_id: str | None = Field(None, description="Broker order ID if available")
    
    # Trade details
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    side: Literal["BUY", "SELL"] = Field(..., description="Trade side")
    status: Literal["SUCCESS", "FAILED", "PARTIAL", "PENDING"] = Field(
        ..., description="Execution status"
    )
    
    # Quantities and pricing
    requested_quantity: Decimal = Field(..., gt=0, description="Originally requested quantity")
    executed_quantity: Decimal = Field(..., ge=0, description="Actually executed quantity")
    average_price: Decimal | None = Field(None, gt=0, description="Average execution price")
    
    # Financial impact
    total_value: Decimal = Field(..., ge=0, description="Total trade value")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="Commission paid")
    fees: Decimal = Field(default=Decimal("0"), ge=0, description="Additional fees")
    total_cost: Decimal = Field(..., ge=0, description="Total cost including fees")
    
    # Execution quality metrics
    slippage: Decimal | None = Field(None, description="Price slippage from expected")
    execution_time_ms: int | None = Field(None, ge=0, description="Execution time in milliseconds")
    
    # Error handling
    error_code: str | None = Field(None, description="Error code if execution failed")
    error_message: str | None = Field(None, description="Human-readable error message")
    
    # Market context
    market_price_at_execution: Decimal | None = Field(
        None, gt=0, description="Market price at time of execution"
    )
    
    # Additional metadata
    broker: str | None = Field(None, description="Executing broker identifier")
    venue: str | None = Field(None, description="Execution venue")
    strategy_context: str | None = Field(None, description="Originating strategy context")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionReportDTO:
        """Create DTO from dictionary with validation and type conversion.
        
        Args:
            data: Dictionary containing execution report data
            
        Returns:
            Validated ExecutionReportDTO instance
            
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
            
        # Ensure execution_id is set
        if "execution_id" not in processed_data:
            processed_data["execution_id"] = f"exec_{uuid4()}"
            
        # Convert numeric fields to Decimal
        decimal_fields = [
            "requested_quantity", "executed_quantity", "average_price", "total_value",
            "commission", "fees", "total_cost", "slippage", "market_price_at_execution"
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
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == "SUCCESS"

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "FAILED"

    @property
    def is_partial(self) -> bool:
        """Check if execution was partial."""
        return self.status == "PARTIAL"

    @property
    def is_pending(self) -> bool:
        """Check if execution is still pending."""
        return self.status == "PENDING"

    @property
    def fill_ratio(self) -> Decimal:
        """Calculate fill ratio (executed / requested)."""
        if self.requested_quantity == 0:
            return Decimal("0")
        return self.executed_quantity / self.requested_quantity

    @property
    def net_proceeds(self) -> Decimal:
        """Calculate net proceeds (value - all costs)."""
        return self.total_value - self.commission - self.fees