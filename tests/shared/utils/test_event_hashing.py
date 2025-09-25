"""Tests for event hashing utilities."""

import pytest
from unittest.mock import Mock

from the_alchemiser.shared.utils.event_hashing import (
    generate_signal_hash,
    generate_market_snapshot_id,
    _normalize_signals_for_hash,
    _normalize_portfolio_for_hash,
)
from the_alchemiser.shared.value_objects.core_types import Symbol
from the_alchemiser.shared.types import StrategySignal


class TestSignalHashing:
    """Test signal hash generation."""

    def test_generate_signal_hash_deterministic(self):
        """Test that signal hash generation is deterministic."""
        signals_data = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "reasoning": "Test strategy",
                "is_multi_symbol": False,
            }
        }
        
        portfolio_data = {
            "AAPL": 0.5,
            "GOOGL": 0.3,
            "MSFT": 0.2,
        }
        
        # Generate hash multiple times - should be the same
        hash1 = generate_signal_hash(signals_data, portfolio_data)
        hash2 = generate_signal_hash(signals_data, portfolio_data)
        hash3 = generate_signal_hash(signals_data, portfolio_data)
        
        assert hash1 == hash2 == hash3
        assert len(hash1) == 16  # Should be 16 chars
        assert isinstance(hash1, str)

    def test_generate_signal_hash_different_for_different_data(self):
        """Test that different data produces different hashes."""
        signals_data1 = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "reasoning": "Test strategy",
            }
        }
        
        signals_data2 = {
            "DSL": {
                "symbol": "GOOGL",  # Different symbol
                "action": "BUY",
                "reasoning": "Test strategy",
            }
        }
        
        portfolio_data = {"AAPL": 1.0}
        
        hash1 = generate_signal_hash(signals_data1, portfolio_data)
        hash2 = generate_signal_hash(signals_data2, portfolio_data)
        
        assert hash1 != hash2

    def test_generate_signal_hash_ignores_volatile_fields(self):
        """Test that volatile fields don't affect hash."""
        signals_base = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "reasoning": "Test strategy",
            }
        }
        
        signals_with_timestamp = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "reasoning": "Test strategy",
                "timestamp": "2024-01-01T10:00:00",  # Should be ignored
                "id": "12345",  # Should be ignored
            }
        }
        
        portfolio_data = {"AAPL": 1.0}
        
        hash1 = generate_signal_hash(signals_base, portfolio_data)
        hash2 = generate_signal_hash(signals_with_timestamp, portfolio_data)
        
        assert hash1 == hash2

    def test_generate_signal_hash_handles_errors_gracefully(self):
        """Test that errors in hash generation return fallback."""
        # Use non-serializable data to trigger error
        signals_data = {
            "DSL": {
                "symbol": "AAPL",
                "non_serializable": Mock(),  # This should cause JSON error
            }
        }
        
        portfolio_data = {"AAPL": 1.0}
        
        hash_result = generate_signal_hash(signals_data, portfolio_data)
        
        # Should still return a hash (fallback)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16


class TestMarketSnapshotId:
    """Test market snapshot ID generation."""

    def test_generate_market_snapshot_id_deterministic(self):
        """Test that snapshot ID generation is deterministic for same signals."""
        signals = [
            StrategySignal(
                symbol=Symbol("AAPL"),
                action="BUY",
                target_allocation=0.5,
                reasoning="Test",
            ),
            StrategySignal(
                symbol=Symbol("GOOGL"),
                action="BUY",
                target_allocation=0.3,
                reasoning="Test",
            ),
        ]
        
        # Generate multiple times - content hash should be same, but timestamp differs
        id1 = generate_market_snapshot_id(signals)
        id2 = generate_market_snapshot_id(signals)
        
        # Should have same format and content hash part
        assert id1.startswith("market_")
        assert id2.startswith("market_")
        
        # Content hash (last 8 chars) should be the same
        assert id1.split("_")[-1] == id2.split("_")[-1]

    def test_generate_market_snapshot_id_empty_signals(self):
        """Test snapshot ID generation with empty signals."""
        snapshot_id = generate_market_snapshot_id([])
        
        assert snapshot_id.startswith("empty_snapshot_")
        assert len(snapshot_id) > 15  # Should include timestamp

    def test_generate_market_snapshot_id_different_signals(self):
        """Test that different signals produce different content hashes."""
        signals1 = [
            StrategySignal(
                symbol=Symbol("AAPL"),
                action="BUY",
                target_allocation=0.5,
                reasoning="Test",
            ),
        ]
        
        signals2 = [
            StrategySignal(
                symbol=Symbol("GOOGL"),  # Different symbol
                action="BUY",
                target_allocation=0.5,
                reasoning="Test",
            ),
        ]
        
        id1 = generate_market_snapshot_id(signals1)
        id2 = generate_market_snapshot_id(signals2)
        
        # Content hashes should be different
        assert id1.split("_")[-1] != id2.split("_")[-1]

    def test_generate_market_snapshot_id_handles_errors(self):
        """Test error handling in snapshot ID generation."""
        # Create signals that might cause errors
        signals = [Mock()]  # Invalid signal object
        
        snapshot_id = generate_market_snapshot_id(signals)
        
        # Should return fallback
        assert snapshot_id.startswith("snapshot_")


class TestNormalizationFunctions:
    """Test data normalization functions."""

    def test_normalize_signals_for_hash(self):
        """Test signal data normalization."""
        signals_data = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "symbols": ["GOOGL", "AAPL"],  # Should be sorted
                "timestamp": "2024-01-01",  # Should be removed
                "reasoning": "Test",
            }
        }
        
        normalized = _normalize_signals_for_hash(signals_data)
        
        expected = {
            "DSL": {
                "symbol": "AAPL",
                "action": "BUY",
                "symbols": ["AAPL", "GOOGL"],  # Should be sorted
                "reasoning": "Test",
                # timestamp should be removed
            }
        }
        
        assert normalized == expected

    def test_normalize_portfolio_for_hash(self):
        """Test portfolio data normalization."""
        portfolio_data = {
            "GOOGL": 0.3,
            "AAPL": 0.5,
            "MSFT": 0.2,
        }
        
        normalized = _normalize_portfolio_for_hash(portfolio_data)
        
        # Should be sorted by symbol
        expected = {
            "AAPL": 0.5,
            "GOOGL": 0.3,
            "MSFT": 0.2,
        }
        
        assert normalized == expected

    def test_normalize_portfolio_for_hash_complex_object(self):
        """Test portfolio normalization with complex object."""
        portfolio_data = {
            "allocation": {"AAPL": 0.5, "GOOGL": 0.3},
            "timestamp": "2024-01-01",  # Should be removed
            "metadata": {"source": "test"},
        }
        
        normalized = _normalize_portfolio_for_hash(portfolio_data)
        
        # timestamp should be removed, allocation preserved
        assert "timestamp" not in normalized
        assert "allocation" in normalized
        assert "metadata" in normalized