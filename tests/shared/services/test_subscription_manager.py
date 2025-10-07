"""Business Unit: shared | Status: current.

Comprehensive tests for SubscriptionManager.

Tests cover:
- Initialization and configuration
- Symbol normalization
- Subscription planning (bulk operations)
- Priority management and updates
- Capacity management and limits
- Thread-safety of concurrent operations
- Statistics tracking
- Edge cases and error conditions
"""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.services.subscription_manager import SubscriptionManager
from the_alchemiser.shared.types.market_data import SubscriptionPlan


class TestSubscriptionManagerInitialization:
    """Test SubscriptionManager initialization and configuration."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        manager = SubscriptionManager()
        assert manager._max_symbols == 30
        assert len(manager._subscribed_symbols) == 0
        assert len(manager._subscription_priority) == 0
        assert manager._stats["total_subscriptions"] == 0
        assert manager._stats["subscription_limit_hits"] == 0

    def test_custom_max_symbols(self):
        """Test initialization with custom max_symbols."""
        manager = SubscriptionManager(max_symbols=50)
        assert manager._max_symbols == 50

    def test_invalid_max_symbols_zero(self):
        """Test initialization fails with max_symbols=0."""
        with pytest.raises(ConfigurationError, match="max_symbols must be greater than zero"):
            SubscriptionManager(max_symbols=0)

    def test_invalid_max_symbols_negative(self):
        """Test initialization fails with negative max_symbols."""
        with pytest.raises(ConfigurationError, match="max_symbols must be greater than zero"):
            SubscriptionManager(max_symbols=-5)


class TestSymbolNormalization:
    """Test symbol normalization logic."""

    def test_normalize_empty_list(self):
        """Test normalizing empty symbol list."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols([])
        assert result == []

    def test_normalize_single_symbol(self):
        """Test normalizing single symbol."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols(["aapl"])
        assert result == ["AAPL"]

    def test_normalize_multiple_symbols(self):
        """Test normalizing multiple symbols."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols(["aapl", "TSLA", "googl"])
        assert result == ["AAPL", "TSLA", "GOOGL"]

    def test_normalize_with_whitespace(self):
        """Test normalizing symbols with leading/trailing whitespace."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols([" aapl ", "  TSLA", "GOOGL  "])
        assert result == ["AAPL", "TSLA", "GOOGL"]

    def test_normalize_filters_empty_strings(self):
        """Test that empty strings are filtered out."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols(["aapl", "", "  ", "tsla"])
        assert result == ["AAPL", "TSLA"]

    def test_normalize_preserves_order(self):
        """Test that normalization preserves input order."""
        manager = SubscriptionManager()
        result = manager.normalize_symbols(["zzz", "aaa", "mmm"])
        assert result == ["ZZZ", "AAA", "MMM"]


class TestSingleSymbolSubscription:
    """Test single symbol subscription operations."""

    def test_subscribe_new_symbol(self):
        """Test subscribing to a new symbol."""
        manager = SubscriptionManager(max_symbols=5)
        needs_restart, was_added = manager.subscribe_symbol("AAPL", priority=10.0)
        assert needs_restart is True
        assert was_added is True
        assert "AAPL" in manager.get_subscribed_symbols()
        assert manager._stats["total_subscriptions"] == 1

    def test_subscribe_existing_symbol(self):
        """Test subscribing to already subscribed symbol."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        needs_restart, was_added = manager.subscribe_symbol("AAPL", priority=15.0)
        assert needs_restart is False
        assert was_added is False
        # Priority should be updated to max
        assert manager._subscription_priority["AAPL"] == 15.0

    def test_subscribe_with_default_priority(self):
        """Test subscribing with default priority (timestamp)."""
        manager = SubscriptionManager(max_symbols=5)
        with patch("time.time", return_value=1234567890.0):
            needs_restart, was_added = manager.subscribe_symbol("AAPL")
            assert needs_restart is True
            assert was_added is True
            assert manager._subscription_priority["AAPL"] == 1234567890.0

    def test_subscribe_at_capacity_higher_priority(self):
        """Test subscribing when at capacity with higher priority replaces lowest."""
        manager = SubscriptionManager(max_symbols=3)
        manager.subscribe_symbol("AAPL", priority=5.0)
        manager.subscribe_symbol("TSLA", priority=10.0)
        manager.subscribe_symbol("GOOGL", priority=15.0)

        # Subscribe with higher priority than AAPL (5.0)
        needs_restart, was_added = manager.subscribe_symbol("MSFT", priority=20.0)
        assert needs_restart is True  # Symbol was added (replacement occurred)
        assert was_added is True
        assert "MSFT" in manager.get_subscribed_symbols()
        assert "AAPL" not in manager.get_subscribed_symbols()
        assert manager._stats["subscription_limit_hits"] == 1

    def test_subscribe_at_capacity_lower_priority_rejected(self):
        """Test subscribing when at capacity with lower priority is rejected."""
        manager = SubscriptionManager(max_symbols=3)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=20.0)
        manager.subscribe_symbol("GOOGL", priority=30.0)

        # Try to subscribe with lower priority than all existing
        needs_restart, was_added = manager.subscribe_symbol("MSFT", priority=5.0)
        assert needs_restart is False
        assert was_added is False
        assert "MSFT" not in manager.get_subscribed_symbols()
        assert len(manager.get_subscribed_symbols()) == 3

    def test_subscribe_priority_update_uses_max(self):
        """Test that re-subscribing updates priority to maximum value."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        assert manager._subscription_priority["AAPL"] == 10.0

        # Re-subscribe with lower priority
        manager.subscribe_symbol("AAPL", priority=5.0)
        assert manager._subscription_priority["AAPL"] == 10.0  # Should stay at max

        # Re-subscribe with higher priority
        manager.subscribe_symbol("AAPL", priority=20.0)
        assert manager._subscription_priority["AAPL"] == 20.0  # Should increase


class TestUnsubscribe:
    """Test unsubscription operations."""

    def test_unsubscribe_existing_symbol(self):
        """Test unsubscribing from an existing symbol."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        result = manager.unsubscribe_symbol("AAPL")
        assert result is True
        assert "AAPL" not in manager.get_subscribed_symbols()
        assert "AAPL" not in manager._subscription_priority

    def test_unsubscribe_nonexistent_symbol(self):
        """Test unsubscribing from a symbol not in the list."""
        manager = SubscriptionManager(max_symbols=5)
        result = manager.unsubscribe_symbol("AAPL")
        assert result is False

    def test_unsubscribe_idempotent(self):
        """Test that unsubscribe is idempotent."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        assert manager.unsubscribe_symbol("AAPL") is True
        assert manager.unsubscribe_symbol("AAPL") is False
        assert manager.unsubscribe_symbol("AAPL") is False


class TestBulkSubscriptionPlanning:
    """Test bulk subscription planning logic."""

    def test_plan_bulk_with_empty_list(self):
        """Test planning with empty symbol list."""
        manager = SubscriptionManager(max_symbols=5)
        plan = manager.plan_bulk_subscription([], priority=10.0)
        assert isinstance(plan, SubscriptionPlan)
        assert plan.symbols_to_add == []
        assert plan.symbols_to_replace == []
        assert plan.available_slots == 5

    def test_plan_bulk_new_symbols_within_capacity(self):
        """Test planning new symbols within capacity."""
        manager = SubscriptionManager(max_symbols=5)
        plan = manager.plan_bulk_subscription(["AAPL", "TSLA", "GOOGL"], priority=10.0)
        assert plan.symbols_to_add == ["AAPL", "TSLA", "GOOGL"]
        assert plan.symbols_to_replace == []
        assert plan.available_slots == 5

    def test_plan_bulk_existing_symbols(self):
        """Test planning with already subscribed symbols."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=5.0)
        manager.subscribe_symbol("TSLA", priority=10.0)

        plan = manager.plan_bulk_subscription(["AAPL", "GOOGL"], priority=15.0)
        # AAPL already exists, so only GOOGL should be added
        assert plan.symbols_to_add == ["GOOGL"]
        # AAPL should be marked as successful in results (already subscribed)
        assert plan.results["AAPL"] is True
        # Priority for AAPL should be updated to 15.0 in planning
        assert manager._subscription_priority["AAPL"] == 15.0

    def test_plan_bulk_exceeds_capacity_with_replacements(self):
        """Test planning when symbols exceed capacity and replacements are needed."""
        manager = SubscriptionManager(max_symbols=3)
        manager.subscribe_symbol("OLD1", priority=5.0)
        manager.subscribe_symbol("OLD2", priority=10.0)
        manager.subscribe_symbol("OLD3", priority=15.0)

        # Try to add 2 new symbols with high priority
        plan = manager.plan_bulk_subscription(["NEW1", "NEW2"], priority=20.0)
        assert plan.symbols_to_add == ["NEW1", "NEW2"]
        # Should identify 2 symbols to replace (OLD1 and OLD2, lowest priorities)
        assert len(plan.symbols_to_replace) == 2
        assert "OLD1" in plan.symbols_to_replace
        assert "OLD2" in plan.symbols_to_replace
        # Available slots = 0 (at capacity) + 2 (replacements) = 2
        assert plan.available_slots == 2

    def test_plan_bulk_no_replacements_if_priority_too_low(self):
        """Test that low priority symbols don't trigger replacements."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("HIGH1", priority=100.0)
        manager.subscribe_symbol("HIGH2", priority=200.0)

        # Try to add symbols with lower priority
        plan = manager.plan_bulk_subscription(["LOW1", "LOW2"], priority=50.0)
        assert plan.symbols_to_add == ["LOW1", "LOW2"]
        assert plan.symbols_to_replace == []  # No replacements because priority too low
        assert plan.available_slots == 0


class TestBulkSubscriptionExecution:
    """Test bulk subscription execution."""

    def test_execute_plan_add_new_symbols(self):
        """Test executing plan to add new symbols."""
        manager = SubscriptionManager(max_symbols=5)
        plan = SubscriptionPlan(
            results={},
            symbols_to_add=["AAPL", "TSLA", "GOOGL"],
            symbols_to_replace=[],
            available_slots=5,
            successfully_added=0,
        )

        manager.execute_subscription_plan(plan, priority=10.0)
        assert len(manager.get_subscribed_symbols()) == 3
        assert "AAPL" in manager.get_subscribed_symbols()
        assert plan.successfully_added == 3
        assert plan.results["AAPL"] is True
        assert manager._stats["total_subscriptions"] == 3

    def test_execute_plan_with_replacements(self):
        """Test executing plan that replaces existing symbols."""
        manager = SubscriptionManager(max_symbols=3)
        manager.subscribe_symbol("OLD1", priority=5.0)
        manager.subscribe_symbol("OLD2", priority=10.0)
        manager.subscribe_symbol("OLD3", priority=15.0)

        plan = SubscriptionPlan(
            results={},
            symbols_to_add=["NEW1", "NEW2"],
            symbols_to_replace=["OLD1", "OLD2"],
            available_slots=2,
            successfully_added=0,
        )

        manager.execute_subscription_plan(plan, priority=20.0)
        assert "NEW1" in manager.get_subscribed_symbols()
        assert "NEW2" in manager.get_subscribed_symbols()
        assert "OLD3" in manager.get_subscribed_symbols()
        assert "OLD1" not in manager.get_subscribed_symbols()
        assert "OLD2" not in manager.get_subscribed_symbols()
        assert manager._stats["subscription_limit_hits"] == 2

    def test_execute_plan_exceeds_available_slots(self):
        """Test executing plan when symbols exceed available slots."""
        manager = SubscriptionManager(max_symbols=2)
        plan = SubscriptionPlan(
            results={},
            symbols_to_add=["SYM1", "SYM2", "SYM3"],
            symbols_to_replace=[],
            available_slots=2,
            successfully_added=0,
        )

        manager.execute_subscription_plan(plan, priority=10.0)
        # Only first 2 should be added
        assert len(manager.get_subscribed_symbols()) == 2
        assert plan.successfully_added == 2
        assert plan.results["SYM1"] is True
        assert plan.results["SYM2"] is True
        assert plan.results["SYM3"] is False  # Rejected


class TestCapacityChecking:
    """Test capacity checking logic."""

    def test_can_subscribe_existing_symbol(self):
        """Test that existing symbols can always be subscribed."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("AAPL", priority=10.0)
        assert manager.can_subscribe("AAPL", priority=5.0) is True

    def test_can_subscribe_within_capacity(self):
        """Test subscription allowed when within capacity."""
        manager = SubscriptionManager(max_symbols=3)
        manager.subscribe_symbol("AAPL", priority=10.0)
        assert manager.can_subscribe("TSLA", priority=10.0) is True

    def test_can_subscribe_at_capacity_higher_priority(self):
        """Test subscription allowed at capacity with higher priority."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=20.0)

        assert manager.can_subscribe("GOOGL", priority=30.0) is True

    def test_can_subscribe_at_capacity_lower_priority(self):
        """Test subscription rejected at capacity with lower priority."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=20.0)

        assert manager.can_subscribe("GOOGL", priority=5.0) is False

    def test_can_subscribe_empty_subscriptions(self):
        """Test capacity check with no existing subscriptions."""
        manager = SubscriptionManager(max_symbols=5)
        assert manager.can_subscribe("AAPL", priority=10.0) is True


class TestStatistics:
    """Test statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        manager = SubscriptionManager(max_symbols=5)
        stats = manager.get_stats()
        assert stats["total_subscriptions"] == 0
        assert stats["subscription_limit_hits"] == 0

    def test_stats_increment_on_subscribe(self):
        """Test that stats increment correctly on subscription."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=10.0)
        stats = manager.get_stats()
        assert stats["total_subscriptions"] == 2
        assert stats["subscription_limit_hits"] == 0

    def test_stats_limit_hits_on_replacement(self):
        """Test that limit hits increment on symbol replacement."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=20.0)
        # This should trigger replacement
        manager.subscribe_symbol("GOOGL", priority=30.0)
        stats = manager.get_stats()
        assert stats["subscription_limit_hits"] == 1

    def test_stats_copy_is_independent(self):
        """Test that returned stats dict is a copy."""
        manager = SubscriptionManager(max_symbols=5)
        stats1 = manager.get_stats()
        stats1["total_subscriptions"] = 999
        stats2 = manager.get_stats()
        assert stats2["total_subscriptions"] == 0  # Should not be affected


class TestThreadSafety:
    """Test thread-safety of concurrent operations."""

    def test_concurrent_subscribe_operations(self):
        """Test concurrent subscription operations from multiple threads."""
        manager = SubscriptionManager(max_symbols=100)
        symbols = [f"SYM{i}" for i in range(50)]
        results = []

        def subscribe_symbols(symbol_list):
            for symbol in symbol_list:
                result = manager.subscribe_symbol(symbol, priority=10.0)
                results.append(result)

        # Split symbols into 5 threads
        threads = []
        chunk_size = len(symbols) // 5
        for i in range(5):
            chunk = symbols[i * chunk_size : (i + 1) * chunk_size]
            thread = threading.Thread(target=subscribe_symbols, args=(chunk,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All symbols should be subscribed
        subscribed = manager.get_subscribed_symbols()
        assert len(subscribed) == 50
        for symbol in symbols:
            assert symbol in subscribed

    def test_concurrent_read_write_operations(self):
        """Test concurrent reads and writes don't cause corruption."""
        manager = SubscriptionManager(max_symbols=50)
        stop_flag = threading.Event()
        results = {"reads": 0, "writes": 0, "errors": 0}

        def reader():
            while not stop_flag.is_set():
                try:
                    manager.get_subscribed_symbols()
                    manager.get_stats()
                    results["reads"] += 1
                except Exception:
                    results["errors"] += 1

        def writer():
            i = 0
            while not stop_flag.is_set():
                try:
                    manager.subscribe_symbol(f"SYM{i % 30}", priority=float(i))
                    results["writes"] += 1
                    i += 1
                except Exception:
                    results["errors"] += 1

        # Start readers and writers
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=reader))
        for _ in range(2):
            threads.append(threading.Thread(target=writer))

        for thread in threads:
            thread.start()

        # Run for a short time
        time.sleep(0.5)
        stop_flag.set()

        for thread in threads:
            thread.join()

        # No errors should occur
        assert results["errors"] == 0
        assert results["reads"] > 0
        assert results["writes"] > 0

    def test_concurrent_unsubscribe_operations(self):
        """Test concurrent unsubscribe operations."""
        manager = SubscriptionManager(max_symbols=100)
        symbols = [f"SYM{i}" for i in range(30)]

        # First, subscribe all symbols
        for symbol in symbols:
            manager.subscribe_symbol(symbol, priority=10.0)

        # Now unsubscribe concurrently
        results = []

        def unsubscribe_symbols(symbol_list):
            for symbol in symbol_list:
                result = manager.unsubscribe_symbol(symbol)
                results.append(result)

        threads = []
        chunk_size = len(symbols) // 3
        for i in range(3):
            chunk = symbols[i * chunk_size : (i + 1) * chunk_size]
            thread = threading.Thread(target=unsubscribe_symbols, args=(chunk,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All symbols should be unsubscribed
        subscribed = manager.get_subscribed_symbols()
        assert len(subscribed) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_subscribe_after_unsubscribe(self):
        """Test re-subscribing after unsubscribing."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.unsubscribe_symbol("AAPL")
        needs_restart, was_added = manager.subscribe_symbol("AAPL", priority=20.0)
        assert needs_restart is True
        assert was_added is True
        assert manager._subscription_priority["AAPL"] == 20.0

    def test_get_subscribed_symbols_returns_copy(self):
        """Test that get_subscribed_symbols returns a copy."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("AAPL", priority=10.0)
        symbols1 = manager.get_subscribed_symbols()
        symbols1.add("FAKE")
        symbols2 = manager.get_subscribed_symbols()
        assert "FAKE" not in symbols2
        assert len(symbols2) == 1

    def test_priority_equal_to_lowest(self):
        """Test subscription with priority equal to lowest existing."""
        manager = SubscriptionManager(max_symbols=2)
        manager.subscribe_symbol("AAPL", priority=10.0)
        manager.subscribe_symbol("TSLA", priority=20.0)

        # Try to subscribe with priority equal to lowest (10.0)
        needs_restart, was_added = manager.subscribe_symbol("GOOGL", priority=10.0)
        assert was_added is False  # Should be rejected (needs strictly higher)

    def test_find_symbols_to_replace_sorts_by_priority(self):
        """Test that symbol replacement prioritizes lowest priority symbols."""
        manager = SubscriptionManager(max_symbols=5)
        manager.subscribe_symbol("SYM1", priority=100.0)
        manager.subscribe_symbol("SYM2", priority=50.0)
        manager.subscribe_symbol("SYM3", priority=200.0)
        manager.subscribe_symbol("SYM4", priority=25.0)
        manager.subscribe_symbol("SYM5", priority=150.0)

        # Request 3 replacements with high priority
        plan = manager.plan_bulk_subscription(["NEW1", "NEW2", "NEW3"], priority=300.0)

        # Should replace the 3 lowest priority symbols
        assert len(plan.symbols_to_replace) == 3
        assert "SYM4" in plan.symbols_to_replace  # 25.0
        assert "SYM2" in plan.symbols_to_replace  # 50.0
        assert "SYM1" in plan.symbols_to_replace  # 100.0
        assert "SYM5" not in plan.symbols_to_replace  # 150.0 (higher)
        assert "SYM3" not in plan.symbols_to_replace  # 200.0 (highest)
