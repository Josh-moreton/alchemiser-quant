"""
Risk Policy Interface

Handles risk assessment and limits for order requests.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO, AdjustedOrderRequestDTO


class RiskPolicy(Protocol):
    """
    Policy for assessing and managing risk in order requests.
    
    This policy evaluates orders against risk thresholds and can reject
    or adjust orders that exceed acceptable risk levels.
    """
    
    def validate_and_adjust(
        self, 
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Assess risk and validate order against risk limits.
        
        Args:
            order_request: The original order request to validate
            
        Returns:
            AdjustedOrderRequestDTO with risk assessment and any adjustments
        """
        ...
    
    def calculate_risk_score(
        self, 
        symbol: str, 
        quantity: float, 
        order_type: str = "market"
    ) -> Decimal:
        """
        Calculate a risk score for an order.
        
        Args:
            symbol: Stock symbol
            quantity: Order quantity
            order_type: Type of order
            
        Returns:
            Risk score (higher values indicate higher risk)
        """
        ...
    
    def assess_position_concentration(
        self, 
        symbol: str, 
        additional_quantity: float
    ) -> tuple[bool, str | None]:
        """
        Assess if adding quantity would create excessive concentration.
        
        Args:
            symbol: Stock symbol
            additional_quantity: Additional quantity being added
            
        Returns:
            Tuple of (is_acceptable, warning_message)
        """
        ...
    
    def validate_order_size(
        self, 
        symbol: str, 
        quantity: float, 
        portfolio_value: float
    ) -> tuple[bool, str | None]:
        """
        Validate order size against portfolio limits.
        
        Args:
            symbol: Stock symbol
            quantity: Order quantity  
            portfolio_value: Current portfolio value
            
        Returns:
            Tuple of (is_acceptable, warning_message)
        """
        ...
    
    @property
    def max_risk_score(self) -> Decimal:
        """Get the maximum acceptable risk score."""
        ...
    
    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...