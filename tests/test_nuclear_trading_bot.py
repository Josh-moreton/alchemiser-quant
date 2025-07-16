import pytest
from core.nuclear_trading_bot import NuclearTradingBot

class DummyDataProvider:
    def get_data(self, symbol, period="1y", interval="1d"):
        import pandas as pd
        import numpy as np
        idx = pd.date_range("2024-01-01", periods=100)
        df = pd.DataFrame({"Close": np.linspace(100, 200, 100)}, index=idx)
        return df
    def get_current_price(self, symbol):
        return 123.45

def test_run_once_returns_signal(monkeypatch):
    bot = NuclearTradingBot()
    # Patch data provider to avoid real API calls
    bot.strategy.data_provider = DummyDataProvider()
    bot.data_provider = DummyDataProvider()
    bot.ensure_scalar_price = lambda x: float(x)
    # Patch alert logging to avoid file I/O
    from core import alert_service
    monkeypatch.setattr(alert_service, "log_alert_to_file", lambda alert, log_file_path=None: None)
    monkeypatch.setattr(alert_service, "log_alerts_to_file", lambda alerts, log_file_path=None: None)
    signal = bot.run_once()
    assert signal is not None
    assert isinstance(signal, tuple)
    assert len(signal) == 3
