"""Business Unit: portfolio | Status: current

Test portfolio_v2.core module exports and public API.

Validates that the core submodule properly exports its components
following project standards for module initialization.
"""


class TestPortfolioCoreModuleExports:
    """Test portfolio_v2.core module initialization and exports."""

    def test_core_module_has_all_declaration(self):
        """Test that core module declares __all__ for public API."""
        from the_alchemiser.portfolio_v2 import core

        assert hasattr(core, "__all__")
        assert isinstance(core.__all__, list)
        assert len(core.__all__) == 3

    def test_core_module_exports_portfolio_service_v2(self):
        """Test that PortfolioServiceV2 is exported from core module."""
        from the_alchemiser.portfolio_v2 import core

        assert "PortfolioServiceV2" in core.__all__
        assert hasattr(core, "PortfolioServiceV2")
        assert core.PortfolioServiceV2 is not None

    def test_core_module_exports_rebalance_plan_calculator(self):
        """Test that RebalancePlanCalculator is exported from core module."""
        from the_alchemiser.portfolio_v2 import core

        assert "RebalancePlanCalculator" in core.__all__
        assert hasattr(core, "RebalancePlanCalculator")
        assert core.RebalancePlanCalculator is not None

    def test_core_module_exports_portfolio_state_reader(self):
        """Test that PortfolioStateReader is exported from core module."""
        from the_alchemiser.portfolio_v2 import core

        assert "PortfolioStateReader" in core.__all__
        assert hasattr(core, "PortfolioStateReader")
        assert core.PortfolioStateReader is not None

    def test_core_module_direct_import_portfolio_service_v2(self):
        """Test direct import of PortfolioServiceV2 from core."""
        from the_alchemiser.portfolio_v2.core import PortfolioServiceV2

        assert PortfolioServiceV2 is not None
        assert hasattr(PortfolioServiceV2, "__init__")

    def test_core_module_direct_import_rebalance_plan_calculator(self):
        """Test direct import of RebalancePlanCalculator from core."""
        from the_alchemiser.portfolio_v2.core import RebalancePlanCalculator

        assert RebalancePlanCalculator is not None
        assert hasattr(RebalancePlanCalculator, "__init__")

    def test_core_module_direct_import_portfolio_state_reader(self):
        """Test direct import of PortfolioStateReader from core."""
        from the_alchemiser.portfolio_v2.core import PortfolioStateReader

        assert PortfolioStateReader is not None
        assert hasattr(PortfolioStateReader, "__init__")

    def test_core_module_has_docstring(self):
        """Test that core module has proper docstring."""
        from the_alchemiser.portfolio_v2 import core

        assert core.__doc__ is not None
        assert "Business Unit: portfolio" in core.__doc__
        assert "Status: current" in core.__doc__
        assert "PortfolioServiceV2" in core.__doc__
        assert "RebalancePlanCalculator" in core.__doc__
        assert "PortfolioStateReader" in core.__doc__

    def test_core_module_exports_match_parent_module(self):
        """Test that core exports match what parent module expects."""
        from the_alchemiser.portfolio_v2 import (
            PortfolioServiceV2,
            RebalancePlanCalculator,
        )
        from the_alchemiser.portfolio_v2.core import (
            PortfolioServiceV2 as CorePortfolioServiceV2,
        )
        from the_alchemiser.portfolio_v2.core import (
            RebalancePlanCalculator as CoreRebalancePlanCalculator,
        )

        # Verify parent module lazy imports resolve to same classes as core exports
        assert PortfolioServiceV2 is CorePortfolioServiceV2
        assert RebalancePlanCalculator is CoreRebalancePlanCalculator

    def test_all_exports_are_importable(self):
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.portfolio_v2 import core

        for name in core.__all__:
            assert hasattr(core, name), f"{name} should be accessible on module"
            obj = getattr(core, name)
            assert obj is not None, f"{name} should not be None"


class TestCoreModuleCompliance:
    """Test core module compliance with project standards."""

    def test_core_module_has_shebang_line(self):
        """Test that core module starts with shebang for consistency."""
        import inspect

        from the_alchemiser.portfolio_v2 import core

        # Get source file path
        source_file = inspect.getsourcefile(core)
        assert source_file is not None

        # Read first line
        with open(source_file) as f:
            first_line = f.readline().strip()

        assert first_line == "#!/usr/bin/env python3", (
            "Module should start with shebang for consistency"
        )

    def test_core_module_uses_future_annotations(self):
        """Test that core module uses from __future__ import annotations."""
        import inspect

        from the_alchemiser.portfolio_v2 import core

        # Check annotations are enabled
        assert hasattr(core, "__annotations__"), "Module should support annotations"

        # Read source to verify import
        source_file = inspect.getsourcefile(core)
        assert source_file is not None

        with open(source_file) as f:
            content = f.read()

        assert "from __future__ import annotations" in content, (
            "Module should import annotations from __future__"
        )

    def test_core_module_business_unit_header(self):
        """Test that module docstring includes Business Unit header."""
        from the_alchemiser.portfolio_v2 import core

        assert core.__doc__ is not None
        assert "Business Unit: portfolio" in core.__doc__
        assert "Status: current" in core.__doc__

    def test_core_module_size_within_limits(self):
        """Test that core module stays within recommended size limits."""
        import inspect

        from the_alchemiser.portfolio_v2 import core

        source_file = inspect.getsourcefile(core)
        assert source_file is not None

        with open(source_file) as f:
            lines = f.readlines()

        line_count = len(lines)
        # Core __init__.py should be minimal (well under 500 line soft limit)
        assert line_count < 100, f"Core __init__.py should be minimal, got {line_count} lines"

    def test_core_module_no_wildcard_imports(self):
        """Test that core module doesn't use wildcard imports."""
        import inspect

        from the_alchemiser.portfolio_v2 import core

        source_file = inspect.getsourcefile(core)
        assert source_file is not None

        with open(source_file) as f:
            content = f.read()

        assert "from * import" not in content, "Should not use wildcard imports"
        assert "import *" not in content, "Should not use wildcard imports"
