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
import streamlit as st
from dotenv import load_dotenv

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
    st.header("Forward Projection")
    st.caption("Project your portfolio growth based on historical performance")

    # Load historical metrics
    metrics = load_historical_metrics()

    if not metrics:
        st.error("No historical data available for projections.")
        return

    # Display current metrics
    st.subheader("Historical Performance Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Equity", f"${metrics['current_equity']:,.2f}")
    with col2:
        st.metric("Annualized Return", f"{metrics['annualized_return']:+.1f}%")
    with col3:
        st.metric("Annualized Volatility", f"{metrics['annualized_vol']:.1f}%")
    with col4:
        st.metric("Trading History", f"{metrics['years_trading']:.1f} years")

    st.divider()

    # Projection parameters
    st.subheader("Projection Parameters")

    col1, col2 = st.columns(2)

    with col1:
        projection_years = st.slider(
            "Projection Horizon (Years)",
            min_value=1,
            max_value=20,
            value=10,
            step=1,
        )

        monthly_contribution = st.number_input(
            "Monthly Contribution ($)",
            min_value=0.0,
            max_value=100000.0,
            value=float(round(metrics["avg_monthly_deposit"], -2)),  # Round to nearest 100
            step=100.0,
            help="Average monthly deposit based on your history",
        )

    with col2:
        # Return assumptions for scenarios
        base_return = metrics["annualized_return"]

        conservative_return = st.slider(
            "Conservative Return (%)",
            min_value=-10.0,
            max_value=50.0,
            value=max(base_return * 0.5, 5.0),  # 50% of historical or 5%, whichever is higher
            step=0.5,
        )

        optimistic_return = st.slider(
            "Optimistic Return (%)",
            min_value=-10.0,
            max_value=100.0,
            value=min(base_return * 1.5, 50.0),  # 150% of historical or 50%, whichever is lower
            step=0.5,
        )

    st.divider()

    # Generate projections
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

    # Display chart
    st.subheader("Projected Equity Curve")
    chart_data = create_chart_data(projections)
    st.line_chart(chart_data, height=500)

    # Projection summary table
    st.subheader("Projection Summary")

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

    st.dataframe(
        summary_df.style.format({
            "Final Equity": "${:,.0f}",
            "Total Contributions": "${:,.0f}",
            "Investment Growth": "${:+,.0f}",
            "Growth Multiple": "{:.1f}x",
        }),
        width="stretch",
        hide_index=True,
    )

    # Milestones
    st.subheader("Milestones (Base Case)")
    milestones = [100_000, 250_000, 500_000, 1_000_000, 2_500_000, 5_000_000, 10_000_000]
    base_df = projections["Base Case"]

    milestone_rows = []
    for milestone in milestones:
        if milestone > current_equity:
            # Find when we hit this milestone
            hits = base_df[base_df["Equity"] >= milestone]
            if not hits.empty:
                hit_date = hits["Date"].iloc[0]
                years_to_milestone = (hit_date - datetime.now()).days / 365.25
                milestone_rows.append({
                    "Milestone": f"${milestone:,.0f}",
                    "Projected Date": hit_date.strftime("%b %Y"),
                    "Years Away": f"{years_to_milestone:.1f}",
                })

    if milestone_rows:
        st.dataframe(
            pd.DataFrame(milestone_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No milestones within projection horizon")

    # Disclaimer
    st.divider()
    st.caption(
        "**Disclaimer:** These projections are based on historical performance and assumptions. "
        "Past performance does not guarantee future results. Actual returns may vary significantly "
        "due to market conditions, strategy changes, and other factors."
    )
