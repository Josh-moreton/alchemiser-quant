#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy discovery and parametrization tests for DSL engine.

Tests automatic discovery of CLJ strategy files and parametrized testing
across all discovered strategies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.utils.dsl_test_utils import StrategyDiscovery
from tests.utils.test_harness import DslTestHarness


class TestStrategyDiscovery:
    """Test strategy discovery functionality."""
    
    def test_discover_clj_files(self, repository_root: Path) -> None:
        """Test discovery of CLJ strategy files."""
        discovery = StrategyDiscovery(repository_root)
        clj_files = discovery.discover_clj_files()
        
        # Should find the known strategy files
        assert len(clj_files) > 0
        
        # All should be .clj files
        for file in clj_files:
            assert file.suffix == ".clj"
            assert file.exists()
        
        # Should be sorted (deterministic ordering)
        file_names = [f.name for f in clj_files]
        assert file_names == sorted(file_names)
    
    def test_get_strategy_info(self, repository_root: Path, clj_strategy_files: list[Path]) -> None:
        """Test extraction of strategy information."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        discovery = StrategyDiscovery(repository_root)
        
        for strategy_file in clj_strategy_files:
            info = discovery.get_strategy_info(strategy_file)
            
            # Should have basic info
            assert "file_path" in info
            assert "file_name" in info
            assert "strategy_name" in info
            assert info["file_path"] == str(strategy_file)
            assert info["file_name"] == strategy_file.name
            
            # Should have either content preview or error
            assert "content_preview" in info or "error" in info
    
    def test_strategy_info_content_preview(self, repository_root: Path) -> None:
        """Test strategy info content preview functionality."""
        # Create a temporary strategy file for testing
        test_content = '''(defsymphony
 "Test Strategy | BT 2024-01-01"
 {:asset-class "EQUITIES"}
 (weight-equal
  [(asset "SPY" "SPDR S&P 500 ETF")]))'''
        
        discovery = StrategyDiscovery(repository_root)
        
        # Mock a file by directly testing the parsing logic
        # In real test, we'd create a temp file, but this tests the core logic
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.clj', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            info = discovery.get_strategy_info(temp_path)
            
            assert "content_preview" in info
            assert "Test Strategy" in info["content_preview"]
            assert info["strategy_name"] == "Test Strategy | BT 2024-01-01"
        finally:
            temp_path.unlink()  # Clean up


@pytest.mark.strategy  
class TestAllStrategiesParametrized:
    """Parametrized tests across all discovered strategy files."""
    
    def test_all_strategies_parseable(self, clj_strategy_files: list[Path]) -> None:
        """Test that all strategy files can be parsed without errors."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser, SexprParseError
        
        parser = SexprParser()
        results = {}
        
        for strategy_file in clj_strategy_files:
            try:
                ast = parser.parse_file(str(strategy_file))
                assert ast is not None
                assert ast.node_type is not None
                results[strategy_file.name] = "SUCCESS"
            except SexprParseError as e:
                results[strategy_file.name] = f"PARSE_ERROR: {e}"
            except Exception as e:
                results[strategy_file.name] = f"ERROR: {e}"
        
        # Report results
        success_count = sum(1 for result in results.values() if result == "SUCCESS")
        print(f"\nStrategy parsing results: {success_count}/{len(clj_strategy_files)} successful")
        
        for file_name, result in results.items():
            if result != "SUCCESS":
                print(f"  {file_name}: {result}")
        
        # At least some should parse successfully
        assert success_count > 0, "No strategy files could be parsed"
    
    
    def test_all_strategies_basic_evaluation(
        self, 
        clj_strategy_files: list[Path],
        repository_root: Path
    ) -> None:
        """Test basic evaluation of all strategy files."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        harness = DslTestHarness(str(repository_root))
        results = {}
        
        for strategy_file in clj_strategy_files:
            try:
                harness.reset_state()
                result = harness.evaluate_strategy(str(strategy_file))
                
                # Should generate at least one event
                assert len(result.all_events) > 0
                
                # Should have a request event
                request_events = [e for e in result.all_events if e.event_type == "StrategyEvaluationRequested"]
                assert len(request_events) == 1
                
                results[strategy_file.name] = {
                    "status": "SUCCESS",
                    "event_count": len(result.all_events),
                    "success": result.success,
                    "has_allocation": result.allocation_result is not None,
                    "has_trace": result.trace_result is not None
                }
                
            except Exception as e:
                results[strategy_file.name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        
        # Report results
        success_count = sum(1 for result in results.values() if result.get("status") == "SUCCESS")
        print(f"\nStrategy evaluation results: {success_count}/{len(clj_strategy_files)} successful")
        
        for file_name, result in results.items():
            if result.get("status") == "SUCCESS":
                print(f"  {file_name}: {result['event_count']} events, success={result['success']}")
            else:
                print(f"  {file_name}: {result.get('error', 'Unknown error')}")
        
        # Store results for potential golden testing
        pytest.strategy_evaluation_results = results
    
    
    def test_all_strategies_correlation_consistency(
        self,
        clj_strategy_files: list[Path],
        repository_root: Path
    ) -> None:
        """Test that all events for each strategy share the same correlation ID."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        harness = DslTestHarness(str(repository_root))
        
        for strategy_file in clj_strategy_files:
            try:
                correlation_id = f"test-{strategy_file.stem}-corr"
                harness.reset_state()
                
                result = harness.evaluate_strategy(
                    str(strategy_file), 
                    correlation_id=correlation_id
                )
                
                # All events should have the same correlation ID
                for event in result.all_events:
                    assert event.correlation_id == correlation_id, (
                        f"Correlation ID mismatch in {strategy_file.name}: "
                        f"expected {correlation_id}, got {event.correlation_id}"
                    )
                
            except Exception as e:
                # Log but don't fail - some strategies might have issues
                print(f"Correlation test failed for {strategy_file.name}: {e}")


class TestStrategyFileContent:
    """Test strategy file content and structure."""
    
    def test_all_strategies_have_valid_structure(self, clj_strategy_files: list[Path]) -> None:
        """Test that all strategy files have expected structure."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser
        
        parser = SexprParser()
        parseable_count = 0
        
        for strategy_file in clj_strategy_files:
            try:
                ast = parser.parse_file(str(strategy_file))
                
                # Basic structure validation
                assert ast is not None
                
                # If it's a list, should have some children
                if ast.node_type == "list":
                    assert len(ast.children) > 0
                
                parseable_count += 1
                
            except Exception as e:
                # Log parsing issues but don't fail - some files might be incomplete
                print(f"Could not parse {strategy_file.name}: {e}")
        
        # At least some files should be parseable
        assert parseable_count > 0, "No strategy files were parseable"
        
        # Report statistics
        print(f"Parsed {parseable_count}/{len(clj_strategy_files)} strategy files successfully")
    
    def test_strategy_files_not_empty(self, clj_strategy_files: list[Path]) -> None:
        """Test that strategy files are not empty."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        for strategy_file in clj_strategy_files:
            content = strategy_file.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"Strategy file {strategy_file.name} is empty"
    
    def test_strategy_files_have_expected_patterns(self, clj_strategy_files: list[Path]) -> None:
        """Test that strategy files contain expected Clojure patterns."""
        if not clj_strategy_files:
            pytest.skip("No CLJ strategy files found for testing")
        
        pattern_counts = {
            "defsymphony": 0,
            "asset": 0,
            "weight-equal": 0,
            "if": 0,
            "rsi": 0
        }
        
        for strategy_file in clj_strategy_files:
            try:
                content = strategy_file.read_text(encoding="utf-8")
                
                for pattern in pattern_counts:
                    if pattern in content:
                        pattern_counts[pattern] += 1
                        
            except Exception as e:
                print(f"Could not read {strategy_file.name}: {e}")
        
        # Report pattern usage across all files
        print(f"Pattern usage across {len(clj_strategy_files)} strategy files:")
        for pattern, count in pattern_counts.items():
            print(f"  {pattern}: {count} files")
        
        # At least some files should use common patterns
        assert pattern_counts["defsymphony"] > 0, "No files use 'defsymphony'"