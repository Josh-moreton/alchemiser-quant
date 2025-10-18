"""Business Unit: shared | Status: current.

Integration tests for multi-symbol signal flow end-to-end.

Validates that multi-symbol signals flow correctly from signal generation
through event publication to notification rendering without data loss.
"""

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.events.schemas import SignalGenerated
from the_alchemiser.shared.notifications.templates.signals import SignalsBuilder
from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio


class TestMultiSymbolSignalFlowIntegration:
    """Integration tests for complete multi-symbol signal flow."""

    def test_single_symbol_signal_flow_end_to_end(self):
        """Test single symbol signal flows correctly through all layers."""
        # Step 1: Signal handler output format (as created by SignalGenerationHandler)
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ"],
                "symbol": "TQQQ",
                "action": "BUY",
                "reasoning": "Strong momentum detected",
                "signal": "BUY TQQQ",
                "is_multi_symbol": False,
                "total_allocation": 0.75,
            }
        }

        # Step 2: Consolidated portfolio
        consolidated_portfolio_data = {
            "target_allocations": {"TQQQ": Decimal("0.75")},
            "correlation_id": "test-123",
            "source_strategies": ["grail"],
        }

        # Step 3: Event creation (as done by SignalGenerationHandler)
        event = SignalGenerated(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            event_id="test-event-789",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data=strategy_signals,
            consolidated_portfolio=consolidated_portfolio_data,
            signal_count=1,
        )

        # Step 4: Verify event preserves data
        assert event.signals_data["grail"]["symbols"] == ["TQQQ"]
        assert event.signals_data["grail"]["symbol"] == "TQQQ"
        assert event.signals_data["grail"]["signal"] == "BUY TQQQ"

        # Step 5: Notification rendering
        html = SignalsBuilder.build_signal_summary(
            strategy_signals, consolidated_portfolio_data["target_allocations"]
        )

        # Verify all symbols appear in output
        assert "TQQQ" in html
        assert "BUY TQQQ" in html
        assert "75.0%" in html

    def test_multi_symbol_signal_flow_end_to_end(self):
        """Test multi-symbol signal flows correctly through all layers without data loss."""
        # Step 1: Signal handler output format with MULTIPLE symbols
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],  # Multiple symbols!
                "symbol": "TQQQ",  # First symbol for backward compatibility
                "action": "BUY",
                "reasoning": "Diversified momentum strategy across tech sectors",
                "signal": "BUY TQQQ, SOXL",  # Pre-formatted with all symbols
                "is_multi_symbol": True,
                "total_allocation": 0.75,
            }
        }

        # Step 2: Consolidated portfolio with both symbols
        consolidated_portfolio_data = {
            "target_allocations": {"TQQQ": Decimal("0.5"), "SOXL": Decimal("0.25")},
            "correlation_id": "test-123",
            "source_strategies": ["grail"],
        }

        # Step 3: Event creation
        event = SignalGenerated(
            correlation_id="test-corr-multi",
            causation_id="test-cause-multi",
            event_id="test-event-multi",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data=strategy_signals,
            consolidated_portfolio=consolidated_portfolio_data,
            signal_count=1,
        )

        # Step 4: Verify event preserves ALL symbols (no truncation)
        assert event.signals_data["grail"]["symbols"] == ["TQQQ", "SOXL"]
        assert event.signals_data["grail"]["symbol"] == "TQQQ"
        assert event.signals_data["grail"]["signal"] == "BUY TQQQ, SOXL"
        assert event.signals_data["grail"]["is_multi_symbol"] is True

        # Step 5: Notification rendering - verify NO DATA LOSS
        html = SignalsBuilder.build_signal_summary(
            strategy_signals, consolidated_portfolio_data["target_allocations"]
        )

        # Critical assertion: BOTH symbols must appear in output
        assert "TQQQ" in html, "First symbol missing from notification"
        assert "SOXL" in html, "Second symbol missing from notification - DATA LOSS!"

        # Signal should show both symbols together
        assert (
            "BUY TQQQ, SOXL" in html
        ), "Multi-symbol signal not displaying all symbols together"

        # Consolidated portfolio should show both allocations
        assert "50.0%" in html, "TQQQ allocation missing"
        assert "25.0%" in html, "SOXL allocation missing"

    def test_multi_strategy_multi_symbol_flow(self):
        """Test multiple strategies each with multiple symbols."""
        # Two strategies, each with multiple symbols
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL"],
                "symbol": "TQQQ",
                "action": "BUY",
                "reasoning": "Tech momentum",
                "signal": "BUY TQQQ, SOXL",
                "is_multi_symbol": True,
                "total_allocation": 0.5,
            },
            "nuclear": {
                "symbols": ["UPRO", "TMF"],
                "symbol": "UPRO",
                "action": "BUY",
                "reasoning": "Risk-on allocation",
                "signal": "BUY UPRO, TMF",
                "is_multi_symbol": True,
                "total_allocation": 0.5,
            },
        }

        consolidated_portfolio_data = {
            "target_allocations": {
                "TQQQ": Decimal("0.25"),
                "SOXL": Decimal("0.25"),
                "UPRO": Decimal("0.25"),
                "TMF": Decimal("0.25"),
            },
            "correlation_id": "test-multi-123",
            "source_strategies": ["grail", "nuclear"],
        }

        # Create event
        event = SignalGenerated(
            correlation_id="test-corr-multi-strat",
            causation_id="test-cause-multi-strat",
            event_id="test-event-multi-strat",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data=strategy_signals,
            consolidated_portfolio=consolidated_portfolio_data,
            signal_count=2,
        )

        # Verify event preserves all data
        assert len(event.signals_data["grail"]["symbols"]) == 2
        assert len(event.signals_data["nuclear"]["symbols"]) == 2

        # Render all three template methods
        html_summary = SignalsBuilder.build_signal_summary(
            strategy_signals, consolidated_portfolio_data["target_allocations"]
        )
        html_detailed = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, {})
        html_neutral = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)

        # All 4 symbols must appear in ALL renderings
        for symbol in ["TQQQ", "SOXL", "UPRO", "TMF"]:
            assert symbol in html_summary, f"{symbol} missing from summary - DATA LOSS"
            assert symbol in html_detailed, f"{symbol} missing from detailed - DATA LOSS"
            assert symbol in html_neutral, f"{symbol} missing from neutral - DATA LOSS"

        # Multi-symbol signals should be visible
        assert "TQQQ, SOXL" in html_summary or ("TQQQ" in html_summary and "SOXL" in html_summary)
        assert "UPRO, TMF" in html_summary or ("UPRO" in html_summary and "TMF" in html_summary)

    def test_event_serialization_preserves_symbols_list(self):
        """Test that event serialization/deserialization preserves symbols list."""
        strategy_signals = {
            "grail": {
                "symbols": ["TQQQ", "SOXL", "TECL"],  # 3 symbols
                "symbol": "TQQQ",
                "action": "BUY",
                "reasoning": "Triple momentum",
                "signal": "BUY TQQQ, SOXL, TECL",
                "is_multi_symbol": True,
            }
        }

        consolidated_portfolio_data = {
            "target_allocations": {
                "TQQQ": Decimal("0.33"),
                "SOXL": Decimal("0.33"),
                "TECL": Decimal("0.34"),
            },
            "correlation_id": "test-serialize",
            "source_strategies": ["grail"],
        }

        event = SignalGenerated(
            correlation_id="test-serialize",
            causation_id="test-serialize",
            event_id="test-serialize",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data=strategy_signals,
            consolidated_portfolio=consolidated_portfolio_data,
            signal_count=1,
        )

        # Serialize to dict (as EventBridge would do)
        event_dict = event.model_dump()

        # Verify symbols list is in serialized data
        assert "symbols" in event_dict["signals_data"]["grail"]
        assert event_dict["signals_data"]["grail"]["symbols"] == ["TQQQ", "SOXL", "TECL"]

        # Deserialize back
        event_restored = SignalGenerated.model_validate(event_dict)

        # Verify all symbols preserved after round-trip
        assert event_restored.signals_data["grail"]["symbols"] == ["TQQQ", "SOXL", "TECL"]
        assert len(event_restored.signals_data["grail"]["symbols"]) == 3

    def test_backward_compatibility_no_symbols_list(self):
        """Test that old signal format (no symbols list) still works."""
        # Old format - only has 'symbol' field, no 'symbols' list
        strategy_signals = {
            "grail": {
                "symbol": "TQQQ",
                # No symbols list - testing backward compatibility
                "action": "BUY",
                "reasoning": "Test backward compat",
            }
        }

        consolidated_portfolio_data = {
            "target_allocations": {"TQQQ": Decimal("0.75")},
            "correlation_id": "test-backward",
            "source_strategies": ["grail"],
        }

        # Should still work with all templates
        html_summary = SignalsBuilder.build_signal_summary(
            strategy_signals, consolidated_portfolio_data["target_allocations"]
        )
        html_detailed = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, {})
        html_neutral = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)

        # Symbol should appear in all outputs
        assert "TQQQ" in html_summary
        assert "TQQQ" in html_detailed
        assert "TQQQ" in html_neutral
