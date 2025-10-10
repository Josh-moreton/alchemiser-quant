#!/usr/bin/env python3
"""Tests for TradingModeProvider protocol.

Business Unit: shared | Status: current

Tests protocol conformance and usage patterns for the TradingModeProvider
protocol to ensure type safety and correct behavior.
"""

from __future__ import annotations

import pytest

from the_alchemiser.shared.protocols.orchestrator import TradingModeProvider


# Mock implementations for testing
class MockLiveOrchestrator:
    """Mock orchestrator for live trading mode.
    
    Implements TradingModeProvider protocol with live trading enabled.
    """

    live_trading: bool = True


class MockPaperOrchestrator:
    """Mock orchestrator for paper trading mode.
    
    Implements TradingModeProvider protocol with paper trading enabled.
    """

    live_trading: bool = False


class DynamicModeOrchestrator:
    """Mock orchestrator with dynamic trading mode.
    
    Allows changing trading mode at runtime for testing state changes.
    """

    def __init__(self, live: bool = False) -> None:
        """Initialize orchestrator with specified mode.
        
        Args:
            live: Whether to enable live trading (True) or paper trading (False)
        """
        self.live_trading = live


def test_protocol_conformance_live() -> None:
    """Test that live orchestrator conforms to TradingModeProvider protocol."""
    orchestrator: TradingModeProvider = MockLiveOrchestrator()
    assert orchestrator.live_trading is True


def test_protocol_conformance_paper() -> None:
    """Test that paper orchestrator conforms to TradingModeProvider protocol."""
    orchestrator: TradingModeProvider = MockPaperOrchestrator()
    assert orchestrator.live_trading is False


def test_protocol_attribute_type() -> None:
    """Test that protocol enforces bool type hint."""
    orchestrator = MockLiveOrchestrator()
    result: bool = orchestrator.live_trading
    assert isinstance(result, bool)


def test_dynamic_mode_orchestrator_live() -> None:
    """Test dynamic orchestrator in live mode."""
    orchestrator: TradingModeProvider = DynamicModeOrchestrator(live=True)
    assert orchestrator.live_trading is True


def test_dynamic_mode_orchestrator_paper() -> None:
    """Test dynamic orchestrator in paper mode."""
    orchestrator: TradingModeProvider = DynamicModeOrchestrator(live=False)
    assert orchestrator.live_trading is False


def test_multiple_implementations_coexist() -> None:
    """Test that multiple protocol implementations can coexist."""
    live_orch: TradingModeProvider = MockLiveOrchestrator()
    paper_orch: TradingModeProvider = MockPaperOrchestrator()
    dynamic_orch: TradingModeProvider = DynamicModeOrchestrator(live=True)
    
    assert live_orch.live_trading is True
    assert paper_orch.live_trading is False
    assert dynamic_orch.live_trading is True


def test_protocol_usage_in_conditional() -> None:
    """Test protocol usage in conditional logic (realistic usage pattern)."""
    def determine_mode_string(orchestrator: TradingModeProvider) -> str:
        """Determine mode string from orchestrator (mimics real usage)."""
        return "LIVE" if orchestrator.live_trading else "PAPER"
    
    assert determine_mode_string(MockLiveOrchestrator()) == "LIVE"
    assert determine_mode_string(MockPaperOrchestrator()) == "PAPER"
    assert determine_mode_string(DynamicModeOrchestrator(live=True)) == "LIVE"
    assert determine_mode_string(DynamicModeOrchestrator(live=False)) == "PAPER"


@pytest.mark.parametrize(
    "live_trading,expected_mode",
    [
        (True, "LIVE"),
        (False, "PAPER"),
    ],
)
def test_protocol_parameterized(live_trading: bool, expected_mode: str) -> None:
    """Test protocol with parameterized inputs."""
    orchestrator: TradingModeProvider = DynamicModeOrchestrator(live=live_trading)
    mode = "LIVE" if orchestrator.live_trading else "PAPER"
    assert mode == expected_mode


def test_protocol_attribute_is_readable() -> None:
    """Test that protocol attribute is readable (not write-only)."""
    orchestrator = MockLiveOrchestrator()
    # Should not raise AttributeError
    _ = orchestrator.live_trading
    assert True  # Passed if no exception raised


def test_protocol_minimal_interface() -> None:
    """Test that protocol defines minimal interface (only live_trading)."""
    # This test documents that the protocol intentionally has only one attribute
    orchestrator: TradingModeProvider = MockLiveOrchestrator()
    
    # Should have live_trading attribute
    assert hasattr(orchestrator, "live_trading")
    
    # Protocol should not require additional attributes
    # (this documents the minimal design)
    assert isinstance(orchestrator.live_trading, bool)
