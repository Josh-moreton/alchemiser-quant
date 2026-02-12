"""Business Unit: notifications | Status: current.

Email template rendering for notifications.

This module provides HTML and plain text email templates with consistent branding.
Templates support variable substitution and shared partials (header/footer).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dateutil import parser as date_parser


def _format_timestamp_for_display(timestamp_str: str) -> str:
    """Format ISO 8601 timestamp as human-readable display (e.g., "1st Jan 2026 at 5:43:57pm").

    Args:
        timestamp_str: ISO 8601 formatted timestamp string or empty string.

    Returns:
        Formatted timestamp like "1st Jan 2026 at 5:43:57pm", or original input if parsing fails.

    """
    if not timestamp_str or timestamp_str == "N/A":
        return timestamp_str

    try:
        dt = date_parser.isoparse(timestamp_str)
        # Format: "1st Jan 2026 at 5:43:57pm"
        day = dt.day
        month = dt.strftime("%b")  # Jan, Feb, etc.
        year = dt.year

        # Format day with suffix (1st, 2nd, 3rd, 4th, etc.)
        if day in (1, 21, 31):
            day_suffix = "st"
        elif day in (2, 22):
            day_suffix = "nd"
        elif day in (3, 23):
            day_suffix = "rd"
        else:
            day_suffix = "th"

        # Format time with 12-hour format and am/pm
        time_str = dt.strftime("%-I:%M:%S%p").lower()  # 5:43:57pm

        return f"{day}{day_suffix} {month} {year} at {time_str}"
    except Exception:
        # If parsing fails, return original string
        return timestamp_str


def _format_pnl_html(monthly_pnl: dict[str, Any], yearly_pnl: dict[str, Any]) -> str:
    """Format P&L metrics as an HTML section.

    Supports both legacy format (monthly_pnl/yearly_pnl) and new format
    (monthly_pnl contains 'months' list for 3-month calendar display).

    Args:
        monthly_pnl: Monthly P&L data dict. Can contain:
            - Legacy: total_pnl, total_pnl_pct, period
            - New: 'months' list of dicts with period, total_pnl, total_pnl_pct
        yearly_pnl: Yearly P&L data dict with total_pnl, total_pnl_pct, period.
            Ignored if monthly_pnl contains 'months' list.

    Returns:
        HTML snippet for P&L section, or empty string if no data.

    """

    def format_pnl_value(pnl: float | None, pct: float | None) -> str:
        if pnl is None:
            return "N/A"
        sign = "+" if pnl >= 0 else ""
        color = "#28a745" if pnl >= 0 else "#dc3545"
        pct_str = f" ({sign}{pct:.2f}%)" if pct is not None else ""
        return f'<span style="color: {color};">{sign}${pnl:,.2f}{pct_str}</span>'

    # Check for new 3-month calendar format
    if monthly_pnl and "months" in monthly_pnl:
        months = monthly_pnl.get("months", [])
        if not months:
            return ""

        lines = []
        for month_data in months:
            period = month_data.get("period", "Unknown")
            pnl_str = format_pnl_value(month_data.get("total_pnl"), month_data.get("total_pnl_pct"))
            lines.append(
                f'<p style="margin: 0 0 4px 0; font-size: 11px;">'
                f"<strong>{period}:</strong> {pnl_str}</p>"
            )

        return f"""
        <div style="background-color: #e8f4f8; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">Portfolio Performance</h4>
            {"".join(lines)}
        </div>
"""

    # Legacy format: monthly + yearly
    if not monthly_pnl and not yearly_pnl:
        return ""

    monthly_str = format_pnl_value(monthly_pnl.get("total_pnl"), monthly_pnl.get("total_pnl_pct"))
    yearly_str = format_pnl_value(yearly_pnl.get("total_pnl"), yearly_pnl.get("total_pnl_pct"))

    return f"""
        <div style="background-color: #e8f4f8; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">Portfolio Performance</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Past Month:</strong> {monthly_str}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Past Year:</strong> {yearly_str}</p>
        </div>
"""


def _format_pnl_text(monthly_pnl: dict[str, Any], yearly_pnl: dict[str, Any]) -> str:
    """Format P&L metrics as a plain text section.

    Supports both legacy format (monthly_pnl/yearly_pnl) and new format
    (monthly_pnl contains 'months' list for 3-month calendar display).

    Args:
        monthly_pnl: Monthly P&L data dict. Can contain:
            - Legacy: total_pnl, total_pnl_pct, period
            - New: 'months' list of dicts with period, total_pnl, total_pnl_pct
        yearly_pnl: Yearly P&L data dict with total_pnl, total_pnl_pct, period.
            Ignored if monthly_pnl contains 'months' list.

    Returns:
        Plain text snippet for P&L section, or empty string if no data.

    """

    def format_pnl_value(pnl: float | None, pct: float | None) -> str:
        if pnl is None:
            return "N/A"
        sign = "+" if pnl >= 0 else ""
        pct_str = f" ({sign}{pct:.2f}%)" if pct is not None else ""
        return f"{sign}${pnl:,.2f}{pct_str}"

    # Check for new 3-month calendar format
    if monthly_pnl and "months" in monthly_pnl:
        months = monthly_pnl.get("months", [])
        if not months:
            return ""

        lines = ["PORTFOLIO PERFORMANCE", "-" * 21]
        for month_data in months:
            period = month_data.get("period", "Unknown")
            pnl_str = format_pnl_value(month_data.get("total_pnl"), month_data.get("total_pnl_pct"))
            lines.append(f"• {period}: {pnl_str}")

        return "\n".join(lines) + "\n"

    # Legacy format: monthly + yearly
    if not monthly_pnl and not yearly_pnl:
        return ""

    monthly_str = format_pnl_value(monthly_pnl.get("total_pnl"), monthly_pnl.get("total_pnl_pct"))
    yearly_str = format_pnl_value(yearly_pnl.get("total_pnl"), yearly_pnl.get("total_pnl_pct"))

    return f"""
PORTFOLIO PERFORMANCE
---------------------
• Past Month: {monthly_str}
• Past Year: {yearly_str}
"""


def _format_data_freshness_for_display(data_freshness: dict[str, Any]) -> tuple[str, int, str]:
    """Format data freshness info for email display.

    Handles N/A cases by showing a user-friendly message instead of raw "N/A".
    Formats ISO timestamps as readable dates.

    Args:
        data_freshness: Dict with latest_timestamp, age_days, gate_status, symbols_checked.

    Returns:
        Tuple of (formatted_latest, age_days, gate_status).
        formatted_latest: Human-readable date like "Jan 9, 2026" or descriptive message.

    """
    latest_timestamp = data_freshness.get("latest_timestamp")
    age_days = data_freshness.get("age_days", 0)
    gate_status = data_freshness.get("gate_status", "UNKNOWN")
    symbols_checked = data_freshness.get("symbols_checked", 0)

    # Handle None/missing timestamp
    if not latest_timestamp:
        if symbols_checked > 0:
            return f"No data ({symbols_checked} symbols checked)", age_days, gate_status
        return "No data available", age_days, gate_status

    # Format ISO timestamp to readable date (e.g., "Jan 9, 2026")
    try:
        dt = date_parser.isoparse(latest_timestamp)
        formatted_date = dt.strftime("%b %-d, %Y")  # Jan 9, 2026
        return formatted_date, age_days, gate_status
    except Exception:
        # If parsing fails, return original
        return str(latest_timestamp), age_days, gate_status


def _format_rebalance_plan_html(rebalance_plan_summary: list[dict[str, Any]]) -> str:
    """Format rebalance plan summary as HTML table for email display.

    Args:
        rebalance_plan_summary: List of dicts with symbol, action, weights, trade_amount.

    Returns:
        HTML snippet for rebalance plan table, or empty string if no items.

    """
    if not rebalance_plan_summary:
        return ""

    rows_html = ""
    for item in rebalance_plan_summary:
        symbol = item.get("symbol", "?")
        action = item.get("action", "?")
        current_pct = item.get("current_weight_pct", 0)
        target_pct = item.get("target_weight_pct", 0)
        trade_amount = item.get("trade_amount", 0)

        # Color coding for action
        action_color = "#28a745" if action == "BUY" else "#dc3545"

        # Format trade amount with sign
        amount_sign = "+" if trade_amount > 0 else ""
        amount_str = f"{amount_sign}${trade_amount:,.2f}"

        rows_html += f"""
                <tr>
                    <td style="padding: 4px 8px; border: 1px solid #dee2e6;">{symbol}</td>
                    <td style="padding: 4px 8px; border: 1px solid #dee2e6; color: {action_color}; font-weight: bold;">{action}</td>
                    <td style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">{current_pct:.1f}%</td>
                    <td style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">{target_pct:.1f}%</td>
                    <td style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">{amount_str}</td>
                </tr>"""

    return f"""
        <div style="background-color: #f0f8ff; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #007bff;">
            <h4 style="margin: 0 0 8px 0; color: #004085; font-size: 13px;">Rebalance Plan</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <thead>
                    <tr style="background-color: #e9ecef;">
                        <th style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: left;">Symbol</th>
                        <th style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: left;">Action</th>
                        <th style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">Current</th>
                        <th style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">Target</th>
                        <th style="padding: 4px 8px; border: 1px solid #dee2e6; text-align: right;">Trade $</th>
                    </tr>
                </thead>
                <tbody>{rows_html}
                </tbody>
            </table>
        </div>
"""


def _format_rebalance_plan_text(rebalance_plan_summary: list[dict[str, Any]]) -> str:
    """Format rebalance plan summary as plain text for email display.

    Args:
        rebalance_plan_summary: List of dicts with symbol, action, weights, trade_amount.

    Returns:
        Plain text snippet for rebalance plan, or empty string if no items.

    """
    if not rebalance_plan_summary:
        return ""

    lines = ["REBALANCE PLAN", "-" * 60]
    lines.append(f"{'Symbol':<8} {'Action':<6} {'Current':>8} {'Target':>8} {'Trade $':>12}")
    lines.append("-" * 60)

    for item in rebalance_plan_summary:
        symbol = item.get("symbol", "?")
        action = item.get("action", "?")
        current_pct = item.get("current_weight_pct", 0)
        target_pct = item.get("target_weight_pct", 0)
        trade_amount = item.get("trade_amount", 0)

        amount_sign = "+" if trade_amount > 0 else ""
        amount_str = f"{amount_sign}${trade_amount:,.2f}"

        lines.append(
            f"{symbol:<8} {action:<6} {current_pct:>7.1f}% {target_pct:>7.1f}% {amount_str:>12}"
        )

    lines.append("")
    return "\n".join(lines)


def format_subject(
    component: str,
    status: str,
    env: str,
    run_id: str,
    run_date: datetime | None = None,
    *,
    include_status: bool = True,
) -> str:
    """Format email subject line with status always present for inbox rule routing.

    Format:
      - Production: "{Component} - {STATUS}"
      - Non-production: "[DEV] {Component} - {STATUS}"

    Status is always included (SUCCESS, PARTIAL_SUCCESS, FAILURE, etc.) so that
    inbox rules can route emails based on the subject line.

    Args:
        component: Component name (e.g., "Your Daily Rebalance Summary", "Data Lake Refresh")
        status: Status (SUCCESS, PARTIAL_SUCCESS, SUCCESS_WITH_WARNINGS, FAILURE, RECOVERED)
        env: Environment (dev/staging/prod)
        run_id: Unused; retained for backward compatibility
        run_date: Unused; retained for backward compatibility
        include_status: Whether to include status in subject line (default: True)

    Returns:
        Formatted subject line

    """
    # Capitalize component for consistency
    component_title = component.title()

    # Always include status for inbox rule routing
    status_suffix = f" - {status}" if include_status else ""

    # Production emails have no environment prefix
    if env == "prod":
        return f"{component_title}{status_suffix}"

    # Non-production emails get environment prefix
    env_prefix = f"[{env.upper()}]"
    return f"{env_prefix} {component_title}{status_suffix}"


def render_html_header(component: str, status: str) -> str:
    """Render HTML email header with branding.

    Args:
        component: Component name
        status: Status for color coding

    Returns:
        HTML header snippet

    """
    # Color coding by status
    status_colors = {
        "SUCCESS": "#28a745",
        "SUCCESS_WITH_WARNINGS": "#ffc107",
        "PARTIAL_SUCCESS": "#ffc107",
        "WARNING": "#fd7e14",
        "FAILURE": "#dc3545",
        "RECOVERED": "#17a2b8",
    }
    color = status_colors.get(status, "#6c757d")

    # Logo hosted on GitHub (raw URL for direct image access)
    logo_url = "https://raw.githubusercontent.com/Josh-moreton/alchemiser-quant/main/logo.png"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{component} - {status}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.5; color: #333; max-width: 700px; margin: 0 auto; padding: 15px; font-size: 13px;">
    <div style="padding: 15px 0; border-bottom: 2px solid #e9ecef; text-align: center; margin-bottom: 15px;">
        <img src="{logo_url}" alt="Octarine Capital" style="width: 120px; height: auto; margin-bottom: 8px;">
    </div>
    <div style="background-color: {color}; color: white; padding: 10px; text-align: center; font-size: 14px; font-weight: bold; border-radius: 4px;">
        {status}
    </div>
"""


def render_html_footer() -> str:
    """Render HTML email footer.

    Returns:
        HTML footer snippet

    """
    return """
    <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #e9ecef; text-align: center; color: #6c757d; font-size: 11px;">
        <p style="margin: 0;">Octarine Capital Quantitative Trading System</p>
        <p style="margin: 3px 0 0 0;">Automated notification - do not reply</p>
    </div>
</body>
</html>
"""


def render_text_header(component: str, status: str) -> str:
    """Render plain text email header.

    Args:
        component: Component name
        status: Status

    Returns:
        Plain text header

    """
    return f"""
{"=" * 80}
Status: {status}
"""


def render_text_footer() -> str:
    """Render plain text email footer.

    Returns:
        Plain text footer

    """
    return f"""
{"-" * 80}
Octarine Capital Quantitative Trading System
Automated notification - do not reply
{"-" * 80}
"""


def render_daily_run_success_html(context: dict[str, Any]) -> str:
    """Render HTML for Daily Run SUCCESS email.

    Args:
        context: Template context with run data

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Daily Run", context["status"])
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Identity & Timing</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="padding: 3px;"><strong>Env:</strong></td><td style="padding: 3px;">{env}</td>
                    <td style="padding: 3px;"><strong>Mode:</strong></td><td style="padding: 3px;">{mode}</td></tr>
                <tr><td style="padding: 3px;"><strong>Run ID:</strong></td><td colspan="3" style="padding: 3px;">{run_id}</td></tr>
                <tr><td style="padding: 3px;"><strong>Started:</strong></td><td colspan="3" style="padding: 3px;">{start_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 3px;">{end_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 3px;">{duration}s</td></tr>
            </table>
        </div>

        <div style="background-color: #e7f5e9; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #28a745;">
            <h4 style="margin: 0 0 8px 0; color: #155724; font-size: 13px;">Outcome Summary</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Strategies evaluated:</strong> {strategies_evaluated} | <strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Exposure:</strong> {gross_exposure:.2f}x</p>
            <p style="margin: 0; font-size: 11px;"><strong>Top positions:</strong></p>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 11px;">
"""

    for pos in top_positions[:3]:
        body += f"                <li>{pos['symbol']} {pos['weight']:.1f}%</li>\n"

    if not top_positions:
        body += "                <li>No positions</li>\n"

    body += """
            </ul>
        </div>
"""

    # Add P&L section if data available
    body += _format_pnl_html(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_html(rebalance_plan_summary)

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> {latest_candle} (age {candle_age})
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Warnings</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 11px;">
"""
        for warning in warnings:
            body += f"                <li>{warning}</li>\n"
        body += """
            </ul>
        </div>
"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Links</h4>
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_daily_run_success_text(context: dict[str, Any]) -> str:
    """Render plain text for Daily Run SUCCESS email.

    Args:
        context: Template context with run data

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Daily Run", context["status"])
    footer = render_text_footer()

    # Extract context values (same as HTML version)
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode} | Run ID: {run_id}
Time: {start_time} → {end_time} ({duration}s)

SUMMARY
-------
• Strategies evaluated: {strategies_evaluated} | Symbols evaluated: {symbols_evaluated}
• Eligible: {eligible} | Blocked by risk: {blocked}
• Orders: placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}

PORTFOLIO SNAPSHOT (POST-RUN)
------------------------------
• Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
• Exposure: {gross_exposure:.2f}x
• Top positions:
"""

    for pos in top_positions[:3]:
        body += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"

    if not top_positions:
        body += "  - No positions\n"

    # Add P&L section if data available
    body += _format_pnl_text(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_text(rebalance_plan_summary)

    body += f"""
DATA FRESHNESS USED
-------------------
• Daily candles: {latest_candle} (age {candle_age}) DATA_FRESHNESS_GATE={freshness_gate}
"""

    if warnings:
        body += "\nWARNINGS\n--------\n"
        for warning in warnings:
            body += f"• {warning}\n"

    body += f"""
LINKS
-----
• Logs: {logs_url}
"""

    return header + body + footer


def render_daily_run_partial_success_html(context: dict[str, Any]) -> str:
    """Render HTML for Daily Run PARTIAL_SUCCESS email.

    Used when trades execute successfully but some positions were skipped
    due to non-fractionable assets with quantity rounding to zero.

    Args:
        context: Template context with run data including skipped_symbols

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Daily Run", "PARTIAL_SUCCESS")
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Partial success specific
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Identity & Timing</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="padding: 3px;"><strong>Env:</strong></td><td style="padding: 3px;">{env}</td>
                    <td style="padding: 3px;"><strong>Mode:</strong></td><td style="padding: 3px;">{mode}</td></tr>
                <tr><td style="padding: 3px;"><strong>Run ID:</strong></td><td colspan="3" style="padding: 3px;">{run_id}</td></tr>
                <tr><td style="padding: 3px;"><strong>Started:</strong></td><td colspan="3" style="padding: 3px;">{start_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 3px;">{end_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 3px;">{duration}s</td></tr>
            </table>
        </div>

        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Partial Success</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;">Most trades executed successfully, but some positions were skipped due to non-fractionable assets.</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Strategies evaluated:</strong> {strategies_evaluated} | <strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Skipped Positions (Non-Fractionable)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;">The following symbols were skipped because they don't support fractional shares and the target quantity rounded to zero:</p>
            <ul style="margin: 4px 0 8px 0; padding-left: 20px; font-size: 11px;">
"""

    for symbol in non_fractionable_skipped:
        body += f"                <li><strong>{symbol}</strong></li>\n"

    if not non_fractionable_skipped:
        body += "                <li>None</li>\n"

    body += """
            </ul>
            <p style="font-style: italic; color: #856404; margin: 0; font-size: 11px;">
                <strong>Note:</strong> Consider increasing your total portfolio value or adjusting strategy weights to ensure these assets meet the minimum 1-share threshold.
            </p>
        </div>

"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Exposure:</strong> {gross_exposure:.2f}x</p>
            <p style="margin: 0; font-size: 11px;"><strong>Top positions:</strong></p>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 11px;">
"""

    for pos in top_positions[:3]:
        body += f"                <li>{pos['symbol']} {pos['weight']:.1f}%</li>\n"

    if not top_positions:
        body += "                <li>No positions</li>\n"

    body += """
            </ul>
        </div>
"""

    # Add P&L section if data available
    body += _format_pnl_html(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_html(rebalance_plan_summary)

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> {latest_candle} (age {candle_age})
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Warnings</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 11px;">
"""
        for warning in warnings:
            body += f"                <li>{warning}</li>\n"
        body += """
            </ul>
        </div>
"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Links</h4>
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_daily_run_partial_success_text(context: dict[str, Any]) -> str:
    """Render plain text for Daily Run PARTIAL_SUCCESS email.

    Used when trades execute successfully but some positions were skipped
    due to non-fractionable assets with quantity rounding to zero.

    Args:
        context: Template context with run data including skipped_symbols

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Daily Run", "PARTIAL_SUCCESS")
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Partial success specific
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode} | Run ID: {run_id}
Time: {start_time} → {end_time} ({duration}s)

PARTIAL SUCCESS
---------------
Most trades executed successfully, but some positions were skipped.

SUMMARY
-------
• Strategies evaluated: {strategies_evaluated} | Symbols evaluated: {symbols_evaluated}
• Eligible: {eligible} | Blocked by risk: {blocked}
• Orders: placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}

SKIPPED POSITIONS (NON-FRACTIONABLE)
------------------------------------
The following symbols were skipped because they don't support fractional shares
and the target quantity rounded to zero:
"""

    for symbol in non_fractionable_skipped:
        body += f"  • {symbol}\n"

    if not non_fractionable_skipped:
        body += "  • None\n"

    body += """
Note: Consider increasing your total portfolio value or adjusting strategy
      weights to ensure these assets meet the minimum 1-share threshold.

"""

    body += f"""PORTFOLIO SNAPSHOT (POST-RUN)
------------------------------
• Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
• Exposure: {gross_exposure:.2f}x
• Top positions:
"""

    for pos in top_positions[:3]:
        body += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"

    if not top_positions:
        body += "  - No positions\n"

    # Add P&L section if data available
    body += _format_pnl_text(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_text(rebalance_plan_summary)

    body += f"""
DATA FRESHNESS USED
-------------------
• Daily candles: {latest_candle} (age {candle_age}) DATA_FRESHNESS_GATE={freshness_gate}
"""

    if warnings:
        body += "\nWARNINGS\n--------\n"
        for warning in warnings:
            body += f"• {warning}\n"

    body += f"""
LINKS
-----
• Logs: {logs_url}
"""

    return header + body + footer


def render_daily_run_partial_success_with_failures_html(context: dict[str, Any]) -> str:
    """Render HTML for Daily Run PARTIAL_SUCCESS email with actual failures.

    Used when some trades fail but the failure rate is below the threshold (30%).
    This template shows both the successful execution summary AND the failure details,
    so users don't lose visibility into what succeeded.

    Args:
        context: Template context with run data including failed_symbols

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Daily Run", "PARTIAL_SUCCESS")
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Failure details
    failed_symbols = context.get("failed_symbols", [])
    failure_rate = context.get("failure_rate", 0)
    error_message = context.get("exception_message", "Trade execution failed")

    # Non-fractionable skips (may also be present)
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Identity & Timing</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="padding: 3px;"><strong>Env:</strong></td><td style="padding: 3px;">{env}</td>
                    <td style="padding: 3px;"><strong>Mode:</strong></td><td style="padding: 3px;">{mode}</td></tr>
                <tr><td style="padding: 3px;"><strong>Run ID:</strong></td><td colspan="3" style="padding: 3px;">{run_id}</td></tr>
                <tr><td style="padding: 3px;"><strong>Started:</strong></td><td colspan="3" style="padding: 3px;">{start_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 3px;">{end_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 3px;">{duration}s</td></tr>
            </table>
        </div>

        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Partial Success - {orders_filled}/{orders_placed} Trades Executed</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;">Most trades executed successfully. <strong>{len(failed_symbols)}</strong> trade(s) failed ({failure_rate:.1%} failure rate).</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Strategies evaluated:</strong> {strategies_evaluated} | <strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #f8d7da; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #dc3545;">
            <h4 style="margin: 0 0 8px 0; color: #721c24; font-size: 13px;">Failed Trades ({len(failed_symbols)})</h4>
            <ul style="margin: 4px 0 8px 0; padding-left: 20px; font-size: 11px;">
"""

    for symbol in failed_symbols:
        body += f"                <li><strong>{symbol}</strong></li>\n"

    if not failed_symbols:
        body += "                <li>None</li>\n"

    body += f"""
            </ul>
            <p style="margin: 0; font-size: 11px;"><strong>Error:</strong> {error_message}</p>
        </div>
"""

    # Add non-fractionable skips section if any
    if non_fractionable_skipped:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Skipped Positions (Non-Fractionable)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;">The following symbols were skipped because they don't support fractional shares and the target quantity rounded to zero:</p>
            <ul style="margin: 4px 0 8px 0; padding-left: 20px; font-size: 11px;">
"""
        for symbol in non_fractionable_skipped:
            body += f"                <li><strong>{symbol}</strong></li>\n"
        body += """
            </ul>
        </div>
"""

    body += f"""
        <div style="background-color: #e7f5e9; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #28a745;">
            <h4 style="margin: 0 0 8px 0; color: #155724; font-size: 13px;">Successful Execution Summary</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>{orders_filled} trades executed successfully</strong></p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Exposure:</strong> {gross_exposure:.2f}x</p>
            <p style="margin: 0; font-size: 11px;"><strong>Top positions:</strong></p>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 11px;">
"""

    for pos in top_positions[:3]:
        body += f"                <li>{pos['symbol']} {pos['weight']:.1f}%</li>\n"

    if not top_positions:
        body += "                <li>No positions</li>\n"

    body += """
            </ul>
        </div>
"""

    # Add P&L section if data available
    body += _format_pnl_html(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_html(rebalance_plan_summary)

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> {latest_candle} (age {candle_age})
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>

        <div style="background-color: #d1ecf1; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">Quick Actions</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 11px;">
                <li>Check Alpaca account status and buying power</li>
                <li>Verify the failed symbol(s) are tradeable on Alpaca</li>
                <li>Review order rejection reasons in trade ledger</li>
            </ul>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Warnings</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 11px;">
"""
        for warning in warnings:
            body += f"                <li>{warning}</li>\n"
        body += """
            </ul>
        </div>
"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Links</h4>
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_daily_run_partial_success_with_failures_text(context: dict[str, Any]) -> str:
    """Render plain text for Daily Run PARTIAL_SUCCESS email with actual failures.

    Used when some trades fail but the failure rate is below the threshold (30%).
    This template shows both the successful execution summary AND the failure details.

    Args:
        context: Template context with run data including failed_symbols

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Daily Run", "PARTIAL_SUCCESS")
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    mode = context.get("mode", "PAPER")
    run_id = context.get("run_id", "unknown")

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)

    strategies_evaluated = context.get("strategies_evaluated", 0)
    symbols_evaluated = context.get("symbols_evaluated", 0)
    eligible = context.get("eligible_signals_count", 0)
    blocked = context.get("blocked_by_risk_count", 0)

    orders_placed = context.get("orders_placed", 0)
    orders_filled = context.get("orders_filled", 0)
    orders_cancelled = context.get("orders_cancelled", 0)
    orders_rejected = context.get("orders_rejected", 0)

    equity = context.get("equity", 0)
    cash = context.get("cash", 0)
    gross_exposure = context.get("gross_exposure", 0)
    top_positions = context.get("top_positions", [])

    # Use helper to format data freshness nicely
    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    # Failure details
    failed_symbols = context.get("failed_symbols", [])
    failure_rate = context.get("failure_rate", 0)
    error_message = context.get("exception_message", "Trade execution failed")

    # Non-fractionable skips
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    # Rebalance plan for display
    rebalance_plan_summary = context.get("rebalance_plan_summary", [])

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode} | Run ID: {run_id}
Time: {start_time} → {end_time} ({duration}s)

PARTIAL SUCCESS - {orders_filled}/{orders_placed} TRADES EXECUTED
{"=" * 50}
Most trades executed successfully. {len(failed_symbols)} trade(s) failed ({failure_rate:.1%} failure rate).

SUMMARY
-------
• Strategies evaluated: {strategies_evaluated} | Symbols evaluated: {symbols_evaluated}
• Eligible: {eligible} | Blocked by risk: {blocked}
• Orders: placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}

FAILED TRADES ({len(failed_symbols)})
{"=" * 30}
"""

    for symbol in failed_symbols:
        body += f"  • {symbol}\n"

    if not failed_symbols:
        body += "  • None\n"

    body += f"""
Error: {error_message}
"""

    # Add non-fractionable skips section if any
    if non_fractionable_skipped:
        body += """
SKIPPED POSITIONS (NON-FRACTIONABLE)
------------------------------------
The following symbols were skipped (non-fractionable, quantity rounded to zero):
"""
        for symbol in non_fractionable_skipped:
            body += f"  • {symbol}\n"

    body += f"""
SUCCESSFUL EXECUTION SUMMARY
----------------------------
• {orders_filled} trades executed successfully

PORTFOLIO SNAPSHOT (POST-RUN)
------------------------------
• Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
• Exposure: {gross_exposure:.2f}x
• Top positions:
"""

    for pos in top_positions[:3]:
        body += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"

    if not top_positions:
        body += "  - No positions\n"

    # Add P&L section if data available
    body += _format_pnl_text(monthly_pnl, yearly_pnl)

    # Add Rebalance Plan section if data available
    body += _format_rebalance_plan_text(rebalance_plan_summary)

    body += f"""
DATA FRESHNESS USED
-------------------
• Daily candles: {latest_candle} (age {candle_age}) DATA_FRESHNESS_GATE={freshness_gate}

QUICK ACTIONS
-------------
• Check Alpaca account status and buying power
• Verify the failed symbol(s) are tradeable on Alpaca
• Review order rejection reasons in trade ledger
"""

    if warnings:
        body += "\nWARNINGS\n--------\n"
        for warning in warnings:
            body += f"• {warning}\n"

    body += f"""
LINKS
-----
• Logs: {logs_url}
"""

    return header + body + footer


def render_daily_run_failure_html(context: dict[str, Any]) -> str:
    """Render HTML for Daily Run FAILURE email.

    Args:
        context: Template context with failure data

    Returns:
        Complete HTML email body

    """
    header = render_html_header(
        context.get("component", "Daily Run"),
        context.get("status", "FAILURE"),
    )
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    failed_step = context.get("failed_step", "unknown")
    impact = context.get("impact", "Unknown impact")

    exception_type = context.get("exception_type", "Unknown")
    exception_message = context.get("exception_message", "No details available")
    stack_trace = context.get("stack_trace", "")[:2000]  # Truncate long traces

    retry_attempts = context.get("retry_attempts", 0)
    last_attempt_time = _format_timestamp_for_display(context.get("last_attempt_time_utc", ""))

    last_successful_run = context.get("last_successful_run_id", "N/A")
    last_successful_time = _format_timestamp_for_display(
        context.get("last_successful_run_time_utc", "N/A")
    )

    quick_actions = context.get("quick_actions", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8d7da; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #dc3545;">
            <h4 style="margin: 0 0 8px 0; color: #721c24; font-size: 11px;">What Failed + Impact</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Failed Step:</strong> {failed_step}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Impact:</strong> {impact}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 11px;">Error Signature</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Exception Type:</strong> {exception_type}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Message:</strong> {exception_message}</p>
            <pre style="background-color: #e9ecef; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 10px; margin: 4px 0 0 0;">{stack_trace}</pre>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 11px;">Context</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Env:</strong> {env} | <strong>Run ID:</strong> {run_id}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Retry attempts:</strong> {retry_attempts} | <strong>Last attempt:</strong> {last_attempt_time}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Last successful run:</strong> {last_successful_run} at {last_successful_time}</p>
        </div>

        <div style="background-color: #d1ecf1; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 11px;">Quick Actions</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 11px;">
"""

    for action in quick_actions[:5]:
        body += f"                <li>{action}</li>\n"

    if not quick_actions:
        body += "                <li>Check logs for detailed error information</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 11px;">Links</h4>
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs (filtered by run_id)</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_daily_run_failure_text(context: dict[str, Any]) -> str:
    """Render plain text for Daily Run FAILURE email.

    Args:
        context: Template context with failure data

    Returns:
        Complete plain text email body

    """
    header = render_text_header(
        context.get("component", "Daily Run"),
        context.get("status", "FAILURE"),
    )
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    failed_step = context.get("failed_step", "unknown")
    impact = context.get("impact", "Unknown impact")

    exception_type = context.get("exception_type", "Unknown")
    exception_message = context.get("exception_message", "No details available")
    stack_trace = context.get("stack_trace", "")[:2000]

    retry_attempts = context.get("retry_attempts", 0)
    last_attempt_time = _format_timestamp_for_display(context.get("last_attempt_time_utc", ""))

    last_successful_run = context.get("last_successful_run_id", "N/A")
    last_successful_time = _format_timestamp_for_display(
        context.get("last_successful_run_time_utc", "N/A")
    )

    quick_actions = context.get("quick_actions", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
WHAT FAILED + IMPACT
--------------------
Failed Step: {failed_step}
Impact: {impact}

ERROR SIGNATURE
---------------
Exception Type: {exception_type}
Message: {exception_message}

Stack Trace:
{stack_trace}

CONTEXT
-------
Env: {env} | Run ID: {run_id}
Retry attempts: {retry_attempts} | Last attempt: {last_attempt_time}
Last successful run: {last_successful_run} at {last_successful_time}

QUICK ACTIONS
-------------
"""

    for action in quick_actions[:5]:
        body += f"• {action}\n"

    if not quick_actions:
        body += "• Check logs for detailed error information\n"

    body += f"""
LINKS
-----
• Logs (filtered by run_id): {logs_url}
"""

    return header + body + footer


def render_data_lake_success_html(context: dict[str, Any]) -> str:
    """Render HTML for Data Lake Update SUCCESS email.

    Args:
        context: Template context with update data

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Data Lake Update", "SUCCESS")
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    symbols_updated = context.get("symbols_updated", [])
    symbols_updated_count = context.get("symbols_updated_count", 0)
    total_bars_fetched = context.get("total_bars_fetched", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    # Adjustment data (NEW)
    symbols_adjusted = context.get("symbols_adjusted", [])
    adjustment_count = context.get("adjustment_count", 0)
    adjusted_dates_by_symbol = context.get("adjusted_dates_by_symbol", {})

    body = f"""
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Identity & Timing</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px;"><strong>Env:</strong></td><td style="padding: 5px;">{env}</td>
                    <td style="padding: 5px;"><strong>Run ID:</strong></td><td style="padding: 5px;">{run_id}</td></tr>
                <tr><td style="padding: 5px;"><strong>Started:</strong></td><td colspan="3" style="padding: 5px;">{start_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 5px;">{end_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 5px;">{duration:.1f}s</td></tr>
            </table>
        </div>

        <div style="background-color: #e7f5e9; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0; color: #155724;">Data Refresh Summary</h3>
            <p><strong>Total symbols processed:</strong> {total_symbols}</p>
            <p><strong>Successfully updated:</strong> {symbols_updated_count}</p>
            <p><strong>Total bars fetched:</strong> {total_bars_fetched}</p>
            <p><strong>Data source:</strong> {data_source}</p>
        </div>
"""

    # Add adjustment section if adjustments detected (NEW)
    if symbols_adjusted:
        body += f"""
        <div style="background-color: #fff3cd; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #856404;">Price Adjustments Detected</h3>
            <p><strong>{len(symbols_adjusted)} symbol(s)</strong> had retroactive price adjustments (splits, dividends, etc.).</p>
            <p><strong>Total bars adjusted:</strong> {adjustment_count}</p>
            <div style="margin-top: 10px;">
                <strong>Affected symbols:</strong>
                <ul style="margin-top: 5px;">
"""
        for symbol in sorted(symbols_adjusted):
            dates = adjusted_dates_by_symbol.get(symbol, [])
            date_count = len(dates)
            date_sample = ", ".join(dates[:3]) if dates else "N/A"
            if date_count > 3:
                date_sample += f" ... ({date_count - 3} more)"
            body += f"                    <li><strong>{symbol}</strong>: {date_count} bar(s) adjusted ({date_sample})</li>\n"

        body += """
                </ul>
            </div>
            <p style="font-style: italic; color: #856404; margin-top: 10px;">
                Historical data has been updated with adjusted prices. All indicators and backtests will now use consistent pricing.
            </p>
        </div>
"""

    body += """
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Updated Symbols</h3>
            <ul style="margin-top: 5px; column-count: 3; column-gap: 20px;">
"""

    for symbol in symbols_updated:
        body += f"                <li>{symbol}</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #495057;">Links</h3>
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_data_lake_success_text(context: dict[str, Any]) -> str:
    """Render plain text for Data Lake Update SUCCESS email.

    Args:
        context: Template context with update data

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Data Lake Update", "SUCCESS")
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    symbols_updated = context.get("symbols_updated", [])
    symbols_updated_count = context.get("symbols_updated_count", 0)
    total_bars_fetched = context.get("total_bars_fetched", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    # Adjustment data (NEW)
    symbols_adjusted = context.get("symbols_adjusted", [])
    adjustment_count = context.get("adjustment_count", 0)
    adjusted_dates_by_symbol = context.get("adjusted_dates_by_symbol", {})

    body = f"""
Env: {env} | Run: {run_id}
Time: {start_time} → {end_time} ({duration:.1f}s)

DATA REFRESH SUMMARY
--------------------
• Total symbols processed: {total_symbols}
• Successfully updated: {symbols_updated_count}
• Total bars fetched: {total_bars_fetched}
• Data source: {data_source}
"""

    # Add adjustment section if adjustments detected (NEW)
    if symbols_adjusted:
        body += f"""
PRICE ADJUSTMENTS DETECTED
--------------------------
{len(symbols_adjusted)} symbol(s) had retroactive price adjustments (splits, dividends).
Total bars adjusted: {adjustment_count}

Affected symbols:
"""
        for symbol in sorted(symbols_adjusted):
            dates = adjusted_dates_by_symbol.get(symbol, [])
            date_count = len(dates)
            date_sample = ", ".join(dates[:3]) if dates else "N/A"
            if date_count > 3:
                date_sample += f" ... ({date_count - 3} more)"
            body += f"  • {symbol}: {date_count} bar(s) adjusted ({date_sample})\n"

        body += """
(i) Historical data has been updated with adjusted prices. All indicators
    and backtests will now use consistent pricing.
"""

    body += f"""
UPDATED SYMBOLS
---------------
{", ".join(symbols_updated)}

LINKS
-----
• Logs: {logs_url}
"""

    return header + body + footer


def render_data_lake_partial_html(context: dict[str, Any]) -> str:
    """Render HTML for Data Lake Update SUCCESS_WITH_WARNINGS email (partial success).

    Args:
        context: Template context with update data

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Data Lake Update", "SUCCESS_WITH_WARNINGS")
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    symbols_updated = context.get("symbols_updated", [])
    failed_symbols = context.get("failed_symbols", [])
    symbols_updated_count = context.get("symbols_updated_count", 0)
    symbols_failed_count = context.get("symbols_failed_count", 0)
    total_bars_fetched = context.get("total_bars_fetched", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    # Adjustment data (NEW)
    symbols_adjusted = context.get("symbols_adjusted", [])
    adjustment_count = context.get("adjustment_count", 0)
    adjusted_dates_by_symbol = context.get("adjusted_dates_by_symbol", {})

    body = f"""
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Identity & Timing</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px;"><strong>Env:</strong></td><td style="padding: 5px;">{env}</td>
                    <td style="padding: 5px;"><strong>Run ID:</strong></td><td style="padding: 5px;">{run_id}</td></tr>
                <tr><td style="padding: 5px;"><strong>Started:</strong></td><td colspan="3" style="padding: 5px;">{start_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 5px;">{end_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 5px;">{duration:.1f}s</td></tr>
            </table>
        </div>

        <div style="background-color: #fff3cd; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #856404;">Partial Success</h3>
            <p><strong>Total symbols processed:</strong> {total_symbols}</p>
            <p><strong>Successfully updated:</strong> {symbols_updated_count}</p>
            <p><strong>Failed:</strong> {symbols_failed_count}</p>
            <p><strong>Total bars fetched:</strong> {total_bars_fetched}</p>
            <p><strong>Data source:</strong> {data_source}</p>
        </div>

        <div style="background-color: #f8d7da; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #dc3545;">
            <h3 style="margin-top: 0; color: #721c24;">Failed Symbols</h3>
            <p>{", ".join(failed_symbols) if failed_symbols else "None"}</p>
        </div>
"""

    # Add adjustment section if adjustments detected (NEW)
    if symbols_adjusted:
        body += f"""
        <div style="background-color: #d1ecf1; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #17a2b8;">
            <h3 style="margin-top: 0; color: #0c5460;">Price Adjustments Detected</h3>
            <p><strong>{len(symbols_adjusted)} symbol(s)</strong> had retroactive price adjustments (splits, dividends, etc.).</p>
            <p><strong>Total bars adjusted:</strong> {adjustment_count}</p>
            <div style="margin-top: 10px;">
                <strong>Affected symbols:</strong>
                <ul style="margin-top: 5px;">
"""
        for symbol in sorted(symbols_adjusted):
            dates = adjusted_dates_by_symbol.get(symbol, [])
            date_count = len(dates)
            date_sample = ", ".join(dates[:3]) if dates else "N/A"
            if date_count > 3:
                date_sample += f" ... ({date_count - 3} more)"
            body += f"                    <li><strong>{symbol}</strong>: {date_count} bar(s) adjusted ({date_sample})</li>\n"

        body += """
                </ul>
            </div>
            <p style="font-style: italic; color: #0c5460; margin-top: 10px;">
                Historical data has been updated with adjusted prices for these symbols.
            </p>
        </div>
"""

    body += """
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Successfully Updated Symbols</h3>
            <ul style="margin-top: 5px; column-count: 3; column-gap: 20px;">
"""

    for symbol in symbols_updated:
        body += f"                <li>{symbol}</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #495057;">Links</h3>
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_data_lake_partial_text(context: dict[str, Any]) -> str:
    """Render plain text for Data Lake Update SUCCESS_WITH_WARNINGS email.

    Args:
        context: Template context with update data

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Data Lake Update", "SUCCESS_WITH_WARNINGS")
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    symbols_updated = context.get("symbols_updated", [])
    failed_symbols = context.get("failed_symbols", [])
    symbols_updated_count = context.get("symbols_updated_count", 0)
    symbols_failed_count = context.get("symbols_failed_count", 0)
    total_bars_fetched = context.get("total_bars_fetched", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Run: {run_id}
Time: {start_time} → {end_time} ({duration:.1f}s)

PARTIAL SUCCESS
---------------
• Total symbols processed: {total_symbols}
• Successfully updated: {symbols_updated_count}
• Failed: {symbols_failed_count}
• Total bars fetched: {total_bars_fetched}
• Data source: {data_source}

FAILED SYMBOLS
--------------
{", ".join(failed_symbols) if failed_symbols else "None"}

SUCCESSFULLY UPDATED SYMBOLS
-----------------------------
{", ".join(symbols_updated)}

LINKS
-----
• Logs: {logs_url}
"""

    return header + body + footer


def render_data_lake_failure_html(context: dict[str, Any]) -> str:
    """Render HTML for Data Lake Update FAILURE email.

    Args:
        context: Template context with failure data

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Data Lake Update", "FAILURE")
    footer = render_html_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    failed_symbols = context.get("failed_symbols", [])
    symbols_failed_count = context.get("symbols_failed_count", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    error_message = context.get("error_message", "Data refresh failed")
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Identity & Timing</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px;"><strong>Env:</strong></td><td style="padding: 5px;">{env}</td>
                    <td style="padding: 5px;"><strong>Run ID:</strong></td><td style="padding: 5px;">{run_id}</td></tr>
                <tr><td style="padding: 5px;"><strong>Started:</strong></td><td colspan="3" style="padding: 5px;">{start_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 5px;">{end_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 5px;">{duration:.1f}s</td></tr>
            </table>
        </div>

        <div style="background-color: #f8d7da; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #dc3545;">
            <h3 style="margin-top: 0; color: #721c24;">Data Refresh Failed</h3>
            <p><strong>Total symbols processed:</strong> {total_symbols}</p>
            <p><strong>All failed:</strong> {symbols_failed_count}</p>
            <p><strong>Data source:</strong> {data_source}</p>
            <p><strong>Error:</strong> {error_message}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Failed Symbols</h3>
            <ul style="margin-top: 5px; column-count: 3; column-gap: 20px;">
"""

    for symbol in failed_symbols:
        body += f"                <li>{symbol}</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #d1ecf1; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #17a2b8;">
            <h3 style="margin-top: 0; color: #0c5460;">Quick Actions</h3>
            <ul style="margin-bottom: 0;">
                <li>Check CloudWatch Logs for detailed error traces</li>
                <li>Verify Alpaca API connectivity and rate limits</li>
                <li>Check if market data is available for these symbols</li>
                <li>Review S3 bucket permissions and quotas</li>
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #495057;">Links</h3>
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs (filtered by run_id)</a></p>
        </div>
    </div>
"""

    return header + body + footer


def render_data_lake_failure_text(context: dict[str, Any]) -> str:
    """Render plain text for Data Lake Update FAILURE email.

    Args:
        context: Template context with failure data

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Data Lake Update", "FAILURE")
    footer = render_text_footer()

    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    total_symbols = context.get("total_symbols", 0)
    failed_symbols = context.get("failed_symbols", [])
    symbols_failed_count = context.get("symbols_failed_count", 0)
    data_source = context.get("data_source", "alpaca_api")
    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))
    duration = context.get("duration_seconds", 0)
    error_message = context.get("error_message", "Data refresh failed")
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Run: {run_id}
Time: {start_time} → {end_time} ({duration:.1f}s)

DATA REFRESH FAILED
-------------------
• Total symbols processed: {total_symbols}
• All failed: {symbols_failed_count}
• Data source: {data_source}
• Error: {error_message}

FAILED SYMBOLS
--------------
{", ".join(failed_symbols)}

QUICK ACTIONS
-------------
• Check CloudWatch Logs for detailed error traces
• Verify Alpaca API connectivity and rate limits
• Check if market data is available for these symbols
• Review S3 bucket permissions and quotas

LINKS
-----
• Logs (filtered by run_id): {logs_url}
"""

    return header + body + footer


# Public API
__all__ = [
    "format_subject",
    "render_daily_run_failure_html",
    "render_daily_run_failure_text",
    "render_daily_run_partial_success_html",
    "render_daily_run_partial_success_text",
    "render_daily_run_partial_success_with_failures_html",
    "render_daily_run_partial_success_with_failures_text",
    "render_daily_run_success_html",
    "render_daily_run_success_text",
    "render_schedule_created_html",
    "render_schedule_created_text",
]


def render_schedule_created_html(context: dict[str, Any]) -> str:
    """Render HTML for Schedule Created notification email.

    Handles three scenarios:
    - 'scheduled': Normal trading day schedule created
    - 'early_close': Early close day (e.g., day before holidays)
    - 'skipped_holiday': Market closed for holiday

    Args:
        context: Template context with schedule data

    Returns:
        Complete HTML email body

    """
    status = context.get("status", "scheduled")
    env = context.get("env", "unknown")
    date = context.get("date", "unknown")

    # Determine display status and component name
    if status == "skipped_holiday":
        display_status = "MARKET CLOSED"
        component = "Schedule Skip"
    elif status == "early_close":
        display_status = "EARLY CLOSE"
        component = "Schedule Set"
    else:
        display_status = "SCHEDULED"
        component = "Schedule Set"

    header = render_html_header(component, display_status)
    footer = render_html_footer()

    execution_time = context.get("execution_time", "")
    market_close_time = context.get("market_close_time", "")
    schedule_name = context.get("schedule_name", "")
    skip_reason = context.get("skip_reason", "")

    # Format times for display
    exec_display = _format_timestamp_for_display(execution_time) if execution_time else "N/A"
    close_display = _format_timestamp_for_display(market_close_time) if market_close_time else "N/A"

    if status == "skipped_holiday":
        body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Market Closed</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Date:</strong> {date}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Reason:</strong> {skip_reason or "Holiday"}</p>
            <p style="margin: 0; font-size: 11px; font-style: italic;">No trading schedule created. Normal operations will resume on the next trading day.</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Environment</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Env:</strong> {env}</p>
        </div>
    </div>
"""
    elif status == "early_close":
        body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #d1ecf1; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">Early Close Day</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Date:</strong> {date}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Market Close:</strong> {close_display} (early)</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Execution Time:</strong> {exec_display}</p>
            <p style="margin: 0; font-size: 11px; font-style: italic;">Note: Trading will execute earlier than usual due to early market close.</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Schedule Details</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Schedule Name:</strong> {schedule_name}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Env:</strong> {env}</p>
        </div>
    </div>
"""
    else:
        # Normal scheduled day
        body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #e7f5e9; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #28a745;">
            <h4 style="margin: 0 0 8px 0; color: #155724; font-size: 13px;">Trading Schedule Set</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Date:</strong> {date}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Market Close:</strong> {close_display}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Execution Time:</strong> {exec_display}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Schedule Details</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Schedule Name:</strong> {schedule_name}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Env:</strong> {env}</p>
        </div>
    </div>
"""

    return header + body + footer


def render_schedule_created_text(context: dict[str, Any]) -> str:
    """Render plain text for Schedule Created notification email.

    Args:
        context: Template context with schedule data

    Returns:
        Complete plain text email body

    """
    status = context.get("status", "scheduled")
    env = context.get("env", "unknown")
    date = context.get("date", "unknown")

    # Determine display status
    if status == "skipped_holiday":
        display_status = "MARKET CLOSED"
        component = "Schedule Skip"
    elif status == "early_close":
        display_status = "EARLY CLOSE"
        component = "Schedule Set"
    else:
        display_status = "SCHEDULED"
        component = "Schedule Set"

    header = render_text_header(component, display_status)
    footer = render_text_footer()

    execution_time = context.get("execution_time", "")
    market_close_time = context.get("market_close_time", "")
    schedule_name = context.get("schedule_name", "")
    skip_reason = context.get("skip_reason", "")

    exec_display = _format_timestamp_for_display(execution_time) if execution_time else "N/A"
    close_display = _format_timestamp_for_display(market_close_time) if market_close_time else "N/A"

    if status == "skipped_holiday":
        body = f"""
MARKET CLOSED
-------------
Date: {date}
Reason: {skip_reason or "Holiday"}

No trading schedule created. Normal operations will resume on the next trading day.

Environment: {env}
"""
    elif status == "early_close":
        body = f"""
EARLY CLOSE DAY
---------------
Date: {date}
Market Close: {close_display} (early)
Execution Time: {exec_display}

Note: Trading will execute earlier than usual due to early market close.

SCHEDULE DETAILS
----------------
Schedule Name: {schedule_name}
Environment: {env}
"""
    else:
        body = f"""
TRADING SCHEDULE SET
--------------------
Date: {date}
Market Close: {close_display}
Execution Time: {exec_display}

SCHEDULE DETAILS
----------------
Schedule Name: {schedule_name}
Environment: {env}
"""

    return header + body + footer


def _render_strategy_row_html(strat: dict[str, Any]) -> str:
    """Render an HTML table row for a strategy in the consolidated email.

    Args:
        strat: Per-strategy summary dict.

    Returns:
        HTML table row (``<tr>``) string for the strategy.

    """
    outcome = strat.get("outcome", "")
    trade_count = strat.get("trade_count", 0)

    if outcome == "TRADED":
        succeeded = strat.get("succeeded_trades", 0)
        failed = strat.get("failed_trades", 0)
        outcome_color = "#28a745" if failed == 0 else "#ffc107"
        outcome_label = "TRADED"
        details = f"{succeeded} filled"
        if failed > 0:
            details += f", {failed} failed"
            failed_syms = strat.get("failed_symbols", [])
            if failed_syms:
                details += f" ({', '.join(failed_syms)})"
    elif outcome == "ALL_HOLD":
        outcome_color = "#6c757d"
        outcome_label = "NO REBALANCE"
        details = "All positions at target"
    elif outcome == "FAILED":
        outcome_color = "#dc3545"
        outcome_label = "FAILED"
        details = strat.get("failure_reason", "Unknown error")
        if len(details) > 60:
            details = details[:57] + "..."
    else:
        outcome_color = "#6c757d"
        outcome_label = outcome
        details = ""

    name = strat.get("name", "unknown")
    return f"""
                <tr>
                    <td style="padding: 4px 6px; border-bottom: 1px solid #dee2e6;"><strong>{name}</strong></td>
                    <td style="padding: 4px 6px; border-bottom: 1px solid #dee2e6;">
                        <span style="color: {outcome_color}; font-weight: bold;">{outcome_label}</span>
                    </td>
                    <td style="padding: 4px 6px; text-align: right; border-bottom: 1px solid #dee2e6;">{trade_count}</td>
                    <td style="padding: 4px 6px; border-bottom: 1px solid #dee2e6;">{details}</td>
                </tr>
"""


def _render_portfolio_snapshot_html(
    equity: float,
    cash: float,
    gross_exposure: float,
    top_positions: list[dict[str, Any]],
) -> str:
    """Render the portfolio snapshot section as HTML.

    Args:
        equity: Account equity.
        cash: Account cash.
        gross_exposure: Gross exposure ratio.
        top_positions: Top portfolio positions.

    Returns:
        HTML snippet for portfolio snapshot (empty string if no data).

    """
    if not equity and not cash:
        return ""

    positions_html = ""
    for pos in top_positions[:5]:
        positions_html += f"                <li>{pos['symbol']} {pos['weight']:.1f}%</li>\n"
    if not top_positions:
        positions_html = "                <li>No positions</li>\n"

    return f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Exposure:</strong> {gross_exposure:.2f}x</p>
            <p style="margin: 0; font-size: 11px;"><strong>Top positions:</strong></p>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 11px;">
{positions_html}
            </ul>
        </div>
"""


def render_consolidated_run_html(context: dict[str, Any]) -> str:
    """Render HTML for consolidated daily run email (all strategies).

    This template shows a per-strategy breakdown plus aggregate totals
    and portfolio snapshot. Used when Coordinator dispatches multiple
    strategies and the NotificationSession tracks their completion.

    Args:
        context: Template context with consolidated run data.

    Returns:
        Complete HTML email body.

    """
    header = render_html_header("Daily Run", context.get("overall_status", "SUCCESS"))
    footer = render_html_footer()

    env = context.get("env", "unknown")
    correlation_id = context.get("correlation_id", "unknown")
    total_strategies = context.get("total_strategies", 0)
    strategies = context.get("strategies", [])

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))

    total_trades = context.get("total_trades", 0)
    total_succeeded = context.get("total_succeeded", 0)
    total_failed = context.get("total_failed", 0)
    total_skipped = context.get("total_skipped", 0)

    portfolio_snapshot = context.get("portfolio_snapshot", {})
    equity = portfolio_snapshot.get("equity", 0)
    cash = portfolio_snapshot.get("cash", 0)
    gross_exposure = portfolio_snapshot.get("gross_exposure", 0)
    top_positions = portfolio_snapshot.get("top_positions", [])

    pnl_metrics = context.get("pnl_metrics", {})
    monthly_pnl = pnl_metrics.get("monthly_pnl", {})
    yearly_pnl = pnl_metrics.get("yearly_pnl", {})

    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    rebalance_plan_summary = context.get("rebalance_plan_summary", [])
    logs_url = context.get("logs_url", "#")
    report_url = context.get("strategy_performance_report_url", "")

    # Identity & timing header
    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Identity & Timing</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="padding: 3px;"><strong>Env:</strong></td><td style="padding: 3px;">{env}</td>
                    <td style="padding: 3px;"><strong>Strategies:</strong></td><td style="padding: 3px;">{total_strategies}</td></tr>
                <tr><td style="padding: 3px;"><strong>Run ID:</strong></td><td colspan="3" style="padding: 3px;">{correlation_id}</td></tr>
                <tr><td style="padding: 3px;"><strong>Started:</strong></td><td colspan="3" style="padding: 3px;">{start_time}</td></tr>
                <tr><td style="padding: 3px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 3px;">{end_time}</td></tr>
            </table>
        </div>

        <div style="background-color: #e8f4f8; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">Per-Strategy Results</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr style="background-color: #d1ecf1;">
                    <th style="padding: 4px 6px; text-align: left; border-bottom: 1px solid #bee5eb;">Strategy</th>
                    <th style="padding: 4px 6px; text-align: left; border-bottom: 1px solid #bee5eb;">Outcome</th>
                    <th style="padding: 4px 6px; text-align: right; border-bottom: 1px solid #bee5eb;">Trades</th>
                    <th style="padding: 4px 6px; text-align: left; border-bottom: 1px solid #bee5eb;">Details</th>
                </tr>
"""

    # Per-strategy rows
    for strat in strategies:
        body += _render_strategy_row_html(strat)

    # Aggregate totals
    if total_failed == 0:
        agg_bg = "#e7f5e9"
        agg_border = "#28a745"
        agg_color = "#155724"
    else:
        agg_bg = "#fff3cd"
        agg_border = "#ffc107"
        agg_color = "#856404"

    body += f"""
            </table>
        </div>

        <div style="background-color: {agg_bg}; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid {agg_border};">
            <h4 style="margin: 0 0 8px 0; color: {agg_color}; font-size: 13px;">Aggregate Totals</h4>
            <p style="margin: 0; font-size: 11px;">
                <strong>Total trades:</strong> {total_trades} |
                <strong>Succeeded:</strong> {total_succeeded} |
                <strong>Failed:</strong> {total_failed} |
                <strong>Skipped:</strong> {total_skipped}
            </p>
        </div>
"""

    body += _render_portfolio_snapshot_html(equity, cash, gross_exposure, top_positions)
    body += _format_pnl_html(monthly_pnl, yearly_pnl)
    body += _format_rebalance_plan_html(rebalance_plan_summary)

    # Data freshness
    if data_freshness:
        body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> {latest_candle} (age {candle_age})
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    # Links
    links_items = f'<p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">View Logs</a></p>'
    if report_url:
        links_items += f'\n            <p style="margin: 4px 0 0 0; font-size: 11px;"><a href="{report_url}" style="color: #007bff; text-decoration: none;">Download Strategy Performance Report (CSV)</a></p>'

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Links</h4>
            {links_items}
        </div>
    </div>
"""

    return header + body + footer


def _render_strategy_line_text(strat: dict[str, Any]) -> str:
    """Render a single strategy result as a plain-text line.

    Args:
        strat: Per-strategy summary dict.

    Returns:
        Formatted text line for the strategy.

    """
    name = strat.get("name", "unknown")
    outcome = strat.get("outcome", "")
    trade_count = strat.get("trade_count", 0)

    if outcome == "TRADED":
        succeeded = strat.get("succeeded_trades", 0)
        failed = strat.get("failed_trades", 0)
        line = f"  {name}: {trade_count} trades ({succeeded} filled"
        if failed > 0:
            failed_syms = strat.get("failed_symbols", [])
            line += f", {failed} failed"
            if failed_syms:
                line += f" [{', '.join(failed_syms)}]"
        line += ")"
    elif outcome == "ALL_HOLD":
        line = f"  {name}: No rebalance needed"
    elif outcome == "FAILED":
        reason = strat.get("failure_reason", "Unknown error")
        if len(reason) > 60:
            reason = reason[:57] + "..."
        line = f"  {name}: FAILED - {reason}"
    else:
        line = f"  {name}: {outcome}"

    return line


def _render_portfolio_snapshot_text(
    equity: float,
    cash: float,
    gross_exposure: float,
    top_positions: list[dict[str, Any]],
) -> str:
    """Render the portfolio snapshot section as plain text.

    Args:
        equity: Account equity.
        cash: Account cash.
        gross_exposure: Gross exposure ratio.
        top_positions: Top portfolio positions.

    Returns:
        Plain text snippet for portfolio snapshot (empty string if no data).

    """
    if not equity and not cash:
        return ""

    text = f"""
PORTFOLIO SNAPSHOT (POST-RUN)
-----------------------------
Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
Exposure: {gross_exposure:.2f}x
Top positions:
"""
    for pos in top_positions[:5]:
        text += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"
    if not top_positions:
        text += "  - No positions\n"
    return text


def render_consolidated_run_text(context: dict[str, Any]) -> str:
    """Render plain text for consolidated daily run email (all strategies).

    Args:
        context: Template context with consolidated run data.

    Returns:
        Complete plain text email body.

    """
    header = render_text_header("Daily Run", context.get("overall_status", "SUCCESS"))
    footer = render_text_footer()

    env = context.get("env", "unknown")
    correlation_id = context.get("correlation_id", "unknown")
    total_strategies = context.get("total_strategies", 0)
    strategies = context.get("strategies", [])

    start_time = _format_timestamp_for_display(context.get("start_time_utc", ""))
    end_time = _format_timestamp_for_display(context.get("end_time_utc", ""))

    total_trades = context.get("total_trades", 0)
    total_succeeded = context.get("total_succeeded", 0)
    total_failed = context.get("total_failed", 0)
    total_skipped = context.get("total_skipped", 0)

    portfolio_snapshot = context.get("portfolio_snapshot", {})
    pnl_metrics = context.get("pnl_metrics", {})
    monthly_pnl = pnl_metrics.get("monthly_pnl", {})
    yearly_pnl = pnl_metrics.get("yearly_pnl", {})

    data_freshness = context.get("data_freshness", {})
    latest_candle, candle_age, freshness_gate = _format_data_freshness_for_display(data_freshness)

    rebalance_plan_summary = context.get("rebalance_plan_summary", [])
    logs_url = context.get("logs_url", "#")
    report_url = context.get("strategy_performance_report_url", "")

    body = f"""
Env: {env} | Strategies: {total_strategies} | Run ID: {correlation_id}
Time: {start_time} -> {end_time}

PER-STRATEGY RESULTS
--------------------
"""

    for strat in strategies:
        body += _render_strategy_line_text(strat) + "\n"

    body += f"""
AGGREGATE TOTALS
----------------
Total trades: {total_trades} | Succeeded: {total_succeeded} | Failed: {total_failed} | Skipped: {total_skipped}
"""

    body += _render_portfolio_snapshot_text(
        portfolio_snapshot.get("equity", 0),
        portfolio_snapshot.get("cash", 0),
        portfolio_snapshot.get("gross_exposure", 0),
        portfolio_snapshot.get("top_positions", []),
    )

    body += _format_pnl_text(monthly_pnl, yearly_pnl)
    body += _format_rebalance_plan_text(rebalance_plan_summary)

    if data_freshness:
        body += f"""
DATA FRESHNESS
--------------
Daily candles: {latest_candle} (age {candle_age}) DATA_FRESHNESS_GATE={freshness_gate}
"""

    body += f"""
LINKS
-----
Logs: {logs_url}
"""
    if report_url:
        body += f"Strategy Performance Report: {report_url}\n"

    return header + body + footer
