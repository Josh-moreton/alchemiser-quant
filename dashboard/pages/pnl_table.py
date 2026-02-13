"""Business Unit: dashboard | Status: current.

Daily PnL Table page -- raw tabular view of all DynamoDB PnL records.

Displays every daily PnL record persisted by the account_data Lambda so
the user can inspect exact values for debugging or reconciliation.
"""

from __future__ import annotations

import _setup_imports  # noqa: F401
import pandas as pd
import streamlit as st

from components.styles import inject_styles
from data import account as data_access


@st.cache_data(ttl=300)
def _load_pnl_dataframe() -> pd.DataFrame:
    """Load all PnL records from DynamoDB and return as a DataFrame."""
    records = data_access.get_all_pnl_records()
    if not records:
        return pd.DataFrame()

    rows = []
    for rec in records:
        rows.append(
            {
                "Date": rec.date,
                "Equity": float(rec.equity),
                "Daily P&L ($)": float(rec.profit_loss),
                "Daily P&L (%)": float(rec.profit_loss_pct),
                "Deposit": float(rec.deposit) if rec.deposit else None,
                "Withdrawal": float(rec.withdrawal) if rec.withdrawal else None,
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    return df


def show() -> None:
    """Render the Daily PnL Table page."""
    inject_styles()
    st.title("Daily PnL Records")
    st.caption(
        "Raw daily records from DynamoDB (written by account_data Lambda every 6 hours). "
        "Source: Alpaca portfolio history with deposit adjustments."
    )

    last_updated = data_access.get_data_last_updated()
    if last_updated:
        st.info(f"Data last refreshed: {last_updated}")

    df = _load_pnl_dataframe()

    if df.empty:
        st.warning("No PnL records found in DynamoDB.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric("Date Range", f"{df['Date'].min()} to {df['Date'].max()}")
    with col3:
        total_pnl = df["Daily P&L ($)"].sum()
        st.metric("Cumulative P&L", f"${total_pnl:,.2f}")
    with col4:
        total_deposits = df["Deposit"].sum() if df["Deposit"].notna().any() else 0
        st.metric("Total Deposits", f"${total_deposits:,.2f}")

    st.markdown("---")

    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        show_deposits_only = st.checkbox("Show only days with deposits/withdrawals")
    with filter_col2:
        show_negative_only = st.checkbox("Show only negative P&L days")

    display_df = df.copy()
    if show_deposits_only:
        display_df = display_df[
            display_df["Deposit"].notna() | display_df["Withdrawal"].notna()
        ]
    if show_negative_only:
        display_df = display_df[display_df["Daily P&L ($)"] < 0]

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=700,
        column_config={
            "Date": st.column_config.TextColumn("Date"),
            "Equity": st.column_config.NumberColumn("Equity", format="$%.2f"),
            "Daily P&L ($)": st.column_config.NumberColumn("Daily P&L ($)", format="$%.2f"),
            "Daily P&L (%)": st.column_config.NumberColumn("Daily P&L (%)", format="%.4f%%"),
            "Deposit": st.column_config.NumberColumn("Deposit", format="$%.2f"),
            "Withdrawal": st.column_config.NumberColumn("Withdrawal", format="$%.2f"),
        },
    )

    # CSV download
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="daily_pnl_records.csv",
        mime="text/csv",
    )
