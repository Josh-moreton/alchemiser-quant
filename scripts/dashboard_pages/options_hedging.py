#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Options Hedging dashboard page showing hedge positions, decisions, and analytics.

Displays active hedge positions, decision history, premium spend tracking,
and roll schedule forecasts from DynamoDB hedge tables.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
import streamlit as st
from botocore.exceptions import ClientError
from dashboard_settings import debug_secrets_info, get_dashboard_settings
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Constants
ROLL_TRIGGER_DTE_TAIL = 45  # Days to expiry threshold for tail template rolls
ROLL_TRIGGER_DTE_SMOOTHING = 21  # Days for smoothing template roll cadence
MAX_ANNUAL_PREMIUM_SPEND_PCT = Decimal("0.05")  # 5% NAV annual cap


# =============================================================================
# DynamoDB Query Functions
# =============================================================================


@st.cache_data(ttl=120, show_spinner="Loading hedge positions...")
def query_active_positions(
    table_name: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Query active hedge positions from DynamoDB.

    Returns (positions, error_message).
    """
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key

    try:
        dynamodb = boto3.client("dynamodb", **kwargs)

        # Scan for active positions
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression="#status = :active",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":active": {"S": "active"}},
        )

        positions = []
        for item in response.get("Items", []):
            positions.append(_parse_position_item(item))

        # Sort by expiration date
        positions.sort(key=lambda x: x.get("expiration_date", ""))

        return positions, None

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            return [], f"Table not found: {table_name}"
        return [], f"DynamoDB Error: {e}"
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"


@st.cache_data(ttl=120, show_spinner="Loading hedge history...")
def query_hedge_history(
    table_name: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    limit: int = 50,
    days_back: int = 90,
) -> tuple[list[dict[str, Any]], str | None]:
    """Query hedge history from DynamoDB.

    Returns (history_records, error_message).
    """
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key

    try:
        dynamodb = boto3.client("dynamodb", **kwargs)

        # Calculate time filter
        start_time = datetime.now(UTC) - timedelta(days=days_back)
        start_iso = start_time.isoformat()

        # Scan with time filter (history table uses account_id as PK)
        # Since we don't know the account_id, we scan with time filter
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression="#ts >= :start_time",
            ExpressionAttributeNames={"#ts": "timestamp"},
            ExpressionAttributeValues={":start_time": {"S": start_iso}},
            Limit=limit * 2,  # Over-fetch to allow for filtering
        )

        records = []
        for item in response.get("Items", []):
            records.append(_parse_history_item(item))

        # Sort by timestamp descending (newest first)
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return records[:limit], None

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            return [], f"Table not found: {table_name}"
        return [], f"DynamoDB Error: {e}"
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"


def _parse_position_item(item: dict[str, Any]) -> dict[str, Any]:
    """Parse DynamoDB position item to dict."""
    return {
        "hedge_id": item.get("hedge_id", {}).get("S", ""),
        "option_symbol": item.get("option_symbol", {}).get("S", ""),
        "underlying_symbol": item.get("underlying_symbol", {}).get("S", ""),
        "option_type": item.get("option_type", {}).get("S", "put"),
        "strike_price": Decimal(item.get("strike_price", {}).get("S", "0")),
        "expiration_date": item.get("expiration_date", {}).get("S", ""),
        "contracts": int(item.get("contracts", {}).get("N", "0")),
        "entry_price": Decimal(item.get("entry_price", {}).get("S", "0")),
        "entry_date": item.get("entry_date", {}).get("S", ""),
        "entry_delta": Decimal(item.get("entry_delta", {}).get("S", "0")),
        "total_premium_paid": Decimal(item.get("total_premium_paid", {}).get("S", "0")),
        "status": item.get("status", {}).get("S", "active"),
        "roll_state": item.get("roll_state", {}).get("S", "holding"),
        "hedge_template": item.get("hedge_template", {}).get("S", "tail_first"),
        "is_spread": item.get("is_spread", {}).get("BOOL", False),
        "short_leg_symbol": item.get("short_leg_symbol", {}).get("S"),
        "short_leg_strike": (
            Decimal(item.get("short_leg_strike", {}).get("S", "0"))
            if item.get("short_leg_strike", {}).get("S")
            else None
        ),
        "nav_at_entry": (
            Decimal(item.get("nav_at_entry", {}).get("S", "0"))
            if item.get("nav_at_entry", {}).get("S")
            else None
        ),
        "nav_percentage": (
            Decimal(item.get("nav_percentage", {}).get("S", "0"))
            if item.get("nav_percentage", {}).get("S")
            else None
        ),
    }


def _parse_history_item(item: dict[str, Any]) -> dict[str, Any]:
    """Parse DynamoDB history item to dict."""
    return {
        "account_id": item.get("account_id", {}).get("S", ""),
        "timestamp": item.get("timestamp", {}).get("S", ""),
        "action": item.get("action", {}).get("S", ""),
        "hedge_id": item.get("hedge_id", {}).get("S", ""),
        "option_symbol": item.get("option_symbol", {}).get("S", ""),
        "underlying_symbol": item.get("underlying_symbol", {}).get("S", ""),
        "contracts": int(item.get("contracts", {}).get("N", "0")),
        "premium": Decimal(item.get("premium", {}).get("S", "0")),
        "details": item.get("details", {}).get("M", {}),
        "correlation_id": item.get("correlation_id", {}).get("S", ""),
    }


# =============================================================================
# Display Functions
# =============================================================================


def show_positions_summary(positions: list[dict[str, Any]]) -> None:
    """Display summary metrics for active positions."""
    if not positions:
        st.info("No active hedge positions")
        return

    # Calculate summary metrics
    total_contracts = sum(p.get("contracts", 0) for p in positions)
    total_premium = sum(p.get("total_premium_paid", Decimal("0")) for p in positions)

    # Calculate weighted average DTE
    today = datetime.now(UTC).date()
    total_dte_weighted = Decimal("0")
    for pos in positions:
        exp_str = pos.get("expiration_date", "")
        if exp_str:
            try:
                exp_date = datetime.fromisoformat(exp_str.replace("Z", "+00:00")).date()
                dte = (exp_date - today).days
                total_dte_weighted += Decimal(dte) * pos.get("contracts", 0)
            except (ValueError, TypeError):
                pass

    avg_dte = float(total_dte_weighted / total_contracts) if total_contracts > 0 else 0

    # Count by template
    tail_count = sum(1 for p in positions if p.get("hedge_template") == "tail_first")
    smoothing_count = len(positions) - tail_count

    st.subheader("Position Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Positions", len(positions))
    with col2:
        st.metric("Total Contracts", total_contracts)
    with col3:
        st.metric("Total Premium Paid", f"${float(total_premium):,.2f}")
    with col4:
        st.metric("Avg DTE", f"{avg_dte:.0f} days")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tail Hedges", tail_count)
    with col2:
        st.metric("Smoothing Hedges", smoothing_count)


def show_active_positions_table(positions: list[dict[str, Any]]) -> None:
    """Display active positions in a table."""
    st.subheader("Active Hedge Positions")

    if not positions:
        st.info("No active hedge positions found")
        return

    today = datetime.now(UTC).date()

    rows = []
    for pos in positions:
        # Calculate DTE
        exp_str = pos.get("expiration_date", "")
        dte = 0
        if exp_str:
            try:
                exp_date = datetime.fromisoformat(exp_str.replace("Z", "+00:00")).date()
                dte = (exp_date - today).days
            except (ValueError, TypeError):
                pass

        # Determine roll urgency
        template = pos.get("hedge_template", "tail_first")
        roll_threshold = (
            ROLL_TRIGGER_DTE_TAIL if template == "tail_first" else ROLL_TRIGGER_DTE_SMOOTHING
        )

        if dte <= 14:
            roll_status = "CRITICAL"
        elif dte <= roll_threshold:
            roll_status = "DUE"
        else:
            roll_status = "OK"

        rows.append(
            {
                "Underlying": pos.get("underlying_symbol", ""),
                "Type": pos.get("option_type", "put").upper(),
                "Strike": f"${float(pos.get('strike_price', 0)):,.0f}",
                "Expiry": exp_str[:10] if exp_str else "",
                "DTE": dte,
                "Contracts": pos.get("contracts", 0),
                "Entry $": f"${float(pos.get('entry_price', 0)):.2f}",
                "Entry Δ": f"{float(pos.get('entry_delta', 0)):.2f}",
                "Premium": f"${float(pos.get('total_premium_paid', 0)):,.2f}",
                "Template": template,
                "Roll": roll_status,
            }
        )

    df = pd.DataFrame(rows)

    # Style roll status
    def style_roll(val: str) -> str:
        if val == "CRITICAL":
            return "color: red; font-weight: bold"
        if val == "DUE":
            return "color: orange; font-weight: bold"
        return "color: green"

    styled_df = df.style.map(style_roll, subset=["Roll"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)


def show_roll_forecast(positions: list[dict[str, Any]]) -> None:
    """Display roll schedule forecast."""
    st.subheader("Roll Schedule Forecast")

    if not positions:
        st.info("No positions to forecast rolls for")
        return

    today = datetime.now(UTC).date()

    # Calculate roll dates for each position
    roll_items = []
    for pos in positions:
        exp_str = pos.get("expiration_date", "")
        if not exp_str:
            continue

        try:
            exp_date = datetime.fromisoformat(exp_str.replace("Z", "+00:00")).date()
            dte = (exp_date - today).days

            template = pos.get("hedge_template", "tail_first")
            roll_threshold = (
                ROLL_TRIGGER_DTE_TAIL if template == "tail_first" else ROLL_TRIGGER_DTE_SMOOTHING
            )

            # Estimated roll date (when DTE hits threshold)
            days_until_roll = dte - roll_threshold
            roll_date = today + timedelta(days=max(0, days_until_roll))

            roll_items.append(
                {
                    "underlying": pos.get("underlying_symbol", ""),
                    "expiration": exp_date,
                    "dte": dte,
                    "roll_threshold": roll_threshold,
                    "estimated_roll_date": roll_date,
                    "days_until_roll": days_until_roll,
                    "contracts": pos.get("contracts", 0),
                    "template": template,
                }
            )
        except (ValueError, TypeError):
            pass

    if not roll_items:
        st.info("No valid positions for roll forecast")
        return

    # Sort by roll urgency
    roll_items.sort(key=lambda x: x["days_until_roll"])

    # Display upcoming rolls
    df = pd.DataFrame(
        [
            {
                "Underlying": item["underlying"],
                "Contracts": item["contracts"],
                "Current Expiry": item["expiration"].strftime("%Y-%m-%d"),
                "DTE": item["dte"],
                "Est. Roll Date": item["estimated_roll_date"].strftime("%Y-%m-%d"),
                "Days to Roll": max(0, item["days_until_roll"]),
                "Template": item["template"],
            }
            for item in roll_items
        ]
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Highlight urgent rolls
    urgent_rolls = [item for item in roll_items if item["days_until_roll"] <= 7]
    if urgent_rolls:
        st.warning(f"{len(urgent_rolls)} position(s) due for roll within 7 days!")


def show_history_timeline(records: list[dict[str, Any]]) -> None:
    """Display hedge decision history timeline."""
    st.subheader("Decision History")

    if not records:
        st.info("No hedge history records found")
        return

    rows = []
    for rec in records:
        timestamp = rec.get("timestamp", "")
        # Format timestamp for display
        ts_display = timestamp[:19] if timestamp else ""

        rows.append(
            {
                "Timestamp": ts_display,
                "Action": rec.get("action", "").replace("_", " ").title(),
                "Underlying": rec.get("underlying_symbol", ""),
                "Option": rec.get("option_symbol", "")[:20] + "..."
                if len(rec.get("option_symbol", "")) > 20
                else rec.get("option_symbol", ""),
                "Contracts": rec.get("contracts", 0),
                "Premium": f"${float(rec.get('premium', 0)):,.2f}" if rec.get("premium") else "",
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)


def show_premium_spend_analysis(
    records: list[dict[str, Any]],
    current_nav: Decimal | None = None,
) -> None:
    """Display premium spend analysis vs annual cap."""
    st.subheader("Premium Spend Tracking")

    # Calculate rolling 12-month spend from history
    twelve_months_ago = datetime.now(UTC) - timedelta(days=365)

    ytd_spend = Decimal("0")
    spend_by_month: dict[str, Decimal] = {}

    for rec in records:
        premium = rec.get("premium", Decimal("0"))
        if not premium:
            continue

        # Only count spend actions (opened, rolled)
        action = rec.get("action", "")
        if action not in ("hedge_opened", "hedge_rolled"):
            continue

        timestamp = rec.get("timestamp", "")
        if not timestamp:
            continue

        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if ts >= twelve_months_ago:
                ytd_spend += premium

                # Group by month for chart
                month_key = ts.strftime("%Y-%m")
                spend_by_month[month_key] = spend_by_month.get(month_key, Decimal("0")) + premium
        except (ValueError, TypeError):
            pass

    # Display metrics
    if current_nav and current_nav > 0:
        annual_cap = current_nav * MAX_ANNUAL_PREMIUM_SPEND_PCT
        spend_pct = (ytd_spend / current_nav) * 100
        remaining = max(Decimal("0"), annual_cap - ytd_spend)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("12-Month Spend", f"${float(ytd_spend):,.2f}")
        with col2:
            st.metric("Annual Cap (5% NAV)", f"${float(annual_cap):,.2f}")
        with col3:
            st.metric("Spend % of NAV", f"{float(spend_pct):.2f}%")
        with col4:
            st.metric("Remaining Budget", f"${float(remaining):,.2f}")

        # Progress bar
        progress = min(1.0, float(ytd_spend / annual_cap)) if annual_cap > 0 else 0
        st.progress(progress, text=f"Budget utilization: {progress * 100:.1f}%")
    else:
        st.metric("12-Month Spend", f"${float(ytd_spend):,.2f}")
        st.info("NAV data unavailable - cannot calculate budget utilization")

    # Monthly spend chart
    if spend_by_month:
        st.subheader("Monthly Premium Spend")
        chart_data = pd.DataFrame(
            [{"Month": k, "Premium ($)": float(v)} for k, v in sorted(spend_by_month.items())]
        )
        st.bar_chart(chart_data.set_index("Month"))


def show_position_details(positions: list[dict[str, Any]]) -> None:
    """Display detailed position info in expanders."""
    st.subheader("Position Details")

    if not positions:
        return

    for pos in positions:
        hedge_id = pos.get("hedge_id", "unknown")[:12]
        underlying = pos.get("underlying_symbol", "")
        strike = float(pos.get("strike_price", 0))

        with st.expander(f"{underlying} ${strike:.0f} Put - {hedge_id}..."):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Contract Details**")
                st.write(f"- Option Symbol: `{pos.get('option_symbol', '')}`")
                st.write(f"- Type: {pos.get('option_type', 'put').upper()}")
                st.write(f"- Strike: ${strike:,.2f}")
                st.write(f"- Expiration: {pos.get('expiration_date', '')[:10]}")
                st.write(f"- Contracts: {pos.get('contracts', 0)}")

            with col2:
                st.write("**Entry Details**")
                st.write(f"- Entry Price: ${float(pos.get('entry_price', 0)):.2f}")
                st.write(f"- Entry Date: {pos.get('entry_date', '')[:10]}")
                st.write(f"- Entry Delta: {float(pos.get('entry_delta', 0)):.3f}")
                st.write(f"- Total Premium: ${float(pos.get('total_premium_paid', 0)):,.2f}")

            st.write("**Hedge Configuration**")
            st.write(f"- Template: {pos.get('hedge_template', 'tail_first')}")
            st.write(f"- Roll State: {pos.get('roll_state', 'holding')}")

            if pos.get("is_spread"):
                st.write("**Spread Details**")
                st.write(f"- Short Leg Symbol: `{pos.get('short_leg_symbol', 'N/A')}`")
                st.write(f"- Short Leg Strike: ${float(pos.get('short_leg_strike', 0) or 0):,.2f}")

            if pos.get("nav_at_entry"):
                st.write("**NAV Context**")
                st.write(f"- NAV at Entry: ${float(pos.get('nav_at_entry', 0)):,.2f}")
                st.write(f"- % of NAV: {float(pos.get('nav_percentage', 0) or 0) * 100:.3f}%")


# =============================================================================
# Main Page
# =============================================================================


def show() -> None:
    """Display the options hedging dashboard page."""
    st.title("Options Hedging")
    st.caption("Hedge positions, decisions, and premium spend analytics")

    settings = get_dashboard_settings()

    # Debug expander
    with st.expander("Debug: Configuration", expanded=False):
        debug_info = debug_secrets_info()
        st.text(f"Stage: {settings.stage}")
        st.text(f"AWS Region: {settings.aws_region}")
        st.text(f"Positions Table: {settings.hedge_positions_table}")
        st.text(f"History Table: {settings.hedge_history_table}")
        st.text(f"Has credentials: {settings.has_aws_credentials()}")
        for key, value in debug_info.items():
            st.text(f"  {key}: {value}")

    # Check credentials
    if not settings.has_aws_credentials():
        st.error(
            "AWS credentials not configured. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Streamlit secrets."
        )
        return

    # Query data
    positions, pos_error = query_active_positions(
        table_name=settings.hedge_positions_table,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    history, hist_error = query_hedge_history(
        table_name=settings.hedge_history_table,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        limit=50,
        days_back=90,
    )

    # Try to get current NAV from Alpaca (optional)
    current_nav: Decimal | None = None
    try:
        from the_alchemiser.shared.services.pnl_service import PnLService

        pnl_service = PnLService()
        # Get most recent equity value
        records, _ = pnl_service.get_all_daily_records(period="1W")
        if records:
            current_nav = records[-1].equity
    except Exception:
        pass  # NAV unavailable, continue without

    # Display errors if any
    if pos_error:
        st.warning(f"Positions: {pos_error}")
    if hist_error:
        st.warning(f"History: {hist_error}")

    # Display sections
    st.divider()
    show_positions_summary(positions)

    st.divider()
    show_active_positions_table(positions)

    st.divider()
    show_roll_forecast(positions)

    st.divider()
    show_premium_spend_analysis(history, current_nav)

    st.divider()
    show_history_timeline(history)

    st.divider()
    show_position_details(positions)
