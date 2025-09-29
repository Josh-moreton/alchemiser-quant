#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Extended hours execution strategy for simple bid/ask order placement.

Provides a dedicated execution strategy for extended hours trading that:
- Places buy orders at the ask price for immediate execution  
- Places sell orders at the bid price for immediate execution
- No repricing or repegging logic - just waits for fills
- Bypasses complex liquidity analysis during extended hours
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.types.market_data import QuoteModel

from .smart_execution_strategy import SmartOrderRequest, SmartOrderResult
from .smart_execution_strategy.models import LiquidityMetadata

logger = logging.getLogger(__name__)


class ExtendedHoursExecutionStrategy:
    """Simple execution strategy for extended hours trading.
    
    This strategy implements the user's requirements for extended hours:
    - Buys at ask price (immediate execution)
    - Sells at bid price (immediate execution) 
    - No repricing or repegging
    - Just waits for fills
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize extended hours execution strategy.
        
        Args:
            alpaca_manager: Alpaca broker manager for order placement and quotes
        """
        self.alpaca_manager = alpaca_manager

    def is_extended_hours_active(self) -> bool:
        """Check if extended hours trading is currently active.
        
        Returns:
            True if extended hours trading is enabled and should be used
        """
        return getattr(self.alpaca_manager, "extended_hours_enabled", False)

    async def place_extended_hours_order(self, request: SmartOrderRequest) -> SmartOrderResult:
        """Place order using extended hours strategy.
        
        Strategy:
        - BUY orders: placed at ask price for immediate execution
        - SELL orders: placed at bid price for immediate execution
        - No repricing or repegging - just wait for fill
        
        Args:
            request: Order request with symbol, side, quantity
            
        Returns:
            SmartOrderResult with execution details
        """
        logger.info(
            f"🌙 Placing extended hours order: {request.side} {request.quantity} {request.symbol}"
        )

        # Get current quote to determine bid/ask prices
        quote = await self._get_current_quote(request.symbol)
        if not quote:
            return SmartOrderResult(
                success=False,
                error_message=f"Unable to get quote for {request.symbol} during extended hours",
                execution_strategy="extended_hours_no_quote",
                placement_timestamp=datetime.now(UTC),
            )

        # Determine execution price based on side
        if request.side.upper() == "BUY":
            execution_price = Decimal(str(quote.ask_price))
            price_type = "ASK"
        else:  # SELL
            execution_price = Decimal(str(quote.bid_price))
            price_type = "BID"

        # Quantize to cents
        execution_price = execution_price.quantize(Decimal("0.01"))

        logger.info(
            f"🌙 Extended hours execution: {request.side} {request.symbol} at {price_type} ${execution_price}"
        )

        # Place limit order at the execution price
        try:
            result = await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                request.symbol,
                request.side.lower(),
                float(request.quantity),
                float(execution_price),
                "day",  # Use DAY time-in-force for extended hours
            )

            placement_time = datetime.now(UTC)

            if result.success and result.order_id:
                logger.info(
                    f"✅ Extended hours order placed: {result.order_id} for {request.symbol}"
                )
                # Create proper LiquidityMetadata for extended hours
                metadata: LiquidityMetadata = {
                    "method": "extended_hours_bid_ask",
                    "bid": quote.bid_price,
                    "ask": quote.ask_price,
                    "bid_price": quote.bid_price,
                    "ask_price": quote.ask_price,
                    "spread_percent": ((quote.ask_price - quote.bid_price) / quote.bid_price * 100) if quote.bid_price > 0 else 0.0,
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                    "used_fallback": False,
                    "strategy_recommendation": "extended_hours_simple",
                    "mid": (quote.bid_price + quote.ask_price) / 2,
                }

                return SmartOrderResult(
                    success=True,
                    order_id=result.order_id,
                    final_price=execution_price,
                    anchor_price=execution_price,
                    repegs_used=0,  # No repricing in extended hours strategy
                    execution_strategy="extended_hours_bid_ask",
                    placement_timestamp=placement_time,
                    metadata=metadata,
                )
            else:
                error_msg = result.error or "Extended hours order placement failed"
                logger.error(f"❌ Extended hours order failed: {error_msg}")
                return SmartOrderResult(
                    success=False,
                    error_message=error_msg,
                    execution_strategy="extended_hours_placement_failed",
                    placement_timestamp=placement_time,
                )

        except Exception as e:
            logger.error(f"❌ Exception during extended hours order placement: {e}")
            return SmartOrderResult(
                success=False,
                error_message=f"Extended hours execution error: {str(e)}",
                execution_strategy="extended_hours_exception",
                placement_timestamp=datetime.now(UTC),
            )

    async def _get_current_quote(self, symbol: str) -> QuoteModel | None:
        """Get current quote for the symbol.
        
        Args:
            symbol: Symbol to get quote for
            
        Returns:
            Current quote or None if unavailable
        """
        try:
            # Try to get quote from alpaca manager
            quote_data = await asyncio.to_thread(
                self.alpaca_manager.get_quote,
                symbol
            )
            
            if quote_data and hasattr(quote_data, 'bid_price') and hasattr(quote_data, 'ask_price'):
                # Convert to QuoteModel if needed
                if isinstance(quote_data, QuoteModel):
                    return quote_data
                else:
                    # Create QuoteModel from quote data
                    return QuoteModel(
                        symbol=symbol,
                        bid_price=float(quote_data.bid_price),
                        ask_price=float(quote_data.ask_price),
                        bid_size=getattr(quote_data, 'bid_size', 0.0),
                        ask_size=getattr(quote_data, 'ask_size', 0.0),
                        timestamp=datetime.now(UTC),
                    )
            
            logger.warning(f"Invalid quote data received for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None