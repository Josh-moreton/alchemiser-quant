"""Business Unit: shared | Status: current.

Buying power verification service for handling account state synchronization.

This service addresses the timing issue where broker account state (buying power)
hasn't been updated yet even though orders have settled. It provides retry logic
with exponential backoff to wait for account state synchronization.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class BuyingPowerService:
    """Service for verifying buying power availability with retry logic."""

    def __init__(self, broker_manager: AlpacaManager) -> None:
        """Initialize buying power service.
        
        Args:
            broker_manager: Broker manager for account operations

        """
        self.broker_manager = broker_manager

    def verify_buying_power_available(
        self, 
        expected_amount: Decimal, 
        max_retries: int = 5,
        initial_wait: float = 1.0
    ) -> tuple[bool, Decimal]:
        """Verify that buying power is actually available in account with retry logic.
        
        This method addresses the timing issue where the broker's account buying_power
        field hasn't been updated yet even though sell orders have settled.
        
        Args:
            expected_amount: Minimum buying power expected to be available
            max_retries: Maximum number of retry attempts
            initial_wait: Initial wait time in seconds (doubles each retry)
            
        Returns:
            Tuple of (is_available, actual_buying_power)

        """
        logger.info(f"💰 Verifying ${expected_amount} buying power availability (with retries)")
        
        for attempt in range(max_retries):
            try:
                # Force fresh account data retrieval
                buying_power = self.broker_manager.get_buying_power()
                if buying_power is None:
                    logger.warning(f"Could not retrieve buying power on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = initial_wait * (2 ** attempt)
                        logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                    continue
                
                actual_buying_power = Decimal(str(buying_power))
                
                logger.info(
                    f"💰 Attempt {attempt + 1}: Actual buying power ${actual_buying_power}, "
                    f"needed ${expected_amount}"
                )
                
                if actual_buying_power >= expected_amount:
                    logger.info(
                        f"✅ Buying power verified: ${actual_buying_power} >= ${expected_amount}"
                    )
                    return True, actual_buying_power
                
                # Log the shortfall
                shortfall = expected_amount - actual_buying_power
                logger.warning(
                    f"⚠️ Buying power shortfall: ${shortfall} "
                    f"(have ${actual_buying_power}, need ${expected_amount})"
                )
                
                # Wait before next attempt (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = initial_wait * (2 ** attempt)
                    logger.info(
                        f"⏳ Waiting {wait_time:.1f}s for account state to update..."
                    )
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error verifying buying power on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = initial_wait * (2 ** attempt)
                    time.sleep(wait_time)
        
        # Final check - get the last known buying power
        try:
            final_buying_power_raw = self.broker_manager.get_buying_power()
            final_buying_power = Decimal(str(final_buying_power_raw)) if final_buying_power_raw else Decimal("0")
        except Exception:
            final_buying_power = Decimal("0")
            
        logger.error(
            f"❌ Buying power verification failed after {max_retries} attempts. "
            f"Final buying power: ${final_buying_power}, needed: ${expected_amount}"
        )
        return False, final_buying_power

    def force_account_refresh(self) -> bool:
        """Force a fresh account data retrieval from the broker.
        
        This can help when account state appears stale after order settlements.
        
        Returns:
            True if refresh successful, False otherwise

        """
        try:
            logger.info("🔄 Forcing account state refresh...")
            buying_power = self.broker_manager.get_buying_power()
            portfolio_value = self.broker_manager.get_portfolio_value()
            
            if buying_power is not None and portfolio_value is not None:
                logger.info(
                    f"✅ Account refreshed - Buying power: ${buying_power:,.2f}, "
                    f"Portfolio value: ${portfolio_value:,.2f}"
                )
                return True
            logger.warning("⚠️ Account refresh returned incomplete data")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to refresh account state: {e}")
            return False

    def estimate_order_cost(self, symbol: str, quantity: Decimal, buffer_pct: float = 5.0) -> Decimal | None:
        """Estimate the cost of a buy order with a price buffer.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage (default 5%)
            
        Returns:
            Estimated cost with buffer, or None if price unavailable

        """
        try:
            current_price = self.broker_manager.get_current_price(symbol)
            if current_price:
                estimated_cost = quantity * Decimal(str(current_price))
                buffer_multiplier = Decimal(str(1 + buffer_pct / 100))
                return estimated_cost * buffer_multiplier
            return None
        except Exception as e:
            logger.error(f"Failed to estimate order cost for {symbol}: {e}")
            return None

    def check_sufficient_buying_power(
        self, 
        symbol: str, 
        quantity: Decimal, 
        buffer_pct: float = 5.0
    ) -> tuple[bool, Decimal, Decimal | None]:
        """Check if there's sufficient buying power for a buy order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage
            
        Returns:
            Tuple of (is_sufficient, current_buying_power, estimated_cost)

        """
        try:
            estimated_cost = self.estimate_order_cost(symbol, quantity, buffer_pct)
            buying_power = self.broker_manager.get_buying_power()
            
            if buying_power is None or estimated_cost is None:
                return False, Decimal("0"), estimated_cost
                
            current_bp = Decimal(str(buying_power))
            is_sufficient = current_bp >= estimated_cost
            
            logger.info(
                f"💰 Buying power check for {symbol}: "
                f"estimated cost ${estimated_cost} (with {buffer_pct}% buffer), "
                f"available ${current_bp}, sufficient: {is_sufficient}"
            )
            
            return is_sufficient, current_bp, estimated_cost
            
        except Exception as e:
            logger.error(f"Error checking buying power for {symbol}: {e}")
            return False, Decimal("0"), None