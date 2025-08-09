from the_alchemiser.services import (
    AccountService,
    CacheManager,
    ConfigService,
    MarketDataClient,
    SecretsService,
    StreamingService,
    TradingClientService,
)


def test_public_api_imports():
    assert all(
        obj is not None
        for obj in (
            AccountService,
            CacheManager,
            ConfigService,
            MarketDataClient,
            SecretsService,
            StreamingService,
            TradingClientService,
        )
    )
