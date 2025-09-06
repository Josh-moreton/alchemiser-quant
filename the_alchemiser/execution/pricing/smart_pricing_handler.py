#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Smart Pricing Handler.

This module provides intelligent pricing strategies based on market conditions,
bid/ask spreads, and order aggressiveness settings.
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.shared.logging.logging_utils import get_logger, log_error_with_context
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide
from the_alchemiser.shared.types.exceptions import DataProviderError


class SmartPricingHandler:
    """Handles intelligent price calculation for limit orders."""

    def __init__(self, data_provider: Any) -> None:
        """Initialize with data provider for market data."""
        self.data_provider = data_provider

    def get_smart_limit_price(
        self, symbol: str, side: BrokerOrderSide, aggressiveness: float = 0.5
    ) -> float | None:
        """Get a smart limit price based on current bid/ask.

        Args:
            symbol: Stock symbol
            side: BrokerOrderSide.BUY or BrokerOrderSide.SELL
            aggressiveness: 0.0 = most conservative, 1.0 = most aggressive (market price)

        Returns:
            Calculated limit price, or None if data unavailable

        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)

            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None

            if side == BrokerOrderSide.BUY:
                # For buying: bid = conservative, ask = aggressive
                price = bid + (ask - bid) * aggressiveness
            else:
                # For selling: ask = conservative, bid = aggressive
                price = ask - (ask - bid) * aggressiveness

            return round(float(price), 2)

        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Failed to get smart limit price for {symbol}: {e}"),
                "smart_pricing",
                function="get_smart_limit_price",
                symbol=symbol,
                side=side.name,
                aggressiveness=aggressiveness,
                error_type=type(e).__name__,
            )
            logging.error(f"Error getting smart limit price for {symbol}: {e}")
            return None
        except Exception as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Unexpected error getting smart limit price for {symbol}: {e}"),
                "smart_pricing",
                function="get_smart_limit_price",
                symbol=symbol,
                side=side.name,
                aggressiveness=aggressiveness,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error getting smart limit price for {symbol}: {e}")
            return None

    def get_progressive_pricing(
        self, symbol: str, side: BrokerOrderSide, step: int = 1, total_steps: int = 4
    ) -> float | None:
        """Get progressive pricing for multi-step limit order strategies.

        Args:
            symbol: Stock symbol
            side: BrokerOrderSide.BUY or BrokerOrderSide.SELL
            step: Current step (1-based)
            total_steps: Total number of steps

        Returns:
            Calculated price for this step, or None if data unavailable

        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)

            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None

            midpoint = (bid + ask) / 2.0
            spread = ask - bid

            # Calculate step percentage (0% to 30% through spread)
            step_percentage = min((step - 1) / max(total_steps - 1, 1) * 0.3, 0.3)

            if side == BrokerOrderSide.BUY:
                # Step from midpoint toward ask
                price = midpoint + (spread / 2 * step_percentage)
            else:
                # Step from midpoint toward bid
                price = midpoint - (spread / 2 * step_percentage)

            return round(float(price), 2)

        except Exception as e:
            logging.error(f"Error getting progressive price for {symbol}: {e}")
            return None

    def get_aggressive_sell_price(self, symbol: str, aggressiveness: float = 0.85) -> float | None:
        """Get aggressive sell pricing for quick liquidation (favors speed over price).

        Args:
            symbol: Stock symbol
            aggressiveness: How aggressive (0.85 = 85% toward bid from ask)

        Returns:
            Calculated aggressive sell price, or None if data unavailable

        """
        return self.get_smart_limit_price(symbol, BrokerOrderSide.SELL, aggressiveness)

    def get_conservative_buy_price(self, symbol: str, aggressiveness: float = 0.75) -> float | None:
        """Get conservative buy pricing for better fill prices (favors price over speed).

        Args:
            symbol: Stock symbol
            aggressiveness: How aggressive (0.75 = 75% toward ask from bid)

        Returns:
            Calculated conservative buy price, or None if data unavailable

        """
        return self.get_smart_limit_price(symbol, BrokerOrderSide.BUY, aggressiveness)

    def get_aggressive_marketable_limit(
        self, symbol: str, side: BrokerOrderSide, bid: float, ask: float
    ) -> float:
        """Calculate aggressive marketable limit prices per better orders spec.

        This is the "pro equivalent of hitting the market but with a seatbelt":
        - BUY: ask + 1 tick (ask + 0.01)
        - SELL: bid - 1 tick (bid - 0.01)

        Args:
            symbol: Stock symbol
            side: BUY or SELL
            bid: Current bid price
            ask: Current ask price

        Returns:
            Aggressive limit price that should execute quickly

        """
        if side == BrokerOrderSide.BUY:
            # Buy at ask + 1 cent (aggressive but protected)
            return round(ask + 0.01, 2)
        # Sell at bid - 1 cent (aggressive but protected)
        return round(max(bid - 0.01, 0.01), 2)  # Ensure positive price

    def validate_aggressive_limit(
        self,
        limit_price: float,
        market_price: float,
        side: BrokerOrderSide,
        max_slippage_bps: float = 20,
    ) -> bool:
        """Validate that aggressive limit price is within acceptable slippage bounds.

        For leveraged ETFs, opportunity cost often outweighs small slippage costs.
        Default 20 bps tolerance is reasonable for 3x ETFs.
        """
        if market_price <= 0:
            return True  # Can't validate without market price

        slippage = abs(limit_price - market_price) / market_price * 10000  # bps

        if slippage > max_slippage_bps:
            logging.warning(
                f"Aggressive limit slippage {slippage:.1f}bps exceeds {max_slippage_bps}bps limit"
            )
            return False

        return True

    def get_liquidity_anchored_price(
        self, 
        symbol: str, 
        side: BrokerOrderSide, 
        spread_quality: str = "normal",
        urgency: str = "normal"
    ) -> float | None:
        """Get liquidity-anchored price that places orders at or just inside bid/ask.
        
        This implements the core principle: "Anchor to Liquidity, Not Hope"
        Orders are placed at or just inside the best bid/ask, not arbitrarily far from market.
        
        Args:
            symbol: Stock symbol
            side: BrokerOrderSide.BUY or BrokerOrderSide.SELL
            spread_quality: "tight", "normal", or "wide" 
            urgency: "low", "normal", "high", or "urgent"
            
        Returns:
            Price anchored to current liquidity, or None if data unavailable
        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)

            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None
                
            # Calculate spread metrics
            spread = ask - bid
            midpoint = (bid + ask) / 2.0
            spread_bps = (spread / midpoint) * 10000 if midpoint > 0 else 0
            
            # Determine how far inside the spread to place order based on spread quality
            if spread_quality == "tight":  # ≤ 3¢ or ≤ 10 bps
                # Tight spreads: be more aggressive to ensure fills
                inside_factor = 0.8 if urgency in ["high", "urgent"] else 0.6
            elif spread_quality == "wide":  # > 5¢ or > 100 bps  
                # Wide spreads: can be more patient, place closer to midpoint
                inside_factor = 0.2 if urgency in ["high", "urgent"] else 0.1
            else:  # "normal" spreads
                # Normal spreads: balanced approach
                inside_factor = 0.5 if urgency in ["high", "urgent"] else 0.3
                
            if side == BrokerOrderSide.BUY:
                # BUY: Start from ask and move inside toward bid
                # Example: Bid £10.00 / Ask £10.20 -> place around £10.11-£10.12 (inside spread)
                price = ask - (spread * inside_factor)
                # Ensure we don't go below bid
                price = max(price, bid + 0.01)
            else:
                # SELL: Start from bid and move inside toward ask  
                # Example: Bid £10.00 / Ask £10.20 -> place around £10.08-£10.09 (inside spread)
                price = bid + (spread * inside_factor)
                # Ensure we don't go above ask
                price = min(price, ask - 0.01)
                
            # Additional urgency adjustments
            if urgency == "urgent":
                if side == BrokerOrderSide.BUY:
                    # Be even more aggressive for urgent buys
                    price = min(price + 0.01, ask)
                else:
                    # Be even more aggressive for urgent sells
                    price = max(price - 0.01, bid)
                    
            logging.info(
                f"Liquidity-anchored price for {symbol} {side.value}: "
                f"bid={bid:.2f}, ask={ask:.2f}, spread={spread:.2f}¢, "
                f"quality={spread_quality}, urgency={urgency}, price={price:.2f}"
            )
            
            return round(float(price), 2)

        except (AttributeError, ValueError, TypeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Failed to get liquidity-anchored price for {symbol}: {e}"),
                "liquidity_anchored_pricing",
                function="get_liquidity_anchored_price",
                symbol=symbol,
                side=side.name,
                spread_quality=spread_quality,
                urgency=urgency,
                error_type=type(e).__name__,
            )
            logging.error(f"Error getting liquidity-anchored price for {symbol}: {e}")
            return None
        except Exception as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                DataProviderError(f"Unexpected error getting liquidity-anchored price for {symbol}: {e}"),
                "liquidity_anchored_pricing",
                function="get_liquidity_anchored_price",
                symbol=symbol,
                side=side.name,
                spread_quality=spread_quality,
                urgency=urgency,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error getting liquidity-anchored price for {symbol}: {e}")
            return None
