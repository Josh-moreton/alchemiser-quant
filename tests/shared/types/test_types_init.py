#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared/types/__init__.py module interface.

Validates:
- All exports in __all__ are importable
- No unintended exports (API surface control)
- Re-exported types match source types
- Import mechanics work correctly
- Deprecated types are not exported

This test suite ensures the types module maintains a clean public API
and prevents accidental breakage of the module interface.
"""

from __future__ import annotations

from typing import get_type_hints

import pytest


class TestTypesModuleInterface:
    """Test suite for types module public API."""

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ list matches expected exports."""
        from the_alchemiser.shared import types

        # Check __all__ exists
        assert hasattr(types, "__all__"), "Module must define __all__"

        # Updated for v2.10.7+: Removed deprecated types
        # BrokerOrderSide, BrokerTimeInForce, OrderSideType, TimeInForceType removed
        # StrategySignal moved to shared.schemas
        expected_exports = {
            "MarketDataPort",
            "Quantity",
            "StrategyEngine",
            "StrategyType",
        }
        actual_exports = set(types.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. Expected: {expected_exports}, Got: {actual_exports}"
        )

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import types

        for name in types.__all__:
            assert hasattr(types, name), f"Export '{name}' in __all__ but not importable"
            obj = getattr(types, name)
            assert obj is not None, f"Export '{name}' is None"

    @pytest.mark.skip(reason="BrokerOrderSide removed in v2.10.7+ - use Alpaca SDK enums directly")
    def test_broker_order_side_export(self) -> None:
        """Test BrokerOrderSide enum is correctly exported."""
        from the_alchemiser.shared.types import BrokerOrderSide
        from the_alchemiser.shared.types.broker_enums import (
            BrokerOrderSide as SourceBrokerOrderSide,
        )

        # Verify it's the same enum (not a copy)
        assert BrokerOrderSide is SourceBrokerOrderSide
        assert BrokerOrderSide.__name__ == "BrokerOrderSide"
        assert hasattr(BrokerOrderSide, "BUY")
        assert hasattr(BrokerOrderSide, "SELL")

    @pytest.mark.skip(
        reason="BrokerTimeInForce removed in v2.10.7+ - use Alpaca SDK enums directly"
    )
    def test_broker_time_in_force_export(self) -> None:
        """Test BrokerTimeInForce enum is correctly exported."""
        from the_alchemiser.shared.types import BrokerTimeInForce
        from the_alchemiser.shared.types.broker_enums import (
            BrokerTimeInForce as SourceBrokerTimeInForce,
        )

        # Verify it's the same enum (not a copy)
        # Note: Direct identity check may fail due to reload, check by name and members
        assert BrokerTimeInForce.__name__ == "BrokerTimeInForce"
        assert SourceBrokerTimeInForce.__name__ == "BrokerTimeInForce"
        assert hasattr(BrokerTimeInForce, "DAY")
        assert hasattr(BrokerTimeInForce, "GTC")

    def test_market_data_port_export(self) -> None:
        """Test MarketDataPort protocol is correctly exported."""
        from the_alchemiser.shared.types import MarketDataPort
        from the_alchemiser.shared.types.market_data_port import (
            MarketDataPort as SourceMarketDataPort,
        )

        # Verify it's the same protocol (not a copy)
        assert MarketDataPort is SourceMarketDataPort
        assert MarketDataPort.__name__ == "MarketDataPort"

    def test_quantity_export(self) -> None:
        """Test Quantity value object is correctly exported."""
        from the_alchemiser.shared.types import Quantity
        from the_alchemiser.shared.types.quantity import Quantity as SourceQuantity

        # Verify it's the same class (not a copy)
        assert Quantity is SourceQuantity
        assert Quantity.__name__ == "Quantity"

    def test_strategy_engine_export(self) -> None:
        """Test StrategyEngine protocol is correctly exported."""
        from the_alchemiser.shared.types import StrategyEngine
        from the_alchemiser.shared.types.strategy_protocol import (
            StrategyEngine as SourceStrategyEngine,
        )

        # Verify it's the same protocol (not a copy)
        assert StrategyEngine is SourceStrategyEngine
        assert StrategyEngine.__name__ == "StrategyEngine"

    @pytest.mark.skip(reason="StrategySignal moved to shared.schemas in v2.10.7+")
    def test_strategy_signal_export(self) -> None:
        """Test StrategySignal value object is correctly exported."""
        from the_alchemiser.shared.types import StrategySignal
        from the_alchemiser.shared.types.strategy_value_objects import (
            StrategySignal as SourceStrategySignal,
        )

        # Verify it's the same class (not a copy)
        assert StrategySignal is SourceStrategySignal
        assert StrategySignal.__name__ == "StrategySignal"

    def test_strategy_type_export(self) -> None:
        """Test StrategyType enum is correctly exported."""
        from the_alchemiser.shared.types import StrategyType
        from the_alchemiser.shared.types.strategy_types import (
            StrategyType as SourceStrategyType,
        )

        # Verify it's the same enum (not a copy)
        assert StrategyType is SourceStrategyType
        assert StrategyType.__name__ == "StrategyType"

    @pytest.mark.skip(reason="Type aliases removed in v2.10.7+ - use Alpaca SDK enums directly")
    def test_type_aliases_export(self) -> None:
        """Test that type aliases are correctly exported."""
        from the_alchemiser.shared.types import OrderSideType, TimeInForceType
        from the_alchemiser.shared.types.broker_enums import (
            OrderSideType as SourceOrderSideType,
        )
        from the_alchemiser.shared.types.broker_enums import (
            TimeInForceType as SourceTimeInForceType,
        )

        # Verify type aliases are the same objects
        assert OrderSideType is SourceOrderSideType
        assert TimeInForceType is SourceTimeInForceType

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no leaks)."""
        from the_alchemiser.shared import types

        # Get all public symbols (excluding dunder)
        public_symbols = [name for name in dir(types) if not name.startswith("_")]

        # Get __all__
        declared_exports = set(types.__all__)

        # Public symbols should only include __all__ items (and no extras)
        extra_exports = set(public_symbols) - declared_exports

        # Allow module-level metadata, stdlib imports, and submodules
        # Note: Python imports make submodules visible even if not in __all__
        # This is expected behavior for facade modules
        allowed_extras = {
            "annotations",  # from __future__ import annotations
            # Submodules (imported by this module or transitively)
            "account",
            "broker_enums",
            "market_data",
            "market_data_port",
            "money",
            "percentage",
            "quantity",
            "quote",
            "strategy_protocol",
            "strategy_registry",
            "strategy_types",
            "strategy_value_objects",
            "time_in_force",  # Imported but not exported (deprecated)
            # Classes imported but not exported
            "TimeInForce",  # Imported from time_in_force (noqa)
        }

        unexpected_exports = extra_exports - allowed_extras

        assert not unexpected_exports, (
            f"Module exports unexpected symbols: {unexpected_exports}. "
            f"These should either be added to __all__ or made private with _ prefix."
        )

    def test_star_import_behavior(self) -> None:
        """Test that 'from types import *' only imports __all__ items."""
        # Create a new module namespace for testing
        test_namespace: dict[str, object] = {}

        # Execute star import in clean namespace
        exec("from the_alchemiser.shared.types import *", test_namespace)

        # Get imported names (excluding builtins)
        imported_names = {name for name in test_namespace if not name.startswith("_")}

        # Expected imports
        from the_alchemiser.shared import types

        expected_names = set(types.__all__)

        assert imported_names == expected_names, (
            f"Star import mismatch. "
            f"Expected: {expected_names}, "
            f"Got: {imported_names}, "
            f"Missing: {expected_names - imported_names}, "
            f"Extra: {imported_names - expected_names}"
        )

    def test_module_has_docstring(self) -> None:
        """Test that the module has a proper docstring."""
        from the_alchemiser.shared import types

        assert types.__doc__ is not None, "Module must have a docstring"
        assert len(types.__doc__) > 0, "Module docstring must not be empty"
        assert "Business Unit: shared" in types.__doc__, (
            "Module docstring must include 'Business Unit: shared'"
        )
        assert "Status: current" in types.__doc__, "Module docstring must include 'Status: current'"

    def test_exports_are_types_or_protocols(self) -> None:
        """Test that all exports are types, protocols, or type aliases."""
        import typing

        from the_alchemiser.shared import types

        for name in types.__all__:
            obj = getattr(types, name)

            # Should be a class, protocol, or type alias
            is_type = isinstance(obj, type)
            is_protocol = hasattr(obj, "_is_protocol")
            # Type aliases are tricky - they're either typing constructs or raw types
            is_type_alias = (
                hasattr(typing, "get_origin") and typing.get_origin(obj) is not None
            ) or isinstance(obj, type)

            assert is_type or is_protocol or is_type_alias, (
                f"Export '{name}' should be a type/protocol/alias, got {type(obj)}"
            )

    @pytest.mark.skip(reason="StrategySignal moved to shared.schemas in v2.10.7+")
    def test_relative_imports_work(self) -> None:
        """Test that relative imports within the module work correctly."""
        # Import from module directly
        from the_alchemiser.shared.types import StrategySignal

        # Import from submodule
        from the_alchemiser.shared.types.strategy_value_objects import (
            StrategySignal as DirectStrategySignal,
        )

        # Should be the same object
        assert StrategySignal is DirectStrategySignal

    @pytest.mark.skip(reason="StrategySignal moved to shared.schemas in v2.10.7+")
    def test_imports_are_deterministic(self) -> None:
        """Test that imports are deterministic (same result on re-import)."""
        # First import
        from the_alchemiser.shared.types import StrategySignal as First

        # Re-import (should use cached module)
        from the_alchemiser.shared.types import StrategySignal as Second

        # Should be identical
        assert First is Second

    def test_no_circular_imports(self) -> None:
        """Test that importing the module doesn't cause circular import issues."""
        # This test passes if the import succeeds without errors
        import importlib

        # Force reload to test import mechanics
        from the_alchemiser.shared import types

        importlib.reload(types)

        # Should still be able to access exports
        assert hasattr(types, "__all__")
        assert len(types.__all__) > 0


class TestDeprecatedTypes:
    """Test suite for deprecated type handling."""

    def test_time_in_force_not_exported(self) -> None:
        """Test that TimeInForce is NOT exported (deprecated)."""
        from the_alchemiser.shared import types

        # Should not be in __all__
        assert "TimeInForce" not in types.__all__, (
            "TimeInForce should not be in __all__ (deprecated as of v2.10.7)"
        )

        # Should not be accessible via star import
        test_namespace: dict[str, object] = {}
        exec("from the_alchemiser.shared.types import *", test_namespace)
        assert "TimeInForce" not in test_namespace, (
            "TimeInForce should not be imported via star import"
        )

    def test_time_in_force_import_via_submodule(self) -> None:
        """Test that TimeInForce can still be imported from submodule (deprecated)."""
        # Should still be importable from submodule for backward compatibility
        from the_alchemiser.shared.types.time_in_force import TimeInForce

        # Verify it exists and is the deprecated class
        assert TimeInForce is not None
        # TimeInForce is a dataclass with a 'value' field, not an attribute
        # Check if it's a dataclass
        import dataclasses

        assert dataclasses.is_dataclass(TimeInForce)

    def test_time_in_force_raises_deprecation_warning(self) -> None:
        """Test that TimeInForce raises DeprecationWarning on instantiation."""
        from the_alchemiser.shared.types.time_in_force import TimeInForce

        with pytest.warns(DeprecationWarning, match="TimeInForce is deprecated"):
            # Should raise deprecation warning
            tif = TimeInForce(value="day")
            assert tif.value == "day"


class TestModuleBoundaries:
    """Test suite for module boundary enforcement."""

    def test_no_imports_from_business_modules(self) -> None:
        """Test that types module doesn't import from business modules."""
        import inspect

        from the_alchemiser.shared import types

        # Get source file
        source_file = inspect.getsourcefile(types)
        assert source_file is not None

        with open(source_file) as f:
            source_code = f.read()

        # Should not import from business modules
        forbidden_imports = [
            "from the_alchemiser.strategy_v2",
            "from the_alchemiser.portfolio_v2",
            "from the_alchemiser.execution_v2",
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in source_code, (
                f"types module should not import from business modules: {forbidden}"
            )

    def test_only_relative_imports(self) -> None:
        """Test that all imports from types submodules are relative."""
        import inspect

        from the_alchemiser.shared import types

        source_file = inspect.getsourcefile(types)
        assert source_file is not None

        with open(source_file) as f:
            source_code = f.read()

        # All imports should be relative (start with .)
        import_lines = [
            line.strip() for line in source_code.split("\n") if line.strip().startswith("from .")
        ]

        # Should have relative imports
        assert len(import_lines) > 0, "Should have relative imports"

        # No absolute imports of submodules
        forbidden = "from the_alchemiser.shared.types."
        assert forbidden not in source_code, f"Should use relative imports, not: {forbidden}"


class TestTypePreservation:
    """Test suite for type information preservation."""

    @pytest.mark.skip(reason="StrategySignal moved to shared.schemas in v2.10.7+")
    def test_type_hints_preserved(self) -> None:
        """Test that type hints are preserved through re-exports."""
        from the_alchemiser.shared.types import StrategySignal

        # Should maintain type information
        type_hints = get_type_hints(StrategySignal)

        # Verify key fields have type hints
        assert "symbol" in type_hints
        assert "action" in type_hints
        assert "timestamp" in type_hints

    def test_protocols_are_runtime_checkable(self) -> None:
        """Test that protocol exports are runtime checkable."""
        from typing import Any

        from the_alchemiser.shared.types import MarketDataPort, StrategyEngine

        # Both should be runtime checkable protocols
        assert hasattr(MarketDataPort, "_is_protocol")
        assert hasattr(StrategyEngine, "_is_protocol")

        # Should support isinstance checks
        class MockMarketData:
            def get_bars(self, symbol: Any, period: Any, timeframe: Any) -> list[Any]:
                return []

            def get_latest_quote(self, symbol: Any) -> None:
                return None

            def get_mid_price(self, symbol: Any) -> None:
                return None

        # Should pass protocol check
        assert isinstance(MockMarketData(), MarketDataPort)


class TestModuleMetadata:
    """Test suite for module metadata and documentation."""

    def test_module_docstring_structure(self) -> None:
        """Test that module docstring follows standard structure."""
        from the_alchemiser.shared import types

        docstring = types.__doc__
        assert docstring is not None

        # Should have business unit line
        lines = docstring.split("\n")
        first_line = lines[0]
        assert "Business Unit:" in first_line
        assert "Status:" in first_line

    def test_deprecation_note_in_docstring(self) -> None:
        """Test that deprecation of TimeInForce is documented."""
        from the_alchemiser.shared import types

        docstring = types.__doc__
        assert docstring is not None

        # Should mention TimeInForce deprecation
        assert "TimeInForce" in docstring
        assert "deprecated" in docstring.lower() or "BrokerTimeInForce" in docstring

    def test_all_exports_have_docstrings(self) -> None:
        """Test that all exported types have docstrings."""
        from the_alchemiser.shared import types

        # Type aliases don't have docstrings, skip them
        skip_types = {"OrderSideType", "TimeInForceType"}

        for name in types.__all__:
            if name in skip_types:
                continue

            obj = getattr(types, name)

            # Should have a docstring (either on the class or in the module)
            has_docstring = hasattr(obj, "__doc__") and obj.__doc__ is not None

            assert has_docstring, f"Export '{name}' should have a docstring"
