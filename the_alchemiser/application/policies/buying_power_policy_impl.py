"""
Buying Power Policy Implementation

Concrete implementation of BuyingPowerPolicy that handles buying power validation.
Extracts logic from PositionManager and ensures BuyingPowerError is raised properly.
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
from the_alchemiser.services.errors.exceptions import BuyingPowerError, DataProviderError

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class BuyingPowerPolicyImpl:
    """
    Concrete implementation of buying power policy.
    
    Handles validation of orders against available buying power and raises
    BuyingPowerError for insufficient funds (no string parsing heuristics).
    """
    
    def __init__(self, trading_client: Any, data_provider: Any) -> None:
        """
        Initialize the buying power policy.
        
        Args:
            trading_client: Trading client for account data
            data_provider: Data provider for price information
        """
        self.trading_client = trading_client
        self.data_provider = data_provider
        self._policy_name = "BuyingPowerPolicy"
    
    def validate_and_adjust(
        self, 
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Validate order against available buying power.
        
        For buy orders, checks if order value is within buying power limits.
        Raises BuyingPowerError for insufficient funds.
        
        Args:
            order_request: The original order request to validate
            
        Returns:
            AdjustedOrderRequestDTO with buying power validation results
            
        Raises:
            BuyingPowerError: If insufficient buying power for the order
        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating buying power for {order_request.symbol}",
            policy=self.policy_name,
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=str(order_request.quantity),
        )
        
        warnings: list[PolicyWarningDTO] = []
        
        # Only validate buying power for buy orders
        if order_request.side.lower() == "buy":
            try:
                # Validate buying power - this will raise BuyingPowerError if insufficient
                self.validate_buying_power(
                    order_request.symbol,
                    float(order_request.quantity),
                    float(order_request.limit_price) if order_request.limit_price else None
                )
                
                log_with_context(
                    logger,
                    logging.INFO,
                    f"Buying power validation passed",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol,
                    quantity=str(order_request.quantity),
                )
                
            except BuyingPowerError as e:
                # Log the buying power rejection with structured data
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Buy order rejected due to insufficient buying power",
                    policy=self.policy_name,
                    action="reject",
                    symbol=order_request.symbol,
                    quantity=str(order_request.quantity),
                    required_amount=str(e.required_amount) if e.required_amount else "unknown",
                    available_amount=str(e.available_amount) if e.available_amount else "unknown",
                    shortfall=str(e.shortfall) if e.shortfall else "unknown",
                )
                
                return AdjustedOrderRequestDTO(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    order_type=order_request.order_type,
                    time_in_force=order_request.time_in_force,
                    limit_price=order_request.limit_price,
                    client_order_id=order_request.client_order_id,
                    is_approved=False,
                    rejection_reason=str(e),
                    total_risk_score=Decimal("0"),
                )
            
            except Exception as e:
                # For unexpected errors during buying power validation, log and continue
                # This matches the original behavior of returning warnings instead of failing
                warning_msg = f"Unable to validate buying power for {order_request.symbol}: {e}"
                
                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="allow",
                    message=warning_msg,
                    original_value=str(order_request.quantity),
                    adjusted_value=str(order_request.quantity),
                    risk_level="medium",
                )
                warnings.append(warning)
                
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Buying power validation failed but allowing order to proceed",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol,
                    error=str(e),
                    error_type=type(e).__name__,
                )
        
        # Approve the order (sell orders or buy orders that passed validation)
        log_with_context(
            logger,
            logging.INFO,
            f"Buying power policy approved order",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol,
            side=order_request.side,
        )
        
        return AdjustedOrderRequestDTO(
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=order_request.quantity,
            order_type=order_request.order_type,
            time_in_force=order_request.time_in_force,
            limit_price=order_request.limit_price,
            client_order_id=order_request.client_order_id,
            is_approved=True,
            warnings=warnings,
            total_risk_score=Decimal("0"),
        )
    
    def get_available_buying_power(self) -> float:
        """
        Get current available buying power.
        
        Returns:
            Available buying power amount
        """
        try:
            account = self.trading_client.get_account()
            return float(getattr(account, "buying_power", 0) or 0)
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to get buying power: {e}",
                policy=self.policy_name,
                error=str(e),
            )
            raise BuyingPowerError(
                f"Unable to retrieve buying power: {e}",
                required_amount=None,
                available_amount=None,
            ) from e
    
    def estimate_order_value(
        self, 
        symbol: str, 
        quantity: float, 
        order_type: str = "market"
    ) -> float:
        """
        Estimate the total value of an order.
        
        Args:
            symbol: Stock symbol
            quantity: Order quantity
            order_type: Type of order ("market" or "limit")
            
        Returns:
            Estimated order value in dollars
        """
        try:
            current_price = self.data_provider.get_current_price(symbol)
            if current_price is None or current_price <= 0:
                raise DataProviderError(f"Invalid current price for {symbol}: {current_price}")
            
            return float(current_price) * quantity
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to estimate order value for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                quantity=str(quantity),
                error=str(e),
            )
            raise DataProviderError(f"Unable to estimate order value for {symbol}: {e}") from e
    
    def validate_buying_power(
        self, 
        symbol: str, 
        quantity: float, 
        estimated_price: float | None = None
    ) -> bool:
        """
        Validate if sufficient buying power exists for an order.
        
        Args:
            symbol: Stock symbol
            quantity: Order quantity
            estimated_price: Price estimate (if None, fetches current price)
            
        Returns:
            True if sufficient buying power exists
            
        Raises:
            BuyingPowerError: If insufficient buying power
        """
        try:
            buying_power = self.get_available_buying_power()
            
            # Get price for order value calculation
            if estimated_price is None:
                current_price = self.data_provider.get_current_price(symbol)
                if current_price is None or current_price <= 0:
                    raise DataProviderError(f"Invalid current price for {symbol}: {current_price}")
                price_value = float(current_price)
            else:
                price_value = estimated_price
            
            order_value = quantity * price_value
            
            if order_value > buying_power:
                shortfall = order_value - buying_power
                raise BuyingPowerError(
                    f"Order value ${order_value:.2f} exceeds buying power ${buying_power:.2f} for {symbol}",
                    symbol=symbol,
                    required_amount=order_value,
                    available_amount=buying_power,
                    shortfall=shortfall,
                )
            
            return True
            
        except BuyingPowerError:
            # Re-raise BuyingPowerError as-is
            raise
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Error validating buying power for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                quantity=str(quantity),
                error=str(e),
                error_type=type(e).__name__,
            )
            # Convert any other errors to BuyingPowerError for consistency
            raise BuyingPowerError(
                f"Unable to validate buying power for {symbol}: {e}",
                symbol=symbol,
            ) from e
    
    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name