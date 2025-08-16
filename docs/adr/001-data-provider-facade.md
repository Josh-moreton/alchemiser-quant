# ADR 001: Data Provider Facade

## Context
Legacy `data_provider.py` coupled market data and trading logic. A facade
now wraps the modular services so existing callers can migrate without
behaviour changes.

## Decision
All code must import `UnifiedDataProvider` from
`infrastructure/data_providers/unified_data_provider_facade`. The legacy
module emits a `DeprecationWarning` and will raise `ImportError` once
`IMPORTERROR_ON_LEGACY=1` is set in CI.

## Consequences
- Centralised data access via facade.
- Guard rails prevent reintroducing the old module.
- After two to four weeks of green builds the legacy module will be
removed.
