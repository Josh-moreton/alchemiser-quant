#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

DynamoDB data loader for Streamlit dashboard.
Provides functions to load account snapshots and P&L history from DynamoDB.
"""

from __future__ import annotations

import os
from pathlib import Path

import _setup_imports  # noqa: F401
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from dashboard_settings import DashboardSettings

# Import repository classes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "layers" / "shared"))

from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)
from the_alchemiser.shared.repositories.pnl_history_repository import (
    PnLHistoryRepository,
)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_pnl_from_dynamodb() -> pd.DataFrame:
    """Load P&L data from DynamoDB.
    
    Returns:
        DataFrame with P&L history or empty DataFrame if error.
    """
    try:
        settings = DashboardSettings()
        
        # Initialize repository
        repo = PnLHistoryRepository(table_name=settings.pnl_history_table)
        
        # Get account ID from environment or settings
        account_id = os.environ.get("ALPACA_ACCOUNT_ID", "unknown")
        if account_id == "unknown":
            # Try to derive from Alpaca keys if available
            try:
                from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
                from alpaca.trading.client import TradingClient
                
                api_key, secret_key, endpoint = get_alpaca_keys()
                if api_key and secret_key:
                    paper = endpoint and "paper" in endpoint.lower() if endpoint else True
                    trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
                    account = trading_client.get_account()
                    account_id = account.account_number
            except Exception:
                # Fallback to a default
                account_id = "default"
        
        # Get all P&L records
        records = repo.get_all_records(account_id)
        
        if not records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        rows = []
        for rec in records:
            rows.append({
                "Date": pd.to_datetime(rec.date),
                "Equity": float(rec.equity),
                "P&L ($)": float(rec.profit_loss),
                "P&L (%)": float(rec.profit_loss_pct) * 100,  # Convert to percentage
                "Deposits": float(rec.deposit),
                "Withdrawals": float(rec.withdrawal),
            })
        
        df = pd.DataFrame(rows)
        df = df.sort_values("Date").reset_index(drop=True)
        
        # Calculate cumulative columns
        df["Cumulative P&L"] = df["P&L ($)"].cumsum()
        df["Cumulative Deposits"] = df["Deposits"].cumsum()
        
        # Time-Weighted Return (TWR): compound daily returns to get true trading performance
        daily_returns_decimal = df["P&L (%)"] / 100  # Convert % to decimal
        df["Cumulative Return (%)"] = (
            ((1 + daily_returns_decimal).cumprod() - 1) * 100
        ).round(2)
        
        return df
        
    except Exception as e:
        st.error(f"Error loading P&L from DynamoDB: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_account_snapshot_from_dynamodb() -> dict | None:
    """Load latest account snapshot from DynamoDB.
    
    Returns:
        Dict with account information or None if error.
    """
    try:
        settings = DashboardSettings()
        
        # Initialize repository
        repo = AccountSnapshotRepository(table_name=settings.account_snapshots_table)
        
        # Get latest snapshot
        snapshot = repo.get_latest_snapshot()
        
        if not snapshot:
            return None
        
        # Convert to dict for easy access
        return {
            "equity": float(snapshot.equity),
            "cash": float(snapshot.cash),
            "buying_power": float(snapshot.buying_power),
            "portfolio_value": float(snapshot.portfolio_value),
            "long_market_value": float(snapshot.long_market_value),
            "short_market_value": float(snapshot.short_market_value),
            "timestamp": snapshot.timestamp,
        }
        
    except Exception as e:
        st.error(f"Error loading account snapshot from DynamoDB: {e}")
        return None


def has_dynamodb_data() -> bool:
    """Check if DynamoDB tables are configured and accessible.
    
    Returns:
        True if tables are accessible, False otherwise.
    """
    try:
        settings = DashboardSettings()
        return (
            settings.pnl_history_table is not None 
            and settings.account_snapshots_table is not None
        )
    except Exception:
        return False
