"""CLI entry-point for backtests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from .config_schema import BacktestConfig
from .runner import BacktestRunner

app = typer.Typer(help="The Alchemiser CLI")
backtest_app = typer.Typer(help="Backtesting utilities", invoke_without_command=True)
app.add_typer(backtest_app, name="backtest")


@backtest_app.callback()
def run(
    start: datetime = typer.Option(..., help="Start date"),
    end: datetime = typer.Option(..., help="End date"),
    symbols: str = typer.Option(..., help="Comma separated symbols"),
    config: Path = typer.Option(..., help="YAML config file"),
    universe: Path | None = typer.Option(None, help="Universe CSV"),
    bar_interval: str = typer.Option("1m", help="Bar interval"),
) -> None:
    """Run a simple backtest."""

    cfg = BacktestConfig.from_yaml(config)
    cfg = cfg.model_copy(
        update={"start": start.date(), "end": end.date(), "bar_interval": bar_interval}
    )
    symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]
    artefact_dir = Path("artefacts") / datetime.now().strftime("%Y%m%d_%H%M%S")
    runner = BacktestRunner.from_config(cfg, symbols_list, artefact_dir)
    runner.run()
    typer.echo(str(artefact_dir))
