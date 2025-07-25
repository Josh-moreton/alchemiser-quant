import datetime as dt
import typer
from rich.console import Console
from tests.test_backtest import run_backtest

console = Console()


def run(
    start: str = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(1000, help="Initial equity for backtest"),
    price_type: str = typer.Option("close", help="Price type: close, open, or mid")
):
    """Run a backtest for the given date range and price type."""
    start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
    end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    console.print(f"[bold green]Running backtest from {start} to {end} using {price_type} prices...")
    run_backtest(start_dt, end_dt, initial_equity=initial_equity, price_type=price_type)

if __name__ == "__main__":
    typer.run(run)
