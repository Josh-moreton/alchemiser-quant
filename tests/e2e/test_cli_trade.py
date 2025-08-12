"""Tests for trade CLI command covering paper and live modes.

Rationale: Close coverage gaps for CLI trade paths by faking main and
asserting argument propagation, user feedback and error handling.
"""

import pytest

from the_alchemiser.interface.cli.cli import app


@pytest.fixture(autouse=True)
def disable_sleep(monkeypatch):
    """Make tests run swiftly by removing actual waiting."""
    monkeypatch.setattr("time.sleep", lambda *_: None)


def test_trade_cli_invokes_main(monkeypatch, cli_runner):
    """Paper trading should call main with trade arguments only."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)

    result = cli_runner.invoke(app, ["trade", "--no-header"])

    assert result.exit_code == 0
    assert called["argv"] == ["trade"]
    assert "trading completed successfully" in result.stdout


def test_trade_cli_live_invokes_main(monkeypatch, cli_runner):
    """Live trading forwards --live flag and reports success."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)

    result = cli_runner.invoke(
        app, ["trade", "--live", "--force", "--no-header"]
    )

    assert result.exit_code == 0
    assert called["argv"] == ["trade", "--live"]
    assert "LIVE trading completed successfully" in result.stdout


def test_trade_cli_failure_path(monkeypatch, cli_runner):
    """When main reports failure the CLI should exit with error."""

    def fake_main(argv=None, settings=None):
        return False

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)

    result = cli_runner.invoke(app, ["trade", "--no-header"])

    assert result.exit_code == 1
    assert "trading failed" in result.stdout
