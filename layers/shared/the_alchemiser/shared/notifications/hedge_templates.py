"""Business Unit: notifications | Status: current.

Email template rendering for hedge evaluation notifications.

Provides HTML and plain text templates for hedge evaluation results,
separate from the main portfolio notification templates.
Reuses shared partials (header/footer) from templates module.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.notifications.templates import (
    render_html_footer,
    render_html_header,
    render_text_footer,
    render_text_header,
)


def render_hedge_evaluation_success_html(context: dict[str, Any]) -> str:
    """Render HTML for hedge evaluation SUCCESS email.

    Displays IV regime, template selection, and full recommendation details
    including underlying, delta target, DTE, estimated contracts, and premium budget.

    Args:
        context: Template context with hedge evaluation data

    Returns:
        Complete HTML email body

    """
    header = render_html_header("Hedge Evaluation", "SUCCESS")
    footer = render_html_footer()

    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    portfolio_nav = context.get("portfolio_nav", "N/A")
    vix_tier = context.get("vix_tier", "unknown")
    template_selected = context.get("template_selected", "unknown")
    template_regime = context.get("template_regime", "N/A")
    template_reason = context.get("template_selection_reason", "")
    total_premium = context.get("total_premium_budget", "N/A")
    budget_nav_pct = context.get("budget_nav_pct", "N/A")
    current_vix = context.get("current_vix", "N/A")
    exposure_multiplier = context.get("exposure_multiplier", "1.0")
    recommendations = context.get("recommendations", [])
    logs_url = context.get("logs_url", "#")

    # Build recommendations table rows
    rec_rows = _build_recommendation_rows_html(recommendations)

    body = f"""
    <div style="padding: 15px 0;">
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Evaluation Summary</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="padding: 3px;"><strong>Env:</strong></td><td style="padding: 3px;">{env}</td>
                    <td style="padding: 3px;"><strong>IV Regime:</strong></td><td style="padding: 3px;">{vix_tier}</td></tr>
                <tr><td style="padding: 3px;"><strong>Template:</strong></td><td style="padding: 3px;">{template_selected}</td>
                    <td style="padding: 3px;"><strong>VIX Estimate:</strong></td><td style="padding: 3px;">{current_vix}</td></tr>
                <tr><td style="padding: 3px;"><strong>Portfolio NAV:</strong></td><td style="padding: 3px;">${portfolio_nav}</td>
                    <td style="padding: 3px;"><strong>Exposure Mult:</strong></td><td style="padding: 3px;">{exposure_multiplier}x</td></tr>
                <tr><td style="padding: 3px;"><strong>Premium Budget:</strong></td><td style="padding: 3px;">${total_premium}</td>
                    <td style="padding: 3px;"><strong>Budget (% NAV):</strong></td><td style="padding: 3px;">{budget_nav_pct}%</td></tr>
                <tr><td style="padding: 3px;"><strong>Run ID:</strong></td><td colspan="3" style="padding: 3px; font-size: 10px;">{run_id}</td></tr>
            </table>
        </div>
"""

    if template_reason:
        body += f"""
        <div style="background-color: #e8f4fd; padding: 10px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #17a2b8;">
            <strong style="font-size: 11px; color: #495057;">Template Rationale:</strong>
            <span style="font-size: 11px; color: #495057;"> {template_reason}</span>
            <br><span style="font-size: 10px; color: #6c757d;">Regime: {template_regime}</span>
        </div>
"""

    if recommendations:
        body += """
        <div style="margin-bottom: 12px;">
            <h4 style="margin: 0 0 8px 0; color: #495057; font-size: 13px;">Hedge Recommendations</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px; border: 1px solid #dee2e6;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 6px; text-align: left; border-bottom: 2px solid #dee2e6;">Underlying</th>
                        <th style="padding: 6px; text-align: right; border-bottom: 2px solid #dee2e6;">Delta</th>
                        <th style="padding: 6px; text-align: right; border-bottom: 2px solid #dee2e6;">DTE</th>
                        <th style="padding: 6px; text-align: right; border-bottom: 2px solid #dee2e6;">Contracts</th>
                        <th style="padding: 6px; text-align: right; border-bottom: 2px solid #dee2e6;">Premium</th>
                        <th style="padding: 6px; text-align: left; border-bottom: 2px solid #dee2e6;">Template</th>
                    </tr>
                </thead>
                <tbody>
"""
        body += rec_rows
        body += """
                </tbody>
            </table>
        </div>
"""
    else:
        body += """
        <div style="background-color: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #ffc107;">
            <strong style="font-size: 11px;">No hedge recommendations generated.</strong>
        </div>
"""

    body += f"""
        <div style="margin-top: 12px; font-size: 11px;">
            <strong>Links</strong><br>
            <a href="{logs_url}" style="color: #007bff;">View Logs (filtered by run_id)</a>
        </div>
    </div>
"""

    return header + body + footer


def render_hedge_evaluation_success_text(context: dict[str, Any]) -> str:
    """Render plain text for hedge evaluation SUCCESS email.

    Args:
        context: Template context with hedge evaluation data

    Returns:
        Complete plain text email body

    """
    header = render_text_header("Hedge Evaluation", "SUCCESS")
    footer = render_text_footer()

    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")
    portfolio_nav = context.get("portfolio_nav", "N/A")
    vix_tier = context.get("vix_tier", "unknown")
    template_selected = context.get("template_selected", "unknown")
    template_regime = context.get("template_regime", "N/A")
    template_reason = context.get("template_selection_reason", "")
    total_premium = context.get("total_premium_budget", "N/A")
    budget_nav_pct = context.get("budget_nav_pct", "N/A")
    current_vix = context.get("current_vix", "N/A")
    exposure_multiplier = context.get("exposure_multiplier", "1.0")
    recommendations = context.get("recommendations", [])
    logs_url = context.get("logs_url", "#")

    lines = [
        header,
        "EVALUATION SUMMARY",
        f"  Env: {env}  |  IV Regime: {vix_tier}",
        f"  Template: {template_selected}  |  VIX Estimate: {current_vix}",
        f"  Portfolio NAV: ${portfolio_nav}  |  Exposure Mult: {exposure_multiplier}x",
        f"  Premium Budget: ${total_premium}  |  Budget (% NAV): {budget_nav_pct}%",
        f"  Run ID: {run_id}",
        "",
    ]

    if template_reason:
        lines.extend(
            [
                f"Template Rationale: {template_reason}",
                f"  Regime: {template_regime}",
                "",
            ]
        )

    if recommendations:
        lines.append("HEDGE RECOMMENDATIONS")
        lines.append(
            f"  {'Underlying':<12} {'Delta':>8} {'DTE':>6} {'Contracts':>10} {'Premium':>12} {'Template':<12}"
        )
        lines.append(f"  {'-' * 62}")
        for rec in recommendations:
            lines.append(
                f"  {rec.get('underlying_symbol', 'N/A'):<12} "
                f"{rec.get('target_delta', 'N/A'):>8} "
                f"{rec.get('target_dte', 'N/A'):>6} "
                f"{rec.get('contracts_estimated', 'N/A'):>10} "
                f"${rec.get('premium_budget', 'N/A'):>11} "
                f"{rec.get('hedge_template', 'N/A'):<12}"
            )
        lines.append("")
    else:
        lines.extend(["No hedge recommendations generated.", ""])

    lines.extend(
        [
            f"Logs: {logs_url}",
        ]
    )

    return "\n".join(lines) + footer


def _build_recommendation_rows_html(recommendations: list[dict[str, Any]]) -> str:
    """Build HTML table rows for hedge recommendations.

    Args:
        recommendations: List of recommendation dicts from HedgeEvaluationCompleted event

    Returns:
        HTML table rows string

    """
    rows = ""
    for rec in recommendations:
        underlying = rec.get("underlying_symbol", "N/A")
        delta = rec.get("target_delta", "N/A")
        dte = rec.get("target_dte", "N/A")
        contracts = rec.get("contracts_estimated", "N/A")
        premium = rec.get("premium_budget", "N/A")
        template = rec.get("hedge_template", "N/A")

        rows += f"""
                    <tr>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6;">{underlying}</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6; text-align: right;">{delta}</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6; text-align: right;">{dte}</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6; text-align: right;">{contracts}</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6; text-align: right;">${premium}</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6;">{template}</td>
                    </tr>
"""
    return rows
