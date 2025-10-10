#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Test shared.math package public API exports.

Verifies that the public API surface of the math utilities package is complete
and correctly exported through __init__.py.
"""


class TestMathPackageExports:
    """Test shared.math package __init__.py exports."""

    def test_all_exports_available(self) -> None:
        """Test that all symbols in __all__ are importable from package root."""
        from the_alchemiser.shared import math

        # Verify __all__ is defined
        assert hasattr(math, "__all__")
        assert isinstance(math.__all__, list)
        assert len(math.__all__) == 18  # Total count of exported symbols

        # Verify all symbols in __all__ are actually exported
        for symbol in math.__all__:
            assert hasattr(math, symbol), f"Symbol {symbol} not found in package exports"

    def test_math_utils_functions_importable(self) -> None:
        """Test that statistical utility functions can be imported from package root."""
        from the_alchemiser.shared.math import (
            calculate_ensemble_score,
            calculate_moving_average,
            calculate_moving_average_return,
            calculate_percentage_change,
            calculate_rolling_metric,
            calculate_stdev_returns,
            normalize_to_range,
            safe_division,
        )

        # Verify they are callable
        assert callable(calculate_ensemble_score)
        assert callable(calculate_moving_average)
        assert callable(calculate_moving_average_return)
        assert callable(calculate_percentage_change)
        assert callable(calculate_rolling_metric)
        assert callable(calculate_stdev_returns)
        assert callable(normalize_to_range)
        assert callable(safe_division)

    def test_trading_math_functions_importable(self) -> None:
        """Test that trading calculation functions can be imported from package root."""
        from the_alchemiser.shared.math import (
            calculate_allocation_discrepancy,
            calculate_dynamic_limit_price,
            calculate_dynamic_limit_price_with_symbol,
            calculate_position_size,
            calculate_rebalance_amounts,
            calculate_slippage_buffer,
        )

        # Verify they are callable
        assert callable(calculate_allocation_discrepancy)
        assert callable(calculate_dynamic_limit_price)
        assert callable(calculate_dynamic_limit_price_with_symbol)
        assert callable(calculate_position_size)
        assert callable(calculate_rebalance_amounts)
        assert callable(calculate_slippage_buffer)

    def test_trading_math_protocol_importable(self) -> None:
        """Test that TickSizeProvider protocol can be imported from package root."""
        from the_alchemiser.shared.math import TickSizeProvider

        # Verify it's a type (Protocol)
        assert TickSizeProvider is not None

    def test_num_functions_importable(self) -> None:
        """Test that float comparison utilities can be imported from package root."""
        from the_alchemiser.shared.math import floats_equal

        assert callable(floats_equal)

    def test_asset_info_classes_importable(self) -> None:
        """Test that asset metadata classes can be imported from package root."""
        # Verify AssetType is an enum
        from enum import Enum

        from the_alchemiser.shared.math import AssetType, FractionabilityDetector

        assert issubclass(AssetType, Enum)

        # Verify FractionabilityDetector is a class
        assert isinstance(FractionabilityDetector, type)

    def test_all_matches_imports(self) -> None:
        """Test that __all__ list matches actual imported symbols."""
        from the_alchemiser.shared import math

        expected_exports = {
            # From math_utils
            "calculate_ensemble_score",
            "calculate_moving_average",
            "calculate_moving_average_return",
            "calculate_percentage_change",
            "calculate_rolling_metric",
            "calculate_stdev_returns",
            "normalize_to_range",
            "safe_division",
            # From trading_math
            "calculate_allocation_discrepancy",
            "calculate_dynamic_limit_price",
            "calculate_dynamic_limit_price_with_symbol",
            "calculate_position_size",
            "calculate_rebalance_amounts",
            "calculate_slippage_buffer",
            "TickSizeProvider",
            # From num
            "floats_equal",
            # From asset_info
            "AssetType",
            "FractionabilityDetector",
        }

        actual_exports = set(math.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. "
            f"Expected: {expected_exports}, "
            f"Got: {actual_exports}, "
            f"Missing: {expected_exports - actual_exports}, "
            f"Extra: {actual_exports - expected_exports}"
        )

    def test_no_private_exports(self) -> None:
        """Test that __all__ does not export any private symbols."""
        from the_alchemiser.shared import math

        for symbol in math.__all__:
            assert not symbol.startswith("_"), f"Private symbol {symbol} should not be in __all__"
