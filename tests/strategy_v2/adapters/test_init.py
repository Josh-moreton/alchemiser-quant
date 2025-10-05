"""Business Unit: strategy | Status: current.

Test suite for strategy_v2.adapters.__init__ module.

Tests module interface, public API exports, and import correctness.
"""

import inspect

import pytest

from the_alchemiser.strategy_v2 import adapters


class TestAdaptersModuleInterface:
    """Test suite for adapters module interface."""

    def test_module_has_correct_docstring(self):
        """Test module has proper business unit header."""
        assert adapters.__doc__ is not None
        assert "Business Unit: strategy" in adapters.__doc__
        assert "Status: current" in adapters.__doc__

    def test_module_exports_feature_pipeline(self):
        """Test module exports FeaturePipeline class."""
        assert hasattr(adapters, "FeaturePipeline")
        assert "FeaturePipeline" in adapters.__all__

    def test_module_exports_market_data_provider(self):
        """Test module exports MarketDataProvider protocol."""
        assert hasattr(adapters, "MarketDataProvider")
        assert "MarketDataProvider" in adapters.__all__

    def test_module_exports_strategy_market_data_adapter(self):
        """Test module exports StrategyMarketDataAdapter class."""
        assert hasattr(adapters, "StrategyMarketDataAdapter")
        assert "StrategyMarketDataAdapter" in adapters.__all__

    def test_all_contains_exactly_three_exports(self):
        """Test __all__ contains exactly the expected three exports."""
        assert len(adapters.__all__) == 3
        expected = {"FeaturePipeline", "MarketDataProvider", "StrategyMarketDataAdapter"}
        assert set(adapters.__all__) == expected

    def test_no_unexpected_exports(self):
        """Test module doesn't export unexpected items."""
        public_names = [name for name in dir(adapters) if not name.startswith("_")]
        # Filter out __all__, expected module attributes, and submodules
        expected_extras = ["annotations", "feature_pipeline", "market_data_adapter"]
        unexpected = [
            name
            for name in public_names
            if name not in adapters.__all__ and name not in expected_extras
        ]
        # Should only have the three main exports plus submodules
        assert len(unexpected) == 0, f"Unexpected exports: {unexpected}"


class TestFeaturePipelineExport:
    """Test FeaturePipeline export correctness."""

    def test_feature_pipeline_is_class(self):
        """Test FeaturePipeline is a class."""
        assert inspect.isclass(adapters.FeaturePipeline)

    def test_feature_pipeline_can_be_instantiated(self):
        """Test FeaturePipeline can be instantiated."""
        pipeline = adapters.FeaturePipeline()
        assert pipeline is not None

    def test_feature_pipeline_has_required_methods(self):
        """Test FeaturePipeline has expected public methods."""
        expected_methods = [
            "compute_returns",
            "compute_volatility",
            "compute_moving_average",
            "compute_correlation",
            "is_close",
        ]
        for method in expected_methods:
            assert hasattr(adapters.FeaturePipeline, method)


class TestMarketDataProviderExport:
    """Test MarketDataProvider export correctness."""

    def test_market_data_provider_is_protocol(self):
        """Test MarketDataProvider is a Protocol."""
        # Check if it's a protocol by inspecting class attributes
        assert hasattr(adapters.MarketDataProvider, "get_bars")
        assert hasattr(adapters.MarketDataProvider, "get_current_prices")

    def test_market_data_provider_defines_get_bars(self):
        """Test MarketDataProvider defines get_bars method."""
        assert hasattr(adapters.MarketDataProvider, "get_bars")

    def test_market_data_provider_defines_get_current_prices(self):
        """Test MarketDataProvider defines get_current_prices method."""
        assert hasattr(adapters.MarketDataProvider, "get_current_prices")


class TestStrategyMarketDataAdapterExport:
    """Test StrategyMarketDataAdapter export correctness."""

    def test_strategy_market_data_adapter_is_class(self):
        """Test StrategyMarketDataAdapter is a class."""
        assert inspect.isclass(adapters.StrategyMarketDataAdapter)

    def test_strategy_market_data_adapter_has_required_methods(self):
        """Test StrategyMarketDataAdapter has expected public methods."""
        expected_methods = ["get_bars", "get_current_prices", "validate_connection"]
        for method in expected_methods:
            assert hasattr(adapters.StrategyMarketDataAdapter, method)


class TestImportCorrectness:
    """Test import correctness and boundaries."""

    def test_imports_from_same_package(self):
        """Test imports are from same package (relative imports)."""
        # This verifies the module structure is correct
        from the_alchemiser.strategy_v2.adapters import (
            FeaturePipeline,
            MarketDataProvider,
            StrategyMarketDataAdapter,
        )

        assert FeaturePipeline is not None
        assert MarketDataProvider is not None
        assert StrategyMarketDataAdapter is not None

    def test_no_wildcard_imports(self):
        """Test module doesn't use wildcard imports."""
        # Read the source file to verify
        import pathlib

        module_path = pathlib.Path(adapters.__file__)
        source = module_path.read_text()
        assert "from * import" not in source
        assert "import *" not in source


class TestModuleCompliance:
    """Test module compliance with coding standards."""

    def test_module_has_shebang(self):
        """Test module has proper shebang."""
        import pathlib

        module_path = pathlib.Path(adapters.__file__)
        source = module_path.read_text()
        assert source.startswith("#!/usr/bin/env python3")

    def test_module_has_future_annotations(self):
        """Test module imports __future__ annotations."""
        import pathlib

        module_path = pathlib.Path(adapters.__file__)
        source = module_path.read_text()
        assert "from __future__ import annotations" in source

    def test_module_size_within_limits(self):
        """Test module is within size limits (≤ 500 lines soft, ≤ 800 hard)."""
        import pathlib

        module_path = pathlib.Path(adapters.__file__)
        line_count = len(module_path.read_text().splitlines())
        assert line_count <= 500, f"Module has {line_count} lines, exceeds 500 line target"
        assert line_count <= 800, f"Module has {line_count} lines, exceeds 800 line hard limit"
