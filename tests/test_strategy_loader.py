"""Test the DSL strategy loader functionality."""

import pytest
from unittest.mock import Mock
import pandas as pd
import tempfile
from pathlib import Path
from decimal import Decimal

from the_alchemiser.domain.dsl.strategy_loader import StrategyLoader, StrategyResult
from the_alchemiser.domain.dsl.errors import DSLError
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


class TestStrategyLoader:
    """Test DSL strategy loader functionality."""
    
    @pytest.fixture
    def mock_market_data_port(self) -> Mock:
        """Create mock market data port."""
        mock_port = Mock(spec=MarketDataPort)
        
        # Mock normal price data
        price_data = pd.DataFrame({
            'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
            'volume': [1000] * 10
        })
        mock_port.get_data.return_value = price_data
        mock_port.get_current_price.return_value = 109.0
        
        return mock_port
    
    @pytest.fixture
    def strategy_loader(self, mock_market_data_port: Mock) -> StrategyLoader:
        """Create strategy loader."""
        return StrategyLoader(mock_market_data_port)
    
    def test_load_strategy_file(self, strategy_loader: StrategyLoader) -> None:
        """Test loading strategy from file."""
        # Create a temporary strategy file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.clj', delete=False) as f:
            f.write('(asset "SPY" "S&P 500 ETF")')
            temp_path = f.name
        
        try:
            # Load the file
            source_code = strategy_loader.load_strategy_file(temp_path)
            assert source_code == '(asset "SPY" "S&P 500 ETF")'
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_load_nonexistent_file(self, strategy_loader: StrategyLoader) -> None:
        """Test error handling for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            strategy_loader.load_strategy_file("/nonexistent/file.clj")
    
    def test_evaluate_simple_strategy(self, strategy_loader: StrategyLoader) -> None:
        """Test evaluating simple strategy."""
        strategy_code = '(asset "SPY" "S&P 500 ETF")'
        
        portfolio, trace = strategy_loader.evaluate_strategy(strategy_code)
        
        # Should produce single-asset portfolio
        assert isinstance(portfolio, dict)
        assert portfolio == {"SPY": pytest.approx(Decimal('1.0'))}
        
        # Should have trace entries
        assert isinstance(trace, list)
        assert len(trace) > 0
        
        # Should have portfolio construction trace
        portfolio_trace = next((entry for entry in trace if entry["type"] == "portfolio"), None)
        assert portfolio_trace is not None
    
    def test_evaluate_conditional_strategy(self, strategy_loader: StrategyLoader) -> None:
        """Test evaluating conditional strategy."""
        strategy_code = '''
        (if (> (rsi "SPY" {:window 10}) 50)
            (weight-equal 
                (asset "TQQQ" "ProShares UltraPro QQQ")
                (asset "UPRO" "ProShares UltraPro S&P 500"))
            (asset "UVXY" "ProShares Ultra VIX"))
        '''
        
        portfolio, trace = strategy_loader.evaluate_strategy(strategy_code)
        
        # Should produce valid portfolio
        assert isinstance(portfolio, dict)
        assert len(portfolio) > 0
        
        # All weights should sum to 1.0
        total_weight = sum(portfolio.values())
        assert abs(total_weight - Decimal('1.0')) < Decimal('1e-9')
        
        # Should have comprehensive trace
        assert len(trace) > 0
        
        # Should have RSI calculation
        rsi_trace = next((entry for entry in trace if entry["type"] == "indicator" and entry["indicator"] == "rsi"), None)
        assert rsi_trace is not None
        assert rsi_trace["symbol"] == "SPY"
        assert rsi_trace["window"] == 10
        
        # Should have comparison
        comparison_trace = next((entry for entry in trace if entry["type"] == "comparison"), None)
        assert comparison_trace is not None
    
    def test_evaluate_strategy_file(self, strategy_loader: StrategyLoader) -> None:
        """Test evaluating strategy from actual file."""
        # Use the test strategy file we created
        strategy_path = Path("test_strategies/simple_rsi.clj")
        if strategy_path.exists():
            portfolio, trace = strategy_loader.evaluate_strategy_file(strategy_path)
            
            # Should produce valid portfolio
            assert isinstance(portfolio, dict)
            assert len(portfolio) > 0
            
            # All weights should sum to 1.0
            total_weight = sum(portfolio.values())
            assert abs(total_weight - Decimal('1.0')) < Decimal('1e-9')
            
            # Should have trace
            assert len(trace) > 0
    
    def test_validate_portfolio_valid(self, strategy_loader: StrategyLoader) -> None:
        """Test portfolio validation with valid portfolio."""
        valid_portfolio = {"SPY": Decimal('0.6'), "QQQ": Decimal('0.4')}
        
        # Should not raise any exception
        strategy_loader.validate_portfolio(valid_portfolio)
    
    def test_validate_portfolio_invalid_sum(self, strategy_loader: StrategyLoader) -> None:
        """Test portfolio validation with invalid weight sum."""
        invalid_portfolio = {"SPY": Decimal('0.6'), "QQQ": Decimal('0.5')}  # Sums to 1.1
        
        with pytest.raises(ValueError, match="Portfolio weights sum"):
            strategy_loader.validate_portfolio(invalid_portfolio)
    
    def test_validate_portfolio_negative_weights(self, strategy_loader: StrategyLoader) -> None:
        """Test portfolio validation with negative weights."""
        invalid_portfolio = {"SPY": Decimal('1.2'), "QQQ": Decimal('-0.2')}  # Negative weight
        
        with pytest.raises(ValueError, match="negative weights"):
            strategy_loader.validate_portfolio(invalid_portfolio)
    
    def test_validate_portfolio_empty(self, strategy_loader: StrategyLoader) -> None:
        """Test portfolio validation with empty portfolio."""
        empty_portfolio = {}
        
        with pytest.raises(ValueError, match="Portfolio cannot be empty"):
            strategy_loader.validate_portfolio(empty_portfolio)
    
    def test_save_and_load_trace(self, strategy_loader: StrategyLoader) -> None:
        """Test saving trace to file."""
        strategy_code = '(asset "SPY" "S&P 500 ETF")'
        _, trace = strategy_loader.evaluate_strategy(strategy_code)
        
        # Save trace to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            strategy_loader.save_trace(trace, temp_path)
            
            # Verify file was created and contains valid JSON
            import json
            with open(temp_path, 'r') as f:
                loaded_trace = json.load(f)
            
            assert isinstance(loaded_trace, list)
            assert len(loaded_trace) == len(trace)
        finally:
            # Clean up
            Path(temp_path).unlink()


class TestStrategyResult:
    """Test strategy result container."""
    
    def test_strategy_result_creation(self) -> None:
        """Test creating strategy result."""
        portfolio = {"SPY": 0.6, "QQQ": 0.4}
        trace = [{"type": "test", "value": 1}]
        
        result = StrategyResult(portfolio, trace, "Test Strategy", {"version": "1.0"})
        
        assert result.portfolio == portfolio
        assert result.trace == trace
        assert result.strategy_name == "Test Strategy"
        assert result.metadata == {"version": "1.0"}
        assert result.num_positions == 2
        assert result.max_weight == 0.6
        assert result.min_weight == 0.4
    
    def test_strategy_result_top_positions(self) -> None:
        """Test getting top positions."""
        portfolio = {"SPY": 0.5, "QQQ": 0.3, "IWM": 0.2}
        trace = []
        
        result = StrategyResult(portfolio, trace)
        top_positions = result.get_top_positions(2)
        
        assert len(top_positions) == 2
        assert top_positions[0] == ("SPY", 0.5)
        assert top_positions[1] == ("QQQ", 0.3)
    
    def test_strategy_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        portfolio = {"SPY": 1.0}
        trace = [{"type": "test"}]
        
        result = StrategyResult(portfolio, trace, "Test")
        result_dict = result.to_dict()
        
        assert "strategy_name" in result_dict
        assert "portfolio" in result_dict
        assert "summary" in result_dict
        assert "trace" in result_dict
        assert result_dict["summary"]["num_positions"] == 1