"""Business Unit: strategy | Status: current.

Test portfolio operators for DSL evaluation.

Tests portfolio construction operators including weight-equal,
weight-specified, weight-inverse-volatility, group, asset, and filter.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext
from the_alchemiser.strategy_v2.engines.dsl.operators.portfolio import (
    asset,
    collect_assets_from_value,
    filter_assets,
    group,
    weight_equal,
    weight_inverse_volatility,
    weight_specified,
)
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


@pytest.mark.unit
class TestCollectAssetsFromValue:
    """Test collect_assets_from_value helper function."""

    def test_collect_from_portfolio_fragment(self):
        """Test collecting assets from PortfolioFragment."""
        fragment = PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="test",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )
        assets = collect_assets_from_value(fragment)
        assert set(assets) == {"AAPL", "GOOGL"}

    def test_collect_from_string(self):
        """Test collecting assets from string."""
        assets = collect_assets_from_value("AAPL")
        assert assets == ["AAPL"]

    def test_collect_from_list(self):
        """Test collecting assets from nested list."""
        value = ["AAPL", "GOOGL", ["MSFT"]]
        assets = collect_assets_from_value(value)
        assert assets == ["AAPL", "GOOGL", "MSFT"]

    def test_collect_from_empty(self):
        """Test collecting from empty or unsupported values."""
        assert collect_assets_from_value([]) == []
        assert collect_assets_from_value(None) == []
        assert collect_assets_from_value(42) == []


@pytest.mark.unit
class TestWeightEqual:
    """Test weight_equal operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        return context

    def test_weight_equal_empty_args_raises_error(self, mock_context):
        """Test weight-equal with no arguments raises error.

        DSL strategies must always produce a non-empty allocation.
        """
        with pytest.raises(DslEvaluationError, match="requires at least one asset argument"):
            weight_equal([], mock_context)

    def test_weight_equal_single_asset(self, mock_context):
        """Test weight-equal with single asset."""
        mock_context.evaluate_node.return_value = "AAPL"
        args = [ASTNode.atom("AAPL")]

        result = weight_equal(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert result.weights == {"AAPL": Decimal("1.0")}

    def test_weight_equal_multiple_assets(self, mock_context):
        """Test weight-equal with multiple assets."""
        mock_context.evaluate_node.side_effect = ["AAPL", "GOOGL", "MSFT"]
        args = [ASTNode.atom("AAPL"), ASTNode.atom("GOOGL"), ASTNode.atom("MSFT")]

        result = weight_equal(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert len(result.weights) == 3
        assert all(abs(float(w) - 1.0 / 3) < 1e-10 for w in result.weights.values())

    def test_weight_equal_deduplication(self, mock_context):
        """Test weight-equal deduplicates symbols."""
        mock_context.evaluate_node.side_effect = ["AAPL", "GOOGL", "AAPL"]
        args = [ASTNode.atom("AAPL"), ASTNode.atom("GOOGL"), ASTNode.atom("AAPL")]

        result = weight_equal(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert len(result.weights) == 2
        assert result.weights == {"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")}

    def test_weight_equal_empty_result_raises_error(self, mock_context):
        """Test weight-equal raises error when all args evaluate to empty.

        DSL strategies must always produce a non-empty allocation.
        """
        # Simulate args that evaluate to empty lists (like filter returning no matches)
        mock_context.evaluate_node.side_effect = [[], []]
        args = [ASTNode.list_node([]), ASTNode.list_node([])]

        with pytest.raises(DslEvaluationError, match="evaluated to zero assets"):
            weight_equal(args, mock_context)


@pytest.mark.unit
class TestWeightSpecified:
    """Test weight_specified operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        context.as_decimal = Mock(side_effect=lambda x: Decimal(str(x)))
        return context

    def test_weight_specified_invalid_args_empty(self, mock_context):
        """Test weight-specified with empty args raises error."""
        with pytest.raises(DslEvaluationError, match="pairs of weight and asset"):
            weight_specified([], mock_context)

    def test_weight_specified_invalid_args_single(self, mock_context):
        """Test weight-specified with single arg raises error."""
        with pytest.raises(DslEvaluationError, match="pairs of weight and asset"):
            weight_specified([ASTNode.atom(Decimal("0.5"))], mock_context)

    def test_weight_specified_invalid_args_odd(self, mock_context):
        """Test weight-specified with odd number of args raises error."""
        args = [
            ASTNode.atom(Decimal("0.5")),
            ASTNode.atom("AAPL"),
            ASTNode.atom(Decimal("0.5")),
        ]
        with pytest.raises(DslEvaluationError, match="pairs of weight and asset"):
            weight_specified(args, mock_context)

    def test_weight_specified_basic(self, mock_context):
        """Test weight-specified with valid pairs."""
        mock_context.evaluate_node.side_effect = [0.6, "AAPL", 0.4, "GOOGL"]
        args = [
            ASTNode.atom(Decimal("0.6")),
            ASTNode.atom("AAPL"),
            ASTNode.atom(Decimal("0.4")),
            ASTNode.atom("GOOGL"),
        ]

        result = weight_specified(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert result.weights == {"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")}


@pytest.mark.unit
class TestWeightInverseVolatility:
    """Test weight_inverse_volatility operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        context.as_decimal = Mock(side_effect=lambda x: Decimal(str(x)))
        context.indicator_service = Mock()
        context.event_publisher = Mock()
        return context

    def test_weight_inverse_volatility_empty_args(self, mock_context):
        """Test weight-inverse-volatility with no arguments."""
        with pytest.raises(DslEvaluationError, match="requires window and assets"):
            weight_inverse_volatility([], mock_context)

    def test_weight_inverse_volatility_no_assets_raises_error(self, mock_context):
        """Test weight-inverse-volatility with window but no assets raises error.

        DSL strategies must always produce a non-empty allocation.
        """
        mock_context.evaluate_node.return_value = 6
        args = [ASTNode.atom(Decimal("6"))]

        with pytest.raises(DslEvaluationError, match="evaluated to zero assets"):
            weight_inverse_volatility(args, mock_context)

    def test_weight_inverse_volatility_basic(self, mock_context):
        """Test weight-inverse-volatility with valid data."""
        # Setup mocks
        mock_context.evaluate_node.side_effect = [6, "AAPL", "GOOGL"]

        # Mock indicator for AAPL with volatility = 0.2
        indicator_aapl = Mock(spec=TechnicalIndicator)
        indicator_aapl.stdev_return_6 = 0.2
        indicator_aapl.metadata = {}

        # Mock indicator for GOOGL with volatility = 0.4
        indicator_googl = Mock(spec=TechnicalIndicator)
        indicator_googl.stdev_return_6 = 0.4
        indicator_googl.metadata = {}

        mock_context.indicator_service.get_indicator.side_effect = [
            indicator_aapl,
            indicator_googl,
        ]

        args = [
            ASTNode.atom(Decimal("6")),
            ASTNode.atom("AAPL"),
            ASTNode.atom("GOOGL"),
        ]

        result = weight_inverse_volatility(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert "AAPL" in result.weights
        assert "GOOGL" in result.weights

        # AAPL has lower volatility (0.2), so it should have higher weight
        # inverse weights: AAPL=5.0, GOOGL=2.5, total=7.5
        # normalized: AAPL=5.0/7.5≈0.667, GOOGL=2.5/7.5≈0.333
        assert abs(float(result.weights["AAPL"]) - 2.0 / 3) < 1e-10
        assert abs(float(result.weights["GOOGL"]) - 1.0 / 3) < 1e-10


@pytest.mark.unit
class TestAsset:
    """Test asset operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        return context

    def test_asset_empty_args(self, mock_context):
        """Test asset with no arguments."""
        with pytest.raises(DslEvaluationError, match="requires at least 1 argument"):
            asset([], mock_context)

    def test_asset_valid(self, mock_context):
        """Test asset with valid symbol."""
        mock_context.evaluate_node.return_value = "AAPL"
        args = [ASTNode.atom("AAPL")]

        result = asset(args, mock_context)
        assert result == "AAPL"

    def test_asset_non_string(self, mock_context):
        """Test asset with non-string value."""
        mock_context.evaluate_node.return_value = 42
        args = [ASTNode.atom(Decimal("42"))]

        with pytest.raises(DslEvaluationError, match="must be string"):
            asset(args, mock_context)


@pytest.mark.unit
class TestGroup:
    """Test group operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        return context

    def test_group_insufficient_args(self, mock_context):
        """Test group with insufficient arguments."""
        with pytest.raises(DslEvaluationError, match="requires at least 2 arguments"):
            group([ASTNode.atom("test-group")], mock_context)

    def test_group_combines_fragments(self, mock_context):
        """Test group combines portfolio fragments."""
        fragment1 = PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="test",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )
        fragment2 = PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="test",
            weights={"MSFT": Decimal("1.0")},
        )

        mock_context.evaluate_node.side_effect = [fragment1, fragment2]
        args = [
            ASTNode.atom("test-group"),
            ASTNode.list_node([]),
            ASTNode.list_node([]),
        ]

        result = group(args, mock_context)
        assert isinstance(result, PortfolioFragment)
        assert "AAPL" in result.weights
        assert "GOOGL" in result.weights
        assert "MSFT" in result.weights


@pytest.mark.unit
class TestFilter:
    """Test filter_assets operator."""

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = str(uuid.uuid4())
        context.trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )
        context.evaluate_node = Mock()
        context.as_decimal = Mock(side_effect=lambda x: Decimal(str(x)))
        return context

    def test_filter_insufficient_args(self, mock_context):
        """Test filter with insufficient arguments."""
        with pytest.raises(DslEvaluationError, match="requires 2 or 3 arguments"):
            filter_assets([ASTNode.atom("condition")], mock_context)

    def test_filter_too_many_args(self, mock_context):
        """Test filter with too many arguments."""
        args = [
            ASTNode.atom("condition"),
            ASTNode.atom("selection"),
            ASTNode.atom("portfolio"),
            ASTNode.atom("extra"),
        ]
        with pytest.raises(DslEvaluationError, match="requires 2 or 3 arguments"):
            filter_assets(args, mock_context)
