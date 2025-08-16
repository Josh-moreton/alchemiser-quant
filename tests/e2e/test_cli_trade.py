from typing import List

import pytest
from typer.testing import CliRunner

from the_alchemiser.interface.cli.cli import app
from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade import (
    UnifiedDataProviderFacade,
)


def _stub_main(calls: List[UnifiedDataProviderFacade]):
    def _inner(argv=None):
        from the_alchemiser.container.application_container import ApplicationContainer
        from the_alchemiser.services.shared.secrets_service import SecretsService

        # Avoid real credential lookup
        SecretsService.get_alpaca_credentials = lambda self, paper_trading: ("key", "secret")
        container = ApplicationContainer()
        dp = container.infrastructure.data_provider()
        calls.append(dp)
        return True

    return _inner


def test_trade_paper_uses_facade(monkeypatch):
    calls: List[UnifiedDataProviderFacade] = []
    monkeypatch.setattr("the_alchemiser.main.main", _stub_main(calls))
    runner = CliRunner()
    result = runner.invoke(app, ["trade"])
    assert result.exit_code == 0
    assert isinstance(calls[0], UnifiedDataProviderFacade)


def test_trade_live_dry_run(monkeypatch):
    calls: List[UnifiedDataProviderFacade] = []
    monkeypatch.setattr("the_alchemiser.main.main", _stub_main(calls))
    runner = CliRunner()
    result = runner.invoke(app, ["trade", "--live"])
    assert result.exit_code == 0
    assert isinstance(calls[0], UnifiedDataProviderFacade)
