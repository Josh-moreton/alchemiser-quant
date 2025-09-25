"""Tests for portfolio idempotency store."""

import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch

from the_alchemiser.shared.persistence.portfolio_idempotency_store import (
    PortfolioIdempotencyStore,
    get_portfolio_idempotency_store,
)


class TestPortfolioIdempotencyStore:
    """Test portfolio idempotency store functionality."""

    def test_init_with_default_persistence_handler(self):
        """Test initialization with default persistence handler."""
        store = PortfolioIdempotencyStore()
        
        assert store._max_cache_entries == 500  # Default value
        assert store._cache_file == "portfolio_idempotency_cache.json"
        assert store._persistence_handler is not None

    def test_init_with_custom_persistence_handler(self):
        """Test initialization with custom persistence handler."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(
            persistence_handler=mock_handler,
            max_cache_entries=100,
        )
        
        assert store._max_cache_entries == 100
        assert store._persistence_handler is mock_handler

    def test_has_plan_hash_not_exists(self):
        """Test checking for non-existent plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        result = store.has_plan_hash("test_hash", "test_correlation")
        
        assert result is False

    def test_has_plan_hash_exists_not_expired(self):
        """Test checking for existing, non-expired plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Add entry to cache
        current_time = datetime.now(UTC)
        cache_key = "test_correlation:test_hash"
        store._cache[cache_key] = {
            "plan_hash": "test_hash",
            "correlation_id": "test_correlation",
            "created_at": current_time.isoformat(),
        }
        
        result = store.has_plan_hash("test_hash", "test_correlation")
        
        assert result is True

    def test_has_plan_hash_exists_expired(self):
        """Test checking for existing but expired plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Add expired entry to cache
        expired_time = datetime.now(UTC) - timedelta(hours=7)  # Expired (>6 hours)
        cache_key = "test_correlation:test_hash"
        store._cache[cache_key] = {
            "plan_hash": "test_hash",
            "correlation_id": "test_correlation",
            "created_at": expired_time.isoformat(),
        }
        
        result = store.has_plan_hash("test_hash", "test_correlation")
        
        assert result is False
        # Entry should be removed from cache
        assert cache_key not in store._cache

    def test_store_plan_hash(self):
        """Test storing plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        mock_handler.write_text.return_value = True
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        store.store_plan_hash(
            plan_hash="test_hash",
            correlation_id="test_correlation",
            causation_id="test_causation",
            account_snapshot_id="test_snapshot",
            metadata={"test": "value"},
        )
        
        cache_key = "test_correlation:test_hash"
        assert cache_key in store._cache
        
        entry = store._cache[cache_key]
        assert entry["plan_hash"] == "test_hash"
        assert entry["correlation_id"] == "test_correlation"
        assert entry["causation_id"] == "test_causation"
        assert entry["account_snapshot_id"] == "test_snapshot"
        assert entry["metadata"] == {"test": "value"}
        assert "created_at" in entry
        
        # Should have called persistence
        mock_handler.write_text.assert_called_once()

    def test_store_plan_hash_trims_cache_when_full(self):
        """Test that cache is trimmed when it exceeds max entries."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        mock_handler.write_text.return_value = True
        
        store = PortfolioIdempotencyStore(
            persistence_handler=mock_handler,
            max_cache_entries=2,  # Small cache for testing
        )
        
        # Add entries up to the limit
        store.store_plan_hash("hash1", "corr1")
        store.store_plan_hash("hash2", "corr2")
        
        assert len(store._cache) == 2
        
        # Add one more - should trigger trimming
        store.store_plan_hash("hash3", "corr3")
        
        # Should still be at max size
        assert len(store._cache) == 2

    def test_get_plan_metadata_exists(self):
        """Test getting metadata for existing plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Add entry to cache
        current_time = datetime.now(UTC)
        cache_key = "test_correlation:test_hash"
        test_entry = {
            "plan_hash": "test_hash",
            "correlation_id": "test_correlation",
            "created_at": current_time.isoformat(),
            "metadata": {"test": "value"},
        }
        store._cache[cache_key] = test_entry
        
        result = store.get_plan_metadata("test_hash", "test_correlation")
        
        assert result == test_entry

    def test_get_plan_metadata_not_exists(self):
        """Test getting metadata for non-existent plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        result = store.get_plan_metadata("test_hash", "test_correlation")
        
        assert result is None

    def test_get_plan_metadata_expired(self):
        """Test getting metadata for expired plan hash."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Add expired entry to cache
        expired_time = datetime.now(UTC) - timedelta(hours=7)  # Expired
        cache_key = "test_correlation:test_hash"
        store._cache[cache_key] = {
            "plan_hash": "test_hash",
            "correlation_id": "test_correlation",
            "created_at": expired_time.isoformat(),
        }
        
        result = store.get_plan_metadata("test_hash", "test_correlation")
        
        assert result is None
        # Entry should be removed from cache
        assert cache_key not in store._cache

    def test_clear_expired_entries(self):
        """Test clearing expired entries from cache."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        mock_handler.write_text.return_value = True
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        current_time = datetime.now(UTC)
        expired_time = current_time - timedelta(hours=7)  # Expired
        
        # Add mix of expired and non-expired entries
        store._cache = {
            "corr1:hash1": {
                "created_at": current_time.isoformat(),  # Not expired
            },
            "corr2:hash2": {
                "created_at": expired_time.isoformat(),  # Expired
            },
            "corr3:hash3": {
                "created_at": current_time.isoformat(),  # Not expired
            },
            "corr4:hash4": {
                "created_at": "invalid_date",  # Invalid date - should be expired
            },
        }
        
        removed_count = store.clear_expired_entries()
        
        assert removed_count == 2  # Two expired entries
        assert len(store._cache) == 2  # Two remaining entries
        assert "corr1:hash1" in store._cache
        assert "corr3:hash3" in store._cache
        assert "corr2:hash2" not in store._cache
        assert "corr4:hash4" not in store._cache
        
        # Should have saved cache after clearing
        mock_handler.write_text.assert_called()

    def test_load_cache_file_exists(self):
        """Test loading cache from existing file."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = True
        mock_handler.read_text.return_value = '{"test_key": {"test": "value"}}'
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Cache should be loaded
        assert "test_key" in store._cache
        assert store._cache["test_key"] == {"test": "value"}

    def test_load_cache_file_not_exists(self):
        """Test loading cache when file doesn't exist."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Cache should be empty
        assert len(store._cache) == 0

    def test_load_cache_error_handling(self):
        """Test error handling during cache loading."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = True
        mock_handler.read_text.side_effect = Exception("File read error")
        
        # Should not raise exception
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Cache should be empty due to error
        assert len(store._cache) == 0

    def test_save_cache(self):
        """Test saving cache to persistence."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        mock_handler.write_text.return_value = True
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Add entry to cache
        store._cache["test_key"] = {"test": "value"}
        
        # Save cache
        store._save_cache()
        
        # Should have called write_text with JSON content
        mock_handler.write_text.assert_called()
        args, kwargs = mock_handler.write_text.call_args
        assert args[0] == "portfolio_idempotency_cache.json"
        assert "test_key" in args[1]  # JSON content should contain the key

    def test_save_cache_error_handling(self):
        """Test error handling during cache saving."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        mock_handler.write_text.side_effect = Exception("Write error")
        
        store = PortfolioIdempotencyStore(persistence_handler=mock_handler)
        
        # Should not raise exception
        store._save_cache()

    def test_trim_cache(self):
        """Test cache trimming functionality."""
        mock_handler = Mock()
        mock_handler.file_exists.return_value = False
        
        store = PortfolioIdempotencyStore(
            persistence_handler=mock_handler,
            max_cache_entries=3,
        )
        
        # Add entries with different timestamps
        current_time = datetime.now(UTC)
        times = [
            current_time - timedelta(hours=3),  # Oldest
            current_time - timedelta(hours=2),  # Middle
            current_time - timedelta(hours=1),  # Newest
            current_time,  # Most recent
        ]
        
        for i, time in enumerate(times):
            store._cache[f"key{i}"] = {
                "created_at": time.isoformat(),
            }
        
        # Trim cache
        store._trim_cache()
        
        # Should keep only the most recent entries
        assert len(store._cache) == 3
        
        # Should keep the most recent entries (key1, key2, key3)
        remaining_keys = set(store._cache.keys())
        assert "key3" in remaining_keys  # Most recent
        assert "key2" in remaining_keys  # Second most recent
        assert "key1" in remaining_keys  # Third most recent
        assert "key0" not in remaining_keys  # Oldest - should be removed


class TestGetPortfolioIdempotencyStore:
    """Test global store instance."""

    def test_get_portfolio_idempotency_store_singleton(self):
        """Test that the same instance is returned."""
        # Clear any existing instance first
        from the_alchemiser.shared.persistence import portfolio_idempotency_store
        portfolio_idempotency_store._portfolio_store = None
        
        store1 = get_portfolio_idempotency_store()
        store2 = get_portfolio_idempotency_store()
        
        assert store1 is store2
        assert isinstance(store1, PortfolioIdempotencyStore)

    def test_get_portfolio_idempotency_store_creates_instance(self):
        """Test that instance is created if not exists."""
        # Clear any existing instance first
        from the_alchemiser.shared.persistence import portfolio_idempotency_store
        portfolio_idempotency_store._portfolio_store = None
        
        store = get_portfolio_idempotency_store()
        
        assert isinstance(store, PortfolioIdempotencyStore)
        assert store is not None