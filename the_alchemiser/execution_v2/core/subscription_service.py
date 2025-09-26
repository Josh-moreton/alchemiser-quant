"""Business Unit: execution | Status: current.

Subscription service for real-time pricing integration.

Encapsulates RealTimePricing access via WebSocketConnectionManager for localized
subscription behavior within execution workflows.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO

if TYPE_CHECKING:
    from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing real-time pricing subscriptions during execution."""

    def __init__(
        self,
        pricing_service: RealTimePricingService | None = None,
        *,
        enable_subscriptions: bool = True,
    ) -> None:
        """Initialize subscription service.

        Args:
            pricing_service: Real-time pricing service
            enable_subscriptions: Whether to enable subscriptions

        """
        self.pricing_service = pricing_service
        self.enable_subscriptions = enable_subscriptions

    def extract_all_symbols(self, plan: RebalancePlanDTO) -> list[str]:
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
        if not self.pricing_service or not self.enable_subscriptions:
            logger.info("📡 Subscriptions disabled, skipping bulk subscription")
            return {}

        if not symbols:
            return {}

        logger.info(f"📡 Bulk subscribing to {len(symbols)} symbols for real-time pricing")

        # Use the enhanced bulk subscription method
        subscription_results = self.pricing_service.bulk_subscribe_symbols(
            symbols,
            priority=5.0,  # High priority for execution
        )

        successful_subscriptions = sum(1 for success in subscription_results.values() if success)
        logger.info(
            f"✅ Bulk subscription complete: {successful_subscriptions}/{len(symbols)} "
            "symbols subscribed"
        )

        return subscription_results

    def cleanup_subscriptions(self, symbols: list[str]) -> None:
        """Clean up subscriptions after execution.

        Args:
            symbols: List of symbols to unsubscribe from

        """
        if not self.pricing_service or not self.enable_subscriptions or not symbols:
            return

        logger.info(f"🧹 Cleaning up subscriptions for {len(symbols)} symbols")

        try:
            # Unsubscribe from all symbols
            for symbol in symbols:
                try:
                    self.pricing_service.unsubscribe_symbol(symbol)
                except Exception as exc:
                    logger.debug(f"Error unsubscribing from {symbol}: {exc}")

            logger.info("🧹 Subscription cleanup completed")
        except Exception as exc:
            logger.warning(f"Error during subscription cleanup: {exc}")