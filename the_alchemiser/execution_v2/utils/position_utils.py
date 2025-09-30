"""Business Unit: execution | Status: current.

Position and pricing utilities extracted from the main executor.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PositionUtils:
    """Utilities for position management and pricing operations."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None,
        *,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize position utilities.

        Args:
            alpaca_manager: Alpaca broker manager
            pricing_service: Real-time pricing service
            enable_smart_execution: Whether smart execution is enabled

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.enable_smart_execution = enable_smart_execution

    def extract_all_symbols(self, plan: RebalancePlan) -> list[str]:
        """Extract all symbols from the rebalance plan.

        Args:
            plan: Rebalance plan to extract symbols from

        Returns:
            List of unique symbols in the plan

        """
        symbols = {item.symbol for item in plan.items if item.action in ["BUY", "SELL"]}
        sorted_symbols = sorted(symbols)
        logger.debug(f"📋 Extracted {len(sorted_symbols)} unique symbols for execution")
        return sorted_symbols

    def bulk_subscribe_symbols(self, symbols: list[str]) -> dict[str, bool]:
        """Bulk subscribe to all symbols for efficient real-time pricing.

        Args:
            symbols: List of symbols to subscribe to

        Returns:
            Dictionary mapping symbol to subscription success

        """
        if not self.pricing_service or not self.enable_smart_execution:
            logger.info("📡 Smart execution disabled, skipping bulk subscription")
            return {}

        if not symbols:
            return {}

        logger.info(
            f"📡 Bulk subscribing to {len(symbols)} symbols for real-time pricing"
        )

        # Use the enhanced bulk subscription method
        subscription_results = self.pricing_service.bulk_subscribe_symbols(
            symbols,
            priority=5.0,  # High priority for execution
        )

        successful_subscriptions = sum(
            1 for success in subscription_results.values() if success
        )
        logger.info(
            f"✅ Bulk subscription complete: {successful_subscriptions}/{len(symbols)} "
            "symbols subscribed"
        )

        return subscription_results

    def cleanup_subscriptions(self, symbols: list[str]) -> None:
        """Clean up symbol subscriptions after execution.

        Args:
            symbols: List of symbols to unsubscribe from

        """
        if not self.pricing_service or not symbols:
            return

        logger.info(f"🧹 Cleaning up subscriptions for {len(symbols)} symbols...")

        try:
            # Unsubscribe symbols one by one (no bulk method available)
            for symbol in symbols:
                self.pricing_service.unsubscribe_symbol(symbol)
            logger.debug(f"📡 Unsubscribed from {len(symbols)} symbols")
        except Exception as exc:
            logger.warning(f"⚠️ Error during unsubscription: {exc}")

        logger.info("✅ Subscription cleanup complete")

    def get_price_for_estimation(self, symbol: str) -> Decimal | None:
        """Get current price for trade estimation.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable

        """
        # Try real-time pricing first if available
        if self.pricing_service and self.enable_smart_execution:
            try:
                quote = self.pricing_service.get_quote_data(symbol)
                if (
                    quote
                    and hasattr(quote, "bid_price")
                    and hasattr(quote, "ask_price")
                ):
                    bid = quote.bid_price
                    ask = quote.ask_price
                    if bid and ask and bid > 0 and ask > 0:
                        mid_price = (Decimal(str(bid)) + Decimal(str(ask))) / Decimal(
                            "2"
                        )
                        logger.debug(
                            f"💰 Real-time price for {symbol}: ${mid_price:.2f}"
                        )
                        return mid_price
            except Exception as exc:
                logger.debug(f"Could not get real-time price for {symbol}: {exc}")

        # Fallback to static pricing
        try:
            static_price = self.alpaca_manager.get_current_price(symbol)
            if static_price and static_price > 0:
                price_decimal = Decimal(str(static_price))
                logger.debug(f"💰 Static price for {symbol}: ${price_decimal:.2f}")
                return price_decimal
        except Exception as exc:
            logger.warning(f"⚠️ Could not get static price for {symbol}: {exc}")

        return None

    def adjust_quantity_for_fractionability(
        self, symbol: str, raw_quantity: Decimal
    ) -> Decimal:
        """Adjust quantity based on whether the symbol supports fractional shares.

        Args:
            symbol: Stock symbol
            raw_quantity: Raw calculated quantity

        Returns:
            Adjusted quantity (rounded down for non-fractional symbols)

        """
        try:
            # Check if asset supports fractional trading
            asset_info = self.alpaca_manager.get_asset_info(symbol)
            supports_fractional = getattr(asset_info, "fractionable", False)

            if supports_fractional:
                # Keep fractional quantity (limit to 6 decimal places for precision)
                adjusted_quantity = raw_quantity.quantize(Decimal("0.000001"))
                logger.debug(
                    f"📊 {symbol}: fractional shares supported, quantity={adjusted_quantity}"
                )
                return adjusted_quantity
            # Round down to whole shares
            adjusted_quantity = raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)
            logger.debug(
                f"📊 {symbol}: whole shares only, quantity={adjusted_quantity}"
            )
            return adjusted_quantity

        except Exception as exc:
            logger.debug(f"Error checking fractionability for {symbol}: {exc}")
            # Default to whole shares if we can't determine fractionability
            return raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)

    def get_position_quantity(self, symbol: str) -> Decimal:
        """Get current position quantity for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current position quantity (0 if no position)

        """
        try:
            position = self.alpaca_manager.get_position(symbol)
            if position:
                qty = getattr(position, "qty", Decimal("0"))
                logger.debug(f"📊 Current position for {symbol}: {qty} shares")
                return qty
        except Exception as exc:
            logger.debug(f"Could not get position for {symbol}: {exc}")

        return Decimal("0")
