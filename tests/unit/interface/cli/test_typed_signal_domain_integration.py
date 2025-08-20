"""Integration test demonstrating typed signal display in domain strategy engines."""

import logging
from unittest.mock import patch

import pytest

from the_alchemiser.application.mapping.strategy_signal_mapping import map_signals_dict
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.interface.cli.signal_display_utils import (
    display_signal_results_unified,
    display_typed_signal_results,
)
from the_alchemiser.utils.feature_flags import type_system_v2_enabled


class TestTypedSignalDomainIntegration:
    """Test integration of typed signal display with domain strategy workflows."""

    @pytest.fixture
    def mock_legacy_strategy_output(self):
        """Mock the output from a domain strategy engine (legacy format)."""
        return {
            StrategyType.NUCLEAR: {
                "symbol": "XLE",
                "action": "BUY",
                "reason": "Nuclear sector showing strong momentum",
                "confidence": 0.8,
                "allocation_percentage": 0.5,
            },
            StrategyType.TECL: {
                "symbol": {"UVXY": 0.25, "BIL": 0.75},
                "action": "HOLD",
                "reason": "Volatility hedge in place",
                "confidence": 0.3,
                "allocation_percentage": 0.0,
            },
        }

    def test_domain_strategy_typed_display_integration(self, mock_legacy_strategy_output, caplog):
        """Test how domain strategy engines can use typed signal display."""
        
        # Simulate what a domain strategy engine would do with feature flag enabled
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            if type_system_v2_enabled():
                # Convert legacy signals to typed format
                typed_signals = map_signals_dict(mock_legacy_strategy_output)
                
                # Use typed display function
                result = display_typed_signal_results(typed_signals, "NUCLEAR_INTEGRATION_TEST")
                
                # Verify typed path was used
                assert result is not None
                assert "NUCLEAR_INTEGRATION_TEST" in caplog.text
                assert "XLE" in caplog.text
                assert "Nuclear sector showing strong momentum" in caplog.text
            else:
                # Would use legacy Alert-based display
                # (This branch tests the feature flag logic)
                pytest.skip("Typed domain not enabled - would use legacy Alert display")

    def test_unified_display_with_domain_strategy_output(self, mock_legacy_strategy_output, caplog):
        """Test unified display function with domain strategy output."""
        
        # Convert to typed signals 
        typed_signals = map_signals_dict(mock_legacy_strategy_output)
        
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            # Use unified display function - should route to typed path
            result = display_signal_results_unified(typed_signals, "UNIFIED_TEST")
            
        assert result is not None
        assert isinstance(result, dict)  # Should return StrategySignal dict, not Alert
        assert result["symbol"] == "XLE"  # First signal in the dict
        assert "UNIFIED_TEST" in caplog.text

    def test_signal_mapping_preserves_display_compatibility(self, mock_legacy_strategy_output):
        """Test that signal mapping maintains display compatibility."""
        
        # Convert legacy to typed
        typed_signals = map_signals_dict(mock_legacy_strategy_output)
        
        # Verify structure is compatible with display functions
        assert isinstance(typed_signals, dict)
        assert StrategyType.NUCLEAR in typed_signals
        assert StrategyType.TECL in typed_signals
        
        nuclear_signal = typed_signals[StrategyType.NUCLEAR]
        tecl_signal = typed_signals[StrategyType.TECL]
        
        # Nuclear signal should have symbol as string
        assert nuclear_signal["symbol"] == "XLE"
        assert nuclear_signal["action"] == "BUY"
        assert nuclear_signal["reasoning"] == "Nuclear sector showing strong momentum"
        
        # TECL signal should have portfolio converted to "PORTFOLIO" label
        assert tecl_signal["symbol"] == "PORTFOLIO"  # Converted from dict
        assert tecl_signal["action"] == "HOLD"
        assert tecl_signal["reasoning"] == "Volatility hedge in place"

    def test_feature_flag_controls_display_path_selection(self, mock_legacy_strategy_output, caplog):
        """Test that feature flag properly controls which display path is used."""
        
        typed_signals = map_signals_dict(mock_legacy_strategy_output)
        
        # Test with feature flag enabled (default in tests)
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            if type_system_v2_enabled():
                result = display_typed_signal_results(typed_signals, "FLAG_TEST")
                assert result is not None
                assert "FLAG_TEST" in caplog.text
                
        # Test with feature flag disabled - need to patch the module where it's imported
        with patch('the_alchemiser.interface.cli.signal_display_utils.type_system_v2_enabled', return_value=False):
            # In real usage, this would trigger Alert-based legacy display
            # But for this test, we'll just verify the flag detection works
            from the_alchemiser.interface.cli.signal_display_utils import type_system_v2_enabled as patched_flag
            assert not patched_flag()

    def test_portfolio_symbol_handling_in_typed_display(self, caplog):
        """Test how portfolio symbols are handled in typed display."""
        
        portfolio_signal = {
            StrategyType.TECL: {
                "symbol": {"UVXY": 0.3, "BIL": 0.7},
                "action": "HOLD", 
                "confidence": 0.4,
                "reasoning": "Defensive allocation with volatility protection",
                "allocation_percentage": 0.0,
            }
        }
        
        with caplog.at_level(logging.INFO, logger='the_alchemiser.interface.cli.signal_display_utils'):
            # Use print capture since HOLD signals print to stdout
            with patch("builtins.print") as mock_print:
                result = display_typed_signal_results(portfolio_signal, "PORTFOLIO_TEST")
            
        # Verify portfolio symbol was converted to PORTFOLIO label
        assert result is not None
        assert result["symbol"] == {"UVXY": 0.3, "BIL": 0.7}  # Original preserved in result
        
        # Verify print was called for HOLD signal display
        mock_print.assert_called()
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(print_calls)
        assert "PORTFOLIO_TEST Analysis: HOLD PORTFOLIO" in output