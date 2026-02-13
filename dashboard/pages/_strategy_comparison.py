"""Business Unit: dashboard | Status: current.

Strategy comparison renderer for the Strategy Performance page.

Renders multi-strategy P&L overlay charts and side-by-side metrics
tables. Extracted from strategy_performance.py to keep modules under
the 500-line target.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import strategy as sda
from components.ui import section_header, styled_dataframe

_ACCENT_COLORS = [
    "#7CF5D4",
    "#10B981",
    "#F59E0B",
    "#3B82F6",
    "#8B5CF6",
    "#EF4444",
]


def show_comparison(
    snapshots: list[dict[str, Any]],
    metadata: dict[str, dict[str, Any]],
) -> None:
    """Render multi-strategy comparison overlay."""
    section_header("Strategy Comparison")

    strategy_names = sorted(s["strategy_name"] for s in snapshots)
    display_map = {
        name: metadata.get(name, {}).get("display_name", name) for name in strategy_names
    }

    selected = st.multiselect(
        "Select strategies to compare (2-6)",
        options=strategy_names,
        format_func=lambda x: display_map.get(x, x),
        max_selections=6,
    )

    if len(selected) < 2:
        st.info("Select at least 2 strategies to compare.")
        return

    fig_cmp, comparison_rows = _build_comparison_chart(
        selected, snapshots, display_map
    )

    fig_cmp.update_layout(
        height=400,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"title": ""},
        yaxis={"title": "Realized P&L ($)", "tickformat": "$,.0f"},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    if comparison_rows:
        cdf = pd.DataFrame(comparison_rows)
        styled_dataframe(
            cdf,
            formats={
                "Realized P&L": "${:,.2f}",
                "Win Rate (%)": "{:.1f}%",
                "P&L Sharpe": "{:.2f}",
                "Max DD": "${:,.2f}",
                "Profit Factor": "{:.2f}",
            },
            highlight_positive_negative=["Realized P&L", "P&L Sharpe"],
        )


def _build_comparison_chart(
    selected: list[str],
    snapshots: list[dict[str, Any]],
    display_map: dict[str, str],
) -> tuple[go.Figure, list[dict[str, Any]]]:
    """Build overlaid P&L chart and comparison metrics rows."""
    fig_cmp = go.Figure()
    comparison_rows: list[dict[str, Any]] = []

    for i, name in enumerate(selected):
        ts = sda.get_strategy_time_series(name)
        if not ts:
            continue

        df_ts = pd.DataFrame(ts)
        df_ts["timestamp"] = pd.to_datetime(df_ts["snapshot_timestamp"])
        df_ts = df_ts.sort_values("timestamp")
        df_ts["date"] = df_ts["timestamp"].dt.date
        df_ts = df_ts.drop_duplicates(subset="date", keep="last")

        color = _ACCENT_COLORS[i % len(_ACCENT_COLORS)]
        display = display_map.get(name, name)

        fig_cmp.add_trace(
            go.Scatter(
                x=df_ts["timestamp"],
                y=df_ts["realized_pnl"],
                mode="lines",
                name=display,
                line={"color": color, "width": 2},
                hovertemplate=(
                    f"{display}<br>Date: %{{x|%b %d, %Y}}<br>"
                    f"P&L: $%{{y:,.2f}}<extra></extra>"
                ),
            )
        )

        snap = next((s for s in snapshots if s["strategy_name"] == name), None)
        risk = sda.get_strategy_metrics(name) or {}
        if snap:
            comparison_rows.append(
                {
                    "Strategy": display,
                    "Realized P&L": snap["realized_pnl"],
                    "Win Rate (%)": snap["win_rate"],
                    "Trades": snap["completed_trades"],
                    "P&L Sharpe": risk.get("pnl_sharpe", 0.0),
                    "Max DD": risk.get("max_drawdown", 0.0),
                    "Profit Factor": (
                        risk["profit_factor"]
                        if risk.get("profit_factor") is not None
                        else float("nan")
                    ),
                }
            )

    return fig_cmp, comparison_rows
