"""Business Unit: dashboard | Status: current.

Reusable UI Components for Octarine Capital Dashboard.

This module provides styled, reusable components that maintain
visual consistency across all dashboard pages.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from components.styles import (
    format_currency,
    format_percent,
    get_colors,
    inject_styles,
    positive_negative_color,
)

# ============================================================================
# Metric Components
# ============================================================================


def hero_metric(
    label: str,
    value: str,
    subtitle: str | None = None,
) -> None:
    """Render a large, prominent hero metric with gradient background.

    Args:
        label: Metric label (displayed small above value)
        value: The main value to display (pre-formatted)
        subtitle: Optional subtitle below the value
    """
    subtitle_html = f'<div class="hero-metric-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="hero-metric">
            <div class="hero-metric-label">{label}</div>
            <div class="hero-metric-value">{value}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_positive: bool | None = None,
    accent: bool = False,
) -> None:
    """Render a styled metric card.

    Args:
        label: Metric label (displayed small above value)
        value: The main value to display (pre-formatted)
        delta: Optional delta/change value
        delta_positive: Whether delta is positive (green) or negative (red)
        accent: Whether to show accent border on left
    """
    colors = get_colors()
    card_class = "metric-card metric-card-accent" if accent else "metric-card"

    delta_html = ""
    if delta is not None:
        if delta_positive is True:
            delta_html = f'<div class="metric-delta metric-delta-positive">{delta}</div>'
        elif delta_positive is False:
            delta_html = f'<div class="metric-delta metric-delta-negative">{delta}</div>'
        else:
            delta_html = f'<div class="metric-delta" style="color: {colors.text_secondary}">{delta}</div>'

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(metrics: list[dict[str, Any]]) -> None:
    """Render a row of metric cards.

    Args:
        metrics: List of dicts with keys: label, value, delta (optional),
                delta_positive (optional), accent (optional)
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            metric_card(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta"),
                delta_positive=metric.get("delta_positive"),
                accent=metric.get("accent", False),
            )


# ============================================================================
# Section Components
# ============================================================================


def section_header(title: str) -> None:
    """Render a styled section header with turquoise accent underline.

    Args:
        title: Section title text
    """
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def section_divider() -> None:
    """Render a subtle section divider."""
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)


# ============================================================================
# Status Components
# ============================================================================


def status_badge(status: str, text: str | None = None) -> str:
    """Generate HTML for a status badge.

    Args:
        status: One of "ok", "warning", "critical", "neutral"
        text: Display text (defaults to status)

    Returns:
        HTML string for the badge
    """
    display_text = text or status.upper()
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{display_text}</span>'


def render_status_badge(status: str, text: str | None = None) -> None:
    """Render a status badge directly.

    Args:
        status: One of "ok", "warning", "critical", "neutral"
        text: Display text (defaults to status)
    """
    st.markdown(status_badge(status, text), unsafe_allow_html=True)


# ============================================================================
# Progress Components
# ============================================================================


def progress_bar(
    value: float,
    max_value: float = 100,
    label: str | None = None,
    show_percentage: bool = True,
    warning_threshold: float = 70,
    danger_threshold: float = 90,
) -> None:
    """Render a styled progress bar with optional color thresholds.

    Args:
        value: Current value
        max_value: Maximum value (default 100)
        label: Optional label to show
        show_percentage: Whether to show percentage text
        warning_threshold: Percentage at which bar turns warning color
        danger_threshold: Percentage at which bar turns danger color
    """
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0

    bar_class = "progress-bar"
    if percentage >= danger_threshold:
        bar_class += " progress-bar-danger"
    elif percentage >= warning_threshold:
        bar_class += " progress-bar-warning"

    label_html = f'<div style="margin-bottom: 0.5rem; font-size: 0.875rem;">{label}</div>' if label else ""
    percent_html = f'<span style="margin-left: 0.5rem; font-size: 0.875rem;">{percentage:.1f}%</span>' if show_percentage else ""

    st.markdown(
        f"""
        {label_html}
        <div style="display: flex; align-items: center;">
            <div class="progress-container" style="flex: 1;">
                <div class="{bar_class}" style="width: {percentage}%;"></div>
            </div>
            {percent_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Pipeline/Workflow Components
# ============================================================================


def pipeline_status(
    steps: list[dict[str, Any]],
) -> None:
    """Render a pipeline status visualization.

    Args:
        steps: List of dicts with keys: name, status ("complete", "error", "pending")
    """
    html_parts = []
    for i, step in enumerate(steps):
        status = step.get("status", "pending")
        name = step["name"]

        if status == "complete":
            icon = "checkmark"
            step_class = "pipeline-step pipeline-step-complete"
        elif status == "error":
            icon = "x"
            step_class = "pipeline-step pipeline-step-error"
        else:
            icon = "o"
            step_class = "pipeline-step pipeline-step-pending"

        html_parts.append(f'<span class="{step_class}">{icon} {name}</span>')

        if i < len(steps) - 1:
            html_parts.append('<span class="pipeline-arrow">-></span>')

    st.markdown(
        f'<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem;">{"".join(html_parts)}</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
# Alert Components
# ============================================================================


def alert_box(
    message: str,
    alert_type: str = "info",
    icon: str | None = None,
) -> None:
    """Render a styled alert box.

    Args:
        message: Alert message text
        alert_type: One of "info", "success", "warning", "error"
        icon: Optional emoji/icon to prepend
    """
    icon_html = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="alert-box alert-{alert_type}">{icon_html}{message}</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
# Table Components
# ============================================================================


def styled_dataframe(
    df: pd.DataFrame,
    formats: dict[str, str] | None = None,
    highlight_positive_negative: list[str] | None = None,
    hide_index: bool = True,
    height: int | None = None,
) -> None:
    """Render a styled pandas DataFrame.

    Args:
        df: DataFrame to display
        formats: Dict mapping column names to format strings
        highlight_positive_negative: List of column names to color green/red by value
        hide_index: Whether to hide the row index
        height: Optional fixed height in pixels
    """
    if df.empty:
        st.info("No data available")
        return

    styled = df.style

    # Apply number formats
    if formats:
        styled = styled.format(formats)

    # Apply positive/negative coloring
    if highlight_positive_negative:
        colors = get_colors()

        def color_positive_negative(val: Any) -> str:
            try:
                num_val = float(val) if not isinstance(val, (int, float)) else val
                if num_val > 0:
                    return f"color: {colors.positive}"
                elif num_val < 0:
                    return f"color: {colors.negative}"
            except (ValueError, TypeError):
                pass
            return ""

        for col in highlight_positive_negative:
            if col in df.columns:
                styled = styled.map(color_positive_negative, subset=[col])

    # Build dataframe kwargs - only include height if specified
    df_kwargs: dict[str, Any] = {
        "hide_index": hide_index,
        "width": "stretch",
    }
    if height is not None:
        df_kwargs["height"] = height

    st.dataframe(styled, **df_kwargs)


def direction_styled_dataframe(
    df: pd.DataFrame,
    direction_col: str = "Direction",
    formats: dict[str, str] | None = None,
    hide_index: bool = True,
    height: int | None = None,
) -> None:
    """Render a DataFrame with BUY/SELL direction coloring.

    Args:
        df: DataFrame to display
        direction_col: Name of the direction column
        formats: Dict mapping column names to format strings
        hide_index: Whether to hide the row index
        height: Optional fixed height in pixels
    """
    if df.empty:
        st.info("No data available")
        return

    colors = get_colors()

    def color_direction(val: Any) -> str:
        val_str = str(val).upper()
        if val_str == "BUY":
            return f"color: {colors.positive}; font-weight: 600"
        elif val_str == "SELL":
            return f"color: {colors.negative}; font-weight: 600"
        return ""

    styled = df.style

    if formats:
        styled = styled.format(formats)

    if direction_col in df.columns:
        styled = styled.map(color_direction, subset=[direction_col])

    # Build dataframe kwargs - only include height if specified
    df_kwargs: dict[str, Any] = {
        "hide_index": hide_index,
        "width": "stretch",
    }
    if height is not None:
        df_kwargs["height"] = height

    st.dataframe(styled, **df_kwargs)


# ============================================================================
# Layout Helpers
# ============================================================================


def card_columns(
    num_columns: int,
    contents: list[callable],
) -> None:
    """Render multiple card contents in columns.

    Args:
        num_columns: Number of columns
        contents: List of callables that render content
    """
    cols = st.columns(num_columns)
    for col, content_fn in zip(cols, contents):
        with col:
            content_fn()


def two_column_layout(
    left_content: callable,
    right_content: callable,
    left_width: int = 6,
    right_width: int = 4,
) -> None:
    """Render two-column layout with configurable widths.

    Args:
        left_content: Callable that renders left column content
        right_content: Callable that renders right column content
        left_width: Relative width of left column (default 6)
        right_width: Relative width of right column (default 4)
    """
    col_left, col_right = st.columns([left_width, right_width])
    with col_left:
        left_content()
    with col_right:
        right_content()


# ============================================================================
# Page Setup Helper
# ============================================================================


def setup_page(title: str, subtitle: str | None = None) -> None:
    """Standard page setup: inject styles and render header.

    Args:
        title: Page title
        subtitle: Optional subtitle/description
    """
    inject_styles()
    st.title(title)
    if subtitle:
        st.caption(subtitle)
