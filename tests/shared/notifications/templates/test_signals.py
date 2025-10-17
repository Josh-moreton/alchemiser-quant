"""Business Unit: shared | Status: current.

Tests for signals template builder.

Validates HTML generation for trading signals, technical indicators,
and market regime analysis in email notifications.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.errors.exceptions import TemplateGenerationError
from the_alchemiser.shared.notifications.templates.signals import (
    RSI_OVERBOUGHT_CRITICAL,
    RSI_OVERBOUGHT_WARNING,
    RSI_OVERSOLD,
    SignalsBuilder,
)


class TestRSIColor:
    """Tests for RSI color determination."""

    def test_rsi_color_overbought_critical(self) -> None:
        """Test RSI color for critical overbought (>80)."""
        assert SignalsBuilder._get_rsi_color(85.0) == "#EF4444"
        assert SignalsBuilder._get_rsi_color(80.1) == "#EF4444"
        assert SignalsBuilder._get_rsi_color(100.0) == "#EF4444"

    def test_rsi_color_overbought_warning(self) -> None:
        """Test RSI color for warning overbought (70-80)."""
        assert SignalsBuilder._get_rsi_color(75.0) == "#F59E0B"
        assert SignalsBuilder._get_rsi_color(70.1) == "#F59E0B"
        assert SignalsBuilder._get_rsi_color(79.9) == "#F59E0B"

    def test_rsi_color_normal(self) -> None:
        """Test RSI color for normal range (<70)."""
        assert SignalsBuilder._get_rsi_color(50.0) == "#10B981"
        assert SignalsBuilder._get_rsi_color(0.0) == "#10B981"
        assert SignalsBuilder._get_rsi_color(69.9) == "#10B981"

    def test_rsi_color_boundary_80(self) -> None:
        """Test RSI color at 80 boundary (should be warning, not critical)."""
        # At exactly 80, should not be > 80, so should be warning
        assert SignalsBuilder._get_rsi_color(80.0) == "#F59E0B"

    def test_rsi_color_boundary_70(self) -> None:
        """Test RSI color at 70 boundary (should be normal, not warning)."""
        # At exactly 70, should not be > 70, so should be normal
        assert SignalsBuilder._get_rsi_color(70.0) == "#10B981"

    @given(rsi=st.floats(min_value=0.0, max_value=100.0, allow_nan=False))
    def test_rsi_color_always_returns_valid_color(self, rsi: float) -> None:
        """Property: RSI color should always return a valid hex color."""
        color = SignalsBuilder._get_rsi_color(rsi)
        assert color.startswith("#")
        assert len(color) == 7
        assert color in ["#EF4444", "#F59E0B", "#10B981"]


class TestPriceVsMAInfo:
    """Tests for price vs moving average comparison."""

    def test_price_above_ma(self) -> None:
        """Test price above moving average returns bullish signal."""
        label, color = SignalsBuilder._get_price_vs_ma_info(150.0, 100.0)
        assert label == "Above"
        assert color == "#10B981"  # Green

    def test_price_below_ma(self) -> None:
        """Test price below moving average returns bearish signal."""
        label, color = SignalsBuilder._get_price_vs_ma_info(100.0, 150.0)
        assert label == "Below"
        assert color == "#EF4444"  # Red

    def test_price_equal_ma(self) -> None:
        """Test price equal to moving average (not strictly above)."""
        label, color = SignalsBuilder._get_price_vs_ma_info(100.0, 100.0)
        assert label == "Below"  # Equal is not > ma
        assert color == "#EF4444"


class TestTruncateReason:
    """Tests for reason string truncation."""

    def test_truncate_short_string(self) -> None:
        """Test that short strings are not truncated."""
        result = SignalsBuilder._truncate_reason("Short reason", 100)
        assert result == "Short reason"
        assert "..." not in result

    def test_truncate_long_string(self) -> None:
        """Test that long strings are truncated with ellipsis."""
        long_reason = "A" * 150
        result = SignalsBuilder._truncate_reason(long_reason, 100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
        assert result[:100] == "A" * 100

    def test_truncate_exact_length(self) -> None:
        """Test string at exact max length is not truncated."""
        reason = "A" * 100
        result = SignalsBuilder._truncate_reason(reason, 100)
        assert result == reason
        assert "..." not in result

    @given(
        text=st.text(min_size=0, max_size=1000),
        max_len=st.integers(min_value=10, max_value=500),
    )
    def test_truncate_never_exceeds_max(self, text: str, max_len: int) -> None:
        """Property: Truncated text never exceeds max_length + 3 (for ...)."""
        result = SignalsBuilder._truncate_reason(text, max_len)
        assert len(result) <= max_len + 3


class TestBuildSignalInformation:
    """Tests for signal information HTML generation."""

    def test_signal_information_empty(self) -> None:
        """Test signal information with None signal."""
        result = SignalsBuilder.build_signal_information(None)
        assert result == ""

    def test_signal_information_with_reason(self) -> None:
        """Test signal information with complete signal data."""
        # Create mock signal object
        signal = type(
            "Signal",
            (),
            {"action": "BUY", "symbol": "SPY", "reason": "Strong uptrend"},
        )()

        result = SignalsBuilder.build_signal_information(signal)
        assert "BUY SPY" in result
        assert "Strong uptrend" in result
        assert "Signal Information" in result

    def test_signal_information_without_reason(self) -> None:
        """Test signal information when signal has no reason."""
        signal = type("Signal", (), {"action": "SELL", "symbol": "QQQ", "reason": None})()

        result = SignalsBuilder.build_signal_information(signal)
        assert "SELL QQQ" in result
        assert "Signal Information" in result
        # Should not include " - " when no reason
        assert " - " not in result

    def test_signal_information_raises_on_invalid_signal(self) -> None:
        """Test that invalid signal raises TemplateGenerationError."""
        # Create object that will fail when accessed
        signal = type("BadSignal", (), {})()

        with pytest.raises(TemplateGenerationError) as exc_info:
            SignalsBuilder.build_signal_information(signal)

        assert "Failed to generate signal information HTML" in str(exc_info.value)
        assert exc_info.value.template_type == "signals"
        assert exc_info.value.data_type == "signal"


class TestBuildTechnicalIndicators:
    """Tests for technical indicators HTML generation."""

    def test_technical_indicators_empty(self) -> None:
        """Test technical indicators with empty dict."""
        result = SignalsBuilder.build_technical_indicators({})
        assert "No technical indicators available" in result

    def test_technical_indicators_no_data(self) -> None:
        """Test technical indicators when signals have no indicator data."""
        strategy_signals = {
            "STRATEGY1": {"symbol": "SPY", "action": "BUY"},
        }
        result = SignalsBuilder.build_technical_indicators(strategy_signals)
        assert "No technical indicators data found" in result

    def test_technical_indicators_with_data(self) -> None:
        """Test technical indicators with valid data."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "SPY": {
                        "rsi_10": 75.5,
                        "rsi_20": 68.2,
                        "current_price": 450.25,
                        "ma_200": 440.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_technical_indicators(strategy_signals)
        assert "Technical Indicators" in result
        assert "SPY" in result
        assert "75.5" in result or "75.5" in result  # RSI value
        assert "450.25" in result or "$450.25" in result  # Price


class TestBuildDetailedStrategySignals:
    """Tests for detailed strategy signals HTML generation."""

    def test_detailed_signals_empty(self) -> None:
        """Test detailed signals with empty dict."""
        result = SignalsBuilder.build_detailed_strategy_signals({}, {})
        assert "No strategy signals available" in result

    def test_detailed_signals_buy_action(self) -> None:
        """Test detailed signals with BUY action."""
        strategy_signals = {
            "STRATEGY1": {
                "symbol": "SPY",
                "action": "BUY",
                "reason": "Strong momentum",
                "timestamp": "2024-01-01 10:00:00",
            }
        }
        strategy_summary = {"STRATEGY1": {"allocation": 0.5}}

        result = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)
        assert "Strategy Signals" in result
        assert "BUY" in result
        assert "SPY" in result
        assert "Strong momentum" in result
        assert "50.0%" in result or "50%" in result  # Allocation

    def test_detailed_signals_sell_action(self) -> None:
        """Test detailed signals with SELL action."""
        strategy_signals = {
            "STRATEGY1": {
                "symbol": "QQQ",
                "action": "SELL",
                "reason": "Overbought conditions",
            }
        }

        result = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, {})
        assert "SELL" in result
        assert "QQQ" in result
        assert "Overbought conditions" in result

    def test_detailed_signals_truncates_long_reason(self) -> None:
        """Test that long reasons are truncated to 300 chars."""
        long_reason = "A" * 400
        strategy_signals = {
            "STRATEGY1": {
                "symbol": "SPY",
                "action": "BUY",
                "reason": long_reason,
            }
        }

        result = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, {})
        # Should be truncated with ...
        assert "..." in result
        # Should not contain full 400 char string
        assert "A" * 400 not in result


class TestBuildMarketRegimeAnalysis:
    """Tests for market regime analysis HTML generation."""

    def test_market_regime_empty(self) -> None:
        """Test market regime with empty signals."""
        result = SignalsBuilder.build_market_regime_analysis({})
        assert result == ""

    def test_market_regime_no_spy_data(self) -> None:
        """Test market regime when no SPY data available."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "QQQ": {
                        "current_price": 400.0,
                        "ma_200": 380.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        assert result == ""

    def test_market_regime_bullish(self) -> None:
        """Test market regime analysis shows bullish when price > MA."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "SPY": {
                        "current_price": 450.0,
                        "ma_200": 440.0,
                        "rsi_10": 55.0,
                        "rsi_20": 52.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        assert "Market Regime Analysis" in result
        assert "Bullish Trend" in result
        assert "SPY" in result
        assert "450.00" in result or "$450.00" in result

    def test_market_regime_bearish(self) -> None:
        """Test market regime analysis shows bearish when price < MA."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "SPY": {
                        "current_price": 400.0,
                        "ma_200": 420.0,
                        "rsi_10": 45.0,
                        "rsi_20": 48.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        assert "Bearish Trend" in result

    def test_market_regime_rsi_overbought(self) -> None:
        """Test RSI status shows overbought when RSI > 80."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "SPY": {
                        "current_price": 450.0,
                        "ma_200": 440.0,
                        "rsi_10": 85.0,
                        "rsi_20": 75.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        assert "Overbought" in result

    def test_market_regime_rsi_oversold(self) -> None:
        """Test RSI status shows oversold when RSI < 20."""
        strategy_signals = {
            "STRATEGY1": {
                "technical_indicators": {
                    "SPY": {
                        "current_price": 400.0,
                        "ma_200": 420.0,
                        "rsi_10": 15.0,
                        "rsi_20": 18.0,
                    }
                }
            }
        }
        result = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        assert "Oversold" in result


class TestBuildStrategySignalsNeutral:
    """Tests for neutral mode strategy signals HTML generation."""

    def test_signals_neutral_empty(self) -> None:
        """Test neutral signals with empty dict."""
        result = SignalsBuilder.build_strategy_signals_neutral({})
        assert result == ""

    def test_signals_neutral_with_data(self) -> None:
        """Test neutral signals with valid data."""
        strategy_signals = {
            "STRATEGY1": {
                "action": "BUY",
                "symbol": "SPY",
                "reason": "Strong momentum",
            },
            "STRATEGY2": {
                "action": "SELL",
                "symbol": "QQQ",
                "reason": "Weak trend",
            },
        }
        result = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
        assert "Strategy Signals" in result
        assert "BUY" in result
        assert "SELL" in result
        assert "SPY" in result
        assert "QQQ" in result

    def test_signals_neutral_truncates_reason(self) -> None:
        """Test that reasons are truncated to 100 chars in neutral mode."""
        long_reason = "A" * 150
        strategy_signals = {
            "STRATEGY1": {
                "action": "BUY",
                "symbol": "SPY",
                "reason": long_reason,
            }
        }
        result = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
        assert "..." in result
        # Should not contain the full long reason
        assert long_reason not in result

    def test_signals_neutral_handles_enum_strategy_name(self) -> None:
        """Test neutral signals handles StrategyType enum names."""
        # Create mock enum
        strategy_enum = type("StrategyType", (), {"name": "NUCLEAR"})()
        strategy_signals = {
            strategy_enum: {
                "action": "BUY",
                "symbol": "URA",
                "reason": "Strong nuclear sentiment",
            }
        }
        result = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
        assert "NUCLEAR" in result

    def test_signals_neutral_skips_invalid_data(self) -> None:
        """Test that invalid signal data is skipped with warning."""
        strategy_signals = {
            "STRATEGY1": "not a dict",  # Invalid
            "STRATEGY2": {  # Valid
                "action": "BUY",
                "symbol": "SPY",
                "reason": "Valid signal",
            },
        }
        result = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
        # Should still generate HTML for valid signal
        assert "SPY" in result
        assert "BUY" in result


class TestBuildSignalSummary:
    """Tests for signal summary section builder."""

    def test_signal_summary_with_complete_data(self) -> None:
        """Test signal summary with both strategy signals and consolidated portfolio."""
        strategy_signals = {
            "momentum": {
                "action": "BUY",
                "symbol": "TQQQ",
                "reason": "Strong uptrend detected",
            },
            "mean_reversion": {
                "action": "BUY",
                "symbol": "SOXL",
                "reason": "Oversold conditions",
            },
        }
        consolidated_portfolio = {
            "TQQQ": 0.75,
            "SOXL": 0.25,
        }

        result = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        assert result is not None
        assert "Signal Summary" in result
        assert "Momentum:" in result or "momentum" in result.lower()
        assert "Mean Reversion:" in result or "mean_reversion" in result.lower()
        assert "Consolidated Signal" in result
        assert "75.0% TQQQ" in result
        assert "25.0% SOXL" in result

    def test_signal_summary_with_strategy_signals_only(self) -> None:
        """Test signal summary with only strategy signals (no portfolio)."""
        strategy_signals = {
            "momentum": {
                "action": "BUY",
                "symbol": "SPY",
                "reason": "Test",
            }
        }

        result = SignalsBuilder.build_signal_summary(strategy_signals, {})

        assert result is not None
        assert "Signal Summary" in result
        assert "BUY SPY" in result

    def test_signal_summary_with_portfolio_only(self) -> None:
        """Test signal summary with only consolidated portfolio (no strategy signals)."""
        consolidated_portfolio = {
            "QQQ": 0.6,
            "SPY": 0.4,
        }

        result = SignalsBuilder.build_signal_summary({}, consolidated_portfolio)

        assert result is not None
        assert "Signal Summary" in result
        assert "Consolidated Signal" in result
        assert "60.0% QQQ" in result
        assert "40.0% SPY" in result

    def test_signal_summary_empty_data(self) -> None:
        """Test signal summary with no data returns empty string."""
        result = SignalsBuilder.build_signal_summary({}, {})

        assert result == ""

    def test_signal_summary_handles_enum_strategy_names(self) -> None:
        """Test signal summary correctly handles StrategyType enum keys."""

        class StrategyType:
            def __init__(self, name: str) -> None:
                self.name = name

        strategy_signals = {
            StrategyType("dsl_momentum"): {
                "action": "BUY",
                "symbol": "TQQQ",
                "reason": "Test",
            }
        }
        consolidated_portfolio = {"TQQQ": 1.0}

        result = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        assert result is not None
        assert "Dsl Momentum:" in result or "dsl_momentum" in result.lower()

    def test_signal_summary_ignores_invalid_signal_data(self) -> None:
        """Test signal summary skips invalid signal data."""
        strategy_signals = {
            "valid": {
                "action": "BUY",
                "symbol": "SPY",
                "reason": "Test",
            },
            "invalid": "not a dict",
        }
        consolidated_portfolio = {"SPY": 1.0}

        result = SignalsBuilder.build_signal_summary(strategy_signals, consolidated_portfolio)

        assert result is not None
        assert "Valid:" in result or "valid" in result.lower()
        # Should not crash, should skip invalid entry

    def test_signal_summary_sorts_portfolio_by_allocation(self) -> None:
        """Test consolidated signal sorts symbols by allocation descending."""
        consolidated_portfolio = {
            "SMALL": 0.1,
            "LARGE": 0.6,
            "MEDIUM": 0.3,
        }

        result = SignalsBuilder.build_signal_summary({}, consolidated_portfolio)

        assert result is not None
        # Check that LARGE appears before MEDIUM which appears before SMALL
        large_pos = result.find("60.0% LARGE")
        medium_pos = result.find("30.0% MEDIUM")
        small_pos = result.find("10.0% SMALL")
        assert large_pos < medium_pos < small_pos

    def test_signal_summary_excludes_zero_allocations(self) -> None:
        """Test consolidated signal excludes zero allocations."""
        consolidated_portfolio = {
            "ACTIVE": 0.7,
            "ZERO": 0.0,
            "ALSO_ACTIVE": 0.3,
        }

        result = SignalsBuilder.build_signal_summary({}, consolidated_portfolio)

        assert result is not None
        assert "70.0% ACTIVE" in result
        assert "30.0% ALSO_ACTIVE" in result
        assert "ZERO" not in result


class TestConstants:
    """Tests for module constants."""

    def test_rsi_thresholds_defined(self) -> None:
        """Test that RSI threshold constants are properly defined."""
        assert RSI_OVERBOUGHT_CRITICAL == 80.0
        assert RSI_OVERBOUGHT_WARNING == 70.0
        assert RSI_OVERSOLD == 20.0
        # Verify ordering
        assert RSI_OVERBOUGHT_CRITICAL > RSI_OVERBOUGHT_WARNING
        assert RSI_OVERBOUGHT_WARNING > RSI_OVERSOLD
