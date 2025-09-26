"""Business Unit: shared | Status: current.

Bulk subscription planning, replacement policy, and priority management.
"""

from __future__ import annotations

import logging
import time

from .models import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionPlanner:
    """Manages subscription planning and priority-based replacement."""

    def __init__(self, max_symbols: int = 30) -> None:
        """Initialize subscription planner.
        
        Args:
            max_symbols: Maximum number of symbols to subscribe to concurrently

        """
        self._max_symbols = max_symbols

    def normalize_symbols(self, symbols: list[str]) -> list[str]:
        """Normalize symbol list by cleaning and filtering.
        
        Args:
            symbols: List of raw symbols
            
        Returns:
            Cleaned and normalized symbol list

        """
        return [symbol.upper().strip() for symbol in symbols if symbol.strip()]

    def plan_bulk_subscription(
        self,
        symbols: list[str],
        priority: float,
        subscribed_symbols: set[str],
        subscription_priority: dict[str, float],
    ) -> SubscriptionPlan:
        """Plan bulk subscription operations.
        
        Args:
            symbols: List of symbols to subscribe to
            priority: Priority for new subscriptions
            subscribed_symbols: Currently subscribed symbols
            subscription_priority: Current priority mapping
            
        Returns:
            SubscriptionPlan with planned operations

        """
        results: dict[str, bool] = {}
        symbols_to_add = []

        # Handle existing symbols
        for symbol in symbols:
            if symbol in subscribed_symbols:
                # Update priority if higher
                current_priority = subscription_priority.get(symbol, 0)
                if priority > current_priority:
                    subscription_priority[symbol] = priority
                results[symbol] = True
                logger.debug(
                    f"Already subscribed to {symbol}, priority now "
                    f"{subscription_priority[symbol]:.1f}"
                )
            else:
                symbols_to_add.append(symbol)

        # Calculate capacity and replacements
        available_slots = self._max_symbols - len(subscribed_symbols)
        symbols_to_replace = self._find_symbols_to_replace(
            symbols_to_add, available_slots, priority, subscription_priority
        )

        return SubscriptionPlan(
            results=results,
            symbols_to_add=symbols_to_add,
            symbols_to_replace=symbols_to_replace,
            available_slots=available_slots + len(symbols_to_replace),
            successfully_added=0,
        )

    def _find_symbols_to_replace(
        self,
        symbols_to_add: list[str],
        available_slots: int,
        priority: float,
        subscription_priority: dict[str, float],
    ) -> list[str]:
        """Find existing symbols that can be replaced with higher priority ones.
        
        Args:
            symbols_to_add: New symbols to add
            available_slots: Available subscription slots
            priority: Priority of new symbols
            subscription_priority: Current priority mapping
            
        Returns:
            List of symbols to replace

        """
        if len(symbols_to_add) <= available_slots:
            return []

        existing_symbols = sorted(
            subscription_priority.keys(),
            key=lambda x: subscription_priority.get(x, 0),
        )

        symbols_to_replace: list[str] = []
        symbols_needed = len(symbols_to_add) - available_slots

        for symbol in existing_symbols:
            if len(symbols_to_replace) >= symbols_needed:
                break
            if subscription_priority.get(symbol, 0) < priority:
                symbols_to_replace.append(symbol)

        return symbols_to_replace

    def can_replace_symbol(
        self,
        new_priority: float,
        subscribed_symbols: set[str],
        subscription_priority: dict[str, float],
    ) -> tuple[bool, str | None]:
        """Check if we can replace a symbol with a higher priority one.
        
        Args:
            new_priority: Priority of the new symbol
            subscribed_symbols: Currently subscribed symbols
            subscription_priority: Current priority mapping
            
        Returns:
            Tuple of (can_replace, symbol_to_replace)

        """
        if len(subscribed_symbols) < self._max_symbols:
            return True, None

        # Find lowest priority symbol
        lowest_priority_symbol = min(
            subscribed_symbols,
            key=lambda s: subscription_priority.get(s, 0),
        )
        lowest_priority = subscription_priority.get(lowest_priority_symbol, 0)

        if new_priority > lowest_priority:
            return True, lowest_priority_symbol

        return False, None

    def execute_subscription_plan(
        self,
        plan: SubscriptionPlan,
        priority: float,
        subscribed_symbols: set[str],
        subscription_priority: dict[str, float],
        stats: dict[str, int],
    ) -> None:
        """Execute the planned subscription operations.
        
        Args:
            plan: Subscription plan to execute
            priority: Priority for new subscriptions
            subscribed_symbols: Currently subscribed symbols (modified in place)
            subscription_priority: Priority mapping (modified in place)
            stats: Statistics dictionary (modified in place)

        """
        # Remove symbols to be replaced
        for symbol_to_remove in plan.symbols_to_replace:
            subscribed_symbols.discard(symbol_to_remove)
            subscription_priority.pop(symbol_to_remove, None)
            stats["subscription_limit_hits"] += 1
            logger.info(f"📊 Replaced {symbol_to_remove} for higher priority symbols")

        # Add new symbols
        for symbol in plan.symbols_to_add[: plan.available_slots]:
            subscribed_symbols.add(symbol)
            subscription_priority[symbol] = priority
            plan.results[symbol] = True
            plan.successfully_added += 1
            stats["total_subscriptions"] += 1

        # Mark symbols we couldn't subscribe to due to limits
        for symbol in plan.symbols_to_add[plan.available_slots :]:
            plan.results[symbol] = False
            logger.warning(f"⚠️ Cannot subscribe to {symbol} - subscription limit reached")

    def get_default_priority(self) -> float:
        """Get default priority based on current timestamp.
        
        Returns:
            Default priority value

        """
        return time.time()