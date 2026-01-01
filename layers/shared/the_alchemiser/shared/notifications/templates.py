"""Business Unit: notifications | Status: current.

Email template rendering for notifications.

This module provides HTML and plain text email templates with consistent branding.
Templates support variable substitution and shared partials (header/footer).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _format_pnl_html(monthly_pnl: dict[str, Any], yearly_pnl: dict[str, Any]) -> str:
    """Format P&L metrics as an HTML section.

    Args:
        monthly_pnl: Monthly P&L data dict with total_pnl, total_pnl_pct, period.
        yearly_pnl: Yearly P&L data dict with total_pnl, total_pnl_pct, period.

    Returns:
        HTML snippet for P&L section, or empty string if no data.

    """
    if not monthly_pnl and not yearly_pnl:
        return ""

    def format_pnl_value(pnl: float | None, pct: float | None) -> str:
        if pnl is None:
            return "N/A"
        sign = "+" if pnl >= 0 else ""
        color = "#28a745" if pnl >= 0 else "#dc3545"
        pct_str = f" ({sign}{pct:.2f}%)" if pct is not None else ""
        return f'<span style="color: {color};">{sign}${pnl:,.2f}{pct_str}</span>'

    monthly_str = format_pnl_value(monthly_pnl.get("total_pnl"), monthly_pnl.get("total_pnl_pct"))
    yearly_str = format_pnl_value(yearly_pnl.get("total_pnl"), yearly_pnl.get("total_pnl_pct"))

    return f"""
        <div style="background-color: #e8f4f8; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <h4 style="margin: 0 0 8px 0; color: #0c5460; font-size: 13px;">📈 Portfolio Performance</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Past Month:</strong> {monthly_str}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Past Year:</strong> {yearly_str}</p>
        </div>
"""


def _format_pnl_text(monthly_pnl: dict[str, Any], yearly_pnl: dict[str, Any]) -> str:
    """Format P&L metrics as a plain text section.

    Args:
        monthly_pnl: Monthly P&L data dict with total_pnl, total_pnl_pct, period.
        yearly_pnl: Yearly P&L data dict with total_pnl, total_pnl_pct, period.

    Returns:
        Plain text snippet for P&L section, or empty string if no data.

    """
    if not monthly_pnl and not yearly_pnl:
        return ""

    def format_pnl_value(pnl: float | None, pct: float | None) -> str:
        if pnl is None:
            return "N/A"
        sign = "+" if pnl >= 0 else ""
        pct_str = f" ({sign}{pct:.2f}%)" if pct is not None else ""
        return f"{sign}${pnl:,.2f}{pct_str}"

    monthly_str = format_pnl_value(monthly_pnl.get("total_pnl"), monthly_pnl.get("total_pnl_pct"))
    yearly_str = format_pnl_value(yearly_pnl.get("total_pnl"), yearly_pnl.get("total_pnl_pct"))

    return f"""
PORTFOLIO PERFORMANCE
---------------------
• Past Month: {monthly_str}
• Past Year: {yearly_str}
"""


def format_subject(
    component: str,
    status: str,
    env: str,
    run_id: str,
    run_date: datetime | None = None,
) -> str:
    """Format email subject line following strict spec.

    Format: Alchemiser <Component> — <STATUS> — <YYYY-MM-DD> — <env> — run_id=<run_id>

    Args:
        component: Component name (e.g., "Daily Run", "Data Lake Update")
        status: Status (SUCCESS, SUCCESS_WITH_WARNINGS, FAILURE, RECOVERED)
        env: Environment (dev/staging/prod)
        run_id: Run ID (short form, e.g., "8f3c1a")
        run_date: Optional run date (defaults to today)

    Returns:
        Formatted subject line

    """
    if run_date is None:
        run_date = datetime.now(UTC)

    date_str = run_date.strftime("%Y-%m-%d")
    return f"Alchemiser {component} — {status} — {date_str} — {env} — run_id={run_id}"


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
    <title>Alchemiser {component} — {status}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.5; color: #333; max-width: 700px; margin: 0 auto; padding: 15px; font-size: 13px;">
    <div style="padding: 15px 0; border-bottom: 2px solid #e9ecef; text-align: center; margin-bottom: 15px;">
        <img src="{logo_url}" alt="The Alchemiser" style="width: 40px; height: 40px; margin-bottom: 8px; border-radius: 8px;">
        <h1 style="color: #333; margin: 0; font-size: 18px; font-weight: 600;">The Alchemiser</h1>
        <p style="color: #666; margin: 4px 0 0 0; font-size: 13px;">{component}</p>
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
        <p style="margin: 0;">The Alchemiser Quantitative Trading System</p>
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
    THE ALCHEMISER - {component.upper()}
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
The Alchemiser Quantitative Trading System
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

    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)

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
    net_exposure = context.get("net_exposure", 0)
    top_positions = context.get("top_positions", [])

    data_freshness = context.get("data_freshness", {})
    latest_candle = data_freshness.get("latest_timestamp", "N/A")
    candle_age = data_freshness.get("age_days", 0)
    freshness_gate = data_freshness.get("gate_status", "UNKNOWN")

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

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
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Gross exposure:</strong> {gross_exposure:.2f}x | <strong>Net exposure:</strong> {net_exposure:.2f}x</p>
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

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> latest={latest_candle} (age {candle_age}d)
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">⚠️ Warnings</h4>
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
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs</a></p>
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

    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)

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
    net_exposure = context.get("net_exposure", 0)
    top_positions = context.get("top_positions", [])

    data_freshness = context.get("data_freshness", {})
    latest_candle = data_freshness.get("latest_timestamp", "N/A")
    candle_age = data_freshness.get("age_days", 0)
    freshness_gate = data_freshness.get("gate_status", "UNKNOWN")

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode} | Run ID: {run_id}
Time: {start_time} → {end_time} ({duration}s)

SUMMARY
-------
• Symbols evaluated: {symbols_evaluated} | Eligible: {eligible} | Blocked by risk: {blocked}
• Orders: placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}

PORTFOLIO SNAPSHOT (POST-RUN)
------------------------------
• Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
• Gross exposure: {gross_exposure:.2f}x | Net exposure: {net_exposure:.2f}x
• Top positions:
"""

    for pos in top_positions[:3]:
        body += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"

    if not top_positions:
        body += "  - No positions\n"

    # Add P&L section if data available
    body += _format_pnl_text(monthly_pnl, yearly_pnl)

    body += f"""
DATA FRESHNESS USED
-------------------
• Daily candles: latest={latest_candle} (age {candle_age}d) DATA_FRESHNESS_GATE={freshness_gate}
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

    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)

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
    net_exposure = context.get("net_exposure", 0)
    top_positions = context.get("top_positions", [])

    data_freshness = context.get("data_freshness", {})
    latest_candle = data_freshness.get("latest_timestamp", "N/A")
    candle_age = data_freshness.get("age_days", 0)
    freshness_gate = data_freshness.get("gate_status", "UNKNOWN")

    # Partial success specific
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

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
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">⚠️ Partial Success</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;">Most trades executed successfully, but some positions were skipped due to non-fractionable assets.</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p style="margin: 0; font-size: 11px;"><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">📊 Skipped Positions (Non-Fractionable)</h4>
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
                💡 <strong>Tip:</strong> Consider increasing your total portfolio value or adjusting strategy weights to ensure these assets meet the minimum 1-share threshold.
            </p>
        </div>

"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Portfolio Snapshot (Post-Run)</h4>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p style="margin: 0 0 4px 0; font-size: 11px;"><strong>Gross exposure:</strong> {gross_exposure:.2f}x | <strong>Net exposure:</strong> {net_exposure:.2f}x</p>
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

    body += f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Data Freshness</h4>
            <p style="margin: 0; font-size: 11px;"><strong>Daily candles:</strong> latest={latest_candle} (age {candle_age}d)
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 12px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">⚠️ Warnings</h4>
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
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs</a></p>
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

    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)

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
    net_exposure = context.get("net_exposure", 0)
    top_positions = context.get("top_positions", [])

    data_freshness = context.get("data_freshness", {})
    latest_candle = data_freshness.get("latest_timestamp", "N/A")
    candle_age = data_freshness.get("age_days", 0)
    freshness_gate = data_freshness.get("gate_status", "UNKNOWN")

    # Partial success specific
    non_fractionable_skipped = context.get("non_fractionable_skipped_symbols", [])

    # Extract P&L metrics
    monthly_pnl = context.get("monthly_pnl", {})
    yearly_pnl = context.get("yearly_pnl", {})

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode} | Run ID: {run_id}
Time: {start_time} → {end_time} ({duration}s)

⚠️ PARTIAL SUCCESS
------------------
Most trades executed successfully, but some positions were skipped.

SUMMARY
-------
• Symbols evaluated: {symbols_evaluated} | Eligible: {eligible} | Blocked by risk: {blocked}
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
💡 Tip: Consider increasing your total portfolio value or adjusting strategy
   weights to ensure these assets meet the minimum 1-share threshold.

"""

    body += f"""PORTFOLIO SNAPSHOT (POST-RUN)
------------------------------
• Equity: ${equity:,.2f} | Cash: ${cash:,.2f}
• Gross exposure: {gross_exposure:.2f}x | Net exposure: {net_exposure:.2f}x
• Top positions:
"""

    for pos in top_positions[:3]:
        body += f"  - {pos['symbol']} {pos['weight']:.1f}%\n"

    if not top_positions:
        body += "  - No positions\n"

    # Add P&L section if data available
    body += _format_pnl_text(monthly_pnl, yearly_pnl)

    body += f"""
DATA FRESHNESS USED
-------------------
• Daily candles: latest={latest_candle} (age {candle_age}d) DATA_FRESHNESS_GATE={freshness_gate}
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
    header = render_html_header("Daily Run", "FAILURE")
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
    last_attempt_time = context.get("last_attempt_time_utc", "")

    last_successful_run = context.get("last_successful_run_id", "N/A")
    last_successful_time = context.get("last_successful_run_time_utc", "N/A")

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
            <p style="margin: 0; font-size: 11px;"><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs (filtered by run_id)</a></p>
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
    header = render_text_header("Daily Run", "FAILURE")
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
    last_attempt_time = context.get("last_attempt_time_utc", "")

    last_successful_run = context.get("last_successful_run_id", "N/A")
    last_successful_time = context.get("last_successful_run_time_utc", "N/A")

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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)
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

        <div style="background-color: #e7f5e9; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0; color: #155724;">Data Refresh Summary</h3>
            <p><strong>Total symbols processed:</strong> {total_symbols}</p>
            <p><strong>Successfully updated:</strong> {symbols_updated_count}</p>
            <p><strong>Total bars fetched:</strong> {total_bars_fetched}</p>
            <p><strong>Data source:</strong> {data_source}</p>
        </div>

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
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs</a></p>
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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Run: {run_id}
Time: {start_time} → {end_time} ({duration:.1f}s)

DATA REFRESH SUMMARY
--------------------
• Total symbols processed: {total_symbols}
• Successfully updated: {symbols_updated_count}
• Total bars fetched: {total_bars_fetched}
• Data source: {data_source}

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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)
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

        <div style="background-color: #fff3cd; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #856404;">⚠️ Partial Success</h3>
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
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs</a></p>
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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
    duration = context.get("duration_seconds", 0)
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Run: {run_id}
Time: {start_time} → {end_time} ({duration:.1f}s)

⚠️ PARTIAL SUCCESS
------------------
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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
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
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs (filtered by run_id)</a></p>
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
    start_time = context.get("start_time_utc", "")
    end_time = context.get("end_time_utc", "")
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
    "render_daily_run_success_html",
    "render_daily_run_success_text",
]
