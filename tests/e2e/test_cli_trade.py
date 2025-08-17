from typing import Any

from typer.testing import CliRunner

from the_alchemiser.interface.cli.cli import app
from the_alchemiser.services.market_data.typed_data_provider_adapter import (
    TypedDataProviderAdapter,
)


def _stub_main(calls: list[Any]):
    def _inner(argv=None):
        from the_alchemiser.container.application_container import ApplicationContainer

        # Use testing container to provide dummy credentials via config
        container = ApplicationContainer.create_for_environment("test")
        dp = container.infrastructure.data_provider()
        calls.append(dp)
        return True

    return _inner


def test_trade_paper_uses_adapter(monkeypatch):
    calls: list[Any] = []
    monkeypatch.setattr("the_alchemiser.main.main", _stub_main(calls))
    runner = CliRunner()
    result = runner.invoke(app, ["trade"])
    assert result.exit_code == 0
    assert isinstance(calls[0], TypedDataProviderAdapter)


def test_trade_live_dry_run(monkeypatch):
    calls: list[Any] = []
    monkeypatch.setattr("the_alchemiser.main.main", _stub_main(calls))
    runner = CliRunner()
    result = runner.invoke(app, ["trade", "--live"])
    assert result.exit_code == 0
    assert isinstance(calls[0], TypedDataProviderAdapter)
