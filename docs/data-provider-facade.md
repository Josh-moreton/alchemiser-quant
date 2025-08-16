# Data Provider Facade

All access to market data and account information must go through the
`UnifiedDataProvider` facade located at
`the_alchemiser.infrastructure.data_providers.unified_data_provider_facade`.

The legacy `data_provider.py` module is deprecated and kept only for
parity tests during migration. Importing it will emit a
`DeprecationWarning` and eventually raise `ImportError`.

## Rationale

The facade preserves the original interface while delegating to modular
services. This enables a clean transition without behaviour drift and
provides a single integration point for future enhancements.
