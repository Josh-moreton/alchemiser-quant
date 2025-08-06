"""Signals content builder for email templates.

This module handles building HTML content for technical indicators,
strategy signals, and trading signal analysis.
"""

from typing import Any

from .base import BaseEmailTemplate


class SignalsBuilder:
    """Builds signals-related HTML content for emails."""

    @staticmethod
    def build_signal_information(signal: Any) -> str:
        """Build HTML for signal information section.

        Args:
            signal: Signal object (Alert or StrategySignal) to display

        Returns:
            HTML string for signal information
        """
        if not signal:
            return ""

        try:
            return f"""
            <div style="margin: 24px 0; padding: 16px; background-color: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px;">
                <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 16px; font-weight: 600;">📈 Signal Information</h3>
                <p style="margin: 0; color: #92400E;">
                    <strong>{signal.action} {signal.symbol}</strong>
                    {f" - {signal.reason}" if hasattr(signal, "reason") and signal.reason else ""}
                </p>
            </div>
            """
        except Exception:
            return """
            <div style="margin: 24px 0; padding: 16px; background-color: #FEE2E2; border-left: 4px solid #EF4444; border-radius: 8px;">
                <p style="margin: 0; color: #DC2626; font-style: italic;">Error reading signal data</p>
            </div>
            """

    @staticmethod
    def build_technical_indicators(strategy_signals: dict[Any, Any]) -> str:
        """Build technical indicators HTML section."""
        if not strategy_signals:
            return BaseEmailTemplate.create_alert_box("No technical indicators available", "info")

        indicators_html = ""

        for strategy_type, signal_data in strategy_signals.items():
            technical_indicators = signal_data.get("technical_indicators", {})
            if not technical_indicators:
                continue

            strategy_name = str(strategy_type).replace("StrategyType.", "")

            indicators_rows = ""
            for symbol, indicators in technical_indicators.items():
                rsi_10 = indicators.get("rsi_10", 0)
                rsi_20 = indicators.get("rsi_20", 0)
                current_price = indicators.get("current_price", 0)
                ma_200 = indicators.get("ma_200", 0)

                # Color coding for RSI
                rsi_color = "#EF4444" if rsi_10 > 80 else "#F59E0B" if rsi_10 > 70 else "#10B981"

                # Price vs MA comparison
                price_vs_ma = "Above" if current_price > ma_200 else "Below"
                price_color = "#10B981" if current_price > ma_200 else "#EF4444"

                indicators_rows += f"""
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
            return BaseEmailTemplate.create_alert_box("No technical indicators data found", "info")

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📊 Technical Indicators</h3>
            {indicators_html}
        </div>
        """

    @staticmethod
    def build_detailed_strategy_signals(
        strategy_signals: dict[Any, Any], strategy_summary: dict[str, Any]
    ) -> str:
        """Build detailed strategy signals HTML section."""
        if not strategy_signals:
            return BaseEmailTemplate.create_alert_box("No strategy signals available", "info")

        signals_html = ""

        for strategy_type, signal_data in strategy_signals.items():
            strategy_name = str(strategy_type).replace("StrategyType.", "")

            # Get strategy summary data if available
            summary_data = strategy_summary.get(strategy_name, {})
            allocation = summary_data.get("allocation", 0)

            symbol = signal_data.get("symbol", "N/A")
            action = signal_data.get("action", "UNKNOWN")
            reason = signal_data.get("reason", "No reason provided")
            timestamp = signal_data.get("timestamp", "")

            # Determine signal styling
            if action == "BUY":
                action_color = "#10B981"
                action_bg = "#D1FAE5"
                action_emoji = "📈"
            elif action == "SELL":
                action_color = "#EF4444"
                action_bg = "#FEE2E2"
                action_emoji = "📉"
            else:
                action_color = "#6B7280"
                action_bg = "#F3F4F6"
                action_emoji = "⏸️"

            # Format reason text (truncate if too long)
            formatted_reason = reason[:300] + "..." if len(reason) > 300 else reason
            formatted_reason = formatted_reason.replace("\n", "<br>")

            signals_html += f"""
            <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 12px; border-left: 4px solid {action_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <h4 style="margin: 0; color: #1F2937; font-size: 18px; font-weight: 600;">
                            {strategy_name} Strategy
                        </h4>
                        <div style="margin-top: 4px;">
                            <span style="color: #6B7280; font-size: 14px;">Target: </span>
                            <span style="font-weight: 600; color: #1F2937;">{symbol}</span>
                            {f'<span style="color: #6B7280; font-size: 14px; margin-left: 16px;">Allocation: </span><span style="font-weight: 600; color: #1F2937;">{allocation:.1%}</span>' if allocation > 0 else ''}
                        </div>
                    </div>
                    <div style="background-color: {action_bg}; color: {action_color}; padding: 8px 16px; border-radius: 20px; font-size: 16px; font-weight: 600;">
                        {action_emoji} {action}
                    </div>
                </div>
                <div style="background-color: #F8FAFC; padding: 16px; border-radius: 8px; margin-bottom: 12px;">
                    <h5 style="margin: 0 0 8px 0; color: #374151; font-size: 14px; font-weight: 600;">Strategy Reasoning:</h5>
                    <div style="color: #4B5563; font-size: 14px; line-height: 1.5;">
                        {formatted_reason}
                    </div>
                </div>
                {f'<div style="color: #9CA3AF; font-size: 12px; text-align: right;">Generated: {timestamp}</div>' if timestamp else ''}
            </div>
            """

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">🎯 Strategy Signals</h3>
            {signals_html}
        </div>
        """

    @staticmethod
    def build_market_regime_analysis(strategy_signals: dict[Any, Any]) -> str:
        """Build market regime analysis section."""
        if not strategy_signals:
            return ""

        # Extract SPY data if available
        spy_data = None
        for signal_data in strategy_signals.values():
            technical_indicators = signal_data.get("technical_indicators", {})
            if "SPY" in technical_indicators:
                spy_data = technical_indicators["SPY"]
                break

        if not spy_data:
            return ""

        current_price = spy_data.get("current_price", 0)
        ma_200 = spy_data.get("ma_200", 0)
        rsi_10 = spy_data.get("rsi_10", 0)
        rsi_20 = spy_data.get("rsi_20", 0)

        # Determine market regime
        if current_price > ma_200:
            regime = "BULL MARKET"
            regime_color = "#10B981"
            regime_bg = "#D1FAE5"
            regime_emoji = "🐂"
        else:
            regime = "BEAR MARKET"
            regime_color = "#EF4444"
            regime_bg = "#FEE2E2"
            regime_emoji = "🐻"

        # RSI analysis
        rsi_status = ""
        if rsi_10 > 80:
            rsi_status = "Overbought"
            rsi_color = "#EF4444"
        elif rsi_10 < 20:
            rsi_status = "Oversold"
            rsi_color = "#10B981"
        else:
            rsi_status = "Neutral"
            rsi_color = "#6B7280"

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">🌊 Market Regime Analysis</h3>
            <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h4 style="margin: 0; color: #1F2937; font-size: 16px; font-weight: 600;">SPY Market Analysis</h4>
                    <div style="background-color: {regime_bg}; color: {regime_color}; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                        {regime_emoji} {regime}
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
