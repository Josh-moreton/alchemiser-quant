import pytest

from the_alchemiser.shared.config.config import Settings


@pytest.mark.unit
def test_strategy_loader_uses_dev_packaged_defaults(monkeypatch):
    monkeypatch.setenv("APP__STAGE", "dev")
    monkeypatch.delenv("STRATEGY__DSL_FILES", raising=False)
    monkeypatch.delenv("STRATEGY__DSL_ALLOCATIONS", raising=False)

    s = Settings()
    assert s.strategy.dsl_files, "Expected dev packaged DSL files"
    assert s.strategy.dsl_allocations, "Expected dev packaged allocations"
    # keys should match files
    assert set(s.strategy.dsl_files) == set(s.strategy.dsl_allocations.keys())
    # weights roughly sum to 1.0
    total = sum(s.strategy.dsl_allocations.values())
    assert 0.99 <= total <= 1.01


@pytest.mark.unit
def test_strategy_loader_uses_prod_packaged_defaults(monkeypatch):
    monkeypatch.setenv("APP__STAGE", "prod")
    monkeypatch.delenv("STRATEGY__DSL_FILES", raising=False)
    monkeypatch.delenv("STRATEGY__DSL_ALLOCATIONS", raising=False)

    s = Settings()
    assert s.strategy.dsl_files, "Expected prod packaged DSL files"
    assert s.strategy.dsl_allocations, "Expected prod packaged allocations"
    assert set(s.strategy.dsl_files) == set(s.strategy.dsl_allocations.keys())
    total = sum(s.strategy.dsl_allocations.values())
    assert 0.99 <= total <= 1.01
