from datetime import UTC, datetime
from types import SimpleNamespace

import pandas as pd
import pytest

from the_alchemiser.infrastructure.data_providers.data_provider import (
    UnifiedDataProvider as LegacyProvider,
)
from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade import (
    UnifiedDataProvider as FacadeProvider,
)
from the_alchemiser.services.errors.exceptions import MarketDataError

pytestmark = pytest.mark.contract

GOLDEN_DF = pd.DataFrame(
    {
        "Open": [1.0, 2.0],
        "High": [1.2, 2.2],
        "Low": [0.8, 1.8],
        "Close": [1.1, 2.1],
        "Volume": [100, 200],
    },
    index=pd.to_datetime(
        [
            datetime(2023, 1, 1, tzinfo=UTC),
            datetime(2023, 1, 2, tzinfo=UTC),
        ]
    ),
)
GOLDEN_DF.index.name = "Date"


@pytest.fixture(params=[LegacyProvider, FacadeProvider])
def provider(request, monkeypatch):
    cls = request.param
    if cls is LegacyProvider:
        monkeypatch.setattr(
            "the_alchemiser.infrastructure.secrets.secrets_manager.SecretsManager.get_alpaca_keys",
            lambda self, paper_trading=True: ("key", "secret"),
        )
        prov = cls(paper_trading=True, enable_real_time=False)

        def fake_bars(request_obj):
            bar1 = SimpleNamespace(
                open=1.0,
                high=1.2,
                low=0.8,
                close=1.1,
                volume=100,
                timestamp=datetime(2023, 1, 1, tzinfo=UTC),
            )
            bar2 = SimpleNamespace(
                open=2.0,
                high=2.2,
                low=1.8,
                close=2.1,
                volume=200,
                timestamp=datetime(2023, 1, 2, tzinfo=UTC),
            )
            return SimpleNamespace(AAPL=[bar1, bar2])

        monkeypatch.setattr(prov.data_client, "get_stock_bars", fake_bars)
        monkeypatch.setattr(
            prov.data_client,
            "get_stock_latest_quote",
            lambda req: {"AAPL": SimpleNamespace(bid_price=10.0, ask_price=10.2)},
        )
        monkeypatch.setattr(
            prov.trading_client,
            "get_account",
            lambda: SimpleNamespace(model_dump=lambda: {"equity": 1000}),
        )
        monkeypatch.setattr(
            prov.trading_client,
            "get_all_positions",
            lambda: [SimpleNamespace(model_dump=lambda: {"symbol": "AAPL", "qty": "10"})],
        )
    else:
        monkeypatch.setattr(
            "the_alchemiser.services.shared.secrets_service.SecretsService.get_alpaca_credentials",
            lambda self, paper_trading=True: ("key", "secret"),
        )
        prov = cls(paper_trading=True, enable_real_time=False)
        monkeypatch.setattr(
            prov._market_data_client,
            "get_historical_bars",
            lambda symbol, period, timeframe: GOLDEN_DF,
        )
        monkeypatch.setattr(
            prov._market_data_client,
            "get_latest_quote",
            lambda symbol: (10.0, 10.2),
        )
        # Modern path stubs
        monkeypatch.setattr(
            prov._trading_client_service,
            "get_account_info",
            lambda: {"equity": 1000},
        )
        # Positions now flow through the modern trading client service
        monkeypatch.setattr(
            prov._trading_client_service,
            "get_all_positions",
            lambda: [{"symbol": "AAPL", "qty": "10"}],
        )
    return prov


def test_get_data_parity(provider):
    df = provider.get_data("AAPL", period="1d", interval="1d")
    pd.testing.assert_frame_equal(df, GOLDEN_DF)


def test_get_current_price_parity(provider):
    price = provider.get_current_price("AAPL")
    assert price == pytest.approx(10.1)


def test_get_latest_quote_parity(provider):
    bid, ask = provider.get_latest_quote("AAPL")
    assert bid == pytest.approx(10.0)
    assert ask == pytest.approx(10.2)


def test_account_positions_parity(provider):
    info = provider.get_account_info()
    assert info == {"equity": 1000}
    positions = provider.get_positions()
    assert positions == [{"symbol": "AAPL", "qty": "10"}]


def test_error_parity(provider, monkeypatch):
    if isinstance(provider, LegacyProvider):
        monkeypatch.setattr(
            provider.data_client,
            "get_stock_bars",
            lambda req: (_ for _ in ()).throw(MarketDataError("boom")),
        )
    else:
        monkeypatch.setattr(
            provider._market_data_client,
            "get_historical_bars",
            lambda symbol, period, timeframe: (_ for _ in ()).throw(MarketDataError("boom")),
        )
    df = provider.get_data("AAPL", period="1d", interval="1d")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
