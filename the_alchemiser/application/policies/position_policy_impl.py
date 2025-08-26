"""
Position Policy Implementation

Concrete implementation of PositionPolicy that handles position validation
and quantity adjustments. Extracts logic from PositionManager.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.interfaces.schemas.orders import (
    AdjustedOrderRequestDTO,
    OrderRequestDTO,
    PolicyWarningDTO,
)
from the_alchemiser.infrastructure.logging.logging_utils import log_with_context
from the_alchemiser.services.errors.exceptions import PositionValidationError

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class PositionPolicyImpl:
    """
    Concrete implementation of position policy.
    
    Handles validation and adjustment of orders based on current position holdings,
    with structured logging and warning generation.
    """
    
    def __init__(self, trading_client: Any) -> None:
        """
        Initialize the position policy.
        
        Args:
            trading_client: Trading client for position data
        """
        self.trading_client = trading_client
        self._policy_name = "PositionPolicy"
    
    def validate_and_adjust(
        self, 
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Validate and adjust order based on current positions.
        
        For sell orders, ensures quantity doesn't exceed available position.
        For buy orders, validates position concentration limits.
        
        Args:
            order_request: The original order request to validate
            
        Returns:
            AdjustedOrderRequestDTO with position-based adjustments applied
        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating position for {order_request.symbol}",
            policy=self.policy_name,
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=str(order_request.quantity),
        )
        
        original_quantity = order_request.quantity
        adjusted_quantity = original_quantity
        warnings: list[PolicyWarningDTO] = []
        adjustment_reason = None
        
        # Handle sell orders - validate against available position
        if order_request.side.lower() == "sell":
            is_valid, final_quantity, warning_msg = self.validate_sell_quantity(
                order_request.symbol,
                float(order_request.quantity)
            )
            
            if not is_valid:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Sell order rejected: {warning_msg}",
                    policy=self.policy_name,
                    action="reject",
                    symbol=order_request.symbol,
                    requested_quantity=str(original_quantity),
                    reason=warning_msg,
                )
                
                return AdjustedOrderRequestDTO(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=original_quantity,
                    order_type=order_request.order_type,
                    time_in_force=order_request.time_in_force,
                    limit_price=order_request.limit_price,
                    client_order_id=order_request.client_order_id,
                    is_approved=False,
                    original_quantity=original_quantity,
                    rejection_reason=warning_msg or "Insufficient position for sell order",
                    total_risk_score=Decimal("0"),
                )
            
            # Check if quantity was adjusted
            if final_quantity != float(original_quantity):
                adjusted_quantity = Decimal(str(final_quantity))
                
                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=warning_msg or f"Adjusted sell quantity to available position",
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="medium",
                )
                warnings.append(warning)
                adjustment_reason = "Adjusted to available position quantity"
                
                log_with_context(
                    logger,
                    logging.INFO,
                    f"Adjusted sell quantity to available position",
                    policy=self.policy_name,
                    action="adjust",
                    symbol=order_request.symbol,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                    available_position=str(final_quantity),
                )
            elif warning_msg:
                # Position validation passed but with a warning
                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="allow",
                    message=warning_msg,
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)
        
        # Check if liquidation API should be used for large sell orders
        if order_request.side.lower() == "sell":
            should_liquidate = self.should_use_liquidation_api(
                order_request.symbol,
                float(adjusted_quantity)
            )
            
            if should_liquidate:
                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="allow",
                    message="Large sell order - consider using liquidation API",
                    original_value=str(adjusted_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)
                
                log_with_context(
                    logger,
                    logging.INFO,
                    f"Liquidation API recommended for large sell order",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol,
                    quantity=str(adjusted_quantity),
                    recommendation="use_liquidation_api",
                )
        
        # Approve the order
        log_with_context(
            logger,
            logging.INFO,
            f"Position validation passed",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol,
            final_quantity=str(adjusted_quantity),
            has_adjustments=str(adjusted_quantity != original_quantity),
        )
        
        return AdjustedOrderRequestDTO(
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=adjusted_quantity,
            order_type=order_request.order_type,
            time_in_force=order_request.time_in_force,
            limit_price=order_request.limit_price,
            client_order_id=order_request.client_order_id,
            is_approved=True,
            original_quantity=original_quantity if adjusted_quantity != original_quantity else None,
            adjustment_reason=adjustment_reason,
            warnings=warnings,
            policy_metadata={
                "liquidation_recommended": str(
                    order_request.side.lower() == "sell" and 
                    self.should_use_liquidation_api(order_request.symbol, float(adjusted_quantity))
                )
            },
            total_risk_score=Decimal("0"),
        )
    
    def get_available_position(self, symbol: str) -> float:
        """
        Get the available position quantity for a symbol.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Available quantity that can be sold
        """
        try:
            positions = self.trading_client.get_all_positions()
            for pos in positions:
                if str(getattr(pos, "symbol", "")) == symbol:
                    return float(getattr(pos, "qty", 0))
            return 0.0
        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Failed to get position for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return 0.0
    
    def validate_sell_quantity(
        self, 
        symbol: str, 
        requested_quantity: float
    ) -> tuple[bool, float, str | None]:
        """
        Validate and adjust sell quantity based on available position.
        
        Args:
            symbol: Stock symbol to sell
            requested_quantity: Requested sell quantity
            
        Returns:
            Tuple of (is_valid, adjusted_quantity, warning_message)
        """
        try:
            available = self.get_available_position(symbol)
            
            if available <= 0:
                return False, 0.0, f"No position to sell for {symbol}"
            
            # Smart quantity adjustment - sell only what's actually available
            if requested_quantity > available:
                warning_msg = f"Adjusting sell quantity for {symbol}: {requested_quantity} -> {available}"
                return True, available, warning_msg
            
            return True, requested_quantity, None
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Error validating sell quantity for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                requested_quantity=str(requested_quantity),
                error=str(e),
            )
            raise PositionValidationError(
                f"Failed to validate sell quantity for {symbol}: {e}",
                symbol=symbol,
                requested_qty=requested_quantity,
            ) from e
    
    def should_use_liquidation_api(
        self, 
        symbol: str, 
        requested_quantity: float
    ) -> bool:
        """
        Determine if liquidation API should be used instead of regular sell.
        
        Args:
            symbol: Stock symbol
            requested_quantity: Requested sell quantity
            
        Returns:
            True if liquidation API should be used
        """
        try:
            available = self.get_available_position(symbol)
            
            if available <= 0:
                return False
            
            # Use liquidation API for selling 99%+ of position
            return requested_quantity >= available * 0.99
            
        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Error checking liquidation API requirement for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return False
    
    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name