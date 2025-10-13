"""Business Unit: portfolio | Status: current.

Test portfolio_v2.models module exports and public API.

Tests that the models module's public API exports work correctly,
ensuring PortfolioSnapshot can be imported cleanly and the module
docstring and __all__ are properly defined.
"""

import pytest


class TestPortfolioV2ModelsInit:
    """Test portfolio_v2.models module initialization and exports."""

    def test_import_portfolio_snapshot_from_models(self) -> None:
        """Test importing PortfolioSnapshot from models module."""
        from the_alchemiser.portfolio_v2.models import PortfolioSnapshot

        assert PortfolioSnapshot is not None
        assert hasattr(PortfolioSnapshot, "__init__")
        assert hasattr(PortfolioSnapshot, "__post_init__")

    def test_models_module_has_all(self) -> None:
        """Test that models module defines __all__."""
        from the_alchemiser.portfolio_v2 import models

        assert hasattr(models, "__all__")
        assert isinstance(models.__all__, list)
        assert "PortfolioSnapshot" in models.__all__

    def test_models_module_has_docstring(self) -> None:
        """Test that models module has proper docstring."""
        from the_alchemiser.portfolio_v2 import models

        assert models.__doc__ is not None
        assert "Business Unit: portfolio" in models.__doc__
        assert "Status: current" in models.__doc__

    def test_portfolio_snapshot_import_direct_vs_module(self) -> None:
        """Test that direct and module imports return same class."""
        from the_alchemiser.portfolio_v2.models import PortfolioSnapshot as PS1
        from the_alchemiser.portfolio_v2.models.portfolio_snapshot import (
            PortfolioSnapshot as PS2,
        )

        assert PS1 is PS2

    def test_portfolio_snapshot_is_frozen_dataclass(self) -> None:
        """Test that PortfolioSnapshot is a frozen dataclass."""
        from decimal import Decimal

        from the_alchemiser.portfolio_v2.models import PortfolioSnapshot

        # Create a snapshot
        snapshot = PortfolioSnapshot(
            positions={"AAPL": Decimal("10")},
            prices={"AAPL": Decimal("150.00")},
            cash=Decimal("1000.00"),
            total_value=Decimal("2500.00"),
        )

        # Verify it's frozen (immutable)
        with pytest.raises(Exception):  # dataclass(frozen=True) raises FrozenInstanceError
            snapshot.cash = Decimal("2000.00")  # type: ignore[misc]

    def test_portfolio_snapshot_validation_via_import(self) -> None:
        """Test that imported PortfolioSnapshot has validation."""
        from decimal import Decimal

        from the_alchemiser.portfolio_v2.models import PortfolioSnapshot

        # Test that validation works (missing price should raise error)
        with pytest.raises(ValueError, match="Missing prices for positions"):
            PortfolioSnapshot(
                positions={"AAPL": Decimal("10")},
                prices={},  # Missing price for AAPL
                cash=Decimal("1000.00"),
                total_value=Decimal("2500.00"),
            )

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.portfolio_v2 import models

        for export_name in models.__all__:
            assert hasattr(models, export_name)
            exported_item = getattr(models, export_name)
            assert exported_item is not None
