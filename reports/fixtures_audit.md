# Fixtures Audit

| Fixture | Scope | Location | Notes |
|---------|-------|----------|-------|
| `disable_network` | function (autouse) | `tests/_config/network.py` | Blocks outbound network; can be bypassed with `@pytest.mark.enable_network` |
| `types_flag` | function | `tests/fixtures/flags.py` | Helper to set `TYPES_V2_ENABLED` feature flag |
| `clear_flag_env` | function (autouse) | various test modules | duplicated across files; can be replaced by `types_flag` |
