"""
Unit tests for typed Nuclear strategy engine with mocked MarketDataPort.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.strategies.nuclear_typed_engine import NuclearTypedEngine
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from tests.utils.float_checks import assert_close


class TestNuclearTypedEngine:
    """Test cases for NuclearTypedEngine."""

    @pytest.fixture
    def engine(self) -> NuclearTypedEngine:
        """Create Nuclear typed engine instance."""
        return NuclearTypedEngine()

    @pytest.fixture
    def mock_port(self) -> Mock:
        """Create mock MarketDataPort."""
        port = Mock(spec=MarketDataPort)

        # Default successful responses
        port.get_current_price.return_value = 100.0

        # Default market data with basic OHLCV structure
        default_df = pd.DataFrame({
            "Open": [99.0, 100.0, 101.0] * 50,  # 150 rows for sufficient history
            "High": [101.0, 102.0, 103.0] * 50,
            "Low": [98.0, 99.0, 100.0] * 50,
            "Close": [100.0, 101.0, 102.0] * 50,
            "Volume": [1000000, 1100000, 1200000] * 50,
        }, index=pd.date_range('2023-01-01', periods=150, freq='D'))

        port.get_data.return_value = default_df
        return port

    @pytest.fixture
    def mock_port_spy_overbought(self, mock_port: Mock) -> Mock:
        """Mock port with SPY in overbought condition (RSI > 79)."""
        # Create data that will produce high RSI
        overbought_prices = [50.0] + [60.0 + i * 2 for i in range(149)]  # Strong uptrend
        df = pd.DataFrame({
            "Open": overbought_prices,
            "High": [p * 1.02 for p in overbought_prices],
            "Low": [p * 0.98 for p in overbought_prices],
            "Close": overbought_prices,
            "Volume": [1000000] * 150,
        }, index=pd.date_range('2023-01-01', periods=150, freq='D'))

        mock_port.get_data.return_value = df
        return mock_port

    @pytest.fixture
    def mock_port_spy_oversold(self, mock_port: Mock) -> Mock:
        """Mock port with SPY in oversold condition (RSI < 30)."""
        # Create data that will produce low RSI
        oversold_prices = [100.0] + [80.0 - i * 0.5 for i in range(149)]  # Strong downtrend
        df = pd.DataFrame({
            "Open": oversold_prices,
            "High": [p * 1.01 for p in oversold_prices],
            "Low": [p * 0.99 for p in oversold_prices],
            "Close": oversold_prices,
            "Volume": [1000000] * 150,
        }, index=pd.date_range('2023-01-01', periods=150, freq='D'))

        mock_port.get_data.return_value = df
        return mock_port

    def test_engine_initialization(self, engine: NuclearTypedEngine) -> None:
        """Test Nuclear engine initializes correctly."""
        assert engine.strategy_name == "Nuclear"
        assert len(engine.get_required_symbols()) > 0
        assert "SPY" in engine.get_required_symbols()
        assert "UVXY" in engine.get_required_symbols()

    def test_get_required_symbols(self, engine: NuclearTypedEngine) -> None:
        """Test required symbols include all Nuclear strategy symbols."""
        symbols = engine.get_required_symbols()

        # Check key symbols are present
        expected_symbols = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX", "UVXY", "BTAL", "QQQ", "SQQQ"]
        for symbol in expected_symbols:
            assert symbol in symbols

    def test_generate_signals_success(self, engine: NuclearTypedEngine, mock_port: Mock) -> None:
        """Test successful signal generation."""
        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port, now)

        assert isinstance(signals, list)
        assert len(signals) >= 1

        # Check signal structure
        signal = signals[0]
        assert isinstance(signal, StrategySignal)
        assert signal.action in ("BUY", "SELL", "HOLD")
        assert 0 <= signal.confidence.value <= 1
        assert signal.target_allocation.value >= 0
        assert signal.reasoning != ""

    def test_generate_signals_spy_overbought(
        self, engine: NuclearTypedEngine, mock_port_spy_overbought: Mock
    ) -> None:
        """Test signal generation with SPY overbought condition."""
        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port_spy_overbought, now)

        assert len(signals) == 1
        signal = signals[0]

        # Should generate defensive signal
        assert signal.action == "BUY"
        # Should be UVXY or similar volatility hedge
        assert signal.symbol.value in ["UVXY", "BTAL"]
        assert signal.confidence.value > Decimal("0.6")  # High confidence for clear overbought
        assert "overbought" in signal.reasoning.lower()

    def test_generate_signals_spy_oversold(
        self, engine: NuclearTypedEngine, mock_port_spy_oversold: Mock
    ) -> None:
        """Test signal generation with SPY oversold condition."""
        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port_spy_oversold, now)

        assert len(signals) == 1
        signal = signals[0]

        # Should generate buy signal for oversold bounce
        assert signal.action == "BUY"
        assert signal.confidence.value > Decimal("0.7")  # High confidence for oversold
        assert "oversold" in signal.reasoning.lower()

    def test_generate_signals_no_data(self, engine: NuclearTypedEngine) -> None:
        """Test signal generation when no market data available."""
        mock_port = Mock(spec=MarketDataPort)
        mock_port.get_data.return_value = pd.DataFrame()  # Empty dataframe
        mock_port.get_current_price.return_value = None

        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port, now)

        # Should return empty list when no data
        assert signals == []

    def test_generate_signals_missing_spy(self, engine: NuclearTypedEngine) -> None:
        """Test signal generation when SPY data is missing."""
        mock_port = Mock(spec=MarketDataPort)

        # Return data for all symbols except SPY
        def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
            if symbol == "SPY":
                return pd.DataFrame()  # Empty for SPY
            else:
                return pd.DataFrame({
                    "Open": [100.0] * 50,
                    "High": [101.0] * 50,
                    "Low": [99.0] * 50,
                    "Close": [100.0] * 50,
                    "Volume": [1000000] * 50,
                }, index=pd.date_range('2023-01-01', periods=50, freq='D'))

        mock_port.get_data.side_effect = mock_get_data
        mock_port.get_current_price.return_value = 100.0

        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port, now)

        assert len(signals) == 1
        signal = signals[0]
        assert signal.action == "HOLD"
        assert "missing spy data" in signal.reasoning.lower()

    def test_generate_signals_error_handling(self, engine: NuclearTypedEngine) -> None:
        """Test error handling in signal generation."""
        mock_port = Mock(spec=MarketDataPort)
        mock_port.get_data.side_effect = Exception("Data fetch failed")

        now = datetime.now(UTC)

        # With the current implementation, errors in data fetching result in empty data
        # which leads to empty signals, not an exception
        signals = engine.generate_signals(mock_port, now)
        assert signals == []

    def test_confidence_calculation_extremes(self, engine: NuclearTypedEngine) -> None:
        """Test confidence calculation for extreme conditions."""
        # Test extremely overbought
        confidence = engine._calculate_confidence(
            "UVXY", "BUY", "SPY extremely overbought - volatility hedge"
        )
        assert_close(confidence, 0.9)

        # Test oversold
        confidence = engine._calculate_confidence(
            "TQQQ", "BUY", "TQQQ oversold opportunity"
        )
        assert_close(confidence, 0.85)

        # Test hold signal
        confidence = engine._calculate_confidence(
            "SPY", "HOLD", "Neutral market conditions"
        )
        assert_close(confidence, 0.6)

    def test_target_allocation_calculation(self, engine: NuclearTypedEngine) -> None:
        """Test target allocation calculation for different signal types."""
        # Test hold signals
        allocation = engine._calculate_target_allocation("SPY", "HOLD")
        assert_close(allocation, 0.0)

        # Test portfolio signals
        allocation = engine._calculate_target_allocation("UVXY_BTAL_PORTFOLIO", "BUY")
        assert_close(allocation, 1.0)

        # Test volatility hedge
        allocation = engine._calculate_target_allocation("UVXY", "BUY")
        assert_close(allocation, 0.25)

        # Test leveraged positions
        allocation = engine._calculate_target_allocation("TQQQ", "BUY")
        assert_close(allocation, 0.30)

    def test_portfolio_signal_handling(
        self, engine: NuclearTypedEngine, mock_port: Mock
    ) -> None:
        """Test handling of portfolio signals (UVXY_BTAL_PORTFOLIO)."""
        # Mock SPY in moderate overbought range (79-81)
        moderate_overbought_prices = [50.0] + [55.0 + i * 0.8 for i in range(149)]
        df = pd.DataFrame({
            "Open": moderate_overbought_prices,
            "High": [p * 1.02 for p in moderate_overbought_prices],
            "Low": [p * 0.98 for p in moderate_overbought_prices],
            "Close": moderate_overbought_prices,
            "Volume": [1000000] * 150,
        }, index=pd.date_range('2023-01-01', periods=150, freq='D'))

        mock_port.get_data.return_value = df

        now = datetime.now(UTC)
        signals = engine.generate_signals(mock_port, now)

        if signals and "BTAL" in signals[0].reasoning:
            signal = signals[0]
            # Portfolio signal should map to primary symbol
            assert signal.symbol.value == "UVXY"
            assert signal.target_allocation.value == Decimal("1.0")  # 100% for defensive portfolio

    def test_validate_market_data_availability(
        self, engine: NuclearTypedEngine, mock_port: Mock
    ) -> None:
        """Test market data validation."""
        # Should pass with mock data
        result = engine.validate_market_data_availability(mock_port)
        assert result is True

        # Test with some symbols unavailable
        mock_port.get_current_price.side_effect = lambda symbol: None if symbol == "SPY" else 100.0

        from the_alchemiser.services.errors.exceptions import ValidationError
        with pytest.raises(ValidationError):
            engine.validate_market_data_availability(mock_port)

    def test_safe_generate_signals_with_error(
        self, engine: NuclearTypedEngine
    ) -> None:
        """Test safe signal generation handles errors gracefully."""
        mock_port = Mock(spec=MarketDataPort)
        mock_port.get_data.side_effect = Exception("Network error")

        now = datetime.now(UTC)
        signals = engine.safe_generate_signals(mock_port, now)

        # Should return empty list on error
        assert signals == []
