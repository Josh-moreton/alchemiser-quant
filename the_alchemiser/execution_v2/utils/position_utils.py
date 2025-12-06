"""Business Unit: execution | Status: current.

Position and pricing utilities extracted from the main executor.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors.exceptions import (
    MarketDataError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = get_logger(__name__)


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

        logger.info(f"📡 Bulk subscribing to {len(symbols)} symbols for real-time pricing")

        # Use the enhanced bulk subscription method
        subscription_results: dict[str, bool] = self.pricing_service.subscribe_symbols_bulk(
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
        except (AttributeError, RuntimeError) as exc:
            logger.warning(
                "⚠️ Error during unsubscription (known error)",
                error=str(exc),
                error_type=type(exc).__name__,
            )
        except Exception as exc:
            logger.warning(
                "⚠️ Error during unsubscription (unexpected error)",
                error=str(exc),
                error_type=type(exc).__name__,
            )

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
            real_time_price = self._get_real_time_price(symbol)
            if real_time_price is not None:
                return real_time_price

        # Fallback to static pricing
        return self._get_static_price(symbol)

    def _get_real_time_price(self, symbol: str) -> Decimal | None:
        """Get price from real-time pricing service.

        Args:
            symbol: Stock symbol

        Returns:
            Mid-price from real-time quote or None if unavailable

        """
        if not self.pricing_service:
            return None

        try:
            quote = self.pricing_service.get_quote_data(symbol)
            if not quote:
                return None

            if not (hasattr(quote, "bid_price") and hasattr(quote, "ask_price")):
                return None

            bid = quote.bid_price
            ask = quote.ask_price

            if not (bid and ask and bid > 0 and ask > 0):
                return None

            mid_price = (Decimal(str(bid)) + Decimal(str(ask))) / Decimal("2")
            logger.debug(f"💰 Real-time price for {symbol}: ${mid_price:.2f}")
            return mid_price

        except (AttributeError, ValueError, TypeError) as exc:
            logger.debug(
                "Could not get real-time price (data error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return None
        except Exception as exc:
            logger.debug(
                "Could not get real-time price (unexpected error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return None

    def _get_static_price(self, symbol: str) -> Decimal | None:
        """Get price from static Alpaca pricing.

        Args:
            symbol: Stock symbol

        Returns:
            Current price from Alpaca API or None if unavailable

        """
        try:
            static_price = self.alpaca_manager.get_current_price(symbol)
            if not static_price or static_price <= 0:
                return None

            price_decimal = Decimal(str(static_price))
            logger.debug(f"💰 Static price for {symbol}: ${price_decimal:.2f}")
            return price_decimal

        except (TradingClientError, MarketDataError) as exc:
            logger.warning(
                "⚠️ Could not get static price (client error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return None
        except (ValueError, TypeError) as exc:
            logger.warning(
                "⚠️ Could not get static price (conversion error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return None
        except Exception as exc:
            logger.warning(
                "⚠️ Could not get static price (unexpected error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return None

    def adjust_quantity_for_fractionability(self, symbol: str, raw_quantity: Decimal) -> Decimal:
        """Adjust quantity based on whether the symbol supports fractional shares.

        Args:
            symbol: Stock symbol
            raw_quantity: Raw calculated quantity

        Returns:
            Adjusted quantity (rounded down for non-fractional symbols)

        """
        try:
            # Ensure input is always a Decimal for safety
            if not isinstance(raw_quantity, Decimal):
                raw_quantity = Decimal(str(raw_quantity))

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
            logger.debug(f"📊 {symbol}: whole shares only, quantity={adjusted_quantity}")
            return adjusted_quantity

        except (TradingClientError, ValidationError) as exc:
            logger.debug(
                "Error checking fractionability (client error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            # Default to whole shares if we can't determine fractionability
            if not isinstance(raw_quantity, Decimal):
                raw_quantity = Decimal(str(raw_quantity))
            return raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)
        except (AttributeError, ValueError, TypeError) as exc:
            logger.debug(
                "Error checking fractionability (data error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            # Default to whole shares if we can't determine fractionability
            if not isinstance(raw_quantity, Decimal):
                raw_quantity = Decimal(str(raw_quantity))
            return raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)
        except Exception as exc:
            logger.debug(
                "Error checking fractionability (unexpected error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            # Default to whole shares if we can't determine fractionability
            if not isinstance(raw_quantity, Decimal):
                raw_quantity = Decimal(str(raw_quantity))
            return raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)

    def get_position_quantity(self, symbol: str) -> Decimal:
        """Get current position quantity for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current position quantity (0 if no position), rounded to 6 decimal places
            to avoid precision errors when selling fractional shares

        """
        try:
            position = self.alpaca_manager.get_position(symbol)
            if position:
                qty = getattr(position, "qty", 0)
                # Ensure we always return a Decimal, even if the position object returns a string/float
                qty_decimal = Decimal(str(qty))

                # Round down to 6 decimal places to ensure we never try to sell more than available
                # This prevents errors like "requested: 7.227358, available: 7.2273576"
                qty_decimal = qty_decimal.quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

                logger.debug(f"📊 Current position for {symbol}: {qty_decimal} shares")
                return qty_decimal
        except (TradingClientError, ValidationError) as exc:
            logger.debug(
                f"Could not get position for {symbol} (client error): {exc}",
                error_type=type(exc).__name__,
            )
        except (ValueError, TypeError) as exc:
            logger.debug(
                f"Could not get position for {symbol} (conversion error): {exc}",
                error_type=type(exc).__name__,
            )
        except Exception as exc:
            logger.debug(
                f"Could not get position for {symbol} (unexpected error): {exc}",
                error_type=type(exc).__name__,
            )

        return Decimal("0")
