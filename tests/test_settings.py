import os
from tempfile import NamedTemporaryFile
from the_alchemiser.core.config import load_settings


def test_env_overrides_yaml(monkeypatch):
    yaml_content = """
alpaca:
  endpoint: "http://yaml-endpoint"
"""
    with NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(yaml_content)
        path = tmp.name

    monkeypatch.setenv("ALPACA__endpoint", "http://env-endpoint")
    settings = load_settings(path)
    assert settings.alpaca.endpoint == "http://env-endpoint"
    os.remove(path)


def test_defaults_applied(monkeypatch):
    monkeypatch.delenv("ALPACA__endpoint", raising=False)
    settings = load_settings(None)
    assert settings.alpaca.cash_reserve_pct == 0.05
