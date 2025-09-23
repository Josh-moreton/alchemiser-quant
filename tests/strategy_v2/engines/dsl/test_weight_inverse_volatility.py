#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Unit tests for weight-inverse-volatility operator with real indicator computation.

Tests the DSL weight-inverse-volatility operator that computes real volatility
using the IndicatorService stdev_return indicator instead of mocked values.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import (
    IndicatorRequestDTO,
    PortfolioFragmentDTO,
)
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext
from the_alchemiser.strategy_v2.engines.dsl.events import DslEventPublisher
from the_alchemiser.strategy_v2.engines.dsl.operators.portfolio import weight_inverse_volatility
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


class TestWeightInverseVolatility:
    """Test weight-inverse-volatility operator with real indicator computation."""

    def test_weight_inverse_volatility_with_real_indicators(self) -> None:
        """Test weight-inverse-volatility computes real volatility from indicators."""
        # Mock indicator service that returns synthetic volatility values
        mock_indicator_service = Mock()
        mock_event_publisher = Mock()
        
        # Define test volatilities for symbols
        test_volatilities = {
            "SPY": 0.20,  # 20% volatility
            "QQQ": 0.25,  # 25% volatility 
            "TLT": 0.15,  # 15% volatility
        }
        
        def mock_get_indicator(request: IndicatorRequestDTO) -> TechnicalIndicatorDTO:
            symbol = request.symbol
            volatility = test_volatilities.get(symbol, 0.25)  # Default 25%
            
            return TechnicalIndicatorDTO(
                symbol=symbol,
                timestamp=datetime.now(UTC),
                current_price=None,
                stdev_return_6=volatility,
                data_source="test_data",
                metadata={"value": volatility, "window": request.parameters.get("window", 6)},
            )
        
        mock_indicator_service.get_indicator.side_effect = mock_get_indicator
        
        # Mock evaluate_node function
        def mock_evaluate_node(node: ASTNodeDTO, correlation_id: str, trace: TraceDTO) -> str | int | list[str]:
            if node.value == Decimal("6"):  # window parameter
                return 6
            if node.get_symbol_name() == "test-assets":  # asset list symbol
                return ["SPY", "QQQ", "TLT"]
            return node.value
        
        # Create context
        context = DslContext(
            indicator_service=mock_indicator_service,
            event_publisher=mock_event_publisher,
            correlation_id=str(uuid.uuid4()),
            trace=TraceDTO(
                trace_id="test",
                correlation_id=str(uuid.uuid4()),
                strategy_id="test_strategy",
                started_at=datetime.now(UTC),
                entries=[],
            ),
            evaluate_node=mock_evaluate_node,
        )
        
        # Create test arguments: window=6, assets=["SPY", "QQQ", "TLT"]
        window_node = ASTNodeDTO.atom(Decimal("6"))
        assets_node = ASTNodeDTO.symbol("test-assets")  # This will be mocked in evaluate_node
        args = [window_node, assets_node]
        
        # Execute weight_inverse_volatility
        result = weight_inverse_volatility(args, context)
        
        # Verify result is a PortfolioFragmentDTO
        assert isinstance(result, PortfolioFragmentDTO)
        assert result.source_step == "weight_inverse_volatility"
        assert len(result.weights) == 3
        
        # Verify weights are properly normalized (sum to 1.0)
        total_weight = sum(result.weights.values())
        assert math.isclose(total_weight, 1.0, rel_tol=1e-9), f"Weights sum to {total_weight}, expected 1.0"
        
        # Verify inverse volatility weighting logic: higher volatility = lower weight
        # Expected inverse weights: SPY=1/0.20=5.0, QQQ=1/0.25=4.0, TLT=1/0.15=6.67
        # Total inverse = 15.67, normalized: SPY=5.0/15.67≈0.319, QQQ=4.0/15.67≈0.255, TLT=6.67/15.67≈0.426
        spy_weight = result.weights["SPY"]
        qqq_weight = result.weights["QQQ"]
        tlt_weight = result.weights["TLT"]
        
        # TLT should have highest weight (lowest volatility)
        assert tlt_weight > spy_weight, f"TLT weight {tlt_weight} should be > SPY weight {spy_weight}"
        assert tlt_weight > qqq_weight, f"TLT weight {tlt_weight} should be > QQQ weight {qqq_weight}"
        
        # SPY should have higher weight than QQQ (lower volatility)
        assert spy_weight > qqq_weight, f"SPY weight {spy_weight} should be > QQQ weight {qqq_weight}"
        
        # Verify expected approximate weights with tolerance
        expected_spy = 5.0 / (5.0 + 4.0 + 6.666667)  # ≈ 0.319
        expected_qqq = 4.0 / (5.0 + 4.0 + 6.666667)  # ≈ 0.255
        expected_tlt = 6.666667 / (5.0 + 4.0 + 6.666667)  # ≈ 0.426
        
        assert math.isclose(spy_weight, expected_spy, rel_tol=1e-3), f"SPY weight {spy_weight} vs expected {expected_spy}"
        assert math.isclose(qqq_weight, expected_qqq, rel_tol=1e-3), f"QQQ weight {qqq_weight} vs expected {expected_qqq}"
        assert math.isclose(tlt_weight, expected_tlt, rel_tol=1e-3), f"TLT weight {tlt_weight} vs expected {expected_tlt}"
        
        # Verify indicator service was called correctly for each symbol
        assert mock_indicator_service.get_indicator.call_count == 3
        
        # Verify each call had correct parameters
        calls = mock_indicator_service.get_indicator.call_args_list
        symbols_called = {call[0][0].symbol for call in calls}
        assert symbols_called == {"SPY", "QQQ", "TLT"}
        
        # Verify all calls used stdev_return indicator with window=6
        for call in calls:
            request = call[0][0]
            assert request.indicator_type == "stdev_return"
            assert request.parameters["window"] == 6

    def test_weight_inverse_volatility_handles_missing_indicators(self) -> None:
        """Test weight-inverse-volatility handles missing indicator data gracefully."""
        mock_indicator_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock indicator service that throws for some symbols
        def mock_get_indicator(request: IndicatorRequestDTO) -> TechnicalIndicatorDTO:
            if request.symbol == "UNKNOWN":
                from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError
                raise DslEvaluationError(f"No stdev-return for {request.symbol}")
            
            # Return data for known symbols
            return TechnicalIndicatorDTO(
                symbol=request.symbol,
                timestamp=datetime.now(UTC),
                current_price=None,
                stdev_return_6=0.20,
                data_source="test_data",
                metadata={"value": 0.20, "window": 6},
            )
        
        mock_indicator_service.get_indicator.side_effect = mock_get_indicator
        
        def mock_evaluate_node(node: ASTNodeDTO, correlation_id: str, trace: TraceDTO) -> str | int | list[str]:
            if node.value == Decimal("6"):
                return 6
            if node.get_symbol_name() == "test-assets":
                return ["SPY", "UNKNOWN"]
            return node.value
        
        context = DslContext(
            indicator_service=mock_indicator_service,
            event_publisher=mock_event_publisher,
            correlation_id=str(uuid.uuid4()),
            trace=TraceDTO(
                trace_id="test",
                correlation_id=str(uuid.uuid4()),
                strategy_id="test_strategy",
                started_at=datetime.now(UTC),
                entries=[],
            ),
            evaluate_node=mock_evaluate_node,
        )
        
        window_node = ASTNodeDTO.atom(Decimal("6"))
        assets_node = ASTNodeDTO.symbol("test-assets")
        args = [window_node, assets_node]
        
        # Should skip UNKNOWN and only weight SPY
        result = weight_inverse_volatility(args, context)
        
        assert isinstance(result, PortfolioFragmentDTO)
        assert len(result.weights) == 1
        assert "SPY" in result.weights
        assert "UNKNOWN" not in result.weights
        assert math.isclose(result.weights["SPY"], 1.0, rel_tol=1e-9)

    def test_weight_inverse_volatility_empty_assets(self) -> None:
        """Test weight-inverse-volatility with empty asset list."""
        mock_indicator_service = Mock()
        mock_event_publisher = Mock()
        
        def mock_evaluate_node(node: ASTNodeDTO, correlation_id: str, trace: TraceDTO) -> str | int | list[str]:
            if node.value == Decimal("6"):
                return 6
            if node.get_symbol_name() == "test-assets":
                return []
            return node.value
        
        context = DslContext(
            indicator_service=mock_indicator_service,
            event_publisher=mock_event_publisher,
            correlation_id=str(uuid.uuid4()),
            trace=TraceDTO(
                trace_id="test",
                correlation_id=str(uuid.uuid4()),
                strategy_id="test_strategy",
                started_at=datetime.now(UTC),
                entries=[],
            ),
            evaluate_node=mock_evaluate_node,
        )
        
        window_node = ASTNodeDTO.atom(Decimal("6"))
        assets_node = ASTNodeDTO.symbol("test-assets")
        args = [window_node, assets_node]
        
        result = weight_inverse_volatility(args, context)
        
        assert isinstance(result, PortfolioFragmentDTO)
        assert len(result.weights) == 0
        assert result.source_step == "weight_inverse_volatility"

    def test_weight_inverse_volatility_requires_window_and_assets(self) -> None:
        """Test weight-inverse-volatility raises error without required arguments."""
        mock_indicator_service = Mock()
        mock_event_publisher = Mock()
        
        context = DslContext(
            indicator_service=mock_indicator_service,
            event_publisher=mock_event_publisher,
            correlation_id=str(uuid.uuid4()),
            trace=TraceDTO(
                trace_id="test",
                correlation_id=str(uuid.uuid4()),
                strategy_id="test_strategy",
                started_at=datetime.now(UTC),
                entries=[],
            ),
            evaluate_node=Mock(),
        )
        
        # Empty args should raise error
        with pytest.raises(DslEvaluationError, match="weight-inverse-volatility requires window and assets"):
            weight_inverse_volatility([], context)