from the_alchemiser.interface.cli.cli import app


def test_signal_cli_default_uses_di(monkeypatch, cli_runner):
    """CLI signal command should use DI by default."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)
    result = cli_runner.invoke(app, ["signal", "--no-header"])
    assert result.exit_code == 0
    assert called["argv"] == ["signal"]  # No --legacy flag means DI is used


def test_signal_cli_legacy_mode(monkeypatch, cli_runner):
    """CLI signal command should use legacy mode when --legacy flag is provided."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)
    result = cli_runner.invoke(app, ["signal", "--no-header", "--legacy"])
    assert result.exit_code == 0
    assert called["argv"] == ["signal", "--legacy"]
