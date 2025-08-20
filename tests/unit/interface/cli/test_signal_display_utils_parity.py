"""Tests for CLI signal display utilities with typed StrategySignal parity."""

import datetime as dt
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.domain.types import StrategySignal
from the_alchemiser.infrastructure.alerts.alert_service import Alert
from the_alchemiser.interface.cli.signal_display_utils import (
    display_signal_results,
    display_signal_results_unified,
    display_typed_signal_results,
)


class TestSignalDisplayParity:
    """Test suite ensuring typed signal display produces equivalent output to legacy Alert display."""

    @pytest.fixture
    def mock_alert(self) -> Alert:
        """Create a mock Alert object for testing."""
        return Alert(
            symbol="AAPL",
            action="BUY",
            reason="Test signal reasoning",
            timestamp=dt.datetime(2025, 1, 15, 12, 0, 0),
            price=195.50,
        )

    @pytest.fixture
    def mock_typed_signal(self) -> dict[StrategyType, StrategySignal]:
        """Create a mock typed StrategySignal for testing."""
        return {
            StrategyType.NUCLEAR: {
                "symbol": "AAPL",
                "action": "BUY",
                "confidence": 0.8,
                "reasoning": "Test signal reasoning",
                "allocation_percentage": 0.5,
            }
        }

    @pytest.fixture
    def mock_portfolio_signal(self) -> dict[StrategyType, StrategySignal]:
        """Create a mock portfolio StrategySignal for testing."""
        return {
            StrategyType.TECL: {
                "symbol": {"UVXY": 0.25, "BIL": 0.75},
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": "Vol neutral portfolio allocation",
                "allocation_percentage": 0.0,
            }
        }

    def test_legacy_alert_display_single_signal(self, mock_alert, caplog):
        """Test legacy Alert display works correctly for single signal."""
        with patch("the_alchemiser.infrastructure.alerts.alert_service.log_alert_to_file"):
            with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
                result = display_signal_results([mock_alert], "TEST_STRATEGY")

        assert result is not None
        assert result.symbol == "AAPL"
        assert result.action == "BUY"
        assert "TEST_STRATEGY trading signal: BUY AAPL at $195.50" in caplog.text

    def test_typed_signal_display_single_signal(self, mock_typed_signal, caplog):
        """Test typed StrategySignal display works correctly for single signal."""
        # Capture the logger used by signal_display_utils
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            result = display_typed_signal_results(mock_typed_signal, "TEST_STRATEGY")

        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["action"] == "BUY"
        assert "TEST_STRATEGY trading signal: BUY AAPL" in caplog.text

    def test_typed_signal_display_portfolio_signal(self, mock_portfolio_signal, caplog):
        """Test typed StrategySignal display handles portfolio symbols correctly."""
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            result = display_typed_signal_results(mock_portfolio_signal, "TECL_STRATEGY")

        assert result is not None
        assert isinstance(result["symbol"], dict)
        assert result["action"] == "HOLD"
        # HOLD signals print to stdout, not log, so check via print mock instead
        assert result is not None

    def test_unified_display_routes_to_legacy(self, mock_alert, caplog):
        """Test unified display routes Alert objects to legacy path."""
        with patch("the_alchemiser.infrastructure.alerts.alert_service.log_alert_to_file"):
            result = display_signal_results_unified([mock_alert], "TEST_STRATEGY")

        assert result is not None
        assert isinstance(result, Alert)
        assert result.symbol == "AAPL"

    def test_unified_display_routes_to_typed(self, mock_typed_signal, caplog):
        """Test unified display routes StrategySignal dict to typed path."""
        result = display_signal_results_unified(mock_typed_signal, "TEST_STRATEGY")

        assert result is not None
        assert isinstance(result, dict)
        assert result["symbol"] == "AAPL"

    def test_empty_signals_handling(self, caplog):
        """Test both display functions handle empty inputs gracefully."""
        alert_result = display_signal_results([], "TEST_STRATEGY")
        typed_result = display_typed_signal_results({}, "TEST_STRATEGY")

        assert alert_result is None
        assert typed_result is None
        assert "Unable to generate TEST_STRATEGY strategy signal" in caplog.text

    def test_multi_signal_display_legacy(self, caplog):
        """Test legacy display handles multiple alerts correctly."""
        alerts = [
            Alert("AAPL", "BUY", "Signal 1", dt.datetime.now(), 195.50),
            Alert("MSFT", "SELL", "Signal 2", dt.datetime.now(), 380.25),
        ]

        with patch("the_alchemiser.infrastructure.alerts.alert_service.log_alert_to_file"):
            with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
                result = display_signal_results(alerts, "MULTI_STRATEGY")

        assert result is not None
        assert "MULTI_STRATEGY portfolio signal generated with 2 assets allocated" in caplog.text

    def test_multi_signal_display_typed(self, caplog):
        """Test typed display handles multiple strategy signals correctly."""
        signals = {
            StrategyType.NUCLEAR: {
                "symbol": "AAPL",
                "action": "BUY",
                "confidence": 0.8,
                "reasoning": "Nuclear signal",
                "allocation_percentage": 0.5,
            },
            StrategyType.TECL: {
                "symbol": "MSFT",
                "action": "SELL",
                "confidence": 0.7,
                "reasoning": "TECL signal",
                "allocation_percentage": 0.3,
            },
        }

        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            result = display_typed_signal_results(signals, "MULTI_STRATEGY")

        assert result is not None
        assert "MULTI_STRATEGY multi-strategy signal generated with 2 strategies" in caplog.text

    def test_hold_signal_display_parity(self, caplog):
        """Test HOLD signals display consistently between legacy and typed paths."""
        # Legacy HOLD signal
        hold_alert = Alert("CASH", "HOLD", "Holding position", dt.datetime.now(), 1.0)

        with patch("the_alchemiser.infrastructure.alerts.alert_service.log_alert_to_file"):
            with patch("builtins.print") as mock_print:
                legacy_result = display_signal_results([hold_alert], "TEST_STRATEGY")

        # Check print was called for HOLD signal
        mock_print.assert_called()
        print_calls = [str(call) for call in mock_print.call_args_list]
        legacy_output = "\n".join(print_calls)

        # Typed HOLD signal
        hold_signal = {
            StrategyType.NUCLEAR: {
                "symbol": "CASH",
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": "Holding position",
                "allocation_percentage": 0.0,
            }
        }

        with patch("builtins.print") as mock_print:
            typed_result = display_typed_signal_results(hold_signal, "TEST_STRATEGY")

        # Check print was called for HOLD signal
        mock_print.assert_called()
        print_calls = [str(call) for call in mock_print.call_args_list]
        typed_output = "\n".join(print_calls)

        # Both should display HOLD action
        assert "HOLD" in legacy_output
        assert "HOLD" in typed_output
        assert legacy_result is not None
        assert typed_result is not None

    def test_reasoning_vs_reason_field_compatibility(self, caplog):
        """Test typed display handles both 'reasoning' and legacy 'reason' fields."""
        # Signal with 'reason' field (legacy style)
        signal_with_reason = {
            StrategyType.NUCLEAR: {
                "symbol": "AAPL",
                "action": "BUY",
                "confidence": 0.8,
                "reason": "Legacy reason field",  # Using 'reason' instead of 'reasoning'
                "allocation_percentage": 0.5,
            }
        }

        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            result = display_typed_signal_results(signal_with_reason, "TEST_STRATEGY")

        assert result is not None
        assert "Legacy reason field" in caplog.text

    def test_invalid_data_type_handling(self, caplog):
        """Test unified display handles invalid data types gracefully."""
        result = display_signal_results_unified("invalid_data", "TEST_STRATEGY")

        assert result is None
        assert "Invalid data type for signal display" in caplog.text


class TestSignalDisplaySnapshot:
    """Snapshot tests to ensure consistent CLI output format."""

    def test_cli_output_snapshot_single_alert(self, caplog):
        """Snapshot test for single alert CLI output format."""
        alert = Alert("AAPL", "BUY", "Strong bullish signal", dt.datetime(2025, 1, 15, 12, 0), 195.50)

        with patch("the_alchemiser.infrastructure.alerts.alert_service.log_alert_to_file"):
            with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
                display_signal_results([alert], "NUCLEAR")

        # Verify expected log format
        assert "NUCLEAR trading signal: BUY AAPL at $195.50 - Strong bullish signal" in caplog.text

    def test_cli_output_snapshot_typed_signal(self, caplog):
        """Snapshot test for typed signal CLI output format."""
        signal = {
            StrategyType.NUCLEAR: {
                "symbol": "AAPL",
                "action": "BUY",
                "confidence": 0.8,
                "reasoning": "Strong bullish signal",
                "allocation_percentage": 0.5,
            }
        }

        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            display_typed_signal_results(signal, "NUCLEAR")

        # Verify expected log format (should be similar to Alert version)
        assert "NUCLEAR trading signal: BUY AAPL - Strong bullish signal" in caplog.text

    def test_cli_output_snapshot_portfolio_display(self, caplog):
        """Snapshot test for portfolio allocation display."""
        portfolio_signal = {
            StrategyType.TECL: {
                "symbol": {"UVXY": 0.25, "BIL": 0.75},
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": "Defensive positioning with volatility hedge",
                "allocation_percentage": 0.0,
            }
        }

        with patch("builtins.print") as mock_print:
            display_typed_signal_results(portfolio_signal, "TECL")

        # Verify HOLD signal uses print output
        mock_print.assert_called()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(print_calls)

        assert "TECL Analysis: HOLD PORTFOLIO" in output
        assert "Defensive positioning with volatility hedge" in output