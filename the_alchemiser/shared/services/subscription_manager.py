"""Business Unit: shared | Status: current.

Subscription management for real-time market data streams.

This module handles subscription logic, priority management, and
capacity constraints for WebSocket market data streams.
"""

from __future__ import annotations

import threading
import time

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.market_data import SubscriptionPlan


class SubscriptionManager:
    """Manages subscriptions to real-time market data streams."""

    def __init__(self, max_symbols: int = 30) -> None:
        """Initialize the subscription manager.
        
        Args:
            max_symbols: Maximum number of concurrent symbol subscriptions
        """
        self._max_symbols = max_symbols
        self._subscribed_symbols: set[str] = set()
        self._subscription_priority: dict[str, float] = {}
        self._subscription_lock = threading.Lock()
        self._stats: dict[str, int] = {
            "total_subscriptions": 0,
            "subscription_limit_hits": 0,
        }
        self.logger = get_logger(__name__)

    def normalize_symbols(self, symbols: list[str]) -> list[str]:
        """Normalize symbol list by cleaning and filtering.
        
        Args:
            symbols: List of raw symbol strings
            
        Returns:
            List of cleaned and uppercased symbols
        """
        return [symbol.upper().strip() for symbol in symbols if symbol.strip()]

    def plan_bulk_subscription(self, symbols: list[str], priority: float) -> SubscriptionPlan:
        """Plan bulk subscription operations.
        
        Args:
            symbols: List of symbols to subscribe to
            priority: Priority score for subscriptions
            
        Returns:
            SubscriptionPlan with planned operations
        """
        results: dict[str, bool] = {}
        symbols_to_add = []

        # Handle existing symbols
        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                self._subscription_priority[symbol] = max(
                    self._subscription_priority.get(symbol, 0), priority
                )
                results[symbol] = True
                self.logger.debug(
                    f"Already subscribed to {symbol}, updated priority to "
                    f"{self._subscription_priority[symbol]:.1f}"
                )
            else:
                symbols_to_add.append(symbol)

        # Calculate capacity and replacements
        available_slots = self._max_symbols - len(self._subscribed_symbols)
        symbols_to_replace = self._find_symbols_to_replace(
            symbols_to_add, available_slots, priority
        )

        return SubscriptionPlan(
            results=results,
            symbols_to_add=symbols_to_add,
            symbols_to_replace=symbols_to_replace,
            available_slots=available_slots + len(symbols_to_replace),
            successfully_added=0,
        )

    def _find_symbols_to_replace(
        self, symbols_to_add: list[str], available_slots: int, priority: float
    ) -> list[str]:
        """Find existing symbols that can be replaced with higher priority ones.
        
        Args:
            symbols_to_add: Symbols that need slots
            available_slots: Current available capacity
            priority: Priority of new symbols
            
        Returns:
            List of symbols to replace
        """
        if len(symbols_to_add) <= available_slots:
            return []

        existing_symbols = sorted(
            self._subscription_priority.keys(),
            key=lambda x: self._subscription_priority.get(x, 0),
        )

        symbols_to_replace: list[str] = []
        symbols_needed = len(symbols_to_add) - available_slots

        for symbol in existing_symbols:
            if len(symbols_to_replace) >= symbols_needed:
                break
            if self._subscription_priority.get(symbol, 0) < priority:
                symbols_to_replace.append(symbol)

        return symbols_to_replace

    def execute_subscription_plan(self, plan: SubscriptionPlan, priority: float) -> None:
        """Execute the planned subscription operations.
        
        Args:
            plan: Subscription plan to execute
            priority: Priority for new subscriptions
        """
        # Remove symbols to be replaced
        for symbol_to_remove in plan.symbols_to_replace:
            self._subscribed_symbols.discard(symbol_to_remove)
            self._subscription_priority.pop(symbol_to_remove, None)
            self._stats["subscription_limit_hits"] += 1
            self.logger.info(f"📊 Replaced {symbol_to_remove} for higher priority symbols")

        # Add new symbols
        for symbol in plan.symbols_to_add[: plan.available_slots]:
            self._subscribed_symbols.add(symbol)
            self._subscription_priority[symbol] = priority
            plan.results[symbol] = True
            plan.successfully_added += 1
            self._stats["total_subscriptions"] += 1

        # Mark symbols we couldn't subscribe to due to limits
        for symbol in plan.symbols_to_add[plan.available_slots :]:
            plan.results[symbol] = False
            self.logger.warning(f"⚠️ Cannot subscribe to {symbol} - subscription limit reached")

    def subscribe_symbol(
        self, symbol: str, priority: float | None = None
    ) -> tuple[bool, bool]:
        """Subscribe to a single symbol with priority management.
        
        Args:
            symbol: Stock symbol to subscribe to
            priority: Priority score (higher = more important)
            
        Returns:
            Tuple of (needs_restart, was_added)
        """
        if priority is None:
            priority = time.time()

        with self._subscription_lock:
            # Check if we need to manage subscription limits
            if (
                symbol not in self._subscribed_symbols
                and len(self._subscribed_symbols) >= self._max_symbols
            ):
                # Find lowest priority symbol to unsubscribe
                lowest_priority_symbol = min(
                    self._subscribed_symbols,
                    key=lambda s: self._subscription_priority.get(s, 0),
                )
                lowest_priority = self._subscription_priority.get(lowest_priority_symbol, 0)

                if priority > lowest_priority:
                    # Unsubscribe lowest priority symbol
                    self.logger.info(
                        f"📊 Subscription limit reached. Replacing {lowest_priority_symbol} "
                        f"(priority: {lowest_priority:.1f}) with {symbol} (priority: {priority:.1f})"
                    )
                    self._subscribed_symbols.remove(lowest_priority_symbol)
                    self._subscription_priority.pop(lowest_priority_symbol, None)
                    self._stats["subscription_limit_hits"] += 1
                else:
                    self.logger.warning(
                        f"⚠️ Cannot subscribe to {symbol} - priority {priority:.1f} too low "
                        f"(limit: {self._max_symbols} symbols)"
                    )
                    return False, False

            if symbol not in self._subscribed_symbols:
                self._subscribed_symbols.add(symbol)
                self._subscription_priority[symbol] = priority
                self.logger.info(
                    f"📡 Added {symbol} to subscription list (priority: {priority:.1f})"
                )
                self.logger.debug(f"📊 Current subscriptions: {sorted(self._subscribed_symbols)}")
                self._stats["total_subscriptions"] += 1
                return True, True
            else:
                # Update priority for existing subscription
                self._subscription_priority[symbol] = max(
                    self._subscription_priority.get(symbol, 0), priority
                )
                return False, False

    def unsubscribe_symbol(self, symbol: str) -> bool:
        """Unsubscribe from a symbol.
        
        Args:
            symbol: Stock symbol to unsubscribe from
            
        Returns:
            True if symbol was removed
        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                self._subscription_priority.pop(symbol, None)
                self.logger.info(f"📉 Unsubscribed from {symbol}")
                return True
            return False

    def get_subscribed_symbols(self) -> set[str]:
        """Get current subscribed symbols.
        
        Returns:
            Set of currently subscribed symbols
        """
        with self._subscription_lock:
            return self._subscribed_symbols.copy()

    def get_stats(self) -> dict[str, int]:
        """Get subscription statistics.
        
        Returns:
            Dictionary of statistics
        """
        return self._stats.copy()

    def can_subscribe(self, symbol: str, priority: float) -> bool:
        """Check if a symbol can be subscribed with given priority.
        
        Args:
            symbol: Stock symbol
            priority: Desired priority
            
        Returns:
            True if subscription is possible
        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                return True
                
            if len(self._subscribed_symbols) < self._max_symbols:
                return True
                
            # Check if we can replace a lower priority symbol
            lowest_priority = min(
                (self._subscription_priority.get(s, 0) for s in self._subscribed_symbols),
                default=float('inf')
            )
            return priority > lowest_priority
