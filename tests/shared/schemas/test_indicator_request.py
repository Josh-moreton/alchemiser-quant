"""Business Unit: shared | Status: current.

Unit tests for indicator_request DTOs.

Tests the IndicatorRequest and PortfolioFragment DTOs to ensure proper
validation, immutability, schema versioning, and event traceability.
"""

import math
import uuid

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.indicator_request import (
    IndicatorRequest,
    PortfolioFragment,
)


@pytest.mark.unit
class TestIndicatorRequest:
    """Test IndicatorRequest DTO."""

    def test_create_valid_request(self) -> None:
        """Test creating a valid indicator request."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            indicator_type="rsi",
            parameters={"window": 14},
        )

        assert request.request_id == "req-123"
        assert request.correlation_id == "corr-456"
        assert request.symbol == "AAPL"
        assert request.indicator_type == "rsi"
        assert request.parameters == {"window": 14}
        assert request.schema_version == "1.0"
        assert request.causation_id is None

    def test_request_with_causation_id(self) -> None:
        """Test creating request with causation_id."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            causation_id="cause-789",
            symbol="AAPL",
            indicator_type="rsi",
            parameters={"window": 14},
        )

        assert request.causation_id == "cause-789"

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="aapl",  # lowercase
            indicator_type="rsi",
            parameters={"window": 14},
        )

        assert request.symbol == "AAPL"

    def test_symbol_with_special_chars(self) -> None:
        """Test symbol with dots and dashes is accepted."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="brk.b",
            indicator_type="rsi",
            parameters={},
        )

        assert request.symbol == "BRK.B"

    def test_invalid_symbol_format(self) -> None:
        """Test that invalid symbol format raises error."""
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            IndicatorRequest(
                request_id="req-123",
                correlation_id="corr-456",
                symbol="@#$%",
                indicator_type="rsi",
                parameters={},
            )

    def test_indicator_type_literal_validation(self) -> None:
        """Test that indicator_type is validated against known types."""
        # Valid indicator type
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            indicator_type="moving_average",
            parameters={},
        )
        assert request.indicator_type == "moving_average"

        # Invalid indicator type should raise ValidationError
        with pytest.raises(ValidationError):
            IndicatorRequest(
                request_id="req-123",
                correlation_id="corr-456",
                symbol="AAPL",
                indicator_type="invalid_indicator",  # type: ignore[arg-type]
                parameters={},
            )

    def test_parameters_type_validation(self) -> None:
        """Test that parameters dict validates types."""
        # Valid parameter types
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            indicator_type="rsi",
            parameters={"window": 14, "threshold": 70.0, "name": "test"},
        )
        assert request.parameters == {"window": 14, "threshold": 70.0, "name": "test"}

    def test_request_is_frozen(self) -> None:
        """Test that IndicatorRequest is immutable."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            indicator_type="rsi",
            parameters={"window": 14},
        )

        with pytest.raises(ValidationError, match="frozen"):
            request.symbol = "GOOGL"  # type: ignore[misc]

    def test_rsi_request_factory(self) -> None:
        """Test RSI request factory method."""
        request = IndicatorRequest.rsi_request(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            window=21,
        )

        assert request.request_id == "req-123"
        assert request.correlation_id == "corr-456"
        assert request.symbol == "AAPL"
        assert request.indicator_type == "rsi"
        assert request.parameters == {"window": 21}
        assert request.schema_version == "1.0"

    def test_rsi_request_factory_with_causation(self) -> None:
        """Test RSI request factory with causation_id."""
        request = IndicatorRequest.rsi_request(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            causation_id="cause-789",
        )

        assert request.causation_id == "cause-789"

    def test_moving_average_request_factory(self) -> None:
        """Test moving average request factory method."""
        request = IndicatorRequest.moving_average_request(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            window=50,
        )

        assert request.request_id == "req-123"
        assert request.indicator_type == "moving_average"
        assert request.parameters == {"window": 50}

    def test_model_dump_includes_all_fields(self) -> None:
        """Test that model_dump includes all fields including schema_version."""
        request = IndicatorRequest(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
            indicator_type="rsi",
            parameters={"window": 14},
        )

        data = request.model_dump()
        assert "schema_version" in data
        assert data["schema_version"] == "1.0"
        assert data["causation_id"] is None


@pytest.mark.unit
class TestPortfolioFragment:
    """Test PortfolioFragment DTO."""

    def test_create_valid_fragment(self) -> None:
        """Test creating a valid portfolio fragment."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="weight_equal",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        assert fragment.fragment_id == "frag-123"
        assert fragment.source_step == "weight_equal"
        assert fragment.weights == {"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")}
        assert fragment.total_weight == Decimal("1.0")
        assert fragment.schema_version == "1.0"
        assert fragment.correlation_id is None
        assert fragment.causation_id is None

    def test_fragment_with_traceability_ids(self) -> None:
        """Test creating fragment with correlation and causation IDs."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="weight_equal",
            correlation_id="corr-456",
            causation_id="cause-789",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        assert fragment.correlation_id == "corr-456"
        assert fragment.causation_id == "cause-789"

    def test_fragment_is_frozen(self) -> None:
        """Test that PortfolioFragment is immutable."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="weight_equal",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        with pytest.raises(ValidationError, match="frozen"):
            fragment.fragment_id = "frag-456"  # type: ignore[misc]

    def test_normalize_weights_basic(self) -> None:
        """Test basic weight normalization."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={"AAPL": Decimal("2.0"), "GOOGL": Decimal("2.0")},
            total_weight=Decimal("1.0"),
        )

        normalized = fragment.normalize_weights()

        # Should sum to 1.0
        assert math.isclose(float(sum(normalized.weights.values())), 1.0, abs_tol=1e-9)
        assert math.isclose(float(normalized.weights["AAPL"]), 0.5, abs_tol=1e-9)
        assert math.isclose(float(normalized.weights["GOOGL"]), 0.5, abs_tol=1e-9)

    def test_normalize_weights_empty(self) -> None:
        """Test normalizing empty weights returns self."""
        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={},
        )

        normalized = fragment.normalize_weights()
        assert normalized.weights == {}
        assert normalized is fragment  # Should return self

    def test_normalize_weights_zero_sum(self) -> None:
        """Test normalizing zero sum weights returns self."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={"AAPL": Decimal("0.0"), "GOOGL": Decimal("0.0")},
        )

        normalized = fragment.normalize_weights()
        assert normalized is fragment  # Should return self

    def test_normalize_weights_uses_isclose(self) -> None:
        """Test that normalize_weights uses math.isclose for float comparison."""
        from decimal import Decimal

        # Create weights that sum to very close to zero but not exactly
        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={"AAPL": Decimal("1e-10"), "GOOGL": Decimal("-1e-10")},
        )

        normalized = fragment.normalize_weights()
        # Should detect this as zero and return self
        assert normalized is fragment

    def test_normalize_weights_idempotent(self) -> None:
        """Test that normalizing twice gives same result."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={"AAPL": Decimal("2.0"), "GOOGL": Decimal("3.0")},
        )

        normalized_once = fragment.normalize_weights()
        normalized_twice = normalized_once.normalize_weights()

        # Should be idempotent
        assert math.isclose(
            float(normalized_once.weights["AAPL"]),
            float(normalized_twice.weights["AAPL"]),
            abs_tol=1e-9,
        )
        assert math.isclose(
            float(normalized_once.weights["GOOGL"]),
            float(normalized_twice.weights["GOOGL"]),
            abs_tol=1e-9,
        )

    def test_normalize_weights_preserves_other_fields(self) -> None:
        """Test that normalizing weights preserves other fields."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            correlation_id="corr-456",
            causation_id="cause-789",
            weights={"AAPL": Decimal("2.0"), "GOOGL": Decimal("2.0")},
            metadata={"key": "value"},
        )

        normalized = fragment.normalize_weights()

        assert normalized.fragment_id == "frag-123"
        assert normalized.source_step == "test"
        assert normalized.correlation_id == "corr-456"
        assert normalized.causation_id == "cause-789"
        assert normalized.metadata == {"key": "value"}

    def test_total_weight_constraint(self) -> None:
        """Test that total_weight is constrained between 0 and 1."""
        from decimal import Decimal

        # Valid total_weight
        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={},
            total_weight=Decimal("0.5"),
        )
        assert fragment.total_weight == Decimal("0.5")

        # Invalid total_weight > 1
        with pytest.raises(ValidationError):
            PortfolioFragment(
                fragment_id="frag-123",
                source_step="test",
                weights={},
                total_weight=Decimal("1.5"),
            )

        # Invalid total_weight < 0
        with pytest.raises(ValidationError):
            PortfolioFragment(
                fragment_id="frag-123",
                source_step="test",
                weights={},
                total_weight=Decimal("-0.5"),
            )

    def test_model_dump_includes_all_fields(self) -> None:
        """Test that model_dump includes all fields including schema_version."""
        from decimal import Decimal

        fragment = PortfolioFragment(
            fragment_id="frag-123",
            source_step="test",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        data = fragment.model_dump()
        assert "schema_version" in data
        assert data["schema_version"] == "1.0"
        assert data["correlation_id"] is None
        assert data["causation_id"] is None


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_indicator_request_without_new_fields(self) -> None:
        """Test that existing code works without specifying new fields."""
        # This is how existing code creates IndicatorRequest
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            correlation_id="corr-123",
            symbol="AAPL",
            indicator_type="current_price",
            parameters={},
        )

        # Should work with defaults
        assert request.schema_version == "1.0"
        assert request.causation_id is None

    def test_portfolio_fragment_without_new_fields(self) -> None:
        """Test that existing code works without specifying new fields."""
        from decimal import Decimal

        # This is how existing code creates PortfolioFragment
        fragment = PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_equal",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        # Should work with defaults
        assert fragment.schema_version == "1.0"
        assert fragment.correlation_id is None
        assert fragment.causation_id is None

    def test_factory_methods_backward_compatible(self) -> None:
        """Test that factory methods work without causation_id."""
        # Existing usage without causation_id
        rsi_request = IndicatorRequest.rsi_request(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
        )

        ma_request = IndicatorRequest.moving_average_request(
            request_id="req-123",
            correlation_id="corr-456",
            symbol="AAPL",
        )

        assert rsi_request.causation_id is None
        assert ma_request.causation_id is None
