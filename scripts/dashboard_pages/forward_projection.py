#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Forward Projection page for equity curve projections based on historical TWR.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path

import _setup_imports  # noqa: F401
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from .components import (
    hero_metric,
    metric_card,
    metric_row,
    progress_bar,
    section_header,
    styled_dataframe,
)
from .styles import format_currency, format_percent, inject_styles

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.services.pnl_service import PnLService


@st.cache_data(ttl=300)
def load_historical_metrics() -> dict:
    """Load historical performance metrics for projection baseline."""
    service = PnLService()
    daily_records, _ = service.get_all_daily_records(period="1A")

    # Filter to active trading days only (equity > 0)
    active_records = [r for r in daily_records if r.equity > 0]

    if not active_records:
        return {}

    # Convert to DataFrame for calculations
    df = pd.DataFrame([
        {
            "Date": pd.to_datetime(r.date),
            "Equity": float(r.equity),
            "P&L (%)": float(r.profit_loss_pct),
            "Deposits": float(r.deposit) if r.deposit else 0.0,
        }
        for r in active_records
    ]).sort_values("Date")

    # Calculate TWR (time-weighted return)
    daily_returns_decimal = df["P&L (%)"] / 100
    twr = ((1 + daily_returns_decimal).prod() - 1)

    # Calculate time period
    first_date = df["Date"].iloc[0]
    last_date = df["Date"].iloc[-1]
    years = (last_date - first_date).days / 365.25

    # Annualized TWR
    if years > 0:
        annualized_return = (1 + twr) ** (1 / years) - 1
    else:
        annualized_return = 0.0

    # Calculate volatility (annualized)
    daily_vol = daily_returns_decimal.std()
    annualized_vol = daily_vol * math.sqrt(252)

    # Current equity and deposits
    current_equity = df["Equity"].iloc[-1]
    total_deposits = df["Deposits"].sum()
    avg_monthly_deposit = total_deposits / max(years * 12, 1)

    return {
        "current_equity": current_equity,
        "annualized_return": annualized_return * 100,  # As percentage
        "annualized_vol": annualized_vol * 100,  # As percentage
        "total_deposits": total_deposits,
        "avg_monthly_deposit": avg_monthly_deposit,
        "trading_days": len(df),
        "years_trading": years,
        "start_date": first_date,
        "end_date": last_date,
    }


def project_equity(
    starting_equity: float,
    annual_return_pct: float,
    years: int,
    monthly_contribution: float = 0.0,
) -> pd.DataFrame:
    """Project equity forward with optional contributions.
    
    Args:
        starting_equity: Current portfolio value
        annual_return_pct: Expected annual return (percentage, e.g., 15 for 15%)
        years: Number of years to project
        monthly_contribution: Monthly deposit amount
    
    Returns:
        DataFrame with Date, Equity columns
    """
    months = years * 12
    monthly_return = (1 + annual_return_pct / 100) ** (1/12) - 1

    dates = []
    equity = []

    current = starting_equity
    start_date = datetime.now()

    for month in range(months + 1):
        date = start_date + timedelta(days=month * 30.44)  # Average days per month
        dates.append(date)
        equity.append(current)

        # Grow for next month
        current = current * (1 + monthly_return) + monthly_contribution

    return pd.DataFrame({
        "Date": dates,
        "Equity": equity,
    })


def create_chart_data(projections: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine projections into a single DataFrame for charting."""
    # Create combined dataframe with Date as index
    combined = pd.DataFrame()
    
    for scenario_name, df in projections.items():
        if combined.empty:
            combined["Date"] = df["Date"]
        combined[scenario_name] = df["Equity"]
    
    combined = combined.set_index("Date")
    return combined


def show() -> None:
    """Render the forward projection page."""
    # Inject styles for this page
    inject_styles()

    st.title("Forward Projection")
    st.caption("Project your portfolio growth based on historical performance")

    # Load historical metrics
    metrics = load_historical_metrics()

    if not metrics:
        st.error("No historical data available for projections.")
        return

    # =========================================================================
    # HERO METRIC: Current Equity
    # =========================================================================
    hero_metric(
        label="Current Portfolio Value",
        value=format_currency(metrics["current_equity"]),
        subtitle=f"Trading since {metrics['start_date'].strftime('%b %Y')} ({metrics['years_trading']:.1f} years)",
    )

    # =========================================================================
    # HISTORICAL PERFORMANCE SUMMARY (3 columns)
    # =========================================================================
    metric_row([
        {
            "label": "Annualized Return",
            "value": format_percent(metrics["annualized_return"], include_sign=True),
            "delta_positive": metrics["annualized_return"] > 0,
            "accent": True,
        },
        {
            "label": "Annualized Volatility",
            "value": format_percent(metrics["annualized_vol"]),
        },
        {
            "label": "Trading Days",
            "value": f"{metrics['trading_days']:,}",
        },
    ])

    # =========================================================================
    # PROJECTION PARAMETERS (side-by-side controls and assumptions)
    # =========================================================================
    section_header("Projection Parameters")

    col_controls, col_assumptions = st.columns([1, 1])

    with col_controls:
        st.subheader("Controls")

        projection_years = st.slider(
            "Projection Horizon (Years)",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
        )

        monthly_contribution = st.number_input(
            "Monthly Contribution ($)",
            min_value=0.0,
            max_value=100000.0,
            value=float(round(metrics["avg_monthly_deposit"], -2)),
            step=100.0,
            help="Average monthly deposit based on your history",
        )

    with col_assumptions:
        st.subheader("Scenario Assumptions")

        base_return = metrics["annualized_return"]

        conservative_return = st.slider(
            "Conservative Return (%)",
            min_value=-10.0,
            max_value=200.0,
            value=max(base_return * 0.5, 5.0),
            step=0.5,
            help="50% of historical return or 5%, whichever is higher",
        )

        optimistic_return = st.slider(
            "Optimistic Return (%)",
            min_value=-10.0,
            max_value=500.0,
            value=min(base_return * 1.5, 50.0),
            step=0.5,
            help="150% of historical return or 50%, whichever is lower",
        )

    # =========================================================================
    # GENERATE PROJECTIONS
    # =========================================================================
    current_equity = metrics["current_equity"]

    projections = {
        "Conservative": project_equity(
            current_equity,
            conservative_return,
            projection_years,
            monthly_contribution,
        ),
        "Base Case": project_equity(
            current_equity,
            base_return,
            projection_years,
            monthly_contribution,
        ),
        "Optimistic": project_equity(
            current_equity,
            optimistic_return,
            projection_years,
            monthly_contribution,
        ),
    }

    # =========================================================================
    # PROJECTION CHART (full width)
    # =========================================================================
    section_header("Projected Equity Curve")
    
    use_log_scale = st.checkbox("Use logarithmic scale", value=False, help="Log scale better shows percentage growth over time")
    
    # Scenario colors (matches theme)
    scenario_colors = {
        "Conservative": "#808080",
        "Base Case": "#7CF5D4",
        "Optimistic": "#4CAF50",
    }
    
    fig = go.Figure()
    
    for scenario_name, df in projections.items():
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Equity"],
                mode="lines",
                name=scenario_name,
                line=dict(color=scenario_colors[scenario_name], width=2),
                hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%b %Y}<br>Equity: $%{y:,.0f}<extra></extra>",
            )
        )
    
    fig.update_layout(
        height=500,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            title="Date",
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=3, label="3y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
        ),
        yaxis=dict(
            title="Equity ($)",
            type="log" if use_log_scale else "linear",
            tickformat="$,.0f",
        ),
        margin=dict(l=60, r=20, t=40, b=60),
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # PROJECTION SUMMARY TABLE
    # =========================================================================
    section_header("Projection Summary")

    summary_data = []
    for scenario_name, df in projections.items():
        final_equity = df["Equity"].iloc[-1]
        total_contributions = monthly_contribution * projection_years * 12
        total_growth = final_equity - current_equity - total_contributions
        growth_multiple = final_equity / current_equity

        summary_data.append({
            "Scenario": scenario_name,
            "Final Equity": final_equity,
            "Total Contributions": total_contributions,
            "Investment Growth": total_growth,
            "Growth Multiple": growth_multiple,
        })

    summary_df = pd.DataFrame(summary_data)

    styled_dataframe(
        summary_df,
        formats={
            "Final Equity": "${:,.0f}",
            "Total Contributions": "${:,.0f}",
            "Investment Growth": "${:+,.0f}",
            "Growth Multiple": "{:.1f}x",
        },
        highlight_positive_negative=["Investment Growth"],
    )

    # =========================================================================
    # MILESTONES WITH PROGRESS BARS
    # =========================================================================
    section_header("Milestones (Base Case)")

    milestones = [100_000, 250_000, 500_000, 1_000_000, 2_500_000, 5_000_000, 10_000_000]
    base_df = projections["Base Case"]
    final_base_equity = base_df["Equity"].iloc[-1]

    # Display progress toward each milestone
    for milestone in milestones:
        if milestone > current_equity:
            # Find when we hit this milestone
            hits = base_df[base_df["Equity"] >= milestone]
            if not hits.empty:
                hit_date = hits["Date"].iloc[0]
                years_to_milestone = (hit_date - datetime.now()).days / 365.25

                # Progress is how far along we are to hitting this milestone
                progress_pct = (current_equity / milestone) * 100

                col_label, col_bar, col_date = st.columns([2, 6, 2])

                with col_label:
                    st.write(f"**{format_currency(milestone)}**")

                with col_bar:
                    progress_bar(
                        value=current_equity,
                        max_value=milestone,
                        show_percentage=True,
                        warning_threshold=70,
                        danger_threshold=90,
                    )

                with col_date:
                    st.write(f"{hit_date.strftime('%b %Y')} ({years_to_milestone:.1f}y)")
            else:
                # Milestone not reachable within projection horizon
                col_label, col_info = st.columns([2, 8])
                with col_label:
                    st.write(f"**{format_currency(milestone)}**")
                with col_info:
                    st.caption("Beyond projection horizon")

            # Stop after 5 milestones for cleaner display
            if milestone >= final_base_equity:
                break

    # =========================================================================
    # DISCLAIMER
    # =========================================================================
    st.divider()
    st.caption(
        "**Disclaimer:** These projections are based on historical performance and assumptions. "
        "Past performance does not guarantee future results. Actual returns may vary significantly "
        "due to market conditions, strategy changes, and other factors."
    )
