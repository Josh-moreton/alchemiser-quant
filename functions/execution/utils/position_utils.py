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
from the_alchemiser.shared.utils.validation_utils import detect_suspicious_quote_prices

logger = get_logger(__name__)

# Price validation thresholds (aligned with executor.py)
MIN_REASONABLE_PRICE = Decimal("0.50")  # Sub-$0.50 prices are suspicious
MAX_SPREAD_PERCENT = 15.0  # >15% spread triggers REST fallback


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
        """Get current price for trade estimation with validation and fallback.

        Uses a multi-stage approach:
        1. Try real-time WebSocket pricing with quote validation
        2. If quote looks suspicious, fall back to REST API immediately
        3. If real-time unavailable, use REST API directly

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable

        """
        # Try real-time pricing first if available
        if self.pricing_service and self.enable_smart_execution:
            try:
                quote = self.pricing_service.get_quote_data(symbol)
                if quote and hasattr(quote, "bid_price") and hasattr(quote, "ask_price"):
                    bid = quote.bid_price
                    ask = quote.ask_price

                    # Validate quote before using it
                    if bid and ask:
                        is_suspicious, reasons = detect_suspicious_quote_prices(
                            bid_price=bid,
                            ask_price=ask,
                            min_price=float(MIN_REASONABLE_PRICE),
                            max_spread_percent=MAX_SPREAD_PERCENT,
                        )

                        if is_suspicious:
                            logger.warning(
                                "⚠️ Suspicious real-time quote detected, falling back to REST",
                                extra={
                                    "symbol": symbol,
                                    "bid": str(bid),
                                    "ask": str(ask),
                                    "reasons": reasons,
                                    "action": "rest_fallback",
                                },
                            )
                            # Skip to REST fallback below
                        elif bid > 0 and ask > 0:
                            mid_price = (Decimal(str(bid)) + Decimal(str(ask))) / Decimal("2")
                            logger.debug(
                                "💰 Real-time price for symbol (validated)",
                                extra={
                                    "symbol": symbol,
                                    "price": str(mid_price),
                                    "bid": str(bid),
                                    "ask": str(ask),
                                    "source": "real_time_websocket_validated",
                                },
                            )
                            return mid_price
                    else:
                        logger.warning(
                            "⚠️ Real-time quote has invalid bid/ask",
                            extra={
                                "symbol": symbol,
                                "bid": str(bid) if bid else None,
                                "ask": str(ask) if ask else None,
                            },
                        )
                else:
                    logger.debug(
                        "Real-time quote not available for symbol",
                        extra={"symbol": symbol, "quote_exists": quote is not None},
                    )
            except (AttributeError, ValueError, TypeError) as exc:
                logger.debug(
                    "Could not get real-time price (data error)",
                    symbol=symbol,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
            except Exception as exc:
                logger.debug(
                    "Could not get real-time price (unexpected error)",
                    symbol=symbol,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )

        # Fallback to REST API (static pricing)
        return self._get_price_from_rest_api(symbol)

    def _get_price_from_rest_api(self, symbol: str) -> Decimal | None:
        """Get price from REST API as fallback.

        Args:
            symbol: Stock symbol

        Returns:
            Price from REST API or None if unavailable

        """
        try:
            static_price = self.alpaca_manager.get_current_price(symbol)
            if static_price and static_price > 0:
                price_decimal = Decimal(str(static_price))

                # Validate REST API price too
                if price_decimal < MIN_REASONABLE_PRICE:
                    logger.error(
                        "🚨 REST API returned suspicious price",
                        extra={
                            "symbol": symbol,
                            "price": str(price_decimal),
                            "min_reasonable": str(MIN_REASONABLE_PRICE),
                            "source": "alpaca_rest_api",
                        },
                    )
                    return None

                logger.debug(
                    "💰 Static price for symbol",
                    extra={
                        "symbol": symbol,
                        "price": str(price_decimal),
                        "source": "alpaca_rest_api",
                    },
                )
                return price_decimal
            logger.warning(
                "⚠️ Static price unavailable or zero",
                extra={
                    "symbol": symbol,
                    "static_price": str(static_price) if static_price else None,
                },
            )
        except (TradingClientError, MarketDataError) as exc:
            logger.warning(
                "⚠️ Could not get static price (client error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
        except (ValueError, TypeError) as exc:
            logger.warning(
                "⚠️ Could not get static price (conversion error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )
        except Exception as exc:
            logger.warning(
                "⚠️ Could not get static price (unexpected error)",
                symbol=symbol,
                error=str(exc),
                error_type=type(exc).__name__,
            )

        logger.error(
            "🚨 All price discovery methods failed",
            extra={"symbol": symbol, "real_time_enabled": self.enable_smart_execution},
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
