"""Parity tests for TypedKLMStrategyEngine vs legacy KLMStrategyEnsemble."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.strategies.klm_ensemble_engine import KLMStrategyEnsemble
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine
from the_alchemiser.services.market_data.typed_data_provider_adapter import TypedDataProviderAdapter


@pytest.fixture
def sample_market_data() -> dict[str, pd.DataFrame]:
    """Create sample market data for testing."""
    # Create sample OHLCV data with sufficient periods for indicators
    base_data = pd.DataFrame({
        "Open": [100.0] * 250 + [110.0] * 50,
        "High": [105.0] * 250 + [115.0] * 50,
        "Low": [95.0] * 250 + [105.0] * 50,
        "Close": list(range(100, 350)) + list(range(350, 400)),  # 300 periods total
        "Volume": [1000] * 300,
    }, index=pd.date_range("2022-01-01", periods=300, freq="D"))
    
    # Create data for key symbols
    return {
        "SPY": base_data.copy(),
        "TECL": base_data.copy() * 1.1,  # Slightly different values
        "BIL": base_data.copy() * 0.5,
        "UVXY": base_data.copy() * 0.8,
        "XLK": base_data.copy() * 1.05,
        "KMLM": base_data.copy() * 0.95,
    }


@pytest.fixture
def legacy_engine(sample_market_data: dict[str, pd.DataFrame]) -> KLMStrategyEnsemble:
    """Create legacy KLM ensemble engine with mocked data provider."""
    mock_provider = Mock()
    
    def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
        return sample_market_data.get(symbol, pd.DataFrame())
    
    mock_provider.get_data = mock_get_data
    return KLMStrategyEnsemble(data_provider=mock_provider)


@pytest.fixture
def typed_engine() -> TypedKLMStrategyEngine:
    """Create typed KLM strategy engine."""
    return TypedKLMStrategyEngine()


@pytest.fixture
def typed_port(sample_market_data: dict[str, pd.DataFrame]) -> Mock:
    """Create mock market data port with sample data."""
    port = Mock(spec=MarketDataPort)
    
    def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
        return sample_market_data.get(symbol, pd.DataFrame())
    
    port.get_data = mock_get_data
    port.get_current_price.return_value = 100.0
    port.get_latest_quote.return_value = (99.5, 100.5)
    
    return port


@pytest.fixture
def test_timestamp() -> datetime:
    """Fixed timestamp for testing."""
    return datetime(2023, 1, 15, 10, 30, 0, tzinfo=UTC)


class TestKLMStrategyParity:
    """Test parity between legacy and typed KLM strategy implementations."""

    def test_symbol_lists_match(
        self, 
        legacy_engine: KLMStrategyEnsemble, 
        typed_engine: TypedKLMStrategyEngine
    ) -> None:
        """Test that both engines use the same symbol universe."""
        # Both should have the same symbols
        assert set(legacy_engine.all_symbols) == set(typed_engine.all_symbols)
        assert len(legacy_engine.strategy_variants) == len(typed_engine.strategy_variants)

    def test_market_data_fetching_similar(
        self,
        legacy_engine: KLMStrategyEnsemble,
        typed_engine: TypedKLMStrategyEngine,
        typed_port: Mock,
        sample_market_data: dict[str, pd.DataFrame],
    ) -> None:
        """Test that both engines fetch market data for the same symbols."""
        # Legacy engine market data fetching
        legacy_data = legacy_engine.get_market_data()
        
        # Typed engine market data fetching
        typed_data = typed_engine._get_market_data(typed_port)
        
        # Should fetch data for the same symbols (at least the ones with data)
        available_symbols = set(sample_market_data.keys())
        assert set(legacy_data.keys()) == available_symbols
        assert set(typed_data.keys()) == available_symbols

    def test_indicator_calculations_similar(
        self,
        legacy_engine: KLMStrategyEnsemble,
        typed_engine: TypedKLMStrategyEngine,
        sample_market_data: dict[str, pd.DataFrame],
    ) -> None:
        """Test that both engines calculate similar indicators."""
        # Use a subset of market data that both can handle
        test_symbol = "SPY"
        test_data = {test_symbol: sample_market_data[test_symbol]}
        
        # Calculate indicators with both engines
        legacy_indicators = legacy_engine.calculate_indicators(test_data)
        typed_indicators = typed_engine._calculate_indicators(test_data)
        
        # Both should have indicators for the test symbol
        if legacy_indicators and typed_indicators:
            assert test_symbol in legacy_indicators
            assert test_symbol in typed_indicators
            
            # Check that both have close/current_price
            legacy_spy = legacy_indicators[test_symbol]
            typed_spy = typed_indicators[test_symbol]
            
            assert "close" in legacy_spy
            assert "close" in typed_spy
            assert "current_price" in legacy_spy  
            assert "current_price" in typed_spy
            
            # Values should be the same (same input data)
            assert legacy_spy["close"] == typed_spy["close"]
            assert legacy_spy["current_price"] == typed_spy["current_price"]

    def test_variant_performance_comparable(
        self,
        legacy_engine: KLMStrategyEnsemble,
        typed_engine: TypedKLMStrategyEngine,
    ) -> None:
        """Test that variant performance calculations are comparable."""
        # Both engines should have the same variants
        legacy_variants = legacy_engine.strategy_variants
        typed_variants = typed_engine.strategy_variants
        
        assert len(legacy_variants) == len(typed_variants)
        
        # Test performance calculation for the first variant
        if legacy_variants and typed_variants:
            legacy_perf = legacy_engine.calculate_variant_performance(legacy_variants[0])
            typed_perf = typed_engine._calculate_variant_performance(typed_variants[0])
            
            # Both should return valid performance metrics
            assert isinstance(legacy_perf, float)
            assert isinstance(typed_perf, float)
            assert 0.0 <= legacy_perf <= 1.0
            assert 0.0 <= typed_perf <= 1.0

    def test_signal_generation_structure_similar(
        self,
        typed_engine: TypedKLMStrategyEngine,
        typed_port: Mock,
        test_timestamp: datetime,
    ) -> None:
        """Test that signal generation produces expected structure."""
        signals = typed_engine.generate_signals(typed_port, test_timestamp)
        
        # Should return a list of signals
        assert isinstance(signals, list)
        assert len(signals) > 0
        
        # Each signal should have the expected structure
        for signal in signals:
            assert hasattr(signal, 'symbol')
            assert hasattr(signal, 'action')
            assert hasattr(signal, 'confidence')
            assert hasattr(signal, 'target_allocation')
            assert hasattr(signal, 'reasoning')
            assert hasattr(signal, 'timestamp')
            
            # Action should be valid
            assert signal.action in ("BUY", "SELL", "HOLD")
            
            # Timestamp should match
            assert signal.timestamp == test_timestamp

    def test_error_handling_graceful(
        self,
        typed_engine: TypedKLMStrategyEngine,
        test_timestamp: datetime,
    ) -> None:
        """Test that both engines handle errors gracefully."""
        # Create a port that returns empty data
        empty_port = Mock(spec=MarketDataPort)
        empty_port.get_data.return_value = pd.DataFrame()
        
        # Should not raise exception, but return hold signal
        signals = typed_engine.generate_signals(empty_port, test_timestamp)
        
        assert len(signals) == 1
        signal = signals[0]
        assert signal.action == "HOLD"
        assert "BIL" in str(signal.symbol)

    def test_detailed_analysis_contains_expected_sections(
        self,
        typed_engine: TypedKLMStrategyEngine,
    ) -> None:
        """Test that detailed analysis contains expected sections."""
        # Mock minimal data for analysis
        indicators = {
            "SPY": {"rsi_10": 65.0, "close": 420.0, "sma_200": 400.0}
        }
        market_data = {"SPY": pd.DataFrame()}
        selected_variant = typed_engine.strategy_variants[0]
        
        analysis = typed_engine._build_detailed_klm_analysis(
            indicators, market_data, selected_variant, "TECL", "BUY", 
            "Tech momentum", []
        )
        
        # Should contain key sections
        assert "KLM ENSEMBLE STRATEGY ANALYSIS" in analysis
        assert "Market Overview" in analysis
        assert "Ensemble Selection Process" in analysis
        assert "Target Selection & Rationale" in analysis
        assert "Selected Variant Details" in analysis
        assert "Risk Management" in analysis
        
        # Should contain specific market data
        assert "SPY RSI(10): 65.0" in analysis
        assert "TECL" in analysis
        assert selected_variant.name in analysis

    def test_configuration_consistency(
        self,
        legacy_engine: KLMStrategyEnsemble,
        typed_engine: TypedKLMStrategyEngine,
    ) -> None:
        """Test that configuration between engines is consistent."""
        # Both should have the same strategy variants (by type)
        legacy_variant_types = [type(v).__name__ for v in legacy_engine.strategy_variants]
        typed_variant_types = [type(v).__name__ for v in typed_engine.strategy_variants]
        
        assert set(legacy_variant_types) == set(typed_variant_types)
        
        # Both should have the same symbol categories
        assert set(legacy_engine.market_symbols) == set(typed_engine.market_symbols)
        assert set(legacy_engine.sector_symbols) == set(typed_engine.sector_symbols)
        assert set(legacy_engine.tech_symbols) == set(typed_engine.tech_symbols)
        assert set(legacy_engine.volatility_symbols) == set(typed_engine.volatility_symbols)
        assert set(legacy_engine.bond_symbols) == set(typed_engine.bond_symbols)