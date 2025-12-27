# Shared Module Changelog

## [1.0.0] - Contract versioning bootstrap
- Added `CONTRACT_VERSION` marker (`1.0.0`) for shared event and schema contracts.
- Annotated shared events and DTOs used by strategy_v2, portfolio_v2, execution_v2, and orchestration with `__event_version__` / `__schema_version__` and aligned schema_version defaults.
- Documented contract coverage in `CONTRACTS.md` and added compatibility tests under `tests/<module>/`.
- Hardened import rules to prevent new cross-module dependencies outside `shared/`.
