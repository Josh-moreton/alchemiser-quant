"""Test evaluating a more complex Nuclear-style strategy."""

import pytest
from unittest.mock import Mock
import pandas as pd
from decimal import Decimal

from the_alchemiser.domain.dsl.strategy_loader import StrategyLoader
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


def test_nuclear_simple_strategy():
    """Test the simplified Nuclear strategy."""
    # Create mock market data port
    mock_port = Mock(spec=MarketDataPort)
    
    # Mock SPY data with RSI around 75 (between 79 and 81)
    spy_data = pd.DataFrame({
        'close': [100, 103, 106, 109, 112, 115, 118, 121, 124, 127], # Strong uptrend for moderate RSI
        'volume': [1000] * 10
    })
    mock_port.get_data.return_value = spy_data
    mock_port.get_current_price.return_value = 127.0
    
    # Load and evaluate the simplified Nuclear strategy
    strategy_loader = StrategyLoader(mock_port)
    portfolio, trace = strategy_loader.evaluate_strategy_file("test_strategies/nuclear_simple.clj")
    
    # Should produce valid portfolio
    assert isinstance(portfolio, dict)
    assert len(portfolio) > 0
    
    # All weights should sum to 1.0
    total_weight = sum(portfolio.values())
    assert abs(total_weight - Decimal('1.0')) < Decimal('1e-9')
    
    # Should have trace entries for RSI, comparisons, and portfolio construction
    assert len(trace) > 0
    
    # Find RSI calculations
    rsi_traces = [entry for entry in trace if entry["type"] == "indicator" and entry["indicator"] == "rsi"]
    assert len(rsi_traces) >= 1  # At least one RSI calculation
    
    # Find comparisons
    comparison_traces = [entry for entry in trace if entry["type"] == "comparison"]
    assert len(comparison_traces) >= 1  # At least one comparison
    
    # Find conditionals
    conditional_traces = [entry for entry in trace if entry["type"] == "conditional"]
    assert len(conditional_traces) >= 1  # At least one conditional
    
    # Check the decision path makes sense
    for conditional_trace in conditional_traces:
        assert "condition" in conditional_trace
        assert "branch_taken" in conditional_trace
        assert conditional_trace["branch_taken"] in ["then", "else"]
    
    print(f"Strategy produced portfolio: {portfolio}")
    print(f"Total trace entries: {len(trace)}")
    
    # All portfolio weights should be positive
    for symbol, weight in portfolio.items():
        assert weight > 0, f"Weight for {symbol} should be positive, got {weight}"


if __name__ == "__main__":
    test_nuclear_simple_strategy()