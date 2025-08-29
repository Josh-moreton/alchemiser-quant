"""Business Unit: strategy & signal generation; Status: current.

Strategy Signal Contract V1 for cross-context communication.

This module provides the versioned application contract for strategy signals,
enabling clean communication between Strategy and Portfolio contexts without
domain leakage.

Example Usage:
    # Creating a signal contract
    signal = SignalContractV1(
        correlation_id=uuid4(),
        symbol=Symbol("AAPL"),
        action=ActionType.BUY,
        target_allocation=Percentage(Decimal("0.15")),
        confidence=0.85,
        reasoning="Strong bullish momentum detected"
    )
    
    # Accessing contract data
    print(f"Signal for {signal.symbol}: {signal.action}")
    print(f"Confidence: {signal.confidence}")
"""

from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from the_alchemiser.domain.shared_kernel import ActionType, Percentage
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

from ._envelope import EnvelopeV1


class SignalContractV1(EnvelopeV1):
    """Version 1 contract for strategy signals crossing context boundaries.
    
    This contract enables Strategy -> Portfolio communication without exposing
    internal domain objects. All fields use primitives or shared kernel types.
    
    Attributes:
        symbol: Stock/ETF symbol from shared kernel
        action: Trading action (BUY/SELL/HOLD) from shared kernel
        target_allocation: Target portfolio percentage from shared kernel  
        confidence: Signal confidence level (0.0-1.0) - uses float for non-financial data
        reasoning: Optional human-readable explanation for the signal

    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    symbol: Symbol = Field(..., description="Stock/ETF symbol")
    action: ActionType = Field(..., description="Trading action: BUY/SELL/HOLD")
    target_allocation: Percentage = Field(..., description="Target portfolio allocation (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence level (0.0-1.0)")
    reasoning: str | None = Field(None, description="Optional reasoning for the signal")
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence_precision(cls, v: float) -> float:
        """Validate confidence is within valid range for non-financial float usage."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


def signal_from_domain(
    domain_signal: object,  # StrategySignal from domain - using object to avoid domain import
    correlation_id: UUID,
    causation_id: UUID | None = None,
) -> SignalContractV1:
    """Map a domain StrategySignal to a SignalContractV1.
    
    Args:
        domain_signal: Domain StrategySignal object
        correlation_id: Root correlation ID for message tracing
        causation_id: Optional ID of the message that caused this signal
        
    Returns:
        SignalContractV1 ready for cross-context communication
        
    Note:
        This function intentionally uses object type to avoid importing domain
        objects into the application layer. The actual domain object should have
        the expected attributes: symbol, action, target_allocation, confidence, reasoning.

    """
    # Convert confidence from domain Confidence value object to float
    confidence_value = float(domain_signal.confidence.value)  # type: ignore[attr-defined]
    
    # Map action string to ActionType enum
    action_map = {"BUY": ActionType.BUY, "SELL": ActionType.SELL, "HOLD": ActionType.HOLD}
    action = action_map[domain_signal.action]  # type: ignore[attr-defined]
    
    return SignalContractV1(
        correlation_id=correlation_id,
        causation_id=causation_id,
        symbol=domain_signal.symbol,  # type: ignore[attr-defined]
        action=action,
        target_allocation=domain_signal.target_allocation,  # type: ignore[attr-defined]
        confidence=confidence_value,
        reasoning=domain_signal.reasoning,  # type: ignore[attr-defined]
    )


# Note: to_domain() method intentionally omitted to avoid cross-context domain coupling.
# Portfolio context should translate contract data to its own domain representations
# rather than reconstructing Strategy domain objects.