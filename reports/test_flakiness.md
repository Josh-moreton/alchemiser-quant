# Suspected Flaky Tests

| Test File | Potential Cause | Recommendation |
|-----------|-----------------|---------------|
| `tests/unit/services/trading/test_place_limit_order_flag.py` & `test_place_market_order_flag.py` | manual monkeypatching of `builtins.__import__` and dummy classes may leak between tests | use fixtures to patch cleanly and reset imports |
| Network-dependent tests | None present due to network guard | use `@pytest.mark.enable_network` when needed |
