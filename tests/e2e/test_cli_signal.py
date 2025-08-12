from the_alchemiser.interface.cli.cli import app


def test_signal_cli_invokes_main(monkeypatch, cli_runner):
    """CLI signal command should invoke main with signal argument."""
    called = {}

    def fake_main(argv=None, settings=None):
        called["argv"] = argv
        return True

    monkeypatch.setattr("the_alchemiser.main.main", fake_main)
    result = cli_runner.invoke(app, ["signal", "--no-header"])
    assert result.exit_code == 0
    assert called["argv"] == ["signal"]
