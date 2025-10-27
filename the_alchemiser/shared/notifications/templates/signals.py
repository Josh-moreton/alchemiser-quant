"""Business Unit: shared; Status: current.

Signals content builder for email templates.

This module handles building HTML content for technical indicators,
strategy signals, and trading signal analysis.

Note:
    This module is display-only and does not perform financial calculations.
    Float comparisons use threshold values appropriate for display purposes.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

from ...errors.exceptions import TemplateGenerationError
from ...logging import get_logger
from ...types.strategy_types import StrategyType
from .base import BaseEmailTemplate

if TYPE_CHECKING:
    from re import Match

# Module logger
logger = get_logger(__name__)

# Constants
_STRATEGY_TYPE_PREFIX = "StrategyType."

# RSI Thresholds (industry standard)
# RSI > 80: Critically overbought - likely reversal
# RSI 70-80: Overbought warning - caution
# RSI < 20: Oversold - potential buy opportunity
RSI_OVERBOUGHT_CRITICAL = 80.0
RSI_OVERBOUGHT_WARNING = 70.0
RSI_OVERSOLD = 20.0

# String truncation limits
MAX_REASON_LENGTH_DETAILED = 300  # For detailed signal view with full context
MAX_REASON_LENGTH_SUMMARY = 100  # For summary tables where space is limited

# Action color mappings for consistent UI
ACTION_COLORS = {
    "BUY": {
        "text": "#10B981",
        "background": "#D1FAE5",
        "label": "BUY",
    },
    "SELL": {
        "text": "#EF4444",
        "background": "#FEE2E2",
        "label": "SELL",
    },
    "HOLD": {
        "text": "#6B7280",
        "background": "#F3F4F6",
        "label": "HOLD",
    },
}


# Type definitions for better type safety
class TechnicalIndicators(TypedDict, total=False):
    """Technical indicator data structure."""

    rsi_10: float
    rsi_20: float
    current_price: float
    ma_200: float


class SignalData(TypedDict, total=False):
    """Signal data structure for strategy signals."""

    action: str
    symbol: str
    reason: str
    timestamp: str
    technical_indicators: dict[str, TechnicalIndicators]


class SignalProtocol(Protocol):
    """Protocol for signal objects."""

    action: str
    symbol: str
    reason: str | None


class SignalsBuilder:
    """Builds signals-related HTML content for emails.

    This class provides static methods for generating HTML sections
    for trading signals, technical indicators, and market analysis
    that are embedded in email notifications.

    All methods are pure functions that take signal/indicator data
    and return formatted HTML strings. No I/O or side effects.
    """

    @staticmethod
    def _get_rsi_color(rsi_value: float) -> str:
        """Get color for RSI value based on overbought/oversold thresholds.

        Uses industry-standard RSI thresholds:
        - Above 80: Critically overbought - Red (#EF4444)
        - 70-80: Overbought warning - Orange (#F59E0B)
        - Below 70: Normal range - Green (#10B981)

        Args:
            rsi_value: RSI indicator value (typically 0-100)

        Returns:
            Hex color code string for visual display

        """
        if rsi_value > RSI_OVERBOUGHT_CRITICAL:
            return "#EF4444"  # Red - Overbought
        if rsi_value > RSI_OVERBOUGHT_WARNING:
            return "#F59E0B"  # Orange - Warning
        return "#10B981"  # Green - Normal

    @staticmethod
    def _get_price_vs_ma_info(current_price: float, ma_200: float) -> tuple[str, str]:
        """Get price vs moving average comparison info.

        Compares current price to 200-day moving average to determine
        trend direction (bullish if above, bearish if below).

        Args:
            current_price: Current asset price
            ma_200: 200-day moving average

        Returns:
            Tuple of (label, color) where:
            - label: "Above" or "Below"
            - color: Green for above, Red for below

        """
        if current_price > ma_200:
            return "Above", "#10B981"
        return "Below", "#EF4444"

    @staticmethod
    def _format_indicator_row(symbol: str, indicators: TechnicalIndicators) -> str:
        """Format a single indicator row for technical indicators table.

        Args:
            symbol: Stock symbol (e.g., "SPY", "QQQ")
            indicators: Dictionary containing technical indicator values

        Returns:
            HTML table row string

        Note:
            Missing indicators default to 0 for display purposes.
            This is acceptable for HTML display but should not be
            used for trading calculations.

        """
        rsi_10 = indicators.get("rsi_10", 0)
        rsi_20 = indicators.get("rsi_20", 0)
        current_price = indicators.get("current_price", 0)
        ma_200 = indicators.get("ma_200", 0)

        rsi_color = SignalsBuilder._get_rsi_color(rsi_10)
        price_vs_ma, price_color = SignalsBuilder._get_price_vs_ma_info(current_price, ma_200)

        return f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                {symbol}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {rsi_color}; font-weight: 600;">
                {rsi_10:.1f}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                {rsi_20:.1f}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                ${current_price:.2f}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {price_color};">
                {price_vs_ma}
            </td>
        </tr>
        """

    @staticmethod
    def _truncate_reason(reason: str, max_length: int) -> str:
        """Truncate reason string to maximum length.

        Args:
            reason: The reason text to truncate
            max_length: Maximum length before truncation

        Returns:
            Truncated string with ellipsis if longer than max_length,
            original string otherwise

        """
        if len(reason) > max_length:
            return reason[:max_length] + "..."
        return reason

    @staticmethod
    def _truncate_with_arrows(parts: list[str], max_length: int) -> str:
        """Truncate decision path parts while preserving complete nodes.

        Args:
            parts: List of decision path parts split by arrows
            max_length: Maximum length before truncation

        Returns:
            Truncated string with preserved nodes and ellipsis

        """
        result_parts: list[str] = []
        current_length = 0

        for part in parts:
            # Account for arrow separator (3 chars: " → ")
            part_length = len(part) + (3 if result_parts else 0)

            if current_length + part_length <= max_length - 3:  # Reserve 3 for "..."
                result_parts.append(part)
                current_length += part_length
            else:
                break

        if result_parts:
            return " → ".join(result_parts) + "..."
        return ""

    @staticmethod
    def _format_decision_path_for_table(reason: str, max_length: int) -> str:
        """Format decision path for table display with smart truncation.

        Preserves decision path symbols (✓, →) and intelligently truncates
        while maintaining readability. Used in neutral signal tables where
        space is limited.

        Args:
            reason: The reasoning text containing decision path (may include ✓ and → symbols)
            max_length: Maximum length before truncation

        Returns:
            Formatted string with decision path symbols preserved, truncated if needed

        Examples:
            >>> _format_decision_path_for_table("Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation", 100)
            "Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"

            >>> _format_decision_path_for_table("Very long decision path with many conditions...", 50)
            "Very long decision path with many conditions..."

        """
        if len(reason) <= max_length:
            return reason

        # For decision paths with arrows, try to keep complete decision nodes
        if "→" in reason:
            parts = reason.split(" → ")
            truncated = SignalsBuilder._truncate_with_arrows(parts, max_length)
            if truncated:
                return truncated

        # Fallback to simple truncation if no arrow or can't preserve nodes
        return reason[:max_length] + "..."

    @staticmethod
    def _render_decision_tree(reason: str) -> str:
        """Render decision path as hierarchical tree with visual formatting.

        Converts flat decision path text into visually structured HTML
        with proper indentation and hierarchy. Used in detailed signal cards
        to provide clear visual distinction between decision steps.

        Args:
            reason: The reasoning text containing decision path

        Returns:
            HTML string with hierarchical formatting for decision steps

        Examples:
            Input: "Nuclear: ✓ 5 > 3 → ✓ TQQQ RSI(10) < 81 → 75.0% allocation"
            Output: HTML with indented decision steps and visual hierarchy

        Note:
            - Preserves checkmarks (✓) and arrows (→) from decision paths
            - Adds visual indentation for better readability
            - Falls back to simple formatting if no decision path detected

        """
        # Check if this contains decision path formatting (arrows and checkmarks)
        if "→" not in reason and "✓" not in reason:
            # Not a decision path, return as-is wrapped in basic formatting
            return f'<div style="color: #4B5563; font-size: 14px; line-height: 1.5;">{reason}</div>'

        # Split by arrows to get decision steps
        steps = reason.split(" → ")

        # Build hierarchical HTML structure
        html_parts = []

        for i, step in enumerate(steps):
            # Calculate indentation based on step depth
            indent = i * 16  # 16px per level

            # Determine if this is a success (✓) or failure step
            is_success = "✓" in step
            color = "#10B981" if is_success else "#6B7280"  # Green for success, gray otherwise

            # Add step with indentation
            html_parts.append(
                f'<div style="margin-left: {indent}px; color: {color}; font-size: 14px; '
                f'line-height: 1.8; font-family: monospace;">{step.strip()}</div>'
            )

        return "".join(html_parts)

    @staticmethod
    def build_signal_information(signal: SignalProtocol | Any) -> str:  # noqa: ANN401
        """Build HTML for signal information section.

        Args:
            signal: Signal object (Alert or StrategySignal) with action,
                   symbol, and optional reason attributes

        Returns:
            HTML string for signal information box, or empty string if no signal

        Raises:
            TemplateGenerationError: If signal processing fails

        Note:
            Still accepts Any for backwards compatibility with existing callers.
            Will be fully typed once all signal objects implement SignalProtocol.

        """
        if not signal:
            logger.debug("build_signal_information_skipped", reason="no_signal")
            return ""

        try:
            action = getattr(signal, "action", "UNKNOWN")
            symbol = getattr(signal, "symbol", "UNKNOWN")
            reason = getattr(signal, "reason", None)

            logger.debug(
                "building_signal_information",
                action=action,
                symbol=symbol,
                has_reason=reason is not None,
            )

            return f"""
            <div style="margin: 24px 0; padding: 16px; background-color: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px;">
                <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 15px; font-weight: 600; letter-spacing: 0.3px;">Signal Information</h3>
                <p style="margin: 0; color: #92400E; line-height: 1.6;">
                    <strong>{action} {symbol}</strong>
                    {f" - {reason}" if reason else ""}
                </p>
            </div>
            """
        except Exception as e:
            logger.error(
                "signal_information_generation_failed",
                error=str(e),
                signal_type=type(signal).__name__,
                module="signals",
            )
            raise TemplateGenerationError(
                f"Failed to generate signal information HTML: {e}",
                template_type="signals",
                data_type="signal",
            ) from e

    @staticmethod
    def build_technical_indicators(strategy_signals: dict[Any, SignalData]) -> str:
        """Build technical indicators HTML section.

        Args:
            strategy_signals: Dictionary mapping strategy types to signal data

        Returns:
            HTML string containing technical indicators table(s)

        Note:
            Still accepts Any keys for backwards compatibility.
            Strategy types may be enums or strings.

        """
        if not strategy_signals:
            logger.debug("build_technical_indicators_skipped", reason="no_signals")
            return BaseEmailTemplate.create_alert_box("No technical indicators available", "info")

        logger.debug("building_technical_indicators", strategy_count=len(strategy_signals))

        indicators_html = ""

        for strategy_type, signal_data in strategy_signals.items():
            technical_indicators = signal_data.get("technical_indicators", {})
            if not technical_indicators:
                continue

            strategy_name = str(strategy_type).replace(_STRATEGY_TYPE_PREFIX, "")

            # Generate indicator rows using helper method
            indicators_rows = "".join(
                SignalsBuilder._format_indicator_row(symbol, indicators)
                for symbol, indicators in technical_indicators.items()
            )

            if indicators_rows:
                indicators_html += f"""
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 12px 0; color: #1F2937; font-size: 16px; font-weight: 600;">
                        {strategy_name} Strategy Indicators
                    </h4>
                    <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <thead>
                            <tr style="background-color: #F9FAFB;">
                                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                                <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">RSI(10)</th>
                                <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">RSI(20)</th>
                                <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Price</th>
                                <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">vs 200MA</th>
                            </tr>
                        </thead>
                        <tbody>
                            {indicators_rows}
                        </tbody>
                    </table>
                </div>
                """

        if not indicators_html:
            logger.debug("build_technical_indicators_no_data")
            return BaseEmailTemplate.create_alert_box("No technical indicators data found", "info")

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">Technical Indicators</h3>
            {indicators_html}
        </div>
        """

    @staticmethod
    def build_detailed_strategy_signals(
        strategy_signals: dict[Any, SignalData],
        strategy_summary: dict[str, Any],
    ) -> str:
        """Build detailed strategy signals HTML section.

        Args:
            strategy_signals: Dictionary mapping strategy types to signal data
            strategy_summary: Dictionary containing strategy allocation summaries

        Returns:
            HTML string containing detailed signal cards

        Note:
            Uses ACTION_COLORS constant for consistent styling.
            Reason text is truncated to MAX_REASON_LENGTH_DETAILED (300 chars).

        """
        if not strategy_signals:
            logger.debug("build_detailed_strategy_signals_skipped", reason="no_signals")
            return BaseEmailTemplate.create_alert_box("No strategy signals available", "info")

        logger.debug(
            "building_detailed_strategy_signals",
            signal_count=len(strategy_signals),
        )

        signals_html = ""

        for strategy_type, signal_data in strategy_signals.items():
            strategy_name = str(strategy_type).replace(_STRATEGY_TYPE_PREFIX, "")

            # Get strategy summary data if available
            summary_data = strategy_summary.get(strategy_name, {})
            allocation = summary_data.get("allocation", 0)

            # Get symbols list and join for display
            symbols_list = signal_data.get("symbols", [])
            if isinstance(symbols_list, list):
                symbol = ", ".join(str(s) for s in symbols_list) if symbols_list else "N/A"
            else:
                symbol = str(symbols_list) if symbols_list else "N/A"

            action = signal_data.get("action", "UNKNOWN")
            reason = signal_data.get("reason", "No reason provided")
            timestamp = signal_data.get("timestamp", "")

            # Get colors from constant mapping
            colors = ACTION_COLORS.get(action, ACTION_COLORS["HOLD"])
            action_color = colors["text"]
            action_bg = colors["background"]
            action_label = colors["label"]

            # Render decision tree for detailed display
            # First truncate if too long, then render as tree
            truncated_reason = SignalsBuilder._truncate_reason(reason, MAX_REASON_LENGTH_DETAILED)
            formatted_reason = SignalsBuilder._render_decision_tree(truncated_reason)

            signals_html += f"""
            <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 12px; border-left: 4px solid {action_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <h4 style="margin: 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
                            {strategy_name} Strategy
                        </h4>
                        <div style="margin-top: 4px;">
                            <span style="color: #6B7280; font-size: 14px;">Target: </span>
                            <span style="font-weight: 600; color: #1F2937;">{symbol}</span>
                            {f'<span style="color: #6B7280; font-size: 14px; margin-left: 16px;">Allocation: </span><span style="font-weight: 600; color: #1F2937;">{allocation:.1%}</span>' if allocation > 0 else ""}
                        </div>
                    </div>
                    <div style="background-color: {action_bg}; color: {action_color}; padding: 8px 16px; border-radius: 20px; font-size: 15px; font-weight: 600;">
                        {action_label}
                    </div>
                </div>
                <div style="background-color: #F8FAFC; padding: 16px; border-radius: 8px; margin-bottom: 12px;">
                    <h5 style="margin: 0 0 8px 0; color: #374151; font-size: 14px; font-weight: 600;">Strategy Reasoning:</h5>
                    {formatted_reason}
                </div>
                {f'<div style="color: #9CA3AF; font-size: 12px; text-align: right;">Generated: {timestamp}</div>' if timestamp else ""}
            </div>
            """

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">Strategy Signals</h3>
            {signals_html}
        </div>
        """

    @staticmethod
    def build_market_regime_analysis(strategy_signals: dict[Any, SignalData]) -> str:
        """Build market regime analysis section.

        Analyzes SPY (S&P 500 ETF) technical indicators to determine
        overall market regime (bullish/bearish) based on price vs 200MA
        and RSI levels.

        Args:
            strategy_signals: Dictionary mapping strategy types to signal data

        Returns:
            HTML string containing market regime analysis, or empty string
            if SPY data is not available

        Note:
            Uses RSI_OVERBOUGHT_CRITICAL and RSI_OVERSOLD constants
            for threshold comparisons.

        """
        if not strategy_signals:
            logger.debug("build_market_regime_analysis_skipped", reason="no_signals")
            return ""

        # Extract SPY data if available
        spy_data = None
        for signal_data in strategy_signals.values():
            technical_indicators = signal_data.get("technical_indicators", {})
            if "SPY" in technical_indicators:
                spy_data = technical_indicators["SPY"]
                break

        if not spy_data:
            logger.debug("build_market_regime_analysis_skipped", reason="no_spy_data")
            return ""

        current_price = spy_data.get("current_price", 0)
        ma_200 = spy_data.get("ma_200", 0)
        rsi_10 = spy_data.get("rsi_10", 0)
        rsi_20 = spy_data.get("rsi_20", 0)

        logger.debug(
            "building_market_regime_analysis",
            current_price=current_price,
            ma_200=ma_200,
            rsi_10=rsi_10,
        )

        # Determine market regime based on price vs 200MA
        if current_price > ma_200:
            regime = "Bullish Trend"
            regime_color = "#10B981"
            regime_bg = "#D1FAE5"
        else:
            regime = "Bearish Trend"
            regime_color = "#EF4444"
            regime_bg = "#FEE2E2"

        # RSI analysis using defined thresholds
        if rsi_10 > RSI_OVERBOUGHT_CRITICAL:
            rsi_status = "Overbought"
            rsi_color = "#EF4444"
        elif rsi_10 < RSI_OVERSOLD:
            rsi_status = "Oversold"
            rsi_color = "#10B981"
        else:
            rsi_status = "Neutral"
            rsi_color = "#6B7280"

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">Market Regime Analysis</h3>
            <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h4 style="margin: 0; color: #1F2937; font-size: 15px; font-weight: 600; letter-spacing: 0.3px;">SPY Market Analysis</h4>
                    <div style="background-color: {regime_bg}; color: {regime_color}; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                        {regime}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                    <div style="text-align: center; padding: 12px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 18px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">
                            ${current_price:.2f}
                        </div>
                        <div style="font-size: 12px; color: #6B7280;">Current Price</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 18px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">
                            ${ma_200:.2f}
                        </div>
                        <div style="font-size: 12px; color: #6B7280;">200-Day MA</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 18px; font-weight: 600; color: {rsi_color}; margin-bottom: 4px;">
                            {rsi_10:.1f}
                        </div>
                        <div style="font-size: 12px; color: #6B7280;">RSI(10) - {rsi_status}</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 18px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">
                            {rsi_20:.1f}
                        </div>
                        <div style="font-size: 12px; color: #6B7280;">RSI(20)</div>
                    </div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def build_price_action_gauge(strategy_signals: dict[Any, SignalData]) -> str:
        """Build price action gauge table showing RSI and price vs MA for all symbols.

        Creates a comprehensive gauge showing technical indicators for each symbol
        to help classify market conditions (overbought/oversold, bullish/bearish).

        Args:
            strategy_signals: Dictionary mapping strategy types to signal data

        Returns:
            HTML string containing price action gauge table, or empty string
            if no technical indicator data is available

        Note:
            Conflicting indicators (e.g., RSI oversold but price above MA) are
            indicated in the gauge classification.

        """
        if not strategy_signals:
            logger.debug("build_price_action_gauge_skipped", reason="no_signals")
            return ""

        # Collect all unique symbols and their indicators
        symbol_indicators = SignalsBuilder._collect_symbol_indicators(strategy_signals)

        if not symbol_indicators:
            logger.debug("build_price_action_gauge_skipped", reason="no_indicator_data")
            return ""

        logger.debug(
            "building_price_action_gauge",
            symbol_count=len(symbol_indicators),
        )

        # Build gauge rows
        gauge_rows = []
        for symbol in sorted(symbol_indicators.keys()):
            indicators = symbol_indicators[symbol]
            rsi_10 = indicators.get("rsi_10")
            current_price = indicators.get("current_price")
            ma_200 = indicators.get("ma_200")

            # Skip symbols with missing required indicators
            if rsi_10 is None or current_price is None or ma_200 is None:
                logger.debug(
                    "Skipping symbol due to missing indicator(s)",
                    symbol=symbol,
                    rsi_10=rsi_10,
                    current_price=current_price,
                    ma_200=ma_200,
                )
                continue

            # Get RSI classification and color
            rsi_classification = SignalsBuilder._get_rsi_classification(rsi_10)
            rsi_color = SignalsBuilder._get_rsi_color(rsi_10)

            # Get price vs MA info
            price_vs_ma_label, price_vs_ma_color = SignalsBuilder._get_price_vs_ma_info(
                current_price, ma_200
            )

            # Build composite gauge classification
            trend = "Bullish" if current_price > ma_200 else "Bearish"
            conflict_note = (
                " ⚠️"
                if SignalsBuilder._has_conflicting_indicators(rsi_10, current_price, ma_200)
                else ""
            )
            gauge_classification = f"{rsi_classification.title()} / {trend}{conflict_note}"

            # Build and append gauge row
            gauge_rows.append(
                SignalsBuilder._build_gauge_row(
                    symbol,
                    rsi_10,
                    rsi_color,
                    price_vs_ma_label,
                    price_vs_ma_color,
                    gauge_classification,
                )
            )

        gauge_table = "".join(gauge_rows)

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">Price Action Gauge</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Symbol
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            RSI(10)
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Price vs 200-MA
                        </th>
                        <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Gauge
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {gauge_table}
                </tbody>
            </table>
            <div style="margin-top: 8px; padding: 8px; background-color: #FEF3C7; border-radius: 6px; font-size: 12px; color: #92400E;">
                ⚠️ indicates conflicting indicators (e.g., RSI oversold but price above MA or vice versa)
            </div>
        </div>
        """

    @staticmethod
    def _safe_float_conversion(value: float | int | str, context: str = "") -> float:
        """Safely convert a value to float with error handling.

        Args:
            value: Value to convert to float (float, int, or string)
            context: Context string for logging (e.g., symbol name)

        Returns:
            Float value or 0.0 if conversion fails

        """
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid allocation value in consolidated_portfolio",
                value=value,
                context=context,
            )
            return 0.0

    @staticmethod
    def _extract_strategy_name_and_content(reasoning: str) -> tuple[str, str]:
        """Extract strategy name and content from reasoning string.

        Args:
            reasoning: Raw DSL reasoning string

        Returns:
            Tuple of (strategy_name, content)

        """
        if ":" in reasoning:
            parts = reasoning.split(":", 1)
            return parts[0].strip(), parts[1].strip()
        return "", reasoning

    @staticmethod
    def _extract_allocation(content: str) -> str:
        """Extract allocation percentage from content string.

        Args:
            content: Content portion of reasoning string

        Returns:
            Human-readable allocation string or empty string

        """
        if "%" in content and "allocation" in content.lower():
            import re

            match = re.search(r"(\d+\.?\d*)\s*%\s*allocation", content, re.IGNORECASE)
            if match:
                return f"allocation set to {match.group(1)}%"
        return ""

    @staticmethod
    def _get_rsi_classification(rsi_value: float) -> str:
        """Get RSI classification label based on value.

        Args:
            rsi_value: RSI indicator value (0-100)

        Returns:
            Classification label (overbought/oversold/neutral)

        """
        if rsi_value > RSI_OVERBOUGHT_CRITICAL:
            return "critically overbought"
        if rsi_value > RSI_OVERBOUGHT_WARNING:
            return "overbought"
        if rsi_value < RSI_OVERSOLD:
            return "oversold"
        return "neutral"

    @staticmethod
    def _collect_symbol_indicators(
        strategy_signals: dict[Any, SignalData],
    ) -> dict[str, TechnicalIndicators]:
        """Collect all unique symbols and their technical indicators.

        Args:
            strategy_signals: Dictionary mapping strategy types to signal data

        Returns:
            Dictionary mapping symbols to their technical indicators

        """
        symbol_indicators: dict[str, TechnicalIndicators] = {}
        for signal_data in strategy_signals.values():
            technical_indicators = signal_data.get("technical_indicators", {})
            for symbol, indicators in technical_indicators.items():
                if symbol not in symbol_indicators:
                    symbol_indicators[symbol] = indicators
        return symbol_indicators

    @staticmethod
    def _has_conflicting_indicators(rsi_10: float, current_price: float, ma_200: float) -> bool:
        """Check if RSI and price vs MA indicators conflict.

        Args:
            rsi_10: RSI(10) value
            current_price: Current asset price
            ma_200: 200-day moving average

        Returns:
            True if indicators conflict (e.g., RSI oversold but price above MA)

        """
        oversold_but_bullish = rsi_10 < RSI_OVERSOLD and current_price > ma_200
        overbought_but_bearish = rsi_10 > RSI_OVERBOUGHT_CRITICAL and current_price < ma_200
        return oversold_but_bullish or overbought_but_bearish

    @staticmethod
    def _build_gauge_row(
        symbol: str,
        rsi_10: float,
        rsi_color: str,
        price_vs_ma_label: str,
        price_vs_ma_color: str,
        gauge_classification: str,
    ) -> str:
        """Build a single gauge table row.

        Args:
            symbol: Stock symbol
            rsi_10: RSI(10) value
            rsi_color: Color for RSI display
            price_vs_ma_label: Label for price vs MA comparison
            price_vs_ma_color: Color for price vs MA display
            gauge_classification: Composite gauge classification text

        Returns:
            HTML table row string

        """
        return f"""
                <tr>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;">
                        {symbol}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: {rsi_color}; font-weight: 600;">
                        {rsi_10:.1f}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: {price_vs_ma_color}; font-weight: 600;">
                        {price_vs_ma_label}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: left; color: #374151;">
                        {gauge_classification}
                    </td>
                </tr>
                """

    @staticmethod
    def _parse_rsi_condition_with_value(
        symbol: str,
        rsi_period: str,
        operator: str,
        threshold: str,
        indicators: TechnicalIndicators,
    ) -> str | None:
        """Parse RSI condition with actual value from indicators.

        Args:
            symbol: Stock symbol
            rsi_period: RSI period (e.g., "10", "20")
            operator: Comparison operator (">", "<", ">=", "<=")
            threshold: Threshold value
            indicators: Technical indicators for the symbol

        Returns:
            Formatted condition string with actual RSI value, or None if not available

        """
        rsi_field = f"rsi_{rsi_period}"
        actual_rsi = indicators.get(rsi_field)

        if actual_rsi is not None and isinstance(actual_rsi, (int, float)):
            classification = SignalsBuilder._get_rsi_classification(float(actual_rsi))
            operator_word = "above" if ">" in operator else "below"
            return (
                f"{symbol} RSI({rsi_period}) is **{actual_rsi:.1f}**, "
                f"{operator_word} the **{threshold}** threshold "
                f"(**{classification}**)"
            )
        return None

    @staticmethod
    def _parse_rsi_condition_match(
        match: Match[str],
        technical_indicators: dict[str, TechnicalIndicators] | None,
    ) -> str:
        """Parse matched RSI condition into human-readable text.

        Args:
            match: Regex match object with RSI condition parts
            technical_indicators: Optional dict of technical indicators

        Returns:
            Formatted condition string

        """
        symbol = match.group(1)
        rsi_period = match.group(2)
        operator = match.group(3)
        threshold = match.group(4)

        # Try to get actual RSI value if indicators available
        if technical_indicators and symbol in technical_indicators:
            indicators = technical_indicators[symbol]
            with_value = SignalsBuilder._parse_rsi_condition_with_value(
                symbol, rsi_period, operator, threshold, indicators
            )
            if with_value:
                return with_value

        # Fallback without actual value
        operator_word = "above" if ">" in operator else "below"
        return f"{symbol} RSI({rsi_period}) {operator_word} {threshold}"

    @staticmethod
    def _parse_rsi_condition(
        condition: str,
        technical_indicators: dict[str, TechnicalIndicators] | None,
    ) -> str | None:
        """Parse RSI condition into human-readable text.

        Args:
            condition: Condition string containing RSI
            technical_indicators: Optional dict of technical indicators

        Returns:
            Parsed condition string or None

        """
        # Extract symbol, RSI period, operator, and threshold
        match = re.search(
            r"\b([A-Z]{2,5})\s+RSI\((\d+)\)\s*([<>]=?)\s*(\d+\.?\d*)",
            condition,
            re.IGNORECASE,
        )

        if match:
            return SignalsBuilder._parse_rsi_condition_match(match, technical_indicators)

        # Fallback for simple RSI mentions without thresholds
        symbols = re.findall(r"\b([A-Z]{2,5})\s+(?:rsi|RSI)", condition)
        if symbols:
            return f"RSI conditions met on {' and '.join(symbols)}"

        return None

    @staticmethod
    def _parse_drawdown_condition(condition: str) -> str | None:
        """Parse drawdown condition into human-readable text.

        Args:
            condition: Condition string containing drawdown

        Returns:
            Parsed condition string or None

        """
        symbols = re.findall(r"\b[A-Z]{2,5}\b", condition)
        symbols = [s for s in symbols if s not in ("RSI", "MAX", "AND", "OR")]

        # Try to extract threshold percentage
        threshold_match = re.search(r"(\d+\.?\d*)%", condition)
        threshold_text = f" **{threshold_match.group(1)}%**" if threshold_match else ""

        if symbols:
            if len(symbols) == 1:
                return f"{symbols[0]} exceeded max drawdown threshold{threshold_text}"
            return f"drawdown check on {', '.join(symbols)}{threshold_text}"

        return None

    @staticmethod
    def _parse_condition(
        condition: str,
        technical_indicators: dict[str, TechnicalIndicators] | None = None,
    ) -> str | None:
        """Parse a single condition into human-readable text with actual indicator values.

        Args:
            condition: Condition string to parse (e.g., "SPY RSI(10)>79")
            technical_indicators: Optional dict mapping symbols to their technical indicators

        Returns:
            Human-readable condition string with actual values, or None if should be skipped

        Examples:
            >>> _parse_condition("SPY RSI(10)>79", {"SPY": {"rsi_10": 82.5}})
            "SPY RSI(10) is 82.5, above the 79 threshold (critically overbought)"

        """
        # Skip allocation text
        if "allocation" in condition.lower() or not condition:
            return None

        # Parse RSI conditions with thresholds
        if "rsi" in condition.lower():
            return SignalsBuilder._parse_rsi_condition(condition, technical_indicators)

        # Parse max-drawdown conditions
        if "max-drawdown" in condition.lower() or "drawdown" in condition.lower():
            return SignalsBuilder._parse_drawdown_condition(condition)

        return "conditions satisfied"

    @staticmethod
    def _deduplicate_conditions(conditions: list[str]) -> list[str]:
        """Deduplicate conditions while preserving order.

        Args:
            conditions: List of condition strings

        Returns:
            List of unique conditions in original order

        """
        seen = set()
        unique_conditions = []
        for cond in conditions:
            if cond not in seen:
                seen.add(cond)
                unique_conditions.append(cond)
        return unique_conditions

    @staticmethod
    def _extract_conditions_from_dsl(
        content: str,
        technical_indicators: dict[str, TechnicalIndicators] | None,
    ) -> list[str]:
        """Extract and parse conditions from DSL content.

        Args:
            content: DSL content string with conditions
            technical_indicators: Optional dict mapping symbols to their technical indicators

        Returns:
            List of parsed condition strings

        """
        conditions = []
        parts = content.split("→")
        for part in parts:
            part = part.strip()
            if "✓" in part:
                condition = part.replace("✓", "").strip()
                parsed = SignalsBuilder._parse_condition(condition, technical_indicators)
                if parsed:
                    conditions.append(parsed)
        return conditions

    @staticmethod
    def _build_summary_text(
        strategy_name: str,
        unique_conditions: list[str],
        allocation: str,
    ) -> str:
        """Build final summary text from components.

        Args:
            strategy_name: Name of the strategy
            unique_conditions: List of parsed conditions
            allocation: Allocation text

        Returns:
            Formatted summary string

        """
        summary_parts = []
        if strategy_name:
            summary_parts.append(f"{strategy_name} strategy triggered")
        if unique_conditions:
            summary_parts.append(", ".join(unique_conditions))
        if allocation:
            summary_parts.append(allocation)

        if not summary_parts:
            return ""
        if len(summary_parts) == 1:
            return summary_parts[0]
        return f"{summary_parts[0]}: {', '.join(summary_parts[1:])}"

    @staticmethod
    def _parse_dsl_reasoning_to_human_readable(
        reasoning: str,
        technical_indicators: dict[str, TechnicalIndicators] | None = None,
    ) -> str:
        """Parse DSL reasoning into human-readable text with actual indicator values.

        Converts technical DSL expressions like:
        "Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"

        Into enriched human-friendly text with actual values like:
        "Nuclear strategy triggered: SPY RSI(10) is 82.5, above the 79 threshold (overbought),
        allocation set to 75.0%"

        Args:
            reasoning: Raw DSL reasoning string with technical expressions
            technical_indicators: Optional dict mapping symbols to their technical indicators

        Returns:
            Human-readable summary string with actual indicator values

        """
        if not reasoning:
            return ""

        strategy_name, content = SignalsBuilder._extract_strategy_name_and_content(reasoning)
        allocation = SignalsBuilder._extract_allocation(content)

        # Extract and parse conditions
        conditions = SignalsBuilder._extract_conditions_from_dsl(content, technical_indicators)
        unique_conditions = SignalsBuilder._deduplicate_conditions(conditions)

        # Build summary
        summary = SignalsBuilder._build_summary_text(strategy_name, unique_conditions, allocation)
        if summary:
            return summary

        # Fallback to truncated original if parsing fails
        return SignalsBuilder._truncate_reason(reasoning, MAX_REASON_LENGTH_SUMMARY)

    @staticmethod
    def _format_strategy_display_name(strategy_name: str | StrategyType) -> str:
        """Format strategy name for display.

        Args:
            strategy_name: Strategy name (enum or string)

        Returns:
            Formatted display name

        """
        if hasattr(strategy_name, "name"):
            return strategy_name.name.replace("_", " ").title()
        return str(strategy_name).title()

    @staticmethod
    def _build_signal_string_from_data(signal_data: dict[str, Any] | SignalData) -> str:
        """Build signal string from signal data.

        Args:
            signal_data: Dictionary containing signal information

        Returns:
            Formatted signal string

        """
        signal_str = str(signal_data.get("signal", ""))
        if signal_str:
            return signal_str

        # Fallback: build signal from symbols/action
        action = str(signal_data.get("action", "UNKNOWN"))
        symbols_list = signal_data.get("symbols", [])
        if symbols_list and isinstance(symbols_list, list):
            symbols_str = ", ".join(str(s) for s in symbols_list)
            return f"{action} {symbols_str}"
        return action

    @staticmethod
    def _build_strategy_row_html(
        strategy_display_name: str,
        display_line: str,
    ) -> str:
        """Build HTML for a single strategy row.

        Args:
            strategy_display_name: Formatted strategy name
            display_line: Display line with reasoning and signal

        Returns:
            HTML string for the row

        """
        return f"""
                <div style="padding: 8px 0; color: #374151; font-size: 14px; line-height: 1.6;">
                    <strong style="color: #1F2937;">{strategy_display_name}:</strong> {display_line}
                </div>
                """

    @staticmethod
    def _build_strategy_rows(
        strategy_signals: dict[str | StrategyType, SignalData],
    ) -> list[str]:
        """Build HTML rows for individual strategy signals.

        Args:
            strategy_signals: Dictionary mapping strategy names to signal data

        Returns:
            List of HTML row strings

        """
        strategy_rows = []
        for strategy_name, signal_data in strategy_signals.items():
            if not isinstance(signal_data, dict):
                continue

            strategy_display_name = SignalsBuilder._format_strategy_display_name(strategy_name)

            # Get signal components
            reasoning = str(signal_data.get("reasoning", signal_data.get("reason", "")))
            signal_str = SignalsBuilder._build_signal_string_from_data(signal_data)
            technical_indicators = signal_data.get("technical_indicators", {})

            # Parse DSL reasoning into human-readable text
            human_readable_reason = ""
            if reasoning:
                human_readable_reason = SignalsBuilder._parse_dsl_reasoning_to_human_readable(
                    reasoning,
                    technical_indicators,
                )

            # Build display line
            display_line = (
                f"{human_readable_reason} → {signal_str}" if human_readable_reason else signal_str
            )

            strategy_rows.append(
                SignalsBuilder._build_strategy_row_html(strategy_display_name, display_line)
            )

        return strategy_rows

    @staticmethod
    def _build_consolidated_string(consolidated_portfolio: dict[str, float]) -> str:
        """Build consolidated allocation string from portfolio.

        Args:
            consolidated_portfolio: Dictionary mapping symbols to allocations

        Returns:
            Formatted allocation string

        """
        if not consolidated_portfolio:
            return ""

        sorted_allocations = sorted(
            consolidated_portfolio.items(),
            key=lambda x: SignalsBuilder._safe_float_conversion(x[1], x[0]),
            reverse=True,
        )

        allocation_parts = []
        for symbol, weight in sorted_allocations:
            try:
                float_weight = float(weight)
            except (ValueError, TypeError):
                logger.warning("Invalid allocation value", symbol=symbol, value=weight)
                continue
            if float_weight > 0:
                allocation_parts.append(f"{float_weight:.1%} {symbol}")

        return " / ".join(allocation_parts) if allocation_parts else "No allocation"

    @staticmethod
    def build_signal_summary(
        strategy_signals: dict[str | StrategyType, SignalData],
        consolidated_portfolio: dict[str, float],
    ) -> str:
        """Build signal summary section showing individual and consolidated signals.

        Creates a concise summary at the top of the email showing:
        1. Individual strategy signals (e.g., "Strategy A: 50% TQQQ / 50% SOXL")
        2. Consolidated signal (aggregated allocation across all strategies)

        Args:
            strategy_signals: Dictionary mapping strategy names/types to signal data
            consolidated_portfolio: Dictionary mapping symbols to target allocations

        Returns:
            HTML string containing signal summary section, or empty string
            if no signals or portfolio data available

        Note:
            This section appears immediately after the email header to provide
            a quick overview of generated signals before portfolio and trade details.

        """
        if not strategy_signals and not consolidated_portfolio:
            logger.debug("build_signal_summary_skipped", reason="no_data")
            return ""

        logger.debug(
            "building_signal_summary",
            signal_count=len(strategy_signals),
            portfolio_symbols=len(consolidated_portfolio),
        )

        # Build individual strategy signal rows
        strategy_rows = SignalsBuilder._build_strategy_rows(strategy_signals)
        strategy_section = "".join(strategy_rows) if strategy_rows else ""

        # Build consolidated signal from portfolio
        consolidated_str = SignalsBuilder._build_consolidated_string(consolidated_portfolio)

        return f"""
        <div style="margin: 0 0 28px 0; padding: 20px; background-color: #F0F9FF; border-left: 4px solid #3B82F6; border-radius: 8px;">
            <h3 style="margin: 0 0 14px 0; color: #1E40AF; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
                📊 Signal Summary
            </h3>
            {strategy_section}
            {
            f'''
            <div style="margin-top: 16px; padding-top: 16px; border-top: 2px solid #DBEAFE;">
                <div style="color: #1E40AF; font-size: 15px; font-weight: 600; margin-bottom: 6px;">
                    Consolidated Signal:
                </div>
                <div style="color: #1F2937; font-size: 14px; font-weight: 500; line-height: 1.6;">
                    {consolidated_str}
                </div>
            </div>
            '''
            if consolidated_str
            else ""
        }
        </div>
        """

    @staticmethod
    def build_strategy_signals_neutral(strategy_signals: dict[Any, Any]) -> str:
        """Build strategy signals section for neutral mode (no financial data).

        Creates a summary table of strategy signals without detailed
        financial metrics. Used for quick overview emails.

        Args:
            strategy_signals: Dictionary mapping strategy names/types to signal data

        Returns:
            HTML string containing strategy signals table, or empty string
            if no signals available

        Note:
            - Handles both StrategyType enum and string keys
            - Reason text truncated to MAX_REASON_LENGTH_SUMMARY (100 chars)
            - Uses ACTION_COLORS constant for consistent styling

        """
        if not strategy_signals:
            logger.debug("build_strategy_signals_neutral_skipped", reason="no_signals")
            return ""

        logger.debug(
            "building_strategy_signals_neutral",
            signal_count=len(strategy_signals),
        )

        signal_rows = []

        for strategy_name, signal_data in strategy_signals.items():
            if not isinstance(signal_data, dict):
                logger.warning(
                    "invalid_signal_data_type",
                    strategy=str(strategy_name),
                    data_type=type(signal_data).__name__,
                )
                continue

            action = signal_data.get("action", "UNKNOWN")
            # Get symbols list and join for display
            symbols_list = signal_data.get("symbols", [])
            symbol = ", ".join(str(s) for s in symbols_list) if symbols_list else "UNKNOWN"
            reason = signal_data.get("reason", "No reason provided")

            # Convert strategy_name to string and format
            # Handle both StrategyType enum and string
            if hasattr(strategy_name, "name"):
                # It's a StrategyType enum
                strategy_display_name = strategy_name.name.upper()
            else:
                # It's already a string
                strategy_display_name = (
                    str(strategy_name).replace(_STRATEGY_TYPE_PREFIX, "").upper()
                )

            # Get colors from constant mapping
            colors = ACTION_COLORS.get(action, ACTION_COLORS["HOLD"])
            action_color = colors["text"]
            action_label = colors["label"]

            # Format decision path for table display with smart truncation
            display_reason = SignalsBuilder._format_decision_path_for_table(
                reason, MAX_REASON_LENGTH_SUMMARY
            )

            signal_rows.append(
                f"""
                <tr>
                    <td style="padding: 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;">
                        {strategy_display_name}
                    </td>
                    <td style="padding: 16px; border-bottom: 1px solid #E5E7EB; text-align: center; font-weight: 600; color: {action_color};">
                        {action_label}
                    </td>
                    <td style="padding: 16px; border-bottom: 1px solid #E5E7EB; text-align: center; font-weight: 600; color: #374151;">
                        {symbol}
                    </td>
                    <td style="padding: 16px; border-bottom: 1px solid #E5E7EB; color: #6B7280; font-size: 14px; line-height: 1.4;">
                        {display_reason}
                    </td>
                </tr>
            """
            )

        signals_table = "".join(signal_rows)

        content = f"""
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    <th style="padding: 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Strategy
                    </th>
                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Action
                    </th>
                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Target
                    </th>
                    <th style="padding: 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Analysis
                    </th>
                </tr>
            </thead>
            <tbody>
                {signals_table}
            </tbody>
        </table>
        """

        return BaseEmailTemplate.create_section("🎯 Strategy Signals", content)
