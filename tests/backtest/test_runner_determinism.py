from datetime import date
from pathlib import Path

from the_alchemiser.backtest.config_schema import BacktestConfig
from the_alchemiser.backtest.runner import BacktestRunner


def build_runner(tmp: Path) -> BacktestRunner:
    cfg_path = Path(__file__).resolve().parents[2] / "configs" / "backtest.example.yaml"
    cfg = BacktestConfig.from_yaml(cfg_path)
    cfg = cfg.model_copy(update={"start": date(2024, 1, 1), "end": date(2024, 1, 1)})
    return BacktestRunner.from_config(cfg, ["AAPL"], tmp)


def test_runner_determinism(tmp_path: Path) -> None:
    stats1 = build_runner(tmp_path / "one").run()
    stats2 = build_runner(tmp_path / "two").run()
    assert stats1 == stats2
