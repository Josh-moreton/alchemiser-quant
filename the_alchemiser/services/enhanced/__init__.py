"""Deprecated package shim.

The real modules have been moved to structured locations under:
- the_alchemiser.services.account
- the_alchemiser.services.market_data
- the_alchemiser.services.trading

Please update imports using the migration script:
    poetry run python scripts/update_imports_after_services_reorg.py --apply
"""

__all__: list[str] = []
