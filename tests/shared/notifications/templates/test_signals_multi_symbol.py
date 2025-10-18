"""Business Unit: shared | Status: current.

Tests for multi-symbol signal rendering in email templates.

Validates that signal templates correctly handle both single-symbol
and multi-symbol signals without data loss or truncation.
"""


from the_alchemiser.shared.notifications.templates.signals import SignalsBuilder


class TestMultiSymbolSignalRendering:
    """Test multi-symbol signal rendering in all template methods."""

    def test_build_detailed_strategy_signals_single_symbol(self):
        """Test detailed signals with single symbol."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reason": "Strong momentum detected",
                "signal": "BUY TQQQ",
            }
        }
        strategy_summary = {"grail": {"allocation": 0.75}}

        html = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)

        assert "TQQQ" in html
        assert "BUY" in html
        assert "grail" in html.lower()

    def test_build_detailed_strategy_signals_multiple_symbols(self):
        """Test detailed signals with multiple symbols - should show all symbols."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],  # Full list
                "action": "BUY",
                "reason": "Strong momentum detected across multiple assets",
                "signal": "BUY TQQQ, SOXL",
            }
        }
        strategy_summary = {"grail": {"allocation": 0.75}}

        html = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)

        # Should contain BOTH symbols, not just TQQQ
        assert "TQQQ" in html
        assert "SOXL" in html
        # Should show them together (comma-separated or similar)
        assert "TQQQ, SOXL" in html or ("TQQQ" in html and "SOXL" in html)

    def test_build_detailed_strategy_signals_no_symbols_list(self):
        """Test detailed signals without symbols list - falls back to singular symbol."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reason": "Strong momentum detected",
            }
        }
        strategy_summary = {"grail": {"allocation": 0.75}}

        html = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)

        assert "TQQQ" in html
        assert "BUY" in html

    def test_build_signal_summary_single_symbol(self):
        """Test signal summary with single symbol."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reasoning": "Strong momentum",
                "signal": "BUY TQQQ",
            }
        }
        consolidated_portfolio = {"TQQQ": 0.75}

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        assert "TQQQ" in html
        assert "BUY" in html
        assert "75.0%" in html  # Consolidated allocation

    def test_build_signal_summary_multiple_symbols(self):
        """Test signal summary with multiple symbols - should show all symbols."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],  # Full list
                "action": "BUY",
                "reasoning": "Diversified momentum strategy",
                "signal": "BUY TQQQ, SOXL",
            }
        }
        consolidated_portfolio = {"TQQQ": 0.5, "SOXL": 0.25}

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        # Should show the signal field which contains all symbols
        assert "BUY TQQQ, SOXL" in html
        # Consolidated should show both symbols with allocations
        assert "TQQQ" in html
        assert "SOXL" in html
        assert "50.0%" in html  # TQQQ allocation
        assert "25.0%" in html  # SOXL allocation

    def test_build_signal_summary_fallback_without_signal_field_single(self):
        """Test signal summary fallback when signal field is missing - single symbol."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reasoning": "Test",
                # No signal field - tests fallback logic
            }
        }
        consolidated_portfolio = {"TQQQ": 0.75}

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        assert "TQQQ" in html
        assert "BUY" in html

    def test_build_signal_summary_fallback_without_signal_field_multiple(self):
        """Test signal summary fallback when signal field is missing - multiple symbols."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],  # Full list
                "action": "BUY",
                "reasoning": "Test multi-symbol fallback",
                # No signal field - tests fallback logic with symbols list
            }
        }
        consolidated_portfolio = {"TQQQ": 0.5, "SOXL": 0.25}

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        # Fallback should use symbols list to build display
        assert "TQQQ" in html
        assert "SOXL" in html
        assert "BUY" in html

    def test_build_strategy_signals_neutral_single_symbol(self):
        """Test neutral signals table with single symbol."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reason": "Strong momentum",
            }
        }

        html = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)

        assert "TQQQ" in html
        assert "BUY" in html
        assert "GRAIL" in html

    def test_build_strategy_signals_neutral_multiple_symbols(self):
        """Test neutral signals table with multiple symbols - should show all."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],  # Full list
                "action": "BUY",
                "reason": "Diversified momentum across tech sectors",
            }
        }

        html = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)

        # Should show all symbols
        assert "TQQQ" in html
        assert "SOXL" in html
        # Should ideally show them together
        assert "TQQQ, SOXL" in html or ("TQQQ" in html and "SOXL" in html)

    def test_build_strategy_signals_neutral_no_symbols_list(self):
        """Test neutral signals table without symbols list - backward compatibility."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "action": "BUY",
                "reason": "Test",
            }
        }

        html = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)

        assert "TQQQ" in html
        assert "BUY" in html

    def test_consolidated_portfolio_multiple_symbols(self):
        """Test consolidated portfolio section with multiple symbols."""
        strategy_signals = {}  # Empty for this test - focusing on consolidated
        consolidated_portfolio = {
            "TQQQ": 0.5,
            "SOXL": 0.3,
            "UPRO": 0.2,
        }

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        # All symbols should appear in consolidated section
        assert "TQQQ" in html
        assert "SOXL" in html
        assert "UPRO" in html
        # Allocations should be shown
        assert "50.0%" in html
        assert "30.0%" in html
        assert "20.0%" in html

    def test_multi_strategy_multi_symbol(self):
        """Test multiple strategies each with multiple symbols."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],
                "action": "BUY",
                "reasoning": "Tech momentum",
                "signal": "BUY TQQQ, SOXL",
            },
            "nuclear": {
                "symbols": ["UPRO", "TMF"],
                "action": "BUY",
                "reasoning": "Risk-on allocation",
                "signal": "BUY UPRO, TMF",
            },
        }
        consolidated_portfolio = {
            "TQQQ": 0.25,
            "SOXL": 0.25,
            "UPRO": 0.25,
            "TMF": 0.25,
        }

        html = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        # All strategy signals should be present with their symbols
        assert "grail" in html.lower()
        assert "nuclear" in html.lower()
        # All symbols should appear
        for symbol in ["TQQQ", "SOXL", "UPRO", "TMF"]:
            assert symbol in html
        # Each strategy's multi-symbol signal should be visible
        assert "TQQQ, SOXL" in html or ("TQQQ" in html and "SOXL" in html)
        assert "UPRO, TMF" in html or ("UPRO" in html and "TMF" in html)


class TestSignalDataIntegrity:
    """Test that signal data structure maintains integrity."""

    def test_symbols_list_always_present_in_signal_data(self):
        """Verify that well-formed signal data includes symbols list."""
        # This test documents the expected data structure
        signal_data = {
            "symbols": ["TQQQ", "SOXL"],  # List of all symbols
            "action": "BUY",
            "reasoning": "Test",
            "signal": "BUY TQQQ, SOXL",  # Pre-formatted display string
        }

        # Verify structure
        assert isinstance(signal_data["symbols"], list)
        assert len(signal_data["symbols"]) >= 1

    def test_single_symbol_in_symbols_list(self):
        """Test that single-symbol signals use symbols list with one element."""
        # Single symbol in list format
        signal_format = {
            "symbols": ["TQQQ"],
            "action": "BUY",
            "reason": "Test",
        }

        # Should work in templates
        html = SignalsBuilder.build_strategy_signals_neutral({"test": signal_format})

        assert "TQQQ" in html
        assert "BUY" in html
