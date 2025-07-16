import pytest
from core.alert_service import Alert, create_alert, create_alerts_from_signal

class DummyDataProvider:
    def get_current_price(self, symbol):
        return 100.0

def test_create_alert():
    alert = create_alert('SPY', 'BUY', 'Test reason', 100.0)
    assert isinstance(alert, Alert)
    assert alert.symbol == 'SPY'
    assert alert.action == 'BUY'
    assert alert.reason == 'Test reason'
    assert alert.price == 100.0

def test_create_alerts_from_signal_basic():
    alerts = create_alerts_from_signal('SPY', 'BUY', 'Test', {}, None, DummyDataProvider(), lambda x: x)
    assert isinstance(alerts, list)
    assert len(alerts) == 1
    assert alerts[0].symbol == 'SPY'
