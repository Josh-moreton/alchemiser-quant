"""Business Unit: shared | Status: current.

Comprehensive tests for RealTimePriceStore utility.

Tests cover:
- Thread-safety of storage operations
- Input validation and error handling
- Data update and retrieval operations
- Price priority logic
- Spread validation
- Cleanup operations
- Statistics tracking
- Staleness detection
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from the_alchemiser.shared.services.real_time_price_store import RealTimePriceStore


class TestRealTimePriceStoreInitialization:
    """Test RealTimePriceStore initialization."""

    def test_initialization_with_defaults(self):
        """Test that store initializes with default parameters."""
        store = RealTimePriceStore()
        assert store._cleanup_interval == 60
        assert store._max_quote_age == 300
        assert len(store._quotes) == 0
        assert len(store._price_data) == 0
        assert len(store._quote_data) == 0

    def test_initialization_with_custom_params(self):
        """Test that store initializes with custom parameters."""
        store = RealTimePriceStore(cleanup_interval=30, max_quote_age=120)
        assert store._cleanup_interval == 30
        assert store._max_quote_age == 120

    def test_initialization_validates_positive_cleanup_interval(self):
        """Test that negative cleanup_interval raises ValueError."""
        with pytest.raises(ValueError, match="cleanup_interval must be positive"):
            RealTimePriceStore(cleanup_interval=0)

        with pytest.raises(ValueError, match="cleanup_interval must be positive"):
            RealTimePriceStore(cleanup_interval=-10)

    def test_initialization_validates_positive_max_quote_age(self):
        """Test that negative max_quote_age raises ValueError."""
        with pytest.raises(ValueError, match="max_quote_age must be positive"):
            RealTimePriceStore(max_quote_age=0)

        with pytest.raises(ValueError, match="max_quote_age must be positive"):
            RealTimePriceStore(max_quote_age=-100)


class TestRealTimePriceStoreQuoteUpdates:
    """Test quote data update operations."""

    def test_update_quote_data_basic(self):
        """Test basic quote data update."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_quote_data(
            symbol="AAPL",
            bid_price=150.0,
            ask_price=150.5,
            bid_size=100.0,
            ask_size=200.0,
            timestamp=timestamp,
        )

        # Check QuoteModel storage
        quote_data = store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.symbol == "AAPL"
        assert quote_data.bid_price == Decimal("150.0")
        assert quote_data.ask_price == Decimal("150.5")
        assert quote_data.bid_size == Decimal("100.0")
        assert quote_data.ask_size == Decimal("200.0")

    def test_update_quote_data_validates_empty_symbol(self):
        """Test that empty symbol raises ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            store.update_quote_data("", 150.0, 150.5, 100.0, 200.0, timestamp)

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            store.update_quote_data("   ", 150.0, 150.5, 100.0, 200.0, timestamp)

    def test_update_quote_data_validates_negative_bid(self):
        """Test that negative bid price raises ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Bid price cannot be negative"):
            store.update_quote_data("AAPL", -1.0, 150.5, 100.0, 200.0, timestamp)

    def test_update_quote_data_validates_negative_ask(self):
        """Test that negative ask price raises ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Ask price cannot be negative"):
            store.update_quote_data("AAPL", 150.0, -1.0, 100.0, 200.0, timestamp)

    def test_update_quote_data_validates_negative_sizes(self):
        """Test that negative sizes raise ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Bid size cannot be negative"):
            store.update_quote_data("AAPL", 150.0, 150.5, -10.0, 200.0, timestamp)

        with pytest.raises(ValueError, match="Ask size cannot be negative"):
            store.update_quote_data("AAPL", 150.0, 150.5, 100.0, -20.0, timestamp)

    def test_update_quote_data_validates_timezone_aware(self):
        """Test that naive timestamp raises ValueError."""
        store = RealTimePriceStore()
        naive_timestamp = datetime.now()  # No timezone

        with pytest.raises(ValueError, match="Timestamp must be timezone-aware"):
            store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, naive_timestamp)

    def test_update_quote_data_accepts_none_sizes(self):
        """Test that None sizes are converted to Decimal zero."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_quote_data(
            symbol="AAPL",
            bid_price=150.0,
            ask_price=150.5,
            bid_size=None,
            ask_size=None,
            timestamp=timestamp,
        )

        quote_data = store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_size == Decimal("0.0")
        assert quote_data.ask_size == Decimal("0.0")


class TestRealTimePriceStoreTradeUpdates:
    """Test trade data update operations."""

    def test_update_trade_data_basic(self):
        """Test basic trade data update."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_trade_data(
            symbol="AAPL",
            price=151.0,
            timestamp=timestamp,
            volume=1000,
        )

        # Check PriceDataModel storage
        price_data = store.get_price_data("AAPL")
        assert price_data is not None
        assert price_data.symbol == "AAPL"
        assert price_data.price == Decimal("151.0")
        assert price_data.volume == 1000

    def test_update_trade_data_validates_empty_symbol(self):
        """Test that empty symbol raises ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            store.update_trade_data("", 151.0, timestamp, 1000)

    def test_update_trade_data_validates_positive_price(self):
        """Test that non-positive price raises ValueError."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        with pytest.raises(ValueError, match="Trade price must be positive"):
            store.update_trade_data("AAPL", 0.0, timestamp, 1000)

        with pytest.raises(ValueError, match="Trade price must be positive"):
            store.update_trade_data("AAPL", -10.0, timestamp, 1000)

        with pytest.raises(ValueError, match="Trade price must be positive"):
            store.update_trade_data("AAPL", None, timestamp, 1000)

    def test_update_trade_data_validates_timezone_aware(self):
        """Test that naive timestamp raises ValueError."""
        store = RealTimePriceStore()
        naive_timestamp = datetime.now()  # No timezone

        with pytest.raises(ValueError, match="Timestamp must be timezone-aware"):
            store.update_trade_data("AAPL", 151.0, naive_timestamp, 1000)

    def test_update_trade_data_accepts_none_volume(self):
        """Test that None volume is accepted."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_trade_data(
            symbol="AAPL",
            price=151.0,
            timestamp=timestamp,
            volume=None,
        )

        price_data = store.get_price_data("AAPL")
        assert price_data is not None
        assert price_data.volume is None

    def test_update_trade_data_merges_with_quote(self):
        """Test that trade update preserves existing quote data."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # First add quote data
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)

        # Then add trade data
        store.update_trade_data("AAPL", 150.25, timestamp, 1000)

        # Verify both exist
        quote_data = store.get_quote_data("AAPL")
        price_data = store.get_price_data("AAPL")

        assert quote_data is not None
        assert price_data is not None
        assert price_data.price == Decimal("150.25")
        assert price_data.bid == quote_data.bid_price
        assert price_data.ask == quote_data.ask_price


class TestRealTimePriceStoreRetrieval:
    """Test data retrieval operations."""

    def test_get_real_time_price_priority_mid_price(self):
        """Test that mid-price is preferred when bid/ask available."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_quote_data("AAPL", 150.0, 151.0, 100.0, 200.0, timestamp)

        price = store.get_real_time_price("AAPL")
        assert price == Decimal("150.5")  # Mid-price

    def test_get_real_time_price_fallback_to_trade(self):
        """Test fallback to last trade price when no quote."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_trade_data("AAPL", 150.25, timestamp, 1000)

        price = store.get_real_time_price("AAPL")
        assert price == Decimal("150.25")

    def test_get_real_time_price_fallback_to_bid(self):
        """Test fallback to bid when no ask or trade."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # Simulate partial quote (bid only)
        store.update_quote_data("AAPL", 150.0, 0.0, 100.0, 0.0, timestamp)

        price = store.get_real_time_price("AAPL")
        assert price == Decimal("150.0")

    def test_get_real_time_price_fallback_to_ask(self):
        """Test fallback to ask when no bid or trade."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # Simulate partial quote (ask only)
        store.update_quote_data("AAPL", 0.0, 151.0, 0.0, 200.0, timestamp)

        price = store.get_real_time_price("AAPL")
        assert price == Decimal("151.0")

    def test_get_real_time_price_returns_none_when_missing(self):
        """Test that None is returned for missing symbol."""
        store = RealTimePriceStore()

        price = store.get_real_time_price("UNKNOWN")
        assert price is None

    def test_get_bid_ask_spread_valid(self):
        """Test bid/ask spread retrieval."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)

        spread = store.get_bid_ask_spread("AAPL")
        assert spread is not None
        bid, ask = spread
        assert bid == Decimal("150.0")
        assert ask == Decimal("150.5")

    def test_get_bid_ask_spread_rejects_inverted(self):
        """Test that inverted spread (ask <= bid) returns None."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # Create inverted spread
        store.update_quote_data("AAPL", 151.0, 150.0, 100.0, 200.0, timestamp)

        spread = store.get_bid_ask_spread("AAPL")
        assert spread is None  # Should reject inverted spread

    def test_get_bid_ask_spread_returns_none_when_missing(self):
        """Test that None is returned for missing symbol."""
        store = RealTimePriceStore()

        spread = store.get_bid_ask_spread("UNKNOWN")
        assert spread is None


class TestRealTimePriceStoreOptimizedPrice:
    """Test optimized price for order placement."""

    def test_get_optimized_price_for_order_immediate(self):
        """Test immediate price return when data is recent."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # Add recent data
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)

        callback_called = []

        def subscribe_callback(symbol: str):
            callback_called.append(symbol)

        # Should return immediately since data is very recent
        price = store.get_optimized_price_for_order("AAPL", subscribe_callback, max_wait=0.5)

        assert price == Decimal("150.25")  # Mid-price
        assert callback_called == ["AAPL"]  # Callback was called

    def test_get_optimized_price_for_order_waits_for_data(self):
        """Test that method waits for data if not available."""
        store = RealTimePriceStore()

        callback_called = []

        def subscribe_callback(symbol: str):
            callback_called.append(symbol)
            # Simulate delayed data arrival
            threading.Timer(
                0.1,
                lambda: store.update_quote_data(
                    "AAPL", 150.0, 150.5, 100.0, 200.0, datetime.now(UTC)
                ),
            ).start()

        start = time.time()
        price = store.get_optimized_price_for_order("AAPL", subscribe_callback, max_wait=0.5)
        elapsed = time.time() - start

        assert price == Decimal("150.25")  # Got data
        assert elapsed < 0.5  # Didn't wait full timeout
        assert elapsed >= 0.1  # But did wait for data

    def test_get_optimized_price_for_order_timeout(self):
        """Test that method times out if no data arrives."""
        store = RealTimePriceStore()

        def subscribe_callback(symbol: str):
            pass  # No data will arrive

        start = time.time()
        price = store.get_optimized_price_for_order("UNKNOWN", subscribe_callback, max_wait=0.2)
        elapsed = time.time() - start

        assert price is None  # No data
        assert elapsed >= 0.2  # Waited full timeout


class TestRealTimePriceStoreStats:
    """Test statistics tracking."""

    def test_get_stats_empty(self):
        """Test stats for empty store."""
        store = RealTimePriceStore()
        stats = store.get_stats()

        assert stats["symbols_tracked"] == 0
        assert stats["symbols_tracked_structured_prices"] == 0
        assert stats["symbols_tracked_structured_quotes"] == 0

    def test_get_stats_with_data(self):
        """Test stats with stored data."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)
        store.update_trade_data("MSFT", 250.0, timestamp, 500)

        stats = store.get_stats()

        assert stats["symbols_tracked"] == 2
        assert stats["symbols_tracked_structured_quotes"] == 1  # Only AAPL
        assert stats["symbols_tracked_structured_prices"] == 1  # Only MSFT


class TestRealTimePriceStoreStaleness:
    """Test staleness detection."""

    def test_has_recent_data_true(self):
        """Test recent data detection."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        store.update_trade_data("AAPL", 150.0, timestamp, 1000)

        assert store.has_recent_data("AAPL", max_age_seconds=1.0) is True

    def test_has_recent_data_false_old(self):
        """Test stale data detection."""
        store = RealTimePriceStore()
        old_timestamp = datetime.now(UTC) - timedelta(seconds=10)

        # Manually set old update time
        store._last_update["AAPL"] = old_timestamp

        assert store.has_recent_data("AAPL", max_age_seconds=1.0) is False

    def test_has_recent_data_false_missing(self):
        """Test missing data detection."""
        store = RealTimePriceStore()

        assert store.has_recent_data("UNKNOWN", max_age_seconds=1.0) is False


class TestRealTimePriceStoreCleanup:
    """Test cleanup operations."""

    def test_start_cleanup_idempotent(self):
        """Test that starting cleanup twice is safe."""
        store = RealTimePriceStore()

        def is_connected():
            return True

        store.start_cleanup(is_connected)
        thread1 = store._cleanup_thread

        store.start_cleanup(is_connected)
        thread2 = store._cleanup_thread

        assert thread1 is thread2  # Same thread

        store.stop_cleanup()

    def test_cleanup_removes_old_quotes(self):
        """Test that cleanup removes stale data."""
        store = RealTimePriceStore(cleanup_interval=1, max_quote_age=2)
        timestamp = datetime.now(UTC)

        # Add data
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)

        # Set old timestamp
        store._last_update["AAPL"] = datetime.now(UTC) - timedelta(seconds=10)

        def is_connected():
            return True

        store.start_cleanup(is_connected)

        # Wait for cleanup cycle
        time.sleep(2)

        # Data should be removed
        assert store.get_quote_data("AAPL") is None

        store.stop_cleanup()

    def test_cleanup_preserves_recent_quotes(self):
        """Test that cleanup preserves recent data."""
        store = RealTimePriceStore(cleanup_interval=1, max_quote_age=60)
        timestamp = datetime.now(UTC)

        # Add recent data
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)
        store._last_update["AAPL"] = datetime.now(UTC)  # Very recent

        def is_connected():
            return True

        store.start_cleanup(is_connected)

        # Wait for cleanup cycle
        time.sleep(2)

        # Data should still be there
        assert store.get_quote_data("AAPL") is not None

        store.stop_cleanup()

    def test_cleanup_skips_when_disconnected(self):
        """Test that cleanup skips when disconnected."""
        store = RealTimePriceStore(cleanup_interval=1, max_quote_age=2)
        timestamp = datetime.now(UTC)

        # Add data with old timestamp
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)
        store._last_update["AAPL"] = datetime.now(UTC) - timedelta(seconds=10)

        def is_connected():
            return False  # Always disconnected

        store.start_cleanup(is_connected)

        # Wait for cleanup cycle
        time.sleep(2)

        # Data should still be there (cleanup skipped)
        assert store.get_quote_data("AAPL") is not None

        store.stop_cleanup()


class TestRealTimePriceStoreThreadSafety:
    """Test thread safety of price store operations."""

    def test_concurrent_quote_updates_same_symbol(self):
        """Test that concurrent updates to same symbol are thread-safe."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)
        results = []

        def update_quote(bid: float):
            try:
                store.update_quote_data(
                    "AAPL",
                    bid_price=bid,
                    ask_price=bid + 0.5,
                    bid_size=100.0,
                    ask_size=200.0,
                    timestamp=timestamp,
                )
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        threads = [threading.Thread(target=update_quote, args=(150.0 + i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 10
        assert all(r == "success" for r in results)

        # Should have one quote (last update wins)
        quote = store.get_quote_data("AAPL")
        assert quote is not None

    def test_concurrent_updates_different_symbols(self):
        """Test that concurrent updates to different symbols are thread-safe."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)
        results = []

        def update_symbol(symbol: str):
            try:
                store.update_quote_data(
                    symbol,
                    bid_price=150.0,
                    ask_price=150.5,
                    bid_size=100.0,
                    ask_size=200.0,
                    timestamp=timestamp,
                )
                results.append(symbol)
            except Exception as e:
                results.append(f"error: {e}")

        symbols = [f"SYM{i}" for i in range(20)]
        threads = [threading.Thread(target=update_symbol, args=(s,)) for s in symbols]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 20
        assert all(r.startswith("SYM") for r in results)

        # Should have all symbols
        stats = store.get_stats()
        assert stats["symbols_tracked_structured_quotes"] == 20

    def test_concurrent_read_write(self):
        """Test that concurrent reads and writes are thread-safe."""
        store = RealTimePriceStore()
        timestamp = datetime.now(UTC)

        # Pre-populate
        store.update_quote_data("AAPL", 150.0, 150.5, 100.0, 200.0, timestamp)

        read_results = []
        write_count = [0]

        def read_price():
            for _ in range(100):
                price = store.get_real_time_price("AAPL")
                read_results.append(price)
                time.sleep(0.001)

        def write_price():
            for i in range(50):
                store.update_quote_data(
                    "AAPL",
                    bid_price=150.0 + i * 0.1,
                    ask_price=150.5 + i * 0.1,
                    bid_size=100.0,
                    ask_size=200.0,
                    timestamp=timestamp,
                )
                write_count[0] += 1
                time.sleep(0.001)

        readers = [threading.Thread(target=read_price) for _ in range(3)]
        writers = [threading.Thread(target=write_price) for _ in range(2)]

        for thread in readers + writers:
            thread.start()
        for thread in readers + writers:
            thread.join()

        # All reads should return valid prices (not None, not corrupt)
        assert len(read_results) == 300
        assert all(isinstance(p, Decimal) for p in read_results)
        assert write_count[0] == 100
