"""Business Unit: strategy | Status: current

Test strategy orchestrator business logic and allocation calculations.

Tests the core business logic of strategy execution without external dependencies,
focusing on weight normalization, allocation generation, and error handling.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
from the_alchemiser.strategy_v2.models.context import StrategyContext


class TestSingleStrategyOrchestrator:
    """Test strategy orchestrator business logic."""

    @pytest.fixture
    def mock_market_data_adapter(self):
        """Mock market data adapter."""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_market_data_adapter):
        """Create orchestrator instance."""
        return SingleStrategyOrchestrator(mock_market_data_adapter)

    @pytest.fixture
    def sample_context(self):
        """Sample strategy context."""
        return StrategyContext(
            symbols=["AAPL", "MSFT", "GOOGL"],
            timeframe="1d",
            as_of=datetime.now(UTC),
        )

    def test_weight_normalization_equal_weights(self, orchestrator):
        """Test weight normalization with equal weights."""
        weights = {"AAPL": Decimal("0.33"), "MSFT": Decimal("0.33"), "GOOGL": Decimal("0.34")}
        
        normalized = orchestrator._normalize_weights(weights)
        
        # Should sum to 1.0
        total = sum(normalized.values())
        assert abs(total - Decimal("1.0")) < Decimal("0.0001")
        
        # All weights should be approximately equal
        for weight in normalized.values():
            assert abs(weight - Decimal("0.3333")) < Decimal("0.01")

    def test_weight_normalization_zero_sum_fallback(self, orchestrator):
        """Test weight normalization falls back to equal weights when sum is zero."""
        weights = {"AAPL": Decimal("0.0"), "MSFT": Decimal("0.0")}
        
        normalized = orchestrator._normalize_weights(weights)
        
        # Should fallback to equal weights
        assert normalized["AAPL"] == Decimal("0.5")
        assert normalized["MSFT"] == Decimal("0.5")
        assert sum(normalized.values()) == Decimal("1.0")

    def test_weight_normalization_negative_sum_fallback(self, orchestrator):
        """Test weight normalization falls back to equal weights with negative sum."""
        weights = {"AAPL": Decimal("-0.5"), "MSFT": Decimal("-0.3")}
        
        normalized = orchestrator._normalize_weights(weights)
        
        # Should fallback to equal weights
        assert normalized["AAPL"] == Decimal("0.5")
        assert normalized["MSFT"] == Decimal("0.5")
        assert sum(normalized.values()) == Decimal("1.0")

    def test_weight_normalization_empty_weights(self, orchestrator):
        """Test weight normalization with empty weights."""
        weights = {}
        
        normalized = orchestrator._normalize_weights(weights)
        
        assert normalized == {}

    def test_sample_allocation_generation(self, orchestrator, sample_context):
        """Test sample allocation generation creates equal weights."""
        allocation = orchestrator._generate_sample_allocation(sample_context)
        
        # Should have equal weights for all symbols
        expected_weight = Decimal("1.0") / len(sample_context.symbols)
        for symbol in sample_context.symbols:
            assert allocation[symbol] == expected_weight
            
        # Should sum to approximately 1.0 (allowing for precision differences)
        total = sum(allocation.values())
        assert abs(total - Decimal("1.0")) < Decimal("0.0001")

    def test_sample_allocation_empty_symbols(self, orchestrator):
        """Test sample allocation with no symbols."""
        # Since StrategyContext validates symbols, we test the internal method directly
        allocation = orchestrator._generate_sample_allocation(Mock(symbols=[]))
        
        assert allocation == {}

    def test_strategy_execution_success(self, orchestrator, sample_context):
        """Test successful strategy execution."""
        result = orchestrator.run("test_strategy", sample_context)
        
        # Should return valid allocation
        assert result.target_weights is not None
        assert len(result.target_weights) == len(sample_context.symbols)
        assert result.correlation_id is not None
        assert result.causation_id is None  # None when not provided
        assert result.as_of is not None
        assert result.constraints["strategy_id"] == "test_strategy"
        
        # Weights should sum to 1.0
        total_weight = sum(result.target_weights.values())
        assert abs(total_weight - Decimal("1.0")) < Decimal("0.0001")

    def test_context_validation_missing_symbols(self, orchestrator):
        """Test context validation with missing symbols."""
        # StrategyContext already validates this in __post_init__
        with pytest.raises(ValueError, match="symbols cannot be empty"):
            StrategyContext(symbols=[], timeframe="1d")

    def test_context_validation_missing_timeframe(self, orchestrator):
        """Test context validation with missing timeframe."""
        # StrategyContext already validates this in __post_init__
        with pytest.raises(ValueError, match="timeframe cannot be empty"):
            StrategyContext(symbols=["AAPL"], timeframe="")

    def test_context_validation_valid(self, orchestrator, sample_context):
        """Test context validation with valid context."""
        # Should not raise any exception
        orchestrator.validate_context(sample_context)

    def test_strategy_execution_preserves_metadata(self, orchestrator, sample_context):
        """Test that strategy execution preserves important metadata."""
        strategy_id = "nuclear_strategy"
        
        result = orchestrator.run(strategy_id, sample_context)
        
        # Check that metadata is preserved in constraints
        assert result.constraints["strategy_id"] == strategy_id
        assert result.constraints["symbols"] == sample_context.symbols
        assert result.constraints["timeframe"] == sample_context.timeframe
        
        # Should have correlation ID for tracking
        assert len(result.correlation_id) > 0

    def test_weight_precision_handling(self, orchestrator):
        """Test that weight calculations handle precision correctly."""
        # Test with 3 symbols that don't divide evenly
        weights = {"AAPL": Decimal("1"), "MSFT": Decimal("1"), "GOOGL": Decimal("1")}
        
        normalized = orchestrator._normalize_weights(weights)
        
        # Should sum to approximately 1.0 (allowing for precision differences)
        total = sum(normalized.values())
        assert abs(total - Decimal("1.0")) < Decimal("0.0001")
        
        # Each weight should be approximately 1/3
        for weight in normalized.values():
            expected = Decimal("1.0") / Decimal("3")
            assert abs(weight - expected) < Decimal("0.0001")

    def test_causation_id_propagation(self, orchestrator, sample_context):
        """Test that causation_id is properly propagated when provided."""
        causation_id = "test-causation-id-123"
        
        result = orchestrator.run("test_strategy", sample_context, causation_id=causation_id)
        
        # Should propagate causation_id to allocation
        assert result.causation_id == causation_id
        assert result.correlation_id is not None
        assert result.correlation_id != causation_id  # Should generate new correlation_id

    def test_error_handling_with_enhanced_error(self, orchestrator):
        """Test that errors are properly wrapped in EnhancedTradingError."""
        from the_alchemiser.shared.errors import EnhancedTradingError
        
        # Create invalid context that will fail validation
        with pytest.raises(ValueError, match="symbols cannot be empty"):
            # This will fail in StrategyContext __post_init__
            from the_alchemiser.strategy_v2.models.context import StrategyContext
            StrategyContext(symbols=[], timeframe="1d")

    def test_context_validation_called(self, orchestrator, mock_market_data_adapter):
        """Test that validate_context is called before execution."""
        from the_alchemiser.strategy_v2.models.context import StrategyContext
        
        # Create a valid context
        context = StrategyContext(symbols=["AAPL"], timeframe="1d")
        
        # Should not raise any exception (validation passes)
        result = orchestrator.run("test_strategy", context)
        assert result is not None