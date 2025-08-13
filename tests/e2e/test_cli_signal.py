from the_alchemiser.interface.cli.cli import app


def test_signal_cli_invokes_main_with_di(monkeypatch, cli_runner):
    """CLI signal command should pass the DI flag to main."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)
    result = cli_runner.invoke(app, ["signal", "--no-header", "--use-di"])
    assert result.exit_code == 0
    assert called["argv"] == ["signal", "--use-di"]
