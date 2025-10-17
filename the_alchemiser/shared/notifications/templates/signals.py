"""Business Unit: shared; Status: current.

Signals content builder for email templates.

This module handles building HTML content for technical indicators,
strategy signals, and trading signal analysis.

Note:
    This module is display-only and does not perform financial calculations.
    Float comparisons use threshold values appropriate for display purposes.

"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from ...errors.exceptions import TemplateGenerationError
from ...logging import get_logger
from ...types.strategy_types import StrategyType
from .base import BaseEmailTemplate

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

            symbol = signal_data.get("symbol", "N/A")
            action = signal_data.get("action", "UNKNOWN")
            reason = signal_data.get("reason", "No reason provided")
            timestamp = signal_data.get("timestamp", "")

            # Get colors from constant mapping
            colors = ACTION_COLORS.get(action, ACTION_COLORS["HOLD"])
            action_color = colors["text"]
            action_bg = colors["background"]
            action_label = colors["label"]

            # Truncate reason text using helper method
            formatted_reason = SignalsBuilder._truncate_reason(reason, MAX_REASON_LENGTH_DETAILED)
            formatted_reason = formatted_reason.replace("\n", "<br>")

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
                    <div style="color: #4B5563; font-size: 14px; line-height: 1.5;">
                        {formatted_reason}
                    </div>
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
        strategy_rows = []
        for strategy_name, signal_data in strategy_signals.items():
            if not isinstance(signal_data, dict):
                continue

            # Format strategy name
            if hasattr(strategy_name, "name"):
                strategy_display_name = strategy_name.name.replace("_", " ").title()
            else:
                # Strip StrategyType enum prefix (e.g., "StrategyType.DSL" -> "DSL") for display
                strategy_display_name = (
                    str(strategy_name).replace(_STRATEGY_TYPE_PREFIX, "").replace("_", " ").title()
                )

            # Get target allocation for this strategy if available
            # Strategy signals may include allocation data
            symbol = signal_data.get("symbol", "")
            action = signal_data.get("action", "UNKNOWN")
            reason = signal_data.get("reason", "")

            # Build allocation string from signal
            allocation_str = f"{action}"
            if symbol:
                allocation_str += f" {symbol}"

            # Add reasoning if available (decision path explanation)
            reasoning_html = ""
            if reason:
                # Truncate reasoning for summary display
                truncated_reason = SignalsBuilder._truncate_reason(reason, MAX_REASON_LENGTH_SUMMARY)
                reasoning_html = f"""
                    <div style="margin-left: 16px; margin-top: 4px; color: #6B7280; font-size: 13px; line-height: 1.5;">
                        → {truncated_reason}
                    </div>
                """

            strategy_rows.append(
                f"""
                <div style="padding: 8px 0; color: #374151; font-size: 14px; line-height: 1.6;">
                    <strong style="color: #1F2937;">{strategy_display_name}:</strong> {allocation_str}
                    {reasoning_html}
                </div>
                """
            )

        # Build consolidated signal from portfolio
        consolidated_str = ""
        if consolidated_portfolio:
            # Sort by allocation descending with safe float conversion
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
            consolidated_str = " / ".join(allocation_parts) if allocation_parts else "No allocation"

        # Build the complete signal summary section
        strategy_section = "".join(strategy_rows) if strategy_rows else ""

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
            symbol = signal_data.get("symbol", "UNKNOWN")
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

            # Truncate reason for summary display
            display_reason = SignalsBuilder._truncate_reason(reason, MAX_REASON_LENGTH_SUMMARY)

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
