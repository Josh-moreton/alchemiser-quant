"""
Parity tests for Nuclear strategy: legacy vs typed implementation.

These tests verify that the new typed Nuclear strategy produces equivalent results
to the legacy implementation when the TYPES_V2_ENABLED flag is on/off.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.application.mapping.strategy_signal_mapping import legacy_signal_to_typed
from the_alchemiser.domain.strategies.nuclear_signals import NuclearStrategyEngine as LegacyNuclearStrategy
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_nuclear_strategy import TypedNuclearStrategy
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal


class MockDataProviderToPortAdapter:
    """Adapter to make a mock data provider look like a MarketDataPort."""
    
    def __init__(self, mock_data_provider: Mock) -> None:
        self.data_provider = mock_data_provider
    
    def get_data(self, symbol: str, timeframe: str = "1day", period: str = "1y", **kwargs: Any) -> pd.DataFrame:
        return self.data_provider.get_data(symbol)
    
    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        try:
            return self.data_provider.get_current_price(symbol)
        except Exception:
            return None
    
    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        try:
            price = self.data_provider.get_current_price(symbol)
            return (price * 0.999, price * 1.001) if price else (None, None)
        except Exception:
            return (None, None)


class TestNuclearStrategyParity:
    """Test parity between legacy and typed Nuclear strategy implementations."""

    @pytest.fixture
    def mock_data_provider(self) -> Mock:
        """Create mock data provider with realistic market data."""
        mock_provider = Mock()
        
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            """Generate realistic market data for testing."""
            base_price = {
                "SPY": 450.0,
                "IOO": 80.0,
                "TQQQ": 50.0,
                "VTV": 150.0,
                "XLF": 35.0,
                "VOX": 90.0,
                "UVXY": 15.0,
                "BTAL": 25.0,
                "QQQ": 380.0,
                "SQQQ": 8.0,
                "PSQ": 12.0,
                "UPRO": 60.0,
                "TLT": 95.0,
                "IEF": 105.0,
                "SMR": 25.0,
                "BWXT": 95.0,
                "LEU": 30.0,
                "EXC": 40.0,
                "NLR": 85.0,
                "OKLO": 15.0,
            }.get(symbol, 100.0)
            
            # Create 300 days of data
            dates = pd.date_range("2023-01-01", periods=300, freq="D")
            data = []
            
            for i in range(300):
                # Add some realistic price movement
                price_mult = 1.0 + (i / 1000) + (0.02 * (i % 20 - 10) / 10)
                price = base_price * price_mult
                data.append({
                    "Open": price * 0.995,
                    "High": price * 1.01,
                    "Low": price * 0.99,
                    "Close": price,
                    "Volume": 1000000 + (i * 1000),
                })
            
            return pd.DataFrame(data, index=dates)
        
        mock_provider.get_data.side_effect = get_data_side_effect
        
        def get_current_price_side_effect(symbol: str) -> float:
            df = get_data_side_effect(symbol)
            return float(df["Close"].iloc[-1])
        
        mock_provider.get_current_price.side_effect = get_current_price_side_effect
        
        return mock_provider

    @pytest.fixture
    def legacy_strategy(self, mock_data_provider: Mock) -> LegacyNuclearStrategy:
        """Create legacy Nuclear strategy with mock data provider."""
        return LegacyNuclearStrategy(data_provider=mock_data_provider)

    @pytest.fixture
    def typed_strategy(self) -> TypedNuclearStrategy:
        """Create typed Nuclear strategy with dynamic allocation enabled for parity testing."""
        return TypedNuclearStrategy(enable_dynamic_allocation=True)

    @pytest.fixture
    def mock_port(self, mock_data_provider: Mock) -> MarketDataPort:
        """Create MarketDataPort adapter for mock data provider."""
        return MockDataProviderToPortAdapter(mock_data_provider)

    @pytest.fixture
    def now(self) -> datetime:
        """Fixed timestamp for consistent testing."""
        return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    def _create_spy_overbought_data(self) -> pd.DataFrame:
        """Create SPY data that results in RSI > 81 (extremely overbought)."""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        base_price = 450.0
        
        data = []
        for i in range(300):
            if i < 280:
                # Normal price movement for first 280 days
                price = base_price + (i * 0.1)
            else:
                # Sharp price increase in last 20 days to create RSI > 81
                price = base_price + (280 * 0.1) + ((i - 280) * 2.0)
            
            data.append({
                "Open": price * 0.995,
                "High": price * 1.01,
                "Low": price * 0.99,
                "Close": price,
                "Volume": 1000000,
            })
        
        return pd.DataFrame(data, index=dates)

    def _create_spy_oversold_data(self) -> pd.DataFrame:
        """Create SPY data that results in RSI < 30 (oversold)."""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        base_price = 450.0
        
        data = []
        for i in range(300):
            if i < 280:
                # Normal price movement for first 280 days
                price = base_price + (i * 0.1)
            else:
                # Sharp price decrease in last 20 days to create RSI < 30
                price = base_price + (280 * 0.1) - ((i - 280) * 2.0)
            
            data.append({
                "Open": price * 0.995,
                "High": price * 1.01,
                "Low": price * 0.99,
                "Close": price,
                "Volume": 1000000,
            })
        
        return pd.DataFrame(data, index=dates)

    def _create_spy_bull_market_data(self) -> pd.DataFrame:
        """Create SPY data for bull market conditions."""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        base_price = 450.0
        
        data = []
        for i in range(300):
            # Steady upward trend to ensure current price > 200 MA
            price = base_price + (i * 0.2)
            
            data.append({
                "Open": price * 0.995,
                "High": price * 1.01,
                "Low": price * 0.99,
                "Close": price,
                "Volume": 1000000,
            })
        
        return pd.DataFrame(data, index=dates)

    def test_parity_spy_extremely_overbought_scenario(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test parity for SPY extremely overbought scenario."""
        
        # Setup scenario where SPY RSI > 81 (extremely overbought)
        # Create fresh data for SPY to avoid recursion
        spy_data = self._create_spy_overbought_data()
        
        original_get_data = mock_data_provider.get_data.side_effect
        
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            if symbol == "SPY":
                return spy_data
            # Use original data for other symbols
            return original_get_data(symbol)
        
        mock_data_provider.get_data.side_effect = get_data_side_effect
        
        # Test legacy strategy
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # Verify parity
        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]
        
        # Core signal parity
        assert typed_signal.symbol.value == legacy_symbol
        assert typed_signal.action == legacy_action
        assert legacy_symbol == "UVXY"  # Should be UVXY for extremely overbought
        assert legacy_action == "BUY"
        
        # Reasoning should contain similar key information
        assert "extremely overbought" in legacy_reason.lower()
        assert "extremely overbought" in typed_signal.reasoning.lower()
        assert "uvxy" in typed_signal.reasoning.lower()

    def test_parity_spy_oversold_scenario(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test parity for SPY oversold scenario."""
        
        # Setup scenario where SPY RSI < 30 (oversold)
        spy_data = self._create_spy_oversold_data()
        
        original_get_data = mock_data_provider.get_data.side_effect
        
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            if symbol == "SPY":
                return spy_data
            return original_get_data(symbol)
        
        mock_data_provider.get_data.side_effect = get_data_side_effect
        
        # Test legacy strategy
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # Verify parity
        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]
        
        # Core signal parity
        assert typed_signal.symbol.value == legacy_symbol
        assert typed_signal.action == legacy_action
        assert legacy_symbol == "UPRO"  # Should be UPRO for SPY oversold
        assert legacy_action == "BUY"
        
        # Reasoning should contain similar key information
        assert "oversold" in legacy_reason.lower()
        assert "oversold" in typed_signal.reasoning.lower()

    def test_parity_bull_market_scenario(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test parity for bull market scenario."""
        
        # Setup bull market scenario (SPY above 200 MA, moderate RSI)
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            df = mock_data_provider.get_data(symbol)
            if symbol == "SPY":
                df = df.copy()
                # Ensure current price is above 200 MA but RSI is moderate
                ma_200 = df["Close"].rolling(200).mean().iloc[-1]
                df.loc[df.index[-1], "Close"] = ma_200 * 1.05  # 5% above 200 MA
            return df
        
        mock_data_provider.get_data.side_effect = get_data_side_effect
        
        # Test legacy strategy
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # Verify parity
        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]
        
        # Core signal parity
        assert typed_signal.symbol.value == legacy_symbol
        assert typed_signal.action == legacy_action
        
        # Should be bull market strategy
        assert "bull market" in legacy_reason.lower()
        assert "bull market" in typed_signal.reasoning.lower()

    def test_parity_hold_scenario(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test parity for neutral/hold scenario."""
        
        # Use default data which should result in neutral conditions
        # Test legacy strategy
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # Verify parity
        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]
        
        # Core signal parity
        assert typed_signal.symbol.value == legacy_symbol
        assert typed_signal.action == legacy_action
        
        # For neutral conditions, both should provide the same recommendation
        # The exact symbol/action depends on the specific market conditions
        # but both implementations should give the same result

    def test_legacy_to_typed_signal_mapping(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        mock_data_provider: Mock,
    ) -> None:
        """Test that legacy signals can be mapped to typed signals."""
        
        # Get legacy signal
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        symbol, action, reason = legacy_strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # Create legacy signal dict (as would be used in the system)
        legacy_signal_dict = {
            "symbol": symbol,
            "action": action,
            "reason": reason,
            "confidence": 0.75,  # Default confidence
            "allocation_percentage": 0.5,  # Default allocation
        }
        
        # Map to typed signal
        typed_signal = legacy_signal_to_typed(legacy_signal_dict)
        
        # Verify mapping
        assert isinstance(typed_signal, dict)  # StrategySignal TypedDict format
        assert typed_signal["symbol"] == symbol or typed_signal["symbol"] == "PORTFOLIO"
        assert typed_signal["action"] == action
        assert typed_signal["reasoning"] == reason
        assert typed_signal["confidence"] == pytest.approx(0.75, rel=1e-9, abs=1e-9)
        assert typed_signal["allocation_percentage"] == pytest.approx(0.5, rel=1e-9, abs=1e-9)

    def test_edge_case_missing_spy_data_parity(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test parity when SPY data is missing."""
        
        # Make SPY data return empty dataframe
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            if symbol == "SPY":
                return pd.DataFrame()  # Empty dataframe
            return mock_data_provider.get_data(symbol)
        
        mock_data_provider.get_data.side_effect = get_data_side_effect
        
        # Test legacy strategy - should handle gracefully
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # Both should handle missing SPY data similarly
        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]
        
        # Both should fall back to safe defaults when SPY data is missing
        assert typed_signal.symbol.value == legacy_symbol
        assert typed_signal.action == legacy_action
        # Should both indicate missing data issue
        assert "missing" in legacy_reason.lower() or "spy" in legacy_reason.lower()
        assert "missing" in typed_signal.reasoning.lower() or "spy" in typed_signal.reasoning.lower()

    def test_confidence_and_allocation_generation(
        self,
        typed_strategy: TypedNuclearStrategy,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test that typed strategy generates appropriate confidence and allocation values."""
        
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        assert len(typed_signals) == 1
        signal = typed_signals[0]
        
        # Validate typed signal structure
        assert isinstance(signal, StrategySignal)
        assert Decimal("0") <= signal.confidence.value <= Decimal("1")
        assert Decimal("0") <= signal.target_allocation.value <= Decimal("1")
        
        # Confidence should be reasonable based on signal type
        if signal.action == "BUY":
            assert signal.confidence.value >= Decimal("0.5")  # Should have reasonable confidence for buy signals
        elif signal.action == "HOLD":
            assert signal.confidence.value <= Decimal("0.5")  # Lower confidence for hold signals

    def test_portfolio_signal_handling(
        self,
        legacy_strategy: LegacyNuclearStrategy,
        typed_strategy: TypedNuclearStrategy,
        mock_data_provider: Mock,
        mock_port: MarketDataPort,
        now: datetime,
    ) -> None:
        """Test handling of portfolio signals (UVXY_BTAL_PORTFOLIO)."""
        
        # Setup scenario for portfolio hedge signal (SPY moderately overbought)
        def get_data_side_effect(symbol: str) -> pd.DataFrame:
            df = mock_data_provider.get_data(symbol)
            if symbol == "SPY":
                df = df.copy()
                # Create moderate overbought scenario (79 < RSI < 81)
                df.loc[df.index[-15:], "Close"] = df["Close"].iloc[-16] * 1.08
            return df
        
        mock_data_provider.get_data.side_effect = get_data_side_effect
        
        # Test legacy strategy
        market_data = legacy_strategy.get_market_data()
        indicators = legacy_strategy.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_strategy.evaluate_nuclear_strategy(
            indicators, market_data
        )
        
        # Test typed strategy
        typed_signals = typed_strategy.generate_signals(mock_port, now)
        
        # If legacy returns portfolio signal, typed should handle it appropriately
        if "PORTFOLIO" in legacy_symbol:
            typed_signal = typed_signals[0]
            assert typed_signal.symbol.value == "PORTFOLIO" or "UVXY" in typed_signal.symbol.value
            # Should have high allocation for portfolio hedge
            assert typed_signal.target_allocation.value >= Decimal("0.5")