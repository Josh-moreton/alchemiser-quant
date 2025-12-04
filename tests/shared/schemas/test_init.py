#!/usr/bin/env python3
"""Tests for shared.schemas.__init__.py package exports.

Business Unit: shared | Status: current

Verifies that the schemas package facade:
- Exports all declared symbols in __all__
- All exports are importable
- __all__ is alphabetically sorted for maintainability
- Module has proper documentation
- Backward compatibility for moved symbols works correctly
"""

from __future__ import annotations

import warnings

import pytest


def test_all_exports_are_importable() -> None:
    """Verify all items in __all__ can be imported."""
    from the_alchemiser.shared import schemas

    missing_exports = []
    for name in schemas.__all__:
        if not hasattr(schemas, name):
            missing_exports.append(name)

    assert not missing_exports, (
        f"The following items are in __all__ but not importable: {missing_exports}"
    )


def test_all_is_sorted() -> None:
    """Verify __all__ is alphabetically sorted for maintainability."""
    from the_alchemiser.shared import schemas

    sorted_all = sorted(schemas.__all__)
    assert schemas.__all__ == sorted_all, (
        "__all__ should be alphabetically sorted for maintainability. "
        f"Expected order: {sorted_all[:5]}... but got: {schemas.__all__[:5]}..."
    )


def test_module_docstring() -> None:
    """Verify module has proper docstring with business unit."""
    from the_alchemiser.shared import schemas

    assert schemas.__doc__ is not None, "Module should have docstring"
    assert "Business Unit:" in schemas.__doc__, "Docstring should have Business Unit header"
    assert "shared" in schemas.__doc__, "Business Unit should be 'shared'"
    assert "Status:" in schemas.__doc__, "Docstring should have Status indicator"


def test_import_common_schemas() -> None:
    """Verify common schema classes can be imported and instantiated."""
    from the_alchemiser.shared.schemas import (
        Error,
        Result,
    )

    # Test Result base class
    assert Result is not None
    assert hasattr(Result, "model_validate")  # Pydantic model

    # Test Error schema
    assert Error is not None
    assert hasattr(Error, "model_validate")


def test_import_account_schemas() -> None:
    """Verify account-related schemas are importable."""
    from the_alchemiser.shared.schemas import (
        AccountMetrics,
        AccountSummary,
        BuyingPowerResult,
    )

    assert AccountMetrics is not None
    assert AccountSummary is not None
    assert BuyingPowerResult is not None


def test_import_execution_schemas() -> None:
    """Verify execution-related schemas are importable."""
    from the_alchemiser.shared.schemas import (
        ExecutedOrder,
        ExecutionReport,
        ExecutionResult,
        ExecutionStatus,
    )

    assert ExecutedOrder is not None
    assert ExecutionReport is not None
    assert ExecutionResult is not None
    assert ExecutionStatus is not None


def test_import_market_data_schemas() -> None:
    """Verify market data schemas are importable."""
    from the_alchemiser.shared.schemas import (
        MarketBar,
        MarketData,
        MarketStatusResult,
        PriceResult,
    )

    assert MarketBar is not None
    assert MarketData is not None
    assert MarketStatusResult is not None
    assert PriceResult is not None


def test_import_portfolio_schemas() -> None:
    """Verify portfolio-related schemas are importable."""
    from the_alchemiser.shared.schemas import (
        PortfolioMetrics,
        PortfolioState,
        Position,
    )

    assert PortfolioMetrics is not None
    assert PortfolioState is not None
    assert Position is not None


def test_import_trade_schemas() -> None:
    """Verify trade-related schemas are importable."""
    from the_alchemiser.shared.schemas import (
        RebalancePlan,
        TradeLedger,
        TradeRunResult,
    )

    assert RebalancePlan is not None
    assert TradeLedger is not None
    assert TradeRunResult is not None


def test_import_utility_functions() -> None:
    """Verify utility functions are importable and callable."""
    from the_alchemiser.shared.schemas import (
        create_failure_result,
        create_success_result,
    )

    assert callable(create_failure_result)
    assert callable(create_success_result)


def test_error_context_data_backward_compatibility() -> None:
    """Verify ErrorContextData import with deprecation warning.

    ErrorContextData was moved to shared.errors.context in v2.18.0.
    The import should work but emit a deprecation warning.
    Scheduled for removal in v3.0.0.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import ErrorContextData through the facade
        from the_alchemiser.shared.schemas import ErrorContextData

        # Verify import worked
        assert ErrorContextData is not None
        assert hasattr(ErrorContextData, "model_validate")

        # Verify deprecation warning was issued
        assert len(w) >= 1, "Should emit at least one deprecation warning"
        deprecation_warnings = [
            warning for warning in w if issubclass(warning.category, DeprecationWarning)
        ]
        assert len(deprecation_warnings) >= 1, "Should have at least one DeprecationWarning"

        # Find the ErrorContextData deprecation warning
        error_context_warnings = [
            warning
            for warning in deprecation_warnings
            if "deprecated" in str(warning.message).lower()
            and "shared.errors.context" in str(warning.message)
        ]
        assert len(error_context_warnings) >= 1, "Should have ErrorContextData deprecation warning"
        assert "v3.0.0" in str(error_context_warnings[0].message)


def test_error_context_data_direct_import_no_warning() -> None:
    """Verify direct import from new location works without warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import from correct location (no warning expected)
        from the_alchemiser.shared.errors.context import ErrorContextData

        assert ErrorContextData is not None
        assert len(w) == 0, "Direct import from new location should not emit warnings"


def test_no_import_star() -> None:
    """Verify module does not use 'import *' (banned by guidelines)."""
    import inspect

    from the_alchemiser.shared import schemas

    source = inspect.getsource(schemas)
    assert "import *" not in source, "Module should not use 'import *'"


def test_export_count() -> None:
    """Verify expected number of exports (regression test)."""
    from the_alchemiser.shared import schemas

    # As of 2025-06-20, there are 66 exports (added StrategyLot, StrategyLotSummary, LotExitRecord)
    # This test will catch unintended additions/removals
    assert len(schemas.__all__) == 66, (
        f"Expected 66 exports in __all__, found {len(schemas.__all__)}. "
        "If this is intentional, update the test."
    )


def test_all_schemas_are_pydantic_models() -> None:
    """Verify all schema classes (not enums/functions) are Pydantic models."""
    from the_alchemiser.shared import schemas

    # Skip utility functions and enums
    skip_names = {
        "create_failure_result",
        "create_success_result",
        "ExecutionStatus",
        "OrderAction",
        "TradingMode",
        "WebSocketStatus",
    }

    for name in schemas.__all__:
        if name in skip_names:
            continue

        obj = getattr(schemas, name)

        # Check if it's a class and has Pydantic model_validate method
        if isinstance(obj, type):
            assert hasattr(obj, "model_validate"), (
                f"{name} should be a Pydantic model with model_validate method"
            )


def test_invalid_attribute_raises_error() -> None:
    """Verify accessing non-existent attributes raises AttributeError."""
    from the_alchemiser.shared import schemas

    with pytest.raises(AttributeError, match="has no attribute 'NonExistentSchema'"):
        _ = schemas.NonExistentSchema  # type: ignore[attr-defined]


def test_module_has_getattr() -> None:
    """Verify module implements __getattr__ for backward compatibility."""
    from the_alchemiser.shared import schemas

    assert hasattr(schemas, "__getattr__"), (
        "Module should implement __getattr__ for backward compatibility"
    )
