"""Integration test for TypedKLMStrategyEngine with the strategy management system."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal


@pytest.fixture
def integration_port() -> Mock:
    """Create a realistic market data port for integration testing."""
    port = Mock(spec=MarketDataPort)
    
    # Create realistic market data for key symbols
    def create_realistic_data(symbol: str) -> pd.DataFrame:
        base_price = {"SPY": 420, "TECL": 45, "BIL": 91, "UVXY": 12, "XLK": 150, "KMLM": 28}.get(symbol, 100)
        
        # 250 days of data with some realistic variation
        prices = []
        current_price = base_price
        for i in range(250):
            # Add some random-ish movement
            change = (i % 7 - 3) * 0.01 * current_price  # Simple pattern
            current_price = max(current_price + change, current_price * 0.95)
            prices.append(current_price)
            
        return pd.DataFrame({
            "Open": [p * 0.995 for p in prices],
            "High": [p * 1.01 for p in prices],
            "Low": [p * 0.99 for p in prices],
            "Close": prices,
            "Volume": [1000000 + (i * 10000) for i in range(250)],
        }, index=pd.date_range("2023-01-01", periods=250, freq="D"))
    
    def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
        if symbol in ["SPY", "TECL", "BIL", "UVXY", "XLK", "KMLM", "TQQQ", "SOXL"]:
            return create_realistic_data(symbol)
        # Return empty for unknown symbols
        return pd.DataFrame()
    
    port.get_data = mock_get_data
    port.get_current_price.return_value = 420.0  # SPY price
    port.get_latest_quote.return_value = (419.5, 420.5)
    
    return port


class TestTypedKLMStrategyEngineIntegration:
    """Integration tests for TypedKLMStrategyEngine."""

    def test_signal_generation_integration(
        self, 
        integration_port: Mock
    ) -> None:
        """Test complete signal generation pipeline with realistic data."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        # Generate signals
        signals = engine.generate_signals(integration_port, timestamp)
        
        # Should generate valid signals
        assert len(signals) > 0
        assert all(isinstance(signal, StrategySignal) for signal in signals)
        
        # All signals should have the same timestamp
        assert all(signal.timestamp == timestamp for signal in signals)
        
        # Validate signal structure
        for signal in signals:
            # Valid action
            assert signal.action in ("BUY", "SELL", "HOLD")
            
            # Valid symbol (string representation should not be empty)
            assert str(signal.symbol).strip() != ""
            
            # Valid confidence (0-1 range)
            assert 0 <= signal.confidence.value <= 1
            
            # Valid allocation (0-1 range)
            assert 0 <= signal.target_allocation.value <= 1
            
            # Reasoning should be informative
            assert len(signal.reasoning) > 10
            assert "KLM" in signal.reasoning or "Ensemble" in signal.reasoning

    def test_strategy_manager_compatibility(
        self,
        integration_port: Mock,
    ) -> None:
        """Test compatibility with strategy manager patterns."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        # Test the legacy interface compatibility (what StrategyManager expects)
        # This simulates how the typed engine would be called in a migration scenario
        
        # 1. Generate signals
        signals = engine.generate_signals(integration_port, timestamp)
        
        # 2. Convert to legacy-compatible format for gradual migration
        legacy_compatible_result = None
        if signals:
            primary_signal = signals[0]  # Take the first/primary signal
            
            # Convert to the tuple format that legacy StrategyManager expects
            legacy_compatible_result = (
                str(primary_signal.symbol),  # symbol_or_allocation  
                primary_signal.action,       # action
                primary_signal.reasoning,    # enhanced_reason
                "TypedKLMEnsemble"          # variant_name
            )
        
        # Verify the legacy format is correct
        assert legacy_compatible_result is not None
        assert len(legacy_compatible_result) == 4
        assert isinstance(legacy_compatible_result[0], str)  # symbol
        assert legacy_compatible_result[1] in ("BUY", "SELL", "HOLD")  # action
        assert isinstance(legacy_compatible_result[2], str)  # reason  
        assert isinstance(legacy_compatible_result[3], str)  # variant

    def test_error_resilience_integration(
        self,
    ) -> None:
        """Test error handling in integration scenarios."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        # Test with port that fails for some symbols
        failing_port = Mock(spec=MarketDataPort)
        
        call_count = 0
        def failing_get_data(symbol: str, **kwargs) -> pd.DataFrame:
            nonlocal call_count
            call_count += 1
            
            # Fail for every other call
            if call_count % 2 == 0:
                raise Exception(f"Network error for {symbol}")
            
            # Return minimal data for successful calls
            return pd.DataFrame({
                "Open": [100.0],
                "High": [105.0],
                "Low": [95.0],
                "Close": [102.0],
                "Volume": [1000],
            }, index=pd.to_datetime(["2023-01-01"]))
        
        failing_port.get_data = failing_get_data
        
        # Should still generate signals (graceful degradation)
        signals = engine.generate_signals(failing_port, timestamp)
        
        # Should return at least a hold signal
        assert len(signals) >= 1
        
        # At least one signal should be present
        for signal in signals:
            assert isinstance(signal, StrategySignal)
            assert signal.timestamp == timestamp

    def test_performance_characteristics(
        self,
        integration_port: Mock,
    ) -> None:
        """Test performance characteristics for integration."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        import time
        
        # Measure signal generation time
        start_time = time.time()
        signals = engine.generate_signals(integration_port, timestamp)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds for integration test)
        assert execution_time < 5.0, f"Signal generation took {execution_time:.2f}s, expected < 5s"
        
        # Should return results
        assert len(signals) > 0
        
        # Log performance for monitoring
        print(f"Signal generation completed in {execution_time:.3f}s with {len(signals)} signals")

    def test_multi_asset_allocation_integration(
        self,
        integration_port: Mock,
    ) -> None:
        """Test multi-asset allocation scenarios."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        signals = engine.generate_signals(integration_port, timestamp)
        
        # Check if we have multi-asset allocation (more than one signal)
        if len(signals) > 1:
            # Verify allocations sum to reasonable total (within 100%)
            total_allocation = sum(signal.target_allocation.value for signal in signals)
            assert total_allocation <= 1.0, f"Total allocation {total_allocation} exceeds 100%"
            
            # Each signal should have distinct symbols
            symbols = [str(signal.symbol) for signal in signals]
            assert len(symbols) == len(set(symbols)), "Duplicate symbols in allocation"
            
        # Single asset case
        elif len(signals) == 1:
            signal = signals[0]
            # For single asset, allocation should be 0 (HOLD) or 1 (full allocation)
            assert signal.target_allocation.value in [0.0, 1.0] or 0 < signal.target_allocation.value <= 1.0

    def test_signal_reasoning_quality(
        self,
        integration_port: Mock,
    ) -> None:
        """Test the quality and informativeness of signal reasoning."""
        engine = TypedKLMStrategyEngine()
        timestamp = datetime(2023, 12, 15, 10, 30, 0, tzinfo=UTC)
        
        signals = engine.generate_signals(integration_port, timestamp)
        
        for signal in signals:
            reasoning = signal.reasoning
            
            # Should contain key information
            assert "KLM" in reasoning or "Ensemble" in reasoning
            
            # Should be reasonably detailed (more than just a few words)
            assert len(reasoning.split()) >= 3, f"Reasoning too brief: {reasoning}"
            
            # Should not contain error messages in normal operation (unless it's a hold signal with valid reason)
            if "Error" in reasoning or "Failed" in reasoning:
                # If there are errors, it should be a HOLD signal
                assert signal.action == "HOLD", f"Error reasoning should result in HOLD signal: {reasoning}"
                
            # For non-error signals, action should be reflected in context
            if not any(word in reasoning for word in ["Error", "Failed", "No indicators", "No market data"]):
                assert signal.action in reasoning or signal.action.lower() in reasoning.lower()