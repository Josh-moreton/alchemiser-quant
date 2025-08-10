from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from the_alchemiser.interface.cli.cli import app

runner = CliRunner()


@patch("the_alchemiser.main.run_all_signals_display", return_value=True)
def test_signal_command(mock_run) -> None:
    result = runner.invoke(app, ["signal", "--no-header"], env={"DRY_RUN": "1"})
    assert result.exit_code == 0
    mock_run.assert_called_once()


@patch("the_alchemiser.main.run_multi_strategy_trading", return_value=True)
def test_trade_paper_command(mock_run) -> None:
    result = runner.invoke(
        app,
        ["trade", "--no-header", "--force", "--ignore-market-hours"],
        env={"DRY_RUN": "1"},
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(live_trading=False, ignore_market_hours=True)


@patch("the_alchemiser.main.run_multi_strategy_trading", return_value=True)
def test_trade_live_command(mock_run) -> None:
    result = runner.invoke(
        app,
        ["trade", "--live", "--force", "--no-header", "--ignore-market-hours"],
        env={"DRY_RUN": "1"},
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(live_trading=True, ignore_market_hours=True)
