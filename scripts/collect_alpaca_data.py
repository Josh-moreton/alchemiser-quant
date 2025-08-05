#!/usr/bin/env python3
"""
Alpaca API Data Collection Utility

This utility collects real data from your Alpaca account for structure validation,
testing, and development purposes. Can be used to:

- Validate TypedDict definitions against real API responses
- Generate sample data for testing
- Verify API compatibility during development

Usage:
    python scripts/collect_alpaca_data.py

The script will create timestamped JSON files with account, position, and order data.
"""

import json
import os
from datetime import datetime
from typing import Any

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOrdersRequest

    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

from the_alchemiser.core.secrets.secrets_manager import SecretsManager


def collect_account_data(trading_client: TradingClient) -> dict[str, Any]:
    """Collect account data from Alpaca API."""
    print("📊 Collecting account data...")

    account = trading_client.get_account()

    # Convert to dict for JSON serialization
    account_dict = {
        "account_id": account.id,
        "equity": account.equity,
        "cash": account.cash,
        "buying_power": account.buying_power,
        "day_trades_remaining": account.daytrade_count,
        "portfolio_value": account.portfolio_value,
        "last_equity": account.last_equity,
        "daytrading_buying_power": account.daytrading_buying_power,
        "regt_buying_power": account.regt_buying_power,
        "status": account.status.value if hasattr(account.status, "value") else str(account.status),
    }

    print(f"✅ Account data collected for account: {account_dict['account_id']}")
    return account_dict


def collect_positions_data(trading_client: TradingClient) -> list[dict[str, Any]]:
    """Collect positions data from Alpaca API."""
    print("📈 Collecting positions data...")

    positions = trading_client.get_all_positions()

    positions_list = []
    for position in positions:
        position_dict = {
            "symbol": position.symbol,
            "qty": position.qty,
            "side": position.side.value if hasattr(position.side, "value") else str(position.side),
            "market_value": position.market_value,
            "cost_basis": position.cost_basis,
            "unrealized_pl": position.unrealized_pl,
            "unrealized_plpc": position.unrealized_plpc,
            "current_price": position.current_price,
        }
        positions_list.append(position_dict)

    print(f"✅ Positions data collected: {len(positions_list)} positions")
    return positions_list


def collect_orders_data(trading_client: TradingClient, limit: int = 10) -> list[dict[str, Any]]:
    """Collect orders data from Alpaca API."""
    print(f"📋 Collecting recent orders data (limit: {limit})...")

    # Get recent orders
    orders_request = GetOrdersRequest(limit=limit)
    orders = trading_client.get_orders(orders_request)

    orders_list = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side.value if hasattr(order.side, "value") else str(order.side),
            "order_type": (
                order.order_type.value
                if hasattr(order.order_type, "value")
                else str(order.order_type)
            ),
            "time_in_force": (
                order.time_in_force.value
                if hasattr(order.time_in_force, "value")
                else str(order.time_in_force)
            ),
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "filled_qty": order.filled_qty,
            "filled_avg_price": order.filled_avg_price,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        }
        orders_list.append(order_dict)

    print(f"✅ Orders data collected: {len(orders_list)} orders")
    return orders_list


def save_data_to_files(
    account_data: dict[str, Any],
    positions_data: list[dict[str, Any]],
    orders_data: list[dict[str, Any]],
) -> None:
    """Save collected data to JSON files."""

    # Create data directory if it doesn't exist
    data_dir = "data_validation_samples"
    os.makedirs(data_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save account data
    account_file = f"{data_dir}/account_data_{timestamp}.json"
    with open(account_file, "w") as f:
        json.dump(account_data, f, indent=2, default=str)
    print(f"💾 Account data saved to: {account_file}")

    # Save positions data
    positions_file = f"{data_dir}/positions_data_{timestamp}.json"
    with open(positions_file, "w") as f:
        json.dump(positions_data, f, indent=2, default=str)
    print(f"💾 Positions data saved to: {positions_file}")

    # Save orders data
    orders_file = f"{data_dir}/orders_data_{timestamp}.json"
    with open(orders_file, "w") as f:
        json.dump(orders_data, f, indent=2, default=str)
    print(f"💾 Orders data saved to: {orders_file}")

    print(f"\n🎯 Data collection complete! Files saved in '{data_dir}/' directory")
    print("📝 You can now run: python scripts/validate_data_structures.py")


def main():
    """Main data collection function."""

    print("🧪 Alpaca Data Collection for Structure Validation")
    print("=" * 60)

    if not ALPACA_AVAILABLE:
        print("❌ Alpaca Trading API not available. Please install: pip install alpaca-trade-api")
        return

    # Get API keys from AWS Secrets Manager
    try:
        secrets_manager = SecretsManager()

        # Determine if using paper trading (default to True for safety)
        paper_trading = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        print(f"📋 Using environment: {'LIVE' if not paper_trading else 'PAPER'}")

        # Get API keys from AWS Secrets Manager
        api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=paper_trading)

        if not api_key or not secret_key:
            print("❌ Could not retrieve Alpaca API credentials from AWS Secrets Manager.")
            print("   Please ensure your AWS credentials are configured and the secrets exist.")
            return

        print("✅ Successfully retrieved Alpaca API credentials from AWS Secrets Manager")

    except Exception as e:
        print(f"❌ Error retrieving secrets: {e}")
        return

    # Initialize trading client
    try:
        trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper_trading,
        )
        print("✅ Connected to Alpaca API")
    except Exception as e:
        print(f"❌ Error connecting to Alpaca API: {e}")
        return

    try:
        # Collect data
        account_data = collect_account_data(trading_client)
        positions_data = collect_positions_data(trading_client)
        orders_data = collect_orders_data(trading_client, limit=20)

        # Save to files
        save_data_to_files(account_data, positions_data, orders_data)

    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
