#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Scenario-based testing for DSL engine.

Tests different market scenarios including normal, stress, and edge cases
using the event-driven test harness.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.utils.dsl_test_utils import ScenarioGenerator
from tests.utils.test_harness import DslTestHarness


class TestMarketScenarios:
    """Test DSL engine under different market scenarios."""
    
    def test_normal_market_scenario(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test DSL engine under normal market conditions."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        # Use the first strategy file for scenario testing
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root), seed=42)
        scenario_gen = ScenarioGenerator(seed=42)
        
        # Generate normal market scenario
        scenario = scenario_gen.generate_normal_market_scenario()
        
        # Inject market conditions
        harness.inject_market_conditions(scenario)
        
        # Evaluate strategy under normal conditions
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Verify basic functionality
        assert len(result.all_events) > 0
        assert result.correlation_id is not None
        
        # Log scenario results for analysis
        print(f"Normal scenario results for {strategy_file.name}:")
        print(f"  Events generated: {len(result.all_events)}")
        print(f"  Success: {result.success}")
        print(f"  Has allocation: {result.allocation_result is not None}")
    
    def test_stress_market_scenario(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test DSL engine under stress market conditions."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root), seed=42)
        scenario_gen = ScenarioGenerator(seed=42)
        
        # Generate stress scenario
        scenario = scenario_gen.generate_stress_scenario()
        
        # Inject stress conditions
        harness.inject_market_conditions(scenario)
        
        # Evaluate strategy under stress
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Should still handle gracefully
        assert len(result.all_events) > 0
        
        print(f"Stress scenario results for {strategy_file.name}:")
        print(f"  Events generated: {len(result.all_events)}")
        print(f"  Success: {result.success}")
    
    def test_edge_case_scenario(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test DSL engine under edge case conditions."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root), seed=42)
        scenario_gen = ScenarioGenerator(seed=42)
        
        # Generate edge case scenario
        scenario = scenario_gen.generate_edge_case_scenario()
        
        # Inject edge case conditions
        harness.inject_market_conditions(scenario)
        
        # Evaluate strategy with edge cases
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Should handle gracefully even with problematic data
        assert len(result.all_events) > 0
        
        print(f"Edge case scenario results for {strategy_file.name}:")
        print(f"  Events generated: {len(result.all_events)}")
        print(f"  Success: {result.success}")
    
    def test_multi_symbol_scenario(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test DSL engine with multi-symbol scenarios."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root), seed=42)
        scenario_gen = ScenarioGenerator(seed=42)
        
        # Generate multi-symbol scenario
        scenario = scenario_gen.generate_multi_symbol_scenario()
        
        # Inject multi-symbol conditions
        harness.inject_market_conditions(scenario)
        
        # Evaluate strategy with multiple symbols
        result = harness.evaluate_strategy(str(strategy_file))
        
        assert len(result.all_events) > 0
        
        print(f"Multi-symbol scenario results for {strategy_file.name}:")
        print(f"  Events generated: {len(result.all_events)}")
        print(f"  Success: {result.success}")


@pytest.mark.property
class TestDslEngineInvariants:
    """Property-based tests for DSL engine invariants."""
    
    def test_idempotency_with_same_seed(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that strategy evaluation is idempotent with same seed."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        # Run same evaluation twice with identical setup
        harness1 = DslTestHarness(str(repository_root), seed=42)
        result1 = harness1.evaluate_strategy(str(strategy_file))
        
        harness2 = DslTestHarness(str(repository_root), seed=42)
        result2 = harness2.evaluate_strategy(str(strategy_file))
        
        # Results should be identical
        assert len(result1.all_events) == len(result2.all_events)
        
        # Event types should match
        types1 = [e.event_type for e in result1.all_events]
        types2 = [e.event_type for e in result2.all_events]
        assert types1 == types2
        
        print(f"Idempotency test for {strategy_file.name}: ✓")
    
    def test_correlation_id_propagation(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that correlation IDs are properly propagated."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        correlation_id = "test-property-correlation-123"
        
        harness = DslTestHarness(str(repository_root))
        result = harness.evaluate_strategy(
            str(strategy_file), 
            correlation_id=correlation_id
        )
        
        # All events must have the same correlation ID
        for event in result.all_events:
            assert event.correlation_id == correlation_id
        
        print(f"Correlation ID propagation test for {strategy_file.name}: ✓")
    
    def test_state_reset_isolation(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that state resets properly isolate evaluations."""
        if len(clj_strategy_files) < 2:
            pytest.skip("Need at least 2 strategy files for isolation testing")
        
        harness = DslTestHarness(str(repository_root), seed=42)
        
        # Evaluate first strategy
        result1 = harness.evaluate_strategy(str(clj_strategy_files[0]))
        events_before_reset = len(harness.event_recorder.events)
        
        # Reset state
        harness.reset_state()
        
        # Verify state was cleared
        assert len(harness.event_recorder.events) == 0
        
        # Evaluate second strategy
        result2 = harness.evaluate_strategy(str(clj_strategy_files[1]))
        
        # Results should be independent
        assert result1.correlation_id != result2.correlation_id
        
        print(f"State reset isolation test: ✓")
    
    def test_time_monotonicity(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test that virtual time advances monotonically."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root))
        initial_time = harness.virtual_time
        
        # Advance virtual time
        harness.advance_virtual_time(3600)  # 1 hour
        
        # Time should have advanced
        assert harness.virtual_time > initial_time
        
        # Evaluate strategy at new time
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Should work at any virtual time
        assert len(result.all_events) > 0
        
        print(f"Time monotonicity test: ✓")


@pytest.mark.event_driven
class TestEventDrivenWorkflow:
    """Test the complete event-driven workflow."""
    
    def test_end_to_end_event_flow(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test complete end-to-end event flow."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root))
        
        # Record initial state
        initial_event_count = len(harness.event_recorder.events)
        assert initial_event_count == 0
        
        # Trigger evaluation
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Verify event flow
        assert len(result.all_events) > initial_event_count
        
        # Should have at least a request event
        request_events = [e for e in result.all_events if e.event_type == "StrategyEvaluationRequested"]
        assert len(request_events) >= 1
        
        # Verify request event exists (may not be first due to processing order)
        assert any(event.event_type == "StrategyEvaluationRequested" for event in result.all_events)
        
        print(f"End-to-end event flow test for {strategy_file.name}:")
        print(f"  Total events: {len(result.all_events)}")
        
        # Print event sequence
        for i, event in enumerate(result.all_events):
            print(f"  {i+1}. {event.event_type}")
    
    def test_event_bus_metrics(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test event bus metrics and statistics."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        strategy_file = clj_strategy_files[0]
        
        harness = DslTestHarness(str(repository_root))
        
        # Check initial metrics
        initial_stats = harness.event_bus.get_stats()
        print(f"Initial event bus stats: {initial_stats}")
        
        # Evaluate strategy
        result = harness.evaluate_strategy(str(strategy_file))
        
        # Check final metrics
        final_stats = harness.event_bus.get_stats()
        print(f"Final event bus stats: {final_stats}")
        
        # Verify metrics increased
        assert final_stats["total_events_published"] > initial_stats["total_events_published"]
        
        # Should have handlers registered
        assert final_stats["total_handlers"] > 0
    
    def test_multiple_evaluations_same_harness(
        self, 
        repository_root: Path, 
        clj_strategy_files: list[Path]
    ) -> None:
        """Test multiple evaluations using the same harness."""
        if len(clj_strategy_files) < 2:
            pytest.skip("Need at least 2 strategy files for multiple evaluation testing")
        
        harness = DslTestHarness(str(repository_root))
        results = []
        
        # Evaluate multiple strategies
        for i, strategy_file in enumerate(clj_strategy_files[:3]):  # Test first 3
            harness.reset_state()
            result = harness.evaluate_strategy(str(strategy_file))
            results.append(result)
            
            print(f"Evaluation {i+1} ({strategy_file.name}): {len(result.all_events)} events")
        
        # Verify all evaluations worked
        assert len(results) == min(3, len(clj_strategy_files))
        
        # Each should have generated events
        for result in results:
            assert len(result.all_events) > 0
        
        # Correlation IDs should be different
        correlation_ids = [result.correlation_id for result in results]
        assert len(set(correlation_ids)) == len(correlation_ids)  # All unique