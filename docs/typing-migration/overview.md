# Structured Type Migration – Overview

## Executive summary
This programme converts all dict/`Any` payloads into explicit models across
interfaces, services, providers, CLI, email templates and caches. The target
is a fully typed boundary with `mypy --strict`, typed cache entries and stable
CLI/email outputs. We assume Python 3.11, Poetry tooling and existing tests.
External provider contracts stay unchanged. No CLI flags or email copy may
break without explicit versioning.

### Non-goals
- Feature work unrelated to typing
- Performance tuning beyond cache refactors
- Rewriting third‑party SDKs

### Assumptions
- All TODOs marked in repository are accurate and in scope (~96 items)
- Pydantic v1 is available; dataclasses used otherwise
- Existing tests cover current behaviour and can be extended

## Phases
| Phase | Objective |
|-------|-----------|
|5|Establish baseline models and migrate order execution flow|
|6|Backfill types in services and align return signatures|
|7|Introduce domain models for orders and results|
|8|Replace remaining `Any` in application layer|
|9|Typed provider interfaces and adapters|
|10|Typed cache keys and values|
|11|Align portfolio and position snapshots|
|12|CLI commands consume typed payloads|
|13|Email templates accept typed context|
|14|Final removal of shims and dict fallbacks|
|15|Enable `mypy --strict` and delete leftover TODOs|

## Data-flow boundaries
| Boundary | Old shape | New type |
|----------|-----------|----------|
|Broker order placement|`dict`|`OrderDetails`|
|Execution result|`dict`|`ExecutionResultDTO`|
|Strategy signal|`dict`|`SignalPayload`|
|Portfolio snapshot|`dict`|`PositionSnapshot`|
|Account info|`dict`|`AccountInfo`|
|Provider quote|`dict`|`Quote`|

## CLI commands
- `trading_executor` — phases 5,12
- `signal_analyzer` — phase 12
- `dashboard_utils` — phase 12

## Email templates
- `trading_report` — phase 13
- `portfolio` — phase 13
- `performance` — phase 13
- `signals` — phase 13
- `error_report` — phase 13

## Cache map
| Key pattern | TTL | Current | Target |
|-------------|-----|--------|--------|
|`quotes:{symbol}`|60s|raw dict|`CacheEntry[Quote]`|
|`bars:{symbol}:{interval}`|300s|raw dict|`CacheEntry[Bar]`|
|`account:{id}`|600s|raw dict|`CacheEntry[AccountInfo]`|

## Dependency graph
`Phase5 → Phase6 → Phase7 → Phase8 → Phase9 → Phase10 → Phase11 → Phase12 → Phase13 → Phase14 → Phase15`
