from pathlib import Path

from typer.testing import CliRunner

from the_alchemiser.backtest.cli import app


def test_cli_smoke() -> None:
    runner = CliRunner()
    cfg = Path(__file__).resolve().parents[2] / "configs" / "backtest.example.yaml"
    with runner.isolated_filesystem():
        Path("config.yaml").write_text(cfg.read_text())
        result = runner.invoke(
            app,
            [
                "backtest",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--symbols",
                "AAPL",
                "--config",
                "config.yaml",
            ],
        )
        assert result.exit_code == 0, result.stdout
        artefact_dir = Path(result.stdout.strip())
        assert artefact_dir.joinpath("orders.csv").exists()
        assert artefact_dir.joinpath("fills.csv").exists()
        assert artefact_dir.joinpath("stats.json").exists()
