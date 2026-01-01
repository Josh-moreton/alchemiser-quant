"""Business Unit: notifications | Status: current.

Email template rendering for notifications.

This module provides HTML and plain text email templates with consistent branding.
Templates support variable substitution and shared partials (header/footer).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


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
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
        <img src="{logo_url}" alt="The Alchemiser" style="width: 60px; height: 60px; margin-bottom: 10px; border-radius: 12px;">
        <h1 style="color: white; margin: 0; font-size: 28px;">The Alchemiser</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">{component}</p>
    </div>
    <div style="background-color: {color}; color: white; padding: 15px; text-align: center; font-size: 20px; font-weight: bold;">
        {status}
    </div>
"""


def render_html_footer() -> str:
    """Render HTML email footer.

    Returns:
        HTML footer snippet

    """
    return """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e9ecef; text-align: center; color: #6c757d; font-size: 14px;">
        <p>The Alchemiser Quantitative Trading System</p>
        <p style="margin: 5px 0;">Automated notification - do not reply</p>
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
    corr_id = context.get("correlation_id", run_id)
    version = context.get("version_git_sha", "unknown")[:7]
    strategy_version = context.get("strategy_version", "unknown")

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

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Identity & Timing</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px;"><strong>Env:</strong></td><td style="padding: 5px;">{env}</td>
                    <td style="padding: 5px;"><strong>Mode:</strong></td><td style="padding: 5px;">{mode}</td></tr>
                <tr><td style="padding: 5px;"><strong>Run ID:</strong></td><td style="padding: 5px;">{run_id}</td>
                    <td style="padding: 5px;"><strong>Corr ID:</strong></td><td style="padding: 5px;">{corr_id}</td></tr>
                <tr><td style="padding: 5px;"><strong>Version:</strong></td><td style="padding: 5px;">{version}</td>
                    <td style="padding: 5px;"><strong>Strategy:</strong></td><td style="padding: 5px;">{strategy_version}</td></tr>
                <tr><td style="padding: 5px;"><strong>Started:</strong></td><td colspan="3" style="padding: 5px;">{start_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Ended:</strong></td><td colspan="3" style="padding: 5px;">{end_time}</td></tr>
                <tr><td style="padding: 5px;"><strong>Duration:</strong></td><td colspan="3" style="padding: 5px;">{duration}s</td></tr>
            </table>
        </div>

        <div style="background-color: #e7f5e9; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0; color: #155724;">Outcome Summary</h3>
            <p><strong>Symbols evaluated:</strong> {symbols_evaluated} | <strong>Eligible signals:</strong> {eligible} | <strong>Blocked by risk:</strong> {blocked}</p>
            <p><strong>Orders:</strong> placed={orders_placed} | filled={orders_filled} | cancelled={orders_cancelled} | rejected={orders_rejected}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Portfolio Snapshot (Post-Run)</h3>
            <p><strong>Equity:</strong> ${equity:,.2f} | <strong>Cash:</strong> ${cash:,.2f}</p>
            <p><strong>Gross exposure:</strong> {gross_exposure:.2f}x | <strong>Net exposure:</strong> {net_exposure:.2f}x</p>
            <p><strong>Top positions:</strong></p>
            <ul style="margin-top: 5px;">
"""

    for pos in top_positions[:3]:
        body += f"                <li>{pos['symbol']} {pos['weight']:.1f}%</li>\n"

    if not top_positions:
        body += "                <li>No positions</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Data Freshness</h3>
            <p><strong>Daily candles:</strong> latest={latest_candle} (age {candle_age}d)
            <span style="color: {"#28a745" if freshness_gate == "PASS" else "#dc3545"}; font-weight: bold;">
                DATA_FRESHNESS_GATE={freshness_gate}
            </span></p>
        </div>
"""

    if warnings:
        body += """
        <div style="background-color: #fff3cd; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #856404;">⚠️ Warnings</h3>
            <ul style="margin-bottom: 0;">
"""
        for warning in warnings:
            body += f"                <li>{warning}</li>\n"
        body += """
            </ul>
        </div>
"""

    body += f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #495057;">Links</h3>
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs</a></p>
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
    corr_id = context.get("correlation_id", run_id)
    version = context.get("version_git_sha", "unknown")[:7]
    strategy_version = context.get("strategy_version", "unknown")

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

    warnings = context.get("warnings", [])
    logs_url = context.get("logs_url", "#")

    body = f"""
Env: {env} | Mode: {mode}
Run: {run_id} (corr_id={corr_id}) | Version: {version} | Strategy: {strategy_version}
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
    corr_id = context.get("correlation_id", run_id)
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
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
        <div style="background-color: #f8d7da; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #dc3545;">
            <h3 style="margin-top: 0; color: #721c24;">What Failed + Impact</h3>
            <p><strong>Failed Step:</strong> {failed_step}</p>
            <p><strong>Impact:</strong> {impact}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Error Signature</h3>
            <p><strong>Exception Type:</strong> {exception_type}</p>
            <p><strong>Message:</strong> {exception_message}</p>
            <pre style="background-color: #e9ecef; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 12px;">{stack_trace}</pre>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #495057;">Context</h3>
            <p><strong>Env:</strong> {env} | <strong>Run ID:</strong> {run_id} | <strong>Corr ID:</strong> {corr_id}</p>
            <p><strong>Retry attempts:</strong> {retry_attempts} | <strong>Last attempt:</strong> {last_attempt_time}</p>
            <p><strong>Last successful run:</strong> {last_successful_run} at {last_successful_time}</p>
        </div>

        <div style="background-color: #d1ecf1; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #17a2b8;">
            <h3 style="margin-top: 0; color: #0c5460;">Quick Actions</h3>
            <ul style="margin-bottom: 0;">
"""

    for action in quick_actions[:5]:
        body += f"                <li>{action}</li>\n"

    if not quick_actions:
        body += "                <li>Check logs for detailed error information</li>\n"

    body += f"""
            </ul>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #495057;">Links</h3>
            <p><a href="{logs_url}" style="color: #007bff; text-decoration: none;">📋 View Logs (filtered by run_id)</a></p>
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
    corr_id = context.get("correlation_id", run_id)
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
Env: {env} | Run ID: {run_id} | Corr ID: {corr_id}
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
    "render_daily_run_success_html",
    "render_daily_run_success_text",
]
