"""Tests for event-driven import enforcement.

Validates that import linter properly detects violations of event-driven architecture principles.
"""

import subprocess
import pytest
from pathlib import Path


def test_import_linter_detects_event_driven_violations():
    """Test that import linter detects violations of event-driven architecture."""
    
    # Run import linter and capture output
    result = subprocess.run(
        ["lint-imports", "--config", "pyproject.toml"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    # Should fail due to violations
    assert result.returncode != 0, "Import linter should detect violations"
    
    # Should detect specific violations (clean output of ANSI codes)
    output = result.stdout
    clean_output = output.replace('\x1b[1m', '').replace('\x1b[0m', '').replace('\x1b[22m', '').replace('\x1b[32m', '').replace('\x1b[31m', '').replace('\x1b[33m', '')
    
    assert "Event-driven orchestration enforcement - direct imports BROKEN" in clean_output
    assert "trading_orchestrator.py" in clean_output or "trading_orchestrator" in clean_output
    assert "signal_orchestrator.py" in clean_output or "signal_orchestrator" in clean_output
    assert "portfolio_orchestrator.py" in clean_output or "portfolio_orchestrator" in clean_output


def test_event_driven_violations_documented():
    """Test that specific event-driven violations are documented."""
    
    result = subprocess.run(
        ["lint-imports", "--config", "pyproject.toml"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    output = result.stdout
    
    # Check for specific violation patterns
    violations = [
        "execution_v2.models.execution_result",  # Direct model import
        "strategy_v2.engines.dsl.strategy_engine",  # Direct engine import
        "portfolio_v2",  # Direct service import
    ]
    
    for violation in violations:
        assert violation in output, f"Should detect violation: {violation}"


def test_event_driven_orchestrator_compliance():
    """Test that EventDrivenOrchestrator follows event-driven principles."""
    
    # EventDrivenOrchestrator should only import from shared modules and events
    from the_alchemiser.orchestration.event_driven_orchestrator import EventDrivenOrchestrator
    
    # This should not raise import errors and should be compliant
    assert EventDrivenOrchestrator is not None
    
    # Check that it uses event-based communication
    orchestrator_file = Path(__file__).parent.parent.parent / "the_alchemiser" / "orchestration" / "event_driven_orchestrator.py"
    content = orchestrator_file.read_text()
    
    # Should import events but not business logic
    assert "from the_alchemiser.shared.events import" in content
    assert "SignalGenerated" in content
    assert "RebalancePlanned" in content
    assert "TradeExecuted" in content
    
    # Should NOT directly import business modules
    business_imports = [
        "from the_alchemiser.strategy_v2.engines",
        "from the_alchemiser.portfolio_v2.core", 
        "from the_alchemiser.execution_v2.models"
    ]
    
    for bad_import in business_imports:
        assert bad_import not in content, f"EventDrivenOrchestrator should not have: {bad_import}"


@pytest.mark.skipif(
    subprocess.run(["which", "lint-imports"], capture_output=True).returncode != 0,
    reason="lint-imports not available"
)
def test_import_linter_configuration():
    """Test that import linter configuration is properly set up."""
    
    config_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    content = config_file.read_text()
    
    # Should have event-driven enforcement contracts
    assert "Event-driven orchestration enforcement - direct imports" in content
    assert "Event-driven orchestration enforcement - deep imports" in content
    
    # Should target the right modules
    assert "the_alchemiser.orchestration.trading_orchestrator" in content
    assert "the_alchemiser.orchestration.signal_orchestrator" in content
    assert "the_alchemiser.orchestration.portfolio_orchestrator" in content