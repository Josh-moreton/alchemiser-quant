"""Parity tests for TECL strategy to ensure typed interface matches legacy behavior."""

from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.utils.common import ActionType


class TestTECLStrategyParity:
    """Test suite ensuring typed TECL strategy produces equivalent results to legacy interface."""

    @pytest.fixture
    def mock_market_data_port(self) -> Mock:
        """Create a mock MarketDataPort that returns consistent data."""
        mock_port = Mock(spec=MarketDataPort)
        
        # Create comprehensive market data with enough points for indicators
        def create_sample_data(symbol: str) -> pd.DataFrame:
            # Create 250+ data points for reliable technical indicators
            base_price = {"SPY": 450, "XLK": 180, "KMLM": 40, "TECL": 45, "TQQQ": 35, 
                         "BIL": 91.5, "UVXY": 12, "SPXL": 85, "SQQQ": 15, "BSV": 77}.get(symbol, 100)
            
            # Generate realistic price data with some volatility
            prices = []
            for i in range(250):
                # Add some realistic price movement
                variance = (i % 10 - 5) * 0.01  # Small variations
                price = base_price * (1 + variance)
                prices.append(price)
            
            return pd.DataFrame({
                'Open': [p * 0.998 for p in prices],
                'High': [p * 1.005 for p in prices],
                'Low': [p * 0.995 for p in prices],
                'Close': prices,
                'Volume': [1000000 + i * 1000 for i in range(250)]
            })
        
        mock_port.get_data.side_effect = create_sample_data
        mock_port.get_current_price.return_value = 103.0
        mock_port.get_latest_quote.return_value = (102.5, 103.5)
        
        return mock_port

    @pytest.fixture
    def tecl_strategy(self, mock_market_data_port: Mock) -> TECLStrategyEngine:
        """Create a TECL strategy instance for testing."""
        return TECLStrategyEngine(data_provider=mock_market_data_port)

    def test_legacy_vs_typed_signal_consistency(self, tecl_strategy: TECLStrategyEngine):
        """Test that typed signals are consistent with legacy evaluate_tecl_strategy output."""
        # Get market data and indicators
        market_data = tecl_strategy.get_market_data()
        indicators = tecl_strategy.calculate_indicators(market_data)
        
        # Get legacy result
        symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Get typed signals
        signals = tecl_strategy.generate_signals()
        
        # Should have exactly one signal
        assert len(signals) == 1
        signal = signals[0]
        
        # Verify action consistency
        assert signal.action == action
        
        # Verify reasoning consistency
        assert signal.reasoning == reasoning
        
        # Verify symbol consistency
        if isinstance(symbol_or_allocation, dict):
            # Portfolio allocation - should pick primary symbol
            primary_symbol = max(symbol_or_allocation.keys(), 
                               key=lambda s: symbol_or_allocation[s])
            assert signal.symbol.value == primary_symbol
            
            # Total allocation should be sum of allocations
            total_allocation = sum(symbol_or_allocation.values())
            expected_allocation = Decimal(str(total_allocation))
            assert signal.target_allocation.value == expected_allocation
        else:
            # Single symbol
            assert signal.symbol.value == symbol_or_allocation
            assert signal.target_allocation.value == Decimal("1.0")

    def test_bull_market_parity(self, tecl_strategy: TECLStrategyEngine):
        """Test parity in bull market conditions."""
        # Create bull market indicators
        indicators = self._create_bull_market_indicators()
        market_data = {symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols}
        
        # Test legacy interface
        symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Mock the internal methods to use our test data
        tecl_strategy.get_market_data = Mock(return_value=market_data)
        tecl_strategy.calculate_indicators = Mock(return_value=indicators)
        
        # Test typed interface
        signals = tecl_strategy.generate_signals()
        
        # Verify parity
        assert len(signals) == 1
        signal = signals[0]
        
        assert signal.action == action
        assert signal.reasoning == reasoning
        
        # Verify expected bull market behavior
        assert action == ActionType.BUY.value
        assert len(reasoning) > 0

    def test_bear_market_parity(self, tecl_strategy: TECLStrategyEngine):
        """Test parity in bear market conditions."""
        # Create bear market indicators
        indicators = self._create_bear_market_indicators()
        market_data = {symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols}
        
        # Test legacy interface
        symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Mock the internal methods to use our test data
        tecl_strategy.get_market_data = Mock(return_value=market_data)
        tecl_strategy.calculate_indicators = Mock(return_value=indicators)
        
        # Test typed interface
        signals = tecl_strategy.generate_signals()
        
        # Verify parity
        assert len(signals) == 1
        signal = signals[0]
        
        assert signal.action == action
        assert signal.reasoning == reasoning
        
        # Verify expected bear market behavior
        assert action == ActionType.BUY.value  # TECL strategy always generates BUY signals
        assert len(reasoning) > 0

    def test_portfolio_allocation_parity(self, tecl_strategy: TECLStrategyEngine):
        """Test parity when strategy returns portfolio allocation."""
        # Create indicators that trigger portfolio allocation (e.g., overbought TQQQ)
        indicators = self._create_bull_market_indicators()
        indicators["TQQQ"]["rsi_10"] = 85.0  # Trigger overbought condition
        
        market_data = {symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols}
        
        # Test legacy interface
        symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Should return portfolio allocation
        assert isinstance(symbol_or_allocation, dict)
        assert "UVXY" in symbol_or_allocation
        assert "BIL" in symbol_or_allocation
        
        # Mock the internal methods
        tecl_strategy.get_market_data = Mock(return_value=market_data)
        tecl_strategy.calculate_indicators = Mock(return_value=indicators)
        
        # Test typed interface
        signals = tecl_strategy.generate_signals()
        
        # Verify parity
        assert len(signals) == 1
        signal = signals[0]
        
        assert signal.action == action
        assert signal.reasoning == reasoning
        
        # Should pick the symbol with largest allocation
        primary_symbol = max(symbol_or_allocation.keys(), 
                           key=lambda s: symbol_or_allocation[s])
        assert signal.symbol.value == primary_symbol
        
        # Total allocation should match sum
        total_allocation = sum(symbol_or_allocation.values())
        expected_decimal = Decimal(str(total_allocation))
        assert signal.target_allocation.value == expected_decimal

    def test_multiple_market_scenarios_parity(self, tecl_strategy: TECLStrategyEngine):
        """Test parity across multiple market scenarios."""
        scenarios = [
            ("bull_normal", self._create_bull_market_indicators()),
            ("bear_normal", self._create_bear_market_indicators()),
            ("bull_overbought", self._create_overbought_bull_indicators()),
            ("bear_oversold", self._create_oversold_bear_indicators()),
        ]
        
        for scenario_name, indicators in scenarios:
            market_data = {symbol: pd.DataFrame({'Close': [100.0]}) for symbol in tecl_strategy.all_symbols}
            
            # Legacy result
            symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(indicators, market_data)
            
            # Mock for typed interface
            tecl_strategy.get_market_data = Mock(return_value=market_data)
            tecl_strategy.calculate_indicators = Mock(return_value=indicators)
            
            # Typed result
            signals = tecl_strategy.generate_signals()
            
            # Verify parity
            assert len(signals) == 1, f"Scenario {scenario_name}: Expected 1 signal"
            signal = signals[0]
            
            assert signal.action == action, f"Scenario {scenario_name}: Action mismatch"
            assert signal.reasoning == reasoning, f"Scenario {scenario_name}: Reasoning mismatch"

    def test_error_handling_parity(self, tecl_strategy: TECLStrategyEngine):
        """Test that error handling is consistent between interfaces."""
        # Test with missing data
        incomplete_indicators = {"SPY": {"current_price": 450.0}}  # Missing required indicators
        market_data = {}
        
        # Legacy interface should handle gracefully
        try:
            symbol_or_allocation, action, reasoning = tecl_strategy.evaluate_tecl_strategy(incomplete_indicators, market_data)
            legacy_succeeded = True
            legacy_result = (symbol_or_allocation, action, reasoning)
        except Exception:
            legacy_succeeded = False
            legacy_result = None
        
        # Mock for typed interface
        tecl_strategy.get_market_data = Mock(return_value=market_data)
        tecl_strategy.calculate_indicators = Mock(return_value=incomplete_indicators)
        
        # Typed interface should handle gracefully
        signals = tecl_strategy.generate_signals()
        
        if legacy_succeeded and legacy_result:
            # If legacy succeeded, typed should produce equivalent signal
            assert len(signals) == 1
            signal = signals[0]
            assert signal.action == legacy_result[1]
            assert signal.reasoning == legacy_result[2]
        else:
            # If legacy failed, typed should return empty list
            assert signals == []

    def _create_bull_market_indicators(self) -> dict[str, dict[str, float]]:
        """Create indicators representing normal bull market conditions."""
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
            "TECL": {"current_price": 45.0, "ma_200": 40.0, "rsi_10": 60.0, "rsi_9": 58.0, "rsi_20": 62.0, "ma_20": 44.0},
            "TQQQ": {"current_price": 35.0, "ma_200": 30.0, "rsi_10": 65.0, "rsi_9": 63.0, "rsi_20": 67.0, "ma_20": 34.0},
            "BIL": {"current_price": 91.5, "ma_200": 91.0, "rsi_10": 50.0, "rsi_9": 48.0, "rsi_20": 52.0, "ma_20": 91.3},
            "UVXY": {"current_price": 12.0, "ma_200": 15.0, "rsi_10": 45.0, "rsi_9": 43.0, "rsi_20": 47.0, "ma_20": 13.0},
            "SPXL": {"current_price": 85.0, "ma_200": 75.0, "rsi_10": 60.0, "rsi_9": 58.0, "rsi_20": 62.0, "ma_20": 83.0},
            "SQQQ": {"current_price": 15.0, "ma_200": 18.0, "rsi_10": 40.0, "rsi_9": 38.0, "rsi_20": 42.0, "ma_20": 16.0},
            "BSV": {"current_price": 77.0, "ma_200": 76.0, "rsi_10": 50.0, "rsi_9": 48.0, "rsi_20": 52.0, "ma_20": 76.8},
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
            "XLK": {"current_price": 150.0, "ma_200": 170.0, "rsi_10": 40.0, "rsi_9": 38.0, "rsi_20": 42.0, "ma_20": 155.0},
            "KMLM": {"current_price": 35.0, "ma_200": 38.0, "rsi_10": 45.0, "rsi_9": 43.0, "rsi_20": 47.0, "ma_20": 36.0},
            "TECL": {"current_price": 25.0, "ma_200": 40.0, "rsi_10": 30.0, "rsi_9": 28.0, "rsi_20": 32.0, "ma_20": 28.0},
            "TQQQ": {"current_price": 20.0, "ma_200": 30.0, "rsi_10": 25.0, "rsi_9": 23.0, "rsi_20": 27.0, "ma_20": 22.0},
            "BIL": {"current_price": 91.5, "ma_200": 91.0, "rsi_10": 60.0, "rsi_9": 58.0, "rsi_20": 62.0, "ma_20": 91.3},
            "UVXY": {"current_price": 25.0, "ma_200": 15.0, "rsi_10": 80.0, "rsi_9": 78.0, "rsi_20": 82.0, "ma_20": 22.0},
            "SPXL": {"current_price": 45.0, "ma_200": 75.0, "rsi_10": 25.0, "rsi_9": 23.0, "rsi_20": 27.0, "ma_20": 48.0},
            "SQQQ": {"current_price": 25.0, "ma_200": 18.0, "rsi_10": 70.0, "rsi_9": 68.0, "rsi_20": 72.0, "ma_20": 23.0},
            "BSV": {"current_price": 78.0, "ma_200": 76.0, "rsi_10": 65.0, "rsi_9": 63.0, "rsi_20": 67.0, "ma_20": 77.5},
        }

    def _create_overbought_bull_indicators(self) -> dict[str, dict[str, float]]:
        """Create indicators with overbought conditions in bull market."""
        indicators = self._create_bull_market_indicators()
        indicators["TQQQ"]["rsi_10"] = 85.0  # Trigger overbought condition
        return indicators

    def _create_oversold_bear_indicators(self) -> dict[str, dict[str, float]]:
        """Create indicators with oversold conditions in bear market."""
        indicators = self._create_bear_market_indicators()
        indicators["TQQQ"]["rsi_10"] = 25.0  # Trigger oversold condition
        return indicators