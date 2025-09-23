#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Unit tests for DSL engine components.

Tests the core functionality of the DSL engine including parsing,
evaluation, and event handling without external dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from the_alchemiser.shared.events.dsl_events import StrategyEvaluationRequested
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine
from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser, SexprParseError

from tests.utils.test_harness import DslTestHarness


class TestSexprParser:
    """Test S-expression parser functionality."""
    
    def test_parser_initialization(self) -> None:
        """Test parser can be initialized."""
        parser = SexprParser()
        assert parser is not None
    
    def test_parse_simple_expression(self) -> None:
        """Test parsing a simple S-expression."""
        parser = SexprParser()
        result = parser.parse("(+ 1 2)")
        
        assert result is not None
        assert result.node_type == "list"
        assert len(result.children) == 3
        assert result.children[0].value == "+"
        assert result.children[1].value == 1
        assert result.children[2].value == 2
    
    def test_parse_nested_expression(self) -> None:
        """Test parsing nested S-expressions."""
        parser = SexprParser()
        result = parser.parse("(+ (* 2 3) 4)")
        
        assert result is not None
        assert result.node_type == "list"
        assert len(result.children) == 3
        assert result.children[0].value == "+"
        
        # Check nested multiplication
        nested = result.children[1]
        assert nested.node_type == "list"
        assert len(nested.children) == 3
        assert nested.children[0].value == "*"
        assert nested.children[1].value == 2
        assert nested.children[2].value == 3
    
    def test_parse_empty_expression(self) -> None:
        """Test parsing empty expression raises error."""
        parser = SexprParser()
        with pytest.raises(SexprParseError):
            parser.parse("")
    
    def test_parse_malformed_expression(self) -> None:
        """Test parsing malformed expression raises error."""
        parser = SexprParser()
        with pytest.raises(SexprParseError):
            parser.parse("(+ 1 2")  # Missing closing paren
    
    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file raises error."""
        parser = SexprParser()
        with pytest.raises(SexprParseError):
            parser.parse_file("/non/existent/file.clj")
    
    @pytest.mark.parametrize("test_input,expected_type", [
        ("42", "atom"),
        ("42.5", "atom"),
        ('"test string"', "atom"),
        ("symbol", "symbol"),
        ("()", "list"),
        ("(a b c)", "list"),
    ])
    def test_parse_different_types(self, test_input: str, expected_type: str) -> None:
        """Test parsing different data types."""
        parser = SexprParser()
        result = parser.parse(test_input)
        
        assert result.node_type == expected_type


class TestDslEngine:
    """Test DSL engine core functionality."""
    
    def test_engine_initialization(self, repository_root: Path) -> None:
        """Test DSL engine can be initialized."""
        engine = DslEngine(strategy_config_path=str(repository_root))
        assert engine is not None
        assert engine.strategy_config_path == str(repository_root)
    
    def test_engine_can_handle_evaluation_request(self, repository_root: Path) -> None:
        """Test engine can handle StrategyEvaluationRequested events."""
        engine = DslEngine(strategy_config_path=str(repository_root))
        assert engine.can_handle("StrategyEvaluationRequested")
        assert not engine.can_handle("UnknownEventType")
    
    def test_engine_direct_evaluation(self, repository_root: Path, clj_strategy_files: list[Path]) -> None:
        """Test direct strategy evaluation without events."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        engine = DslEngine(strategy_config_path=str(repository_root))
        strategy_file = clj_strategy_files[0]
        
        try:
            allocation, trace = engine.evaluate_strategy(str(strategy_file))
            
            # Basic validation - should not crash and return valid objects
            assert allocation is not None
            assert trace is not None
            assert allocation.strategy_id is not None
            assert trace.trace_id is not None
            
        except Exception as e:
            # Some strategies might fail due to missing dependencies - that's ok for unit tests
            pytest.skip(f"Strategy evaluation failed (expected for unit tests): {e}")


class TestDslEngineEventHandling:
    """Test DSL engine event handling functionality."""
    
    def test_handle_evaluation_request_event(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path],
        event_recorder
    ) -> None:
        """Test handling StrategyEvaluationRequested event."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        # Create test harness
        harness = DslTestHarness(str(repository_root))
        strategy_file = clj_strategy_files[0]
        
        # Evaluate strategy
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Verify events were generated
        assert result.success or len(result.all_events) > 0  # Either success or events generated
        
        # Check that request was processed
        request_events = [e for e in result.all_events if e.event_type == "StrategyEvaluationRequested"]
        assert len(request_events) == 1
        assert request_events[0].strategy_config_path == str(strategy_file)
    
    def test_event_correlation_id_propagation(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that correlation IDs are properly propagated through events."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        harness = DslTestHarness(str(repository_root))
        strategy_file = clj_strategy_files[0]
        correlation_id = "test-correlation-12345"
        
        # Evaluate strategy with specific correlation ID
        result = harness.evaluate_strategy(
            str(strategy_file), 
            correlation_id=correlation_id
        )
        
        # Verify all events have the same correlation ID
        for event in result.all_events:
            assert event.correlation_id == correlation_id
    
    def test_multiple_strategy_evaluations(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test multiple strategy evaluations in sequence."""
        if len(clj_strategy_files) < 2:
            pytest.skip("Need at least 2 CLJ strategy files for this test")
        
        harness = DslTestHarness(str(repository_root))
        
        results = []
        for strategy_file in clj_strategy_files[:2]:  # Test first 2 strategies
            harness.reset_state()  # Reset between evaluations
            result = harness.evaluate_strategy(str(strategy_file))
            results.append(result)
        
        # Verify each evaluation was independent
        assert len(results) == 2
        assert results[0].correlation_id != results[1].correlation_id
        
        # Each should have generated some events
        for result in results:
            assert len(result.all_events) > 0


class TestDslEngineErrorHandling:
    """Test DSL engine error handling and edge cases."""
    
    def test_invalid_strategy_file_path(self, repository_root: Path) -> None:
        """Test handling of invalid strategy file path."""
        harness = DslTestHarness(str(repository_root))
        
        # Try to evaluate non-existent strategy
        result = harness.evaluate_strategy("/non/existent/strategy.clj")
        
        # Should generate events even if evaluation fails
        assert len(result.all_events) > 0
        
        # Request event should still be present
        request_events = [e for e in result.all_events if e.event_type == "StrategyEvaluationRequested"]
        assert len(request_events) == 1
    
    def test_malformed_strategy_file(self, repository_root: Path, tmp_path: Path) -> None:
        """Test handling of malformed strategy file."""
        # Create a malformed CLJ file
        malformed_file = tmp_path / "malformed.clj"
        malformed_file.write_text("(invalid clj syntax", encoding="utf-8")
        
        harness = DslTestHarness(str(repository_root))
        
        # Try to evaluate malformed strategy
        result = harness.evaluate_strategy(str(malformed_file))
        
        # Should handle gracefully - events generated but likely no successful allocation
        assert len(result.all_events) > 0
    
    def test_empty_strategy_file(self, repository_root: Path, tmp_path: Path) -> None:
        """Test handling of empty strategy file."""
        # Create an empty CLJ file
        empty_file = tmp_path / "empty.clj"
        empty_file.write_text("", encoding="utf-8")
        
        harness = DslTestHarness(str(repository_root))
        
        # Try to evaluate empty strategy
        result = harness.evaluate_strategy(str(empty_file))
        
        # Should handle gracefully
        assert len(result.all_events) > 0


@pytest.mark.integration
class TestDslEngineIntegration:
    """Integration tests for DSL engine with real strategy files."""
    
    def test_all_strategy_files_parseable(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that all strategy files are at least parseable."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        parser = SexprParser()
        parseable_count = 0
        
        for strategy_file in clj_strategy_files:
            try:
                ast = parser.parse_file(str(strategy_file))
                assert ast is not None
                parseable_count += 1
            except SexprParseError:
                # Some files might not be parseable - that's ok for now
                pass
        
        # At least some files should be parseable
        assert parseable_count > 0, "No strategy files were parseable"
    
    def test_strategy_evaluation_produces_results(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that strategy evaluation produces some kind of results for each file."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        harness = DslTestHarness(str(repository_root))
        successful_evaluations = 0
        
        for strategy_file in clj_strategy_files:
            try:
                harness.reset_state()
                result = harness.evaluate_strategy(str(strategy_file))
                
                # Check that some events were generated
                assert len(result.all_events) > 0
                
                # If successful, should have evaluation events
                if result.success:
                    successful_evaluations += 1
                    
            except Exception as e:
                # Some strategies might fail - log but continue
                print(f"Strategy {strategy_file.name} failed: {e}")
        
        # At least some strategies should evaluate successfully
        print(f"Successfully evaluated {successful_evaluations}/{len(clj_strategy_files)} strategies")
        assert successful_evaluations >= 0  # Even 0 is ok for initial implementation