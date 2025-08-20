"""Unit tests for typed TECL strategy engine."""

from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class TestTECLStrategyEngineTyped:
    """Test suite for typed TECL strategy engine."""

    @pytest.fixture
    def mock_market_data_port(self) -> Mock:
        """Create a mock MarketDataPort for testing."""
        mock_port = Mock(spec=MarketDataPort)
        
        # Create sample market data
        sample_data = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        mock_port.get_data.return_value = sample_data
        mock_port.get_current_price.return_value = 103.0
        mock_port.get_latest_quote.return_value = (102.5, 103.5)
        
        return mock_port

    @pytest.fixture
    def tecl_strategy(self, mock_market_data_port: Mock) -> TECLStrategyEngine:
        """Create a TECL strategy instance for testing."""
        return TECLStrategyEngine(data_provider=mock_market_data_port)

    def test_init_with_typed_port(self, mock_market_data_port: Mock):
        """Test initialization with MarketDataPort."""
        strategy = TECLStrategyEngine(data_provider=mock_market_data_port)
        
        assert strategy.data_provider is mock_market_data_port
        assert strategy.indicators is not None
        assert len(strategy.all_symbols) > 0
        assert "SPY" in strategy.market_symbols
        assert "TECL" in strategy.tech_symbols

    def test_get_market_data(self, tecl_strategy: TECLStrategyEngine, mock_market_data_port: Mock):
        """Test market data retrieval."""
        market_data = tecl_strategy.get_market_data()
        
        # Verify data provider was called for each symbol
        assert mock_market_data_port.get_data.call_count == len(tecl_strategy.all_symbols)
        
        # Verify market data structure
        assert isinstance(market_data, dict)
        assert len(market_data) == len(tecl_strategy.all_symbols)
        
        for symbol in tecl_strategy.all_symbols:
            assert symbol in market_data
            assert isinstance(market_data[symbol], pd.DataFrame)

    def test_calculate_indicators(self, tecl_strategy: TECLStrategyEngine):
        """Test indicator calculation."""
        # Mock market data
        market_data = {}
        for symbol in tecl_strategy.all_symbols:
            market_data[symbol] = pd.DataFrame({
                'Close': [100.0, 101.0, 102.0, 103.0, 104.0] * 50  # Enough data for indicators
            })
        
        indicators = tecl_strategy.calculate_indicators(market_data)
        
        assert isinstance(indicators, dict)
        assert len(indicators) == len(tecl_strategy.all_symbols)
        
        for symbol in tecl_strategy.all_symbols:
            assert symbol in indicators
            indicator_data = indicators[symbol]
            
            # Check required indicators
            assert 'rsi_9' in indicator_data
            assert 'rsi_10' in indicator_data
            assert 'rsi_20' in indicator_data
            assert 'ma_200' in indicator_data
            assert 'ma_20' in indicator_data
            assert 'current_price' in indicator_data
            
            # Verify data types
            assert isinstance(indicator_data['current_price'], float)

    def test_generate_signals_bull_market(self, tecl_strategy: TECLStrategyEngine, mock_market_data_port: Mock):
        """Test signal generation in bull market conditions."""
        # Create bull market indicators (SPY above 200 MA)
        indicators = self._create_bull_market_indicators()
        
        # Mock the strategy methods
        tecl_strategy.get_market_data = Mock(return_value={
            symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols
        })
        tecl_strategy.calculate_indicators = Mock(return_value=indicators)
        
        signals = tecl_strategy.generate_signals()
        
        assert isinstance(signals, list)
        assert len(signals) > 0
        
        # Verify signal structure
        signal = signals[0]
        assert isinstance(signal, StrategySignal)
        assert isinstance(signal.symbol, Symbol)
        assert signal.action in ("BUY", "SELL", "HOLD")
        assert isinstance(signal.confidence, Confidence)
        assert isinstance(signal.target_allocation, Percentage)
        assert isinstance(signal.reasoning, str)
        assert len(signal.reasoning) > 0

    def test_generate_signals_bear_market(self, tecl_strategy: TECLStrategyEngine, mock_market_data_port: Mock):
        """Test signal generation in bear market conditions."""
        # Create bear market indicators (SPY below 200 MA)
        indicators = self._create_bear_market_indicators()
        
        # Mock the strategy methods
        tecl_strategy.get_market_data = Mock(return_value={
            symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols
        })
        tecl_strategy.calculate_indicators = Mock(return_value=indicators)
        
        signals = tecl_strategy.generate_signals()
        
        assert isinstance(signals, list)
        assert len(signals) > 0
        
        # Verify signal structure
        signal = signals[0]
        assert isinstance(signal, StrategySignal)
        assert signal.action in ("BUY", "SELL", "HOLD")

    def test_generate_signals_with_portfolio_allocation(self, tecl_strategy: TECLStrategyEngine):
        """Test signal generation when strategy returns portfolio allocation."""
        # Mock to return portfolio allocation
        tecl_strategy.get_market_data = Mock(return_value={
            symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols
        })
        tecl_strategy.calculate_indicators = Mock(return_value=self._create_bull_market_indicators())
        tecl_strategy.evaluate_tecl_strategy = Mock(return_value=(
            {"UVXY": 0.25, "BIL": 0.75},
            "BUY",
            "Mixed allocation strategy"
        ))
        
        signals = tecl_strategy.generate_signals()
        
        assert len(signals) == 1
        signal = signals[0]
        
        # Should pick the largest allocation as primary symbol
        assert signal.symbol.value in ["BIL", "UVXY"]  # BIL has larger allocation
        assert signal.target_allocation.value == Decimal("1.0")  # Total allocation

    def test_generate_signals_error_handling(self, tecl_strategy: TECLStrategyEngine):
        """Test error handling in signal generation."""
        # Mock to raise exception
        tecl_strategy.get_market_data = Mock(side_effect=Exception("Market data error"))
        
        signals = tecl_strategy.generate_signals()
        
        # Should return empty list on error
        assert signals == []

    def test_run_once(self, tecl_strategy: TECLStrategyEngine):
        """Test run_once method returns alerts."""
        # Mock generate_signals to return valid signals
        mock_signal = StrategySignal(
            symbol=Symbol("TECL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("1.0")),
            reasoning="Test signal"
        )
        tecl_strategy.generate_signals = Mock(return_value=[mock_signal])
        
        alerts = tecl_strategy.run_once()
        
        assert alerts is not None
        assert len(alerts) == 1
        assert "TECL Strategy" in alerts[0].message
        assert alerts[0].severity == "INFO"

    def test_validate_signal_valid(self, tecl_strategy: TECLStrategyEngine):
        """Test signal validation with valid signal."""
        valid_signal = StrategySignal(
            symbol=Symbol("TECL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("1.0")),
            reasoning="Valid test signal"
        )
        
        assert tecl_strategy.validate_signal(valid_signal) is True

    def test_validate_signal_invalid(self, tecl_strategy: TECLStrategyEngine):
        """Test signal validation with invalid signal."""
        # Test with invalid confidence (>1.0)
        with pytest.raises(ValueError):
            invalid_signal = StrategySignal(
                symbol=Symbol("TECL"),
                action="BUY",
                confidence=Confidence(Decimal("1.5")),  # Invalid: > 1.0
                target_allocation=Percentage(Decimal("1.0")),
                reasoning="Invalid test signal"
            )

    def test_protocol_compliance(self, tecl_strategy: TECLStrategyEngine):
        """Test that TECLStrategyEngine implements StrategyEngine protocol."""
        from the_alchemiser.domain.strategies.protocols.strategy_engine import StrategyEngine
        
        # Check protocol compliance
        assert isinstance(tecl_strategy, StrategyEngine)
        
        # Check required methods exist
        assert hasattr(tecl_strategy, 'generate_signals')
        assert hasattr(tecl_strategy, 'run_once')
        assert hasattr(tecl_strategy, 'validate_signal')
        
        # Check method signatures are correct
        assert callable(tecl_strategy.generate_signals)
        assert callable(tecl_strategy.run_once)
        assert callable(tecl_strategy.validate_signal)

    def _create_bull_market_indicators(self) -> dict[str, dict[str, float]]:
        """Create indicators representing bull market conditions."""
        return {
            "SPY": {
                "current_price": 450.0,
                "ma_200": 400.0,  # Price above 200 MA = bull market
                "rsi_10": 60.0,
                "rsi_9": 58.0,
                "rsi_20": 62.0,
                "ma_20": 445.0,
            },
            "XLK": {
                "current_price": 180.0,
                "ma_200": 170.0,
                "rsi_10": 65.0,
                "rsi_9": 63.0,
                "rsi_20": 67.0,
                "ma_20": 178.0,
            },
            "KMLM": {
                "current_price": 40.0,
                "ma_200": 38.0,
                "rsi_10": 55.0,
                "rsi_9": 53.0,
                "rsi_20": 57.0,
                "ma_20": 39.5,
            },
            "TECL": {
                "current_price": 45.0,
                "ma_200": 40.0,
                "rsi_10": 60.0,
                "rsi_9": 58.0,
                "rsi_20": 62.0,
                "ma_20": 44.0,
            },
            "TQQQ": {
                "current_price": 35.0,
                "ma_200": 30.0,
                "rsi_10": 65.0,
                "rsi_9": 63.0,
                "rsi_20": 67.0,
                "ma_20": 34.0,
            },
            "BIL": {
                "current_price": 91.5,
                "ma_200": 91.0,
                "rsi_10": 50.0,
                "rsi_9": 48.0,
                "rsi_20": 52.0,
                "ma_20": 91.3,
            },
            "UVXY": {
                "current_price": 12.0,
                "ma_200": 15.0,
                "rsi_10": 45.0,
                "rsi_9": 43.0,
                "rsi_20": 47.0,
                "ma_20": 13.0,
            },
            "SPXL": {
                "current_price": 85.0,
                "ma_200": 75.0,
                "rsi_10": 60.0,
                "rsi_9": 58.0,
                "rsi_20": 62.0,
                "ma_20": 83.0,
            },
            "SQQQ": {
                "current_price": 15.0,
                "ma_200": 18.0,
                "rsi_10": 40.0,
                "rsi_9": 38.0,
                "rsi_20": 42.0,
                "ma_20": 16.0,
            },
            "BSV": {
                "current_price": 77.0,
                "ma_200": 76.0,
                "rsi_10": 50.0,
                "rsi_9": 48.0,
                "rsi_20": 52.0,
                "ma_20": 76.8,
            },
        }

    def _create_bear_market_indicators(self) -> dict[str, dict[str, float]]:
        """Create indicators representing bear market conditions."""
        return {
            "SPY": {
                "current_price": 380.0,
                "ma_200": 420.0,  # Price below 200 MA = bear market
                "rsi_10": 35.0,
                "rsi_9": 33.0,
                "rsi_20": 37.0,
                "ma_20": 385.0,
            },
            "XLK": {
                "current_price": 150.0,
                "ma_200": 170.0,
                "rsi_10": 40.0,
                "rsi_9": 38.0,
                "rsi_20": 42.0,
                "ma_20": 155.0,
            },
            "KMLM": {
                "current_price": 35.0,
                "ma_200": 38.0,
                "rsi_10": 45.0,
                "rsi_9": 43.0,
                "rsi_20": 47.0,
                "ma_20": 36.0,
            },
            "TECL": {
                "current_price": 25.0,
                "ma_200": 40.0,
                "rsi_10": 30.0,
                "rsi_9": 28.0,
                "rsi_20": 32.0,
                "ma_20": 28.0,
            },
            "TQQQ": {
                "current_price": 20.0,
                "ma_200": 30.0,
                "rsi_10": 25.0,
                "rsi_9": 23.0,
                "rsi_20": 27.0,
                "ma_20": 22.0,
            },
            "BIL": {
                "current_price": 91.5,
                "ma_200": 91.0,
                "rsi_10": 60.0,
                "rsi_9": 58.0,
                "rsi_20": 62.0,
                "ma_20": 91.3,
            },
            "UVXY": {
                "current_price": 25.0,
                "ma_200": 15.0,
                "rsi_10": 80.0,
                "rsi_9": 78.0,
                "rsi_20": 82.0,
                "ma_20": 22.0,
            },
            "SPXL": {
                "current_price": 45.0,
                "ma_200": 75.0,
                "rsi_10": 25.0,
                "rsi_9": 23.0,
                "rsi_20": 27.0,
                "ma_20": 48.0,
            },
            "SQQQ": {
                "current_price": 25.0,
                "ma_200": 18.0,
                "rsi_10": 70.0,
                "rsi_9": 68.0,
                "rsi_20": 72.0,
                "ma_20": 23.0,
            },
            "BSV": {
                "current_price": 78.0,
                "ma_200": 76.0,
                "rsi_10": 65.0,
                "rsi_9": 63.0,
                "rsi_20": 67.0,
                "ma_20": 77.5,
            },
        }