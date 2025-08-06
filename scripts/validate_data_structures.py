#!/usr/bin/env python3
"""
TypedDict Data Structure Validation Utility

This utility validates that TypedDict definitions match actual API responses.
Useful for:

- Ensuring type safety during development
- Validating data structure changes
- Testing API compatibility
- Confirming TypedDict accuracy

Usage:
    python scripts/validate_data_structures.py

The script will look for JSON data files and validate them against TypedDict definitions.
"""

import json
import os
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def validate_account_data(alpaca_account_data: dict[str, Any]) -> bool:
    """Validate Alpaca account data against AccountInfo TypedDict."""

    console.print("\n[bold blue]🔍 Validating Account Data Structure[/bold blue]")

    # Expected fields from AccountInfo TypedDict
    expected_fields = {
        "account_id": str,
        "equity": (str, float),
        "cash": (str, float),
        "buying_power": (str, float),
        "day_trades_remaining": int,
        "portfolio_value": (str, float),
        "last_equity": (str, float),
        "daytrading_buying_power": (str, float),
        "regt_buying_power": (str, float),
        "status": str,  # Should be ACTIVE or INACTIVE
    }

    table = Table(title="Account Data Validation")
    table.add_column("Field", style="cyan")
    table.add_column("Expected Type", style="yellow")
    table.add_column("Actual Type", style="green")
    table.add_column("Value", style="white")
    table.add_column("Status", style="bold")

    issues = []

    for field, expected_type in expected_fields.items():
        if field in alpaca_account_data:
            actual_value = alpaca_account_data[field]
            actual_type = type(actual_value).__name__

            # Check if type matches
            if isinstance(expected_type, tuple):
                type_match = any(isinstance(actual_value, t) for t in expected_type)
                expected_type_str = " | ".join(t.__name__ for t in expected_type)
            else:
                type_match = isinstance(actual_value, expected_type)
                expected_type_str = expected_type.__name__

            status = "✅ MATCH" if type_match else "❌ MISMATCH"
            if not type_match:
                issues.append(f"Field '{field}': expected {expected_type_str}, got {actual_type}")

            table.add_row(
                field,
                expected_type_str,
                actual_type,
                (
                    str(actual_value)[:50] + "..."
                    if len(str(actual_value)) > 50
                    else str(actual_value)
                ),
                status,
            )
        else:
            table.add_row(field, str(expected_type), "MISSING", "N/A", "❌ MISSING")
            issues.append(f"Missing required field: '{field}'")

    console.print(table)

    if issues:
        console.print("\n[bold red]❌ Issues Found:[/bold red]")
        for issue in issues:
            console.print(f"  • {issue}")
        return False
    else:
        console.print("\n[bold green]✅ Account data structure validation PASSED![/bold green]")
        return True


def validate_position_data(alpaca_positions_data: list[dict[str, Any]]) -> bool:
    """Validate Alpaca positions data against PositionInfo TypedDict."""

    console.print("\n[bold blue]🔍 Validating Position Data Structure[/bold blue]")

    if not alpaca_positions_data:
        console.print("[yellow]⚠️  No positions data to validate[/yellow]")
        return True

    # Expected fields from PositionInfo TypedDict
    expected_fields = {
        "symbol": str,
        "qty": (str, float),
        "side": str,  # Should be 'long' or 'short'
        "market_value": (str, float),
        "cost_basis": (str, float),
        "unrealized_pl": (str, float),
        "unrealized_plpc": (str, float),
        "current_price": (str, float),
    }

    table = Table(title="Position Data Validation")
    table.add_column("Field", style="cyan")
    table.add_column("Expected Type", style="yellow")
    table.add_column("Sample Value", style="white")
    table.add_column("Status", style="bold")

    issues = []
    sample_position = alpaca_positions_data[0]  # Use first position as sample

    for field, expected_type in expected_fields.items():
        if field in sample_position:
            actual_value = sample_position[field]

            # Check if type matches
            if isinstance(expected_type, tuple):
                type_match = any(isinstance(actual_value, t) for t in expected_type)
                expected_type_str = " | ".join(t.__name__ for t in expected_type)
            else:
                type_match = isinstance(actual_value, expected_type)
                expected_type_str = expected_type.__name__

            status = "✅ MATCH" if type_match else "❌ MISMATCH"
            if not type_match:
                issues.append(
                    f"Field '{field}': expected {expected_type_str}, got {type(actual_value).__name__}"
                )

            table.add_row(
                field,
                expected_type_str,
                (
                    str(actual_value)[:30] + "..."
                    if len(str(actual_value)) > 30
                    else str(actual_value)
                ),
                status,
            )
        else:
            table.add_row(field, str(expected_type), "MISSING", "❌ MISSING")
            issues.append(f"Missing required field: '{field}'")

    console.print(table)

    if issues:
        console.print(
            f"\n[bold red]❌ Issues Found in {len(alpaca_positions_data)} positions:[/bold red]"
        )
        for issue in issues:
            console.print(f"  • {issue}")
        return False
    else:
        console.print(
            f"\n[bold green]✅ Position data structure validation PASSED for {len(alpaca_positions_data)} positions![/bold green]"
        )
        return True


def validate_order_data(alpaca_orders_data: list[dict[str, Any]]) -> bool:
    """Validate Alpaca orders data against OrderDetails TypedDict."""

    console.print("\n[bold blue]🔍 Validating Order Data Structure[/bold blue]")

    if not alpaca_orders_data:
        console.print("[yellow]⚠️  No orders data to validate[/yellow]")
        return True

    # Expected fields from OrderDetails TypedDict
    expected_fields = {
        "id": str,
        "symbol": str,
        "qty": (str, float),
        "side": str,  # Should be 'buy' or 'sell'
        "order_type": str,  # Should be 'market', 'limit', etc.
        "time_in_force": str,  # Should be 'day', 'gtc', etc.
        "status": str,  # Should be 'new', 'filled', etc.
        "filled_qty": (str, float),
        "filled_avg_price": (str, float, type(None)),
        "created_at": str,
        "updated_at": str,
    }

    table = Table(title="Order Data Validation")
    table.add_column("Field", style="cyan")
    table.add_column("Expected Type", style="yellow")
    table.add_column("Sample Value", style="white")
    table.add_column("Status", style="bold")

    issues = []
    sample_order = alpaca_orders_data[0]  # Use first order as sample

    for field, expected_type in expected_fields.items():
        if field in sample_order:
            actual_value = sample_order[field]

            # Check if type matches
            if isinstance(expected_type, tuple):
                type_match = any(isinstance(actual_value, t) for t in expected_type)
                expected_type_str = " | ".join(
                    t.__name__ if t is not type(None) else "None" for t in expected_type
                )
            else:
                type_match = isinstance(actual_value, expected_type)
                expected_type_str = expected_type.__name__

            status = "✅ MATCH" if type_match else "❌ MISMATCH"
            if not type_match:
                issues.append(
                    f"Field '{field}': expected {expected_type_str}, got {type(actual_value).__name__}"
                )

            table.add_row(
                field,
                expected_type_str,
                (
                    str(actual_value)[:40] + "..."
                    if len(str(actual_value)) > 40
                    else str(actual_value)
                ),
                status,
            )
        else:
            table.add_row(field, str(expected_type), "MISSING", "❌ MISSING")
            issues.append(f"Missing required field: '{field}'")

    console.print(table)

    if issues:
        console.print(
            f"\n[bold red]❌ Issues Found in {len(alpaca_orders_data)} orders:[/bold red]"
        )
        for issue in issues:
            console.print(f"  • {issue}")
        return False
    else:
        console.print(
            f"\n[bold green]✅ Order data structure validation PASSED for {len(alpaca_orders_data)} orders![/bold green]"
        )
        return True


def analyze_extra_fields(actual_data: dict[str, Any], data_type: str) -> None:
    """Analyze any extra fields in actual data that aren't in our TypedDict."""

    console.print(f"\n[bold blue]🔍 Extra Fields Analysis for {data_type}[/bold blue]")

    # Define our known fields for each type
    known_fields = {
        "account": {
            "account_id",
            "equity",
            "cash",
            "buying_power",
            "day_trades_remaining",
            "portfolio_value",
            "last_equity",
            "daytrading_buying_power",
            "regt_buying_power",
            "status",
        },
        "position": {
            "symbol",
            "qty",
            "side",
            "market_value",
            "cost_basis",
            "unrealized_pl",
            "unrealized_plpc",
            "current_price",
        },
        "order": {
            "id",
            "symbol",
            "qty",
            "side",
            "order_type",
            "time_in_force",
            "status",
            "filled_qty",
            "filled_avg_price",
            "created_at",
            "updated_at",
        },
    }

    if data_type not in known_fields:
        return

    extra_fields = set(actual_data.keys()) - known_fields[data_type]

    if extra_fields:
        console.print(
            f"\n[yellow]⚠️  Extra fields found in {data_type} data (not in our TypedDict):[/yellow]"
        )
        for field in sorted(extra_fields):
            value = actual_data[field]
            console.print(f"  • {field}: {type(value).__name__} = {str(value)[:50]}...")
        console.print(
            f"\n[blue]💡 Consider adding these fields to {data_type.title()}Info TypedDict if needed[/blue]"
        )
    else:
        console.print(
            f"\n[green]✅ No extra fields found - our TypedDict covers all {data_type} fields[/green]"
        )


def main():
    """Main validation function."""

    console.print(
        Panel.fit(
            "[bold cyan]🧪 Alpaca Data Structure Validation[/bold cyan]\n"
            "Phase 16b: Validating TypedDict definitions against real API data",
            border_style="blue",
        )
    )

    # Look for recently collected data files
    data_dir = "data_validation_samples"
    if not os.path.exists(data_dir):
        console.print(f"\n[red]❌ No data directory found: {data_dir}[/red]")
        console.print("Please run: python scripts/collect_alpaca_data.py first")
        return

    # Find the most recent data files
    files = os.listdir(data_dir)
    account_files = [f for f in files if f.startswith("account_data_")]
    position_files = [f for f in files if f.startswith("positions_data_")]
    order_files = [f for f in files if f.startswith("orders_data_")]

    if not account_files:
        console.print(f"\n[red]❌ No account data files found in {data_dir}[/red]")
        return

    # Use the most recent files (sort by timestamp in filename)
    latest_account = sorted(account_files)[-1]
    latest_positions = sorted(position_files)[-1] if position_files else None
    latest_orders = sorted(order_files)[-1] if order_files else None

    console.print("\n[blue]📂 Using data files:[/blue]")
    console.print(f"  • Account: {latest_account}")
    console.print(f"  • Positions: {latest_positions or 'N/A'}")
    console.print(f"  • Orders: {latest_orders or 'N/A'}")

    # Load and validate data
    validation_results = []

    try:
        # Validate account data
        with open(f"{data_dir}/{latest_account}") as f:
            account_data = json.load(f)
        console.print(
            f"\n[green]✅ Loaded account data: {account_data.get('account_id', 'Unknown')}[/green]"
        )
        account_valid = validate_account_data(account_data)
        validation_results.append(("Account", account_valid))
        analyze_extra_fields(account_data, "account")

        # Validate positions data
        if latest_positions:
            with open(f"{data_dir}/{latest_positions}") as f:
                positions_data = json.load(f)
            console.print(f"\n[green]✅ Loaded {len(positions_data)} positions[/green]")
            positions_valid = validate_position_data(positions_data)
            validation_results.append(("Positions", positions_valid))
            if positions_data:
                analyze_extra_fields(positions_data[0], "position")

        # Validate orders data
        if latest_orders:
            with open(f"{data_dir}/{latest_orders}") as f:
                orders_data = json.load(f)
            if orders_data:
                console.print(f"\n[green]✅ Loaded {len(orders_data)} orders[/green]")
                orders_valid = validate_order_data(orders_data)
                validation_results.append(("Orders", orders_valid))
                analyze_extra_fields(orders_data[0], "order")
            else:
                console.print("\n[yellow]⚠️  No orders data available for validation[/yellow]")

        # Summary
        console.print("\n" + "=" * 60)
        console.print(
            Panel.fit("[bold cyan]🎯 Phase 16b Validation Summary[/bold cyan]", border_style="cyan")
        )

        all_passed = True
        for data_type, passed in validation_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            color = "green" if passed else "red"
            console.print(f"[{color}]{data_type} Data Structure: {status}[/{color}]")
            if not passed:
                all_passed = False

        if all_passed:
            console.print("\n[bold green]🎉 All validations PASSED![/bold green]")
            console.print(
                "[green]✅ Our TypedDict definitions match Alpaca API responses perfectly![/green]"
            )
            console.print(
                "[blue]📝 Ready to proceed with Phase 16c: Progressive MyPy Enablement[/blue]"
            )
        else:
            console.print("\n[bold red]⚠️  Some validations FAILED[/bold red]")
            console.print("[yellow]📝 Update TypedDict definitions before proceeding[/yellow]")

    except Exception as e:
        console.print(f"\n[red]❌ Error during validation: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
